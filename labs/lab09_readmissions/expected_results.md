# Expected results: lab09_readmissions

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab09_readmissions
====================================================================================================
6161 index stays; overall 30-day readmission rate 0.168
--- end of block 1 ---
--- end of block 2 ---
enrolled             0       1
readmit_30d      0.132   0.167
age             61.916  69.412
n_chronic        2.274   3.468
chf              0.125   0.323
copd             0.151   0.281
prior_admits     0.336   0.543
length_of_stay   4.116   4.070
medicaid_dual    0.188   0.220
adi             64.915  72.311
--- end of block 3 ---
                Coef.  Std.Err.      z  P>|z|  [0.025  0.975]
Intercept      -4.065     0.488 -8.322  0.000  -5.023  -3.108
enrolled       -0.299     0.169 -1.766  0.077  -0.630   0.033
age             0.005     0.005  0.915  0.360  -0.006   0.015
n_chronic       0.232     0.057  4.034  0.000   0.119   0.344
chf             0.289     0.188  1.540  0.124  -0.079   0.658
copd            0.364     0.182  2.004  0.045   0.008   0.719
prior_admits   -0.032     0.080 -0.403  0.687  -0.190   0.125
length_of_stay -0.021     0.027 -0.783  0.433  -0.073   0.031
medicaid_dual   0.074     0.188  0.393  0.694  -0.295   0.443
adi             0.018     0.005  3.785  0.000   0.009   0.028
Adjusted odds ratio for TCP enrollment: 0.74 (95% CI 0.53-1.03)
--- end of block 4 ---
```
