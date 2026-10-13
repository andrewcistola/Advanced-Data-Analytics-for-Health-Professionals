"""Reference code sets and plan/provider catalogs used by the generator.

Code values (ICD-10-CM, CPT/HCPCS, MS-DRG, revenue codes, CARC, NCPDP reject codes)
are real code formats and descriptions chosen for teaching. Dollar amounts, DRG
weights and HCC coefficients are *approximations for teaching only* and should not
be used as official payment values. NDCs and NPIs are synthetic (they begin with 9
so they cannot collide with real identifiers).
"""

# ---------------------------------------------------------------------------
# Study window
# ---------------------------------------------------------------------------
START_YEAR = 2021
N_YEARS = 5
N_MONTHS = 12 * N_YEARS
AS_OF_DATE = "2026-03-31"  # claims run-out / ledger snapshot date

AGE_BANDS = [(0, 17), (18, 34), (35, 49), (50, 64), (65, 74), (75, 120)]

# ---------------------------------------------------------------------------
# Chronic conditions: prevalence by age band (0-17,18-34,35-49,50-64,65-74,75+)
# ---------------------------------------------------------------------------
CONDITIONS = {
    "HTN":   dict(name="Hypertension",                   prev=[0.01, 0.06, 0.20, 0.40, 0.60, 0.72]),
    "HLD":   dict(name="Hyperlipidemia",                 prev=[0.005, 0.05, 0.18, 0.35, 0.50, 0.52]),
    "OBES":  dict(name="Obesity",                        prev=[0.15, 0.30, 0.38, 0.40, 0.36, 0.25]),
    "DIAB":  dict(name="Type 2 diabetes",                prev=[0.003, 0.02, 0.08, 0.17, 0.25, 0.27]),
    "CAD":   dict(name="Coronary artery disease",        prev=[0.0, 0.003, 0.02, 0.07, 0.14, 0.22]),
    "CHF":   dict(name="Heart failure",                  prev=[0.0, 0.002, 0.006, 0.02, 0.06, 0.13]),
    "AFIB":  dict(name="Atrial fibrillation",            prev=[0.0, 0.001, 0.005, 0.02, 0.06, 0.12]),
    "COPD":  dict(name="COPD",                           prev=[0.0, 0.005, 0.02, 0.06, 0.11, 0.13]),
    "ASTH":  dict(name="Asthma",                         prev=[0.09, 0.08, 0.08, 0.08, 0.07, 0.06]),
    "CKD":   dict(name="Chronic kidney disease",         prev=[0.002, 0.01, 0.03, 0.07, 0.15, 0.25]),
    "DEPR":  dict(name="Depression",                     prev=[0.04, 0.11, 0.11, 0.10, 0.09, 0.09]),
    "RA":    dict(name="Rheumatoid arthritis",           prev=[0.0, 0.004, 0.008, 0.012, 0.015, 0.015]),
    "DEMEN": dict(name="Dementia",                       prev=[0.0, 0.0, 0.0, 0.005, 0.03, 0.12]),
    "OUD":   dict(name="Opioid use disorder",            prev=[0.001, 0.012, 0.012, 0.008, 0.004, 0.002]),
    "KNEEOA": dict(name="Knee osteoarthritis",           prev=[0.0, 0.01, 0.05, 0.12, 0.20, 0.25]),
    "BRCA":  dict(name="Breast cancer (female)",         prev=[0.0, 0.001, 0.004, 0.01, 0.018, 0.02]),
}
CHRONIC_FOR_COUNT = ["HTN", "HLD", "DIAB", "CAD", "CHF", "AFIB", "COPD", "ASTH", "CKD", "DEPR", "RA", "DEMEN", "OUD"]
SERIOUS = ["CHF", "COPD", "CKD", "DEMEN", "BRCA"]

# Diagnosis code(s) used to document each chronic condition on claims
CONDITION_DX = {
    "HTN": ["I10"], "HLD": ["E78.5", "E78.00"], "OBES": ["E66.9"], "DIAB": ["E11.9", "E11.65"],
    "CAD": ["I25.10"], "CHF": ["I50.9", "I50.22", "I50.32"], "AFIB": ["I48.91", "I48.0"],
    "COPD": ["J44.9"], "ASTH": ["J45.909"], "DEPR": ["F32.9", "F32.1", "F33.1"], "RA": ["M06.9"],
    "DEMEN": ["F03.90"], "OUD": ["F11.20"], "KNEEOA": ["M17.11", "M17.12", "M17.0"], "BRCA": ["C50.911"],
}
CKD_STAGE_DX = {"3a": "N18.31", "3b": "N18.32", "4": "N18.4", "5": "N18.5"}

