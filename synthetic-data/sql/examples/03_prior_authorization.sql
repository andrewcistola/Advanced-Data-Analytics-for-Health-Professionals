-- Tracking electronic prior authorization (ePA) use
SELECT YEAR(submitted_datetime) AS yr,
       request_type,
       COUNT(*) AS requests,
       ROUND(AVG(CASE WHEN submission_channel = 'ePA' THEN 1.0 ELSE 0 END), 3) AS epa_share,
       MEDIAN(turnaround_hours) AS median_turnaround_hours
FROM prior_authorizations
GROUP BY YEAR(submitted_datetime), request_type
ORDER BY yr, request_type;
