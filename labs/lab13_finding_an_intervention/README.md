# Lab 13: Finding a Potential Intervention

**Business question:** Understory Health Partners has budget for **one** program next year. Which intervention from this term gives the best return when a model picks who gets it?

**Skills:** a multi-model workflow in scikit-learn: `Pipeline` and `ColumnTransformer`, 5-fold cross-validation, comparing logistic regression, random forest and gradient boosting, and turning predictions into a targeting decision.
**Domain:** cross-domain applications: linking population health, value-based payment and revenue cycle in one decision.
**Tool:** JupyterLab.
**Time:** about 75–90 minutes.

## Definitions

**Cohort:** members with 11+ months of coverage in both 2024 and 2025.

**Target:** `high_cost` = 1 if the member is in the **top 5%** of 2025 medical allowed dollars (sum of `total_allowed` on original, non-denied claims).

**Features (2024):** age, sex, chronic condition count, flags for diabetes, heart failure, COPD and CKD, 2024 allowed dollars, ED visits, inpatient admissions, paid pharmacy fills, payer type (categorical), area deprivation index.

## Program options (assumptions for this lab)

| Program | Who it serves | Cost | Assumed effect |
|---|---|---|---|
| **A. Complex care management** (TCP-style nurse case management, Lab 9) | the members you target | $700 per member per year | reduces a participant's next-year allowed cost by **15%** |
| **B. Sulfonylurea review** (Lab 10) | members age 75+ with a 2024 glipizide fill | $150 per member | prevents **60%** of hypoglycemia ED/inpatient events (assume $6,000 per event and a 5% annual event rate) |
| **C. Mobile clinics** (Lab 11) | everyone in the top 5 zips | $250,000 per zip per year | prevents **15%** of avoidable ED visits (assume $1,200 per visit) |

These effect sizes are teaching assumptions. In real life they would come from the evaluations you did in Labs 9–11 or from published studies.

## Tasks

### 1. Predict high-cost members
Build the cohort and features with SQL. Create a `Pipeline` with a `ColumnTransformer` (scale numeric columns, one-hot encode `payer_type`) and compare three models with 5-fold cross-validated AUC: `LogisticRegression`, `RandomForestClassifier` and `HistGradientBoostingClassifier`.

### 2. Score everyone
Use `cross_val_predict(..., method="predict_proba")` with your best model, so every member gets an out-of-fold predicted probability.

### 3. Net savings for Program A
Rank members by predicted probability. For the top 1%, 5% and 10%: count members, sum their **actual 2025** allowed dollars, and compute savings (15% × allowed), cost ($700 × members) and net savings. Which threshold is best?

Then do a quick back-of-envelope estimate for Program B or C using the assumptions above. Which program wins?

### 4. AI step
Give an AI tool your numbers and ask it to critique your ROI assumptions. Decide which critiques you accept, and say why in two sentences.

## Deliverable

Your notebook plus a one-page recommendation: the program, the target group, the expected net savings, the biggest risks and assumptions, and how you'd measure whether it worked.
