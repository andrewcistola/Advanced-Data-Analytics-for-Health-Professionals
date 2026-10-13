# Lab 2 Solution: Querying Claims Data

## Task 1: Size up 2025

```sql
SELECT COUNT(*) AS claims_2025, COUNT(DISTINCT member_id) AS members_2025
FROM medical_claims
WHERE service_from_date BETWEEN DATE '2025-01-01' AND DATE '2025-12-31';

SELECT claim_id, drg_code, length_of_stay, payer_type, total_allowed
FROM medical_claims
WHERE claim_setting = 'Inpatient'
  AND claim_type = 'Institutional'
  AND service_from_date >= DATE '2025-01-01'
  AND payer_type <> 'Self-pay'          -- self-pay "allowed" is just the discounted charge
  AND total_allowed IS NOT NULL
ORDER BY total_allowed DESC
LIMIT 10;
```

## Task 2: Understory Regional Medical Center in 2025

```sql
SELECT p.provider_name,
       COUNT(*)                                   AS claims,
       ROUND(SUM(c.total_charge))                 AS charges,
       ROUND(SUM(c.total_allowed))                AS allowed,
       ROUND(SUM(c.total_paid))                   AS paid,
       ROUND(SUM(c.total_paid) / SUM(c.total_charge), 3) AS paid_to_charge
FROM medical_claims c
JOIN providers p ON p.npi = c.billing_npi
WHERE p.provider_name = 'Understory Regional Medical Center'
  AND c.service_from_date BETWEEN DATE '2025-01-01' AND DATE '2025-12-31'
  AND c.claim_status IN ('Paid', 'Partially Paid')
GROUP BY p.provider_name;
```

**Why the ratio is low:** charges come from the hospital's chargemaster, a list price set about 3–4× what Medicare pays. Every payer pays its own contracted or fee-schedule rate. The gap between charges and allowed is a contractual adjustment, not lost money, and the patient's share comes out of allowed before the payer pays.

## Task 3: Days to pay by payer

```sql
SELECT payer_type,
       COUNT(*) AS paid_claims,
       ROUND(AVG(DATE_DIFF('day', submission_date, adjudication_date)), 1) AS avg_days_to_pay,
       MAX(DATE_DIFF('day', submission_date, adjudication_date))           AS max_days
FROM medical_claims
WHERE claim_status = 'Paid'
GROUP BY payer_type
ORDER BY avg_days_to_pay DESC;
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- The payment-to-charge ratio at the medical center is roughly 0.25–0.35.
- Medicare FFS pays fastest (about 16 days). Medicaid FFS and Medicaid managed care are slowest (about 32–38 days), with Marketplace plans close behind.

## Task 4: what the AI usually gets wrong

- It includes `Denied` or `Pending` claims, which have no or partial adjudication dates.
- It reverses the dates and gets negative days.
- It uses `service_from_date` instead of `submission_date`, which counts the provider's billing lag as payer delay.

## Sample CFO answer

"In 2025 payers paid $X million on $Y million of charges at Understory Regional Medical Center, a 30% payment-to-charge ratio. That's normal: charges are list prices, and most of the gap is contractual adjustments, not bad debt. Medicare pays in about two weeks. Medicaid plans take five weeks or more, so they're where follow-up staff will have the most impact on cash flow."
