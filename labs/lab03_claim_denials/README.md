# Lab 3: Claim Denials

**Business question:** Understory's revenue cycle director wants to know which denials cost the most and how much denied money is ever recovered. She'll pick one fix for next quarter.

**Skills:** `CASE WHEN` for grouping and flags, conditional aggregation (`SUM(CASE WHEN ... THEN 1 ELSE 0 END)`), `NULL` handling.
**Domain:** claims data analytics: initial denial rate, claim adjustment reason codes (CARCs) and rework.
**Tool:** DBeaver.
**Time:** about 60–75 minutes.

## Background

- When a payer denies a claim, the remittance gives a **CARC** explaining why (for example 16 = missing information, 197 = no prior authorization).
- The **initial denial rate** counts only first submissions. A corrected or appealed claim is a *new* claim in this data, linked to the original by `related_claim_id`.
- Industry surveys put initial denial rates around 10–12% and rising.

## Data

| Table | Use |
|---|---|
| `medical_claims` | `claim_status`, `denial_reason_code`, `related_claim_id`, `account_id`, `payer_type`, `total_charge`, `total_paid` |
| `ref_carc` | CARC descriptions |

Rules for this lab:
- Leave out `Self-pay` and `Pending` claims.
- An **original submission** has `related_claim_id IS NULL`.

## Tasks

### 1. Initial denial rate
By `payer_type` and service year, compute original submissions, denied original submissions, and the denial rate (%). Which payer types are highest? Is the rate rising?

### 2. Denial categories
Use `CASE WHEN` on `denial_reason_code` to build these categories, then rank them by total denied charges (original submissions only):

| Category | CARCs |
|---|---|
| Eligibility / coordination of benefits | 22, 27, 109 |
| Coding and front-end data | 4, 11, 16 |
| Authorization | 197 |
| Medical necessity | 50 |
| Timely filing | 29 |
| Other | everything else |

### 3. What happens after a denial?
For each denied original submission, look at its `account_id`. Did any later claim on the same account get paid? Report:
- the number of denied accounts and their denied charges
- the share eventually paid, and the dollars paid
- the share never recovered

Then break it out by your Task 2 category. Which category is both large *and* rarely recovered?

### 4. AI step
Ask an AI tool for current industry benchmarks for initial claim denial rates. Compare them with your Task 1 results. Note which benchmarks the AI cited a source for and which it didn't.

## Deliverable

Your SQL file plus a 3–5 sentence recommendation naming the **one** denial category to target first, with the numbers that justify it.
