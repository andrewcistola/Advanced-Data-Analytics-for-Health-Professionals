"""Monthly coverage simulation (member-month eligibility)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .reference import (PLANS, PLAN_COLS, NONE, COMM, MKT, MCD_FFS, MCD_MC, MCR_FFS, MA, N_MONTHS,
                        PAYER_TYPE_NAME, PAYER_CATEGORY, PDP_PLAN, PART_B_PREMIUM, START_YEAR, CHRONIC_FOR_COUNT)
from .population import age_at, month_start

PLAN_DF = pd.DataFrame(PLANS, columns=PLAN_COLS)
UNWIND_START, UNWIND_END = 27, 41  # Apr 2023 - Jun 2024 (Florida Medicaid unwinding)
LOB = {COMM: "Commercial", MKT: "Individual (ACA Marketplace)", MCD_FFS: "Medicaid", MCD_MC: "Medicaid",
       MCR_FFS: "Medicare", MA: "Medicare"}


def _plan_choices(ptype, dual=False):
    d = PLAN_DF[PLAN_DF.payer_type_code == ptype]
    if ptype == MA:
        if dual:
            return np.array(d.index), np.array([0.13, 0.08, 0.14, 0.65])
        d = d[d.plan_id != "OS-DSNP"]
    w = d.weight.values
    return np.array(d.index), w / w.sum()


def simulate_coverage(rng, m: pd.DataFrame, death_m: np.ndarray, cond: dict, home_pcp: np.ndarray,
                      pcp_npis: np.ndarray):
    n = len(m)
    st = np.full((N_MONTHS, n), NONE, np.int8)
    plan = np.full((N_MONTHS, n), -1, np.int16)
    dual = np.zeros((N_MONTHS, n), np.int8)        # 0 none, 1 full, 2 partial
    rx = np.zeros((N_MONTHS, n), bool)
    present = np.zeros((N_MONTHS, n), bool)
    adi_z = (m._adi.values - 60) / 20
    enter, exit_ = m._enter_m.values, m._exit_m.values
    birth = m.birth_date.values
    disabled = (m._frailty.values > 1.2) & (rng.random(n) < 0.30)
    has_pdp = rng.random(n) < 0.86
    mcd_permanent_ffs = rng.random(n) < 0.15
    mcd_ffs_months = np.zeros(n, int)
    dual_type = np.where(rng.random(n) < 0.68, 1, 2)
    dual_prob = np.clip(0.13 + 0.07 * adi_z, 0.03, 0.4)
    is_dual_elig = rng.random(n) < dual_prob

    def choose_plan(idx, ptype, dual_flag=None):
        for p in np.unique(ptype):
            sel = idx[ptype == p]
            if p == NONE or len(sel) == 0:
                continue
            if p == MA:
                for dflag in (False, True):
                    s2 = sel[(dual_flag[ptype == p] > 0) == dflag] if dual_flag is not None else sel
                    if len(s2) == 0:
                        continue
                    ids, w = _plan_choices(MA, dflag)
                    plan_out[s2] = rng.choice(ids, size=len(s2), p=w)
            else:
                ids, w = _plan_choices(p)
                plan_out[sel] = rng.choice(ids, size=len(sel), p=w)

    for mm in range(N_MONTHS):
        age = age_at(birth, mm)
        alive = (death_m < 0) | (death_m >= mm)
        pres = (enter <= mm) & (exit_ >= mm) & alive & (age >= -0.1)
        present[mm] = pres
        year = START_YEAR + mm // 12
        jan = (mm % 12 == 0)
        ma_share = 0.50 + 0.02 * (year - START_YEAR)
        new = pres & (enter == mm) if mm > 0 else pres.copy()
        cont = pres & ~new
        cur = st[mm - 1].copy() if mm > 0 else np.full(n, NONE, np.int8)
        cur_plan = plan[mm - 1].copy() if mm > 0 else np.full(n, -1, np.int16)
        cur_dual = dual[mm - 1].copy() if mm > 0 else np.zeros(n, np.int8)
        nxt = cur.copy()
        plan_out = cur_plan.copy()
        dual_out = cur_dual.copy()
        u = rng.random(n)

        # --- initialise new entrants
        idx = np.where(new)[0]
        if len(idx):
            a = age[idx]
            init = np.empty(len(idx), np.int8)
            for k, i in enumerate(idx):
                if a[k] >= 65 or disabled[i] and a[k] >= 19:
                    init[k] = MA if rng.random() < ma_share else MCR_FFS
                elif a[k] < 19:
                    p = np.array([0.07, 0.40, 0.06, 0.47 * (1 + 0.25 * adi_z[i])])
                    init[k] = [NONE, COMM, MKT, MCD_MC][rng.choice(4, p=p / p.sum())]
                else:
                    p = np.array([0.15 * (1 + 0.3 * adi_z[i]), 0.53 * (1 - 0.2 * adi_z[i]), 0.17, 0.15 * (1 + 0.4 * adi_z[i])])
                    p = np.clip(p, 0.01, None)
                    init[k] = [NONE, COMM, MKT, MCD_MC][rng.choice(4, p=p / p.sum())]
                if init[k] == MCD_MC:
                    init[k] = MCD_FFS if mcd_permanent_ffs[i] or rng.random() < 0.1 else MCD_MC
                if init[k] in (MA, MCR_FFS) and is_dual_elig[i]:
                    dual_out[i] = dual_type[i]
            nxt[idx] = init
            choose_plan(idx, init, dual_out[idx])

        # --- transitions for continuing members
        if mm > 0:
            ci = np.where(cont)[0]
            a = age[ci]
            a_prev = age_at(birth[ci], mm - 1)
            s = cur[ci]
            ns = s.copy()
            uu = u[ci]
            turning65 = (a >= 65) & (a_prev < 65)
            turning19 = (a >= 19) & (a_prev < 19)
            medicare = np.isin(s, [MCR_FFS, MA])
            # Medicaid exit hazard depends on policy period (continuous enrollment, unwinding, after)
            if mm < UNWIND_START:
                mcd_exit = np.full(len(ci), 0.0006)
            elif mm <= UNWIND_END:
                mcd_exit = np.where(a < 19, 0.022, 0.032)
            else:
                mcd_exit = np.full(len(ci), 0.009)
            ismcd = np.isin(s, [MCD_FFS, MCD_MC])
            haz = np.select(
                [s == COMM, s == MKT, ismcd, s == NONE],
                [np.full(len(ci), 0.0095), np.full(len(ci), 0.012 + (0.05 if jan else 0)), mcd_exit,
                 np.full(len(ci), 0.045 + (0.12 if jan else 0))], 0.0)
            move = (uu < haz) & ~medicare
            for k in np.where(move)[0]:
                i = ci[k]
                cs = s[k]
                if cs == COMM:
                    dest = rng.choice([NONE, MKT, MCD_MC], p=[0.62, 0.20, 0.18])
                elif cs == MKT:
                    dest = rng.choice([NONE, COMM, MCD_MC], p=[0.60, 0.28, 0.12])
                elif cs in (MCD_FFS, MCD_MC):
                    p = [0.55, 0.15, 0.30] if UNWIND_START <= mm <= UNWIND_END else [0.50, 0.30, 0.20]
                    dest = rng.choice([NONE, COMM, MKT], p=p)
                else:  # uninsured
                    p_m = 0.30 * (1 + 0.4 * adi_z[i]) * (1.6 if a[k] < 19 else 1.0)
                    p_mkt = 0.45 if jan else 0.12
                    p = np.clip(np.array([0.45, p_mkt, p_m]), 0.01, None)
                    dest = rng.choice([COMM, MKT, MCD_MC], p=p / p.sum())
                if dest == MCD_MC:
                    dest = MCD_FFS  # new Medicaid enrollees start FFS before plan selection
                    mcd_ffs_months[i] = int(rng.integers(1, 3))
                ns[k] = dest
            # child aging out of Medicaid/CHIP eligibility
            lose = turning19 & ismcd & (rng.random(len(ci)) < 0.5)
            ns[lose] = rng.choice([NONE, MKT], size=lose.sum(), p=[0.7, 0.3])
            # age into Medicare
            ns[turning65] = np.where(rng.random(turning65.sum()) < ma_share, MA, MCR_FFS)
            for k in np.where(turning65)[0]:
                i = ci[k]
                if ismcd[k] or is_dual_elig[i]:
                    dual_out[i] = dual_type[i]
            # Medicaid FFS -> managed care after initial months
            ffs = (ns == MCD_FFS) & (s == MCD_FFS)
            for k in np.where(ffs)[0]:
                i = ci[k]
                if mcd_permanent_ffs[i]:
                    continue
                mcd_ffs_months[i] -= 1
                if mcd_ffs_months[i] <= 0:
                    ns[k] = MCD_MC
            # Medicare annual election period (effective January)
            if jan:
                sw = medicare & (rng.random(len(ci)) < np.where(s == MCR_FFS, 0.06, 0.02))
                ns[sw] = np.where(s[sw] == MCR_FFS, MA, MCR_FFS)
            nxt[ci] = ns
            changed = ci[(ns != s)]
            choose_plan(changed, nxt[changed], dual_out[changed])
            # plan switching within payer type in January
            if jan:
                sw = ci[(ns == s) & np.isin(s, [COMM, MKT, MA]) & (rng.random(len(ci)) < np.where(s == MKT, 0.18, 0.08))]
                choose_plan(sw, nxt[sw], dual_out[sw])
            # Medicaid FFS -> MC plan assignment
            to_mc = ci[(ns == MCD_MC) & (s != MCD_MC)]
            choose_plan(to_mc, nxt[to_mc])
        nxt[~pres] = NONE
        plan_out[nxt == NONE] = -1
        dual_out[~np.isin(nxt, [MCR_FFS, MA])] = 0
        st[mm], plan[mm], dual[mm] = nxt, plan_out, dual_out
        rx[mm] = np.isin(nxt, [COMM, MKT, MCD_FFS, MCD_MC, MA]) | ((nxt == MCR_FFS) & (has_pdp | (dual_out > 0)))

    # assigned PCP for HMO-type plans: usually the member's home PCP, sometimes an auto-assignment
    assigned = np.array([h if (h is not None and rng.random() < 0.80) else rng.choice(pcp_npis) for h in home_pcp], object)
    return dict(st=st, plan=plan, dual=dual, rx=rx, present=present, disabled=disabled, assigned_pcp=assigned)


def coverage_table(rng, m: pd.DataFrame, cov: dict, cond: dict) -> pd.DataFrame:
    st, plan, dual, rx = cov["st"], cov["plan"], cov["dual"], cov["rx"]
    mi, mo = np.where(st.T != NONE)  # member index, month
    n = len(mi)
    ptype = st[mo, mi]
    pidx = plan[mo, mi]
    P = PLAN_DF
    age = (np.array([np.datetime64(month_start(k).date(), "D") for k in range(N_MONTHS)])[mo]
           - m.birth_date.values[mi].astype("datetime64[D]")).astype("timedelta64[D]").astype(float) / 365.25
    year = START_YEAR + mo // 12
    df = pd.DataFrame({
        "member_id": m.member_id.values[mi],
        "coverage_month": np.array([month_start(k) for k in range(N_MONTHS)])[mo],
        "coverage_year": year,
        "payer_type": [PAYER_TYPE_NAME[p] for p in ptype],
        "payer_category": [PAYER_CATEGORY[p] for p in ptype],
        "line_of_business": [LOB[p] for p in ptype],
        "plan_id": P.plan_id.values[pidx],
        "plan_name": P.plan_name.values[pidx],
        "product_type": P.product_type.values[pidx],
        "funding_type": P.funding_type.values[pidx],
        "metal_tier": P.metal_tier.values[pidx],
    })
    # relationship to subscriber
    r = rng.random(len(m))
    rel = np.where(age < 19, "Child", np.where((age < 26) & (r[mi] < 0.3), "Child", np.where(r[mi] > 0.72, "Spouse", "Self")))
    priv = np.isin(ptype, [COMM, MKT])
    df["relationship_to_subscriber"] = np.where(priv, rel, "Self")
    sub_suffix = (np.arange(len(m)) * 7919 + 1000003) % 9000000 + 1000000
    df["subscriber_id"] = np.where(df.relationship_to_subscriber == "Self", "S" + pd.Series(m.member_id.values[mi]).str[1:].values,
                                   "S" + pd.Series(sub_suffix[mi]).astype(str).values)
    med = np.isin(ptype, [MCR_FFS, MA])
    df["medicare_entitlement_reason"] = np.where(med, np.where(age >= 65, "Age", "Disability"), None)
    d = dual[mo, mi]
    df["dual_status"] = np.select([d == 1, d == 2], ["Full Benefit Dual", "Partial Dual (QMB/SLMB)"], None)
    df["secondary_payer"] = np.where(d > 0, "Medicaid", None)
    df["rx_coverage_flag"] = rx[mo, mi].astype(int)
    df["rx_plan_id"] = np.where(ptype == MCR_FFS, np.where(rx[mo, mi], PDP_PLAN[0], None), np.where(rx[mo, mi], df.plan_id, None))
    hmo = P.requires_pcp.values[pidx]
    df["assigned_pcp_npi"] = np.where(hmo, cov["assigned_pcp"][mi], None)
    # premium / capitation revenue per member month (approximate, for plan finance exercises)
    trend = 1.045 ** (year - START_YEAR)
    agef = np.select([age < 19, age < 30, age < 45, age < 55], [0.55, 0.80, 1.0, 1.35], 1.85)
    base_comm = pd.Series(P.plan_id.values[pidx]).map({"TW-PPO": 620, "TW-HMO": 540, "TW-HDHP": 470, "PB-ASO": 600}).values
    base_mkt = pd.Series(P.metal_tier.values[pidx]).map({"Bronze": 390, "Silver": 510, "Gold": 610}).values
    nchron = sum((cond["onset"][c][mi] <= mo).astype(int) for c in CHRONIC_FOR_COUNT)
    ma_pay = 1050 * (0.80 + 0.13 * np.minimum(nchron, 6)) * np.where(df.plan_id == "OS-DSNP", 1.3, 1.0)
    prem = np.select([ptype == COMM, ptype == MKT, ptype == MCD_MC, ptype == MA],
                     [base_comm * agef, base_mkt * agef * 1.1, np.where(age < 19, 215, 525), ma_pay], np.nan) * trend
    df["premium_pmpm"] = np.round(prem, 2)
    df["part_b_premium"] = np.where(med, [PART_B_PREMIUM[y] for y in year], np.nan)
    df["_mi"] = mi
    df["_mo"] = mo
    return df
