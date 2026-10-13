# Lab 11: Targeting High-Risk Zip Codes

**Business question:** A community-health partnership can fund mobile clinics in **five** zip codes. Where would they prevent the most avoidable ED visits and hospital admissions?

**Skills:** a small neural network in TensorFlow/Keras (dense layers, feature scaling, validation split, early stopping), comparison with logistic regression, and rolling member predictions up to areas (observed vs. expected).
**Domain:** area-level resources and spatial analytics: deprivation, primary care supply, transportation, distance to care.
**Tool:** JupyterLab (TensorFlow is in the course environment).
**Time:** about 75 minutes.

## Definitions

**Cohort:** members with 11+ months of coverage in 2024 and coverage in January 2025.

**Outcome (2025):** `avoidable_event` = 1 if the member had **either**
- an ED facility visit (`claim_setting = 'Emergency'`, `claim_type = 'Institutional'`), or
- an **ambulatory-care-sensitive (ACSC) admission**: an inpatient facility claim whose `dx_1` starts with any of `I50` (heart failure), `J44` (COPD), `J45` (asthma), `E11` (diabetes), `N39.0` (UTI), `J18` (pneumonia), `E86` (dehydration).

**Member features (2024):** age, sex, number of chronic condition groups (code prefixes in the starter code), ED visits, inpatient admissions, and payer (Medicaid, Medicare, Commercial/Marketplace).

**Zip features:** `area_deprivation_index`, `pcp_per_10k`, `pct_no_vehicle`, `miles_to_nearest_hospital`.

## Tasks

### 1. Build the modeling table
One row per cohort member with the outcome, member features, `zip_code` and zip features.

### 2. Neural network vs. logistic regression
Using **all** features (member + zip), split 75/25 (stratified, `random_state=42`) and standardize.
- Logistic regression: `LogisticRegression(max_iter=1000)`.
- Keras network: `Dense(32, relu)` → `Dense(16, relu)` → `Dense(1, sigmoid)`, `binary_crossentropy` loss, `validation_split=0.2`, `EarlyStopping(patience=5, restore_best_weights=True)`.

Compare test AUC. Is the network better?

### 3. Observed vs. expected by zip
Fit a logistic regression on **member features only** (no zip features). Its predictions are each member's *expected* risk given who they are. Sum by zip: members, observed events, expected events, the observed-to-expected (O/E) ratio and excess events (observed − expected). Keep zips with at least 100 members.

Pick **five target zips** using both excess events (volume) and O/E (intensity). Look at their zip features: what do they have in common? Is there one that the zip features *don't* explain?

### 4. AI step
Ask an AI tool why a neural network might not beat logistic regression on this kind of data. Check its reasons against your Task 2 result.

## Starter code

```python
import duckdb, numpy as np, pandas as pd
con = duckdb.connect("../data/health_analytics.duckdb", read_only=True)
CHRONIC_PREFIXES = ("I10", "I12", "E78", "E11", "I25", "I50", "I48", "J44", "J45", "N18", "F32", "F33", "F03", "F11")
ACSC_PREFIXES = ("I50", "J44", "J45", "E11", "N39.0", "J18", "E86")
```

## Deliverable

Your notebook plus a ranked list of five zip codes with one line of justification each (members, O/E, excess events, and what the zip features suggest).
