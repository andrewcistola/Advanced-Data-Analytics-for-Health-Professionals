# Expected results: lab07_provider_performance

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab07_provider_performance
====================================================================================================
                                   practice_name  attributed_members  ed_per_1000  allowed_pmpm
0                          Baker Family Practice                 389        421.6       2644.62
1                       Barnes Internal Medicine                  80        400.0       4238.68
2                        Chapman Family Practice                 470        366.0       2433.76
3                        Farrell Family Practice                 654        336.4       1961.92
4            Gainesville Community Health Center                1994        424.8       2739.06
5   Gainesville Pediatrics & Adolescent Medicine                 261        291.2        880.52
6                  Green Cove Springs Pediatrics                 162        290.1        824.11
7                  Ocala Community Health Center                 687        464.3       2327.65
8         Ocala Pediatrics & Adolescent Medicine                 265        207.5        834.78
9                            Pierce Primary Care                 199        361.8       2333.60
10         Understory Primary Care - Gainesville                1161        324.7       2359.27
11      Understory Primary Care - Gainesville 24                 727        316.4       2406.63
12           Understory Primary Care - Inverness                 243        321.0       1964.13
13           Understory Primary Care - Lake City                 469        467.0       2825.33
14        Understory Primary Care - Lake City 21                 115        608.7       2578.23
--- end of block 1 ---
                                   practice_name  attributed_members  ed_per_1000  allowed_pmpm
0                          Baker Family Practice                 389        390.7        207.10
1                       Barnes Internal Medicine                  80        362.5        328.62
2                        Chapman Family Practice                 470        338.3        190.67
3                        Farrell Family Practice                 654        310.4        158.78
4            Gainesville Community Health Center                1994        398.7        214.69
5   Gainesville Pediatrics & Adolescent Medicine                 261        268.2         75.76
6                  Green Cove Springs Pediatrics                 162        277.8         71.47
7                  Ocala Community Health Center                 687        433.8        187.48
8         Ocala Pediatrics & Adolescent Medicine                 265        188.7         70.53
9                            Pierce Primary Care                 199        331.7        178.70
10         Understory Primary Care - Gainesville                1161        298.9        189.75
11      Understory Primary Care - Gainesville 24                 727        290.2        197.23
12           Understory Primary Care - Inverness                 243        284.0        150.89
13           Understory Primary Care - Lake City                 469        439.2        228.20
14        Understory Primary Care - Lake City 21                 115        539.1        195.47
--- end of block 2 ---
                             practice_name  attributed_members  diabetic_members  a1c_pct  ci_low  ci_high  aco_pct         vs_aco  ed_per_1000  allowed_pmpm
0     Understory Primary Care - Palatka 27                 134                29    100.0   100.0    100.0     92.5        small n        477.6        212.12
1            Green Cove Springs Pediatrics                 162                 4    100.0   100.0    100.0     92.5        small n        277.8         71.47
2   Ocala Pediatrics & Adolescent Medicine                 265                 3    100.0   100.0    100.0     92.5        small n        188.7         70.53
3     Understory Primary Care - Middleburg                 462                84     96.4    92.5    100.4     92.5  not different        342.0        186.05
4                  Young Internal Medicine                 354                46     95.7    89.8    101.5     92.5  not different        226.0        309.26
5      Understory Primary Care - Lake City                 469                85     95.3    90.8     99.8     92.5  not different        439.2        228.20
6    Understory Primary Care - Gainesville                1161               177     94.4    90.9     97.8     92.5  not different        298.9        189.75
7       Understory Primary Care - Ocala 12                 355                63     93.7    87.6     99.7     92.5  not different        309.9        194.73
8      Gainesville Community Health Center                1994               373     93.6    91.1     96.1     92.5  not different        398.7        214.69
9      Understory Primary Care - Weirsdale                 181                31     93.5    84.9    102.2     92.5  not different        469.6        204.98
10           Ocala Community Health Center                 687               124     93.5    89.2     97.9     92.5  not different        433.8        187.48
11     Understory Primary Care - Inverness                 243                39     92.3    83.9    100.7     92.5  not different        284.0        150.89
12                Barnes Internal Medicine                  80                13     92.3    77.8    106.8     92.5        small n        362.5        328.62
13                 Farrell Family Practice                 654               100     92.0    86.7     97.3     92.5  not different        310.4        158.78
14                     Pierce Primary Care                 199                36     91.7    82.6    100.7     92.5  not different        331.7        178.70
--- end of block 3 ---
```
