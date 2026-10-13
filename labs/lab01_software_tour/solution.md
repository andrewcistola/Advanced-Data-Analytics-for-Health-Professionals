# Lab 1 Solution: Software Tour

## Task 2: Keys

| Table | Primary key |
|---|---|
| `beneficiaries` | `member_id` |
| `medical_claims` | `claim_id` |
| `providers` | `npi` |

Other keys students might find: `medical_claim_lines` (`claim_id`, `line_number`), `coverage_member_months` (`member_id`, `coverage_month`), `pharmacy_claims` (`rx_claim_id`).

```sql
-- Each pair of numbers should match (unique key)
SELECT COUNT(*) AS rows_, COUNT(DISTINCT member_id) AS distinct_keys FROM beneficiaries;
SELECT COUNT(*) AS rows_, COUNT(DISTINCT claim_id)  AS distinct_keys FROM medical_claims;
SELECT COUNT(*) AS rows_, COUNT(DISTINCT npi)       AS distinct_keys FROM providers;
```

Foreign keys (any two):

| Child column | Parent |
|---|---|
| `medical_claim_lines.claim_id` | `medical_claims.claim_id` |
| `medical_claims.member_id` | `beneficiaries.member_id` |
| `medical_claims.billing_npi` (also `rendering_npi`) | `providers.npi` |
| `pharmacy_claims.prescriber_npi` | `providers.npi` |
| `beneficiaries.zip_code` | `zip_area.zip_code` |

```sql
-- Lines joined to their claim header
SELECT c.claim_id, c.claim_setting, l.line_number, l.procedure_code, l.line_allowed
FROM medical_claims c
JOIN medical_claim_lines l ON l.claim_id = c.claim_id
LIMIT 10;

-- Claims joined to the billing provider
SELECT c.claim_id, p.provider_name, p.specialty
FROM medical_claims c
JOIN providers p ON p.npi = c.billing_npi
LIMIT 10;
```

## Task 3: One member's story

Any member works. This picks a member with diabetes, inpatient care and prescriptions, so the story is interesting.

```sql
CREATE OR REPLACE TEMP VIEW my_member AS
SELECT c.member_id
FROM medical_claims c
WHERE c.claim_setting = 'Inpatient' AND c.dx_1 LIKE 'E11%'
  AND c.member_id IN (SELECT member_id FROM pharmacy_claims)
ORDER BY c.member_id
LIMIT 1;

-- Who
SELECT b.member_id, b.sex, b.birth_date,
       DATE_DIFF('year', b.birth_date, DATE '2025-12-31') AS age_end_2025,
       b.zip_code, b.county, b.death_date
FROM beneficiaries b JOIN my_member USING (member_id);

-- Coverage over time: one row per continuous plan spell
SELECT payer_type, plan_name, MIN(coverage_month) AS first_month, MAX(coverage_month) AS last_month,
       COUNT(*) AS months
FROM coverage_member_months JOIN my_member USING (member_id)
GROUP BY payer_type, plan_name
ORDER BY first_month;

-- Care by setting
SELECT claim_setting, COUNT(*) AS claims, ROUND(SUM(total_allowed)) AS allowed
FROM medical_claims JOIN my_member USING (member_id)
GROUP BY claim_setting ORDER BY claims DESC;

-- Top diagnoses
SELECT c.dx_1, r.description, COUNT(*) AS claims
FROM medical_claims c JOIN my_member USING (member_id)
LEFT JOIN ref_icd10 r ON r.icd10_code = c.dx_1
GROUP BY c.dx_1, r.description ORDER BY claims DESC LIMIT 5;

-- Prescriptions
SELECT generic_name, COUNT(*) AS fills, MIN(fill_date) AS first_fill, MAX(fill_date) AS last_fill
FROM pharmacy_claims JOIN my_member USING (member_id)
WHERE claim_status = 'Paid'
GROUP BY generic_name ORDER BY fills DESC;
```

**What a good story looks like:** "Member M01xxxxx is a 71-year-old woman in Marion County. She was on a Medicare Advantage HMO the whole period. She has type 2 diabetes, hypertension and CKD. She saw her PCP about every three months, had one inpatient stay for a hyperglycemic crisis in 2023, and fills metformin, glipizide and atorvastatin, with gaps between fills." Grade on whether the queries support each statement.

## Task 4: AI check

A correct answer says the **header** holds what applies to the whole claim: member, dates, billing provider, diagnoses, payer, totals, status, DRG for inpatient. The **lines** hold each billed service: procedure/revenue code, modifiers, units, line charge and allowed amount, line-level denial. Common AI misses:
- not mentioning that institutional claims use revenue codes
- saying diagnoses are on lines (in 837 claims they're on the header, with pointers from lines)
- treating paid amounts as only line-level (inpatient DRG payment is claim-level here)
