# Lab 9 Solution: Assessing Impact of a Readmissions Reduction Program

## Task 1: Index stays and readmissions

```python
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

stays = con.sql("""
    WITH ip AS (
        SELECT c.member_id, c.claim_id, c.billing_npi, p.provider_name AS hospital, p.health_system,
               c.admission_date, c.discharge_date, c.length_of_stay, c.discharge_status
        FROM medical_claims c JOIN providers p ON p.npi = c.billing_npi
        WHERE c.claim_setting = 'Inpatient' AND c.claim_type = 'Institutional'
          AND c.related_claim_id IS NULL
          AND c.drg_code NOT IN ('795', '807', '470')
    )
    SELECT i.*,
           CASE WHEN EXISTS (SELECT 1 FROM ip r
                             WHERE r.member_id = i.member_id
                               AND r.admission_date >  i.discharge_date
                               AND r.admission_date <= i.discharge_date + INTERVAL 30 DAY)
                THEN 1 ELSE 0 END AS readmit_30d,
           CASE WHEN cm.cm_enrollment_id IS NOT NULL THEN 1 ELSE 0 END AS enrolled
    FROM ip i
    LEFT JOIN care_management cm
           ON cm.index_claim_id = i.claim_id AND cm.program_name = 'Transitional Care Program'
    WHERE i.discharge_status IN ('01', '06')
      AND i.discharge_date <= DATE '2025-12-01'
""").df()
print(len(stays), "index stays; overall 30-day readmission rate", round(stays.readmit_30d.mean(), 3))
```

## Task 2: Risk factors

```python
CHRONIC_PREFIXES = {
    "htn": ("I10", "I12"), "lipids": ("E78",), "diabetes": ("E11",), "cad": ("I25",), "chf": ("I50",),
    "afib": ("I48",), "copd": ("J44",), "asthma": ("J45",), "ckd": ("N18",), "depression": ("F32", "F33"),
    "dementia": ("F03",), "oud": ("F11",),
}
case_parts = []
for grp_name, prefixes in CHRONIC_PREFIXES.items():
    cond = " OR ".join("dx LIKE '" + p + "%'" for p in prefixes)
    case_parts.append(f"WHEN {cond} THEN '{grp_name}'")
case_sql = " ".join(case_parts)

con.register("stays_df", stays[["member_id", "claim_id", "admission_date", "discharge_date"]])
risk = con.sql(f"""
    WITH dx AS (
        SELECT member_id, service_from_date, CASE {case_sql} END AS grp
        FROM (UNPIVOT medical_claims ON dx_1, dx_2, dx_3, dx_4, dx_5, dx_6, dx_7, dx_8, dx_9, dx_10
              INTO NAME pos VALUE dx)
    ),
    chronic AS (
        SELECT s.claim_id, COUNT(DISTINCT d.grp) AS n_chronic,
               MAX(CASE WHEN d.grp = 'chf' THEN 1 ELSE 0 END) AS chf,
               MAX(CASE WHEN d.grp = 'copd' THEN 1 ELSE 0 END) AS copd
        FROM stays_df s
        JOIN dx d ON d.member_id = s.member_id AND d.grp IS NOT NULL
                 AND d.service_from_date BETWEEN s.admission_date - INTERVAL 365 DAY AND s.admission_date
        GROUP BY s.claim_id
    ),
    prior_ip AS (
        SELECT s.claim_id, COUNT(*) AS prior_admits
        FROM stays_df s
        JOIN medical_claims c ON c.member_id = s.member_id AND c.claim_setting = 'Inpatient'
             AND c.claim_type = 'Institutional' AND c.related_claim_id IS NULL
             AND c.admission_date >= s.admission_date - INTERVAL 365 DAY AND c.admission_date < s.admission_date
        GROUP BY s.claim_id
    ),
    cov AS (
        SELECT s.claim_id,
               MAX(CASE WHEN m.payer_type LIKE 'Medicaid%' OR m.dual_status IS NOT NULL THEN 1 ELSE 0 END) AS medicaid_dual
        FROM stays_df s
        JOIN coverage_member_months m ON m.member_id = s.member_id
             AND m.coverage_month = DATE_TRUNC('month', s.discharge_date)
        GROUP BY s.claim_id
    )
    SELECT s.claim_id,
           DATE_DIFF('year', b.birth_date, s.admission_date) AS age,
           COALESCE(ch.n_chronic, 0) AS n_chronic, COALESCE(ch.chf, 0) AS chf, COALESCE(ch.copd, 0) AS copd,
           COALESCE(pi.prior_admits, 0) AS prior_admits,
           COALESCE(cv.medicaid_dual, 0) AS medicaid_dual,
           z.area_deprivation_index AS adi
    FROM stays_df s
    JOIN beneficiaries b USING (member_id)
    JOIN zip_area z USING (zip_code)
    LEFT JOIN chronic ch USING (claim_id)
    LEFT JOIN prior_ip pi USING (claim_id)
    LEFT JOIN cov cv USING (claim_id)
""").df()
df = stays.merge(risk, on="claim_id")
df["post"] = (pd.to_datetime(df.discharge_date) >= "2023-07-01").astype(int)
df["understory"] = (df.health_system == "Understory Health").astype(int)
df.groupby(["understory", "post"]).readmit_30d.agg(["count", "mean"]).round(3)
```

