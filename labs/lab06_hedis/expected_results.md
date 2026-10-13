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
0   Longleaf Medicare Advantage PPO          184      154.0      83.7
1  Osprey Dual Complete (HMO D-SNP)           98       81.0      82.7
2   Longleaf Medicare Advantage HMO          284      230.0      81.0
3     Osprey Medicare Advantage HMO          282      221.0      78.4
--- end of block 2 ---
                          plan_name  denominator  a1c_test_rate  eye_exam_rate
0   Longleaf Medicare Advantage HMO          189           85.7           42.9
1   Longleaf Medicare Advantage PPO          102           93.1           43.1
2  Osprey Dual Complete (HMO D-SNP)           73           86.3           37.0
3     Osprey Medicare Advantage HMO          155           82.6           42.6
--- end of block 3 ---
```
