"""Geography (zip-level area table) and the provider directory."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

from .reference import TAXONOMY

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "reference"

URBAN_CITIES = {"Gainesville", "Ocala"}
SUBURBAN_CITIES = {"Lake City", "Palatka", "Orange Park", "Fleming Island", "Middleburg", "Green Cove Springs",
                   "Alachua", "Newberry", "Belleview", "Inverness", "Crystal River", "Starke", "Keystone Heights",
                   "Live Oak", "Summerfield"}

SYSTEM = "Sabal Ridge Health"  # the fictional hospital system whose payment ledger is generated

HOSPITALS = [
    # name, zip, system, chargemaster markup, commercial contract factor, beds
    ("Sabal Ridge Medical Center", "32608", SYSTEM, 3.4, 1.15, 420),
    ("Sabal Ridge Community Hospital", "32055", SYSTEM, 3.1, 1.05, 90),
    ("Coquina Regional Hospital", "34471", "Coquina Health Partners", 3.6, 1.10, 310),
    ("Heronwood Memorial Hospital", "32177", "Independent", 2.9, 0.95, 70),
]


def haversine(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dl = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def build_zip_area(rng: np.random.Generator) -> pd.DataFrame:
    z = pd.read_csv(DATA_DIR / "ncfl_zip_codes.csv", dtype={"zip_code": str})
    n = len(z)
    urb = np.where(z.city.isin(URBAN_CITIES), "Urban", np.where(z.city.isin(SUBURBAN_CITIES), "Suburban", "Rural"))
    z["urbanicity"] = urb
    pop = np.where(urb == "Urban", rng.integers(18000, 46000, n),
                   np.where(urb == "Suburban", rng.integers(9000, 28000, n), rng.integers(1500, 9500, n)))
    z["population"] = pop
    adi_mu = np.where(urb == "Urban", 48, np.where(urb == "Suburban", 62, 76))
    z["area_deprivation_index"] = np.clip(np.round(rng.normal(adi_mu, 16)), 3, 100).astype(int)
    adi = z.area_deprivation_index.values
    z["median_household_income"] = np.round(np.clip(rng.normal(92000 - 560 * adi, 7000), 26000, 140000), -2).astype(int)
    z["pct_below_poverty"] = np.round(np.clip(rng.normal(3 + 0.24 * adi, 2.5), 2, 45), 1)
    z["pct_no_vehicle"] = np.round(np.clip(rng.normal(1 + 0.09 * adi + (urb == "Urban") * 2, 1.5), 0.5, 20), 1)
    z["pct_no_broadband"] = np.round(np.clip(rng.normal(6 + 0.18 * adi + (urb == "Rural") * 8, 3), 2, 50), 1)
    z["pct_age_65_plus"] = np.round(np.clip(rng.normal(np.where(urb == "Urban", 15, 24), 5), 8, 55), 1)
    z["low_food_access_flag"] = (rng.random(n) < (0.10 + 0.005 * adi)).astype(int)
    z["pcp_per_10k"] = np.round(np.clip(rng.normal(np.where(urb == "Urban", 9.5, np.where(urb == "Suburban", 5.5, 2.2)), 1.3), 0.0, 16), 1)
    z["pharmacies_per_10k"] = np.round(np.clip(rng.normal(np.where(urb == "Rural", 1.4, 2.6), 0.6), 0.0, 6), 1)
    # distance to nearest hospital
    hz = z.set_index("zip_code").loc[[h[1] for h in HOSPITALS], ["latitude", "longitude"]].values
    d = np.stack([haversine(z.latitude.values, z.longitude.values, la, lo) for la, lo in hz], axis=1)
    z["miles_to_nearest_hospital"] = np.round(d.min(axis=1), 1)

    # Hidden zip-level risk (answer key): structured part + a few unexplained "hotspots"
    zs = lambda x: (x - x.mean()) / x.std()
    structured = 0.17 * zs(adi.astype(float)) - 0.12 * zs(z.pcp_per_10k.values) + 0.10 * zs(z.pct_no_vehicle.values) \
        + 0.06 * zs(z.miles_to_nearest_hospital.values)
    hotspot = np.zeros(n, bool)
    # hotspots: rural/suburban zips with only moderate ADI so they are not trivially found
    cand = np.where((urb != "Urban") & (adi > 40) & (adi < 80))[0]
    hotspot[rng.choice(cand, size=min(5, len(cand)), replace=False)] = True
    z["_zip_risk"] = np.exp(structured + np.where(hotspot, 0.90, 0.0) + rng.normal(0, 0.06, n))
    z["_hotspot"] = hotspot
    return z


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
class NPIFactory:
    def __init__(self, rng):
        self.rng = rng
        self.used = set()

    def __call__(self):
        while True:
            npi = "9" + "".join(map(str, self.rng.integers(0, 10, 9)))
            if npi not in self.used:
                self.used.add(npi)
                return npi


def build_providers(rng: np.random.Generator, fake, zips: pd.DataFrame) -> pd.DataFrame:
    npi = NPIFactory(rng)
    rows = []
    zw = zips.population.values / zips.population.sum()

    def pick_zip(urban_bias=1.0, high_adi=False):
        w = zw * np.where(zips.urbanicity.values == "Urban", urban_bias, 1.0)
        if high_adi:
            w = w * (zips.area_deprivation_index.values / 50.0) ** 3
        w = w / w.sum()
        return zips.zip_code.values[rng.choice(len(zips), p=w)]

    def person_name(cred):
        sex = rng.choice(["F", "M"])
        first = fake.first_name_female() if sex == "F" else fake.first_name_male()
        return f"{fake.last_name()}, {first} {cred}"

    def add(**kw):
        base = dict(npi=npi(), entity_type="Individual", provider_name=None, credential=None, specialty=None,
                    taxonomy_code=None, practice_id=None, practice_name=None, health_system="Independent",
                    zip_code=None, provider_role=None, aco_name=None, fqhc_flag=0, hospital_markup=None,
                    _quality=0.0, _doc_rate=0.8, _billing_quality=0.0, _epa_adopt_month=None, _fraud_scheme=None,
                    _contract_factor=1.0, _bed_count=None)
        base.update(kw)
        base["taxonomy_code"] = TAXONOMY.get(base["specialty"])
        rows.append(base)
        return base

    # Facilities ---------------------------------------------------------
    for name, z, system, markup, cf, beds in HOSPITALS:
        add(entity_type="Organization", provider_name=name, specialty="General Acute Care Hospital",
            practice_id="TIN-" + name.split()[0].upper()[:4] + z[-2:], practice_name=name, health_system=system,
            zip_code=z, provider_role="Hospital", hospital_markup=markup, _contract_factor=cf, _bed_count=beds,
            _billing_quality=rng.normal(0.3 if system == SYSTEM else 0, 0.2), _epa_adopt_month=18 if system == SYSTEM else 34)
    for name in ["Oak Hammock Rehabilitation & Nursing", "Santa Fe River Nursing Center", "Marion Oaks Skilled Nursing"]:
        add(entity_type="Organization", provider_name=name, specialty="Skilled Nursing Facility",
            practice_id="TIN-SNF" + str(len(rows)), practice_name=name, zip_code=pick_zip(), provider_role="SNF")
    for name, fraud in [("Gulf Atlantic Reference Laboratory", None), ("Prairie Diagnostics Laboratory", "LAB_EXCESSIVE_TESTING")]:
        add(entity_type="Organization", provider_name=name, specialty="Clinical Medical Laboratory",
            practice_id="TIN-LAB" + str(len(rows)), practice_name=name, zip_code=pick_zip(2), provider_role="Lab",
            _fraud_scheme=fraud)
    for name in ["Springs Imaging Center", "Gateway Diagnostic Imaging"]:
        add(entity_type="Organization", provider_name=name, specialty="Radiology Imaging Center",
            practice_id="TIN-IMG" + str(len(rows)), practice_name=name, zip_code=pick_zip(2), provider_role="Imaging",
            _epa_adopt_month=int(rng.integers(6, 40)))
    for name, fraud in [("Suncoast Medical Supply", None), ("Prairie Home Medical Equipment", None),
                        ("Keystone Bracing & Supply", "DME_PHANTOM_BRACES")]:
        add(entity_type="Organization", provider_name=name, specialty="Durable Medical Equipment",
            practice_id="TIN-DME" + str(len(rows)), practice_name=name, zip_code=pick_zip(), provider_role="DME",
            _fraud_scheme=fraud, _epa_adopt_month=int(rng.integers(10, 50)))

    # Pharmacies
    for i in range(14):
        chain = i < 9
        nm = f"Gulf Coast Pharmacy #{1100 + i * 7}" if chain else f"{fake.last_name()} Family Pharmacy"
        add(entity_type="Organization", provider_name=nm, specialty="Community/Retail Pharmacy",
            practice_id="TIN-GCP" if chain else "TIN-RX" + str(len(rows)), practice_name=nm, zip_code=pick_zip(),
            provider_role="Pharmacy")
    add(entity_type="Organization", provider_name="Kestrel Mail Pharmacy Services", specialty="Mail Order Pharmacy",
        practice_id="TIN-KMAIL", practice_name="Kestrel Mail Pharmacy Services", zip_code="32608", provider_role="Pharmacy")
    add(entity_type="Organization", provider_name="Sabal Ridge Specialty Pharmacy", specialty="Specialty Pharmacy",
        practice_id="TIN-SRSP", practice_name="Sabal Ridge Specialty Pharmacy", health_system=SYSTEM, zip_code="32608",
        provider_role="Pharmacy")
    add(entity_type="Organization", provider_name="Wellborn Discount Drugs", specialty="Community/Retail Pharmacy",
        practice_id="TIN-WDD", practice_name="Wellborn Discount Drugs", zip_code=pick_zip(0.2),
        provider_role="Pharmacy", _fraud_scheme="PILL_MILL_PHARMACY")

    # Primary care practices ---------------------------------------------
    n_prac = 34
    for p in range(n_prac):
        peds = p < 5
        fqhc = 5 <= p < 8
        system = SYSTEM if (not fqhc and rng.random() < 0.40) else "Independent"
        aco = "North Florida Community ACO" if rng.random() < 0.5 else None
        z = pick_zip(1.5, high_adi=fqhc)
        city = zips.set_index("zip_code").city[z]
        if fqhc:
            pname = f"{city} Community Health Center"
        elif peds:
            pname = f"{city} Pediatrics" + ("" if p % 2 else " & Adolescent Medicine")
        elif system == SYSTEM:
            pname = f"Sabal Ridge Primary Care - {city}" + (f" {p}" if p % 3 == 0 else "")
        else:
            pname = f"{fake.last_name()} {rng.choice(['Family Medicine', 'Internal Medicine', 'Primary Care', 'Family Practice'])}"
        tin = f"TIN-PC{p:03d}"
        quality = rng.normal(0, 0.5) + (0.25 if aco else 0) + (0.15 if system == SYSTEM else 0)
        doc_rate = float(np.clip(rng.normal(0.80 + (0.07 if aco else 0), 0.07), 0.55, 0.97))
        billing = rng.normal(0, 0.35)
        epa = int(rng.integers(3, 58)) if rng.random() < 0.80 else None  # month of ePA adoption (None = never)
        if system == SYSTEM:
            epa = 18 if epa is None else min(epa, 30)
        n_clin = int(rng.integers(1, 7))
        for c in range(n_clin):
            if peds:
                spec, cred = "Pediatrics", "MD"
            elif c > 0 and rng.random() < 0.3:
                spec, cred = "Nurse Practitioner", "APRN"
            else:
                spec = rng.choice(["Family Medicine", "Internal Medicine"], p=[0.6, 0.4])
                cred = rng.choice(["MD", "DO"], p=[0.75, 0.25])
            add(provider_name=person_name(cred), credential=cred, specialty=spec, practice_id=tin, practice_name=pname,
                health_system=system, zip_code=z, provider_role="PCP", aco_name=aco, fqhc_flag=int(fqhc),
                _quality=quality + rng.normal(0, 0.15), _doc_rate=doc_rate, _billing_quality=billing,
                _epa_adopt_month=epa)
    # two upcoding PCPs (independent solo practices)
    for k in range(2):
        z = pick_zip(1.0)
        pname = f"{fake.last_name()} Medical Associates"
        add(provider_name=person_name("MD"), credential="MD", specialty="Internal Medicine", practice_id=f"TIN-PCF{k}",
            practice_name=pname, zip_code=z, provider_role="PCP", _quality=-0.3, _doc_rate=0.95,
            _billing_quality=-0.2, _epa_adopt_month=None, _fraud_scheme="EM_UPCODING")

    # Specialist groups --------------------------------------------------
    groups = [
        ("Cardiology", 2, 3, "Heart & Vascular"), ("Endocrinology", 1, 2, "Endocrine & Diabetes"),
        ("Pulmonology", 1, 2, "Lung & Sleep"), ("Nephrology", 1, 2, "Kidney Associates"),
        ("Psychiatry", 1, 2, "Behavioral Health"), ("Clinical Social Worker", 2, 3, "Counseling Center"),
        ("Orthopaedic Surgery", 2, 3, "Orthopaedics & Sports Medicine"), ("Ophthalmology", 1, 2, "Eye Institute"),
        ("Optometry", 3, 1, "Vision Care"), ("Gastroenterology", 2, 2, "Digestive Health"),
        ("Obstetrics & Gynecology", 2, 2, "Women's Health"), ("Rheumatology", 1, 2, "Arthritis & Rheumatology"),
        ("Hematology & Oncology", 1, 2, "Cancer Center"), ("Podiatry", 2, 1, "Foot & Ankle"),
        ("Diagnostic Radiology", 1, 4, "Radiology Associates"), ("Physical Therapy", 3, 3, "Physical Therapy"),
    ]
    gi = 0
    for spec, ngroups, nclin, label in groups:
        for g in range(ngroups):
            gi += 1
            system = SYSTEM if rng.random() < 0.45 else "Independent"
            z = pick_zip(2.5)
            city = zips.set_index("zip_code").city[z]
            pname = f"Sabal Ridge {label}" if system == SYSTEM else f"{city} {label}"
            fraud = None
            if spec == "Physical Therapy" and g == 2:
                pname, system, fraud = "Riverbend Physical Therapy", "Independent", "PT_EXCESSIVE_UNITS"
            cred = {"Clinical Social Worker": "LCSW", "Optometry": "OD", "Physical Therapy": "PT", "Podiatry": "DPM"}.get(spec, "MD")
            epa = int(rng.integers(3, 58)) if rng.random() < 0.75 else None
            for c in range(nclin):
                f = fraud
                if spec == "Clinical Social Worker" and g == 1 and c == 0:
                    f = "IMPOSSIBLE_DAY_PSYCHOTHERAPY"
                add(provider_name=person_name(cred), credential=cred, specialty=spec, practice_id=f"TIN-SP{gi:03d}",
                    practice_name=pname, health_system=system, zip_code=z, provider_role="Specialist",
                    _quality=rng.normal(0, 0.3), _doc_rate=float(np.clip(rng.normal(0.9, 0.05), 0.7, 1)),
                    _billing_quality=rng.normal(0, 0.3), _epa_adopt_month=epa, _fraud_scheme=f)
    # pain clinic (pill mill prescriber)
    add(provider_name=person_name("MD"), credential="MD", specialty="Pain Medicine", practice_id="TIN-PAIN1",
        practice_name="Suwannee Valley Pain & Wellness", zip_code=pick_zip(0.2), provider_role="Specialist",
        _fraud_scheme="PILL_MILL_PRESCRIBER")
    # Hospital-based groups: ED physicians and hospitalists per hospital
    for name, z, system, *_ in HOSPITALS:
        short = name.replace(" Hospital", "").replace(" Medical Center", "")
        for spec, label, n in [("Emergency Medicine", "Emergency Physicians", 4), ("Hospitalist", "Hospitalist Group", 4)]:
            for c in range(n):
                add(provider_name=person_name("MD"), credential="MD", specialty=spec, practice_id=f"TIN-{spec[:3].upper()}{z}",
                    practice_name=f"{short} {label}", health_system=system, zip_code=z, provider_role="Hospital-based",
                    _billing_quality=rng.normal(0, 0.2))

    df = pd.DataFrame(rows)
    return df
