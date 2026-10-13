"""Beneficiaries, latent health traits, chronic conditions, deaths, PCP relationships."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .reference import CONDITIONS, AGE_BANDS, N_MONTHS, START_YEAR, SERIOUS
from .world import haversine

BAND_P = [0.19, 0.18, 0.16, 0.19, 0.16, 0.12]
NO_ONSET = 9999


def month_start(m: int) -> pd.Timestamp:
    return pd.Timestamp(START_YEAR + m // 12, m % 12 + 1, 1)


def rand_date_in_month(rng, m: int) -> pd.Timestamp:
    s = month_start(m)
    return s + pd.Timedelta(days=int(rng.integers(0, s.days_in_month)))


def build_members(rng, fake, zips: pd.DataFrame, n: int) -> pd.DataFrame:
    t0 = pd.Timestamp(START_YEAR, 1, 1)
    # entry month: 87% present at start, 3% newborns, 10% move in later
    kind = rng.choice(["start", "newborn", "movein"], size=n, p=[0.87, 0.03, 0.10])
    enter_m = np.where(kind == "start", 0, rng.integers(1, N_MONTHS, n))
    band = rng.choice(len(AGE_BANDS), size=n, p=BAND_P)
    lo = np.array([AGE_BANDS[b][0] for b in band])
    hi = np.array([min(AGE_BANDS[b][1], 98) for b in band])
    age0 = lo + rng.random(n) * (hi - lo + 1)
    age0 = np.where(band == 5, 75 + rng.gamma(2.0, 4.5, n), age0)  # long tail for 75+
    age0 = np.clip(age0, 0, 101)
    birth = np.array([t0 - pd.Timedelta(days=int(a * 365.25)) for a in age0])
    for i in np.where(kind == "newborn")[0]:
        birth[i] = month_start(int(enter_m[i])) + pd.Timedelta(days=int(rng.integers(0, 27)))
    # move-out (exit) month: 7% leave the region
    exit_m = np.where(rng.random(n) < 0.07, rng.integers(1, N_MONTHS, n), N_MONTHS - 1)
    exit_m = np.maximum(exit_m, enter_m)

    sex = np.where(rng.random(n) < 0.515, "F", "M")
    # zip assignment weighted by population and (for older people) share 65+
    old = age0 >= 65
    w_y = zips.population.values * (100 - zips.pct_age_65_plus.values)
    w_o = zips.population.values * zips.pct_age_65_plus.values * 1.6
    zi = np.empty(n, int)
    zi[~old] = rng.choice(len(zips), size=(~old).sum(), p=w_y / w_y.sum())
    zi[old] = rng.choice(len(zips), size=old.sum(), p=w_o / w_o.sum())
    adi = zips.area_deprivation_index.values[zi]
    adi_z = (adi - 60) / 20

    # race/ethnicity (synthetic distribution, tilted by ADI)
    re_cats = np.array(["White, non-Hispanic", "Black, non-Hispanic", "Hispanic", "Asian, non-Hispanic", "Other/Multiple"])
    base = np.array([0.58, 0.16, 0.18, 0.04, 0.04])
    race = np.empty(n, object)
    for i in range(n):
        p = base * np.array([1 - 0.08 * adi_z[i], 1 + 0.35 * adi_z[i], 1, 1 - 0.2 * adi_z[i], 1])
        p = np.clip(p, 0.005, None)
        race[i] = re_cats[rng.choice(5, p=p / p.sum())]
    lang = np.where((race == "Hispanic") & (rng.random(n) < 0.38), "Spanish",
                    np.where((race == "Black, non-Hispanic") & (rng.random(n) < 0.05), "Haitian Creole", "English"))
    first = [fake.first_name_female() if s == "F" else fake.first_name_male() for s in sex]
    last = [fake.last_name() for _ in range(n)]

    m = pd.DataFrame({
        "member_id": [f"M{100000 + i:07d}" for i in range(n)],
        "first_name": first, "last_name": last, "sex": sex,
        "birth_date": pd.to_datetime(birth), "race_ethnicity": race, "preferred_language": lang,
        "zip_code": zips.zip_code.values[zi], "county": zips.county.values[zi],
        "_zi": zi, "_enter_m": enter_m, "_exit_m": exit_m, "_entry_kind": kind,
    })
    # latent traits
    m["_frailty"] = rng.normal(0, 1, n) + 0.25 * adi_z
    m["_care_seek"] = rng.normal(0, 1, n)
    adh = rng.beta(6, 2.3, n) - 0.06 * adi_z
    m["_adherence"] = np.clip(adh, 0.08, 0.99)
    m["_zip_risk"] = zips._zip_risk.values[zi]
    m["_adi"] = adi
    return m


def age_at(birth: np.ndarray, m) -> np.ndarray:
    """Age in years at the start of month m (vectorised)."""
    ref = month_start(int(m)) if np.isscalar(m) else None
    return (np.datetime64(ref.date(), "D") - birth.astype("datetime64[D]")).astype("timedelta64[D]").astype(float) / 365.25


def assign_conditions(rng, m: pd.DataFrame) -> dict:
    n = len(m)
    birth = m.birth_date.values
    age_mid = age_at(birth, 30)
    band = np.digitize(age_mid, [18, 35, 50, 65, 75])
    fr = m._frailty.values
    adi_z = (m._adi.values - 60) / 20
    onset = {}
    has = {}
    order = ["OBES", "HTN", "HLD", "DIAB", "CAD", "CHF", "AFIB", "COPD", "ASTH", "CKD", "DEPR", "RA", "DEMEN",
             "OUD", "KNEEOA", "BRCA"]
    for c in order:
        p = np.array(CONDITIONS[c]["prev"])[band]
        odds = p / (1 - p + 1e-9)
        mult = np.exp(0.45 * fr + 0.25 * adi_z)
        if c == "DIAB":
            mult *= np.where(has["OBES"], 2.0, 0.75)
        if c == "CHF":
            mult *= np.where(has["HTN"] | has["CAD"], 1.6, 0.45)
        if c == "CKD":
            mult *= np.where(has["DIAB"] | has["HTN"], 2.2, 0.6)
        if c == "AFIB":
            mult *= np.where(has["HTN"], 1.5, 0.8)
        if c == "BRCA":
            mult *= (m.sex.values == "F")
        if c in ("ASTH", "DEPR", "OUD", "KNEEOA", "RA", "BRCA"):
            mult = np.exp(0.2 * fr) * (mult > 0) if c != "BRCA" else mult
        pa = odds * mult / (1 + odds * mult)
        h = rng.random(n) < pa
        h &= (age_mid >= 0)
        has[c] = h
        o = np.full(n, NO_ONSET)
        inc = rng.random(n) < 0.18
        o[h & ~inc] = -1
        o[h & inc] = rng.integers(0, N_MONTHS, (h & inc).sum())
        onset[c] = o
    # newborns / young children: only asthma allowed
    young = age_mid < 3
    for c in onset:
        if c != "ASTH":
            onset[c][young] = NO_ONSET
    stage = np.where(onset["CKD"] < NO_ONSET, rng.choice(["3a", "3b", "4", "5"], n, p=[0.55, 0.28, 0.12, 0.05]), None)
    return {"onset": onset, "ckd_stage": stage}


def simulate_deaths(rng, m: pd.DataFrame, cond: dict) -> np.ndarray:
    """Return death month index (or -1) per member."""
    n = len(m)
    death_m = np.full(n, -1)
    n_serious = sum((cond["onset"][c] < 9999).astype(int) for c in SERIOUS)
    fr = m._frailty.values
    for mm in range(N_MONTHS):
        a = age_at(m.birth_date.values, mm)
        q = np.select([a < 1, a < 45, a < 65, a < 75, a < 85], [0.005, 0.0012, 0.005, 0.016, 0.042], 0.12)
        h = 1 - (1 - q) ** (1 / 12)
        h = h * np.exp(0.45 * fr + 0.30 * n_serious) * 0.75
        alive = (death_m < 0) & (m._enter_m.values <= mm) & (m._exit_m.values >= mm) & (a >= 0)
        d = alive & (rng.random(n) < h)
        death_m[d] = mm
    return death_m


def assign_home_pcp(rng, m: pd.DataFrame, prov: pd.DataFrame, zips: pd.DataFrame) -> np.ndarray:
    pcps = prov[prov.provider_role == "PCP"].reset_index(drop=True)
    zl = zips.set_index("zip_code")
    plat = zl.latitude.loc[pcps.zip_code].values
    plon = zl.longitude.loc[pcps.zip_code].values
    mlat = zl.latitude.loc[m.zip_code].values
    mlon = zl.longitude.loc[m.zip_code].values
    age = age_at(m.birth_date.values, 0)
    peds = (pcps.specialty == "Pediatrics").values
    fm = (pcps.specialty == "Family Medicine").values
    fqhc = pcps.fqhc_flag.values == 1
    fraud = pcps._fraud_scheme.notna().values
    out = np.empty(len(m), object)
    no_pcp_p = np.clip(0.10 + 0.05 * (m._adi.values - 60) / 20 - 0.05 * m._care_seek.values, 0.02, 0.35)
    for i in range(len(m)):
        if rng.random() < no_pcp_p[i]:
            out[i] = None
            continue
        d = haversine(mlat[i], mlon[i], plat, plon)
        w = 1.0 / (d + 4.0) ** 2
        if age[i] < 18:
            w = w * np.where(peds, 4.0, np.where(fm, 1.0, 0.0))
        else:
            w = w * np.where(peds, 0.0, 1.0)
        w = w * np.where(fqhc, 1 + 2.0 * max(m._adi.values[i] - 60, 0) / 20, 1.0)
        w = w * np.where(fraud, 3.0, 1.0)
        out[i] = pcps.npi.values[rng.choice(len(pcps), p=w / w.sum())]
    return out
