# Expected results: lab10_diabetes_complications

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab10_diabetes_complications
====================================================================================================
2071 members; complication rate 0.208 ; hypoglycemia rate 0.015
--- end of block 1 ---
0 missing values
--- end of block 2 ---
Test AUC: 0.586
     feature  importance     sd
         adi      0.0534 0.0273
         pdc      0.0112 0.0105
sulfonylurea      0.0064 0.0028
         age      0.0051 0.0114
     insulin      0.0044 0.0040
  gap_months      0.0024 0.0040
  pcp_visits      0.0014 0.0058
   ed_visits      0.0000 0.0000
         ckd     -0.0027 0.0041
--- end of block 3 ---
                          members  hypoglycemia_rate  any_complication_rate
age_75_plus sulfonylurea                                                   
0           0                1060              0.000                  0.207
            1                 455              0.011                  0.176
1           0                 354              0.006                  0.218
            1                 202              0.119                  0.267
--- end of block 4 ---
```