ICD10 = {
    # chronic
    "I10": "Essential (primary) hypertension",
    "I12.9": "Hypertensive chronic kidney disease with stage 1-4 CKD or unspecified CKD",
    "E78.5": "Hyperlipidemia, unspecified", "E78.00": "Pure hypercholesterolemia, unspecified",
    "E66.9": "Obesity, unspecified", "E66.01": "Morbid (severe) obesity due to excess calories",
    "Z68.41": "Body mass index [BMI] 40.0-44.9, adult",
    "E11.9": "Type 2 diabetes mellitus without complications",
    "E11.65": "Type 2 diabetes mellitus with hyperglycemia",
    "E11.22": "Type 2 diabetes mellitus with diabetic chronic kidney disease",
    "E11.42": "Type 2 diabetes mellitus with diabetic polyneuropathy",
    "E11.319": "Type 2 diabetes mellitus with unspecified diabetic retinopathy without macular edema",
    "E11.51": "Type 2 diabetes mellitus with diabetic peripheral angiopathy without gangrene",
    "E11.621": "Type 2 diabetes mellitus with foot ulcer",
    "E11.649": "Type 2 diabetes mellitus with hypoglycemia without coma",
    "E11.10": "Type 2 diabetes mellitus with ketoacidosis without coma",
    "E11.00": "Type 2 diabetes mellitus with hyperosmolarity without NKHHC",
    "L97.509": "Non-pressure chronic ulcer of other part of unspecified foot with unspecified severity",
    "Z89.411": "Acquired absence of right great toe",
    "Z79.4": "Long term (current) use of insulin", "Z79.84": "Long term (current) use of oral hypoglycemic drugs",
    "I25.10": "Atherosclerotic heart disease of native coronary artery without angina pectoris",
    "I50.9": "Heart failure, unspecified", "I50.22": "Chronic systolic (congestive) heart failure",
    "I50.32": "Chronic diastolic (congestive) heart failure", "I50.23": "Acute on chronic systolic (congestive) heart failure",
    "I48.91": "Unspecified atrial fibrillation", "I48.0": "Paroxysmal atrial fibrillation",
    "J44.9": "Chronic obstructive pulmonary disease, unspecified",
    "J44.1": "Chronic obstructive pulmonary disease with (acute) exacerbation",
    "J45.909": "Unspecified asthma, uncomplicated", "J45.901": "Unspecified asthma with (acute) exacerbation",
    "N18.31": "Chronic kidney disease, stage 3a", "N18.32": "Chronic kidney disease, stage 3b",
    "N18.4": "Chronic kidney disease, stage 4 (severe)", "N18.5": "Chronic kidney disease, stage 5",
    "F32.9": "Major depressive disorder, single episode, unspecified",
    "F32.1": "Major depressive disorder, single episode, moderate",
    "F33.1": "Major depressive disorder, recurrent, moderate",
    "M06.9": "Rheumatoid arthritis, unspecified", "F03.90": "Unspecified dementia without behavioral disturbance",
    "F11.20": "Opioid dependence, uncomplicated", "T40.2X1A": "Poisoning by other opioids, accidental, initial encounter",
    "M17.11": "Unilateral primary osteoarthritis, right knee", "M17.12": "Unilateral primary osteoarthritis, left knee",
    "M17.0": "Bilateral primary osteoarthritis of knee", "C50.911": "Malignant neoplasm of unspecified site of right female breast",
    # acute / symptoms
    "J06.9": "Acute upper respiratory infection, unspecified", "J02.9": "Acute pharyngitis, unspecified",
    "H66.90": "Otitis media, unspecified, unspecified ear", "N39.0": "Urinary tract infection, site not specified",
    "J18.9": "Pneumonia, unspecified organism", "A41.9": "Sepsis, unspecified organism",
    "U07.1": "COVID-19", "M54.9": "Dorsalgia, unspecified", "R07.9": "Chest pain, unspecified",
    "R10.9": "Unspecified abdominal pain", "K52.9": "Noninfective gastroenteritis and colitis, unspecified",
    "S93.401A": "Sprain of unspecified ligament of right ankle, initial encounter",
    "S01.81XA": "Laceration without foreign body of other part of head, initial encounter",
    "R55": "Syncope and collapse", "E86.0": "Dehydration", "E16.2": "Hypoglycemia, unspecified",
    "I63.9": "Cerebral infarction, unspecified", "I21.4": "Non-ST elevation (NSTEMI) myocardial infarction",
    "K92.2": "Gastrointestinal hemorrhage, unspecified", "F33.2": "Major depressive disorder, recurrent severe without psychotic features",
    "G47.33": "Obstructive sleep apnea (adult) (pediatric)", "R26.89": "Other abnormalities of gait and mobility",
    # preventive / encounters
    "Z00.00": "Encounter for general adult medical examination without abnormal findings",
    "Z00.01": "Encounter for general adult medical examination with abnormal findings",
    "Z00.129": "Encounter for routine child health examination without abnormal findings",
    "Z12.31": "Encounter for screening mammogram for malignant neoplasm of breast",
    "Z12.11": "Encounter for screening for malignant neoplasm of colon",
    "Z12.12": "Encounter for screening for malignant neoplasm of rectum",
    "Z23": "Encounter for immunization", "Z01.00": "Encounter for examination of eyes and vision without abnormal findings",
    "Z38.00": "Single liveborn infant, delivered vaginally", "O80": "Encounter for full-term uncomplicated delivery",
    "Z37.0": "Single live birth", "Z47.1": "Aftercare following joint replacement surgery",
    "Z96.651": "Presence of right artificial knee joint", "Z86.73": "Personal history of TIA and cerebral infarction without residual deficits",
    "Z59.41": "Food insecurity", "Z59.00": "Homelessness, unspecified",
}

ACUTE_DX = {  # dx used for acute office / urgent visits with relative weights
    "J06.9": 0.24, "J02.9": 0.08, "N39.0": 0.10, "M54.9": 0.14, "R10.9": 0.06, "K52.9": 0.05,
    "S93.401A": 0.05, "S01.81XA": 0.03, "R07.9": 0.04, "U07.1": 0.06, "H66.90": 0.05, "G47.33": 0.03,
    "E86.0": 0.02, "R55": 0.02, "J18.9": 0.03,
}

