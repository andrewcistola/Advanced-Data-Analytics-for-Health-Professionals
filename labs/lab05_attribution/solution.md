# Lab 5 Solution: Patient Attribution

## Task 1: Primary care visits

```sql
CREATE OR REPLACE TEMP TABLE pc_visits AS
SELECT DISTINCT c.claim_id, c.member_id, p.npi, p.practice_name, p.aco_name,
       c.service_from_date AS visit_date
FROM medical_claims c
JOIN medical_claim_lines l ON l.claim_id = c.claim_id
JOIN providers p           ON p.npi = c.rendering_npi
WHERE p.provider_role = 'PCP'
  AND YEAR(c.service_from_date) = 2025
  AND c.related_claim_id IS NULL                 -- count each visit once, not resubmissions
  AND (l.procedure_code BETWEEN '99202' AND '99205'
       OR l.procedure_code BETWEEN '99211' AND '99215'
       OR l.procedure_code BETWEEN '99381' AND '99397'
       OR l.procedure_code IN ('G0438', 'G0439'));

SELECT COUNT(*) AS visits, COUNT(DISTINCT member_id) AS members FROM pc_visits;
```

## Task 2: Plurality attribution

```sql
CREATE OR REPLACE TEMP TABLE attribution AS
WITH by_pcp AS (
    SELECT member_id, npi, practice_name, aco_name,
           COUNT(*) AS visits, MAX(visit_date) AS last_visit
    FROM pc_visits
    GROUP BY ALL
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY visits DESC, last_visit DESC) AS rn
    FROM by_pcp
)
SELECT member_id, npi AS attributed_npi, practice_name, aco_name, visits
FROM ranked WHERE rn = 1;

SELECT COUNT(*) AS attributed_members,
       SUM(CASE WHEN aco_name = 'Understory Health Partners' THEN 1 ELSE 0 END) AS aco_members,
       ROUND(100.0 * AVG(CASE WHEN aco_name = 'Understory Health Partners' THEN 1 ELSE 0 END), 1) AS aco_pct
FROM attribution;
```

## Task 3: Assigned vs. attributed

```sql
WITH assigned AS (
    SELECT DISTINCT member_id, assigned_pcp_npi
    FROM coverage_member_months
    WHERE coverage_month = DATE '2025-12-01' AND assigned_pcp_npi IS NOT NULL
)
SELECT COUNT(*) AS hmo_members,
       SUM(CASE WHEN a.attributed_npi IS NULL THEN 1 ELSE 0 END) AS no_pc_visit,
       ROUND(100.0 * AVG(CASE WHEN a.attributed_npi IS NULL THEN 1 ELSE 0 END), 1) AS pct_no_visit,
       ROUND(100.0 * SUM(CASE WHEN a.attributed_npi = s.assigned_pcp_npi THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN a.attributed_npi IS NOT NULL THEN 1 ELSE 0 END), 0), 1) AS pct_match_among_attributed
FROM assigned s
LEFT JOIN attribution a USING (member_id);
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- About three-quarters of attributed members land with Understory Health Partners practices (all of Understory's employed practices plus about 40% of independents are in the ACO).
- Among HMO members who saw a PCP, the assigned and attributed PCP match only about two-thirds of the time. Mismatches come from plan auto-assignment and from members seeing another clinician in the same practice.
- About one in five HMO members had no primary care visit in 2025.

## Task 4: what the AI usually gets wrong

- It counts **lines** instead of claims, so a visit with a CPT II code or a vaccine counts twice.
- It uses `billing_npi` instead of `rendering_npi`. Here they're the same for professional claims, but in real data billing is often the group NPI.
- It breaks ties arbitrarily (no `last_visit` in the `ORDER BY`).
- It forgets that `ROW_NUMBER()` needs a `PARTITION BY member_id`.

## Sample note

"About N members are attributed to Understory Health Partners for 2025 based on where they got most of their primary care. For HMO members, the plan's assigned PCP matched the PCP they actually saw only about two-thirds of the time, and one in five never came in. Outreach lists built from plan assignment will miss patients and waste calls. We should use claims-based attribution for care management and reconcile it with the plans quarterly."