## Task 3: Naive comparison

```python
grp = df[(df.understory == 1) & (df.post == 1)].copy()
cols = ["readmit_30d", "age", "n_chronic", "chf", "copd", "prior_admits", "length_of_stay", "medicaid_dual", "adi"]
print(grp.groupby("enrolled")[cols].mean().round(3).T)
```

Enrolled and non-enrolled patients are readmitted at similar rates. But enrolled patients are older and sicker: more chronic conditions, more CHF/COPD, more prior admissions, more Medicaid/dual. The program team enrolled the patients they were most worried about.

## Task 4: Risk-adjusted logistic regression

```python
model = smf.logit(
    "readmit_30d ~ enrolled + age + n_chronic + chf + copd + prior_admits + length_of_stay + medicaid_dual + adi",
    data=grp).fit(disp=0)
print(model.summary2().tables[1].round(3))
or_ = np.exp(model.params["enrolled"])
lo, hi = np.exp(model.conf_int().loc["enrolled"])
print(f"Adjusted odds ratio for TCP enrollment: {or_:.2f} (95% CI {lo:.2f}-{hi:.2f})")
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- The overall 30-day readmission rate is about 16–18%.
- **Naive:** enrolled patients are readmitted about as often as, or more often than, those not enrolled (for example 17% vs. 13%).
- Enrolled patients have clearly higher risk factors.
- **Adjusted odds ratio** is about 0.55–0.75, close to the true effect of 0.70, with a 95% confidence interval that sits mostly or entirely below 1. With about 500 enrolled stays the estimate is noisy, and the interval can just touch 1. That's worth discussing: the program likely works, but the evidence for a 25–30% effect needs more time or a better design.

**Why the two disagree:** confounding by indication. Enrollment wasn't random; sicker patients were enrolled. Adjusting for the factors that drove both enrollment and readmission recovers the program's effect.

## Task 5: AI check

Common AI mistakes:
- It reads an odds ratio of 0.70 as "30% fewer readmissions." That's a reduction in odds; with a 15% baseline the risk reduction is about 26%.
- It calls the estimate causal without caveats. Unmeasured confounding (frailty, social support) could remain.
- It ignores the confidence interval.

## Sample recommendation

"Keep and expand the Transitional Care Program. Raw numbers make it look ineffective because the team enrolled our highest-risk patients. After adjusting for age, chronic conditions, prior admissions and social risk, enrolled patients had about 30% lower odds of readmission. Next step: enroll by a risk score so we can compare similar patients, and track 7-day follow-up as a leading indicator."
