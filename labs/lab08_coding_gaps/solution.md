# Lab 8 Solution: Closing Coding Gaps

The code assumes `con` is an open read-only DuckDB connection (`duckdb.connect(DB_PATH, read_only=True)`).

## Task 1: HCCs and recapture

One SQL function builds the member × HCC table for any pair of years, so Task 4 can reuse it.

```python
import duckdb
import numpy as np
import pandas as pd

def hcc_pairs(con, base_year: int) -> pd.DataFrame:
    """Member x HCC pairs coded in base_year, with recaptured = coded again in base_year + 1.
    Limited to members in Medicare Advantage 11+ months in both years."""
    nxt = base_year + 1
    return con.sql(f"""
        WITH ma AS (
            SELECT member_id
            FROM coverage_member_months
            WHERE payer_type = 'Medicare Advantage' AND coverage_year IN ({base_year}, {nxt})
            GROUP BY member_id
            HAVING SUM(CASE WHEN coverage_year = {base_year} THEN 1 ELSE 0 END) >= 11
               AND SUM(CASE WHEN coverage_year = {nxt} THEN 1 ELSE 0 END) >= 11
        ),
        dx AS (
            SELECT member_id, YEAR(service_from_date) AS yr, dx
            FROM (UNPIVOT medical_claims
                  ON dx_1, dx_2, dx_3, dx_4, dx_5, dx_6, dx_7, dx_8, dx_9, dx_10
                  INTO NAME dx_position VALUE dx)
            WHERE YEAR(service_from_date) IN ({base_year}, {nxt})
              AND claim_status <> 'Denied'
        ),
        member_hcc AS (
            SELECT DISTINCT d.member_id, d.yr, h.hcc, h.hcc_label, h.illustrative_coefficient
            FROM dx d JOIN ref_hcc_crosswalk h ON h.icd10_code = d.dx
            WHERE d.member_id IN (SELECT member_id FROM ma)
        )
        SELECT b.member_id, b.hcc, b.hcc_label, b.illustrative_coefficient,
               CASE WHEN n.member_id IS NOT NULL THEN 1 ELSE 0 END AS recaptured
        FROM member_hcc b
        LEFT JOIN member_hcc n ON n.member_id = b.member_id AND n.hcc = b.hcc AND n.yr = {nxt}
        WHERE b.yr = {base_year}
    """).df()

pairs23 = hcc_pairs(con, 2023)
print(len(pairs23), "member-HCC pairs; recapture rate:", round(pairs23.recaptured.mean(), 3))
print(pairs23.groupby("hcc_label").recaptured.agg(["count", "mean"]).sort_values("count", ascending=False).head(10))
```

## Task 2: Features

```python
def member_features(con, year: int) -> pd.DataFrame:
    return con.sql(f"""
        WITH claims AS (
            SELECT DISTINCT c.claim_id, c.member_id, p.provider_role, l.procedure_code
            FROM medical_claims c
            JOIN medical_claim_lines l ON l.claim_id = c.claim_id
            JOIN providers p ON p.npi = c.rendering_npi
            WHERE YEAR(c.service_from_date) = {year} AND c.claim_type = 'Professional'
              AND c.related_claim_id IS NULL
        ),
        visits AS (
            SELECT member_id,
                   COUNT(DISTINCT CASE WHEN provider_role = 'PCP' THEN claim_id END)        AS pcp_visits,
                   COUNT(DISTINCT CASE WHEN provider_role = 'Specialist' THEN claim_id END) AS specialist_visits,
                   MAX(CASE WHEN procedure_code IN ('G0438', 'G0439') THEN 1 ELSE 0 END)   AS had_awv
            FROM claims GROUP BY member_id
        ),
        dual AS (
            SELECT member_id, MAX(CASE WHEN dual_status IS NOT NULL THEN 1 ELSE 0 END) AS dual
            FROM coverage_member_months WHERE coverage_year = {year} GROUP BY member_id
        )
        SELECT b.member_id,
               DATE_DIFF('year', b.birth_date, DATE '{year}-12-31') AS age,
               COALESCE(v.pcp_visits, 0) AS pcp_visits,
               COALESCE(v.specialist_visits, 0) AS specialist_visits,
               COALESCE(v.had_awv, 0) AS had_awv,
               COALESCE(d.dual, 0) AS dual
        FROM beneficiaries b
        LEFT JOIN visits v USING (member_id)
        LEFT JOIN dual d USING (member_id)
    """).df()

def build(con, base_year):
    pairs = hcc_pairs(con, base_year)
    feats = member_features(con, base_year)
    return pairs.merge(feats, on="member_id", how="left")

FEATURES = ["pcp_visits", "specialist_visits", "had_awv", "age", "dual"]
train_df = build(con, 2023)
train_df[FEATURES + ["recaptured"]].describe().round(2)
```

