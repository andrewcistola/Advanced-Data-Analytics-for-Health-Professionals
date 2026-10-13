# Data dictionary

Generated from the default build (25,000 members, seed 42). Row counts change with `--members`/`--seed`.

## `beneficiaries`

One row per person who appears in the region at any time 2021-2025 (the plan/APCD member file).

Rows: 25,000

| Column | Type | Description |
|---|---|---|
| `member_id` | VARCHAR | Unique member identifier (primary key) |
| `first_name` | VARCHAR | Synthetic first name |
| `last_name` | VARCHAR | Synthetic last name |
| `sex` | VARCHAR | Sex (F/M) |
| `birth_date` | DATE | Date of birth |
| `death_date` | DATE | Date of death (null if alive at end of study) |
| `race_ethnicity` | VARCHAR | Self-reported race/ethnicity (synthetic) |
| `preferred_language` | VARCHAR | Preferred language |
| `zip_code` | VARCHAR | 5-digit residence zip code (joins to zip_area) |
| `county` | VARCHAR | County of residence |

## `care_management`

Care management program enrollments.

Rows: 1,089

| Column | Type | Description |
|---|---|---|
| `cm_enrollment_id` | VARCHAR | Enrollment id |
| `member_id` | VARCHAR | Member |
| `program_name` | VARCHAR | Transitional Care Program or Diabetes Complex Case Management |
| `program_sponsor` | VARCHAR | Sponsoring organization |
| `enrollment_date` | DATE | Enrollment date |
| `end_date` | DATE | Program end date |
| `referral_source` | VARCHAR | How the member was identified |
| `index_claim_id` | VARCHAR | Index inpatient claim (Transitional Care Program) |

## `coverage_member_months`

Eligibility: one row per member per month of coverage. Months without a row are uninsured or outside the region.

Rows: 1,209,071

| Column | Type | Description |
|---|---|---|
| `member_id` | VARCHAR | Member identifier |
| `coverage_month` | DATE | First day of the coverage month |
| `coverage_year` | BIGINT | Calendar year |
| `payer_type` | VARCHAR | Commercial, Marketplace, Medicaid FFS, Medicaid Managed Care, Medicare FFS, Medicare Advantage |
| `payer_category` | VARCHAR | Private or Public |
| `line_of_business` | VARCHAR | Commercial, Individual (ACA Marketplace), Medicaid, Medicare |
| `plan_id` | VARCHAR | Plan identifier (joins to plans) |
| `plan_name` | VARCHAR | Plan name |
| `product_type` | VARCHAR | HMO, PPO, EPO, HDHP, FFS, HMO D-SNP |
| `funding_type` | VARCHAR | Fully Insured, Self-Funded (ASO), Capitated, Public |
| `metal_tier` | VARCHAR | Marketplace metal level |
| `relationship_to_subscriber` | VARCHAR | Self, Spouse, Child |
| `subscriber_id` | VARCHAR | Subscriber (policy holder) identifier |
| `medicare_entitlement_reason` | VARCHAR | Age or Disability (Medicare only) |
| `dual_status` | VARCHAR | Full Benefit Dual or Partial Dual (QMB/SLMB) |
| `secondary_payer` | VARCHAR | Secondary coverage (Medicaid for dual eligibles) |
| `rx_coverage_flag` | BIGINT | 1 if pharmacy benefit in force |
| `rx_plan_id` | VARCHAR | Pharmacy plan (Part D PDP for Medicare FFS members) |
| `assigned_pcp_npi` | VARCHAR | Plan-assigned PCP (HMO-type products only) |
| `premium_pmpm` | DOUBLE | Premium or capitation revenue per member per month (approximate) |
| `part_b_premium` | DOUBLE | Standard Part B premium (Medicare members) |

## `hospital_payments`

Patient-accounting transaction ledger for the Understory Health system (hospital + employed physicians). Sum of ar_effect by account_id = outstanding A/R balance as of 2026-03-31.

Rows: 1,181,419

