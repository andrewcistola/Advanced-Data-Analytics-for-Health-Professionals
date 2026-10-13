"""Orchestrates the full build and writes DuckDB + Parquet (+ optional CSV) outputs."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

from . import reference as R
from .world import build_zip_area, build_providers
from .population import build_members, assign_conditions, simulate_deaths, assign_home_pcp, rand_date_in_month, month_start
from .coverage import simulate_coverage, coverage_table, PLAN_DF
from .engine import Engine
from .pharmacy import assign_regimens, PharmacyGenerator, NDC
from .encounters import Generator, TCP_TRUE_OR, CCM_HAZARD_RR, TCP_LAUNCH


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:7.1f}s] {msg}", flush=True)


def build(n_members: int = 25000, seed: int = 42):
    rng = np.random.default_rng(seed)
    fake = Faker("en_US")
    Faker.seed(seed)

    log("geography and providers")
    zips = build_zip_area(rng)
    prov = build_providers(rng, fake, zips)

    log(f"members (n={n_members:,})")
    m = build_members(rng, fake, zips, n_members)
    cond = assign_conditions(rng, m)
    death_m = simulate_deaths(rng, m, cond)
    m["death_date"] = [rand_date_in_month(rng, int(k)) if k >= 0 else pd.NaT for k in death_m]
    # a member cannot die before birth
    bad = m.death_date.notna() & (m.death_date < m.birth_date)
    m.loc[bad, "death_date"] = m.loc[bad, "birth_date"] + pd.Timedelta(days=5)
    home = assign_home_pcp(rng, m, prov, zips)

    log("coverage")
    pcp_npis = prov[(prov.provider_role == "PCP") & prov._fraud_scheme.isna()].npi.values
    cov = simulate_coverage(rng, m, death_m, cond, home, pcp_npis)
    cov_df = coverage_table(rng, m, cov, cond)

    log("regimens")
    reg = assign_regimens(rng, m, cond)

    log("encounters and medical claims")
    eng = Engine(rng, m, prov, cov)
    gen = Generator(rng, m, prov, zips, cond, cov, home, reg, eng)
    gen.run()
    gen.run_fraud()
    log(f"  medical claims: {len(eng.claims):,}  lines: {len(eng.lines):,}  ledger rows: {len(eng.ledger):,}")
    import gc
    for st_ in (eng.claims, eng.lines, eng.ledger):
        st_.freeze()
    gc.collect()

    log("pharmacy claims")
    ph = PharmacyGenerator(rng, gen, eng)
    ph.run_regimens(reg)
    ph.run_acute(gen.acute_rx)
    ph.run_pill_mill(gen.pill_mill, gen.pain_doc,
                     prov[prov._fraud_scheme == "PILL_MILL_PHARMACY"].npi.values[0])
    ph.out.freeze()
    eng.pa.freeze()
    gc.collect()
    log(f"  pharmacy claims: {len(ph.out):,}")

    log("assembling tables")
    tables, answer = {}, {}
    tables["beneficiaries"] = m[["member_id", "first_name", "last_name", "sex", "birth_date", "death_date",
                                 "race_ethnicity", "preferred_language", "zip_code", "county"]].copy()
    tables["coverage_member_months"] = cov_df.drop(columns=["_mi", "_mo"])
    claims = eng.claims.df()
    tables["medical_claims"] = claims.sort_values(["service_from_date", "claim_id"]).reset_index(drop=True)
    tables["medical_claim_lines"] = eng.lines.df()
    rx = ph.out.df().sort_values(["fill_date", "rx_claim_id"]).reset_index(drop=True)
    tables["pharmacy_claims"] = rx
    led = eng.ledger.df()
    led = led[led.transaction_date <= pd.Timestamp(R.AS_OF_DATE)]
    tables["hospital_payments"] = led.sort_values(["transaction_date", "transaction_id"]).reset_index(drop=True)
    tables["prior_authorizations"] = eng.pa.df()
    tables["care_management"] = pd.DataFrame(gen.care_mgmt)
    pub_prov = ["npi", "entity_type", "provider_name", "credential", "specialty", "taxonomy_code", "practice_id",
                "practice_name", "health_system", "zip_code", "provider_role", "aco_name", "fqhc_flag"]
    tables["providers"] = prov[pub_prov].copy()
    tables["zip_area"] = zips[[c for c in zips.columns if not c.startswith("_")]].copy()
    tables["plans"] = PLAN_DF.assign(payer_type=PLAN_DF.payer_type_code.map(R.PAYER_TYPE_NAME))[
        ["plan_id", "plan_name", "payer_type", "product_type", "funding_type", "metal_tier", "deductible",
         "coinsurance", "copay_pcp", "copay_specialist", "copay_ed", "inpatient_copay", "oop_max",
         "requires_prior_auth", "requires_pcp", "timely_filing_days"]].copy()
    tables["plans"]["deductible"] = tables["plans"]["deductible"].where(tables["plans"]["deductible"] >= 0)
    tables["plans"]["inpatient_copay"] = tables["plans"]["inpatient_copay"].where(tables["plans"]["inpatient_copay"] >= 0)
    tables["plans"] = pd.concat([tables["plans"], pd.DataFrame([dict(plan_id=R.PDP_PLAN[0], plan_name=R.PDP_PLAN[1],
                                 payer_type="Medicare Part D (PDP)", product_type="PDP", funding_type="Capitated")])])
    # reference tables
    tables["ref_icd10"] = pd.DataFrame(sorted(R.ICD10.items()), columns=["icd10_code", "description"])
    tables["ref_procedure"] = pd.DataFrame([(k, v[0], v[1], v[2], v[4]) for k, v in R.PROCEDURES.items()],
                                           columns=["procedure_code", "description", "code_type", "category",
                                                    "prior_auth_commonly_required"])
    tables["ref_revenue_code"] = pd.DataFrame(sorted(R.REVENUE_CODES.items()), columns=["revenue_code", "description"])
    tables["ref_drg"] = pd.DataFrame([(k, v[0], v[1]) for k, v in R.DRGS.items()],
                                     columns=["drg_code", "description", "approx_relative_weight"])
    tables["ref_drug"] = pd.DataFrame([(NDC[k], v[0], v[1], v[2], v[4], v[5], v[6], v[7], R.MME_PER_UNIT.get(k))
                                       for k, v in R.DRUGS.items()],
                                      columns=["ndc", "drug_name", "generic_name", "therapeutic_class", "formulary_tier",
                                               "prior_auth_required", "brand_generic_flag", "specialty_drug_flag",
                                               "mme_per_unit"])
    tables["ref_carc"] = pd.DataFrame([(k, v[0], v[1], v[2]) for k, v in R.CARC.items()],
                                      columns=["carc_code", "typical_group_code", "description", "denial_category"])
    tables["ref_ncpdp_reject"] = pd.DataFrame(sorted(R.NCPDP_REJECT.items()), columns=["reject_code", "description"])
    tables["ref_hcc_crosswalk"] = pd.DataFrame(R.HCC_MAP, columns=["icd10_code", "hcc", "hcc_label",
                                                                  "illustrative_coefficient"])

    # ----------------------------------------------------------- answer key
    mt = m[["member_id"]].copy()
    mt["frailty"] = m._frailty.round(3)
    mt["care_seeking"] = m._care_seek.round(3)
    mt["adherence_propensity"] = m._adherence.round(3)
    mt["zip_risk_multiplier"] = m._zip_risk.round(3)
    mt["home_pcp_npi"] = home
    for c, o in cond["onset"].items():
        mt[f"onset_{c.lower()}"] = [None if v >= 9999 else (pd.Timestamp("2020-12-31") if v < 0 else month_start(int(v)))
                                    for v in o]
    mt["ckd_stage"] = cond["ckd_stage"]
    mt["diabetes_complex_cm_until"] = [month_start(gen.ccm_until[i]) if i in gen.ccm_until and gen.ccm_until[i] < 60 else None
                                       for i in range(len(m))]
    answer["member_truth"] = mt
    answer["diabetes_complications"] = pd.DataFrame(gen.truth_dm)
    answer["readmission_index_stays"] = pd.DataFrame(gen.truth_ip)
    fr = prov[prov._fraud_scheme.notna()][["npi", "provider_name", "specialty", "_fraud_scheme"]].rename(
        columns={"_fraud_scheme": "scheme"})
    desc = {"EM_UPCODING": "Bills 99215 for ~65% of established visits (peers ~5-12%)",
            "LAB_EXCESSIVE_TESTING": "Definitive drug panels (G0483) and respiratory panels (87633) added to routine labs; standing monthly orders for patients of kickback practices",
            "DME_PHANTOM_BRACES": "Back/knee braces billed for Medicare members with no related visits; ~30 claims dated after the member's death",
            "PT_EXCESSIVE_UNITS": "11 timed units per visit, ~3 visits/week for 2-3 months",
            "IMPOSSIBLE_DAY_PSYCHOTHERAPY": "60-minute psychotherapy sessions crowded onto Tuesdays (implausible hours per day)",
            "PILL_MILL_PRESCRIBER": "Monthly oxycodone 30 mg x120 for patients travelling from distant zip codes",
            "PILL_MILL_PHARMACY": "Fills nearly all of the pill-mill prescriber's oxycodone"}
    fr["description"] = fr.scheme.map(desc)
    kb = prov[prov.practice_id.isin(gen.kickback_practices)][["npi", "provider_name", "practice_name"]].drop_duplicates("npi")
    kb = kb.assign(specialty="Primary care", scheme="LAB_KICKBACK_REFERRER",
                   description="Practice steers lab work to Prairie Diagnostics Laboratory")[fr.columns.drop("description").tolist() + ["description"]]
    answer["fraud_providers"] = pd.concat([fr, kb[fr.columns]], ignore_index=True)
    answer["zip_risk"] = zips[["zip_code", "city", "county", "_zip_risk", "_hotspot"]].rename(
        columns={"_zip_risk": "zip_risk_multiplier", "_hotspot": "unexplained_hotspot_flag"})
    answer["provider_traits"] = prov[["npi", "provider_name", "practice_id", "specialty", "_quality", "_doc_rate",
                                      "_billing_quality", "_epa_adopt_month"]].rename(columns=lambda c: c.lstrip("_"))
    answer["parameters"] = pd.DataFrame([
        ("seed", str(seed)), ("n_members", str(n_members)),
        ("tcp_launch_date", str(TCP_LAUNCH)), ("tcp_true_readmission_odds_ratio", str(TCP_TRUE_OR)),
        ("tcp_enrollment", "Sicker patients more likely to enroll (selection on baseline risk)"),
        ("followup_7d_log_odds_effect_on_readmission", "-0.45"),
        ("diabetes_ccm_complication_hazard_ratio", str(CCM_HAZARD_RR)),
        ("diabetes_complication_drivers", "A1c (via adherence), area deprivation, coverage gap in prior 24 months, "
         "no usual PCP, frailty, zip risk; plus hypoglycemia from sulfonylurea (glipizide) use at age 75+ (higher with CKD)"),
        ("medicaid_unwinding_window", "2023-04 to 2024-06"),
        ("as_of_date", R.AS_OF_DATE),
    ], columns=["parameter", "value"])
    return tables, answer


def _comment(con, table, schema="main"):
    from .dictionary import TABLES
    if table not in TABLES:
        return
    q = lambda x: x.replace("'", "''")
    tdesc, cols = TABLES[table]
    con.execute(f"COMMENT ON TABLE {schema}.{table} IS '{q(tdesc)}'")
    existing = {r[0] for r in con.execute(
        f"select column_name from information_schema.columns where table_schema='{schema}' and table_name='{table}'").fetchall()}
    for c, d in cols.items():
        if c in existing:
            con.execute(f"COMMENT ON COLUMN {schema}.{table}.{c} IS '{q(d)}'")


def write(tables: dict, answer: dict, out_dir: Path, csv: bool = False,
          db_name: str = "health_analytics.duckdb", instructor_db_name: str = "health_analytics_instructor.duckdb"):
    """Write the student database (course tables only), the instructor database
    (course tables + answer_key schema) and Parquet copies of every table."""
    import duckdb
    out_dir.mkdir(parents=True, exist_ok=True)
    pq = out_dir / "parquet"
    (pq / "main").mkdir(parents=True, exist_ok=True)
    (pq / "answer_key").mkdir(parents=True, exist_ok=True)
    inst_path = out_dir / instructor_db_name
    db_path = out_dir / db_name
    for p in (inst_path, db_path):
        if p.exists():
            p.unlink()
    con = duckdb.connect(str(inst_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS answer_key")
    for schema, tbls in (("main", tables), ("answer_key", answer)):
        for name, df in tbls.items():
            df = df.copy()
            date_cols = []
            for c in df.columns:
                if df[c].dtype == object:
                    sample = df[c].dropna()
                    if len(sample) and hasattr(sample.iloc[0], "isoformat") and not isinstance(sample.iloc[0], str):
                        df[c] = pd.to_datetime(df[c])
                if pd.api.types.is_datetime64_any_dtype(df[c]):
                    v = df[c].dropna()
                    if len(v) == 0 or (v.dt.normalize() == v).all():
                        date_cols.append(c)
            con.register("_df", df)
            cats = [c for c in df.columns if isinstance(df[c].dtype, pd.CategoricalDtype)]
            sel = ", ".join(f'CAST("{c}" AS DATE) AS "{c}"' if c in date_cols else
                            (f'CAST("{c}" AS VARCHAR) AS "{c}"' if c in cats else f'"{c}"') for c in df.columns)
            con.execute(f"CREATE TABLE {schema}.{name} AS SELECT {sel} FROM _df")
            con.unregister("_df")
            _comment(con, name, schema)
            con.execute(f"COPY {schema}.{name} TO '{pq / schema / (name + '.parquet')}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            if csv:
                (out_dir / "csv" / schema).mkdir(parents=True, exist_ok=True)
                con.execute(f"COPY {schema}.{name} TO '{out_dir / 'csv' / schema / (name + '.csv.gz')}' (HEADER, COMPRESSION GZIP)")
            log(f"  wrote {schema}.{name}: {len(df):,} rows")
    con.close()
    # student database: course tables only (no answer key)
    con = duckdb.connect(str(db_path))
    con.execute(f"ATTACH '{inst_path}' AS src (READ_ONLY)")
    for name in tables:
        con.execute(f"CREATE TABLE main.{name} AS SELECT * FROM src.main.{name}")
        _comment(con, name)
    con.execute("DETACH src")
    con.execute("CHECKPOINT")
    con.close()
    log(f"  student database: {db_path}")
    return db_path