# ---------------------------------------------------------------------------
# Illustrative CMS-HCC (V28-style) crosswalk -- for teaching coding-gap logic.
# Category numbers follow the V28 labels; coefficients are illustrative only.
# ---------------------------------------------------------------------------
HCC_MAP = [
    # icd10, hcc, hcc_label, illustrative coefficient
    ("E11.9", 38, "Diabetes with Glycemic, Unspecified, or No Complications", 0.166),
    ("E11.65", 38, "Diabetes with Glycemic, Unspecified, or No Complications", 0.166),
    ("E11.649", 38, "Diabetes with Glycemic, Unspecified, or No Complications", 0.166),
    ("E11.22", 37, "Diabetes with Chronic Complications", 0.166),
    ("E11.42", 37, "Diabetes with Chronic Complications", 0.166),
    ("E11.319", 37, "Diabetes with Chronic Complications", 0.166),
    ("E11.51", 37, "Diabetes with Chronic Complications", 0.166),
    ("E11.621", 37, "Diabetes with Chronic Complications", 0.166),
    ("E11.10", 36, "Diabetes with Severe Acute Complications", 0.166),
    ("E11.00", 36, "Diabetes with Severe Acute Complications", 0.166),
    ("E66.01", 48, "Morbid Obesity", 0.186), ("Z68.41", 48, "Morbid Obesity", 0.186),
    ("I50.9", 226, "Heart Failure, Except End-Stage and Acute", 0.360),
    ("I50.22", 226, "Heart Failure, Except End-Stage and Acute", 0.360),
    ("I50.32", 226, "Heart Failure, Except End-Stage and Acute", 0.360),
    ("I50.23", 225, "Acute on Chronic Heart Failure", 0.360),
    ("I48.91", 238, "Specified Heart Arrhythmias", 0.299), ("I48.0", 238, "Specified Heart Arrhythmias", 0.299),
    ("J44.9", 280, "Chronic Obstructive Pulmonary Disease and Other Chronic Lung Disorders", 0.319),
    ("J44.1", 280, "Chronic Obstructive Pulmonary Disease and Other Chronic Lung Disorders", 0.319),
    ("N18.31", 329, "Chronic Kidney Disease, Moderate (Stage 3, Except 3B)", 0.127),
    ("N18.32", 328, "Chronic Kidney Disease, Moderate (Stage 3B)", 0.127),
    ("N18.4", 327, "Chronic Kidney Disease, Severe (Stage 4)", 0.514),
    ("N18.5", 326, "Chronic Kidney Disease, Stage 5", 0.815),
    ("F32.1", 155, "Major Depression, Moderate or Severe, without Psychosis", 0.299),
    ("F33.1", 155, "Major Depression, Moderate or Severe, without Psychosis", 0.299),
    ("F33.2", 155, "Major Depression, Moderate or Severe, without Psychosis", 0.299),
    ("M06.9", 93, "Rheumatoid Arthritis and Other Specified Inflammatory Rheumatic Disorders", 0.343),
    ("F03.90", 127, "Dementia, Mild or Unspecified", 0.341),
    ("F11.20", 137, "Drug Use Disorder, Moderate/Severe, or Drug Use with Non-Psychotic Complications", 0.329),
    ("C50.911", 23, "Prostate, Breast, and Other Cancers and Tumors", 0.186),
    ("I63.9", 249, "Ischemic or Unspecified Stroke", 0.230),
    ("Z89.411", 409, "Amputation Status, Lower Limb/Amputation Complications", 0.519),
]

