# Expected results: lab13_finding_an_intervention

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab13_finding_an_intervention
====================================================================================================
17398 members; top-5% cost threshold $ 8599
          logistic  random_forest  gradient_boosting
mean_auc     0.783          0.785              0.782
sd           0.011          0.012              0.010
--- end of block 1 ---
Best model: random_forest
--- end of block 2 ---
 target  members  actual_2025_allowed  share_truly_high_cost  savings    cost    net
 top 1%      174              1795593                  0.379   269339  121800 147539
 top 5%      870              6363118                  0.261   954468  609000 345468
top 10%     1740             10184218                  0.207  1527633 1218000 309633
Program B: 222 members, net savings about $6,660
Program C: 1859 members in 5 zips, net savings about $-1,116,800
--- end of block 3 ---
```
