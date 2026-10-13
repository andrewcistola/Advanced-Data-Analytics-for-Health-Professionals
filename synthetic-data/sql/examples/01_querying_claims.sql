-- Querying claims data (DuckDB SQL)
-- Claims and spending by setting and year
SELECT claim_setting,
       YEAR(service_from_date)            AS service_year,
       COUNT(*)                           AS claims,
       SUM(total_allowed)                 AS allowed,
       SUM(total_paid)                    AS paid
FROM medical_claims
WHERE claim_status IN ('Paid', 'Partially Paid')
GROUP BY claim_setting, YEAR(service_from_date)
ORDER BY claim_setting, service_year;

-- Top 10 principal diagnoses for emergency visits
SELECT c.dx_1, r.description, COUNT(*) AS visits
FROM medical_claims c
LEFT JOIN ref_icd10 r ON r.icd10_code = c.dx_1
WHERE c.claim_setting = 'Emergency' AND c.claim_type = 'Institutional'
GROUP BY c.dx_1, r.description
ORDER BY visits DESC
LIMIT 10;
