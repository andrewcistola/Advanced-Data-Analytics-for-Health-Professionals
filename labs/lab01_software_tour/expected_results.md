# Expected results: lab01_software_tour

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab01_software_tour
====================================================================================================
   rows_  distinct_keys
0  25000          25000
    rows_  distinct_keys
0  650869         650869
   rows_  distinct_keys
0    241            241
--- end of block 1 ---
      claim_id claim_setting  line_number procedure_code  line_allowed
0  C0000000001        Office            1          99205        226.44
1  C0000000001        Office            2          3075F          0.00
2  C0000000001        Office            3          3078F          0.00
3  C0000000002        Office            1          99203        235.20
4  C0000000002        Office            2          3075F          0.00
5  C0000000002        Office            3          3078F          0.00
6  C0000000003    Laboratory            1          80053         23.10
7  C0000000003    Laboratory            2          36415          6.30
8  C0000000004    Telehealth            1          99205        222.00
9  C0000000005        Office            1          99204        171.36
      claim_id        provider_name    specialty
0  C0000133262      Tran, Ashley MD  Pulmonology
1  C0000133307      Tran, Ashley MD  Pulmonology
2  C0000133341  Harris, Michelle MD   Nephrology
3  C0000133342  Harris, Michelle MD   Nephrology
4  C0000133400    Jacobs, Denise MD   Nephrology
5  C0000133401    Jacobs, Denise MD   Nephrology
6  C0000133422    Jacobs, Denise MD   Nephrology
7  C0000133479  Harris, Michelle MD   Nephrology
8  C0000133535   Whitehead, John MD   Psychiatry
9  C0000133556    Baker, Madison MD   Psychiatry
--- end of block 2 ---
  member_id sex birth_date  age_end_2025 zip_code  county death_date
0  M0100014   M 1942-05-02            83    34432  Marion        NaT
           payer_type                         plan_name first_month last_month  months
0  Medicare Advantage  Osprey Dual Complete (HMO D-SNP)  2021-01-01 2025-12-01      60
         claim_setting  claims  allowed
0               Office      89  10838.0
1            Emergency      30   7084.0
2           Telehealth      16   1730.0
3            Inpatient      12  32112.0
4           Laboratory       7    199.0
5  Outpatient Hospital       3     32.0
      dx_1                                                                           description  claims
0    F33.1                                        Major depressive disorder, recurrent, moderate      56
1   I25.10       Atherosclerotic heart disease of native coronary artery without angina pectoris      18
2    J44.1                       Chronic obstructive pulmonary disease with (acute) exacerbation      11
3  E11.319  Type 2 diabetes mellitus with unspecified diabetic retinopathy without macular edema       9
4    J44.9                                    Chronic obstructive pulmonary disease, unspecified       9
          generic_name  fills first_fill  last_fill
0            albuterol     23 2021-01-14 2025-11-18
1  hydrochlorothiazide     22 2021-01-06 2025-09-18
2          semaglutide      8 2021-08-14 2022-06-06
3            metformin      7 2021-02-17 2023-07-19
4        empagliflozin      6 2021-01-07 2022-01-09
5            glipizide      5 2021-01-13 2023-10-15
6         atorvastatin      4 2021-02-17 2022-11-12
7           tiotropium      2 2021-01-13 2021-05-03
--- end of block 3 ---
```
