# Lab 7 Solution: Provider Performance Comparison

## Task 1: Optimize the slow query

**Timing the original** (in DBeaver, look at the time under the grid). The runner script times every block:

```sql
-- the slow query, unchanged (copied from slow_scorecard.sql)
WITH visits AS (
    SELECT c.member_id, p.npi, p.practice_name, p.aco_name, c.claim_id, c.service_from_date
    FROM medical_claims c
    JOIN medical_claim_lines l ON l.claim_id = c.claim_id
    JOIN providers p ON p.npi = c.rendering_npi
    WHERE p.provider_role = 'PCP'
      AND CAST(c.service_from_date AS VARCHAR) LIKE '2024%'
      AND c.related_claim_id IS NULL
      AND (l.procedure_code BETWEEN '99202' AND '99215' OR l.procedure_code IN ('G0438', 'G0439'))
),
attrib AS (
    SELECT member_id, practice_name, aco_name
    FROM (
        SELECT member_id, practice_name, aco_name, npi,
               ROW_NUMBER() OVER (PARTITION BY member_id
                                  ORDER BY COUNT(DISTINCT claim_id) DESC, MAX(service_from_date) DESC) AS rn
        FROM visits
        GROUP BY member_id, practice_name, aco_name, npi
    ) WHERE rn = 1
)
SELECT a.practice_name,
       COUNT(DISTINCT a.member_id) AS attributed_members,
       ROUND(1000.0 * COUNT(DISTINCT CASE WHEN c.claim_setting = 'Emergency' AND c.claim_type = 'Institutional'
                                          THEN c.claim_id END)
             / COUNT(DISTINCT a.member_id), 1) AS ed_per_1000,
       ROUND(SUM(l.line_allowed) / COUNT(DISTINCT m.member_id || CAST(m.coverage_month AS VARCHAR)), 2) AS allowed_pmpm
FROM attrib a
JOIN coverage_member_months m ON m.member_id = a.member_id AND CAST(m.coverage_month AS VARCHAR) LIKE '2024%'
LEFT JOIN medical_claims c ON c.member_id = a.member_id AND CAST(c.service_from_date AS VARCHAR) LIKE '2024%'
LEFT JOIN medical_claim_lines l ON l.claim_id = c.claim_id
WHERE a.aco_name = 'Understory Health Partners'
GROUP BY a.practice_name
ORDER BY a.practice_name;
```

**What `EXPLAIN ANALYZE` shows:** the final join creates one row per *member-month × claim × line*. A member with 12 coverage months and 60 claim lines becomes 720 rows. The `COUNT(DISTINCT ...)` calls then spend their time removing that duplication. It's also why `allowed_pmpm` is wrong: every claim line is summed once per coverage month, so PMPM comes out about 12× too high.

**Optimized version:** filter with date ranges, aggregate each source to one row per member, then join.

```sql
CREATE OR REPLACE TEMP TABLE attrib_2024 AS
WITH visits AS (
    SELECT DISTINCT c.claim_id, c.member_id, c.rendering_npi AS npi, c.service_from_date
    FROM medical_claims c
    JOIN medical_claim_lines l ON l.claim_id = c.claim_id
    WHERE c.service_from_date >= DATE '2024-01-01' AND c.service_from_date < DATE '2025-01-01'
      AND c.related_claim_id IS NULL
      AND (l.procedure_code BETWEEN '99202' AND '99215' OR l.procedure_code IN ('G0438', 'G0439'))
), by_pcp AS (
    SELECT v.member_id, v.npi, COUNT(*) AS visits, MAX(v.service_from_date) AS last_visit
    FROM visits v JOIN providers p ON p.npi = v.npi
    WHERE p.provider_role = 'PCP'
    GROUP BY ALL
)
SELECT b.member_id, p.practice_name, p.aco_name
FROM by_pcp b JOIN providers p ON p.npi = b.npi
QUALIFY ROW_NUMBER() OVER (PARTITION BY b.member_id ORDER BY b.visits DESC, b.last_visit DESC) = 1;

WITH mm AS (
    SELECT member_id, COUNT(*) AS member_months
    FROM coverage_member_months WHERE coverage_year = 2024 GROUP BY member_id
), cost AS (
    SELECT member_id,
           SUM(total_allowed) AS allowed,
           COUNT(*) FILTER (WHERE claim_setting = 'Emergency' AND claim_type = 'Institutional') AS ed_visits
    FROM medical_claims
    WHERE service_from_date >= DATE '2024-01-01' AND service_from_date < DATE '2025-01-01'
      AND related_claim_id IS NULL
    GROUP BY member_id
)
SELECT a.practice_name,
       COUNT(*) AS attributed_members,
       ROUND(1000.0 * SUM(COALESCE(c.ed_visits, 0)) / COUNT(*), 1) AS ed_per_1000,
       ROUND(SUM(COALESCE(c.allowed, 0)) / SUM(mm.member_months), 2) AS allowed_pmpm
FROM attrib_2024 a
JOIN mm USING (member_id)
LEFT JOIN cost c USING (member_id)
WHERE a.aco_name = 'Understory Health Partners'
GROUP BY a.practice_name
ORDER BY a.practice_name;
```

