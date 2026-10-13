# Lab 11 Solution: Targeting High-Risk Zip Codes

## Task 1: Modeling table

```python
import numpy as np
import pandas as pd

CHRONIC_PREFIXES = ("I10", "I12", "E78", "E11", "I25", "I50", "I48", "J44", "J45", "N18", "F32", "F33", "F03", "F11")
ACSC_PREFIXES = ("I50", "J44", "J45", "E11", "N39.0", "J18", "E86")
chronic_case = " ".join(f"WHEN dx LIKE '{p}%' THEN '{p[:3]}'" for p in CHRONIC_PREFIXES)
acsc_cond = " OR ".join(f"dx_1 LIKE '{p}%'" for p in ACSC_PREFIXES)

data = con.sql(f"""
    WITH cohort AS (
        SELECT member_id FROM coverage_member_months
        WHERE coverage_year = 2024 GROUP BY member_id HAVING COUNT(*) >= 11
        INTERSECT
        SELECT member_id FROM coverage_member_months WHERE coverage_month = DATE '2025-01-01'
    ),
    payer AS (
        SELECT member_id, ARG_MAX(payer_type, coverage_month) AS payer_type
        FROM coverage_member_months WHERE coverage_year = 2024 GROUP BY member_id
    ),
    chronic AS (
        SELECT member_id, COUNT(DISTINCT CASE {chronic_case} END) AS n_chronic
        FROM (UNPIVOT (SELECT member_id, dx_1, dx_2, dx_3, dx_4, dx_5 FROM medical_claims
                       WHERE YEAR(service_from_date) = 2024)
              ON dx_1, dx_2, dx_3, dx_4, dx_5 INTO NAME pos VALUE dx)
        GROUP BY member_id
    ),
    use24 AS (
        SELECT member_id,
               COUNT(*) FILTER (WHERE claim_setting = 'Emergency') AS ed_2024,
               COUNT(*) FILTER (WHERE claim_setting = 'Inpatient')  AS ip_2024
        FROM medical_claims
        WHERE YEAR(service_from_date) = 2024 AND claim_type = 'Institutional' AND related_claim_id IS NULL
        GROUP BY member_id
    ),
    outcome AS (
        SELECT DISTINCT member_id FROM medical_claims
        WHERE YEAR(service_from_date) = 2025 AND claim_type = 'Institutional' AND related_claim_id IS NULL
          AND (claim_setting = 'Emergency' OR (claim_setting = 'Inpatient' AND ({acsc_cond})))
    )
    SELECT c.member_id, b.zip_code,
           DATE_DIFF('year', b.birth_date, DATE '2025-01-01') AS age,
           CASE WHEN b.sex = 'F' THEN 1 ELSE 0 END AS female,
           COALESCE(ch.n_chronic, 0) AS n_chronic,
           COALESCE(u.ed_2024, 0) AS ed_2024, COALESCE(u.ip_2024, 0) AS ip_2024,
           CASE WHEN p.payer_type LIKE 'Medicaid%' THEN 1 ELSE 0 END AS medicaid,
           CASE WHEN p.payer_type LIKE 'Medicare%' THEN 1 ELSE 0 END AS medicare,
           z.area_deprivation_index AS adi, z.pcp_per_10k, z.pct_no_vehicle, z.miles_to_nearest_hospital,
           CASE WHEN o.member_id IS NOT NULL THEN 1 ELSE 0 END AS avoidable_event
    FROM cohort c
    JOIN beneficiaries b USING (member_id)
    JOIN zip_area z USING (zip_code)
    JOIN payer p USING (member_id)
    LEFT JOIN chronic ch USING (member_id)
    LEFT JOIN use24 u USING (member_id)
    LEFT JOIN outcome o USING (member_id)
""").df()
MEMBER = ["age", "female", "n_chronic", "ed_2024", "ip_2024", "medicaid", "medicare"]
ZIP = ["adi", "pcp_per_10k", "pct_no_vehicle", "miles_to_nearest_hospital"]
print(len(data), "members; 2025 avoidable-event rate", round(data.avoidable_event.mean(), 3))
```

## Task 2: Neural network vs. logistic regression

