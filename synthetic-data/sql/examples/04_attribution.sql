-- Plurality-of-visits PCP attribution (joins)
WITH pcp_visits AS (
    SELECT c.member_id, p.npi, p.practice_id, p.aco_name, COUNT(*) AS visits,
           MAX(c.service_from_date) AS last_visit
    FROM medical_claims c
    JOIN medical_claim_lines l ON l.claim_id = c.claim_id
    JOIN providers p ON p.npi = c.rendering_npi
    WHERE p.provider_role = 'PCP'
      AND l.procedure_code IN ('99202','99203','99204','99205','99211','99212','99213','99214','99215',
                               'G0438','G0439','99395','99396','99397')
      AND YEAR(c.service_from_date) = 2024
    GROUP BY c.member_id, p.npi, p.practice_id, p.aco_name
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY visits DESC, last_visit DESC) AS rn
    FROM pcp_visits
)
SELECT aco_name, COUNT(*) AS attributed_members
FROM ranked WHERE rn = 1
GROUP BY aco_name
ORDER BY attributed_members DESC;
