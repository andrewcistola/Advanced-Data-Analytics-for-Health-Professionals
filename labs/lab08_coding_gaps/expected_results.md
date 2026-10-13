# Expected results: lab08_coding_gaps

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab08_coding_gaps
====================================================================================================
3016 member-HCC pairs; recapture rate: 0.911
                                                    count      mean
hcc_label                                                          
Diabetes with Glycemic, Unspecified, or No Comp...    672  0.894345
Chronic Kidney Disease, Moderate (Stage 3, Exce...    380  0.892105
Heart Failure, Except End-Stage and Acute             311  1.000000
Chronic Obstructive Pulmonary Disease and Other...    301  0.950166
Specified Heart Arrhythmias                           300  0.933333
Chronic Kidney Disease, Moderate (Stage 3B)           212  0.919811
Morbid Obesity                                        178  0.853933
Major Depression, Moderate or Severe, without P...    168  0.928571
Dementia, Mild or Unspecified                         141  0.829787
Chronic Kidney Disease, Severe (Stage 4)              135  0.814815
--- end of block 1 ---
--- end of block 2 ---
Logistic AUC 0.699 | Tree AUC 0.605
Standardized logistic coefficients (most negative = most likely to be missed):
 hcc_327   -0.287
hcc_38    -0.262
hcc_127   -0.262
hcc_48    -0.219
hcc_329   -0.216
hcc_328   -0.158
hcc_326   -0.075
hcc_155   -0.022
dtype: float64
Tree importances:
 specialist_visits    0.382
had_awv              0.211
hcc_38               0.138
age                  0.126
pcp_visits           0.103
hcc_226              0.028
hcc_329              0.011
dual                 0.000
dtype: float64
--- end of block 3 ---
member_id  hcc                                hcc_label  p_recapture  pcp_visits  had_awv
 M0102306  127            Dementia, Mild or Unspecified     0.579237           0        0
 M0115740  127            Dementia, Mild or Unspecified     0.590076           0        0
 M0104006  327 Chronic Kidney Disease, Severe (Stage 4)     0.591718           0        0
 M0104060  327 Chronic Kidney Disease, Severe (Stage 4)     0.597780           1        0
 M0110665  327 Chronic Kidney Disease, Severe (Stage 4)     0.604044           1        0
 M0117089  327 Chronic Kidney Disease, Severe (Stage 4)     0.610273           1        0
 M0102438  327 Chronic Kidney Disease, Severe (Stage 4)     0.612341           1        0
 M0112232  327 Chronic Kidney Disease, Severe (Stage 4)     0.614668           1        0
 M0105818  127            Dementia, Mild or Unspecified     0.614859           1        0
 M0106526  327 Chronic Kidney Disease, Severe (Stage 4)     0.623142           1        0
 M0115674  127            Dementia, Mild or Unspecified     0.629185           1        0
 M0115340  327 Chronic Kidney Disease, Severe (Stage 4)     0.631026           1        0
 M0118804  327 Chronic Kidney Disease, Severe (Stage 4)     0.634848           2        0
 M0105344  127            Dementia, Mild or Unspecified     0.637272           1        0
 M0124715  127            Dementia, Mild or Unspecified     0.639282           1        0
2025 AUC: 0.704
Actual 2025 recapture among the 100 lowest-scored pairs: 0.78 vs. all pairs: 0.905
Actual 2025 recapture among the 200 lowest-scored pairs: 0.77 vs. all pairs: 0.905
--- end of block 4 ---
```