# ---------------------------------------------------------------------------
# Procedures: code -> (description, code_type, category, medicare_like_rate, pa_required)
# Rates are approximate national Medicare-like allowed amounts (teaching only).
# ---------------------------------------------------------------------------
PROCEDURES = {
    # E&M office
    "99202": ("Office/outpatient visit, new patient, straightforward", "CPT", "E&M Office", 73, False),
    "99203": ("Office/outpatient visit, new patient, low MDM", "CPT", "E&M Office", 112, False),
    "99204": ("Office/outpatient visit, new patient, moderate MDM", "CPT", "E&M Office", 168, False),
    "99205": ("Office/outpatient visit, new patient, high MDM", "CPT", "E&M Office", 222, False),
    "99211": ("Office/outpatient visit, established, minimal", "CPT", "E&M Office", 24, False),
    "99212": ("Office/outpatient visit, established, straightforward", "CPT", "E&M Office", 57, False),
    "99213": ("Office/outpatient visit, established, low MDM", "CPT", "E&M Office", 92, False),
    "99214": ("Office/outpatient visit, established, moderate MDM", "CPT", "E&M Office", 130, False),
    "99215": ("Office/outpatient visit, established, high MDM", "CPT", "E&M Office", 183, False),
    # preventive
    "99381": ("Initial preventive visit, infant", "CPT", "Preventive", 120, False),
    "99391": ("Periodic preventive visit, infant", "CPT", "Preventive", 105, False),
    "99393": ("Periodic preventive visit, age 5-11", "CPT", "Preventive", 110, False),
    "99394": ("Periodic preventive visit, age 12-17", "CPT", "Preventive", 120, False),
    "99395": ("Periodic preventive visit, age 18-39", "CPT", "Preventive", 125, False),
    "99396": ("Periodic preventive visit, age 40-64", "CPT", "Preventive", 135, False),
    "99397": ("Periodic preventive visit, age 65+", "CPT", "Preventive", 145, False),
    "G0438": ("Annual wellness visit, initial", "HCPCS", "Preventive", 170, False),
    "G0439": ("Annual wellness visit, subsequent", "HCPCS", "Preventive", 115, False),
    "90686": ("Influenza vaccine, quadrivalent, preservative free", "CPT", "Immunization", 20, False),
    "G0008": ("Administration of influenza vaccine", "HCPCS", "Immunization", 33, False),
    # ED professional
    "99281": ("Emergency department visit, level 1", "CPT", "E&M ED", 22, False),
    "99282": ("Emergency department visit, level 2", "CPT", "E&M ED", 40, False),
    "99283": ("Emergency department visit, level 3", "CPT", "E&M ED", 70, False),
    "99284": ("Emergency department visit, level 4", "CPT", "E&M ED", 120, False),
    "99285": ("Emergency department visit, level 5", "CPT", "E&M ED", 175, False),
    # inpatient professional
    "99223": ("Initial hospital inpatient care, high", "CPT", "E&M Inpatient", 205, False),
    "99232": ("Subsequent hospital inpatient care, moderate", "CPT", "E&M Inpatient", 80, False),
    "99239": ("Hospital discharge day management, >30 min", "CPT", "E&M Inpatient", 110, False),
    "99495": ("Transitional care management, moderate complexity", "CPT", "Care Management", 200, False),
    "99490": ("Chronic care management, first 20 minutes", "CPT", "Care Management", 62, False),
    # CPT II quality codes ($0)
    "3044F": ("Most recent HbA1c level < 7.0%", "CPT II", "Quality Reporting", 0, False),
    "3051F": ("Most recent HbA1c level >= 7.0% and < 8.0%", "CPT II", "Quality Reporting", 0, False),
    "3052F": ("Most recent HbA1c level >= 8.0% and <= 9.0%", "CPT II", "Quality Reporting", 0, False),
    "3046F": ("Most recent HbA1c level > 9.0%", "CPT II", "Quality Reporting", 0, False),
    "3074F": ("Most recent systolic BP < 130 mm Hg", "CPT II", "Quality Reporting", 0, False),
    "3075F": ("Most recent systolic BP 130-139 mm Hg", "CPT II", "Quality Reporting", 0, False),
    "3077F": ("Most recent systolic BP >= 140 mm Hg", "CPT II", "Quality Reporting", 0, False),
    "3078F": ("Most recent diastolic BP < 80 mm Hg", "CPT II", "Quality Reporting", 0, False),
    "3079F": ("Most recent diastolic BP 80-89 mm Hg", "CPT II", "Quality Reporting", 0, False),
    "3080F": ("Most recent diastolic BP >= 90 mm Hg", "CPT II", "Quality Reporting", 0, False),
    "2022F": ("Dilated retinal eye exam with interpretation; with evidence of retinopathy", "CPT II", "Quality Reporting", 0, False),
    "2023F": ("Dilated retinal eye exam with interpretation; without evidence of retinopathy", "CPT II", "Quality Reporting", 0, False),
    # labs
    "36415": ("Collection of venous blood by venipuncture", "CPT", "Lab", 3, False),
    "83036": ("Hemoglobin; glycosylated (A1C)", "CPT", "Lab", 9, False),
    "80053": ("Comprehensive metabolic panel", "CPT", "Lab", 11, False),
    "80061": ("Lipid panel", "CPT", "Lab", 13, False),
    "85025": ("Complete blood count with automated differential", "CPT", "Lab", 8, False),
    "82043": ("Albumin; urine, microalbumin, quantitative", "CPT", "Lab", 8, False),
    "82570": ("Creatinine; other source (urine)", "CPT", "Lab", 7, False),
    "81001": ("Urinalysis, automated, with microscopy", "CPT", "Lab", 4, False),
    "84443": ("Thyroid stimulating hormone (TSH)", "CPT", "Lab", 17, False),
    "87633": ("Respiratory virus panel, 12-25 targets", "CPT", "Lab", 416, False),
    "G0483": ("Drug test, definitive, 22 or more drug classes", "HCPCS", "Lab", 246, False),
    "87635": ("SARS-CoV-2 (COVID-19) amplified probe technique", "CPT", "Lab", 51, False),
    "82274": ("Fecal occult blood test, immunoassay (FIT)", "CPT", "Lab", 18, False),
    "81528": ("Oncology (colorectal) screening, multitarget stool DNA", "CPT", "Lab", 509, False),
    # imaging
    "71046": ("Radiologic exam, chest; 2 views", "CPT", "Imaging", 31, False),
    "73562": ("Radiologic exam, knee; 3 views", "CPT", "Imaging", 36, False),
    "77067": ("Screening mammography, bilateral, incl CAD", "CPT", "Imaging", 136, False),
    "74177": ("CT abdomen and pelvis with contrast", "CPT", "Imaging", 330, True),
    "70450": ("CT head/brain without contrast", "CPT", "Imaging", 112, False),
    "72148": ("MRI lumbar spine without contrast", "CPT", "Imaging", 225, True),
    "70553": ("MRI brain without then with contrast", "CPT", "Imaging", 365, True),
    "73721": ("MRI lower extremity joint without contrast", "CPT", "Imaging", 215, True),
    "71250": ("CT thorax without contrast", "CPT", "Imaging", 135, True),
    "78452": ("Myocardial perfusion imaging, SPECT, multiple studies", "CPT", "Imaging", 430, True),
    "93000": ("Electrocardiogram, complete", "CPT", "Cardiology Dx", 17, False),
    "93306": ("Echocardiography, transthoracic, complete with Doppler", "CPT", "Cardiology Dx", 210, False),
    "95810": ("Polysomnography, attended, 4+ parameters", "CPT", "Sleep", 560, True),
    # eye
    "92014": ("Ophthalmological services, comprehensive, established", "CPT", "Eye", 128, False),
    "92250": ("Fundus photography with interpretation and report", "CPT", "Eye", 40, False),
    # procedures
    "45378": ("Colonoscopy, flexible; diagnostic", "CPT", "Procedure", 375, False),
    "45380": ("Colonoscopy, flexible; with biopsy", "CPT", "Procedure", 445, False),
    "27447": ("Arthroplasty, knee, total", "CPT", "Surgery", 1300, True),
    "20610": ("Arthrocentesis/injection, major joint", "CPT", "Procedure", 62, False),
    "11042": ("Debridement, subcutaneous tissue, first 20 sq cm", "CPT", "Procedure", 125, False),
    "28820": ("Amputation, toe; metatarsophalangeal joint", "CPT", "Surgery", 620, False),
    "59400": ("Routine obstetric care incl antepartum, vaginal delivery, postpartum", "CPT", "Obstetrics", 2300, False),
    "99460": ("Initial hospital care, normal newborn", "CPT", "E&M Inpatient", 110, False),
    # therapy / behavioral
    "97110": ("Therapeutic exercises, each 15 min", "CPT", "Physical Therapy", 30, False),
    "97140": ("Manual therapy techniques, each 15 min", "CPT", "Physical Therapy", 28, False),
    "97112": ("Neuromuscular reeducation, each 15 min", "CPT", "Physical Therapy", 34, False),
    "97530": ("Therapeutic activities, each 15 min", "CPT", "Physical Therapy", 36, False),
    "97161": ("PT evaluation, low complexity", "CPT", "Physical Therapy", 100, False),
    "90834": ("Psychotherapy, 45 minutes", "CPT", "Behavioral Health", 105, False),
    "90837": ("Psychotherapy, 60 minutes", "CPT", "Behavioral Health", 155, False),
    "90792": ("Psychiatric diagnostic evaluation with medical services", "CPT", "Behavioral Health", 205, False),
    # DME
    "E0601": ("Continuous positive airway pressure (CPAP) device", "HCPCS", "DME", 85, True),
    "E1390": ("Oxygen concentrator", "HCPCS", "DME", 160, False),
    "K0001": ("Standard wheelchair", "HCPCS", "DME", 60, False),
    "L0650": ("Lumbar-sacral orthosis, sagittal-coronal control, prefabricated", "HCPCS", "DME", 1050, False),
    "L1833": ("Knee orthosis, adjustable knee joints, prefabricated", "HCPCS", "DME", 520, False),
    "E0114": ("Crutches, underarm, pair", "HCPCS", "DME", 45, False),
    # facility revenue-code-only placeholders (for outpatient facility lines)
    "G0463": ("Hospital outpatient clinic visit", "HCPCS", "Facility", 130, False),
}

