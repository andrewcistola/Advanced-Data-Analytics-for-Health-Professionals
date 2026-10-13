# Expected results: lab11_high_risk_zips

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab11_high_risk_zips
====================================================================================================
18552 members; 2025 avoidable-event rate 0.264
--- end of block 1 ---
Test AUC  logistic: 0.696   neural network: 0.688
--- end of block 2 ---
          members  observed  expected  oe_ratio  excess            city    county  area_deprivation_index  pcp_per_10k  pct_no_vehicle  miles_to_nearest_hospital
zip_code                                                                                                                                                         
32003         288       137     94.15      1.46   42.85  Fleming Island      Clay                      90          2.2             9.6                       30.3
32064         280       114     77.35      1.47   36.65        Live Oak  Suwannee                      55          8.2             6.6                       21.5
32025         242       102     67.96      1.50   34.04       Lake City  Columbia                      54          4.8             6.1                        7.7
32053         111        69     36.84      1.87   32.16        Jennings  Hamilton                      89          1.1            12.9                       35.9
32071         129        75     44.37      1.69   30.63         O Brien  Suwannee                     100          0.8            10.5                       24.3
34442         112        64     35.19      1.82   28.81        Hernando    Citrus                      73          1.8             8.0                       22.8
34472         344       134    108.66      1.23   25.34           Ocala    Marion                      94          7.5            10.3                        7.7
34491         194        77     54.93      1.40   22.07     Summerfield    Marion                      60          7.4             5.1                       11.8
32177         308       112     90.12      1.24   21.88         Palatka    Putnam                      90          4.8             8.3                        0.0
34471         580       188    167.26      1.12   20.74           Ocala    Marion                      77         10.1            10.0                        0.0
--- end of block 3 ---
          members  observed  expected  oe_after_zip_features
zip_code                                                    
32064         280       114     66.58                   1.71
32025         242       102     60.62                   1.68
34491         194        77     46.10                   1.67
34442         112        64     42.92                   1.49
34453         203        44     31.80                   1.38
32053         111        69     59.18                   1.17
34474         336        63     54.62                   1.15
32065         238        52     46.93                   1.11
--- end of block 4 ---
```