| Column | Type | Description |
|---|---|---|
| `transaction_id` | VARCHAR | Unique transaction id |
| `account_id` | VARCHAR | Patient account (encounter) |
| `claim_id` | VARCHAR | Claim the transaction relates to |
| `member_id` | VARCHAR | Patient (member) identifier |
| `billing_npi` | VARCHAR | Billing NPI |
| `billing_provider_name` | VARCHAR | Facility or physician |
| `service_line` | VARCHAR | Inpatient, Outpatient, Emergency, Post-acute, Professional |
| `payer_type` | VARCHAR | Payer type (Self-pay if uninsured) |
| `plan_id` | VARCHAR | Plan |
| `service_date` | DATE | Service (or discharge) date |
| `transaction_date` | DATE | Posting date |
| `posting_period` | VARCHAR | YYYY-MM |
| `transaction_type` | VARCHAR | Charge, Insurance Payment, Contractual Adjustment, Sequestration Adjustment, Patient Responsibility, Denial, Line Denial, Appeal Filed, Corrected Claim Submitted, Rebilled to Other Payer, Denial Write-off, Secondary Insurance Payment, Patient Payment, Self-Pay Discount, Charity Care Adjustment, Bad Debt Write-off |
| `transaction_category` | VARCHAR | Charge, Payment, Adjustment, Denial, Write-off, Informational |
| `amount` | DOUBLE | Transaction amount as reported (always positive) |
| `ar_effect` | DOUBLE | Signed effect on A/R (+ increases balance, - reduces) |
| `group_code` | VARCHAR | CARC group code (CO, PR) |
| `carc_code` | VARCHAR | Claim adjustment reason code |
| `check_eft_number` | VARCHAR | Remittance EFT trace number |

## `medical_claim_lines`

Service lines for each medical claim.

Rows: 1,255,626

| Column | Type | Description |
|---|---|---|
| `claim_id` | VARCHAR | Claim identifier |
| `line_number` | BIGINT | Line sequence |
| `service_date` | DATE | Line date of service |
| `procedure_code` | VARCHAR | CPT/HCPCS code (null for revenue-code-only facility lines) |
| `procedure_code_type` | VARCHAR | CPT, CPT II, HCPCS |
| `modifier_1` | VARCHAR | Modifier (95 telehealth, 26 professional component, GP therapy, RR rental, NU new) |
| `modifier_2` | INTEGER | Second modifier |
| `revenue_code` | VARCHAR | UB-04 revenue code (institutional) |
| `units` | BIGINT | Units of service |
| `line_charge` | DOUBLE | Billed charge |
| `line_allowed` | DOUBLE | Allowed amount |
| `line_paid` | DOUBLE | Plan paid (allocated) |
| `line_patient_responsibility` | DOUBLE | Member cost share (allocated) |
| `line_status` | VARCHAR | Paid, Denied, Self-pay, Pending |
| `line_denial_reason_code` | VARCHAR | Line-level CARC (97 bundled, 96 non-covered, 119 benefit max) |

## `medical_claims`

Medical claim headers (837P professional and 837I institutional) with final adjudication. Corrected/rebilled claims are new rows linked by related_claim_id.

Rows: 650,869

