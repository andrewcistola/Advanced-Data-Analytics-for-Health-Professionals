# Lab 9: Assessing Impact of a Readmissions Reduction Program

**Business question:** Understory Health launched a **Transitional Care Program** (TCP) at both of its hospitals on July 1, 2023. Nurses call patients after discharge, reconcile medications and book a follow-up visit within 7 days. Leadership sees that enrolled patients are readmitted about as often as everyone else and wants to cut the program. Did it work?

**Skills:** logistic regression (statsmodels and scikit-learn), odds ratios and confidence intervals, confounding and selection bias.
**Domain:** population health: 30-day readmissions, Medicare's Hospital Readmissions Reduction Program (HRRP), transitions of care.
**Tool:** JupyterLab.
**Time:** about 75 minutes.

## Definitions

- **Index stay:** an inpatient facility claim (`claim_setting = 'Inpatient'`, `claim_type = 'Institutional'`, original submission `related_claim_id IS NULL`), discharged home (`discharge_status` '01' or '06'), not a newborn, delivery or planned joint replacement (`drg_code` not in '795', '807', '470'), discharged by Dec 1, 2025.
- **Readmission:** any other inpatient facility stay (same exclusions) with an admission date 1–30 days after the index discharge date.
- **Enrolled:** the index claim appears in `care_management.index_claim_id` with `program_name = 'Transitional Care Program'`.
- **Analysis group:** index stays at Understory Regional Medical Center or Understory Community Hospital discharged on or after July 1, 2023.

## Tasks

### 1. Build the index-stay table
One row per index stay with `member_id`, `claim_id`, hospital, admission and discharge dates, length of stay, and a `readmit_30d` flag.

### 2. Add risk factors from claims
For each index stay add:
- age at admission
- number of chronic condition groups diagnosed in the 12 months before admission (the code-prefix list is in the starter code)
- inpatient admissions in the prior 12 months
- length of stay
- Medicaid or dual eligible in the discharge month (from `coverage_member_months`)
- area deprivation index of the member's zip (`zip_area`)

### 3. The naive comparison
In the analysis group, compare readmission rates for enrolled vs. not enrolled. Then compare their average risk factors. Who got enrolled?

### 4. Adjust for risk
Fit a logistic regression in the analysis group: `readmit_30d ~ enrolled + risk factors`. Report the **odds ratio for enrollment** with its 95% confidence interval. Explain in two sentences why it differs from Task 3.

### 5. AI step
Paste your regression output into an AI tool and ask it to interpret the enrollment coefficient. Check its interpretation: odds ratio vs. risk ratio, causal claims, and confidence intervals.

## Starter code

```python
import duckdb, numpy as np, pandas as pd
import statsmodels.formula.api as smf
con = duckdb.connect("../data/health_analytics.duckdb", read_only=True)

CHRONIC_PREFIXES = {   # condition group -> ICD-10 prefixes
    "htn": ("I10", "I12"), "lipids": ("E78",), "diabetes": ("E11",), "cad": ("I25",), "chf": ("I50",),
    "afib": ("I48",), "copd": ("J44",), "asthma": ("J45",), "ckd": ("N18",), "depression": ("F32", "F33"),
    "dementia": ("F03",), "oud": ("F11",),
}
```

## Deliverable

Your notebook plus a 5-sentence recommendation to leadership: keep, expand or cut the TCP, and why the raw comparison was misleading.