```python
import tensorflow as tf
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

tf.random.set_seed(42)
X, y = data[MEMBER + ZIP].astype(float), data["avoidable_event"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
scaler = StandardScaler().fit(X_tr)
X_tr_s, X_te_s = scaler.transform(X_tr), scaler.transform(X_te)

logit = LogisticRegression(max_iter=1000).fit(X_tr_s, y_tr)
auc_lr = roc_auc_score(y_te, logit.predict_proba(X_te_s)[:, 1])

nn = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(X_tr_s.shape[1],)),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(1, activation="sigmoid"),
])
nn.compile(optimizer="adam", loss="binary_crossentropy", metrics=[tf.keras.metrics.AUC(name="auc")])
nn.fit(X_tr_s, y_tr, validation_split=0.2, epochs=100, batch_size=256, verbose=0,
       callbacks=[tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)])
auc_nn = roc_auc_score(y_te, nn.predict(X_te_s, verbose=0).ravel())
print(f"Test AUC  logistic: {auc_lr:.3f}   neural network: {auc_nn:.3f}")
```

## Task 3: Observed vs. expected by zip

```python
member_only = LogisticRegression(max_iter=1000).fit(StandardScaler().fit_transform(data[MEMBER]), data["avoidable_event"])
data["expected"] = member_only.predict_proba(StandardScaler().fit_transform(data[MEMBER]))[:, 1]

zips = (data.groupby("zip_code")
            .agg(members=("member_id", "count"), observed=("avoidable_event", "sum"), expected=("expected", "sum"))
            .query("members >= 100"))
zips["oe_ratio"] = zips.observed / zips.expected
zips["excess"] = zips.observed - zips.expected
zips = zips.join(con.sql("SELECT zip_code, city, county, area_deprivation_index, pcp_per_10k, pct_no_vehicle, "
                         "miles_to_nearest_hospital FROM zip_area").df().set_index("zip_code"))
targets = zips.sort_values("excess", ascending=False)
print(targets.head(10).round(2).to_string())
```

To check for a zip the area features *don't* explain, add the zip features to the expected-risk model and look for zips that still have a high O/E:

```python
full = LogisticRegression(max_iter=1000)
Xs_full = StandardScaler().fit_transform(data[MEMBER + ZIP])
data["expected_full"] = full.fit(Xs_full, data["avoidable_event"]).predict_proba(Xs_full)[:, 1]
resid = (data.groupby("zip_code").agg(members=("member_id", "count"), observed=("avoidable_event", "sum"),
                                      expected=("expected_full", "sum")).query("members >= 100"))
resid["oe_after_zip_features"] = resid.observed / resid.expected
print(resid.sort_values("oe_after_zip_features", ascending=False).head(8).round(2).to_string())
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- About a quarter of the cohort has an avoidable event in 2025.
- **The neural network does about as well as logistic regression** (both about 0.70 AUC, within ±0.01). On a handful of tabular features, a network has little to find that a linear model misses.
- **Target zips:** high-deprivation, low-PCP-supply, high-no-vehicle zips (several Ocala, Clay and rural Suwannee/Hamilton zips) have the most excess events. Four of the **five planted "unexplained hotspot" zips** (Lake City 32025, Live Oak 32064, Summerfield 34491, Hernando 34442; see `answer_key.zip_risk.unexplained_hotspot_flag`) top the O/E list *after* adjusting for zip features. The fifth (Anthony 32617) is too small to pass the 100-member filter. Their risk comes from something not in the data, which is worth a site visit.

## Task 4: AI check

Good reasons: small number of features with mostly monotone effects; the signal-to-noise ratio is low (whether a member goes to the ED is largely random); tabular data where tree ensembles or linear models are hard to beat; networks need more data and tuning. Watch for AI claims that a network is "always better with more layers."

## Sample target list (format)

| Rank | Zip | City | Members | O/E | Excess events | Why |
|---|---|---|---|---|---|---|
| 1 | 3xxxx | … | 1,200 | 1.45 | 85 | ADI 88, 1.5 PCPs per 10k, 14% without a vehicle |
| … | | | | | | |