Attributed members and ED rates match the slow query. The ED counts can differ slightly because the slow query also counted resubmitted ED claims; the optimized query counts original submissions only, which is the right definition. PMPM is now correct. Expect the optimized query to run roughly 5–20× faster, depending on the laptop.

## Tasks 2–3: Scorecard with confidence intervals

```sql
CREATE OR REPLACE TEMP TABLE scorecard AS
WITH diabetics AS (
    SELECT member_id FROM medical_claims
    WHERE YEAR(service_from_date) = 2024
      AND (dx_1 LIKE 'E11%' OR dx_2 LIKE 'E11%' OR dx_3 LIKE 'E11%' OR dx_4 LIKE 'E11%')
    GROUP BY member_id HAVING COUNT(DISTINCT claim_id) >= 2
), a1c AS (
    SELECT DISTINCT c.member_id FROM medical_claims c JOIN medical_claim_lines l USING (claim_id)
    WHERE YEAR(l.service_date) = 2024 AND l.procedure_code IN ('83036', '3044F', '3051F', '3052F', '3046F')
), mm AS (
    SELECT member_id, COUNT(*) AS member_months FROM coverage_member_months
    WHERE coverage_year = 2024 GROUP BY member_id
), cost AS (
    SELECT member_id, SUM(total_allowed) AS allowed,
           COUNT(*) FILTER (WHERE claim_setting = 'Emergency' AND claim_type = 'Institutional') AS ed_visits
    FROM medical_claims
    WHERE YEAR(service_from_date) = 2024 AND related_claim_id IS NULL
    GROUP BY member_id
)
SELECT a.practice_name,
       COUNT(*) AS attributed_members,
       COUNT(d.member_id) AS diabetic_members,
       COUNT(x.member_id) AS diabetics_tested,
       COUNT(x.member_id) * 1.0 / NULLIF(COUNT(d.member_id), 0) AS a1c_rate,
       ROUND(1000.0 * SUM(COALESCE(c.ed_visits, 0)) / COUNT(*), 1) AS ed_per_1000,
       ROUND(SUM(COALESCE(c.allowed, 0)) / SUM(mm.member_months), 2) AS allowed_pmpm
FROM attrib_2024 a
JOIN mm USING (member_id)
LEFT JOIN cost c USING (member_id)
LEFT JOIN diabetics d ON d.member_id = a.member_id
LEFT JOIN a1c x ON x.member_id = d.member_id
WHERE a.aco_name = 'Understory Health Partners'
GROUP BY a.practice_name;

WITH aco AS (SELECT SUM(diabetics_tested) * 1.0 / SUM(diabetic_members) AS aco_rate FROM scorecard)
SELECT s.practice_name, s.attributed_members, s.diabetic_members,
       ROUND(100 * s.a1c_rate, 1) AS a1c_pct,
       ROUND(100 * (s.a1c_rate - 1.96 * SQRT(s.a1c_rate * (1 - s.a1c_rate) / s.diabetic_members)), 1) AS ci_low,
       ROUND(100 * (s.a1c_rate + 1.96 * SQRT(s.a1c_rate * (1 - s.a1c_rate) / s.diabetic_members)), 1) AS ci_high,
       ROUND(100 * aco.aco_rate, 1) AS aco_pct,
       CASE WHEN s.diabetic_members < 30 THEN 'small n'
            WHEN s.a1c_rate - 1.96 * SQRT(s.a1c_rate * (1 - s.a1c_rate) / s.diabetic_members) > aco.aco_rate THEN 'above'
            WHEN s.a1c_rate + 1.96 * SQRT(s.a1c_rate * (1 - s.a1c_rate) / s.diabetic_members) < aco.aco_rate THEN 'below'
            ELSE 'not different' END AS vs_aco,
       s.ed_per_1000, s.allowed_pmpm
FROM scorecard s, aco
ORDER BY a1c_pct DESC;
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- Most practices' A1c testing rates fall within a few points of the ACO average, and their intervals overlap it ("not different").
- Several small practices land at the very top or bottom with wide intervals or the "small n" flag. Those are the ones a naive ranking would over-reward or over-penalize.
- Only a few large practices are clearly above or below average.

**Teaching point:** a ranked scorecard without denominators and intervals invites wrong conclusions. It's the core data-management problem in value-based contracts.

## Task 4: AI suggestions that commonly help or hurt

- **Help:** date ranges instead of `CAST(... AS VARCHAR) LIKE`; pre-aggregation; dropping the claim-lines join.
- **Hurt or neutral:** "add an index" (DuckDB is columnar and doesn't need one here); `SELECT DISTINCT` everywhere (slower); materializing everything into temp tables (fine for reuse, rarely faster for one query).
- **Changes the result:** removing `related_claim_id IS NULL`, or counting lines instead of claims.
