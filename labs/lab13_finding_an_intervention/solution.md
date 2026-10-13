# Lab 13 Solution: Finding a Potential Intervention

## Task 1: Cohort, features and model comparison

```python
import numpy as np
import pandas as pd

data = con.sql("""
    WITH cohort AS (
        SELECT member_id FROM coverage_member_months
        WHERE coverage_year IN (2024, 2025)
        GROUP BY member_id
        HAVING SUM(CASE WHEN coverage_year = 2024 THEN 1 ELSE 0 END) >= 11
           AND SUM(CASE WHEN coverage_year = 2025 THEN 1 ELSE 0 END) >= 11
    ),
    med AS (
        SELECT member_id,
               SUM(total_allowed) FILTER (WHERE YEAR(service_from_date) = 2024) AS allowed_2024,
               SUM(total_allowed) FILTER (WHERE YEAR(service_from_date) = 2025) AS allowed_2025,
               COUNT(*) FILTER (WHERE YEAR(service_from_date) = 2024 AND claim_setting = 'Emergency'
                                AND claim_type = 'Institutional') AS ed_2024,
               COUNT(*) FILTER (WHERE YEAR(service_from_date) = 2024 AND claim_setting = 'Inpatient'
                                AND claim_type = 'Institutional') AS ip_2024
        FROM medical_claims
        WHERE related_claim_id IS NULL AND claim_status IN ('Paid', 'Partially Paid', 'Self-pay')
        GROUP BY member_id
    ),
    dx AS (
        SELECT member_id,
               COUNT(DISTINCT LEFT(dx, 3)) FILTER (WHERE LEFT(dx, 3) IN
                   ('I10','I12','E78','E11','I25','I50','I48','J44','J45','N18','F32','F33','F03','F11')) AS n_chronic,
               MAX(CASE WHEN dx LIKE 'E11%' THEN 1 ELSE 0 END) AS diabetes,
               MAX(CASE WHEN dx LIKE 'I50%' THEN 1 ELSE 0 END) AS chf,
               MAX(CASE WHEN dx LIKE 'J44%' THEN 1 ELSE 0 END) AS copd,
               MAX(CASE WHEN dx LIKE 'N18%' THEN 1 ELSE 0 END) AS ckd
        FROM (UNPIVOT (SELECT member_id, dx_1, dx_2, dx_3, dx_4, dx_5 FROM medical_claims
                       WHERE YEAR(service_from_date) = 2024)
              ON dx_1, dx_2, dx_3, dx_4, dx_5 INTO NAME pos VALUE dx)
        GROUP BY member_id
    ),
    rx AS (
        SELECT member_id, COUNT(*) AS rx_fills_2024,
               MAX(CASE WHEN generic_name = 'glipizide' THEN 1 ELSE 0 END) AS sulfonylurea
        FROM pharmacy_claims WHERE claim_status = 'Paid' AND YEAR(fill_date) = 2024
        GROUP BY member_id
    ),
    payer AS (
        SELECT member_id, ARG_MAX(payer_type, coverage_month) AS payer_type
        FROM coverage_member_months WHERE coverage_year = 2024 GROUP BY member_id
    )
    SELECT c.member_id, b.zip_code,
           DATE_DIFF('year', b.birth_date, DATE '2025-01-01') AS age,
           CASE WHEN b.sex = 'F' THEN 1 ELSE 0 END AS female,
           COALESCE(d.n_chronic, 0) AS n_chronic, COALESCE(d.diabetes, 0) AS diabetes, COALESCE(d.chf, 0) AS chf,
           COALESCE(d.copd, 0) AS copd, COALESCE(d.ckd, 0) AS ckd,
           COALESCE(m.allowed_2024, 0) AS allowed_2024, COALESCE(m.ed_2024, 0) AS ed_2024, COALESCE(m.ip_2024, 0) AS ip_2024,
           COALESCE(r.rx_fills_2024, 0) AS rx_fills_2024, COALESCE(r.sulfonylurea, 0) AS sulfonylurea,
           p.payer_type, z.area_deprivation_index AS adi,
           COALESCE(m.allowed_2025, 0) AS allowed_2025
    FROM cohort c
    JOIN beneficiaries b USING (member_id)
    JOIN zip_area z USING (zip_code)
    JOIN payer p USING (member_id)
    LEFT JOIN med m USING (member_id)
    LEFT JOIN dx d USING (member_id)
    LEFT JOIN rx r USING (member_id)
""").df()
data["high_cost"] = (data.allowed_2025 >= data.allowed_2025.quantile(0.95)).astype(int)
print(len(data), "members; top-5% cost threshold $", round(data.allowed_2025.quantile(0.95)))

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = ["age", "female", "n_chronic", "diabetes", "chf", "copd", "ckd", "allowed_2024", "ed_2024", "ip_2024",
           "rx_fills_2024", "adi"]
CATEGORICAL = ["payer_type"]
X, y = data[NUMERIC + CATEGORICAL], data["high_cost"]
prep = ColumnTransformer([("num", StandardScaler(), NUMERIC),
                          ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)])
models = {
    "logistic": LogisticRegression(max_iter=2000),
    "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=20, random_state=42, n_jobs=-1),
    "gradient_boosting": HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=42),
}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {name: cross_val_score(Pipeline([("prep", prep), ("model", m)]), X, y, cv=cv, scoring="roc_auc")
           for name, m in models.items()}
print(pd.DataFrame({k: [v.mean(), v.std()] for k, v in results.items()}, index=["mean_auc", "sd"]).round(3))
```

