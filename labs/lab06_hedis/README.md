# Lab 6: Calculating HEDIS Scores

**Business question:** Longleaf Medicare Advantage is preparing its Star Ratings submission. What are its 2024 rates on three HEDIS-style measures, and how do they compare with the other Medicare Advantage plans in the market?

**Skills:** subqueries (`WHERE ... IN (SELECT ...)`, `EXISTS`), CTEs (`WITH`), and building a measure step by step: eligible population → denominator → numerator.
**Domain:** quality measure calculation: continuous enrollment, measurement year, lookback periods.
**Tool:** DBeaver.
**Time:** about 75 minutes.

## Simplified measure specs

These follow the logic of the NCQA HEDIS measures, simplified for class. There are no hospice, palliative care or frailty exclusions, and no medical-record (hybrid) data.

| Measure | Denominator (measurement year 2024) | Numerator |
|---|---|---|
| **Breast Cancer Screening (BCS)** | Women age 52–74 on Dec 31, 2024 | Mammogram (CPT 77067) between Oct 1, 2022 and Dec 31, 2024 |
| **A1c testing for diabetes** | Age 18–75 on Dec 31, 2024, with 2+ claims with an E11 (type 2 diabetes) diagnosis in 2023–2024 | A1c test in 2024: CPT 83036 or a CPT II result code (3044F, 3051F, 3052F, 3046F) |
| **Eye exam for diabetes** | Same as above | Eye exam in 2024: 92014, 92250, 2022F or 2023F |

**Continuous enrollment** (all measures): enrolled in the *same* Medicare Advantage plan for at least 11 of the 12 months of 2024 (one gap month allowed). Report each member under that plan.

Medicare Advantage rows have `payer_type = 'Medicare Advantage'` in `coverage_member_months`.

## Tasks

### 1. Continuous-enrollment population
Build a CTE or temp table with one row per member: `member_id`, `plan_id` and months enrolled in 2024. Keep members with 11+ months. How many members does each MA plan have?

### 2. Breast cancer screening
Using your Task 1 population and `beneficiaries`, build the BCS denominator. Then use `EXISTS` (or `IN`) against `medical_claim_lines` to flag the numerator. Report the rate by plan.

### 3. Diabetes care
Build the diabetes denominator with a subquery on `medical_claims` (2+ claims with any of `dx_1`–`dx_4` starting with `E11`). Then compute both the A1c testing rate and the eye exam rate by plan.

### 4. AI step
Paste the BCS spec above into an AI tool and ask for the SQL. Run it. Does its denominator match yours? Check age (on Dec 31?), sex, the lookback window and continuous enrollment.

## Deliverable

Your SQL file plus one summary table: plan × three measures (rate and denominator), with two sentences on how Longleaf compares.
