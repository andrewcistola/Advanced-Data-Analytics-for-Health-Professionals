# Expected results: lab12_fraud_detection

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab12_fraud_detection
====================================================================================================
217 providers profiled
--- end of block 1 ---
 k  inertia  silhouette
 2  964.522       0.574
 3  726.611       0.555
 4  585.119       0.566
 5  456.437       0.386
 6  373.099       0.419
 7  284.239       0.440
 8  232.560       0.455
 9  202.424       0.396
10  180.323       0.419
--- end of block 2 ---
           n  claims_per_patient  units_per_claim  charge_per_claim  share_99215  share_far_patients  after_death_share
cluster                                                                                                                
0        130                6.02             1.51            368.37         0.07                0.12               0.00
1         60                3.48             1.34            460.53         0.02                0.21               0.00
2          4               29.09             8.90           1136.40         0.00                0.14               0.00
3         20                1.18             4.27           2906.86         0.00                0.19               0.00
4          1                1.45             1.00           2146.06         0.00                0.52               0.07
5          2               10.69             1.53            459.10         0.64                0.10               0.00
--- end of block 3 ---
            provider_name                 specialty  cluster  small_cluster  outlier_score  claims_per_patient  units_per_claim  charge_per_claim  share_99215  share_far_patients  after_death_share
Keystone Bracing & Supply Durable Medical Equipment        4           True          15.69                1.45             1.00           2146.06         0.00                0.52               0.07
       Lewis, Benjamin MD         Internal Medicine        5           True           8.22                9.88             1.47            456.43         0.65                0.10               0.00
         Murillo, Judy MD         Internal Medicine        5           True           8.12               11.50             1.59            461.77         0.64                0.11               0.00
        Ball, Kimberly PT          Physical Therapy        2           True           5.63               34.61            10.77           1100.06         0.00                0.16               0.00
      Lambert, Natalie PT          Physical Therapy        2           True           5.61               33.96            10.76           1086.62         0.00                0.16               0.00
          Frost, Aaron PT          Physical Therapy        2           True           5.59               33.23            10.76           1093.32         0.00                0.15               0.00
          Jones, Helen MD             Pain Medicine        0          False           5.01               17.43             1.00            464.88         0.29                0.36               0.00
     Rodriguez, Rachel MD   Obstetrics & Gynecology        3          False           3.43                1.04             1.00           7429.13         0.00                0.27               0.00
      Garrison, Shelby MD   Obstetrics & Gynecology        3          False           3.29                1.03             1.00           7392.50         0.00                0.24               0.00
      Shields, Rebekah MD   Obstetrics & Gynecology        3          False           3.29                1.03             1.00           7383.22         0.00                0.14               0.00
--- end of block 4 ---
 rank                  provider_name                       scheme
    1      Keystone Bracing & Supply           DME_PHANTOM_BRACES
    2             Lewis, Benjamin MD                  EM_UPCODING
    3               Murillo, Judy MD                  EM_UPCODING
    4              Ball, Kimberly PT           PT_EXCESSIVE_UNITS
    5            Lambert, Natalie PT           PT_EXCESSIVE_UNITS
    6                Frost, Aaron PT           PT_EXCESSIVE_UNITS
    7                Jones, Helen MD         PILL_MILL_PRESCRIBER
   11              Green, Mandy LCSW IMPOSSIBLE_DAY_PSYCHOTHERAPY
   14 Prairie Diagnostics Laboratory        LAB_EXCESSIVE_TESTING
  111                  Moran, Dan MD        LAB_KICKBACK_REFERRER
  122                Mills, Kevin MD        LAB_KICKBACK_REFERRER
  123              Walton, Eugene MD        LAB_KICKBACK_REFERRER
  154                Evans, Megan MD        LAB_KICKBACK_REFERRER
  159              Lewis, Michael MD        LAB_KICKBACK_REFERRER
  173             Foster, Cynthia DO        LAB_KICKBACK_REFERRER
  199              Kennedy, Laura DO        LAB_KICKBACK_REFERRER
  208               Walls, Brandi MD        LAB_KICKBACK_REFERRER
--- end of block 5 ---
```