# Facility (hospital outpatient) ED level rates and revenue codes
ED_FACILITY_RATE = {"99281": 80, "99282": 150, "99283": 270, "99284": 445, "99285": 640}

REVENUE_CODES = {
    "0120": "Room & board - semi-private", "0200": "Intensive care unit", "0250": "Pharmacy - general",
    "0270": "Medical/surgical supplies", "0300": "Laboratory - general", "0320": "Radiology - diagnostic",
    "0350": "CT scan", "0360": "Operating room services", "0370": "Anesthesia", "0410": "Respiratory services",
    "0420": "Physical therapy", "0450": "Emergency room", "0610": "MRI", "0341": "Nuclear medicine - diagnostic", "0403": "Screening mammography", "0636": "Drugs requiring detailed coding",
    "0710": "Recovery room", "0730": "EKG/ECG", "0750": "Gastrointestinal services", "0761": "Treatment room",
    "0022": "SNF PPS (HIPPS)", "0191": "Subacute care - level I", "0720": "Labor room/delivery",
    "0170": "Nursery",
}

# ---------------------------------------------------------------------------
# MS-DRGs: drg -> (description, approx weight)
# ---------------------------------------------------------------------------
DRGS = {
    "064": ("Intracranial hemorrhage or cerebral infarction w MCC", 1.80),
    "065": ("Intracranial hemorrhage or cerebral infarction w CC or tPA in 24 hrs", 1.03),
    "177": ("Respiratory infections and inflammations w MCC", 1.75),
    "178": ("Respiratory infections and inflammations w CC", 1.25),
    "190": ("Chronic obstructive pulmonary disease w MCC", 1.12),
    "192": ("Chronic obstructive pulmonary disease w/o CC/MCC", 0.73),
    "193": ("Simple pneumonia and pleurisy w MCC", 1.30),
    "194": ("Simple pneumonia and pleurisy w CC", 0.90),
    "247": ("Perc cardiovasc proc w drug-eluting stent w/o MCC", 2.00),
    "280": ("Acute myocardial infarction, discharged alive w MCC", 1.70),
    "282": ("Acute myocardial infarction, discharged alive w/o CC/MCC", 0.75),
    "291": ("Heart failure and shock w MCC", 1.33),
    "292": ("Heart failure and shock w CC", 0.90),
    "308": ("Cardiac arrhythmia and conduction disorders w MCC", 1.17),
    "309": ("Cardiac arrhythmia and conduction disorders w CC", 0.80),
    "378": ("G.I. hemorrhage w CC", 1.00),
    "392": ("Esophagitis, gastroent and misc digest disorders w/o MCC", 0.75),
    "470": ("Major hip and knee joint replacement w/o MCC", 1.90),
    "552": ("Medical back problems w/o MCC", 0.85),
    "616": ("Amputation of lower limb for endocrine, nutrit, and metabol dis w MCC", 3.90),
    "617": ("Amputation of lower limb for endocrine, nutrit, and metabol dis w CC", 2.00),
    "637": ("Diabetes w MCC", 1.38),
    "638": ("Diabetes w CC", 0.87),
    "640": ("Misc disorders of nutrition, metabolism, fluids/electrolytes w MCC", 1.10),
    "641": ("Misc disorders of nutrition, metabolism, fluids/electrolytes w/o MCC", 0.75),
    "683": ("Renal failure w CC", 0.90),
    "690": ("Kidney and urinary tract infections w/o MCC", 0.80),
    "795": ("Normal newborn", 0.17),
    "807": ("Vaginal delivery w/o sterilization/D&C w/o CC/MCC", 0.65),
    "871": ("Septicemia or severe sepsis w/o MV >96 hours w MCC", 1.87),
    "872": ("Septicemia or severe sepsis w/o MV >96 hours w/o MCC", 1.03),
    "885": ("Psychoses", 1.30),
    "896": ("Alcohol, drug abuse or dependence w/o rehabilitation therapy w MCC", 1.55),
    "917": ("Poisoning and toxic effects of drugs w MCC", 1.40),
    "918": ("Poisoning and toxic effects of drugs w/o MCC", 0.65),
}
IPPS_BASE_RATE = 6800.0

# Inpatient admission reasons: reason -> (drg, principal dx, mean LOS, other dx)
ADMIT_REASONS = {
    "CHF":       [("291", "I50.23", 5.0), ("292", "I50.9", 3.8)],
    "COPD":      [("190", "J44.1", 4.5), ("192", "J44.1", 3.0)],
    "PNEUMONIA": [("193", "J18.9", 4.8), ("194", "J18.9", 3.5)],
    "SEPSIS":    [("871", "A41.9", 6.5), ("872", "A41.9", 4.2)],
    "COVID":     [("177", "U07.1", 7.0), ("178", "U07.1", 4.8)],
    "AFIB":      [("308", "I48.91", 3.6), ("309", "I48.91", 2.6)],
    "AMI":       [("280", "I21.4", 4.5), ("282", "I21.4", 2.5), ("247", "I21.4", 2.5)],
    "STROKE":    [("064", "I63.9", 5.5), ("065", "I63.9", 3.4)],
    "DIAB":      [("637", "E11.10", 4.0), ("638", "E11.65", 3.0)],
    "HYPOGLY":   [("640", "E11.649", 3.2), ("641", "E11.649", 2.2)],
    "AMPUT":     [("616", "E11.621", 9.5), ("617", "E11.621", 6.0)],
    "UTI":       [("690", "N39.0", 3.2)],
    "GI":        [("378", "K92.2", 3.5), ("392", "K52.9", 2.8)],
    "RENAL":     [("683", "N18.4", 4.2)],
    "PSYCH":     [("885", "F33.2", 8.5)],
    "OVERDOSE":  [("917", "T40.2X1A", 3.0), ("918", "T40.2X1A", 1.8)],
    "BACK":      [("552", "M54.9", 3.0)],
    "TKA":       [("470", "M17.11", 2.0)],
    "DELIVERY":  [("807", "O80", 2.0)],
}

