# Expected results: lab10_diabetes_complications

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab10_diabetes_complications
====================================================================================================
2122 members; complication rate 0.205 ; hypoglycemia rate 0.012
--- end of block 1 ---
0 missing values
--- end of block 2 ---
Test AUC: 0.625
     feature  importance     sd
         adi      0.0964 0.0315
         pdc      0.0125 0.0096
         age      0.0053 0.0049
sulfonylurea      0.0042 0.0025
  gap_months      0.0029 0.0052
     insulin      0.0013 0.0025
   ed_visits      0.0000 0.0000
  pcp_visits     -0.0005 0.0041
         ckd     -0.0090 0.0043
--- end of block 3 ---
                          members  hypoglycemia_rate  any_complication_rate
age_75_plus sulfonylurea                                                   
0           0                1086              0.000                  0.209
            1                 474              0.004                  0.179
1           0                 363              0.003                  0.182
            1                 199              0.116                  0.286
--- end of block 4 ---
```
