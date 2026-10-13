# Lab 10 Solution: Finding Novel Root Causes of Diabetes Complications

## Task 1: Cohort and outcome

```python
import numpy as np
import pandas as pd

cohort = con.sql("""
    WITH dm AS (
        SELECT member_id FROM medical_claims
        WHERE YEAR(service_from_date) IN (2021, 2022)
          AND (dx_1 LIKE 'E11%' OR dx_2 LIKE 'E11%' OR dx_3 LIKE 'E11%' OR dx_4 LIKE 'E11%')
        GROUP BY member_id HAVING COUNT(DISTINCT claim_id) >= 2
    ),
    observed AS (
        SELECT member_id FROM coverage_member_months
        WHERE coverage_month IN (DATE '2023-01-01', DATE '2025-12-01')
        GROUP BY member_id HAVING COUNT(*) = 2
    ),
    baseline_codes AS (       -- complication codes already present in 2021-2022
        SELECT DISTINCT member_id, dx FROM
            (UNPIVOT (SELECT member_id, dx_1, dx_2, dx_3, dx_4 FROM medical_claims
                      WHERE YEAR(service_from_date) IN (2021, 2022))
             ON dx_1, dx_2, dx_3, dx_4 INTO NAME pos VALUE dx)
        WHERE dx IN ('E11.319', 'E11.22', 'E11.42')
    ),
    events AS (
        SELECT c.member_id,
               MAX(CASE WHEN c.claim_setting IN ('Emergency', 'Inpatient') AND c.dx_1 = 'E11.649' THEN 1 ELSE 0 END) AS hypoglycemia,
               MAX(CASE WHEN c.claim_setting = 'Inpatient' AND c.dx_1 IN ('E11.10', 'E11.00', 'E11.65') THEN 1 ELSE 0 END) AS crisis,
               MAX(CASE WHEN 'E11.621' IN (c.dx_1, c.dx_2, c.dx_3, c.dx_4) OR c.drg_code IN ('616', '617') THEN 1 ELSE 0 END) AS foot,
               MAX(CASE WHEN (c.dx_1 IN ('E11.319', 'E11.22', 'E11.42') OR c.dx_2 IN ('E11.319', 'E11.22', 'E11.42')
                              OR c.dx_3 IN ('E11.319', 'E11.22', 'E11.42') OR c.dx_4 IN ('E11.319', 'E11.22', 'E11.42'))
                         AND NOT EXISTS (SELECT 1 FROM baseline_codes b WHERE b.member_id = c.member_id
                                         AND b.dx IN (c.dx_1, c.dx_2, c.dx_3, c.dx_4))
                        THEN 1 ELSE 0 END) AS new_microvascular
        FROM medical_claims c
        WHERE c.service_from_date BETWEEN DATE '2023-01-01' AND DATE '2025-12-31'
        GROUP BY c.member_id
    )
    SELECT dm.member_id,
           COALESCE(e.hypoglycemia, 0) AS hypoglycemia,
           GREATEST(COALESCE(e.hypoglycemia, 0), COALESCE(e.crisis, 0), COALESCE(e.foot, 0),
                    COALESCE(e.new_microvascular, 0)) AS complication
    FROM dm
    JOIN observed USING (member_id)
    LEFT JOIN events e USING (member_id)
""").df()
print(len(cohort), "members; complication rate", round(cohort.complication.mean(), 3),
      "; hypoglycemia rate", round(cohort.hypoglycemia.mean(), 3))
```

## Task 2: Features

