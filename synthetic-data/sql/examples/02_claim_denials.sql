-- Claim denials with CASE WHEN
SELECT payer_type,
       YEAR(service_from_date) AS service_year,
       COUNT(*) AS claims,
       SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) AS denied,
       ROUND(100.0 * SUM(CASE WHEN claim_status = 'Denied' THEN 1 ELSE 0 END) / COUNT(*), 1) AS denial_rate_pct
FROM medical_claims
WHERE claim_status NOT IN ('Self-pay', 'Pending')
  AND claim_frequency_code = '1' AND related_claim_id IS NULL      -- initial submissions only
GROUP BY payer_type, YEAR(service_from_date)
ORDER BY payer_type, service_year;

-- Denials grouped into categories a revenue-cycle team would act on
SELECT CASE
         WHEN denial_reason_code IN ('27', '109', '22')  THEN 'Eligibility / COB'
         WHEN denial_reason_code IN ('16', '4', '11')    THEN 'Coding & front-end data'
         WHEN denial_reason_code = '197'                 THEN 'Authorization'
         WHEN denial_reason_code = '50'                  THEN 'Medical necessity'
         WHEN denial_reason_code = '29'                  THEN 'Timely filing'
         ELSE 'Other'
       END AS denial_category,
       COUNT(*) AS denied_claims,
       SUM(total_charge) AS denied_charges
FROM medical_claims
WHERE claim_status = 'Denied'
GROUP BY 1
ORDER BY denied_charges DESC;
