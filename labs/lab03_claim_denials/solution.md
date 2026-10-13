# Lab 3 Solution: Claim Denials

## Task 1: Initial denial rate

```sql
SELECT payer_type,
       YEAR(service_from_date) AS service_year,
       COUNT(*) AS original_claims,
       SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied,
       ROUND(100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 1) AS denial_rate_pct
FROM medical_claims
WHERE related_claim_id IS NULL
  AND claim_status NOT IN ('Self-pay', 'Pending')
GROUP BY payer_type, YEAR(service_from_date)
ORDER BY payer_type, service_year;
```

## Task 2: Denial categories

```sql
SELECT CASE
         WHEN denial_reason_code IN ('22', '27', '109') THEN 'Eligibility / COB'
         WHEN denial_reason_code IN ('4', '11', '16')   THEN 'Coding and front-end data'
         WHEN denial_reason_code = '197'                THEN 'Authorization'
         WHEN denial_reason_code = '50'                 THEN 'Medical necessity'
         WHEN denial_reason_code = '29'                 THEN 'Timely filing'
         ELSE 'Other'
       END AS denial_category,
       COUNT(*)                 AS denied_claims,
       ROUND(SUM(total_charge)) AS denied_charges
FROM medical_claims
WHERE claim_status = 'Denied' AND related_claim_id IS NULL
GROUP BY 1
ORDER BY denied_charges DESC;
```

## Task 3: What happens after a denial?

```sql
WITH denied AS (
    SELECT account_id, claim_id, total_charge,
           CASE
             WHEN denial_reason_code IN ('22', '27', '109') THEN 'Eligibility / COB'
             WHEN denial_reason_code IN ('4', '11', '16')   THEN 'Coding and front-end data'
             WHEN denial_reason_code = '197'                THEN 'Authorization'
             WHEN denial_reason_code = '50'                 THEN 'Medical necessity'
             WHEN denial_reason_code = '29'                 THEN 'Timely filing'
             ELSE 'Other'
           END AS denial_category
    FROM medical_claims
    WHERE claim_status = 'Denied' AND related_claim_id IS NULL
),
later_paid AS (
    SELECT account_id, SUM(total_paid) AS paid_later
    FROM medical_claims
    WHERE related_claim_id IS NOT NULL AND claim_status IN ('Paid', 'Partially Paid')
    GROUP BY account_id
)
SELECT d.denial_category,
       COUNT(*)                                                     AS denied_accounts,
       ROUND(SUM(d.total_charge))                                   AS denied_charges,
       ROUND(100.0 * AVG(CASE WHEN p.account_id IS NOT NULL THEN 1 ELSE 0 END), 1) AS pct_eventually_paid,
       ROUND(SUM(COALESCE(p.paid_later, 0)))                        AS dollars_paid_later
FROM denied d
LEFT JOIN later_paid p USING (account_id)
GROUP BY ROLLUP (d.denial_category)
ORDER BY denied_charges DESC;
```

(`ROLLUP` adds a total row where `denial_category` is NULL. It's fine if students compute the total separately.)

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- Medicare FFS has the lowest initial denial rate (about 4–5%). Medicare Advantage has the highest (about 9% in 2021, rising to about 12% in 2025). Commercial, Marketplace and Medicaid plans fall in between, and all payer types trend up.
- **Coding and front-end data** (mostly CARC 16) is the largest category by count and by charges, and most of it is recovered through corrected claims (about 80–90%).
- **Eligibility** denials (27/109) are mostly rebilled to the right payer.
- **Timely filing**, **authorization** and **medical necessity** are smaller but rarely recovered: timely filing never, authorization and medical necessity only about a quarter of the time. Medical necessity denials carry high dollars per claim (often inpatient).

## Sample recommendation

"Front-end data errors (CARC 16, 11, 4) are our largest denial category, about $X of denied charges a year. Most are eventually paid, but each one costs rework and 1–2 months of delay. Medical necessity and authorization denials are smaller, but three-quarters are never recovered. I'd target front-end claim edits first for volume. If the goal is dollars permanently lost, prior-authorization checks for Medicare Advantage are the better target."

Either recommendation is acceptable if the numbers support it.
