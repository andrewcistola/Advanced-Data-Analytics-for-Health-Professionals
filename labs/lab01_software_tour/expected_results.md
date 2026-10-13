# Expected results: lab01_software_tour

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab01_software_tour
====================================================================================================
   rows_  distinct_keys
0  25000          25000
    rows_  distinct_keys
0  639612         639612
   rows_  distinct_keys
0    241            241
--- end of block 1 ---
      claim_id claim_setting  line_number procedure_code  line_allowed
0  C0000000001    Telehealth            1          99204        126.00
1  C0000000002    Telehealth            1          99204        352.80
2  C0000000003        Office            1          99204        131.04
3  C0000000004        Office            1          99204        201.53
4  C0000000004        Office            2          3074F          0.00
5  C0000000004        Office            3          3078F          0.00
6  C0000000005    Laboratory            1          87635          0.00
7  C0000000005    Laboratory            2          36415          0.00
8  C0000000006    Laboratory            1          87635         51.00
9  C0000000006    Laboratory            2          36415          3.00
      claim_id                       provider_name                    specialty
0  C0000132481                     Rivera, Mary MD           Emergency Medicine
1  C0000132525  Understory Regional Medical Center  General Acute Care Hospital
2  C0000132526                    Charles, Erik MD           Emergency Medicine
3  C0000132538           Coquina Regional Hospital  General Acute Care Hospital
4  C0000132539                  Johnson, Curtis MD           Emergency Medicine
5  C0000132568  Understory Regional Medical Center  General Acute Care Hospital
6  C0000132569                    Evans, Nathan MD           Emergency Medicine
7  C0000132673           Coquina Regional Hospital  General Acute Care Hospital
8  C0000132674                  Potter, Sabrina MD           Emergency Medicine
9  C0000132675                  Potter, Sabrina MD           Emergency Medicine
--- end of block 2 ---
  member_id sex birth_date  age_end_2025 zip_code county death_date
0  M0100141   M 1973-02-06            52    32625   Levy        NaT
   payer_type             plan_name first_month last_month  months
0  Commercial  Tidewater Health PPO  2021-01-01 2025-12-01      60
         claim_setting  claims   allowed
0               Office      51   13631.0
1           Laboratory      15     659.0
2            Inpatient       9  103228.0
3            Emergency       8    3529.0
4           Telehealth       5    1202.0
5  Outpatient Hospital       2    1957.0
      dx_1                                                                    description  claims
0    I50.9                                                     Heart failure, unspecified      37
1   E11.51  Type 2 diabetes mellitus with diabetic peripheral angiopathy without gangrene      13
2    E11.9                                 Type 2 diabetes mellitus without complications       7
3    M54.9                                                         Dorsalgia, unspecified       7
4  E11.621                                       Type 2 diabetes mellitus with foot ulcer       5
    generic_name  fills first_fill  last_fill
0     furosemide     52 2021-01-06 2025-12-25
1     carvedilol     51 2021-01-26 2025-12-18
2  empagliflozin     47 2021-01-22 2025-12-28
3   atorvastatin     21 2024-01-14 2025-12-06
4      metformin     18 2021-01-21 2025-10-25
5    ondansetron      1 2025-12-06 2025-12-06
--- end of block 3 ---
```
