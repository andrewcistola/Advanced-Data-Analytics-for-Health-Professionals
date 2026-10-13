# Expected results: lab06_hedis

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab06_hedis
====================================================================================================
                          plan_name  members
0   Longleaf Medicare Advantage HMO     1260
1     Osprey Medicare Advantage HMO     1146
2   Longleaf Medicare Advantage PPO      775
3  Osprey Dual Complete (HMO D-SNP)      341
--- end of block 1 ---
                          plan_name  denominator  numerator  bcs_rate
0     Osprey Medicare Advantage HMO          282      236.0      83.7
1   Longleaf Medicare Advantage PPO          184      147.0      79.9
2   Longleaf Medicare Advantage HMO          284      223.0      78.5
3  Osprey Dual Complete (HMO D-SNP)           98       76.0      77.6
--- end of block 2 ---
                          plan_name  denominator  a1c_test_rate  eye_exam_rate
0   Longleaf Medicare Advantage HMO          184           87.5           41.8
1   Longleaf Medicare Advantage PPO          105           91.4           50.5
2  Osprey Dual Complete (HMO D-SNP)           74           83.8           43.2
3     Osprey Medicare Advantage HMO          162           80.9           44.4
--- end of block 3 ---
```
