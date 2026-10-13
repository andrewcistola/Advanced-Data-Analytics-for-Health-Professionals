"""Clinical event generator: turns members' latent health + coverage into encounters,
which are billed through the Engine (claims) and recorded in answer-key truth tables."""
from __future__ import annotations

import calendar
import math
from collections import defaultdict
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .reference import (NONE, COMM, MKT, MCD_FFS, MCD_MC, MCR_FFS, MA, CONDITION_DX, CKD_STAGE_DX, ACUTE_DX,
                        ADMIT_REASONS, PROCEDURES, ED_FACILITY_RATE, DRGS, N_MONTHS, START_YEAR, CHRONIC_FOR_COUNT)
from .engine import mindex, sigmoid, END_DATE
from .population import NO_ONSET, age_at
from .pharmacy import on_drug, SPECIALIST_RX
from .world import haversine, SYSTEM

ACUTE_CODES = list(ACUTE_DX)
ACUTE_P = np.array(list(ACUTE_DX.values()))
ACUTE_P = ACUTE_P / ACUTE_P.sum()
TELE_SHARE = {2021: 0.26, 2022: 0.15, 2023: 0.10, 2024: 0.08, 2025: 0.07}
TCP_LAUNCH = date(2023, 7, 1)          # Transitional Care Program start at Understory hospitals
TCP_TRUE_OR = 0.70                     # true odds ratio of readmission for enrolled patients
CCM_START_M = 12                       # Diabetes complex case management starts Jan 2022
CCM_HAZARD_RR = 0.80
SPEC_LAMBDA = [  # (condition, specialty, monthly rate)
    ("CHF", "Cardiology", 0.22), ("CAD", "Cardiology", 0.10), ("AFIB", "Cardiology", 0.12),
    ("DIAB", "Endocrinology", 0.035), ("COPD", "Pulmonology", 0.09), ("CKD", "Nephrology", 0.05),
    ("DEPR", "Psychiatry", 0.06), ("RA", "Rheumatology", 0.14), ("BRCA", "Hematology & Oncology", 0.30),
    ("KNEEOA", "Orthopaedic Surgery", 0.05), ("OUD", "Psychiatry", 0.10),
]
SPEC_DX = {"Cardiology": ["CHF", "CAD", "AFIB", "HTN"], "Endocrinology": ["DIAB", "OBES"], "Pulmonology": ["COPD", "ASTH"],
           "Nephrology": ["CKD", "HTN", "DIAB"], "Psychiatry": ["DEPR", "OUD"], "Rheumatology": ["RA"],
           "Hematology & Oncology": ["BRCA"], "Orthopaedic Surgery": ["KNEEOA"]}


def rday(rng, mm: int) -> date:
    y, mo = START_YEAR + mm // 12, mm % 12 + 1
    return date(y, mo, int(rng.integers(1, calendar.monthrange(y, mo)[1] + 1)))


