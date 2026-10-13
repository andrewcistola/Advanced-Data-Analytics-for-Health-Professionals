# Lab 4 Solution: Tracking Electronic Prior Authorization Use

## Task 1: ePA growth

```sql
SELECT YEAR(submitted_datetime) AS yr, request_type, submission_channel, COUNT(*) AS requests
FROM prior_authorizations
GROUP BY ALL
ORDER BY yr, request_type, submission_channel;

SELECT YEAR(submitted_datetime) AS yr, request_type,
       COUNT(*) AS requests,
       ROUND(100.0 * SUM(CASE WHEN submission_channel = 'ePA' THEN 1 ELSE 0 END) / COUNT(*), 1) AS epa_share_pct
FROM prior_authorizations
WHERE YEAR(submitted_datetime) BETWEEN 2021 AND 2025
GROUP BY ALL
ORDER BY request_type, yr;
```

## Task 2: Turnaround and approval by channel

```sql
SELECT submission_channel,
       COUNT(*) AS requests,
       ROUND(MEDIAN(turnaround_hours), 1) AS median_hours,
       ROUND(100.0 * AVG(CASE WHEN decision = 'Approved' THEN 1 ELSE 0 END), 1) AS approval_pct
FROM prior_authorizations
GROUP BY submission_channel
ORDER BY median_hours;

SELECT request_type, submission_channel,
       COUNT(*) AS requests,
       ROUND(MEDIAN(turnaround_hours), 1) AS median_hours,
       ROUND(100.0 * AVG(CASE WHEN decision = 'Approved' THEN 1 ELSE 0 END), 1) AS approval_pct
FROM prior_authorizations
GROUP BY request_type, submission_channel
ORDER BY request_type, median_hours;
```

## Task 3: Practices lagging on ePA (2025)

```sql
SELECT p.practice_name, p.specialty,
       COUNT(*) AS requests_2025,
       ROUND(100.0 * AVG(CASE WHEN a.submission_channel = 'ePA' THEN 1 ELSE 0 END), 1) AS epa_share_pct
FROM prior_authorizations a
JOIN providers p ON p.npi = a.requesting_npi
WHERE YEAR(a.submitted_datetime) = 2025
GROUP BY p.practice_name, p.specialty
HAVING COUNT(*) >= 15          -- HAVING filters groups after aggregation, and WHERE runs before COUNT(*) exists
ORDER BY epa_share_pct
LIMIT 5;
```

## Expected results

Exact numbers are in `expected_results.md`. The pattern:

- **Growth:** medical ePA share rises from about 2% in 2021 to about 20–25% in 2025. Pharmacy ePA starts higher (about 35%) and reaches about 75–80%, because pharmacy ePA is built into most EHR prescribing workflows.
- **Speed:** median turnaround is a few hours for ePA (many are approved in real time), about 30 hours through payer portals, about 20 hours by phone, and 3+ days by fax. Approval rates are highest for ePA (about 90–94%) and lowest for fax (about 82–85%).
- **Laggards:** one high-volume pulmonology group (sleep studies, CPAP and CT) sends hundreds of requests a year, almost all by fax. It's the single biggest opportunity, ahead of the two cardiology groups. Students should notice that volume matters as much as the share.

## Task 4: AI check

Good answers name **X12 278** (HIPAA standard for medical services review), **NCPDP SCRIPT** ePA transactions for pharmacy, and the **HL7 FHIR** Prior Authorization API (Da Vinci implementation guides) that the CMS rule requires payers to support by 2027. Common AI errors: calling NCPDP "D.0" the ePA standard (D.0 is the pharmacy claim standard), or saying the CMS rule covers prescription drugs (its API requirements exclude drugs).

## Sample message

"Electronic PA decisions come back in a median of a few hours vs. more than three days by fax, and they're approved more often. Pharmacy requests are now mostly electronic, but medical requests are still mostly fax and portal. Gainesville Lung & Sleep alone sends nearly 400 requests a year, almost all by fax, followed by the two cardiology groups. A short visit to set up ePA in their EHR would speed up care for their patients and cut staff time."