```python
feats = con.sql("""
    WITH rx AS (
        SELECT member_id,
               SUM(days_supply) AS dm_days, COUNT(DISTINCT generic_name) AS dm_drugs,
               MAX(CASE WHEN generic_name = 'glipizide' THEN 1 ELSE 0 END) AS sulfonylurea,
               MAX(CASE WHEN generic_name = 'insulin glargine' THEN 1 ELSE 0 END) AS insulin
        FROM pharmacy_claims
        WHERE claim_status = 'Paid' AND YEAR(fill_date) IN (2021, 2022)
          AND generic_name IN ('metformin', 'glipizide', 'insulin glargine', 'semaglutide', 'tirzepatide', 'empagliflozin')
        GROUP BY member_id
    ),
    cov AS (
        SELECT member_id, 24 - COUNT(*) AS gap_months FROM coverage_member_months
        WHERE coverage_year IN (2021, 2022) GROUP BY member_id
    ),
    visits AS (
        SELECT c.member_id,
               COUNT(DISTINCT CASE WHEN p.provider_role = 'PCP' AND c.claim_type = 'Professional' THEN c.claim_id END) AS pcp_visits,
               COUNT(DISTINCT CASE WHEN c.claim_setting = 'Emergency' AND c.claim_type = 'Institutional' THEN c.claim_id END) AS ed_visits,
               MAX(CASE WHEN c.dx_1 LIKE 'N18%' OR c.dx_2 LIKE 'N18%' OR c.dx_3 LIKE 'N18%' OR c.dx_4 LIKE 'N18%' THEN 1 ELSE 0 END) AS ckd
        FROM medical_claims c JOIN providers p ON p.npi = c.rendering_npi
        WHERE YEAR(c.service_from_date) IN (2021, 2022) AND c.related_claim_id IS NULL
        GROUP BY c.member_id
    )
    SELECT b.member_id,
           LEAST(COALESCE(rx.dm_days / (730.0 * NULLIF(rx.dm_drugs, 0)), 0), 1) AS pdc,
           COALESCE(rx.sulfonylurea, 0) AS sulfonylurea, COALESCE(rx.insulin, 0) AS insulin,
           COALESCE(cov.gap_months, 24) AS gap_months,
           COALESCE(v.pcp_visits, 0) AS pcp_visits, COALESCE(v.ed_visits, 0) AS ed_visits, COALESCE(v.ckd, 0) AS ckd,
           DATE_DIFF('year', b.birth_date, DATE '2023-01-01') AS age,
           z.area_deprivation_index AS adi
    FROM beneficiaries b
    JOIN zip_area z USING (zip_code)
    LEFT JOIN rx USING (member_id) LEFT JOIN cov USING (member_id) LEFT JOIN visits v USING (member_id)
""").df()

df = cohort.merge(feats, on="member_id")
FEATURES = ["pdc", "sulfonylurea", "insulin", "gap_months", "pcp_visits", "ed_visits", "ckd", "age", "adi"]
print(df[FEATURES].isna().sum().sum(), "missing values")
df[FEATURES + ["complication"]].describe().round(2)
```

## Task 3: Random forest and permutation importance

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

X, y = df[FEATURES], df["complication"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=20, random_state=42, n_jobs=-1).fit(X_tr, y_tr)
print("Test AUC:", round(roc_auc_score(y_te, rf.predict_proba(X_te)[:, 1]), 3))

pi = permutation_importance(rf, X_te, y_te, scoring="roc_auc", n_repeats=20, random_state=42, n_jobs=-1)
importance = pd.DataFrame({"feature": FEATURES, "importance": pi.importances_mean, "sd": pi.importances_std})
print(importance.sort_values("importance", ascending=False).round(4).to_string(index=False))
```

## Task 4: Check the hint

```python
df["age_75_plus"] = (df.age >= 75).astype(int)
tab = (df.groupby(["age_75_plus", "sulfonylurea"])
         .agg(members=("member_id", "count"), hypoglycemia_rate=("hypoglycemia", "mean"),
              any_complication_rate=("complication", "mean"))
         .round(3))
print(tab)
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- About 2,000–2,500 cohort members, with roughly 15–25% having a complication in 2023–2025.
- Test AUC around 0.58–0.68. Complications are hard to predict from claims alone, which is a useful discussion point.
- Top permutation-importance features: **area deprivation** and **PDC** (lower adherence → more complications), then sulfonylurea, age and insulin. Gap months and PCP visits add little in this sample, a reminder that a real driver can still be weak in a modest dataset.
- **The novel finding (Task 4):** hypoglycemia is near zero in every cell *except* members **75+ on a sulfonylurea**, where about 1 in 9 had a hypoglycemia ED visit or admission. Their overall complication rate is also the highest of the four groups. The forest barely ranks sulfonylurea because the effect is an *interaction* in a small subgroup, which is why you check model hints with simple tables.

**Instructor check:** `answer_key.parameters` lists the true drivers (A1c through adherence, deprivation, coverage gaps in the prior 24 months, no usual PCP, frailty, zip risk, and sulfonylurea at 75+ for hypoglycemia). `answer_key.diabetes_complications` lists the true events.

## Task 5: AI check

A good answer: yes. Sulfonylureas, especially long-acting ones such as glyburide and glimepiride, cause hypoglycemia, and the risk rises with age and kidney disease. The 2023 AGS Beers Criteria recommend avoiding sulfonylureas as first- or second-line therapy in older adults and, if one is used, choosing a short-acting agent such as glipizide. Watch for AI answers that call glipizide safe in the elderly without caveats, or that cite Beers recommendations it can't source.

## Sample brief

"Complications are concentrated among members with poor adherence and in high-deprivation zip codes, and coverage gaps add risk. The most actionable new finding: members 75 and older on glipizide have several times the hypoglycemia ED and inpatient rate of everyone else. A pharmacist-led review to deprescribe or switch sulfonylureas in that group is a cheap, targeted case management intervention. Adherence outreach in high-deprivation zips is the broader second priority."
