# Lab 8: Closing Coding Gaps

**Business question:** A Medicare Advantage plan's risk scores, and so its revenue, depend on chronic conditions being documented **every year**. Which members with a hierarchical condition category (HCC) coded last year are most likely to go undocumented this year, so care teams can schedule an annual wellness visit before year-end?

**Skills:** your first scikit-learn workflow: build a feature table with SQL, `train_test_split`, fit `LogisticRegression` and `DecisionTreeClassifier`, `predict_proba`, and compare models with AUC.
**Domain:** risk adjustment: HCCs, annual recapture, and the compliance line. Document what's real; never code what isn't supported by the visit.
**Tool:** JupyterLab.
**Time:** about 75 minutes.

## Key ideas

- CMS pays MA plans more for members with documented chronic conditions. A condition counts only if a provider documents it on a face-to-face claim **in that calendar year**.
- A **recapture gap** is an HCC documented last year that hasn't been documented this year. Some gaps are real (the condition resolved); many are just missed documentation.
- `ref_hcc_crosswalk` maps ICD-10 codes to HCCs. **Its coefficients are illustrative, not official CMS values.**

## Data

`medical_claims` (`dx_1`–`dx_10`), `medical_claim_lines`, `coverage_member_months`, `beneficiaries`, `providers`, `ref_hcc_crosswalk`.

Starter code to connect:

```python
import duckdb, pandas as pd
con = duckdb.connect("../data/health_analytics.duckdb", read_only=True)
```

DuckDB can turn the ten diagnosis columns into rows with `UNPIVOT`:

```sql
UNPIVOT medical_claims ON dx_1, dx_2, dx_3, dx_4, dx_5, dx_6, dx_7, dx_8, dx_9, dx_10 INTO NAME dx_position VALUE dx
```

## Tasks

### 1. Who had an HCC, and was it recaptured?
Limit to members enrolled in Medicare Advantage for at least 11 months of **both** 2023 and 2024. Build one row per **member × HCC** coded in 2023, with a column `recaptured` = 1 if the same HCC appears on any of that member's 2024 claims. Leave out HCCs for acute events that aren't expected to recur every year: 36 (severe acute diabetes complications), 225 (acute on chronic heart failure) and 249 (stroke). What share of 2023 HCCs were recaptured? Which HCCs are recaptured least often?

### 2. Build features (from 2023 claims)
For each member: number of PCP visits, specialist visits, whether they had an annual wellness visit (G0438/G0439), age, and dual-eligible status (`dual_status` not null). Join the features onto the Task 1 table, and add the **HCC itself** as a feature with `pd.get_dummies(df["hcc"], prefix="hcc")`. Some conditions are documented much more reliably than others.

### 3. Train and compare two models
Split 75/25 with `train_test_split(..., stratify=y, random_state=42)`. Fit a `LogisticRegression` (scale the features first) and a `DecisionTreeClassifier(max_depth=4)`. Report each model's test AUC. Which features matter most? Look at the logistic coefficients and the tree's `feature_importances_`.

### 4. Build the outreach list
Rebuild the same features with **2024** data for members with HCCs coded in 2024. Score them with your better model, and list the 100 member-HCC pairs **least** likely to be recaptured in 2025 (lowest predicted probability).

### 5. AI step
Ask an AI tool: *"Where is the line between closing risk adjustment coding gaps and upcoding?"* Write two sentences in your own words.

## Deliverable

Your notebook plus the 100-pair outreach list, with 2–3 sentences on what drives missed recapture and what the care team should do.