# ---------------------------------------------------------------------------
# CARC (claim adjustment reason codes) used in remits / denials
# ---------------------------------------------------------------------------
CARC = {
    "1": ("PR", "Deductible amount", "Patient Responsibility"),
    "2": ("PR", "Coinsurance amount", "Patient Responsibility"),
    "3": ("PR", "Co-payment amount", "Patient Responsibility"),
    "4": ("CO", "The procedure code is inconsistent with the modifier used or a required modifier is missing", "Coding"),
    "11": ("CO", "The diagnosis is inconsistent with the procedure", "Coding"),
    "16": ("CO", "Claim/service lacks information or has submission/billing error(s)", "Front-end / Data"),
    "18": ("CO", "Exact duplicate claim/service", "Duplicate"),
    "22": ("CO", "This care may be covered by another payer per coordination of benefits", "Eligibility / COB"),
    "27": ("CO", "Expenses incurred after coverage terminated", "Eligibility / COB"),
    "29": ("CO", "The time limit for filing has expired", "Timely Filing"),
    "45": ("CO", "Charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement", "Contractual"),
    "50": ("CO", "These are non-covered services because this is not deemed a 'medical necessity' by the payer", "Medical Necessity"),
    "96": ("CO", "Non-covered charge(s)", "Non-covered"),
    "97": ("CO", "The benefit for this service is included in the payment/allowance for another service/procedure that has already been adjudicated", "Bundling"),
    "109": ("CO", "Claim/service not covered by this payer/contractor", "Eligibility / COB"),
    "119": ("CO", "Benefit maximum for this time period or occurrence has been reached", "Benefit Limit"),
    "197": ("CO", "Precertification/authorization/notification/pre-treatment absent", "Authorization"),
    "242": ("CO", "Services not provided by network/primary care providers", "Network"),
    "253": ("CO", "Sequestration - reduction in federal payment", "Contractual"),
}

NCPDP_REJECT = {
    "65": "Patient is not covered",
    "70": "Product/service not covered",
    "75": "Prior authorization required",
    "76": "Plan limitations exceeded",
    "79": "Refill too soon",
}

# ---------------------------------------------------------------------------
# Plans. fee_mult is relative to Medicare-like rates.
# ---------------------------------------------------------------------------
# payer_type codes used internally
NONE, COMM, MKT, MCD_FFS, MCD_MC, MCR_FFS, MA = range(7)
PAYER_TYPE_NAME = {NONE: "Uninsured", COMM: "Commercial", MKT: "Marketplace", MCD_FFS: "Medicaid FFS",
                   MCD_MC: "Medicaid Managed Care", MCR_FFS: "Medicare FFS", MA: "Medicare Advantage"}
PAYER_CATEGORY = {NONE: "None", COMM: "Private", MKT: "Private", MCD_FFS: "Public", MCD_MC: "Public",
                  MCR_FFS: "Public", MA: "Public"}

PLANS = [
    # plan_id, name, payer_type, product, funding, metal, ded, coins, cp_pcp, cp_spec, cp_ed, ip_copay, oop, fee_mult, denial_mult, pa, days_to_pay, timely_days, hmo, weight
    ("TW-PPO", "Tidewater Health PPO", COMM, "PPO", "Fully Insured", None, 1500, 0.20, 30, 60, 300, 0, 6500, 2.10, 1.10, True, 24, 180, False, 0.45),
    ("TW-HMO", "Tidewater Health HMO", COMM, "HMO", "Fully Insured", None, 750, 0.15, 20, 45, 250, 0, 5000, 1.85, 1.20, True, 22, 180, True, 0.25),
    ("TW-HDHP", "Tidewater Health HDHP/HSA", COMM, "HDHP", "Fully Insured", None, 3200, 0.20, 0, 0, 0, 0, 7000, 2.10, 1.05, True, 24, 180, False, 0.20),
    ("PB-ASO", "Pelican Benefit Trust (Self-Funded PPO)", COMM, "PPO", "Self-Funded (ASO)", None, 1000, 0.20, 25, 50, 250, 0, 5000, 2.25, 0.95, True, 28, 365, False, 0.10),
    ("HH-BRZ", "Heron Health Marketplace Bronze", MKT, "EPO", "Fully Insured", "Bronze", 7000, 0.40, 0, 0, 0, 0, 9100, 1.45, 1.25, True, 30, 180, False, 0.25),
    ("HH-SLV", "Heron Health Marketplace Silver", MKT, "EPO", "Fully Insured", "Silver", 4500, 0.30, 35, 70, 400, 0, 8700, 1.45, 1.25, True, 30, 180, False, 0.45),
    ("HH-GLD", "Heron Health Marketplace Gold", MKT, "EPO", "Fully Insured", "Gold", 1500, 0.20, 25, 50, 300, 0, 7500, 1.45, 1.20, True, 30, 180, False, 0.10),
    ("MG-SLV", "Mangrove Marketplace Silver HMO", MKT, "HMO", "Fully Insured", "Silver", 4000, 0.30, 30, 65, 400, 0, 8700, 1.35, 1.35, True, 34, 180, True, 0.20),
    ("FL-MCD", "Florida Medicaid Fee-for-Service", MCD_FFS, "FFS", "Public", None, 0, 0.0, 0, 0, 0, 0, 0, 0.72, 1.00, False, 38, 365, False, 1.0),
    ("CY-MMA", "Cypress Community Health Plan (Medicaid MMA)", MCD_MC, "HMO", "Capitated", None, 0, 0.0, 0, 0, 0, 0, 0, 0.78, 1.40, True, 32, 365, True, 0.55),
    ("MN-MMA", "Manatee Medicaid Managed Care", MCD_MC, "HMO", "Capitated", None, 0, 0.0, 0, 0, 0, 0, 0, 0.75, 1.50, True, 36, 365, True, 0.45),
    ("MCR-FFS", "Original Medicare (Parts A/B)", MCR_FFS, "FFS", "Public", None, -1, 0.20, 0, 0, 0, -1, 0, 1.00, 0.70, False, 16, 365, False, 1.0),
    ("LL-MAHMO", "Longleaf Medicare Advantage HMO", MA, "HMO", "Capitated", None, 0, 0.0, 5, 40, 95, 1500, 4900, 1.00, 1.55, True, 20, 365, True, 0.40),
    ("LL-MAPPO", "Longleaf Medicare Advantage PPO", MA, "PPO", "Capitated", None, 0, 0.0, 10, 45, 110, 1750, 6700, 1.02, 1.45, True, 22, 365, False, 0.25),
    ("OS-MAHMO", "Osprey Medicare Advantage HMO", MA, "HMO", "Capitated", None, 0, 0.0, 0, 35, 90, 1400, 4500, 0.99, 1.65, True, 20, 365, True, 0.35),
    ("OS-DSNP", "Osprey Dual Complete (HMO D-SNP)", MA, "HMO D-SNP", "Capitated", None, 0, 0.0, 0, 0, 0, 0, 0, 1.00, 1.60, True, 20, 365, True, 0.0),
]
PLAN_COLS = ["plan_id", "plan_name", "payer_type_code", "product_type", "funding_type", "metal_tier", "deductible",
             "coinsurance", "copay_pcp", "copay_specialist", "copay_ed", "inpatient_copay", "oop_max", "fee_mult",
             "denial_mult", "requires_prior_auth", "avg_days_to_pay", "timely_filing_days", "requires_pcp", "weight"]
