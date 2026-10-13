-- Simplified HbA1c testing rate for members with diabetes (subqueries)
-- Denominator: members 18-75 with 2 or more diabetes-coded claims in 2024 and 12 months of 2024 coverage
SELECT COUNT(*) AS denominator,
       SUM(CASE WHEN member_id IN (
               SELECT c.member_id FROM medical_claims c
               JOIN medical_claim_lines l ON l.claim_id = c.claim_id
               WHERE l.procedure_code IN ('83036','3044F','3051F','3052F','3046F')
                 AND YEAR(l.service_date) = 2024) THEN 1 ELSE 0 END) AS numerator
FROM beneficiaries b
WHERE DATEDIFF('year', b.birth_date, DATE '2024-12-31') BETWEEN 18 AND 75
  AND member_id IN (SELECT member_id FROM medical_claims
                    WHERE YEAR(service_from_date) = 2024
                      AND (dx_1 LIKE 'E11%' OR dx_2 LIKE 'E11%' OR dx_3 LIKE 'E11%' OR dx_4 LIKE 'E11%')
                    GROUP BY member_id HAVING COUNT(*) >= 2)
  AND member_id IN (SELECT member_id FROM coverage_member_months
                    WHERE coverage_year = 2024 GROUP BY member_id HAVING COUNT(*) = 12);