## Task 3: Train and compare

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score

X, y = train_df[FEATURES], train_df["recaptured"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)

logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_tr, y_tr)
tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=50, random_state=42).fit(X_tr, y_tr)

auc_logit = roc_auc_score(y_te, logit.predict_proba(X_te)[:, 1])
auc_tree = roc_auc_score(y_te, tree.predict_proba(X_te)[:, 1])
print(f"Logistic AUC {auc_logit:.3f} | Tree AUC {auc_tree:.3f}")

coefs = pd.Series(logit[-1].coef_[0], index=FEATURES).sort_values()
print("Standardized logistic coefficients:\n", coefs.round(3))
print("Tree importances:\n", pd.Series(tree.feature_importances_, index=FEATURES).sort_values(ascending=False).round(3))
```

## Task 4: Outreach list for 2025

```python
best = logit if auc_logit >= auc_tree else tree
score_df = build(con, 2024)            # 2024 features; 'recaptured' here is 2025's actual outcome
score_df["p_recapture"] = best.predict_proba(score_df[FEATURES])[:, 1]
outreach = (score_df.sort_values("p_recapture")
            .loc[:, ["member_id", "hcc", "hcc_label", "p_recapture", "pcp_visits", "had_awv"]]
            .head(100))
print(outreach.head(15).to_string(index=False))

# Instructor check: how did the list do? (uses the actual 2025 outcome)
print("2025 AUC:", round(roc_auc_score(score_df.recaptured, score_df.p_recapture), 3))
for n in (100, 200):
    top = score_df.sort_values("p_recapture").head(n)
    print(f"Actual 2025 recapture among the {n} lowest-scored pairs:", round(top.recaptured.mean(), 3),
          "vs. all pairs:", round(score_df.recaptured.mean(), 3))
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- About 90% of 2023 HCCs are recaptured in 2024. Gaps are the minority, which makes them hard to predict.
- Both models reach only a modest AUC (roughly 0.57–0.65 on the test split, and about 0.63 scoring 2024 → 2025).
- The strongest predictors are **PCP visits** and **annual wellness visit** (both raise recapture) and **specialist visits** (specialists document their own conditions). Age and dual status matter little.
- The lowest-scored pairs are recaptured noticeably less often than average (for example about 86% vs. 91%), so an outreach call to the list is more likely to close a real gap. The biggest driver, though, is *next* year's visits, which the model can't see. That's a good discussion of why prediction alone isn't enough: scheduling the wellness visit is the intervention.

**Instructor check:** `answer_key.member_truth` holds true condition onset dates. Nearly every member on the outreach list still has the condition, so these are documentation gaps, not resolved conditions.

## Task 5: Compliance line (sample)

"Closing a gap means making sure a condition the member really has is assessed and documented at a face-to-face visit this year. Upcoding means adding diagnoses without clinical support, for example from old problem lists, chart reviews or Rx data alone, and it's what RADV audits and False Claims Act cases target."
