-- Provider-level billing profile (features for k-means)
SELECT c.billing_npi,
       p.provider_name, p.specialty,
       COUNT(DISTINCT c.claim_id)                                   AS claims,
       COUNT(DISTINCT c.member_id)                                  AS patients,
       COUNT(DISTINCT c.claim_id) * 1.0 / COUNT(DISTINCT c.member_id) AS claims_per_patient,
       SUM(l.units) * 1.0 / COUNT(DISTINCT c.claim_id)              AS units_per_claim,
       SUM(c.total_charge) / COUNT(DISTINCT c.claim_id)             AS charge_per_claim,
       AVG(CASE WHEN l.procedure_code = '99215' THEN 1.0
                WHEN l.procedure_code IN ('99212','99213','99214') THEN 0 END) AS share_99215
FROM medical_claims c
JOIN medical_claim_lines l ON l.claim_id = c.claim_id
JOIN providers p ON p.npi = c.billing_npi
WHERE c.related_claim_id IS NULL
GROUP BY 1, 2, 3
HAVING COUNT(DISTINCT c.claim_id) >= 50;