| Column | Type | Description |
|---|---|---|
| `claim_id` | VARCHAR | Unique claim identifier |
| `related_claim_id` | VARCHAR | Prior claim this claim replaces or rebills |
| `claim_frequency_code` | VARCHAR | 1 = original, 7 = replacement/corrected |
| `resubmission_reason` | VARCHAR | Corrected claim, Appeal overturned, Rebilled to correct payer |
| `account_id` | VARCHAR | Provider patient-account (encounter) identifier; ties resubmissions and ledger rows together |
| `member_id` | VARCHAR | Member identifier |
| `claim_type` | VARCHAR | Professional or Institutional |
| `claim_setting` | VARCHAR | Office, Telehealth, Emergency, Inpatient, Outpatient Hospital, Laboratory, Home / DME, SNF |
| `bill_type` | VARCHAR | UB-04 type of bill (111 inpatient, 131 outpatient, 211 SNF) |
| `place_of_service` | VARCHAR | CMS place of service code |
| `service_from_date` | DATE | First date of service |
| `service_to_date` | DATE | Last date of service |
| `admission_date` | DATE | Inpatient/SNF admission date |
| `discharge_date` | DATE | Inpatient/SNF discharge date |
| `admission_type` | VARCHAR | Emergency, Urgent, Elective, Newborn |
| `discharge_status` | VARCHAR | 01 home, 03 SNF, 06 home health, 07 left AMA, 20 expired |
| `length_of_stay` | DOUBLE | Inpatient/SNF days |
| `drg_code` | VARCHAR | MS-DRG (inpatient) |
| `billing_npi` | VARCHAR | Billing provider NPI (synthetic) |
| `rendering_npi` | VARCHAR | Rendering provider NPI |
| `attending_npi` | VARCHAR | Attending provider NPI (institutional) |
| `referring_npi` | VARCHAR | Referring/ordering provider NPI |
| `facility_npi` | VARCHAR | Facility NPI |
| `payer_type` | VARCHAR | Payer billed (Self-pay if no coverage) |
| `plan_id` | VARCHAR | Plan billed |
| `dx_1` | VARCHAR | Principal diagnosis (ICD-10-CM) |
| `dx_2` | VARCHAR | Secondary diagnosis 2 |
| `dx_3` | VARCHAR | Secondary diagnosis 3 |
| `dx_4` | VARCHAR | Secondary diagnosis 4 |
| `dx_5` | VARCHAR | Secondary diagnosis 5 |
| `dx_6` | VARCHAR | Secondary diagnosis 6 |
| `dx_7` | VARCHAR | Secondary diagnosis 7 |
| `dx_8` | VARCHAR | Secondary diagnosis 8 |
| `dx_9` | VARCHAR | Secondary diagnosis 9 |
| `dx_10` | VARCHAR | Secondary diagnosis 10 |
| `prior_auth_id` | VARCHAR | Prior authorization on file (joins to prior_authorizations) |
| `total_charge` | DOUBLE | Billed charges |
| `total_allowed` | DOUBLE | Allowed amount |
| `total_paid` | DOUBLE | Plan paid amount |
| `deductible_amount` | DOUBLE | Member deductible |
| `coinsurance_amount` | DOUBLE | Member coinsurance |
| `copay_amount` | DOUBLE | Member copay |
| `patient_responsibility` | DOUBLE | Total member cost sharing |
| `sequestration_amount` | DOUBLE | Medicare sequestration reduction |
| `cob_secondary_paid` | DOUBLE | Amount paid by secondary payer (Medicaid crossover) |
| `claim_status` | VARCHAR | Paid, Partially Paid, Denied, Self-pay, Pending (not adjudicated by the as-of date) |
| `denial_reason_code` | VARCHAR | Claim-level CARC when denied (joins to ref_carc) |
| `submission_date` | DATE | Date claim was submitted |
| `adjudication_date` | DATE | Date payer adjudicated (remit date) |
| `appeal_outcome` | VARCHAR | Overturned or Upheld when the denial was appealed |

## `pharmacy_claims`

Pharmacy (NCPDP) claims, paid and rejected.

Rows: 828,727

| Column | Type | Description |
|---|---|---|
| `rx_claim_id` | VARCHAR | Unique pharmacy claim id |
| `member_id` | VARCHAR | Member identifier |
| `fill_date` | DATE | Date filled/submitted |
| `ndc` | VARCHAR | 11-digit NDC (synthetic; joins to ref_drug) |
| `drug_name` | VARCHAR | Drug name and strength |
| `generic_name` | VARCHAR | Generic ingredient |
| `brand_generic_flag` | VARCHAR | Brand or Generic |
| `therapeutic_class` | VARCHAR | Therapeutic class |
| `days_supply` | BIGINT | Days supply |
| `quantity` | DOUBLE | Quantity dispensed |
| `refill_number` | BIGINT | Refill number (0 = original fill) |
| `new_rx_flag` | BIGINT | 1 if a new therapy start |
| `prescriber_npi` | VARCHAR | Prescriber NPI |
| `pharmacy_npi` | VARCHAR | Dispensing pharmacy NPI |
| `mail_order_flag` | BIGINT | 1 if mail order |
| `payer_type` | VARCHAR | Payer type |
| `plan_id` | VARCHAR | Pharmacy plan |
| `formulary_tier` | BIGINT | Tier 1-3, 5 = specialty |
| `prior_auth_required_flag` | BIGINT | 1 if the drug requires PA under this plan |
| `prior_auth_id` | VARCHAR | PA approval used for this fill |
| `claim_status` | VARCHAR | Paid or Rejected |
| `reject_code` | VARCHAR | NCPDP reject code (65, 70, 75, 79) |
| `reject_description` | VARCHAR | Reject reason |
| `ingredient_cost` | DOUBLE | Ingredient cost |
| `dispensing_fee` | DOUBLE | Dispensing fee |
| `total_cost` | DOUBLE | Ingredient + fee |
| `member_copay` | DOUBLE | Member cost share |
| `plan_paid` | DOUBLE | Plan paid |

