# Expected results: lab03_claim_denials

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab03_claim_denials
====================================================================================================
      payer_type  service_year  original_claims  denied  denial_rate_pct
0     Commercial          2021            29464  2335.0              7.9
1     Commercial          2022            31576  2928.0              9.3
2     Commercial          2023            30467  2857.0              9.4
3     Commercial          2024            29974  3135.0             10.5
4     Commercial          2025            28679  2927.0             10.2
5    Marketplace          2021             8726   856.0              9.8
6    Marketplace          2022             9142   990.0             10.8
7    Marketplace          2023             9561  1021.0             10.7
8    Marketplace          2024            10374  1243.0             12.0
9    Marketplace          2025             9790  1156.0             11.8
10  Medicaid FFS          2021             2316   245.0             10.6
11  Medicaid FFS          2022             2755   245.0              8.9
12  Medicaid FFS          2023             2961   303.0             10.2
13  Medicaid FFS          2024             2546   322.0             12.6
14  Medicaid FFS          2025             2410   266.0             11.0
--- end of block 1 ---
             denial_category  denied_claims  denied_charges
0  Coding and front-end data          39721      38212444.0
1          Medical necessity           1010      10817700.0
2          Eligibility / COB          10249      10423960.0
3                      Other           2141       1781063.0
4              Timely filing           2242       1773020.0
5              Authorization            794       1366513.0
--- end of block 2 ---
             denial_category  denied_accounts  denied_charges  pct_eventually_paid  dollars_paid_later
0                        NaN            56157      64374700.0                 69.6          11058012.0
1  Coding and front-end data            39721      38212444.0                 79.7           8339003.0
2          Medical necessity             1010      10817700.0                 22.5            692316.0
3          Eligibility / COB            10249      10423960.0                 67.5           1915029.0
4                      Other             2141       1781063.0                  2.3              5596.0
5              Timely filing             2242       1773020.0                  0.0                 0.0
6              Authorization              794       1366513.0                 25.6            106068.0
--- end of block 3 ---
```
