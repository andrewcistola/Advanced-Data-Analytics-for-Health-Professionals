# Expected results: lab08_coding_gaps

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab08_coding_gaps
====================================================================================================
3206 member-HCC pairs; recapture rate: 0.909
                                                    count      mean
hcc_label                                                          
Diabetes with Glycemic, Unspecified, or No Comp...    685  0.909489
Chronic Kidney Disease, Moderate (Stage 3, Exce...    416  0.908654
Heart Failure, Except End-Stage and Acute             307  0.990228
Chronic Obstructive Pulmonary Disease and Other...    307  0.980456
Specified Heart Arrhythmias                           302  0.963576
Chronic Kidney Disease, Moderate (Stage 3B)           214  0.943925
Morbid Obesity                                        206  0.859223
Major Depression, Moderate or Severe, without P...    173  0.924855
Dementia, Mild or Unspecified                         159  0.911950
Chronic Kidney Disease, Severe (Stage 4)              136  0.794118
--- end of block 1 ---
--- end of block 2 ---
Logistic AUC 0.575 | Tree AUC 0.581
Standardized logistic coefficients:
 had_awv              0.008
dual                 0.037
age                  0.106
specialist_visits    0.128
pcp_visits           0.388
dtype: float64
Tree importances:
 pcp_visits           0.570
specialist_visits    0.227
age                  0.169
had_awv              0.034
dual                 0.000
dtype: float64
--- end of block 3 ---
member_id  hcc                                                              hcc_label  p_recapture  pcp_visits  had_awv
 M0113528   38               Diabetes with Glycemic, Unspecified, or No Complications     0.807407           0        0
 M0118165   38               Diabetes with Glycemic, Unspecified, or No Complications     0.807407           3        0
 M0116649  327                               Chronic Kidney Disease, Severe (Stage 4)     0.807407           4        0
 M0119685  280 Chronic Obstructive Pulmonary Disease and Other Chronic Lung Disorders     0.807407           2        0
 M0119685  329                  Chronic Kidney Disease, Moderate (Stage 3, Except 3B)     0.807407           2        0
 M0112475  280 Chronic Obstructive Pulmonary Disease and Other Chronic Lung Disorders     0.807407           0        0
 M0124874   38               Diabetes with Glycemic, Unspecified, or No Complications     0.807407           0        0
 M0100554   48                                                         Morbid Obesity     0.807407           5        0
 M0100707  226                              Heart Failure, Except End-Stage and Acute     0.807407           3        0
 M0120883  280 Chronic Obstructive Pulmonary Disease and Other Chronic Lung Disorders     0.807407           4        0
 M0105305  280 Chronic Obstructive Pulmonary Disease and Other Chronic Lung Disorders     0.807407           3        0
 M0117488  329                  Chronic Kidney Disease, Moderate (Stage 3, Except 3B)     0.807407           4        0
 M0113801   38               Diabetes with Glycemic, Unspecified, or No Complications     0.807407           1        0
 M0120590  280 Chronic Obstructive Pulmonary Disease and Other Chronic Lung Disorders     0.807407           4        0
 M0120590   38               Diabetes with Glycemic, Unspecified, or No Complications     0.807407           4        0
2025 AUC: 0.629
Actual 2025 recapture among the 100 lowest-scored pairs: 0.8 vs. all pairs: 0.909
Actual 2025 recapture among the 200 lowest-scored pairs: 0.84 vs. all pairs: 0.909
--- end of block 4 ---
```
