# Lab 7: Provider Performance Comparison

**Business question:** Understory Health Partners wants a fair scorecard comparing its primary care practices on quality and cost. Which practices are truly better or worse, and which differences are just noise from small numbers?

**Skills:** SQL optimization: reading a query plan (`EXPLAIN ANALYZE`), filtering and aggregating early, avoiding row explosion from joins, using temp tables for reused results.
**Domain:** why value-based payment data management is hard: attribution, small denominators, and many tables at different grains.
**Tool:** DBeaver (watch the execution time shown under the results grid) or JupyterLab (`%%time`).
**Time:** about 75 minutes.

## Data

`medical_claims`, `medical_claim_lines`, `providers`, `coverage_member_months`. You'll reuse the **plurality attribution** logic from Lab 5, this time for **2024**.

## Tasks

### 1. Make a slow query fast
Run the slow query in `slow_scorecard.sql` (in this folder) and note its run time. Then run it with `EXPLAIN ANALYZE` in front and find the step with the most rows.

Rewrite it so it returns the same result faster. Three ideas to try:
1. Filter dates with a range (`service_from_date >= DATE '2024-01-01'`) instead of converting dates to text.
2. Aggregate each table to one row per member *before* joining.
3. Don't join claim lines unless you need a line-level column.

Record before and after times. Your attributed members and ED rates must match the slow query's. One of its columns, `allowed_pmpm`, is wrong: find out why and fix it in your version.

### 2. Build the scorecard
For each **ACO practice** (`aco_name = 'Understory Health Partners'`), using members attributed in 2024:
- attributed members
- A1c testing rate among attributed members with diabetes (2+ E11 claims in 2024; test = 83036 or 3044F/3051F/3052F/3046F)
- ED visits per 1,000 attributed members (facility ED claims: `claim_setting = 'Emergency'` and `claim_type = 'Institutional'`)
- allowed dollars per member per month (PMPM)

Save it as a temp table.

### 3. Signal or noise?
For the A1c testing rate, add the denominator and a 95% confidence interval:
`rate ± 1.96 × sqrt(rate × (1 − rate) / n)`.
Flag practices with fewer than 30 diabetic members. Which practices' rates are clearly above or below the ACO average (their interval doesn't include it)?

### 4. AI step
Paste the slow query into an AI tool and ask how to make it faster. Test each suggestion. Keep the ones that help and note any that didn't, or that changed the result.

## Deliverable

Your SQL file, a before/after timing table, and the scorecard with 2–3 sentences on which practice differences you'd trust and which you wouldn't.
