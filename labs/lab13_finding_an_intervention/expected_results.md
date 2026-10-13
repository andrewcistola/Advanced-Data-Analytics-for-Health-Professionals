# Expected results: lab13_finding_an_intervention

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab13_finding_an_intervention
====================================================================================================
17398 members; top-5% cost threshold $ 8308
          logistic  random_forest  gradient_boosting
mean_auc     0.780          0.787              0.780
sd           0.011          0.009              0.007
--- end of block 1 ---
Best model: random_forest
--- end of block 2 ---
 target  members  actual_2025_allowed  share_truly_high_cost  savings    cost    net
 top 1%      174              1806875                  0.322   271031  121800 149231
 top 5%      870              6307463                  0.257   946119  609000 337119
top 10%     1740             10086812                  0.202  1513022 1218000 295022
Program B: 223 members, net savings about $6,690
Program C: 1889 members in 5 zips, net savings about $-1,109,960
--- end of block 3 ---
```
