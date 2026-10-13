# Expected results: lab03_claim_denials

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab03_claim_denials
====================================================================================================
      payer_type  service_year  original_claims  denied  denial_rate_pct
0     Commercial          2021            29021  2628.0              9.1
1     Commercial          2022            30968  2786.0              9.0
2     Commercial          2023            30129  2913.0              9.7
3     Commercial          2024            29326  3007.0             10.3
4     Commercial          2025            28110  2826.0             10.1
5    Marketplace          2021             8440   807.0              9.6
6    Marketplace          2022             8650   920.0             10.6
7    Marketplace          2023             9077   995.0             11.0
8    Marketplace          2024            10139  1174.0             11.6
9    Marketplace          2025             9755  1158.0             11.9
10  Medicaid FFS          2021             2329   243.0             10.4
11  Medicaid FFS          2022             2728   253.0              9.3
12  Medicaid FFS          2023             2952   310.0             10.5
13  Medicaid FFS          2024             2455   284.0             11.6
14  Medicaid FFS          2025             2601   261.0             10.0
--- end of block 1 ---
             denial_category  denied_claims  denied_charges
0  Coding and front-end data          39192      37856216.0
1          Eligibility / COB           9857       9926551.0
2          Medical necessity            904       8045943.0
3              Timely filing           2196       1957691.0
4                      Other           2225       1833641.0
5              Authorization            777       1226392.0
--- end of block 2 ---
             denial_category  denied_accounts  denied_charges  pct_eventually_paid  dollars_paid_later
0                        NaN            55151      60846433.0                 69.4          10751664.0
1  Coding and front-end data            39192      37856216.0                 79.8           8357266.0
2          Eligibility / COB             9857       9926551.0                 65.9           1686048.0
3          Medical necessity              904       8045943.0                 23.5            603100.0
4              Timely filing             2196       1957691.0                  0.0                 0.0
5                      Other             2225       1833641.0                  2.8              6951.0
6              Authorization              777       1226392.0                 28.4             98300.0
--- end of block 3 ---
```
