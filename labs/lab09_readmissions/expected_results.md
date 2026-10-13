# Expected results: lab09_readmissions

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab09_readmissions
====================================================================================================
6516 index stays; overall 30-day readmission rate 0.183
--- end of block 1 ---
--- end of block 2 ---
enrolled             0       1
readmit_30d      0.153   0.149
age             63.699  69.222
n_chronic        2.414   3.484
chf              0.175   0.323
copd             0.186   0.307
prior_admits     0.309   0.658
length_of_stay   4.164   3.838
medicaid_dual    0.185   0.231
adi             64.537  71.826
--- end of block 3 ---
                Coef.  Std.Err.      z  P>|z|  [0.025  0.975]
Intercept      -3.677     0.469 -7.837  0.000  -4.597  -2.757
enrolled       -0.631     0.160 -3.954  0.000  -0.943  -0.318
age            -0.003     0.005 -0.640  0.522  -0.014   0.007
n_chronic       0.310     0.058  5.364  0.000   0.196   0.423
chf             0.515     0.172  2.994  0.003   0.178   0.852
copd            0.209     0.169  1.236  0.217  -0.123   0.542
prior_admits    0.091     0.067  1.343  0.179  -0.042   0.223
length_of_stay  0.028     0.025  1.103  0.270  -0.022   0.078
medicaid_dual   0.194     0.178  1.086  0.278  -0.156   0.543
adi             0.014     0.004  3.245  0.001   0.006   0.023
Adjusted odds ratio for TCP enrollment: 0.53 (95% CI 0.39-0.73)
--- end of block 4 ---
```
