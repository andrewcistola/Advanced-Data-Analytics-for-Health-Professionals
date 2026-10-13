# Lab 6 Solution: Calculating HEDIS Scores

## Task 1: Continuous-enrollment population

```sql
CREATE OR REPLACE TEMP TABLE ce_2024 AS
SELECT member_id, plan_id, ANY_VALUE(plan_name) AS plan_name, COUNT(*) AS months
FROM coverage_member_months
WHERE coverage_year = 2024 AND payer_type = 'Medicare Advantage'
GROUP BY member_id, plan_id
HAVING COUNT(*) >= 11;

SELECT plan_name, COUNT(*) AS members FROM ce_2024 GROUP BY plan_name ORDER BY members DESC;
```

## Task 2: Breast cancer screening

```sql
WITH denom AS (
    SELECT ce.member_id, ce.plan_name
    FROM ce_2024 ce
    JOIN beneficiaries b USING (member_id)
    WHERE b.sex = 'F'
      AND DATE_DIFF('year', b.birth_date, DATE '2024-12-31') BETWEEN 52 AND 74
)
SELECT plan_name,
       COUNT(*) AS denominator,
       SUM(CASE WHEN EXISTS (
               SELECT 1
               FROM medical_claims c
               JOIN medical_claim_lines l ON l.claim_id = c.claim_id
               WHERE c.member_id = d.member_id
                 AND l.procedure_code = '77067'
                 AND l.service_date BETWEEN DATE '2022-10-01' AND DATE '2024-12-31')
           THEN 1 ELSE 0 END) AS numerator,
       ROUND(100.0 * numerator / denominator, 1) AS bcs_rate
FROM denom d
GROUP BY plan_name
ORDER BY bcs_rate DESC;
```

`DATE_DIFF('year', ...)` counts calendar-year boundaries, so it can overstate age by up to a year. A stricter version compares `birth_date` with `DATE '2024-12-31' - INTERVAL 52 YEAR`. For this lab either is accepted.

## Task 3: Diabetes care

```sql
WITH diabetics AS (
    SELECT member_id
    FROM medical_claims
    WHERE YEAR(service_from_date) IN (2023, 2024)
      AND (dx_1 LIKE 'E11%' OR dx_2 LIKE 'E11%' OR dx_3 LIKE 'E11%' OR dx_4 LIKE 'E11%')
    GROUP BY member_id
    HAVING COUNT(DISTINCT claim_id) >= 2
),
denom AS (
    SELECT ce.member_id, ce.plan_name
    FROM ce_2024 ce
    JOIN beneficiaries b USING (member_id)
    WHERE ce.member_id IN (SELECT member_id FROM diabetics)
      AND DATE_DIFF('year', b.birth_date, DATE '2024-12-31') BETWEEN 18 AND 75
),
codes_2024 AS (
    SELECT DISTINCT c.member_id, l.procedure_code
    FROM medical_claims c
    JOIN medical_claim_lines l ON l.claim_id = c.claim_id
    WHERE YEAR(l.service_date) = 2024
      AND l.procedure_code IN ('83036', '3044F', '3051F', '3052F', '3046F', '92014', '92250', '2022F', '2023F')
)
SELECT d.plan_name,
       COUNT(*) AS denominator,
       ROUND(100.0 * AVG(CASE WHEN d.member_id IN (SELECT member_id FROM codes_2024
                                                   WHERE procedure_code IN ('83036', '3044F', '3051F', '3052F', '3046F'))
                              THEN 1 ELSE 0 END), 1) AS a1c_test_rate,
       ROUND(100.0 * AVG(CASE WHEN d.member_id IN (SELECT member_id FROM codes_2024
                                                   WHERE procedure_code IN ('92014', '92250', '2022F', '2023F'))
                              THEN 1 ELSE 0 END), 1) AS eye_exam_rate
FROM denom d
GROUP BY d.plan_name
ORDER BY d.plan_name;
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- BCS rates of roughly 78–85%.
- A1c testing around 80–92%.
- Eye exams around 40–50%, the weakest measure for every plan.
- A few points of spread between plans. The D-SNP (Osprey Dual Complete) has the smallest denominators, so its rates swing the most from year to year.

## Task 4: what the AI usually gets wrong

- It computes age on today's date instead of Dec 31 of the measurement year.
- It uses a 12-month or 2-year lookback instead of 27 months (Oct 1 two years prior).
- It drops continuous enrollment or allows any MA plan instead of the same plan.
- It includes men (missing the sex filter) or uses diagnostic mammography codes.