PDP_PLAN = ("KS-PDP", "Kestrel Rx Prescription Drug Plan (Part D)")

# Medicare FFS cost sharing by year (real published values)
PART_B_DEDUCTIBLE = {2021: 203, 2022: 233, 2023: 226, 2024: 240, 2025: 257}
PART_A_DEDUCTIBLE = {2021: 1484, 2022: 1556, 2023: 1600, 2024: 1632, 2025: 1676}
PART_B_PREMIUM = {2021: 148.50, 2022: 170.10, 2023: 164.90, 2024: 174.70, 2025: 185.00}

# ---------------------------------------------------------------------------
# Drugs: key -> (drug_name, generic, class, daily_cost, tier, pa_required, brand/generic, specialty, avail_from_month)
# ---------------------------------------------------------------------------
DRUGS = {
    "METFORMIN":   ("Metformin HCl 500 mg tablet", "metformin", "Antidiabetic - Biguanide", 0.15, 1, False, "Generic", False, 0),
    "GLIPIZIDE":   ("Glipizide 5 mg tablet", "glipizide", "Antidiabetic - Sulfonylurea", 0.20, 1, False, "Generic", False, 0),
    "GLARGINE":    ("Insulin glargine 100 unit/mL pen", "insulin glargine", "Antidiabetic - Insulin", 9.50, 3, False, "Brand", False, 0),
    "SEMAGLUTIDE": ("Ozempic (semaglutide) 1 mg/dose pen", "semaglutide", "Antidiabetic - GLP-1 RA", 31.00, 3, True, "Brand", False, 0),
    "TIRZEPATIDE": ("Mounjaro (tirzepatide) 5 mg/0.5 mL pen", "tirzepatide", "Antidiabetic - GIP/GLP-1 RA", 34.00, 3, True, "Brand", False, 17),
    "EMPAGLIFLOZIN": ("Jardiance (empagliflozin) 10 mg tablet", "empagliflozin", "Antidiabetic - SGLT2 inhibitor", 19.50, 3, False, "Brand", False, 0),
    "LISINOPRIL":  ("Lisinopril 10 mg tablet", "lisinopril", "Antihypertensive - ACE inhibitor", 0.10, 1, False, "Generic", False, 0),
    "AMLODIPINE":  ("Amlodipine 5 mg tablet", "amlodipine", "Antihypertensive - CCB", 0.12, 1, False, "Generic", False, 0),
    "LOSARTAN":    ("Losartan 50 mg tablet", "losartan", "Antihypertensive - ARB", 0.20, 1, False, "Generic", False, 0),
    "HCTZ":        ("Hydrochlorothiazide 25 mg tablet", "hydrochlorothiazide", "Antihypertensive - Diuretic", 0.10, 1, False, "Generic", False, 0),
    "ATORVASTATIN": ("Atorvastatin 40 mg tablet", "atorvastatin", "Statin", 0.20, 1, False, "Generic", False, 0),
    "ROSUVASTATIN": ("Rosuvastatin 20 mg tablet", "rosuvastatin", "Statin", 0.28, 1, False, "Generic", False, 0),
    "METOPROLOL":  ("Metoprolol succinate ER 50 mg tablet", "metoprolol succinate", "Beta blocker", 0.33, 1, False, "Generic", False, 0),
    "CARVEDILOL":  ("Carvedilol 12.5 mg tablet", "carvedilol", "Beta blocker", 0.20, 1, False, "Generic", False, 0),
    "FUROSEMIDE":  ("Furosemide 40 mg tablet", "furosemide", "Loop diuretic", 0.13, 1, False, "Generic", False, 0),
    "SPIRONOLACTONE": ("Spironolactone 25 mg tablet", "spironolactone", "Aldosterone antagonist", 0.20, 1, False, "Generic", False, 0),
    "ENTRESTO":    ("Entresto (sacubitril/valsartan) 49-51 mg tablet", "sacubitril/valsartan", "ARNI", 21.50, 3, True, "Brand", False, 0),
    "APIXABAN":    ("Eliquis (apixaban) 5 mg tablet", "apixaban", "Anticoagulant - DOAC", 18.50, 3, False, "Brand", False, 0),
    "WARFARIN":    ("Warfarin 5 mg tablet", "warfarin", "Anticoagulant - VKA", 0.25, 1, False, "Generic", False, 0),
    "ALBUTEROL":   ("Albuterol sulfate HFA 90 mcg inhaler", "albuterol", "Bronchodilator - SABA", 1.15, 2, False, "Generic", False, 0),
    "FLUTICASONE_SALM": ("Fluticasone/salmeterol 250/50 inhaler", "fluticasone/salmeterol", "Inhaled corticosteroid/LABA", 3.00, 2, False, "Generic", False, 0),
    "TIOTROPIUM":  ("Spiriva (tiotropium) 18 mcg inhalation capsule", "tiotropium", "Bronchodilator - LAMA", 17.00, 3, False, "Brand", False, 0),
    "MONTELUKAST": ("Montelukast 10 mg tablet", "montelukast", "Leukotriene modifier", 0.27, 1, False, "Generic", False, 0),
    "SERTRALINE":  ("Sertraline 50 mg tablet", "sertraline", "Antidepressant - SSRI", 0.17, 1, False, "Generic", False, 0),
    "ESCITALOPRAM": ("Escitalopram 10 mg tablet", "escitalopram", "Antidepressant - SSRI", 0.17, 1, False, "Generic", False, 0),
    "BUPROPION":   ("Bupropion XL 150 mg tablet", "bupropion", "Antidepressant - NDRI", 0.50, 1, False, "Generic", False, 0),
    "ADALIMUMAB":  ("Adalimumab 40 mg/0.4 mL pen", "adalimumab", "Immunology - TNF inhibitor", 230.0, 5, True, "Brand", True, 0),
    "METHOTREXATE": ("Methotrexate 2.5 mg tablet", "methotrexate", "DMARD", 0.65, 1, False, "Generic", False, 0),
    "DONEPEZIL":   ("Donepezil 10 mg tablet", "donepezil", "Cholinesterase inhibitor", 0.33, 1, False, "Generic", False, 0),
    "BUPRENORPHINE": ("Buprenorphine/naloxone 8-2 mg SL film", "buprenorphine/naloxone", "Opioid use disorder", 11.50, 2, True, "Generic", False, 0),
    "ANASTROZOLE": ("Anastrozole 1 mg tablet", "anastrozole", "Antineoplastic - aromatase inhibitor", 0.35, 1, False, "Generic", False, 0),
    "LEVOTHYROXINE": ("Levothyroxine 75 mcg tablet", "levothyroxine", "Thyroid", 0.27, 1, False, "Generic", False, 0),
    "OMEPRAZOLE":  ("Omeprazole 20 mg capsule", "omeprazole", "Proton pump inhibitor", 0.20, 1, False, "Generic", False, 0),
    "GABAPENTIN":  ("Gabapentin 300 mg capsule", "gabapentin", "Anticonvulsant/neuropathic pain", 0.33, 1, False, "Generic", False, 0),
    "OXYCODONE5":  ("Oxycodone HCl 5 mg tablet", "oxycodone", "Opioid analgesic", 0.80, 2, False, "Generic", False, 0),
    "OXYCODONE30": ("Oxycodone HCl 30 mg tablet", "oxycodone", "Opioid analgesic", 4.10, 2, False, "Generic", False, 0),
    "HYDROCODONE": ("Hydrocodone/acetaminophen 5-325 mg tablet", "hydrocodone/acetaminophen", "Opioid analgesic", 0.70, 2, False, "Generic", False, 0),
    "TRAMADOL":    ("Tramadol 50 mg tablet", "tramadol", "Opioid analgesic", 0.30, 1, False, "Generic", False, 0),
    "NALOXONE":    ("Naloxone 4 mg nasal spray", "naloxone", "Opioid antagonist", 45.0, 2, False, "Generic", False, 0),
    "AMOXICILLIN": ("Amoxicillin 500 mg capsule", "amoxicillin", "Antibiotic - Penicillin", 0.80, 1, False, "Generic", False, 0),
    "AZITHROMYCIN": ("Azithromycin 250 mg tablet", "azithromycin", "Antibiotic - Macrolide", 2.00, 1, False, "Generic", False, 0),
    "NITROFURANTOIN": ("Nitrofurantoin monohyd/macro 100 mg capsule", "nitrofurantoin", "Antibiotic - Urinary", 2.10, 1, False, "Generic", False, 0),
    "PREDNISONE":  ("Prednisone 20 mg tablet", "prednisone", "Corticosteroid", 0.60, 1, False, "Generic", False, 0),
    "ONDANSETRON": ("Ondansetron 4 mg ODT", "ondansetron", "Antiemetic", 0.90, 1, False, "Generic", False, 0),
    "CYCLOBENZAPRINE": ("Cyclobenzaprine 10 mg tablet", "cyclobenzaprine", "Muscle relaxant", 0.40, 1, False, "Generic", False, 0),
}
# opioid morphine milligram equivalent per unit (for MME teaching)
MME_PER_UNIT = {"OXYCODONE5": 7.5, "OXYCODONE30": 45.0, "HYDROCODONE": 5.0, "TRAMADOL": 5.0}

