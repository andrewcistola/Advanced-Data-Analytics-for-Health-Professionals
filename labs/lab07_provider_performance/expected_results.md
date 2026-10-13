# Expected results: lab07_provider_performance

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab07_provider_performance
====================================================================================================
                                   practice_name  attributed_members  ed_per_1000  allowed_pmpm
0                          Baker Family Practice                 366        398.9       2809.66
1                       Barnes Internal Medicine                  72        375.0       4505.53
2                        Chapman Family Practice                 473        355.2       2141.44
3                        Farrell Family Practice                 678        382.0       2113.55
4            Gainesville Community Health Center                2024        450.1       2679.45
5   Gainesville Pediatrics & Adolescent Medicine                 226        230.1        962.34
6                  Green Cove Springs Pediatrics                 162        284.0       1112.43
7                  Ocala Community Health Center                 704        448.9       2864.74
8         Ocala Pediatrics & Adolescent Medicine                 259        189.2        884.69
9                            Pierce Primary Care                 198        404.0       2334.29
10         Understory Primary Care - Gainesville                1186        287.5       2162.84
11      Understory Primary Care - Gainesville 24                 721        317.6       2376.34
12           Understory Primary Care - Inverness                 237        286.9       2977.79
13           Understory Primary Care - Lake City                 497        515.1       3046.12
14        Understory Primary Care - Lake City 21                 120        516.7       3048.22
--- end of block 1 ---
                                   practice_name  attributed_members  ed_per_1000  allowed_pmpm
0                          Baker Family Practice                 366        366.1        211.60
1                       Barnes Internal Medicine                  72        347.2        358.39
2                        Chapman Family Practice                 473        329.8        169.61
3                        Farrell Family Practice                 678        348.1        163.36
4            Gainesville Community Health Center                2024        426.4        214.53
5   Gainesville Pediatrics & Adolescent Medicine                 226        216.8         77.09
6                  Green Cove Springs Pediatrics                 162        259.3         92.45
7                  Ocala Community Health Center                 704        411.9        228.04
8         Ocala Pediatrics & Adolescent Medicine                 259        185.3         72.42
9                            Pierce Primary Care                 198        363.6        174.90
10         Understory Primary Care - Gainesville                1186        263.9        169.85
11      Understory Primary Care - Gainesville 24                 721        294.0        188.45
12           Understory Primary Care - Inverness                 237        278.5        245.69
13           Understory Primary Care - Lake City                 497        482.9        241.30
14        Understory Primary Care - Lake City 21                 120        483.3        243.51
--- end of block 2 ---
                                   practice_name  attributed_members  diabetic_members  a1c_pct  ci_low  ci_high  aco_pct         vs_aco  ed_per_1000  allowed_pmpm
0                            Pierce Primary Care                 198                41    100.0   100.0    100.0     92.8          above        363.6        174.90
1                  Green Cove Springs Pediatrics                 162                 3    100.0   100.0    100.0     92.8        small n        259.3         92.45
2         Understory Primary Care - Lake City 21                 120                19    100.0   100.0    100.0     92.8        small n        483.3        243.51
3                       Barnes Internal Medicine                  72                12    100.0   100.0    100.0     92.8        small n        347.2        358.39
4   Gainesville Pediatrics & Adolescent Medicine                 226                 2    100.0   100.0    100.0     92.8        small n        216.8         77.09
5           Understory Primary Care - Middleburg                 463                91     97.8    94.8    100.8     92.8          above        356.4        206.83
6                        Farrell Family Practice                 678               106     97.2    94.0    100.3     92.8          above        348.1        163.36
7            Understory Primary Care - Weirsdale                 195                32     96.9    90.8    102.9     92.8  not different        405.1        221.16
8           Understory Primary Care - Palatka 27                 125                30     96.7    90.2    103.1     92.8  not different        456.0        214.02
9          Understory Primary Care - Gainesville                1186               190     96.3    93.6     99.0     92.8          above        263.9        169.85
10                       Young Internal Medicine                 338                54     94.4    88.3    100.6     92.8  not different        301.8        314.90
11                         Baker Family Practice                 366                70     94.3    88.8     99.7     92.8  not different        366.1        211.60
12           Gainesville Community Health Center                2024               385     93.2    90.7     95.8     92.8  not different        426.4        214.53
13           Understory Primary Care - Lake City                 497                87     92.0    86.2     97.7     92.8  not different        482.9        241.30
14            Understory Primary Care - Ocala 15                 506                73     91.8    85.5     98.1     92.8  not different        306.3        198.24
--- end of block 3 ---
```
