# Lab 4: Tracking Electronic Prior Authorization Use

**Business question:** Federal rules (the CMS Interoperability and Prior Authorization final rule) are pushing payers and providers toward electronic prior authorization (ePA). How fast is ePA growing in our market, does it actually speed up decisions, and which practices should Understory target for ePA outreach?

**Skills:** `GROUP BY` on several columns, `HAVING`, percentages within groups, `MEDIAN`.
**Domain:** transaction standards (X12 278 for medical, NCPDP SCRIPT ePA for pharmacy) and electronic adoption.
**Tool:** DBeaver.
**Time:** about 60 minutes.

## Data

| Table | Use |
|---|---|
| `prior_authorizations` | one row per PA request: `request_type` (Medical/Pharmacy), `submission_channel` (ePA, Payer Portal, Fax, Phone), `submitted_datetime`, `turnaround_hours`, `decision` |
| `providers` | `practice_id`, `practice_name` and `specialty` for the requesting provider (`requesting_npi`) |

## Tasks

### 1. ePA growth
Count PA requests by year (`YEAR(submitted_datetime)`), `request_type` and `submission_channel`. Then compute the **ePA share** for each year and request type: ePA requests ÷ all requests.

### 2. Does ePA speed things up?
By `submission_channel`, compute requests, **median** `turnaround_hours`, and the approval rate (% `Approved`). Repeat with `request_type` added to the `GROUP BY`. Does the pattern hold for both?

### 3. Who's lagging?
For 2025, join `prior_authorizations` to `providers` on `requesting_npi` and compute each **practice's** request count and ePA share. Use `HAVING` to keep practices with at least 10 requests, then list the 5 practices with the lowest ePA share.

*Why `HAVING` and not `WHERE`?* Write one sentence in your SQL comments.

### 4. AI step
Ask an AI tool: *"Which transaction standards are used for electronic prior authorization for medical services vs. prescription drugs?"* Check the answer against the lecture. Did it name X12 278 and NCPDP SCRIPT? Did it mention the FHIR-based APIs in the CMS rule?

## Deliverable

Your SQL file plus a short message (3–5 sentences) to Understory's medical director: how much faster ePA is, and which practices to visit first.