## Task 2: Out-of-fold scores

```python
from sklearn.model_selection import cross_val_predict

best_name = max(results, key=lambda k: results[k].mean())
best = Pipeline([("prep", prep), ("model", models[best_name])])
data["p_high_cost"] = cross_val_predict(best, X, y, cv=cv, method="predict_proba")[:, 1]
print("Best model:", best_name)
```

## Task 3: Net savings

```python
rows = []
ranked = data.sort_values("p_high_cost", ascending=False)
for pct in (0.01, 0.05, 0.10):
    n = int(round(pct * len(ranked)))
    tgt = ranked.head(n)
    savings = 0.15 * tgt.allowed_2025.sum()
    cost = 700 * n
    rows.append({"target": f"top {int(pct * 100)}%", "members": n,
                 "actual_2025_allowed": round(tgt.allowed_2025.sum()),
                 "share_truly_high_cost": round(tgt.high_cost.mean(), 3),
                 "savings": round(savings), "cost": cost, "net": round(savings - cost)})
programA = pd.DataFrame(rows)
print(programA.to_string(index=False))

# Program B: sulfonylurea review for targeted members 75+ on glipizide (all such members, for comparison)
b = data[(data.age >= 75) & (data.sulfonylurea == 1)]
b_net = len(b) * (0.05 * 0.60 * 6000 - 150)
print(f"Program B: {len(b)} members, net savings about ${b_net:,.0f}")

# Program C: mobile clinics in 5 zips (use the five zips with the most 2024 ED visits per member)
zips = data.groupby("zip_code").agg(members=("member_id", "count"), ed=("ed_2024", "sum"))
top5 = zips[zips.members >= 100].sort_values("ed", ascending=False).head(5)
c_net = 0.15 * top5.ed.sum() * 1200 - 5 * 250_000
print(f"Program C: {top5.members.sum()} members in 5 zips, net savings about ${c_net:,.0f}")
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- **Model comparison:** all three models land around AUC 0.78–0.79, within cross-validation noise of each other. Logistic regression is as good as the ensembles here, a good discussion point about choosing the simplest model that works.
- **Program A:** net savings peak around the **top 5%** (about $300–350K). The top 1% has the highest savings per member but too few members; at the top 10%, savings per member fall toward the $700 cost, so net savings flatten.
- **Program B** is small but reliably positive (cheap per member, concentrated risk).
- **Program C** usually loses money under these assumptions: $1.25M of fixed cost against savings from a few hundred prevented ED visits.

Most students should recommend **Program A targeted to the top 1–5%**, possibly paired with B as a low-cost add-on. Grade on reasoning, honest assumptions and a measurement plan (for example a randomized or stepped rollout, or a matched comparison group like Lab 9).

## Task 4: AI critiques worth accepting

- **Regression to the mean:** high-cost members this year are partly high-cost by chance; savings measured against their own baseline overstate the effect.
- The effect size (15%) is assumed. Run a sensitivity analysis at 10% and 20%.
- Not every targeted member will enroll (engagement is often 30–50%), so cost and savings scale down.
- Out-of-fold predictions avoid overfitting, but the model was trained and evaluated on the same years. A true prospective test would train on 2023→2024 and score 2024→2025.
