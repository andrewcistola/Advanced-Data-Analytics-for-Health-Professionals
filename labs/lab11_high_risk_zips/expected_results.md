# Expected results: lab11_high_risk_zips

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab11_high_risk_zips
====================================================================================================
18552 members; 2025 avoidable-event rate 0.264
--- end of block 1 ---
Test AUC  logistic: 0.714   neural network: 0.711
--- end of block 2 ---
          members  observed  expected  oe_ratio  excess            city    county  area_deprivation_index  pcp_per_10k  pct_no_vehicle  miles_to_nearest_hospital
zip_code                                                                                                                                                         
34472         344       161    109.44      1.47   51.56           Ocala    Marion                      94          7.5            10.3                        7.7
32025         242       116     70.79      1.64   45.21       Lake City  Columbia                      54          4.8             6.1                        7.7
32064         280       114     75.74      1.51   38.26        Live Oak  Suwannee                      55          8.2             6.6                       21.5
34491         194        89     55.31      1.61   33.69     Summerfield    Marion                      60          7.4             5.1                       11.8
32003         288       127     97.12      1.31   29.88  Fleming Island      Clay                      90          2.2             9.6                       30.3
34442         112        65     35.94      1.81   29.06        Hernando    Citrus                      73          1.8             8.0                       22.8
32071         129        70     46.06      1.52   23.94         O Brien  Suwannee                     100          0.8            10.5                       24.3
32053         111        60     38.56      1.56   21.44        Jennings  Hamilton                      89          1.1            12.9                       35.9
34471         580       185    164.25      1.13   20.75           Ocala    Marion                      77         10.1            10.0                        0.0
32091         241        87     74.01      1.18   12.99          Starke  Bradford                      83          4.7             9.9                       28.8
--- end of block 3 ---
          members  observed  expected  oe_after_zip_features
zip_code                                                    
34491         194        89     49.80                   1.79
32025         242       116     65.12                   1.78
32064         280       114     65.87                   1.73
34442         112        65     42.57                   1.53
34472         344       161    136.34                   1.18
34480         252        45     39.31                   1.14
32060         165        48     42.31                   1.13
32615         241        46     40.74                   1.13
--- end of block 4 ---
```
