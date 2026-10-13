# Lab 10: Finding Novel Root Causes of Diabetes Complications

**Business question:** The health plan's diabetes care team knows that A1c and medication adherence matter. What *else* predicts serious complications, especially drivers a complex case management program could act on?

**Skills:** random forests in scikit-learn, permutation importance, and checking a model's hint with a simple cross-tab.
**Domain:** evidence on complex case management: targeting the right members with the right intervention.
**Tool:** JupyterLab.
**Time:** about 75 minutes.

## Definitions

**Cohort:** members with 2+ claims with an E11 (type 2 diabetes) diagnosis in 2021–2022, with coverage in both January 2023 and December 2025.

**Outcome (2023–2025):** any of these on a claim:

| Complication | How to find it |
|---|---|
| Hypoglycemia | ED or inpatient claim with `dx_1` = `E11.649` |
| Hyperglycemic crisis | inpatient claim with `dx_1` in (`E11.10`, `E11.00`, `E11.65`) |
| Foot ulcer or amputation | any claim with `E11.621` in `dx_1`–`dx_4`, or `drg_code` in ('616', '617') |
| New retinopathy, nephropathy or neuropathy | `E11.319`, `E11.22` or `E11.42` in `dx_1`–`dx_4`, for members who did **not** have that code in 2021–2022 |

**Features (all from 2021–2022):**
- **PDC** (proportion of days covered) for diabetes drugs: total `days_supply` of paid fills for metformin, glipizide, insulin glargine, semaglutide, tirzepatide or empagliflozin ÷ (730 × number of distinct diabetes drugs filled), capped at 1
- `sulfonylurea` = any paid glipizide fill, and `insulin` = any insulin glargine fill
- `gap_months` = 24 − months with coverage
- `pcp_visits` = PCP office visits
- `ckd` = any N18 diagnosis
- `age` on Jan 1, 2023
- `adi` = the zip's area deprivation index
- `ed_visits` = ED facility claims

## Tasks

### 1. Build the cohort and outcome
Use SQL to build one row per cohort member with `complication` = 1 if they had any outcome event in 2023–2025. Also keep a separate flag `hypoglycemia`.

### 2. Build the features
Add the features above with SQL (or pandas). Check for missing values. A member with no diabetes fills should get PDC = 0.

### 3. Random forest and permutation importance
Split 70/30 (stratified, `random_state=42`). Fit `RandomForestClassifier(n_estimators=300, min_samples_leaf=20, random_state=42)`. Report the test AUC, then compute `permutation_importance` on the test set and rank the features.

### 4. Check a hint
The forest ranks `age` and `sulfonylurea` as important, but importance doesn't say *how*. Cross-tab the **hypoglycemia** rate by `age >= 75` × `sulfonylurea`. What do you see?

### 5. AI step
Ask an AI tool: *"Do sulfonylureas increase hypoglycemia risk in older adults?"* Compare its answer with the American Geriatrics Society Beers Criteria and with your Task 4 table.

## Deliverable

Your notebook plus a one-paragraph brief to the diabetes care team: the top drivers, the one you think is most *actionable*, and the intervention it suggests.
