"""Claims engine: adjudication, denials/rework, prior authorization, hospital ledger.

Encounters are generated in `encounters.py`; every billable event is routed through
`Engine.submit()`, which prices, adjudicates and stores the claim (and, for the
Understory Health system, writes the corresponding patient-accounting ledger rows).
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from .reference import (NONE, COMM, MKT, MCD_FFS, MCD_MC, MCR_FFS, MA, PAYER_TYPE_NAME, PROCEDURES, DRGS,
                        IPPS_BASE_RATE, PART_A_DEDUCTIBLE, PART_B_DEDUCTIBLE, START_YEAR, N_MONTHS, AS_OF_DATE, CARC)
from .coverage import PLAN_DF
from .world import SYSTEM

AS_OF = date.fromisoformat(AS_OF_DATE)
END_DATE = date(START_YEAR + N_MONTHS // 12 - 1, 12, 31)
ALLOWED_INFL = {2021: 1.00, 2022: 1.02, 2023: 1.045, 2024: 1.07, 2025: 1.10}
CHARGE_INFL = {2021: 1.00, 2022: 1.05, 2023: 1.10, 2024: 1.16, 2025: 1.22}
DENIAL_TREND = {2021: 1.00, 2022: 1.07, 2023: 1.15, 2024: 1.24, 2025: 1.32}

CLAIM_COLS = ["claim_id", "related_claim_id", "claim_frequency_code", "resubmission_reason", "account_id",
              "member_id", "claim_type", "claim_setting", "bill_type", "place_of_service", "service_from_date",
              "service_to_date", "admission_date", "discharge_date", "admission_type", "discharge_status",
              "length_of_stay", "drg_code", "billing_npi", "rendering_npi", "attending_npi", "referring_npi",
              "facility_npi", "payer_type", "plan_id"] + [f"dx_{k}" for k in range(1, 11)] + [
              "prior_auth_id", "total_charge", "total_allowed", "total_paid", "deductible_amount",
              "coinsurance_amount", "copay_amount", "patient_responsibility", "sequestration_amount",
              "cob_secondary_paid", "claim_status", "denial_reason_code", "submission_date", "adjudication_date",
              "appeal_outcome"]
LINE_COLS = ["claim_id", "line_number", "service_date", "procedure_code", "procedure_code_type", "modifier_1",
             "modifier_2", "revenue_code", "units", "line_charge", "line_allowed", "line_paid",
             "line_patient_responsibility", "line_status", "line_denial_reason_code"]
LEDGER_COLS = ["transaction_id", "account_id", "claim_id", "member_id", "billing_npi", "billing_provider_name",
               "service_line", "payer_type", "plan_id", "service_date", "transaction_date", "posting_period",
               "transaction_type", "transaction_category", "amount", "ar_effect", "group_code", "carc_code",
               "check_eft_number"]
PA_COLS = ["prior_auth_id", "member_id", "request_type", "service_code", "service_description", "requesting_npi",
           "servicing_npi", "payer_type", "plan_id", "submission_channel", "urgency", "submitted_datetime",
           "decision_datetime", "turnaround_hours", "decision", "denial_reason", "auto_adjudicated_flag"]

# rework behaviour by denial reason: (probability of rework, kind, probability overturned/paid)
REWORK = {
    "16": (0.85, "Corrected claim", 0.92), "11": (0.80, "Corrected claim", 0.85), "4": (0.85, "Corrected claim", 0.90),
    "197": (0.60, "Appeal", 0.45), "50": (0.45, "Appeal", 0.50), "29": (0.12, "Appeal", 0.15),
    "22": (0.75, "Corrected claim", 0.85), "27": (0.85, "Rebill", 1.0), "109": (0.85, "Rebill", 1.0),
    "242": (0.20, "Appeal", 0.30), "18": (0.0, None, 0.0),
}


def mindex(d: date) -> int:
    return (d.year - START_YEAR) * 12 + d.month - 1


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


class Store:
    """Column-oriented row store (lists per column) to keep memory low."""

    def __init__(self, cols):
        self.cols = cols
        self.data = {c: [] for c in cols}

    def add(self, row: dict):
        for c in self.cols:
            self.data[c].append(row.get(c))

    def df(self):
        if getattr(self, "_frozen", None) is not None:
            return self._frozen
        return pd.DataFrame(self.data, columns=self.cols)

    def freeze(self):
        """Convert to a compact DataFrame column by column, releasing the Python lists as we go."""
        out = {}
        for c in self.cols:
            col = pd.Series(self.data[c])
            self.data[c] = []
            if col.dtype == object:
                nn = col.dropna()
                if len(nn) and isinstance(nn.iloc[0], (date, datetime)):
                    col = pd.to_datetime(col)
                elif len(nn) and isinstance(nn.iloc[0], str) and col.nunique() < 0.5 * len(col):
                    col = col.astype("category")
            out[c] = col
        self._frozen = pd.DataFrame(out)
        self.data = {c: [] for c in self.cols}
        return self._frozen

    def __len__(self):
        if getattr(self, "_frozen", None) is not None:
            return len(self._frozen)
        return len(self.data[self.cols[0]])


class Engine:
    def __init__(self, rng, members: pd.DataFrame, providers: pd.DataFrame, cov: dict):
        self.rng = rng
        self.m = members
        self.member_ids = members.member_id.values
        self.adi_z = (members._adi.values - 60) / 20
        self.prov = providers.set_index("npi")
        self.cov = cov
        self.P = PLAN_DF
        self.claims = Store(CLAIM_COLS)
        self.lines = Store(LINE_COLS)
        self.ledger = Store(LEDGER_COLS)
        self.pa = Store(PA_COLS)
        self.n_claim = 0
        self.n_acct = 0
        self.n_txn = 0
        self.n_pa = 0
        self.n_eft = 0
        self.accum = defaultdict(lambda: [0.0, 0.0])      # (i, year) -> [deductible met, oop met]
        self.last_partA = {}                               # i -> last Part A deductible date
        self.pt_visits = defaultdict(int)                  # (i, year) -> PT visits
        pinfo = providers.set_index("npi")
        self.p_name = pinfo.provider_name.to_dict()
        self.p_system = pinfo.health_system.to_dict()
        self.p_role = pinfo.provider_role.to_dict()
        self.p_spec = pinfo.specialty.to_dict()
        self.p_markup = pinfo.hospital_markup.to_dict()
        self.p_contract = pinfo._contract_factor.to_dict()
        self.p_billq = pinfo._billing_quality.to_dict()
        self.p_epa = pinfo._epa_adopt_month.to_dict()
        self.p_practice = pinfo.practice_id.to_dict()

    # ------------------------------------------------------------------ ids
    def _cid(self):
        self.n_claim += 1
        return f"C{self.n_claim:010d}"

    def _acct(self):
        self.n_acct += 1
        return f"A{self.n_acct:09d}"

    def _tid(self):
        self.n_txn += 1
        return f"T{self.n_txn:010d}"

    def _eft(self):
        self.n_eft += 1
        return f"EFT{20000000 + self.n_eft}"

    # ------------------------------------------------------------------ coverage
    def coverage(self, i, d: date):
        mm = mindex(d)
        if mm < 0 or mm >= N_MONTHS:
            return NONE, -1, 0
        return int(self.cov["st"][mm, i]), int(self.cov["plan"][mm, i]), int(self.cov["dual"][mm, i])

    # ------------------------------------------------------------------ prior authorization
    def request_pa(self, i, d: date, code, desc, requesting_npi, servicing_npi, pidx, request_type="Medical",
                   urgency=None):
        """Create a prior-authorization request; return (pa_id, approved, decision_date)."""
        rng = self.rng
        ptype = int(self.P.payer_type_code[pidx])
        y = d.year - START_YEAR
        mm = mindex(d)
        if urgency is None:
            urgency = "Expedited" if rng.random() < 0.10 else "Standard"
        if request_type == "Pharmacy":
            adopt = self.p_epa.get(requesting_npi)
            adopted = adopt is not None and not (isinstance(adopt, float) and math.isnan(adopt)) and mm >= adopt
            p_epa = 0.88 if adopted else min(0.30 + 0.05 * y, 0.55)
            ch_p = [p_epa, 0.0, (1 - p_epa) * 0.8, (1 - p_epa) * 0.2]
        else:
            adopt = self.p_epa.get(requesting_npi)
            adopted = adopt is not None and not (isinstance(adopt, float) and math.isnan(adopt)) and mm >= adopt
            if adopted:
                ch_p = [0.80, 0.15, 0.04, 0.01]
            else:
                portal = 0.30 + 0.06 * y
                ch_p = [0.02 + 0.01 * y, portal, 0.92 - portal - 0.01 * y - 0.08, 0.08]
        ch_p = np.clip(np.array(ch_p), 0, None)
        channel = ["ePA", "Payer Portal", "Fax", "Phone"][rng.choice(4, p=ch_p / ch_p.sum())]
        auto = False
        if channel == "ePA":
            auto = rng.random() < (0.25 + 0.04 * y)
            hours = rng.uniform(0.01, 0.4) if auto else rng.lognormal(math.log(6), 1.0)
        elif channel == "Payer Portal":
            hours = rng.lognormal(math.log(30), 0.8)
        elif channel == "Fax":
            hours = rng.lognormal(math.log(80), 0.6)
        else:
            hours = rng.lognormal(math.log(22), 0.9)
        if urgency == "Expedited":
            hours *= 0.3
        p_appr = {"ePA": 0.91, "Payer Portal": 0.88, "Fax": 0.84, "Phone": 0.86}[channel]
        if ptype == MA:
            p_appr -= 0.04
        approved = auto or rng.random() < p_appr
        sub_dt = datetime(d.year, d.month, d.day) + timedelta(hours=float(rng.uniform(7, 18)))
        dec_dt = sub_dt + timedelta(hours=float(hours))
        self.n_pa += 1
        pa_id = f"PA{self.n_pa:08d}"
        self.pa.add(dict(prior_auth_id=pa_id, member_id=self.member_ids[i], request_type=request_type,
                         service_code=code, service_description=desc, requesting_npi=requesting_npi,
                         servicing_npi=servicing_npi, payer_type=PAYER_TYPE_NAME[ptype], plan_id=self.P.plan_id[pidx],
                         submission_channel=channel, urgency=urgency, submitted_datetime=sub_dt,
                         decision_datetime=dec_dt, turnaround_hours=round(hours, 2),
                         decision="Approved" if approved else "Denied",
                         denial_reason=None if approved else rng.choice(
                             ["Not medically necessary", "Insufficient clinical documentation",
                              "Step therapy / conservative treatment not met", "Service not covered under benefit"],
                             p=[0.40, 0.35, 0.18, 0.07]),
                         auto_adjudicated_flag=int(auto)))
        return pa_id, approved, dec_dt.date()

    # ------------------------------------------------------------------ pricing helpers
    def _charge_markup(self, billing_npi, ctype):
        mk = self.p_markup.get(billing_npi)
        if mk is not None and not (isinstance(mk, float) and math.isnan(mk)):
            return mk
        role = self.p_role.get(billing_npi)
        return {"Lab": 3.8, "DME": 2.4, "Imaging": 3.2, "SNF": 1.6}.get(role, 2.9)

    def _patient_resp(self, i, year, pidx, ptype, category, allowed, preventive, d: date):
        """Return (deductible, coinsurance, copay)."""
        if allowed <= 0 or preventive or ptype in (MCD_FFS, MCD_MC):
            return 0.0, 0.0, 0.0
        P = self.P
        acc = self.accum[(i, year)]
        ded = coins = copay = 0.0
        if ptype == MCR_FFS:
            if category in ("lab",):
                return 0.0, 0.0, 0.0
            if category in ("ip_fac",):
                last = self.last_partA.get(i)
                if last is None or (d - last).days > 60:
                    ded = min(PART_A_DEDUCTIBLE[year], allowed)
                    self.last_partA[i] = d
                return ded, 0.0, 0.0
            if category == "snf":
                return 0.0, 0.0, 0.0
            bded = PART_B_DEDUCTIBLE[year]
            ded = min(max(bded - acc[0], 0), allowed)
            acc[0] += ded
            coins = 0.20 * (allowed - ded)
            return round(ded, 2), round(coins, 2), 0.0
        oop_max = P.oop_max[pidx]
        remaining_oop = max(oop_max - acc[1], 0)
        if ptype == MA:
            if category == "lab":
                return 0.0, 0.0, 0.0
            if category in ("office_pcp", "tele"):
                copay = P.copay_pcp[pidx]
            elif category in ("office_spec", "bh", "eye"):
                copay = P.copay_specialist[pidx]
            elif category == "ed_fac":
                copay = P.copay_ed[pidx]
            elif category == "ip_fac":
                copay = P.inpatient_copay[pidx]
            elif category in ("imaging", "proc", "dme", "pt"):
                coins = 0.20 * allowed
            copay = min(copay, allowed)
            tot = min(copay + coins, remaining_oop)
            scale = tot / (copay + coins) if copay + coins > 0 else 0
            acc[1] += tot
            return 0.0, round(coins * scale, 2), round(copay * scale, 2)
        # commercial / marketplace
        dedu = P.deductible[pidx]
        co = P.coinsurance[pidx]
        cp = {"office_pcp": P.copay_pcp[pidx], "tele": P.copay_pcp[pidx], "office_spec": P.copay_specialist[pidx],
              "bh": P.copay_specialist[pidx], "eye": P.copay_specialist[pidx], "ed_fac": P.copay_ed[pidx]}.get(category, 0)
        if cp > 0:
            copay = min(cp, allowed)
        else:
            ded = min(max(dedu - acc[0], 0), allowed)
            coins = co * (allowed - ded)
        tot = ded + coins + copay
        if tot > remaining_oop:
            scale = remaining_oop / tot if tot > 0 else 0
            ded, coins, copay = ded * scale, coins * scale, copay * scale
        acc[0] += ded
        acc[1] += ded + coins + copay
        return round(ded, 2), round(coins, 2), round(copay, 2)

    # ------------------------------------------------------------------ main entry point
    def submit(self, i, ctype, setting, from_d: date, to_d: date, billing_npi, lines, dx, *, category,
               rendering=None, attending=None, referring=None, facility=None, pos=None, bill_type=None, drg=None,
               admit=None, discharge=None, admit_type=None, dstatus=None, los=None, pa_needed=False, pa_id=None,
               pa_approved=True, preventive=False, account=None, related=None, freq="1", resub_reason=None,
               force_plan=None, submit_d=None, attempt=0, med_nec_risk=0.0, forced_denial=None, ledger_ctx=None, _reuse_cid=None, charges=None):
        """Price, adjudicate and store one claim. `lines` = list of
        (code, revenue_code, units, unit_rate, mod1, mod2, service_date)."""
        rng = self.rng
        if from_d > END_DATE:
            return None
        year = from_d.year
        is_sys = self.p_system.get(billing_npi) == SYSTEM
        new_account = account is None
        if new_account:
            account = self._acct()
        # --- who is billed
        if force_plan is not None:
            ptype, pidx = int(self.P.payer_type_code[force_plan]), force_plan
            dual = 0
        else:
            ptype, pidx, dual = self.coverage(i, from_d)
        wrong_payer = False
        mm = mindex(from_d)
        if attempt == 0 and force_plan is None and mm >= 1:
            prev = [int(self.cov["plan"][k, i]) for k in (mm - 1, mm - 2) if k >= 0]
            prev = [p for p in prev if p >= 0 and p != pidx]
            if prev and rng.random() < (0.5 if ptype == NONE else 0.28):
                pidx = prev[0]
                ptype = int(self.P.payer_type_code[pidx])
                wrong_payer = True
                dual = 0
        # --- charges
        mk = self._charge_markup(billing_npi, ctype) * CHARGE_INFL[year]
        line_rows = []
        for k_, (code, rev, units, rate, m1, m2, sd) in enumerate(lines):
            if charges is not None:
                charge = charges[k_]
            else:
                charge = round(rate * units * mk * rng.uniform(0.95, 1.05), 2) if rate > 0 else 0.0
            line_rows.append([code, rev, units, rate, m1, m2, sd, charge])
        total_charge = round(sum(r[7] for r in line_rows), 2)
        # --- submission lag
        if submit_d is None:
            lag = rng.lognormal(math.log(6 if ctype == "Professional" else 4), 0.8)
            if rng.random() < 0.012 * math.exp(-0.5 * self.p_billq.get(billing_npi, 0) or 0):
                lag += rng.uniform(90, 420)
            submit_d = to_d + timedelta(days=int(lag))
        cid = _reuse_cid or self._cid()
        row = dict(claim_id=cid, related_claim_id=related, claim_frequency_code=freq, resubmission_reason=resub_reason,
                   account_id=account, member_id=self.member_ids[i], claim_type=ctype, claim_setting=setting,
                   bill_type=bill_type, place_of_service=pos, service_from_date=from_d, service_to_date=to_d,
                   admission_date=admit, discharge_date=discharge, admission_type=admit_type, discharge_status=dstatus,
                   length_of_stay=los, drg_code=drg, billing_npi=billing_npi, rendering_npi=rendering,
                   attending_npi=attending, referring_npi=referring, facility_npi=facility,
                   prior_auth_id=pa_id, total_charge=total_charge, submission_date=submit_d)
        dxp = (list(dict.fromkeys(dx)) + [None] * 10)[:10]
        for k in range(10):
            row[f"dx_{k + 1}"] = dxp[k]
        service_line = {"Inpatient": "Inpatient", "Emergency": "Emergency", "SNF": "Post-acute"}.get(
            setting, "Outpatient" if ctype == "Institutional" else "Professional")

        # ================================================================ self-pay
        if ptype == NONE:
            row.update(payer_type="Self-pay", plan_id=None, total_allowed=round(total_charge * 0.40, 2), total_paid=0.0,
                       deductible_amount=0.0, coinsurance_amount=0.0, copay_amount=0.0,
                       patient_responsibility=round(total_charge * 0.40, 2), sequestration_amount=0.0,
                       cob_secondary_paid=0.0, claim_status="Self-pay", denial_reason_code=None,
                       adjudication_date=None, appeal_outcome=None)
            self.claims.add(row)
            for n_, r in enumerate(line_rows, 1):
                self._add_line(cid, n_, r, round(r[7] * 0.4, 2), 0.0, round(r[7] * 0.4, 2), "Self-pay", None)
            if is_sys:
                self._ledger_selfpay(i, account, cid, billing_npi, service_line, to_d, total_charge, new_account)
            return cid

        P = self.P
        row.update(payer_type=PAYER_TYPE_NAME[ptype], plan_id=P.plan_id[pidx])
        days_to_pay = max(3, int(rng.gamma(4, P.avg_days_to_pay[pidx] / 4)))
        adj_d = submit_d + timedelta(days=days_to_pay)

        # ================================================================ claim-level denial
        dm = P.denial_mult[pidx] * DENIAL_TREND[year] * math.exp(-0.6 * (self.p_billq.get(billing_npi, 0) or 0))
        reason = forced_denial
        if reason is None:
            if wrong_payer:
                reason = "27" if rng.random() < 0.8 else "109"
            elif (submit_d - to_d).days > P.timely_filing_days[pidx]:
                reason = "29"
            elif pa_needed and P.requires_prior_auth[pidx] and (pa_id is None or not pa_approved):
                reason = "197"
            else:
                u = rng.random()
                cuts = [("16", 0.033 * dm), ("11", 0.009 * dm), ("4", 0.006 * dm),
                        ("22", (0.006 + (0.02 if dual else 0)) * dm), ("50", med_nec_risk * dm),
                        ("242", 0.018 * dm if P.requires_pcp[pidx] and category == "office_spec" else 0)]
                acc = 0.0
                for code, p in cuts:
                    acc += p
                    if u < acc:
                        reason = code
                        break
            if attempt > 0 and reason not in ("27", "109", "29") and forced_denial is None:
                reason = None if rng.random() < 0.9 else reason
        pending = adj_d > AS_OF
        if pending:
            row.update(total_allowed=None, total_paid=None, deductible_amount=None, coinsurance_amount=None,
                       copay_amount=None, patient_responsibility=None, sequestration_amount=None,
                       cob_secondary_paid=None, claim_status="Pending", denial_reason_code=None,
                       adjudication_date=None, appeal_outcome=None)
            self.claims.add(row)
            for n_, r in enumerate(line_rows, 1):
                self._add_line(cid, n_, r, None, None, None, "Pending", None)
            if is_sys and new_account:
                self._ledger_charge(i, account, cid, billing_npi, service_line, ptype, pidx, to_d, total_charge)
            return cid

        if reason is not None:
            row.update(total_allowed=0.0, total_paid=0.0, deductible_amount=0.0, coinsurance_amount=0.0,
                       copay_amount=0.0, patient_responsibility=0.0, sequestration_amount=0.0, cob_secondary_paid=0.0,
                       claim_status="Denied", denial_reason_code=reason, adjudication_date=adj_d, appeal_outcome=None)
            for n_, r in enumerate(line_rows, 1):
                self._add_line(cid, n_, r, 0.0, 0.0, 0.0, "Denied", reason)
            rw = REWORK.get(reason, (0, None, 0))
            do_rework = rng.random() < rw[0] * (1.15 if is_sys else 1.0)
            if is_sys and new_account:
                self._ledger_charge(i, account, cid, billing_npi, service_line, ptype, pidx, to_d, total_charge)
            if is_sys:
                self._txn(account, cid, i, billing_npi, service_line, ptype, pidx, to_d, adj_d, "Denial",
                          "Denial", total_charge, 0.0, CARC[reason][0], reason)
            if do_rework:
                kind = rw[1]
                resub_d = adj_d + timedelta(days=int(rng.integers(10, 75 if kind == "Appeal" else 40)))
                success = rng.random() < rw[2]
                if kind == "Appeal":
                    row["appeal_outcome"] = "Overturned" if success else "Upheld"
                self.claims.add(row)
                if is_sys:
                    ttype = {"Appeal": "Appeal Filed", "Corrected claim": "Corrected Claim Submitted",
                             "Rebill": "Rebilled to Other Payer"}[kind]
                    self._txn(account, cid, i, billing_npi, service_line, ptype, pidx, to_d, resub_d, ttype,
                              "Informational", 0.0, 0.0, None, None)
                if kind == "Rebill":
                    cur_t, cur_p, _ = self.coverage(i, from_d)
                    fp = cur_p if cur_p >= 0 else None
                    if fp is None:
                        # no other coverage: account becomes self-pay
                        if is_sys:
                            self._ledger_selfpay(i, account, cid, billing_npi, service_line, resub_d, total_charge, False)
                        return cid
                    self.submit(i, ctype, setting, from_d, to_d, billing_npi, lines, dx, category=category,
                                rendering=rendering, attending=attending, referring=referring, facility=facility,
                                pos=pos, bill_type=bill_type, drg=drg, admit=admit, discharge=discharge,
                                admit_type=admit_type, dstatus=dstatus, los=los, pa_needed=pa_needed, pa_id=pa_id,
                                pa_approved=pa_approved, preventive=preventive, account=account, related=cid,
                                freq="1", resub_reason="Rebilled to correct payer", force_plan=fp, submit_d=resub_d,
                                attempt=attempt + 1, charges=[r[7] for r in line_rows], med_nec_risk=med_nec_risk)
                elif success:
                    self.submit(i, ctype, setting, from_d, to_d, billing_npi, lines, dx, category=category,
                                rendering=rendering, attending=attending, referring=referring, facility=facility,
                                pos=pos, bill_type=bill_type, drg=drg, admit=admit, discharge=discharge,
                                admit_type=admit_type, dstatus=dstatus, los=los, pa_needed=False, pa_id=pa_id,
                                preventive=preventive, account=account, related=cid, freq="7",
                                resub_reason="Appeal overturned" if kind == "Appeal" else "Corrected claim",
                                force_plan=pidx, submit_d=resub_d, attempt=attempt + 1, charges=[r[7] for r in line_rows], med_nec_risk=0.0)
                elif is_sys:
                    self._txn(account, cid, i, billing_npi, service_line, ptype, pidx, to_d,
                              resub_d + timedelta(days=int(rng.integers(30, 90))), "Denial Write-off", "Write-off",
                              total_charge, -total_charge, CARC[reason][0], reason)
            else:
                self.claims.add(row)
                if is_sys:
                    self._txn(account, cid, i, billing_npi, service_line, ptype, pidx, to_d,
                              adj_d + timedelta(days=int(rng.integers(30, 120))), "Denial Write-off", "Write-off",
                              total_charge, -total_charge, CARC[reason][0], reason)
            return cid

        # ================================================================ paid claim
        fee = P.fee_mult[pidx] * ALLOWED_INFL[year]
        if ptype in (COMM, MKT):
            fee *= self.p_contract.get(billing_npi, 1.0) or 1.0
        line_allowed = []
        line_status = []
        line_reason = []
        if drg is not None:
            claim_allowed = min(DRGS[drg][1] * IPPS_BASE_RATE * fee * rng.uniform(0.97, 1.03), total_charge)
            tc = total_charge if total_charge > 0 else 1
            line_allowed = [claim_allowed * r[7] / tc for r in line_rows]
            line_status = ["Paid"] * len(line_rows)
            line_reason = [None] * len(line_rows)
        else:
            has_em = any(r[0] in PROCEDURES and PROCEDURES[r[0]][2] in ("E&M Office", "Preventive") for r in line_rows)
            for r in line_rows:
                code = r[0]
                a = r[3] * r[2] * fee
                st, rs = "Paid", None
                if code == "36415" and has_em and ptype in (COMM, MKT, MA) and rng.random() < 0.35:
                    st, rs = "Denied", "97"
                elif code == "92014" and ptype == MCR_FFS and not any(x and x.startswith("E11") for x in dx):
                    st, rs = "Denied", "96"
                elif category == "pt" and ptype in (COMM, MKT) and self.pt_visits[(i, year)] > 20:
                    st, rs = "Denied", "119"
                if st == "Denied":
                    a = 0.0
                a = min(a, r[7])  # payers pay the lesser of billed charge or contracted rate
                line_allowed.append(a)
                line_status.append(st)
                line_reason.append(rs)
            claim_allowed = sum(line_allowed)
        claim_allowed = round(claim_allowed, 2)
        if line_status and all(s == "Denied" for s in line_status):
            forced = next(r for r in line_reason if r)
            return self.submit(i, ctype, setting, from_d, to_d, billing_npi, lines, dx, category=category,
                               rendering=rendering, attending=attending, referring=referring, facility=facility,
                               pos=pos, bill_type=bill_type, drg=drg, admit=admit, discharge=discharge,
                               admit_type=admit_type, dstatus=dstatus, los=los, pa_id=pa_id, preventive=preventive,
                               account=None if new_account else account, related=related, freq=freq,
                               resub_reason=resub_reason, force_plan=pidx, submit_d=submit_d, attempt=attempt + 1, charges=[r[7] for r in line_rows],
                               forced_denial=forced, _reuse_cid=cid)
        ded, coins, copay = self._patient_resp(i, year, pidx, ptype, category, claim_allowed, preventive, to_d)
        pr = round(ded + coins + copay, 2)
        paid = claim_allowed - pr
        seq = 0.0
        if ptype == MCR_FFS:
            rate = 0.0 if adj_d < date(2022, 4, 1) else (0.01 if adj_d < date(2022, 7, 1) else 0.02)
            seq = round(paid * rate, 2)
            paid -= seq
        paid = round(max(paid, 0.0), 2)
        sec = 0.0
        if dual and pr > 0:
            sec = round(pr * rng.uniform(0.15, 0.6), 2)
        status = "Paid" if all(s == "Paid" for s in line_status) else "Partially Paid"
        row.update(total_allowed=claim_allowed, total_paid=paid, deductible_amount=ded, coinsurance_amount=coins,
                   copay_amount=copay, patient_responsibility=pr, sequestration_amount=seq, cob_secondary_paid=sec,
                   claim_status=status, denial_reason_code=None, adjudication_date=adj_d, appeal_outcome=None)
        self.claims.add(row)
        ca = claim_allowed if claim_allowed > 0 else 1
        for n_, r in enumerate(line_rows, 1):
            la = round(line_allowed[n_ - 1], 2)
            self._add_line(cid, n_, r, la, round(paid * la / ca, 2), round(pr * la / ca, 2), line_status[n_ - 1],
                           line_reason[n_ - 1])
        if is_sys:
            if new_account:
                self._ledger_charge(i, account, cid, billing_npi, service_line, ptype, pidx, to_d, total_charge)
            self._ledger_paid(i, account, cid, billing_npi, service_line, ptype, pidx, to_d, adj_d, total_charge,
                              claim_allowed, paid, ded, coins, copay, seq, sec, dual, line_rows, line_status, line_reason)
        return cid

    def _add_line(self, cid, n, r, allowed, paid, pr, status, reason):
        code = r[0]
        ctype = PROCEDURES[code][1] if code in PROCEDURES else None
        self.lines.add(dict(claim_id=cid, line_number=n, service_date=r[6], procedure_code=code,
                            procedure_code_type=ctype, modifier_1=r[4], modifier_2=r[5], revenue_code=r[1],
                            units=r[2], line_charge=r[7], line_allowed=allowed, line_paid=paid,
                            line_patient_responsibility=pr, line_status=status, line_denial_reason_code=reason))

    # ------------------------------------------------------------------ ledger helpers
    def _txn(self, account, cid, i, npi, sline, ptype, pidx, svc_d, t_d, ttype, tcat, amount, ar, grp, carc, eft=None):
        self.ledger.add(dict(transaction_id=self._tid(), account_id=account, claim_id=cid, member_id=self.member_ids[i],
                             billing_npi=npi, billing_provider_name=self.p_name.get(npi), service_line=sline,
                             payer_type="Self-pay" if ptype == NONE else PAYER_TYPE_NAME[ptype],
                             plan_id=None if pidx is None or pidx < 0 else self.P.plan_id[pidx], service_date=svc_d,
                             transaction_date=t_d, posting_period=f"{t_d.year}-{t_d.month:02d}",
                             transaction_type=ttype, transaction_category=tcat, amount=round(amount, 2),
                             ar_effect=round(ar, 2), group_code=grp, carc_code=carc, check_eft_number=eft))

    def _ledger_charge(self, i, account, cid, npi, sline, ptype, pidx, svc_d, charge):
        self._txn(account, cid, i, npi, sline, ptype, pidx, svc_d, svc_d + timedelta(days=int(self.rng.integers(0, 3))),
                  "Charge", "Charge", charge, charge, None, None)

    def _ledger_paid(self, i, account, cid, npi, sline, ptype, pidx, svc_d, adj_d, charge, allowed, paid, ded, coins,
                     copay, seq, sec, dual, line_rows, line_status, line_reason):
        rng = self.rng
        eft = self._eft()
        T = lambda *a, **k: self._txn(account, cid, i, npi, sline, ptype, pidx, svc_d, *a, **k)
        denied_charge = sum(r[7] for r, s in zip(line_rows, line_status) if s != "Paid")
        T(adj_d, "Insurance Payment", "Payment", paid, -paid, None, None, eft)
        contractual = round(charge - denied_charge - allowed, 2)
        if contractual > 0:
            T(adj_d, "Contractual Adjustment", "Adjustment", contractual, -contractual, "CO", "45", eft)
        if seq > 0:
            T(adj_d, "Sequestration Adjustment", "Adjustment", seq, -seq, "CO", "253", eft)
        for amt, code in ((ded, "1"), (coins, "2"), (copay, "3")):
            if amt > 0:
                T(adj_d, "Patient Responsibility", "Informational", amt, 0.0, "PR", code, eft)
        for r, s, rs in zip(line_rows, line_status, line_reason):
            if s != "Paid":
                T(adj_d, "Line Denial", "Denial", r[7], 0.0, "CO", rs, eft)
                T(adj_d + timedelta(days=int(rng.integers(20, 90))), "Denial Write-off", "Write-off", r[7], -r[7], "CO", rs)
        pr = round(ded + coins + copay, 2)
        if pr <= 0:
            return
        if dual:
            d2 = adj_d + timedelta(days=int(rng.integers(14, 45)))
            T(d2, "Secondary Insurance Payment", "Payment", sec, -sec, None, None, self._eft())
            rest = round(pr - sec, 2)
            if rest > 0:
                T(d2, "Contractual Adjustment (Secondary)", "Adjustment", rest, -rest, "CO", "45")
            return
        p_full = {COMM: 0.70, MKT: 0.50, MA: 0.76, MCR_FFS: 0.72}.get(ptype, 0.6) * (1 - 0.12 * self.adi_z[i])
        self._patient_collect(i, account, cid, npi, sline, ptype, pidx, svc_d, adj_d, pr, p_full)

    def _patient_collect(self, i, account, cid, npi, sline, ptype, pidx, svc_d, start_d, bal, p_full):
        rng = self.rng
        T = lambda *a, **k: self._txn(account, cid, i, npi, sline, ptype, pidx, svc_d, *a, **k)
        u = rng.random()
        if u < p_full:
            k = int(rng.choice([1, 1, 1, 2, 3]))
            parts = np.diff(np.r_[0, np.sort(rng.random(k - 1)), 1]) * bal
            d = start_d
            for p in parts:
                d = d + timedelta(days=int(rng.integers(15, 60)))
                T(d, "Patient Payment", "Payment", round(p, 2), -round(p, 2), None, None)
        else:
            paid = 0.0
            if rng.random() < 0.35:
                paid = round(bal * rng.uniform(0.1, 0.6), 2)
                T(start_d + timedelta(days=int(rng.integers(20, 90))), "Patient Payment", "Payment", paid, -paid, None, None)
            rest = round(bal - paid, 2)
            T(start_d + timedelta(days=int(rng.integers(150, 210))), "Bad Debt Write-off", "Write-off", rest, -rest, None, None)

    def _ledger_selfpay(self, i, account, cid, npi, sline, svc_d, charge, new_account):
        rng = self.rng
        T = lambda *a, **k: self._txn(account, cid, i, npi, sline, NONE, None, svc_d, *a, **k)
        if new_account:
            T(svc_d + timedelta(days=int(rng.integers(0, 3))), "Charge", "Charge", charge, charge, None, None)
        disc = round(charge * 0.60, 2)
        T(svc_d + timedelta(days=int(rng.integers(3, 10))), "Self-Pay Discount", "Adjustment", disc, -disc, None, None)
        bal = round(charge - disc, 2)
        if self.m._adi.values[i] >= 65 or rng.random() < 0.30:
            if rng.random() < 0.85:
                T(svc_d + timedelta(days=int(rng.integers(30, 90))), "Charity Care Adjustment", "Write-off", bal, -bal,
                  None, None)
                return
        self._patient_collect(i, account, cid, npi, sline, NONE, None, svc_d, svc_d + timedelta(days=10), bal, 0.15)
