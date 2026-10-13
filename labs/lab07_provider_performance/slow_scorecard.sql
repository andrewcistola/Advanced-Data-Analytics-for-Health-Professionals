-- Lab 7: a deliberately slow scorecard query.
-- It returns, for each 2024 ACO practice: attributed members, ED visits per 1,000 and allowed PMPM.
-- It joins every claim line before aggregating and filters dates as text. One column also has a bug.
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