# Specialty -> NUCC taxonomy code
TAXONOMY = {
    "Family Medicine": "207Q00000X", "Internal Medicine": "207R00000X", "Pediatrics": "208000000X",
    "Nurse Practitioner": "363L00000X", "Cardiology": "207RC0000X", "Endocrinology": "207RE0101X",
    "Pulmonology": "207RP1001X", "Nephrology": "207RN0300X", "Psychiatry": "2084P0800X",
    "Clinical Social Worker": "1041C0700X", "Orthopaedic Surgery": "207X00000X", "Ophthalmology": "207W00000X",
    "Optometry": "152W00000X", "Gastroenterology": "207RG0100X", "Obstetrics & Gynecology": "207V00000X",
    "Emergency Medicine": "207P00000X", "Hospitalist": "208M00000X", "Diagnostic Radiology": "2085R0202X",
    "Rheumatology": "207RR0500X", "Hematology & Oncology": "207RH0003X", "Podiatry": "213E00000X",
    "Pain Medicine": "208VP0014X", "Physical Therapy": "225100000X", "General Acute Care Hospital": "282N00000X",
    "Skilled Nursing Facility": "314000000X", "Clinical Medical Laboratory": "291U00000X",
    "Durable Medical Equipment": "332B00000X", "Community/Retail Pharmacy": "3336C0003X",
    "Mail Order Pharmacy": "3336M0002X", "Specialty Pharmacy": "3336S0011X", "Radiology Imaging Center": "261QR0200X",
}
