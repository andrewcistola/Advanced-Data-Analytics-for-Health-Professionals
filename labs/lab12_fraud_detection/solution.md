# Lab 12 Solution: Fraud Detection

## Task 1: Provider profiles

```python
import numpy as np
import pandas as pd

def miles(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(a))

base = con.sql("""
    WITH c AS (
        SELECT c.claim_id, c.billing_npi, c.member_id, c.total_charge, c.service_from_date
        FROM medical_claims c JOIN providers p ON p.npi = c.billing_npi
        WHERE c.related_claim_id IS NULL AND p.provider_role NOT IN ('Hospital', 'SNF')
    ),
    lines AS (
        SELECT c.billing_npi,
               SUM(l.units) AS units,
               SUM(CASE WHEN l.procedure_code = '99215' THEN 1 ELSE 0 END) AS n_99215,
               SUM(CASE WHEN l.procedure_code IN ('99212', '99213', '99214', '99215') THEN 1 ELSE 0 END) AS n_est
        FROM c JOIN medical_claim_lines l USING (claim_id)
        GROUP BY c.billing_npi
    )
    SELECT c.billing_npi AS npi,
           COUNT(*) AS claims,
           COUNT(DISTINCT c.member_id) AS patients,
           COUNT(*) * 1.0 / COUNT(DISTINCT c.member_id) AS claims_per_patient,
           ANY_VALUE(l.units) * 1.0 / COUNT(*) AS units_per_claim,
           AVG(c.total_charge) AS charge_per_claim,
           COALESCE(ANY_VALUE(l.n_99215) * 1.0 / NULLIF(ANY_VALUE(l.n_est), 0), 0) AS share_99215,
           AVG(CASE WHEN c.service_from_date > b.death_date THEN 1.0 ELSE 0 END) AS after_death_share
    FROM c
    JOIN beneficiaries b USING (member_id)
    JOIN lines l USING (billing_npi)
    GROUP BY c.billing_npi
    HAVING COUNT(*) >= 50
""").df()

# share of patients living 50+ miles away
pts = con.sql("""
    SELECT DISTINCT c.billing_npi AS npi, c.member_id,
           zm.latitude AS m_lat, zm.longitude AS m_lon, zp.latitude AS p_lat, zp.longitude AS p_lon
    FROM medical_claims c
    JOIN beneficiaries b USING (member_id)
    JOIN zip_area zm ON zm.zip_code = b.zip_code
    JOIN providers p ON p.npi = c.billing_npi
    JOIN zip_area zp ON zp.zip_code = p.zip_code
    WHERE c.related_claim_id IS NULL
""").df()
pts["far"] = miles(pts.m_lat, pts.m_lon, pts.p_lat, pts.p_lon) >= 50
far = pts.groupby("npi").far.mean().rename("share_far_patients")

prov = con.sql("SELECT npi, provider_name, specialty, provider_role FROM providers").df()
profiles = base.merge(far, on="npi").merge(prov, on="npi")
FEATURES = ["claims_per_patient", "units_per_claim", "charge_per_claim", "share_99215",
            "share_far_patients", "after_death_share"]
print(len(profiles), "providers profiled")
profiles[FEATURES].describe().round(3)
```

## Task 2: Cluster

```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

X = profiles[FEATURES].copy()
for col in ["claims_per_patient", "units_per_claim", "charge_per_claim"]:
    X[col] = np.log1p(X[col])
Xs = StandardScaler().fit_transform(X)

scores = []
for k in range(2, 11):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(Xs)
    scores.append((k, km.inertia_, silhouette_score(Xs, km.labels_)))
print(pd.DataFrame(scores, columns=["k", "inertia", "silhouette"]).round(3).to_string(index=False))
```

Pick k where the inertia curve bends and silhouette is reasonably high. Around 4–7 is typical; this solution uses k = 6.

**A k-means trap:** extreme providers often form their own tiny cluster, so their distance to *their own* center is near zero. Score each provider by distance to the nearest **large** cluster center instead. Then a provider in a cluster of 1–3 still scores high.

```python
K = 6
km = KMeans(n_clusters=K, n_init=10, random_state=42).fit(Xs)
profiles["cluster"] = km.labels_
sizes = profiles.cluster.value_counts()
print(profiles.groupby("cluster").agg(n=("npi", "count"), **{f: (f, "mean") for f in FEATURES}).round(2).to_string())

# Outlier score: distance to the nearest *large* cluster center (5%+ of providers).
# A provider in a tiny cluster of its own is far from every large center, so it scores high too.
large = [c for c, n in sizes.items() if n >= 0.05 * len(profiles)]
dists = np.linalg.norm(Xs[:, None, :] - km.cluster_centers_[large][None, :, :], axis=2)
profiles["outlier_score"] = dists.min(axis=1)
profiles["small_cluster"] = ~profiles.cluster.isin(large)
```

## Task 3: Top 10 outliers

```python
top10 = profiles.sort_values("outlier_score", ascending=False).head(10)
print(top10[["provider_name", "specialty", "cluster", "small_cluster", "outlier_score"] + FEATURES].round(2).to_string(index=False))
```

Instructor check against the ground truth (not available to students):

```python
truth = con.sql("SELECT npi, scheme FROM answer_key.fraud_providers").df()
check = profiles.sort_values("outlier_score", ascending=False).merge(truth, on="npi", how="left")
check["rank"] = range(1, len(check) + 1)
print(check.loc[check.scheme.notna(), ["rank", "provider_name", "scheme"]].to_string(index=False))
```

## Expected results

Exact numbers are in `expected_results.md`. Eight of the top 10 are planted schemes, and the other two are honest outliers (OB/GYNs, whose global delivery fee makes every claim expensive). The lab ranks around 14th. The pattern:

| Pattern | Suspected scheme | Provider (answer key) |
|---|---|---|
| ~11 units per claim, 30+ claims per patient | excessive units / medically unnecessary PT | Riverbend Physical Therapy clinicians |
| Very high claims per patient, 60-minute psychotherapy | impossible day / phantom sessions | one LCSW |
| High charge per claim, drug and respiratory panels, high claims per patient | excessive testing (and kickbacks) | Prairie Diagnostics Laboratory |
| Patients far away, some services after death, one claim per patient | phantom DME billing | Keystone Bracing & Supply |
| Patients far away, monthly visits, 99214/99215 | pill mill | Suwannee Valley Pain & Wellness prescriber |
| `share_99215` around 0.6 (peers under 0.15) | E&M upcoding | two internists |

Honest outliers also show up: high-cost specialties such as oncology or orthopaedic surgery (high charge per claim), or DME suppliers with monthly rentals (high claims per patient). That's the point of Task 3: distance flags *unusual*, and an analyst decides whether unusual is suspicious. The kickback-referrer PCPs usually don't stand out on their own billing; they show up only when you profile the lab's referral sources.

## Task 4: AI-suggested features (examples)

Max hours of timed services in one day; share of services billed on weekends; number of distinct referring providers per patient; opioid MME per patient (from `pharmacy_claims`); share of claims with modifier 25 or 59. Adding **max daily hours** sends the LCSW straight to the top. Adding **opioid MME** separates the pain clinic from other far-patient providers.
