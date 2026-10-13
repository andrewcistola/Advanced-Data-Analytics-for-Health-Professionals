# Expected results: lab12_fraud_detection

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab12_fraud_detection
====================================================================================================
217 providers profiled
--- end of block 1 ---
 k  inertia  silhouette
 2  964.934       0.552
 3  727.290       0.555
 4  584.721       0.557
 5  455.398       0.428
 6  367.530       0.437
 7  285.529       0.459
 8  235.217       0.484
 9  204.660       0.385
10  179.776       0.397
--- end of block 2 ---
           n  claims_per_patient  units_per_claim  charge_per_claim  share_99215  share_far_patients  after_death_share
cluster                                                                                                                
0        123                5.16             1.50            375.22         0.07                0.12               0.00
1         24                5.77             5.05           2611.98         0.00                0.18               0.00
2         35                8.82             1.52            365.02         0.06                0.24               0.00
3          1                1.42             1.00           2161.22         0.00                0.53               0.08
4          2               10.70             1.56            458.72         0.65                0.10               0.00
5         32                1.43             1.20            512.72         0.00                0.20               0.00
--- end of block 3 ---
            provider_name                 specialty  cluster  small_cluster  outlier_score  claims_per_patient  units_per_claim  charge_per_claim  share_99215  share_far_patients  after_death_share
Keystone Bracing & Supply Durable Medical Equipment        3           True          15.76                1.42             1.00           2161.22         0.00                0.53               0.08
         Murillo, Judy MD         Internal Medicine        4           True           8.22               11.71             1.60            461.39         0.65                0.11               0.00
       Lewis, Benjamin MD         Internal Medicine        4           True           8.20                9.69             1.52            456.04         0.65                0.10               0.00
        Ball, Kimberly PT          Physical Therapy        1          False           4.82               34.31            10.77           1091.66         0.00                0.14               0.00
      Lambert, Natalie PT          Physical Therapy        1          False           4.75               33.32            10.75           1083.09         0.00                0.16               0.00
          Frost, Aaron PT          Physical Therapy        1          False           4.74               33.02            10.76           1085.30         0.00                0.20               0.00
          Jones, Helen MD             Pain Medicine        2          False           4.04               17.14             1.00            466.36         0.31                0.33               0.00
      Shields, Rebekah MD   Obstetrics & Gynecology        1          False           3.72                1.04             1.00           7435.10         0.00                0.22               0.00
     Rodriguez, Rachel MD   Obstetrics & Gynecology        1          False           3.71                1.03             1.00           7392.84         0.00                0.22               0.00
           Adams, Rita MD   Obstetrics & Gynecology        1          False           3.71                1.03             1.00           7398.18         0.00                0.15               0.00
--- end of block 4 ---
 rank                  provider_name                       scheme
    1      Keystone Bracing & Supply           DME_PHANTOM_BRACES
    2               Murillo, Judy MD                  EM_UPCODING
    3             Lewis, Benjamin MD                  EM_UPCODING
    4              Ball, Kimberly PT           PT_EXCESSIVE_UNITS
    5            Lambert, Natalie PT           PT_EXCESSIVE_UNITS
    6                Frost, Aaron PT           PT_EXCESSIVE_UNITS
    7                Jones, Helen MD         PILL_MILL_PRESCRIBER
   12 Prairie Diagnostics Laboratory        LAB_EXCESSIVE_TESTING
   13              Green, Mandy LCSW IMPOSSIBLE_DAY_PSYCHOTHERAPY
  122                Mills, Kevin MD        LAB_KICKBACK_REFERRER
  136                  Moran, Dan MD        LAB_KICKBACK_REFERRER
  144              Walton, Eugene MD        LAB_KICKBACK_REFERRER
  167             Foster, Cynthia DO        LAB_KICKBACK_REFERRER
  175              Lewis, Michael MD        LAB_KICKBACK_REFERRER
  183                Evans, Megan MD        LAB_KICKBACK_REFERRER
  194               Walls, Brandi MD        LAB_KICKBACK_REFERRER
  214              Kennedy, Laura DO        LAB_KICKBACK_REFERRER
--- end of block 5 ---
```