## `plans`

Plan benefit catalog.

Rows: 17

| Column | Type | Description |
|---|---|---|
| `plan_id` | VARCHAR |  |
| `plan_name` | VARCHAR |  |
| `payer_type` | VARCHAR |  |
| `product_type` | VARCHAR |  |
| `funding_type` | VARCHAR |  |
| `metal_tier` | VARCHAR |  |
| `deductible` | DOUBLE |  |
| `coinsurance` | DOUBLE |  |
| `copay_pcp` | DOUBLE |  |
| `copay_specialist` | DOUBLE |  |
| `copay_ed` | DOUBLE |  |
| `inpatient_copay` | DOUBLE |  |
| `oop_max` | DOUBLE |  |
| `requires_prior_auth` | BOOLEAN |  |
| `requires_pcp` | BOOLEAN |  |
| `timely_filing_days` | DOUBLE |  |

## `prior_authorizations`

Prior authorization requests (medical and pharmacy) with submission channel and turnaround.

Rows: 7,173

| Column | Type | Description |
|---|---|---|
| `prior_auth_id` | VARCHAR | PA identifier |
| `member_id` | VARCHAR | Member |
| `request_type` | VARCHAR | Medical or Pharmacy |
| `service_code` | VARCHAR | CPT/HCPCS or NDC requested |
| `service_description` | VARCHAR | Description |
| `requesting_npi` | VARCHAR | Requesting provider |
| `servicing_npi` | VARCHAR | Servicing provider/pharmacy |
| `payer_type` | VARCHAR | Payer type |
| `plan_id` | VARCHAR | Plan |
| `submission_channel` | VARCHAR | ePA, Payer Portal, Fax, Phone |
| `urgency` | VARCHAR | Standard or Expedited |
| `submitted_datetime` | TIMESTAMP | Submitted timestamp |
| `decision_datetime` | TIMESTAMP | Decision timestamp |
| `turnaround_hours` | DOUBLE | Hours to decision |
| `decision` | VARCHAR | Approved or Denied |
| `denial_reason` | VARCHAR | Reason when denied |
| `auto_adjudicated_flag` | BIGINT | 1 if approved in real time |

## `providers`

Provider directory (individuals and organizations). NPIs are synthetic and start with 9.

Rows: 241

| Column | Type | Description |
|---|---|---|
| `npi` | VARCHAR | Synthetic NPI (primary key) |
| `entity_type` | VARCHAR | Individual or Organization |
| `provider_name` | VARCHAR | Name |
| `credential` | VARCHAR | MD, DO, APRN, LCSW, OD, PT, DPM |
| `specialty` | VARCHAR | Specialty |
| `taxonomy_code` | VARCHAR | NUCC taxonomy code |
| `practice_id` | VARCHAR | Group/TIN identifier |
| `practice_name` | VARCHAR | Practice or facility name |
| `health_system` | VARCHAR | Health system affiliation |
| `zip_code` | VARCHAR | Practice zip code |
| `provider_role` | VARCHAR | PCP, Specialist, Hospital-based, Hospital, SNF, Lab, Imaging, DME, Pharmacy |
| `aco_name` | VARCHAR | ACO participation (null if none) |
| `fqhc_flag` | BIGINT | 1 if Federally Qualified Health Center |

## `ref_carc`

Claim adjustment reason codes with denial categories.

Rows: 19

| Column | Type | Description |
|---|---|---|
| `carc_code` | VARCHAR |  |
| `typical_group_code` | VARCHAR |  |
| `description` | VARCHAR |  |
| `denial_category` | VARCHAR |  |

## `ref_drg`

MS-DRGs with approximate relative weights (teaching values).

Rows: 35

| Column | Type | Description |
|---|---|---|
| `drg_code` | VARCHAR |  |
| `description` | VARCHAR |  |
| `approx_relative_weight` | DOUBLE |  |

## `ref_drug`

Drug reference keyed by synthetic NDC; mme_per_unit supports opioid MME calculations.

Rows: 45

| Column | Type | Description |
|---|---|---|
| `ndc` | VARCHAR |  |
| `drug_name` | VARCHAR |  |
| `generic_name` | VARCHAR |  |
| `therapeutic_class` | VARCHAR |  |
| `formulary_tier` | BIGINT |  |
| `prior_auth_required` | BOOLEAN |  |
| `brand_generic_flag` | VARCHAR |  |
| `specialty_drug_flag` | BOOLEAN |  |
| `mme_per_unit` | DOUBLE |  |