class Generator:
    def __init__(self, rng, members, providers, zips, cond, cov, home_pcp, regimens, engine):
        self.rng = rng
        self.m = members
        self.prov = providers
        self.zl = zips.set_index("zip_code")
        self.cond = cond
        self.on = cond["onset"]
        self.cov = cov
        self.home = home_pcp
        self.reg = regimens
        self.e = engine
        n = len(members)
        self.n = n
        self.birth = members.birth_date.values
        self.sex = members.sex.values
        self.fr = members._frailty.values
        self.care = members._care_seek.values
        self.adh = members._adherence.values
        self.adi_z = (members._adi.values - 60) / 20
        self.zrisk = members._zip_risk.values
        self.mll = self.zl.loc[members.zip_code, ["latitude", "longitude"]].values
        self.death = [None if pd.isna(x) else x.date() for x in members.death_date]
        self.bdate = [x.date() for x in members.birth_date]
        p = providers.set_index("npi")
        self.quality = p._quality.to_dict()
        self.doc_rate = p._doc_rate.to_dict()
        self.practice = p.practice_id.to_dict()
        self.system = p.health_system.to_dict()
        self.aco = p.aco_name.to_dict()
        self.fraud = p._fraud_scheme.to_dict()
        pr = providers
        self.pcp_npis = pr[pr.provider_role == "PCP"].npi.values
        self.fqhc_npis = pr[(pr.provider_role == "PCP") & (pr.fqhc_flag == 1)].npi.values
        self.by_practice = pr.groupby("practice_id").npi.apply(list).to_dict()
        self.spec = {}
        for s, g in pr[pr.provider_role == "Specialist"].groupby("specialty"):
            g = g[g._fraud_scheme.isna() | (g.specialty != "Pain Medicine")]
            self.spec[s] = (g.npi.values, self.zl.loc[g.zip_code, ["latitude", "longitude"]].values)
        h = pr[pr.provider_role == "Hospital"]
        self.hosp_npis = h.npi.values
        self.hosp_ll = self.zl.loc[h.zip_code, ["latitude", "longitude"]].values
        self.hosp_beds = h._bed_count.values.astype(float)
        self.hosp_sys = h.health_system.values
        self.hosp_docs = {}
        for hn, hz in zip(h.npi, h.zip_code):
            ed = pr[(pr.specialty == "Emergency Medicine") & (pr.zip_code == hz)].npi.values
            hm = pr[(pr.specialty == "Hospitalist") & (pr.zip_code == hz)].npi.values
            self.hosp_docs[hn] = (ed, hm)
        self.sys_hosp = h[h.health_system == SYSTEM].npi.values
        self.srmc = h[h.provider_name == "Understory Regional Medical Center"].npi.values[0]
        self.lab_map = pr[pr.provider_role == "Lab"].set_index("provider_name").npi.to_dict()
        self.lab_good = self.lab_map["Gulf Atlantic Reference Laboratory"]
        self.lab_fraud = self.lab_map["Prairie Diagnostics Laboratory"]
        img = pr[pr.provider_role == "Imaging"]
        self.img_npis, self.img_ll = img.npi.values, self.zl.loc[img.zip_code, ["latitude", "longitude"]].values
        dme = pr[pr.provider_role == "DME"]
        self.dme_good = dme[dme._fraud_scheme.isna()].npi.values
        self.dme_fraud = dme[dme._fraud_scheme.notna()].npi.values[0]
        snf = pr[pr.provider_role == "SNF"]
        self.snf_npis = snf.npi.values
        pt = pr[pr.specialty == "Physical Therapy"]
        self.pt_good = pt[pt._fraud_scheme.isna()].npi.values
        self.pt_fraud = pt[pt._fraud_scheme.notna()].npi.values
        self.lcsw = pr[pr.specialty == "Clinical Social Worker"]
        self.lcsw_fraud = self.lcsw[self.lcsw._fraud_scheme.notna()].npi.values[0]
        self.lcsw_good = self.lcsw[self.lcsw._fraud_scheme.isna()].npi.values
        self.pain_doc = pr[pr._fraud_scheme == "PILL_MILL_PRESCRIBER"].npi.values[0]
        self.radiologists = pr[pr.specialty == "Diagnostic Radiology"].npi.values
        self.ob = pr[pr.specialty == "Obstetrics & Gynecology"].npi.values
        # practices whose lab work is steered to the fraudulent lab (kickback arrangement)
        indep = pr[(pr.provider_role == "PCP") & (pr.health_system == "Independent") & (pr.fqhc_flag == 0)
                   & (pr.specialty != "Pediatrics")
                   & pr._fraud_scheme.isna()].practice_id.unique()
        self.kickback_practices = set(rng.choice(indep, size=3, replace=False))
        # member state
        self.pref = {}
        self.seen = set()
        self.a1c = {}
        self.last_a1c = {}
        self.dm_comp = defaultdict(set)
        self.ccm_until = {}
        self.colon_done = set()
        self.morbid = rng.random(n) < 0.25
        self.oxygen = set()
        self.flu = set()
        self.yearplan = defaultdict(list)
        self.acute_rx = []
        self.care_mgmt = []
        self.truth_dm = []
        self.truth_ip = []
        self.pill_mill = []
        self.lcsw_panel = set()
        self.n_cm = 0

    # ------------------------------------------------------------------ helpers
    def active(self, i, d: date) -> bool:
        mm = mindex(d)
        if mm < 0 or mm >= N_MONTHS or d > END_DATE:
            return False
        if not self.cov["present"][mm, i] or d < self.bdate[i]:
            return False
        return self.death[i] is None or d <= self.death[i]

    def has(self, i, c, mm):
        return self.on[c][i] <= mm

    def age(self, i, mm):
        return float(age_at(self.birth[i:i + 1], mm)[0])

    def ptype(self, i, mm):
        return int(self.cov["st"][mm, i]) if 0 <= mm < N_MONTHS else NONE

    def pcp_for(self, i):
        h = self.home[i]
        if h is not None:
            if self.rng.random() < 0.85:
                return h
            return self.rng.choice(self.by_practice[self.practice[h]])
        if self.adi_z[i] > 0 and self.rng.random() < 0.6:
            return self.rng.choice(self.fqhc_npis)
        return self.rng.choice(self.pcp_npis)

    def pref_spec(self, i, spec):
        key = (i, spec)
        if key not in self.pref:
            npis, ll = self.spec[spec]
            d = haversine(self.mll[i, 0], self.mll[i, 1], ll[:, 0], ll[:, 1])
            w = 1 / (d + 8) ** 1.5
            self.pref[key] = npis[self.rng.choice(len(npis), p=w / w.sum())]
        return self.pref[key]

    def pref_hosp(self, i):
        key = (i, "H")
        if key not in self.pref:
            d = haversine(self.mll[i, 0], self.mll[i, 1], self.hosp_ll[:, 0], self.hosp_ll[:, 1])
            w = self.hosp_beds ** 0.6 / (d + 5) ** 1.6
            self.pref[key] = self.hosp_npis[self.rng.choice(len(w), p=w / w.sum())]
        return self.pref[key]

    def prescriber(self, i, drug):
        if drug in SPECIALIST_RX:
            spec, p = SPECIALIST_RX[drug]
            if self.rng.random() < p and spec in self.spec:
                return self.pref_spec(i, spec)
        h = self.home[i]
        return h if h is not None else self.rng.choice(self.pcp_npis)

    def q(self, npi):
        return self.quality.get(npi, 0.0) or 0.0

    def a1c_val(self, i, year):
        key = (i, year)
        if key not in self.a1c:
            mm = (year - START_YEAR) * 12 + 6
            v = 6.7 + 3.5 * (0.78 - self.adh[i]) + 0.25 * self.fr[i] + self.rng.normal(0, 0.6)
            if on_drug(self.reg, i, {"GLARGINE"}, mm):
                v += 0.5
            if on_drug(self.reg, i, {"SEMAGLUTIDE", "TIRZEPATIDE"}, mm):
                v -= 0.6
            if self.ccm_until.get(i, -1) >= mm:
                v -= 0.3
            self.a1c[key] = float(np.clip(v, 5.4, 13.5))
        return self.a1c[key]

    def chronic_dx(self, i, mm, rate, focus=None):
        """Chronic-condition diagnosis codes documented on a claim (each with probability `rate`)."""
        rng = self.rng
        out = []
        conds = focus if focus is not None else list(CONDITION_DX) + ["CKD"]
        for c in conds:
            if c not in self.on or not self.has(i, c, mm):
                continue
            if rng.random() > rate:
                continue
            if c == "DIAB":
                comps = sorted(self.dm_comp.get(i, ()))
                if comps:
                    out.extend(comps[:2])
                else:
                    out.append("E11.65" if self.a1c_val(i, START_YEAR + mm // 12) > 8.5 else "E11.9")
                if on_drug(self.reg, i, {"GLARGINE"}, mm):
                    out.append("Z79.4")
                elif on_drug(self.reg, i, {"METFORMIN", "GLIPIZIDE"}, mm):
                    out.append("Z79.84")
            elif c == "CKD":
                out.append(CKD_STAGE_DX[self.cond["ckd_stage"][i]])
            elif c == "HTN" and self.has(i, "CKD", mm):
                out.append("I12.9")
            elif c == "OBES":
                out.extend(["E66.01", "Z68.41"] if self.morbid[i] else ["E66.9"])
            else:
                codes = CONDITION_DX[c]
                out.append(codes[i % len(codes)])
        return out

    def em_level(self, npi, i, nchron, new):
        rng = self.rng
        if new:
            return rng.choice(["99203", "99204", "99205"], p=[0.45, 0.45, 0.10])
        if self.fraud.get(npi) == "EM_UPCODING":
            p = [0.01, 0.07, 0.27, 0.65]
        elif nchron == 0:
            p = [0.12, 0.55, 0.30, 0.03]
        elif nchron <= 2:
            p = [0.06, 0.45, 0.43, 0.06]
        else:
            p = [0.03, 0.30, 0.55, 0.12]
        return rng.choice(["99212", "99213", "99214", "99215"], p=p)

    def L(self, code, units=1, d=None, mod1=None, mod2=None, rev=None, rate=None):
        r = PROCEDURES[code][3] if rate is None and code in PROCEDURES else (rate or 0)
        return (code, rev, units, r, mod1, mod2, d)

    # ------------------------------------------------------------------ encounter types
    def office_visit(self, i, d, npi, *, kind="pcp", dx=None, preventive=False, extra=(), tele=False,
                     referring=None, nchron=0, em=None):
        rng = self.rng
        if not self.active(i, d):
            return None
        mm = mindex(d)
        prac = self.practice.get(npi)
        new = (i, prac) not in self.seen
        self.seen.add((i, prac))
        code = em or self.em_level(npi, i, nchron, new)
        mod = "95" if tele else None
        pos = ("02" if d.year == 2021 else "10") if tele else "11"
        lines = [self.L(code, d=d, mod1=mod)] + list(extra)
        cat = "tele" if tele else ("preventive" if preventive else ("office_pcp" if kind == "pcp" else
                                                                    ("bh" if kind == "bh" else "office_spec")))
        setting = "Telehealth" if tele else "Office"
        return self.e.submit(i, "Professional", setting, d, d, npi, lines, dx, category=cat, rendering=npi,
                             referring=referring, pos=pos, preventive=preventive)

    def quality_codes(self, i, d, npi, mm, diabetic, htn):
        """CPT II reporting codes for HEDIS hybrid-style measures."""
        rng = self.rng
        out = []
        qv = self.q(npi)
        if rng.random() > sigmoid(0.2 + 1.0 * qv):
            return out
        if diabetic and self.last_a1c.get(i, -99) >= mm - 1:
            v = self.a1c_val(i, d.year)
            out.append(self.L("3044F" if v < 7 else "3051F" if v < 8 else "3052F" if v <= 9 else "3046F", d=d))
        if htn:
            ctrl = rng.random() < sigmoid(0.6 + 2.5 * (self.adh[i] - 0.72) + 0.4 * qv - 0.3 * (self.age(i, mm) >= 75)
                                          - 0.2 * self.adi_z[i])
            if ctrl:
                out += [self.L("3074F" if rng.random() < 0.55 else "3075F", d=d), self.L("3078F" if rng.random() < 0.6 else "3079F", d=d)]
            else:
                if rng.random() < 0.75:
                    out += [self.L("3077F", d=d), self.L(rng.choice(["3079F", "3080F"]), d=d)]
                else:
                    out += [self.L("3075F", d=d), self.L("3080F", d=d)]
        return out

    def labs(self, i, d, ordering, codes, dx, preventive=False):
        rng = self.rng
        if not self.active(i, d):
            return
        prac = self.practice.get(ordering)
        if not codes:
            return
        if prac in self.kickback_practices and d >= date(2021, 9, 1):
            codes = list(codes) + (["G0483"] if rng.random() < 0.7 else []) + (["87633"] if rng.random() < 0.5 else [])
            lines = [self.L(c, d=d) for c in codes + ["36415"]]
            self.e.submit(i, "Professional", "Laboratory", d, d, self.lab_fraud, lines, dx, category="lab",
                          rendering=self.lab_fraud, referring=ordering, pos="81", preventive=preventive)
        elif self.system.get(ordering) == SYSTEM:
            lines = [self.L(c, d=d, rev="0300") for c in list(codes) + ["36415"]]
            self.e.submit(i, "Institutional", "Outpatient Hospital", d, d, self.srmc, lines, dx, category="lab",
                          attending=ordering, referring=ordering, facility=self.srmc, bill_type="131", pos="22",
                          preventive=preventive)
        else:
            lines = [self.L(c, d=d) for c in list(codes) + ["36415"]]
            self.e.submit(i, "Professional", "Laboratory", d, d, self.lab_good, lines, dx, category="lab",
                          rendering=self.lab_good, referring=ordering, pos="81", preventive=preventive)

    def imaging(self, i, d, code, ordering, dx, preventive=False):
        rng = self.rng
        if not self.active(i, d):
            return
        pa_needed = PROCEDURES[code][4]
        ptype, pidx, _ = self.e.coverage(i, d)
        pa_id, ok = None, True
        sysord = self.system.get(ordering) == SYSTEM
        if sysord:
            billing = self.srmc
        else:
            dd = haversine(self.mll[i, 0], self.mll[i, 1], self.img_ll[:, 0], self.img_ll[:, 1])
            billing = self.img_npis[int(np.argmin(dd))]
        if pa_needed and pidx >= 0 and self.e.P.requires_prior_auth[pidx]:
            if rng.random() < 0.90:
                pa_id, ok, dec = self.e.request_pa(i, d - timedelta(days=int(rng.integers(3, 12))), code,
                                                   PROCEDURES[code][0], ordering, billing, pidx)
                if not ok and rng.random() < 0.75:
                    return  # service cancelled after PA denial
                if dec > d:
                    d = dec + timedelta(days=int(rng.integers(1, 5)))
                    if not self.active(i, d):
                        return
        rev = {"77067": "0403", "74177": "0350", "70450": "0350", "71250": "0350", "72148": "0610", "70553": "0610",
               "73721": "0610", "78452": "0341"}.get(code, "0320")
        mnr = 0.03 if pa_needed else 0.0
        if sysord:
            lines = [self.L(code, d=d, rev=rev, rate=PROCEDURES[code][3] * 1.5)]
            self.e.submit(i, "Institutional", "Outpatient Hospital", d, d, billing, lines, dx, category="imaging",
                          attending=ordering, referring=ordering, facility=billing, bill_type="131", pos="22",
                          pa_needed=pa_needed, pa_id=pa_id, pa_approved=ok, preventive=preventive, med_nec_risk=mnr)
            rad = rng.choice(self.radiologists)
            self.e.submit(i, "Professional", "Outpatient Hospital", d, d, rad,
                          [self.L(code, d=d, mod1="26", rate=PROCEDURES[code][3] * 0.3)], dx, category="imaging",
                          rendering=rad, referring=ordering, pos="22", preventive=preventive)
        else:
            self.e.submit(i, "Professional", "Office", d, d, billing, [self.L(code, d=d)], dx, category="imaging",
                          rendering=billing, referring=ordering, pos="11", pa_needed=pa_needed, pa_id=pa_id,
                          pa_approved=ok, preventive=preventive, med_nec_risk=mnr)

    def pcp_visit(self, i, d, mm, nchron, preventive=False):
        rng = self.rng
        npi = self.pcp_for(i)
        age = self.age(i, mm)
        diab = self.has(i, "DIAB", mm)
        htn = self.has(i, "HTN", mm)
        doc = self.doc_rate.get(npi, 0.8)
        extra = []
        labs = []
        if preventive:
            ptype = self.ptype(i, mm)
            if ptype in (MCR_FFS, MA):
                code = "G0438" if (i, "AWV") not in self.pref else "G0439"
                self.pref[(i, "AWV")] = 1
            elif age < 1:
                code = "99381" if rng.random() < 0.3 else "99391"
            else:
                code = "99393" if age < 12 else "99394" if age < 18 else "99395" if age < 40 else "99396" if age < 65 else "99397"
            dx = ["Z00.129"] if age < 18 else [rng.choice(["Z00.00", "Z00.01"], p=[0.6, 0.4])]
            dx += self.chronic_dx(i, mm, 0.97)
            if age >= 18:
                labs += ["80053", "85025"] + (["80061"] if age >= 35 or self.has(i, "HLD", mm) else [])
                if rng.random() < 0.15:
                    labs.append("84443")
        else:
            code = None
            chronic = nchron > 0 and rng.random() < 0.68
            if chronic:
                dx = self.chronic_dx(i, mm, 1.0, focus=[rng.choice([c for c in CHRONIC_FOR_COUNT + ["OBES"] if self.has(i, c, mm)] or ["HTN"])])
                dx += self.chronic_dx(i, mm, doc * 0.45)
            else:
                ac = ACUTE_CODES[rng.choice(len(ACUTE_CODES), p=ACUTE_P)]
                if ac == "U07.1" and not (d.year in (2021, 2022) or rng.random() < 0.3):
                    ac = "J06.9"
                if ac == "H66.90" and age > 12:
                    ac = "J02.9"
                dx = [ac] + self.chronic_dx(i, mm, doc * 0.35)
                self._acute_followups(i, d, mm, ac, npi)
            if diab and mm - self.last_a1c.get(i, -99) >= 3:
                ccm = self.ccm_until.get(i, -1) >= mm
                if rng.random() < sigmoid(0.1 + 0.8 * self.q(npi) + 0.8 * ccm):
                    labs.append("83036")
            if (htn or self.has(i, "CKD", mm) or self.has(i, "CHF", mm)) and rng.random() < 0.3:
                labs.append("80053")
        if diab and "83036" not in labs and preventive:
            labs.append("83036")
        if diab and rng.random() < sigmoid(-1.4 + 0.9 * self.q(npi)):
            labs += ["82043", "82570"]
        if "83036" in labs:
            self.last_a1c[i] = mm
        extra = self.quality_codes(i, d, npi, mm, diab, htn)
        tele = (not preventive) and age >= 2 and rng.random() < TELE_SHARE[d.year]
        if tele:
            extra = []
        cid = self.office_visit(i, d, npi, dx=dx, preventive=preventive, extra=extra, tele=tele, nchron=nchron, em=code)
        if labs and not tele:
            self.labs(i, d, npi, list(dict.fromkeys(labs)), dx[:4], preventive=preventive)
        return npi

    def _acute_followups(self, i, d, mm, ac, npi):
        rng = self.rng
        age = self.age(i, mm)
        if ac in ("J06.9", "J02.9", "H66.90") and rng.random() < 0.35:
            self.acute_rx.append((i, d, "AMOXICILLIN" if rng.random() < 0.6 else "AZITHROMYCIN", npi, 10 if rng.random() < 0.6 else 5))
        elif ac == "N39.0" and rng.random() < 0.85:
            self.acute_rx.append((i, d, "NITROFURANTOIN", npi, 5))
        elif ac == "M54.9":
            if rng.random() < 0.35:
                self.acute_rx.append((i, d, "CYCLOBENZAPRINE", npi, 10))
            if rng.random() < 0.12:
                self.acute_rx.append((i, d, rng.choice(["HYDROCODONE", "TRAMADOL"]), npi, 5))
            if rng.random() < 0.18 and age >= 16:
                self.pt_episode(i, d + timedelta(days=int(rng.integers(5, 20))), npi, "M54.9")
            if rng.random() < 0.06 and age >= 18:
                self.imaging(i, d + timedelta(days=int(rng.integers(3, 20))), "72148", npi, ["M54.9"])
        elif ac == "S93.401A":
            if rng.random() < 0.5:
                self.imaging(i, d, "73562", npi, [ac])
            if rng.random() < 0.25 and self.ptype(i, mm) != NONE:
                self.dme(i, d, "E0114", npi, [ac], rentals=1)
        elif ac == "R10.9" and rng.random() < 0.10 and age >= 18:
            self.imaging(i, d + timedelta(days=int(rng.integers(1, 10))), "74177", npi, [ac])
        elif ac == "G47.33" and age >= 25:
            self.sleep_apnea(i, d, npi)
        elif ac == "U07.1" or ac == "J06.9" and d.year <= 2022 and rng.random() < 0.3:
            self.labs(i, d, npi, ["87635"], [ac])

    def spec_visit(self, i, d, mm, spec, cond_code):
        rng = self.rng
        npi = self.pref_spec(i, spec)
        foc = SPEC_DX.get(spec, [cond_code])
        dx = self.chronic_dx(i, mm, 1.0, focus=[cond_code]) + self.chronic_dx(i, mm, 0.9, focus=foc)
        extra = []
        if spec == "Cardiology" and rng.random() < 0.35:
            extra.append(self.L("93000", d=d))
        if spec == "Orthopaedic Surgery" and rng.random() < 0.3:
            extra.append(self.L("20610", d=d))
        nch = sum(self.has(i, c, mm) for c in CHRONIC_FOR_COUNT)
        tele = spec in ("Psychiatry", "Endocrinology") and rng.random() < TELE_SHARE[d.year] * 2
        self.office_visit(i, d, npi, kind="bh" if spec == "Psychiatry" else "spec", dx=dx, extra=extra if not tele else [],
                          tele=tele, referring=self.home[i], nchron=nch)
        if spec == "Orthopaedic Surgery" and rng.random() < 0.08:
            self.imaging(i, d + timedelta(days=int(rng.integers(2, 15))), "73721", npi, dx[:2])
        if spec == "Pulmonology" and rng.random() < 0.06:
            self.imaging(i, d + timedelta(days=int(rng.integers(2, 15))), "71250", npi, dx[:2])
        if spec == "Cardiology" and rng.random() < 0.06:
            self.imaging(i, d + timedelta(days=int(rng.integers(5, 20))), "78452", npi, dx[:3])
        if spec == "Cardiology" and self.has(i, "CHF", mm) and rng.random() < 0.06:
            self.imaging(i, d, "93306", npi, dx[:3])
        if spec == "Endocrinology" and mm - self.last_a1c.get(i, -99) >= 3 and rng.random() < 0.7:
            self.last_a1c[i] = mm
            self.labs(i, d, npi, ["83036", "80053"], dx[:3])

    def eye_exam(self, i, d, mm):
        rng = self.rng
        spec = "Optometry" if rng.random() < 0.6 else "Ophthalmology"
        npi = self.pref_spec(i, spec)
        retino = "E11.319" in self.dm_comp.get(i, ())
        dx = ["E11.319" if retino else "E11.9"] if self.has(i, "DIAB", mm) else ["Z01.00"]
        lines = [self.L("92014", d=d)]
        if rng.random() < 0.5:
            lines.append(self.L("92250", d=d))
        if self.has(i, "DIAB", mm) and rng.random() < 0.45:
            lines.append(self.L("2022F" if retino else "2023F", d=d))
        self.e.submit(i, "Professional", "Office", d, d, npi, lines, dx, category="eye", rendering=npi, pos="11")

    def colon_screen(self, i, d, mm):
        rng = self.rng
        u = rng.random()
        npi = self.home[i] or self.pcp_for(i)
        if u < 0.55:
            self.labs(i, d, npi, ["82274"], ["Z12.11"], preventive=True)
        elif u < 0.75:
            self.labs(i, d, npi, ["81528"], ["Z12.11"], preventive=True)
        else:
            gi = self.pref_spec(i, "Gastroenterology")
            code = "45380" if rng.random() < 0.4 else "45378"
            self.colon_done.add(i)
            if self.system.get(gi) == SYSTEM:
                self.e.submit(i, "Institutional", "Outpatient Hospital", d, d, self.srmc,
                              [self.L(code, d=d, rev="0750", rate=780)], ["Z12.11"], category="proc",
                              attending=gi, facility=self.srmc, bill_type="131", pos="22", preventive=True)
                pos = "22"
            else:
                pos = "11"
            self.e.submit(i, "Professional", "Outpatient Hospital" if pos == "22" else "Office", d, d, gi,
                          [self.L(code, d=d)], ["Z12.11", "Z12.12"], category="proc", rendering=gi, pos=pos,
                          preventive=True)

    def pt_episode(self, i, start, referring, dx_code):
        rng = self.rng
        fraud = rng.random() < 0.18 and len(self.pt_fraud)
        npi = rng.choice(self.pt_fraud) if fraud else rng.choice(self.pt_good)
        n_vis = int(rng.integers(24, 46)) if fraud else int(rng.integers(5, 13))
        step = 2.3 if fraud else 7
        for v in range(n_vis):
            d = start + timedelta(days=int(v * step + rng.integers(0, 2)))
            if not self.active(i, d):
                break
            self.e.pt_visits[(i, d.year)] += 1
            if v == 0:
                lines = [self.L("97161", d=d), self.L("97110", 2, d=d)]
            elif fraud:
                lines = [self.L("97110", 4, d=d, mod1="GP"), self.L("97140", 3, d=d, mod1="GP"),
                         self.L("97112", 2, d=d, mod1="GP"), self.L("97530", 2, d=d, mod1="GP")]
            else:
                lines = [self.L("97110", 2, d=d, mod1="GP"), self.L("97140", 1, d=d, mod1="GP")]
            self.e.submit(i, "Professional", "Office", d, d, npi, lines, [dx_code], category="pt", rendering=npi,
                          referring=referring, pos="11", med_nec_risk=0.01)

    def therapy_series(self, i, start, mm):
        rng = self.rng
        if i in self.lcsw_panel:
            npi, n, step = self.lcsw_fraud, int(rng.integers(10, 20)), 7
        else:
            npi, n, step = rng.choice(self.lcsw_good), int(rng.integers(4, 12)), 10
        dxc = self.chronic_dx(i, mm, 1.0, focus=["DEPR"]) or ["F32.9"]
        for v in range(n):
            d = start + timedelta(days=int(v * step))
            if npi == self.lcsw_fraud:
                d = d + timedelta(days=(1 - d.weekday()) % 7)  # crowd onto Tuesdays
            if not self.active(i, d):
                break
            code = "90837" if (npi == self.lcsw_fraud or rng.random() < 0.4) else "90834"
            tele = rng.random() < TELE_SHARE[d.year] * 2.5
            self.e.submit(i, "Professional", "Telehealth" if tele else "Office", d, d, npi,
                          [self.L(code, d=d, mod1="95" if tele else None)], dxc, category="bh", rendering=npi,
                          pos=("10" if tele else "11"))

    def dme(self, i, d, code, ordering, dx, rentals=1, supplier=None):
        rng = self.rng
        sup = supplier or rng.choice(self.dme_good)
        ptype, pidx, _ = self.e.coverage(i, d)
        pa_id, ok = None, True
        if PROCEDURES[code][4] and pidx >= 0 and self.e.P.requires_prior_auth[pidx]:
            pa_id, ok, dec = self.e.request_pa(i, d - timedelta(days=5), code, PROCEDURES[code][0], ordering, sup, pidx)
            if not ok and rng.random() < 0.8:
                return
        for k in range(rentals):
            dd = d + timedelta(days=30 * k)
            if not self.active(i, dd):
                break
            mod = "RR" if rentals > 1 else "NU"
            self.e.submit(i, "Professional", "Home / DME", dd, dd, sup, [self.L(code, d=dd, mod1=mod)], dx,
                          category="dme", rendering=sup, referring=ordering, pos="12",
                          pa_needed=PROCEDURES[code][4], pa_id=pa_id, pa_approved=ok)

    def sleep_apnea(self, i, d, npi):
        rng = self.rng
        if (i, "OSA") in self.pref:
            return
        self.pref[(i, "OSA")] = 1
        pul = self.pref_spec(i, "Pulmonology")
        d2 = d + timedelta(days=int(rng.integers(14, 40)))
        if not self.active(i, d2):
            return
        self.imaging(i, d2, "95810", pul, ["G47.33"])
        if rng.random() < 0.7:
            self.dme(i, d2 + timedelta(days=14), "E0601", pul, ["G47.33"], rentals=10)

    def snf_stay(self, i, start, days, hosp):
        rng = self.rng
        snf = rng.choice(self.snf_npis)
        end = start + timedelta(days=days)
        if self.death[i] and end > self.death[i]:
            end = self.death[i]
            days = max((end - start).days, 1)
        lines = [self.L(None, units=days, d=start, rev="0022", rate=560)]
        dx = self.chronic_dx(i, mindex(start), 0.95)[:6]
        self.e.submit(i, "Institutional", "SNF", start, end, snf, lines, ["R26.89"] + dx, category="snf",
                      facility=snf, bill_type="211", pos="31", admit=start, discharge=end, los=days,
                      admit_type="Elective", dstatus="01")

    # ------------------------------------------------------------------ ED / inpatient
    def ed_visit(self, i, d, mm, dx, severity=None, hosp=None):
        rng = self.rng
        hosp = hosp or self.pref_hosp(i)
        ed_docs, _ = self.hosp_docs[hosp]
        doc = rng.choice(ed_docs)
        lvl = severity or rng.choice(["99282", "99283", "99284", "99285"], p=[0.12, 0.38, 0.35, 0.15])
        lines = [self.L(lvl, d=d, rev="0450", rate=ED_FACILITY_RATE[lvl])]
        if lvl in ("99284", "99285") or rng.random() < 0.3:
            lines += [self.L("80053", d=d, rev="0300", rate=16), self.L("85025", d=d, rev="0300", rate=12)]
        if dx[0] in ("R07.9", "R55", "I48.91", "I50.23"):
            lines.append(self.L("93000", d=d, rev="0730", rate=60))
            lines.append(self.L("71046", d=d, rev="0320", rate=60))
        elif dx[0] in ("R10.9",) and rng.random() < 0.5:
            lines.append(self.L("74177", d=d, rev="0350", rate=400))
        elif dx[0] in ("S01.81XA", "R55") and rng.random() < 0.4:
            lines.append(self.L("70450", d=d, rev="0350", rate=200))
        elif dx[0] in ("J18.9", "J44.1", "J45.901", "U07.1") and rng.random() < 0.6:
            lines.append(self.L("71046", d=d, rev="0320", rate=60))
        alldx = dx + self.chronic_dx(i, mm, 0.5)
        self.e.submit(i, "Institutional", "Emergency", d, d, hosp, lines, alldx, category="ed_fac", attending=doc,
                      facility=hosp, bill_type="131", pos="23", med_nec_risk=0.004)
        self.e.submit(i, "Professional", "Emergency", d, d, doc, [self.L(lvl, d=d)], alldx[:4], category="ed_prof",
                      rendering=doc, pos="23")
        if dx[0] in ("J06.9", "J02.9", "N39.0", "J45.901", "J44.1") and rng.random() < 0.5:
            drug = {"N39.0": "NITROFURANTOIN", "J45.901": "PREDNISONE", "J44.1": "PREDNISONE"}.get(dx[0], "AMOXICILLIN")
            self.acute_rx.append((i, d, drug, doc, 5))
        if dx[0] in ("K52.9", "R10.9") and rng.random() < 0.5:
            self.acute_rx.append((i, d, "ONDANSETRON", doc, 5))
        if dx[0] in ("S93.401A", "S01.81XA", "M54.9") and rng.random() < 0.2:
            self.acute_rx.append((i, d, "OXYCODONE5", doc, 3))

    def ed_dx(self, i, mm):
        rng = self.rng
        opts = [("R07.9", 0.10), ("R10.9", 0.12), ("J06.9", 0.08), ("N39.0", 0.07), ("M54.9", 0.07), ("S93.401A", 0.08),
                ("S01.81XA", 0.07), ("K52.9", 0.06), ("R55", 0.04), ("E86.0", 0.03), ("J18.9", 0.03)]
        if self.has(i, "ASTH", mm):
            opts.append(("J45.901", 0.20))
        if self.has(i, "COPD", mm):
            opts.append(("J44.1", 0.25))
        if self.has(i, "CHF", mm):
            opts.append(("I50.23", 0.15))
        if self.has(i, "AFIB", mm):
            opts.append(("I48.91", 0.10))
        if self.has(i, "DEPR", mm):
            opts.append(("F33.2", 0.04))
        if START_YEAR + mm // 12 <= 2022:
            opts.append(("U07.1", 0.06))
        c, w = zip(*opts)
        w = np.array(w)
        return [c[rng.choice(len(c), p=w / w.sum())]]

    def ip_reason(self, i, mm):
        rng = self.rng
        opts = [("PNEUMONIA", 0.18), ("SEPSIS", 0.12), ("UTI", 0.08), ("GI", 0.10), ("BACK", 0.04), ("AMI", 0.06),
                ("STROKE", 0.05)]
        for c, r, w in (("CHF", "CHF", 0.9), ("COPD", "COPD", 0.6), ("AFIB", "AFIB", 0.3), ("CKD", "RENAL", 0.25),
                        ("DIAB", "DIAB", 0.15), ("DEPR", "PSYCH", 0.06), ("OUD", "OVERDOSE", 0.3), ("CAD", "AMI", 0.25)):
            if self.has(i, c, mm):
                opts.append((r, w))
        c, w = zip(*opts)
        w = np.array(w)
        return c[rng.choice(len(c), p=w / w.sum())]

    def inpatient(self, i, admit_d, reason, *, hosp=None, admit_type="Emergency", via_ed=True, depth=0,
                  terminal=False, pa=None):
        rng = self.rng
        if not self.active(i, admit_d):
            return None
        mm = mindex(admit_d)
        hosp = hosp or self.pref_hosp(i)
        _, hms = self.hosp_docs[hosp]
        hm = rng.choice(hms)
        variants = ADMIT_REASONS[reason]
        sev = 1 / (1 + math.exp(-(self.fr[i] - 0.2)))
        k = 0 if (len(variants) == 1 or rng.random() < 0.3 + 0.4 * sev) else int(rng.integers(1, len(variants)))
        drg, pdx, mlos = variants[k]
        los = max(1, int(round(rng.gamma(2.5, mlos / 2.5))))
        if reason in ("TKA", "DELIVERY"):
            los = max(1, int(round(rng.normal(mlos, 0.6))))
        disch = admit_d + timedelta(days=los)
        dstatus = "01"
        age = self.age(i, mm)
        if terminal or (self.death[i] and self.death[i] <= disch):
            if self.death[i]:
                disch = max(self.death[i], admit_d)
                los = max((disch - admit_d).days, 1)
            dstatus = "20"
        elif age >= 70 and los >= 3 and rng.random() < 0.28:
            dstatus = "03"
        elif rng.random() < 0.12:
            dstatus = "06"
        elif rng.random() < 0.02:
            dstatus = "07"
        if disch > END_DATE:
            return None
        dx = [pdx] + self.chronic_dx(i, mm, 0.92)
        if reason == "COVID":
            dx.insert(1, "J18.9")
        lines = [self.L(None, los, admit_d, rev="0120", rate=950),
                 self.L(None, los, admit_d, rev="0250", rate=320),
                 self.L(None, los, admit_d, rev="0300", rate=140),
                 self.L(None, 1, admit_d, rev="0270", rate=260),
                 self.L(None, 1, admit_d, rev="0320", rate=180)]
        if k == 0 and DRGS[drg][1] > 1.1:
            lines.append(self.L(None, min(los, 2), admit_d, rev="0200", rate=1800))
        if reason in ("COPD", "PNEUMONIA", "COVID"):
            lines.append(self.L(None, los, admit_d, rev="0410", rate=210))
        if reason in ("TKA", "AMPUT") or drg == "247":
            lines += [self.L(None, 1, admit_d, rev="0360", rate=3200), self.L(None, 1, admit_d, rev="0370", rate=700),
                      self.L(None, 1, admit_d, rev="0710", rate=450)]
        if reason == "DELIVERY":
            lines.append(self.L(None, 1, admit_d, rev="0720", rate=1300))
        if via_ed:
            lines.append(self.L("99284", 1, admit_d, rev="0450", rate=ED_FACILITY_RATE["99284"]))
        mnr = 0.0 if reason in ("TKA", "DELIVERY") else (0.06 if los <= 2 else 0.018)
        pa_id, pa_ok = (pa if pa else (None, True))
        acct_cid = self.e.submit(i, "Institutional", "Inpatient", admit_d, disch, hosp, lines, dx, category="ip_fac",
                                 attending=hm, facility=hosp, bill_type="111", pos="21", drg=drg, admit=admit_d,
                                 discharge=disch, admit_type=admit_type, dstatus=dstatus, los=los,
                                 pa_needed=reason == "TKA", pa_id=pa_id, pa_approved=pa_ok, med_nec_risk=mnr)
        # professional claims
        if via_ed:
            ed_docs, _ = self.hosp_docs[hosp]
            ed = rng.choice(ed_docs)
            self.e.submit(i, "Professional", "Emergency", admit_d, admit_d, ed, [self.L("99285", d=admit_d)], dx[:4],
                          category="ed_prof", rendering=ed, pos="23")
        if reason not in ("DELIVERY",):
            pl = [self.L("99223", d=admit_d)]
            for k2 in range(1, min(los, 12)):
                pl.append(self.L("99232", d=admit_d + timedelta(days=k2)))
            if dstatus != "20":
                pl.append(self.L("99239", d=disch))
            self.e.submit(i, "Professional", "Inpatient", admit_d, disch, hm, pl, dx[:6], category="ip_prof",
                          rendering=hm, pos="21")
        if reason == "TKA":
            ortho = self.pref_spec(i, "Orthopaedic Surgery")
            self.e.submit(i, "Professional", "Inpatient", admit_d, admit_d, ortho, [self.L("27447", d=admit_d)], dx[:3],
                          category="ip_prof", rendering=ortho, pos="21", pa_needed=True, pa_id=pa_id, pa_approved=pa_ok)
            self.acute_rx.append((i, disch, "OXYCODONE5", ortho, 7))
        if reason == "AMPUT":
            pod = self.pref_spec(i, "Podiatry")
            self.e.submit(i, "Professional", "Inpatient", admit_d, admit_d, pod, [self.L("28820", d=admit_d)], dx[:3],
                          category="ip_prof", rendering=pod, pos="21")
            self.dm_comp[i].add("E11.51")
        if reason == "DELIVERY":
            ob = rng.choice(self.ob)
            self.e.submit(i, "Professional", "Inpatient", admit_d, disch, ob, [self.L("59400", d=admit_d)],
                          ["O80", "Z37.0"], category="ip_prof", rendering=ob, pos="21")
        if reason == "OVERDOSE":
            self.acute_rx.append((i, disch, "NALOXONE", hm, 1))
        if dstatus in ("20",):
            return disch
        # ---------------- post-discharge: transitional care, follow-up, readmission
        if reason in ("DELIVERY", "TKA"):
            if reason == "TKA":
                self.pt_episode(i, disch + timedelta(days=int(rng.integers(3, 10))), self.home[i] or hm, "Z96.651")
            return disch
        nch = sum(self.has(i, c, mm) for c in CHRONIC_FOR_COUNT)
        ptype = self.ptype(i, mm)
        base_logit = (-2.75 + 0.35 * self.fr[i] + 0.16 * min(nch, 6) + 0.30 * self.adi_z[i] + 0.35 * (age >= 75)
                      + 0.35 * self.has(i, "CHF", mm) + 0.25 * self.has(i, "COPD", mm)
                      + 0.30 * (ptype in (MCD_FFS, MCD_MC)) + 0.25 * (dstatus == "07"))
        enrolled = False
        if hosp in self.sys_hosp and disch >= TCP_LAUNCH and dstatus in ("01", "06"):
            observable_logit = base_logit - 0.35 * self.fr[i]
            risk_z = (observable_logit + 1.9) / 0.6
            enrolled = rng.random() < sigmoid(0.1 + 0.9 * risk_z)
            if enrolled:
                self.n_cm += 1
                self.care_mgmt.append(dict(cm_enrollment_id=f"CM{self.n_cm:07d}", member_id=self.m.member_id.values[i],
                                           program_name="Transitional Care Program", program_sponsor="Understory Health",
                                           enrollment_date=disch, end_date=disch + timedelta(days=30),
                                           referral_source="Inpatient care team", index_claim_id=acct_cid))
        h = self.home[i]
        p_fu = sigmoid(-0.5 + 0.7 * self.q(h) + 0.3 * self.care[i]) if h is not None else 0.12
        if enrolled:
            p_fu = min(p_fu + 0.30, 0.97)
        fu = rng.random() < p_fu
        fu_day = int(rng.integers(2, 8))
        if fu and self.active(i, disch + timedelta(days=fu_day)) and ptype != NONE:
            npi = h or self.pcp_for(i)
            em = "99495" if (self.aco.get(npi) and rng.random() < 0.6) else "99214"
            self.office_visit(i, disch + timedelta(days=fu_day), npi, dx=[pdx] + self.chronic_dx(i, mm, 0.9), em=em,
                              nchron=nch)
        logit = base_logit - 0.45 * fu + (math.log(TCP_TRUE_OR) if enrolled else 0.0)
        p_readmit = sigmoid(logit)
        readmit = rng.random() < p_readmit and depth < 3
        self.truth_ip.append(dict(member_id=self.m.member_id.values[i], index_claim_id=acct_cid, discharge_date=disch,
                                  hospital_npi=hosp, tcp_enrolled=int(enrolled), followup_7d=int(fu),
                                  true_readmit_probability=round(p_readmit, 4), true_baseline_logit=round(base_logit, 4)))
        if dstatus == "03":
            ptn = self.ptype(i, mm)
            if not (ptn == MCR_FFS and los < 3):
                self.snf_stay(i, disch, int(rng.integers(10, 30)), hosp)
        if readmit:
            rd = disch + timedelta(days=int(min(max(rng.exponential(9) + 1, 1), 30)))
            r2 = reason if rng.random() < 0.5 else self.ip_reason(i, mm)
            h2 = hosp if rng.random() < 0.75 else None
            self.inpatient(i, rd, r2, hosp=h2, depth=depth + 1)
        return disch

    # ------------------------------------------------------------------ diabetes complications
    def dm_complication(self, i, d, mm, hypo=False):
        rng = self.rng
        if hypo:
            kind = "Hypoglycemia"
            if rng.random() < 0.7:
                self.ed_visit(i, d, mm, ["E11.649", "E16.2"], severity="99284")
            else:
                self.inpatient(i, d, "HYPOGLY")
        else:
            kind = rng.choice(["Hyperglycemic crisis", "Foot ulcer", "Retinopathy", "Nephropathy", "Neuropathy"],
                              p=[0.18, 0.25, 0.22, 0.20, 0.15])
            if kind == "Hyperglycemic crisis":
                self.inpatient(i, d, "DIAB")
            elif kind == "Foot ulcer":
                self.dm_comp[i].add("E11.621")
                if rng.random() < 0.15:
                    self.inpatient(i, d, "AMPUT")
                else:
                    pod = self.pref_spec(i, "Podiatry")
                    for k in range(int(rng.integers(1, 5))):
                        dd = d + timedelta(days=14 * k)
                        if not self.active(i, dd):
                            break
                        self.e.submit(i, "Professional", "Office", dd, dd, pod,
                                      [self.L("99213", d=dd), self.L("11042", d=dd)], ["E11.621", "L97.509"],
                                      category="office_spec", rendering=pod, pos="11")
            elif kind == "Retinopathy":
                self.dm_comp[i].add("E11.319")
                self.eye_exam(i, d, mm)
            elif kind == "Nephropathy":
                self.dm_comp[i].add("E11.22")
                if self.on["CKD"][i] >= NO_ONSET:
                    self.on["CKD"][i] = mm
                    self.cond["ckd_stage"][i] = "3a"
                self.labs(i, d, self.home[i] or self.pcp_for(i), ["82043", "82570", "80053"], ["E11.22"])
            else:
                self.dm_comp[i].add("E11.42")
                self.office_visit(i, d, self.home[i] or self.pcp_for(i), dx=["E11.42"], nchron=2)
                self.acute_rx.append((i, d, "GABAPENTIN", self.home[i] or self.pcp_for(i), 30))
        self.truth_dm.append(dict(member_id=self.m.member_id.values[i], event_date=d, complication_type=kind))

    # ------------------------------------------------------------------ yearly schedule
    def schedule_year(self, i, mm0):
        rng = self.rng
        y = START_YEAR + mm0 // 12
        months_left = 12 - mm0 % 12
        ptype = self.ptype(i, mm0)
        age = self.age(i, mm0)
        h = self.home[i]
        qv = self.q(h) if h is not None else -0.6
        pay = {NONE: 0.15, MCD_FFS: 0.8, MCD_MC: 0.9}.get(ptype, 1.0)
        plan = []

        def when():
            return mm0 + int(rng.integers(0, months_left))

        if age < 18:
            p_prev = 0.62
        elif ptype in (MA, MCR_FFS):
            p_prev = 0.52 if ptype == MA else 0.38
        else:
            p_prev = 0.40
        if rng.random() < p_prev * pay * sigmoid(0.5 + 0.8 * qv + 0.6 * self.care[i]) * 1.6:
            plan.append((when(), "preventive"))
        if self.sex[i] == "F" and 50 <= age <= 74 and rng.random() < sigmoid(0.0 + 0.8 * qv + 0.3 * self.care[i]) * pay * 1.05:
            plan.append((when(), "mammogram"))
        if 45 <= age <= 75 and i not in self.colon_done and rng.random() < sigmoid(-1.4 + 0.6 * qv) * pay:
            plan.append((when(), "colon"))
        if self.has(i, "DIAB", mm0 + months_left - 1):
            ccm = self.ccm_until.get(i, -1) >= mm0
            if rng.random() < sigmoid(-0.4 + 0.8 * qv + 0.7 * ccm + 0.2 * self.care[i]) * pay:
                plan.append((when(), "eye"))
        for mmx, kind in plan:
            self.yearplan[mmx].append((i, kind))

    # ------------------------------------------------------------------ main loop
    def run(self):
        rng = self.rng
        on = self.on
        st = self.cov["st"]
        n = self.n
        enter = self.m._enter_m.values
        has_pcp = np.array([h is not None for h in self.home])
        # fraud panel: therapist's patients are members with depression in her area
        dep = np.where(on["DEPR"] < NO_ONSET)[0]
        self.lcsw_panel = set(rng.choice(dep, size=min(90, len(dep)), replace=False).tolist())
        for mm in range(N_MONTHS):
            pres = self.cov["present"][mm]
            idx = np.where(pres)[0]
            age = age_at(self.birth[idx], mm)
            act = {c: on[c][idx] <= mm for c in on}
            nch = sum(act[c].astype(int) for c in CHRONIC_FOR_COUNT)
            pt = st[mm, idx]
            care = np.exp(0.6 * self.care[idx])  # persistent care-seeking: heavy users stay heavy users
            payf = np.select([pt == NONE, np.isin(pt, [MCD_FFS, MCD_MC])], [0.4, 0.9], 1.0)
            hp = has_pcp[idx]
            # yearly schedules
            sched = idx[(mm % 12 == 0) | (enter[idx] == mm)]
            for i in sched:
                self.schedule_year(int(i), mm)
            lam_pcp = (0.055 + 0.045 * np.minimum(nch, 6) + 0.12 * (age < 2) + 0.03 * (age >= 65)) * care * payf * np.where(hp, 1, 0.45)
            lam_ed = 1.3 * ((0.010 + 0.005 * nch + 0.010 * act["ASTH"] * (age < 18) + 0.012 * act["COPD"] + 0.006 * act["CHF"]
                       + 0.008 * act["OUD"]) * self.zrisk[idx] * np.where(hp, 1, 1.5)
                      * np.select([np.isin(pt, [MCD_FFS, MCD_MC]), pt == NONE, np.isin(pt, [MCR_FFS, MA])], [1.6, 1.35, 1.1], 1.0)
                      * np.exp(0.15 * self.care[idx]))
            agef = np.select([age < 18, age < 45, age < 65, age < 75], [0.4, 0.8, 1.3, 2.5], 4.0)
            lam_ip = ((0.0010 * agef + 0.010 * act["CHF"] + 0.006 * act["COPD"] + 0.002 * act["DIAB"] + 0.003 * act["CKD"]
                       + 0.004 * act["DEMEN"] + 0.002 * act["AFIB"] + 0.002 * act["CAD"] + 0.003 * act["OUD"])
                      * np.exp(0.4 * self.fr[idx]) * self.zrisk[idx] ** 0.6 * np.where(pt == NONE, 0.8, 1.0))
            wave = {0: 0.0015, 1: 0.0010, 7: 0.0040, 8: 0.0030, 12: 0.0030, 13: 0.0015, 19: 0.0008, 31: 0.0006}.get(mm, 0.0001)
            lam_cov = wave * np.where(age >= 65, 3.0, 0.5) * np.exp(0.3 * self.fr[idx])
            n_pcp = rng.poisson(lam_pcp)
            n_ed = rng.poisson(lam_ed)
            n_ip = rng.poisson(lam_ip)
            n_cov = rng.poisson(lam_cov)
            spec_events = []
            for c, s, lam in SPEC_LAMBDA:
                rate = lam * act[c] * care * np.where(pt == NONE, 0.3, 1.0)
                if c == "CKD":
                    rate = rate * np.isin(self.cond["ckd_stage"][idx], ["3b", "4", "5"]) * 2.5
                hit = idx[rng.random(len(idx)) < rate]
                spec_events += [(int(i), s, c) for i in hit]
            dep_hit = idx[(rng.random(len(idx)) < 0.025 * act["DEPR"] * care * (pt != NONE))]
            tka = idx[(rng.random(len(idx)) < 0.0025 * act["KNEEOA"] * (age >= 50) * (age < 86) * (pt != NONE))]
            deliv = idx[(rng.random(len(idx)) < 0.0045 * (self.sex[idx] == "F") * (age >= 18) * (age <= 42))]
            od = idx[(rng.random(len(idx)) < 0.004 * act["OUD"])]
            flu = idx[(mm % 12 in (8, 9, 10)) & (rng.random(len(idx)) < np.where(age >= 65, 0.22, 0.09) * hp * (pt != NONE))]
            # diabetes complications
            dm = idx[act["DIAB"]]
            if len(dm):
                a1c = np.array([self.a1c_val(int(i), START_YEAR + mm // 12) for i in dm])
                lo = 0  # any coverage gap since the start of the period
                churn = (st[lo:mm + 1, dm] == NONE).any(axis=0) & pres[dm]
                ccm = np.array([self.ccm_until.get(int(i), -1) >= mm for i in dm])
                h = (0.0030 * np.exp(0.80 * (a1c - 7.5) + 0.12 * self.adi_z[dm] + 0.70 * churn + 0.70 * (~has_pcp[dm])
                                     + 0.25 * self.fr[dm]) * self.zrisk[dm] ** 0.4 * np.where(ccm, CCM_HAZARD_RR, 1.0))
                comp = dm[rng.random(len(dm)) < h]
                agedm = age_at(self.birth[dm], mm)
                su = np.array([on_drug(self.reg, int(i), {"GLIPIZIDE"}, mm) for i in dm])
                hh = 0.0045 * su * (agedm >= 75) * (1 + 0.5 * (on["CKD"][dm] <= mm))
                hypo = dm[rng.random(len(dm)) < hh]
                # complex case management enrolment (plan-sponsored; MA + Medicaid MC)
                if mm >= CCM_START_M:
                    ptd = st[mm, dm]
                    elig = np.isin(ptd, [MA, MCD_MC]) & ~ccm & ((a1c > 8.5) | np.array([len(self.dm_comp.get(int(i), ())) > 0 for i in dm]))
                    newcm = dm[elig & (rng.random(len(dm)) < 0.04)]
                    for i in newcm:
                        i = int(i)
                        dur = int(rng.integers(6, 19))
                        self.ccm_until[i] = mm + dur
                        self.n_cm += 1
                        d0 = rday(rng, mm)
                        pidx = int(self.cov["plan"][mm, i])
                        self.care_mgmt.append(dict(cm_enrollment_id=f"CM{self.n_cm:07d}", member_id=self.m.member_id.values[i],
                                                   program_name="Diabetes Complex Case Management",
                                                   program_sponsor=self.e.P.plan_name[pidx], enrollment_date=d0,
                                                   end_date=min(d0 + timedelta(days=30 * dur), END_DATE),
                                                   referral_source=rng.choice(["Claims-based risk model", "Provider referral",
                                                                               "Hospital discharge"], p=[0.6, 0.3, 0.1]),
                                                   index_claim_id=None))
            else:
                comp, hypo = [], []
            # ---- process events
            for k in np.where(n_pcp > 0)[0]:
                i = int(idx[k])
                for _ in range(min(int(n_pcp[k]), 4)):
                    d = rday(rng, mm)
                    if self.active(i, d):
                        self.pcp_visit(i, d, mm, int(nch[k]))
            for mmx_i, kind in self.yearplan.pop(mm, []):
                i = mmx_i
                d = rday(rng, mm)
                if not self.active(i, d):
                    continue
                if kind == "preventive":
                    self.pcp_visit(i, d, mm, 0, preventive=True)
                elif kind == "mammogram":
                    self.imaging(i, d, "77067", self.home[i] or self.pcp_for(i), ["Z12.31"], preventive=True)
                elif kind == "colon":
                    self.colon_screen(i, d, mm)
                elif kind == "eye":
                    self.eye_exam(i, d, mm)
            for i, s, c in spec_events:
                d = rday(rng, mm)
                if self.active(i, d):
                    self.spec_visit(i, d, mm, s, c)
            for i in dep_hit:
                i = int(i)
                d = rday(rng, mm)
                if self.active(i, d):
                    self.therapy_series(i, d, mm)
            for k in np.where(n_ed > 0)[0]:
                i = int(idx[k])
                d = rday(rng, mm)
                if not self.active(i, d):
                    continue
                dx = self.ed_dx(i, mm)
                if dx[0] in ("J44.1", "I50.23", "J18.9") and rng.random() < 0.25:
                    self.inpatient(i, d, {"J44.1": "COPD", "I50.23": "CHF", "J18.9": "PNEUMONIA"}[dx[0]])
                else:
                    self.ed_visit(i, d, mm, dx)
            for k in np.where(n_ip > 0)[0]:
                i = int(idx[k])
                d = rday(rng, mm)
                self.inpatient(i, d, self.ip_reason(i, mm))
            for k in np.where(n_cov > 0)[0]:
                i = int(idx[k])
                self.inpatient(i, rday(rng, mm), "COVID")
            for i in tka:
                i = int(i)
                d = rday(rng, mm)
                if not self.active(i, d):
                    continue
                ortho = self.pref_spec(i, "Orthopaedic Surgery")
                ptype_, pidx, _ = self.e.coverage(i, d)
                pa = None
                if pidx >= 0 and self.e.P.requires_prior_auth[pidx]:
                    if rng.random() < 0.92:
                        pa_id, ok, dec = self.e.request_pa(i, d - timedelta(days=int(rng.integers(10, 30))), "27447",
                                                           PROCEDURES["27447"][0], ortho, self.pref_hosp(i), pidx,
                                                           urgency="Standard")
                        if not ok and rng.random() < 0.85:
                            continue
                        pa = (pa_id, ok)
                    else:
                        pa = (None, True)
                self.inpatient(i, d, "TKA", hosp=self.pref_hosp(i), admit_type="Elective", via_ed=False, pa=pa)
            for i in deliv:
                i = int(i)
                self.inpatient(int(i), rday(rng, mm), "DELIVERY", admit_type="Urgent", via_ed=False)
            for i in od:
                i = int(i)
                d = rday(rng, mm)
                if not self.active(i, d):
                    continue
                if rng.random() < 0.3:
                    self.inpatient(i, d, "OVERDOSE")
                else:
                    self.ed_visit(i, d, mm, ["T40.2X1A", "F11.20"], severity="99285")
                    self.acute_rx.append((i, d, "NALOXONE", self.home[i] or self.pcp_for(i), 1))
            for i in flu:
                i = int(i)
                if (i, mm // 12) in self.flu:
                    continue
                d = rday(rng, mm)
                if self.active(i, d):
                    self.flu.add((i, mm // 12))
                    npi = self.home[i]
                    self.e.submit(i, "Professional", "Office", d, d, npi,
                                  [self.L("90686", d=d), self.L("G0008", d=d)],
                                  ["Z23"], category="preventive", rendering=npi, pos="11", preventive=True)
            for i in comp:
                d = rday(rng, mm)
                if self.active(int(i), d):
                    self.dm_complication(int(i), d, mm)
            for i in hypo:
                d = rday(rng, mm)
                if self.active(int(i), d):
                    self.dm_complication(int(i), d, mm, hypo=True)
            # chronic DME: home oxygen for severe COPD
            for i in idx[act["COPD"] & (self.fr[idx] > 1.0)]:
                i = int(i)
                if i not in self.oxygen and rng.random() < 0.02:
                    self.oxygen.add(i)
                    self.dme(i, rday(rng, mm), "E1390", self.pref_spec(i, "Pulmonology"), ["J44.9"], rentals=36)
            # terminal hospitalisations
            dying = [int(i) for i in idx if self.death[int(i)] is not None and mindex(self.death[int(i)]) == mm]
            for i in dying:
                if rng.random() < 0.38:
                    dd = self.death[i]
                    start = dd - timedelta(days=int(rng.integers(1, 9)))
                    if mindex(start) >= 0 and self.active(i, start):
                        self.inpatient(i, start, self.ip_reason(i, mm), terminal=True)
            # newborn hospital stay
            for i in idx[(enter[idx] == mm) & (self.m._entry_kind.values[idx] == "newborn")]:
                i = int(i)
                bd = pd.Timestamp(self.birth[i]).date()
                if not self.active(i, bd):
                    continue
                hosp = self.pref_hosp(i)
                los = 2
                self.e.submit(i, "Institutional", "Inpatient", bd, bd + timedelta(days=los), hosp,
                              [self.L(None, los, bd, rev="0170", rate=700)], ["Z38.00"], category="ip_fac",
                              facility=hosp, bill_type="111", pos="21", drg="795", admit=bd,
                              discharge=bd + timedelta(days=los), admit_type="Newborn", dstatus="01", los=los)
                ped = self.home[i] or self.pcp_for(i)
                self.e.submit(i, "Professional", "Inpatient", bd, bd, ped, [self.L("99460", d=bd)], ["Z38.00"],
                              category="ip_prof", rendering=ped, pos="21", preventive=True)
        return self

    # ------------------------------------------------------------------ fraud schemes (run after main loop)
    def run_fraud(self):
        rng = self.rng
        st = self.cov["st"]
        n = self.n
        truth = []
        medicare = lambda i, mm: st[mm, i] in (MCR_FFS, MA)
        # 1) DME: braces billed for Medicare members never seen for back/knee problems, incl. after death
        cands = [i for i in range(n) if any(medicare(i, mm) for mm in (24, 30, 36))]
        sel = rng.choice(cands, size=min(260, len(cands)), replace=False)
        for i in sel:
            i = int(i)
            for _ in range(int(rng.integers(1, 3))):
                mm = int(rng.integers(24, 45))
                d = rday(rng, mm)
                if not self.active(i, d):
                    continue
                ref = rng.choice(self.pcp_npis)
                code = rng.choice(["L0650", "L1833"])
                self.e.submit(i, "Professional", "Home / DME", d, d, self.dme_fraud, [self.L(code, d=d, mod1="NU")],
                              ["M54.9" if code == "L0650" else "M17.11"], category="dme", rendering=self.dme_fraud,
                              referring=ref, pos="12")
        dead = [i for i in range(n) if self.death[i] is not None and date(2023, 1, 1) <= self.death[i] <= date(2024, 6, 1)
                and medicare(i, mindex(self.death[i]))]
        for i in rng.choice(dead, size=min(30, len(dead)), replace=False):
            i = int(i)
            d = self.death[i] + timedelta(days=int(rng.integers(20, 120)))
            last_plan = int(self.cov["plan"][mindex(self.death[i]), i])
            self.e.submit(i, "Professional", "Home / DME", d, d, self.dme_fraud, [self.L("L0650", d=d, mod1="NU")],
                          ["M54.9"], category="dme", rendering=self.dme_fraud, referring=rng.choice(self.pcp_npis),
                          pos="12", force_plan=last_plan, attempt=1)
        # 2) Lab standing orders for Medicare members of kickback practices
        kb = [i for i in range(n) if self.home[i] is not None and self.practice[self.home[i]] in self.kickback_practices]
        for i in kb:
            if rng.random() > 0.45:
                continue
            for mm in range(14, 54, int(rng.integers(1, 3))):
                d = rday(rng, mm)
                if not self.active(i, d) or st[mm, i] == NONE:
                    continue
                self.e.submit(i, "Professional", "Laboratory", d, d, self.lab_fraud,
                              [self.L("G0483", d=d), self.L("80053", d=d), self.L("36415", d=d)], ["M54.9"],
                              category="lab", rendering=self.lab_fraud, referring=self.home[i], pos="81")
        # 3) Pill mill: monthly visits + oxycodone 30 mg
        cand = [i for i in range(n) if 22 <= self.age(i, 12) <= 62 and self.cov["present"][12, i]]
        far = np.array([haversine(self.mll[i, 0], self.mll[i, 1], 30.25, -82.95) for i in cand])
        far = np.asarray(far, dtype=float) ** 2
        w = far / far.sum()
        pm = rng.choice(cand, size=min(130, len(cand)), replace=False, p=w)
        for i in pm:
            i = int(i)
            s_m = int(rng.integers(12, 30))
            e_m = min(s_m + int(rng.integers(6, 30)), 47)
            start, end = rday(rng, s_m), rday(rng, e_m)
            self.pill_mill.append((i, start, end))
            d = start
            while d <= end:
                if self.active(i, d) and st[mindex(d), i] != NONE:
                    self.e.submit(i, "Professional", "Office", d, d, self.pain_doc,
                                  [self.L("99214" if rng.random() < 0.7 else "99215", d=d)], ["M54.9"],
                                  category="office_spec", rendering=self.pain_doc, pos="11")
                d = d + timedelta(days=int(rng.integers(26, 31)))
        return self
