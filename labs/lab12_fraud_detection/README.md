# Lab 12: Fraud Detection

**Business question:** The plan's special investigations unit (SIU) can audit about **ten** providers this year. Which billing patterns look most unusual compared with peers?

**Skills:** unsupervised learning: building provider profiles, scaling, k-means, choosing k (elbow and silhouette), and using distance to the cluster center as an outlier score.
**Domain:** fraud, waste and abuse: upcoding, unbundling and excessive units, phantom billing, impossible days, pill mills, kickbacks.
**Tool:** JupyterLab.
**Time:** about 75 minutes.

## Data

`medical_claims`, `medical_claim_lines`, `providers`, `beneficiaries`, `zip_area`.

Profile **billing providers** (`billing_npi`) with at least 50 original claims (`related_claim_id IS NULL`). Leave out hospitals and skilled nursing facilities (`provider_role` in 'Hospital', 'SNF'), whose claims follow different rules.

## Tasks

### 1. Build provider profiles
One row per billing provider with:

| Feature | Definition |
|---|---|
| `claims_per_patient` | claims ÷ distinct members |
| `units_per_claim` | total line units ÷ claims |
| `charge_per_claim` | total charges ÷ claims |
| `share_99215` | 99215 lines ÷ all 99212–99215 lines (0 if none) |
| `share_far_patients` | share of distinct patients who live 50+ miles from the provider's zip (use `zip_area` latitude/longitude; a starter distance function is below) |
| `after_death_share` | share of claims with a service date after the member's `death_date` |

### 2. Cluster
Log-transform the skewed features (`np.log1p`), standardize, and run k-means for k = 2 to 10 (`n_init=10, random_state=42`). Plot inertia (elbow) and silhouette score. Pick k and fit.

### 3. Rank and profile
Look at cluster sizes first. Extreme providers often form a **tiny cluster of their own**, so their distance to *their own* center is near zero. Score every provider by its distance to the nearest **large** cluster center (clusters with at least 5% of providers).

List the top 10 by that score with their specialty and raw features. For each one, name the scheme the pattern suggests, or say it looks like an honest outlier.

### 4. AI step
Ask an AI tool to propose one more feature for detecting provider fraud in claims data. Add it, re-run Tasks 2–3, and note whether your top 10 changes.

## Starter code

```python
import duckdb, numpy as np, pandas as pd
con = duckdb.connect("../data/health_analytics.duckdb", read_only=True)

def miles(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(a))
```

## Deliverable

Your notebook plus an SIU referral list: 10 providers, one line each with the pattern and the suspected scheme.