## `ref_hcc_crosswalk`

Illustrative ICD-10 to CMS-HCC (V28 labels) crosswalk. Coefficients are illustrative, not official.

Rows: 33

| Column | Type | Description |
|---|---|---|
| `icd10_code` | VARCHAR |  |
| `hcc` | BIGINT |  |
| `hcc_label` | VARCHAR |  |
| `illustrative_coefficient` | DOUBLE |  |

## `ref_icd10`

ICD-10-CM codes used in the data.

Rows: 85

| Column | Type | Description |
|---|---|---|
| `icd10_code` | VARCHAR |  |
| `description` | VARCHAR |  |

## `ref_ncpdp_reject`

NCPDP reject codes.

Rows: 5

| Column | Type | Description |
|---|---|---|
| `reject_code` | VARCHAR |  |
| `description` | VARCHAR |  |

## `ref_procedure`

CPT/HCPCS codes used in the data.

Rows: 94

| Column | Type | Description |
|---|---|---|
| `procedure_code` | VARCHAR |  |
| `description` | VARCHAR |  |
| `code_type` | VARCHAR |  |
| `category` | VARCHAR |  |
| `prior_auth_commonly_required` | BOOLEAN |  |

## `ref_revenue_code`

UB-04 revenue codes.

Rows: 24

| Column | Type | Description |
|---|---|---|
| `revenue_code` | VARCHAR |  |
| `description` | VARCHAR |  |

## `zip_area`

Zip-level area resources and social context (real North Central Florida zip codes and coordinates; all measures synthetic).

Rows: 105

| Column | Type | Description |
|---|---|---|
| `zip_code` | VARCHAR | Zip code |
| `city` | VARCHAR | City |
| `county` | VARCHAR | County |
| `state` | VARCHAR | State |
| `latitude` | DOUBLE | Latitude |
| `longitude` | DOUBLE | Longitude |
| `urbanicity` | VARCHAR | Urban, Suburban, Rural |
| `population` | BIGINT | Synthetic population |
| `area_deprivation_index` | BIGINT | ADI-style national percentile (1-100, synthetic) |
| `median_household_income` | BIGINT | Median household income |
| `pct_below_poverty` | DOUBLE | % below poverty |
| `pct_no_vehicle` | DOUBLE | % households without a vehicle |
| `pct_no_broadband` | DOUBLE | % households without broadband |
| `pct_age_65_plus` | DOUBLE | % population 65+ |
| `low_food_access_flag` | BIGINT | 1 if low food access |
| `pcp_per_10k` | DOUBLE | Primary care physicians per 10,000 |
| `pharmacies_per_10k` | DOUBLE | Pharmacies per 10,000 |
| `miles_to_nearest_hospital` | DOUBLE | Distance to nearest hospital (computed) |

## Instructor-only `answer_key` schema

These tables hold the generator's hidden truth so you can check student answers. They exist only in `health_analytics_instructor.duckdb` (and `parquet/answer_key/`), not in the student file `health_analytics.duckdb`.

- **diabetes_complications**: `member_id`, `event_date`, `complication_type`
- **fraud_providers**: `npi`, `provider_name`, `specialty`, `scheme`, `description`
- **member_truth**: `member_id`, `frailty`, `care_seeking`, `adherence_propensity`, `zip_risk_multiplier`, `home_pcp_npi`, `onset_obes`, `onset_htn`, `onset_hld`, `onset_diab`, `onset_cad`, `onset_chf`, `onset_afib`, `onset_copd`, `onset_asth`, `onset_ckd`, `onset_depr`, `onset_ra`, `onset_demen`, `onset_oud`, `onset_kneeoa`, `onset_brca`, `ckd_stage`, `diabetes_complex_cm_until`
- **parameters**: `parameter`, `value`
- **provider_traits**: `npi`, `provider_name`, `practice_id`, `specialty`, `quality`, `doc_rate`, `billing_quality`, `epa_adopt_month`
- **readmission_index_stays**: `member_id`, `index_claim_id`, `discharge_date`, `hospital_npi`, `tcp_enrolled`, `followup_7d`, `true_readmit_probability`, `true_baseline_logit`
- **zip_risk**: `zip_code`, `city`, `county`, `zip_risk_multiplier`, `unexplained_hotspot_flag`
