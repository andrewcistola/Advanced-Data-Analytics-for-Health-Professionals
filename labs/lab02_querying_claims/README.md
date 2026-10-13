# Lab 2: Querying Claims Data

**Business question:** Understory Health's CFO asks: how much did payers pay us last year, and which payers are slowest to pay?

**Skills:** `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, `DISTINCT`, aggregates (`COUNT`, `SUM`, `AVG`), date filters.
**Domain:** revenue cycle basics: charges vs. allowed vs. paid, patient responsibility, days to payment.
**Tool:** DBeaver.
**Time:** about 60 minutes.

## Background

- **Charge:** the hospital's list price (from its chargemaster). Few payers ever pay it.
- **Allowed amount:** what the payer's contract or fee schedule says the service is worth.
- **Paid amount:** what the payer actually paid, which is the allowed amount minus the patient's share (deductible, coinsurance, copay).
- **Days to pay:** time from when the claim was submitted to when the payer adjudicated it.

## Data

| Table | Use |
|---|---|
| `medical_claims` | one row per claim: dates, setting, payer, charges, allowed, paid, status |
| `providers` | look up the billing provider's name |

Useful columns: `service_from_date`, `claim_setting`, `claim_type`, `claim_status`, `payer_type`, `total_charge`, `total_allowed`, `total_paid`, `submission_date`, `adjudication_date`, `billing_npi`.

## Tasks

### 1. Size up 2025
- How many claims had a 2025 service date, and how many distinct members do they cover?
- List the 10 most expensive **inpatient facility** claims (`claim_setting = 'Inpatient'` and `claim_type = 'Institutional'`) by allowed amount, leaving out self-pay claims. Show the claim ID, DRG, length of stay, payer type and allowed amount.

### 2. Understory Regional Medical Center in 2025
For claims billed by **Understory Regional Medical Center** (find its NPI in `providers`) with a 2025 service date and status `Paid` or `Partially Paid`:
- total charges, allowed and paid
- the payment-to-charge ratio (paid ÷ charges)

In one sentence, explain why the ratio is so far below 100%.

### 3. Days to pay by payer
For all `Paid` claims, compute the average and maximum number of days from `submission_date` to `adjudication_date`, by `payer_type`. Sort from slowest to fastest.

*Hint:* `DATE_DIFF('day', submission_date, adjudication_date)`.

### 4. AI step
Give an AI tool the column names above and ask it to write the Task 3 query. Run it. Does it match your result? If not, why? Common culprits are including denied claims, or getting the dates in the wrong order.

## Deliverable

Your SQL file plus a 3–5 sentence answer to the CFO covering: total paid at the medical center, the payment-to-charge ratio and what it means, and the slowest and fastest payers.
