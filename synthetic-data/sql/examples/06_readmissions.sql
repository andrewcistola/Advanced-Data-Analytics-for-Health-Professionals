-- 30-day all-cause readmissions after discharges from Understory hospitals
WITH stays AS (
    SELECT member_id, claim_id, billing_npi, admission_date, discharge_date, discharge_status
    FROM medical_claims
    WHERE claim_setting = 'Inpatient' AND claim_type = 'Institutional'
      AND related_claim_id IS NULL
      AND drg_code NOT IN ('795', '807', '470')          -- exclude newborns, deliveries, planned joint replacement
), flagged AS (
    SELECT s.*,
           CASE WHEN EXISTS (SELECT 1 FROM stays r
                             WHERE r.member_id = s.member_id
                               AND r.admission_date > s.discharge_date
                               AND r.admission_date <= s.discharge_date + INTERVAL '30 days')
                THEN 1 ELSE 0 END AS readmit_30d
    FROM stays s
    WHERE s.discharge_status IN ('01', '06')
)
SELECT p.provider_name,
       CASE WHEN f.discharge_date >= DATE '2023-07-01' THEN 'Post-launch' ELSE 'Pre-launch' END AS period,
       CASE WHEN cm.cm_enrollment_id IS NOT NULL THEN 'Enrolled' ELSE 'Not enrolled' END AS tcp,
       COUNT(*) AS discharges, ROUND(AVG(readmit_30d), 3) AS readmit_rate
FROM flagged f
JOIN providers p ON p.npi = f.billing_npi
LEFT JOIN care_management cm ON cm.index_claim_id = f.claim_id
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
