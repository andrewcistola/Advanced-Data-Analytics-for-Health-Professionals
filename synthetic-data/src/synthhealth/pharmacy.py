"""Medication regimens and pharmacy claims."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .reference import DRUGS, NCPDP_REJECT, NONE, COMM, MKT, MCD_FFS, MCD_MC, MCR_FFS, MA, PAYER_TYPE_NAME, \
    PDP_PLAN, N_MONTHS, START_YEAR
from .engine import Store, mindex, END_DATE, AS_OF
from .population import NO_ONSET

RX_COLS = ["rx_claim_id", "member_id", "fill_date", "ndc", "drug_name", "generic_name", "brand_generic_flag",
           "therapeutic_class", "days_supply", "quantity", "refill_number", "new_rx_flag", "prescriber_npi",
           "pharmacy_npi", "mail_order_flag", "payer_type", "plan_id", "formulary_tier", "prior_auth_required_flag",
           "prior_auth_id", "claim_status", "reject_code", "reject_description", "ingredient_cost",
           "dispensing_fee", "total_cost", "member_copay", "plan_paid"]

# quantity per day (or per fill basis for inhalers/pens)
QTY_PER_DAY = {"METFORMIN": 2, "GABAPENTIN": 3, "BUPRENORPHINE": 2, "OXYCODONE30": 4, "OXYCODONE5": 4,
               "HYDROCODONE": 4, "TRAMADOL": 3, "CYCLOBENZAPRINE": 3, "AMOXICILLIN": 3, "NITROFURANTOIN": 2,
               "ONDANSETRON": 3, "CARVEDILOL": 2, "FUROSEMIDE": 1, "APIXABAN": 2, "ENTRESTO": 2}
FIXED_QTY = {"ALBUTEROL": 8.5, "FLUTICASONE_SALM": 60, "TIOTROPIUM": 30, "GLARGINE": 15, "SEMAGLUTIDE": 3,
             "TIRZEPATIDE": 2, "ADALIMUMAB": 2, "NALOXONE": 2}
NDC = {k: f"9{1000 + n * 37:04d}{2000 + n * 113:04d}{11 + n % 80:02d}" for n, k in enumerate(DRUGS)}

SPECIALIST_RX = {"SEMAGLUTIDE": ("Endocrinology", 0.3), "TIRZEPATIDE": ("Endocrinology", 0.3),
                 "GLARGINE": ("Endocrinology", 0.4), "ENTRESTO": ("Cardiology", 0.6), "APIXABAN": ("Cardiology", 0.5),
                 "TIOTROPIUM": ("Pulmonology", 0.4), "SERTRALINE": ("Psychiatry", 0.25),
                 "ESCITALOPRAM": ("Psychiatry", 0.25), "BUPROPION": ("Psychiatry", 0.25),
                 "ADALIMUMAB": ("Rheumatology", 1.0), "METHOTREXATE": ("Rheumatology", 0.9),
                 "ANASTROZOLE": ("Hematology & Oncology", 1.0), "BUPRENORPHINE": ("Psychiatry", 0.6)}


def assign_regimens(rng, m: pd.DataFrame, cond: dict) -> dict:
    """Return {member_index: [(drug, start_month, end_month), ...]}"""
    on = cond["onset"]
    n = len(m)
    age = (np.datetime64("2023-07-01") - m.birth_date.values.astype("datetime64[D]")).astype(float) / 365.25
    fr = m._frailty.values
    adh = m._adherence.values
    reg = defaultdict(list)
    has = {c: on[c] < NO_ONSET for c in on}
    glp_p = [0.04, 0.07, 0.10, 0.12, 0.12]

    def start_for(i, c):
        o = on[c][i]
        return 0 if o < 0 else int(min(o + rng.integers(0, 3), N_MONTHS - 1))

    def add(i, drug, s):
        if DRUGS[drug][8] > s:
            s = DRUGS[drug][8]
        # discontinuation
        disc = 0.010 * (1.6 - adh[i])
        e = s + int(rng.geometric(disc)) if disc > 0 else N_MONTHS
        reg[i].append((drug, s, min(e, N_MONTHS - 1)))

    for i in range(n):
        if age[i] < 1:
            continue
        r = rng.random
        if has["HTN"][i] and r() < 0.88:
            s = start_for(i, "HTN")
            picks = [d for d, p in (("LISINOPRIL", .45), ("AMLODIPINE", .35), ("LOSARTAN", .25), ("HCTZ", .25)) if r() < p]
            for d in picks or ["LISINOPRIL"]:
                add(i, d, s)
        statin_p = max(0.75 * has["HLD"][i], 0.62 * (has["DIAB"][i] and age[i] >= 40), 0.80 * has["CAD"][i])
        if statin_p and r() < statin_p:
            c = "HLD" if has["HLD"][i] else ("CAD" if has["CAD"][i] else "DIAB")
            add(i, "ATORVASTATIN" if r() < 0.76 else "ROSUVASTATIN", start_for(i, c))
        if has["DIAB"][i]:
            s = start_for(i, "DIAB")
            ckd = on["CKD"][i] < NO_ONSET and cond["ckd_stage"][i] in ("4", "5")
            if r() < 0.82 and not ckd:
                add(i, "METFORMIN", s)
            if r() < 0.28 + 0.10 * (age[i] >= 65):
                add(i, "GLIPIZIDE", s)
            if r() < 0.18 + 0.10 * (fr[i] > 1):
                add(i, "GLARGINE", s)
            if r() < 0.14 + 0.15 * (has["CHF"][i] or has["CKD"][i]):
                add(i, "EMPAGLIFLOZIN", s)
            for y in range(5):
                if r() < glp_p[y]:
                    sm = max(s, y * 12 + int(rng.integers(0, 12)))
                    add(i, "TIRZEPATIDE" if sm >= 17 and r() < 0.4 else "SEMAGLUTIDE", sm)
                    break
        if has["CHF"][i]:
            s = start_for(i, "CHF")
            if r() < 0.7:
                add(i, "METOPROLOL" if r() < 0.55 else "CARVEDILOL", s)
            if r() < 0.75:
                add(i, "FUROSEMIDE", s)
            if r() < 0.30:
                add(i, "SPIRONOLACTONE", s)
            if r() < 0.25:
                add(i, "ENTRESTO", s + int(rng.integers(0, 24)))
        if has["AFIB"][i]:
            s = start_for(i, "AFIB")
            u = r()
            if u < 0.6:
                add(i, "APIXABAN", s)
            elif u < 0.75:
                add(i, "WARFARIN", s)
            if r() < 0.5:
                add(i, "METOPROLOL", s)
        if has["CAD"][i] and r() < 0.5:
            add(i, "METOPROLOL", start_for(i, "CAD"))
        if has["COPD"][i]:
            s = start_for(i, "COPD")
            if r() < 0.85:
                add(i, "ALBUTEROL", s)
            if r() < 0.35:
                add(i, "TIOTROPIUM", s)
            if r() < 0.40:
                add(i, "FLUTICASONE_SALM", s)
        if has["ASTH"][i]:
            s = start_for(i, "ASTH")
            if r() < 0.8:
                add(i, "ALBUTEROL", s)
            if r() < 0.3:
                add(i, "FLUTICASONE_SALM", s)
            if r() < 0.3:
                add(i, "MONTELUKAST", s)
        if has["DEPR"][i]:
            u = r()
            s = start_for(i, "DEPR")
            if u < 0.35:
                add(i, "SERTRALINE", s)
            elif u < 0.65:
                add(i, "ESCITALOPRAM", s)
            elif u < 0.80:
                add(i, "BUPROPION", s)
        if has["RA"][i]:
            s = start_for(i, "RA")
            if r() < 0.6:
                add(i, "METHOTREXATE", s)
            if r() < 0.3:
                add(i, "ADALIMUMAB", s + int(rng.integers(0, 12)))
        if has["DEMEN"][i] and r() < 0.55:
            add(i, "DONEPEZIL", start_for(i, "DEMEN"))
        if has["OUD"][i]:
            s = start_for(i, "OUD")
            if r() < 0.45:
                add(i, "BUPRENORPHINE", s)
        if has["BRCA"][i] and r() < 0.7:
            add(i, "ANASTROZOLE", start_for(i, "BRCA"))
        if age[i] >= 18:
            if r() < 0.04 + 0.05 * (m.sex.values[i] == "F") + 0.04 * (age[i] >= 65):
                add(i, "LEVOTHYROXINE", 0 if r() < 0.85 else int(rng.integers(0, N_MONTHS)))
            if r() < 0.08:
                add(i, "OMEPRAZOLE", 0 if r() < 0.7 else int(rng.integers(0, N_MONTHS)))
            if r() < 0.04 + 0.08 * has["DIAB"][i]:
                add(i, "GABAPENTIN", 0 if r() < 0.7 else int(rng.integers(0, N_MONTHS)))
    return reg


def on_drug(regimens, i, drug_set, mm) -> bool:
    for d, s, e in regimens.get(i, ()):
        if d in drug_set and s <= mm <= e:
            return True
    return False


class PharmacyGenerator:
    def __init__(self, rng, gen, engine):
        self.rng = rng
        self.g = gen
        self.e = engine
        self.out = Store(RX_COLS)
        self.n = 0
        self.pa_valid = {}
        prov = gen.prov
        retail = prov[(prov.specialty == "Community/Retail Pharmacy") & prov._fraud_scheme.isna()]
        self.retail_npis = retail.npi.values
        self.retail_ll = gen.zl.loc[retail.zip_code, ["latitude", "longitude"]].values
        self.mail_npi = prov[prov.specialty == "Mail Order Pharmacy"].npi.values[0]
        self.spec_npi = prov[prov.specialty == "Specialty Pharmacy"].npi.values[0]
        self.pref_pharm = {}

    def _pharmacy(self, i):
        if i not in self.pref_pharm:
            from .world import haversine
            la, lo = self.g.mll[i]
            d = haversine(la, lo, self.retail_ll[:, 0], self.retail_ll[:, 1])
            w = 1 / (d + 2) ** 2
            self.pref_pharm[i] = self.retail_npis[self.rng.choice(len(w), p=w / w.sum())]
        return self.pref_pharm[i]

    def _rx_plan(self, i, d):
        ptype, pidx, dual = self.e.coverage(i, d)
        mm = mindex(d)
        if mm < 0 or mm >= N_MONTHS or not self.g.cov["rx"][mm, i]:
            return None
        if ptype == MCR_FFS:
            return ptype, PDP_PLAN[0], dual, True
        return ptype, self.e.P.plan_id[pidx], dual, bool(self.e.P.requires_prior_auth[pidx])

    def _copay(self, ptype, plan_id, tier, total, ds, dual):
        if ptype in (MCD_FFS, MCD_MC):
            return 0.0
        mult = 2.5 if ds >= 84 else 1.0
        if ptype in (MA, MCR_FFS):
            if dual:
                return min(4.5 if tier == 1 else 11.2, total)
            cp = {1: 0, 2: 10, 3: 47}.get(tier, 0.33 * total)
        elif ptype == COMM:
            cp = {1: 10, 2: 35, 3: 70}.get(tier, min(0.25 * total, 250))
        else:
            cp = {1: 15, 2: 50, 3: 100}.get(tier, min(0.40 * total, 500))
        return round(min(cp * (mult if tier <= 3 else 1), total), 2)

    def _add(self, i, d, drug, ds, qty, refill, new, prescriber, pharm, cov, status="Paid", reject=None, pa_id=None):
        self.n += 1
        name, generic, cls, daily, tier, pa_req, bg, specialty, _ = DRUGS[drug]
        ptype, plan_id, dual, plan_pa = cov
        infl = (1.06 if bg == "Brand" else 0.99) ** (d.year - START_YEAR)
        ing = round(daily * ds * infl * self.rng.uniform(0.92, 1.08), 2)
        fee = 10.24 if ptype in (MCD_FFS, MCD_MC) else round(float(self.rng.uniform(0.5, 2.5)), 2)
        total = round(ing + fee, 2)
        paid = status == "Paid"
        copay = self._copay(ptype, plan_id, tier, total, ds, dual) if paid else 0.0
        self.out.add(dict(
            rx_claim_id=f"R{self.n:010d}", member_id=self.g.m.member_id.values[i], fill_date=d, ndc=NDC[drug],
            drug_name=name, generic_name=generic, brand_generic_flag=bg, therapeutic_class=cls, days_supply=ds,
            quantity=qty, refill_number=refill, new_rx_flag=int(new), prescriber_npi=prescriber, pharmacy_npi=pharm,
            mail_order_flag=int(pharm == self.mail_npi), payer_type=PAYER_TYPE_NAME[ptype], plan_id=plan_id,
            formulary_tier=tier, prior_auth_required_flag=int(pa_req and plan_pa), prior_auth_id=pa_id,
            claim_status=status, reject_code=reject, reject_description=NCPDP_REJECT.get(reject),
            ingredient_cost=ing if paid else None, dispensing_fee=fee if paid else None,
            total_cost=total if paid else None, member_copay=copay if paid else None,
            plan_paid=round(total - copay, 2) if paid else None))

    def _alive(self, i, d):
        return self.g.active(i, d)

    def run_regimens(self, regimens):
        rng = self.rng
        adh = self.g.m._adherence.values
        for i, regs in regimens.items():
            for drug, s, e in regs:
                info = DRUGS[drug]
                prescriber = self.g.prescriber(i, drug)
                if prescriber is None:
                    continue
                maint = info[4] <= 2 and info[3] < 5
                ninety = maint and rng.random() < 0.35
                mail = ninety and rng.random() < 0.45
                ds = 90 if ninety else (28 if drug in ("SEMAGLUTIDE", "TIRZEPATIDE", "ADALIMUMAB") else 30)
                qty = FIXED_QTY.get(drug, QTY_PER_DAY.get(drug, 1) * ds)
                if drug in FIXED_QTY and ds == 90:
                    qty = FIXED_QTY[drug] * 3
                pharm = self.spec_npi if info[7] else (self.mail_npi if mail else self._pharmacy(i))
                # first fill date
                if s == 0 and self.g.m._enter_m.values[i] == 0:
                    d = date(START_YEAR, 1, 1) + timedelta(days=int(rng.integers(0, ds)))
                else:
                    d = date(START_YEAR + max(s, self.g.m._enter_m.values[i]) // 12,
                             max(s, self.g.m._enter_m.values[i]) % 12 + 1, int(rng.integers(1, 28)))
                end_d = min(date(START_YEAR + e // 12, e % 12 + 1, 28), END_DATE)
                refill = 0
                new = s > 0
                last_cov = None
                stopped = False
                while d <= end_d and not stopped:
                    if not self._alive(i, d):
                        break
                    cov = self._rx_plan(i, d)
                    if cov is None:
                        if last_cov is not None and rng.random() < 0.3:
                            self._add(i, d, drug, ds, qty, refill, new, prescriber, pharm, last_cov,
                                      status="Rejected", reject="65")
                        last_cov = None
                        # no coverage: often goes without (gap) -> next attempt later
                        d = d + timedelta(days=int(ds * rng.uniform(0.8, 1.6)))
                        continue
                    last_cov = cov
                    pa_id = None
                    if info[5] and cov[3]:
                        key = (i, drug)
                        valid = self.pa_valid.get(key)
                        if not valid or valid[0] != cov[1] or valid[1] < d:
                            self._add(i, d, drug, ds, qty, refill, new, prescriber, pharm, cov, status="Rejected",
                                      reject="75")
                            pidx = self.e.coverage(i, d)[1]
                            if pidx < 0:
                                break
                            pa_id, ok, dec = self.e.request_pa(i, d, NDC[drug], info[0], prescriber, pharm, pidx,
                                                               request_type="Pharmacy")
                            if not ok:
                                stopped = True
                                break
                            self.pa_valid[key] = (cov[1], dec + timedelta(days=365))
                            d = dec + timedelta(days=int(rng.integers(0, 3)))
                            if d > END_DATE:
                                break
                        else:
                            pa_id = None
                    if cov[0] in (MCD_FFS, MCD_MC) and drug in ("EMPAGLIFLOZIN", "TIOTROPIUM") and refill == 0 and rng.random() < 0.3:
                        self._add(i, d, drug, ds, qty, refill, new, prescriber, pharm, cov, status="Rejected", reject="70")
                        d = d + timedelta(days=int(rng.integers(2, 8)))
                    if refill > 0 and rng.random() < 0.025:
                        self._add(i, d - timedelta(days=int(rng.integers(5, 10))), drug, ds, qty, refill, False,
                                  prescriber, pharm, cov, status="Rejected", reject="79")
                    self._add(i, d, drug, ds, qty, refill, new and refill == 0, prescriber, pharm, cov, pa_id=pa_id)
                    refill += 1
                    a = adh[i] - (0.06 if info[4] >= 3 and cov[0] in (COMM, MKT) else 0)
                    a = min(max(a, 0.05), 0.99)
                    gap = ds * (1 / a - 1) * rng.exponential(1.0)
                    d = d + timedelta(days=int(ds + gap))
                    if refill % 12 == 0 and rng.random() < 0.15:
                        refill = 0  # new prescription written
                        new = False

    def run_acute(self, acute):
        rng = self.rng
        for i, d, drug, prescriber, ds in acute:
            if d > END_DATE or rng.random() > 0.85:
                continue
            cov = self._rx_plan(i, d)
            if cov is None:
                continue
            qty = FIXED_QTY.get(drug, QTY_PER_DAY.get(drug, 1) * ds)
            self._add(i, d, drug, ds, qty, 0, True, prescriber, self._pharmacy(i), cov)

    def run_pill_mill(self, members, prescriber, pharmacy):
        rng = self.rng
        for i, start, end in members:
            d = start
            while d <= end:
                if not self._alive(i, d):
                    break
                cov = self._rx_plan(i, d)
                if cov is not None:
                    self._add(i, d, "OXYCODONE30", 30, 120, 0, True, prescriber, pharmacy, cov)
                d = d + timedelta(days=int(rng.integers(26, 31)))
