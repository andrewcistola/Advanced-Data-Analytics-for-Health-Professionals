# Instructor notes: what's built into the data

These are the patterns the generator plants deliberately so each lab has a findable answer. The ground truth is also in the `answer_key` schema. **Keep this file and `answer_key` away from students.**

## Claim denials
- The initial denial rate varies by payer. Medicare FFS is lowest (about 3–5%). Medicare Advantage and Medicaid managed care are highest, and MA climbs year over year.
- Denial rates rise about 7% per year relative to 2021 (`DENIAL_TREND` in `engine.py`).
- Reasons follow realistic causes:
  - CO-27/109 when a provider bills the old plan within two months of a coverage change. This clusters around January plan switches and the 2023–24 Medicaid unwinding.
  - CO-29 for late submissions.
  - CO-197 for missing prior auth.
  - CO-50 for short inpatient stays (an observation-vs-inpatient story) and advanced imaging.
  - CO-16/11/4 for coding and data errors. These are lower at providers with better billing quality, and Understory's facilities bill well.
- Line-level denials: CO-97 (venipuncture bundled with an office visit), CO-96 (Medicare doesn't cover routine eye exams without a diabetes dx) and CO-119 (commercial PT over 20 visits a year).
- Reworks appear as new claims linked by `related_claim_id`: corrected claims (frequency 7), appeals (`appeal_outcome`) and rebills to the correct payer. In `hospital_payments`, each account's ledger shows the full denial → appeal → payment or write-off history.

## Electronic prior authorization
- Each practice has an ePA adoption month (`answer_key.provider_traits.epa_adopt_month`). Some never adopt. Understory practices adopt by mid-2022.
- After adoption about 80% of medical PAs go through ePA. Before adoption it's mostly fax, with portal use growing.
- Typical turnaround: ePA about 2–6 hours, with a growing share approved in real time; portal about 30 hours; fax about 80 hours.
- ePA approval rates are higher (more complete submissions).
- Pharmacy requests follow the prescriber's practice: about 88% ePA once the practice has adopted it, 30–55% before.
- Pharmacy reject 75 → PA → paid fill sequences appear in `pharmacy_claims`. PA approvals don't carry over when a member changes plans.

## Attribution
- About 80% of HMO-type members have an `assigned_pcp_npi` equal to their usual PCP. The rest were auto-assigned to a PCP they may never see, so claims-based attribution disagrees with assignment.
- *Understory Health Partners* is the hospital system's ACO. It includes every Understory primary care practice plus about 40% of the independent practices.

## HEDIS and provider performance
- Practice quality (`provider_traits.quality`) drives A1c testing, diabetic eye exams, mammography, colorectal screening, preventive visits, CPT II reporting and 7-day post-discharge follow-up.
- ACO practices (especially Understory's own) score higher on average. Some small practices are noisy, which is useful for teaching about small denominators.
- Blood pressure control (CPT II 3074F–3080F) depends on medication adherence, age 75+ and area deprivation.
- Statin use among diabetics 40–75 is about 62% (SPD).

## Coding gaps
- A routine PCP visit always documents the condition it's about, but documents each of the member's *other* chronic conditions only about 45% × the practice's `doc_rate` of the time (35% × on acute visits, 50% on ED claims). Annual wellness and preventive visits document about 97%. Specialists always code their own conditions.
- As a result, members with few PCP visits and no wellness visit often lose an HCC for a year even though they still have it. Those features predict missed recapture in Lab 8.
- `answer_key.member_truth` holds true onset dates.
- Rx-based suspects:
  - insulin or GLP-1 fills without an E11 dx that year
  - inhalers without J44
  - apixaban without I48
  - donepezil without F03

## Readmission reduction program
- The **Transitional Care Program** launched at both Understory hospitals on **2023-07-01**. Enrollment is recorded in `care_management`, linked through `index_claim_id`.
- True effect: odds ratio of readmission **0.70** for enrolled patients. It also raises 7-day follow-up by about 30 percentage points, and follow-up itself lowers readmission risk (log-odds −0.45).
- **Selection bias:** sicker patients are much more likely to be enrolled, so the naive comparison makes the program look harmful or useless. Enrollment depends only on risk factors visible in claims (age, chronic conditions, CHF/COPD, Medicaid, deprivation), so adjusting for them recovers an odds ratio near 0.70.
- Good approaches: risk-adjust using pre-period claims, or run a difference-in-differences comparing Understory with the other hospitals before and after launch.
- The true per-stay readmission probability is in `answer_key.readmission_index_stays`.

## Diabetes complications
Monthly complication hazard rises with:
- higher A1c, which comes from lower medication adherence (measure with PDC from `pharmacy_claims`)
- area deprivation (smaller effect)
- **any coverage gap since January 2021** (a history of coverage instability)
- **no usual PCP**
- frailty
- zip risk

A second, less obvious pathway: **hypoglycemia events (ED or inpatient, E11.649) among members 75+ taking glipizide (a sulfonylurea)**, more so with CKD.

Diabetes Complex Case Management (MA and Medicaid managed care, from 2022) lowers the hazard (HR 0.80) and raises testing. Again, sicker members are the ones enrolled.

Outcomes are in `answer_key.diabetes_complications`.

**Analysis tip:** gap months also include months when a person had moved away or died. Have students limit the cohort to members observed through the outcome window, or the coverage-gap effect will look backwards.

## High-risk zip codes
- ED visits and admissions rise with area deprivation, fewer PCPs per capita, households without a vehicle and distance to a hospital.
- Five mid-sized zips (population 7,000+) have extra risk that none of the `zip_area` measures explains (`answer_key.zip_risk.unexplained_hotspot_flag`). Students can find them as large positive residuals after modeling expected use from area measures.

## Fraud, waste and abuse
Ground truth is in `answer_key.fraud_providers`.

| Scheme | Provider | Signature |
|---|---|---|
| EM_UPCODING | 2 internists | ~65% of established visits billed 99215 (peers 3–12%) |
| LAB_EXCESSIVE_TESTING | Prairie Diagnostics Laboratory | G0483 definitive drug panels and 87633 respiratory panels on routine labs; standing monthly orders |
| LAB_KICKBACK_REFERRER | 3 independent primary care practices | All their labs go to Prairie |
| DME_PHANTOM_BRACES | Keystone Bracing & Supply | L0650/L1833 braces for Medicare members with no related visits and random referring PCPs, 2023–24; ~30 claims dated **after the member's death** |
| PT_EXCESSIVE_UNITS | Riverbend Physical Therapy | ~11 timed units per visit, ~3 visits/week |
| IMPOSSIBLE_DAY_PSYCHOTHERAPY | One LCSW | 60-minute sessions crowded onto Tuesdays |
| PILL_MILL_PRESCRIBER / PHARMACY | Pain clinic + Wellborn Discount Drugs | Monthly oxycodone 30 mg ×120 (180 MME/day) for patients from distant zips |

## Other realism hooks
- **Medicaid:** continuous enrollment until March 2023, then elevated exits April 2023–June 2024. Most people who leave become uninsured; some move to Marketplace or employer coverage.
- **Telehealth:** about 26% of office visits in 2021, falling to about 7% by 2025.
- **COVID:** admissions concentrated in early 2021, Aug–Sep 2021 (Delta) and Jan 2022 (Omicron).
- **Medicare sequestration:** 0% through March 2022, 1% April–June 2022, 2% after.
- **GLP-1 uptake:** semaglutide use grows over time; tirzepatide appears from mid-2022. Both are high-cost and require PA.
- **Ledger:** commercial contracts at Understory pay above market. Self-pay accounts get a 60% discount, then charity care (high-deprivation zips) or collections and bad debt.
