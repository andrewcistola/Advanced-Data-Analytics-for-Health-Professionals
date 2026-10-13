# Expected results: lab02_querying_claims

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab02_querying_claims
====================================================================================================
   claims_2025  members_2025
0       129609         19574
      claim_id drg_code  length_of_stay  payer_type  total_allowed
0  C0000526090      616            17.0  Commercial       70283.54
1  C0000535990      470             2.0  Commercial       34838.79
2  C0000506080      871             6.0  Commercial       34635.98
3  C0000535676      247             4.0  Commercial       34435.11
4  C0000585146      871             6.0  Commercial       34168.55
5  C0000555812      470             2.0  Commercial       33513.75
6  C0000575333      871            15.0  Commercial       33198.39
7  C0000516196      470             1.0  Commercial       32945.04
8  C0000565638      871             9.0  Commercial       32931.86
9  C0000535646      871             3.0  Commercial       32883.07
--- end of block 1 ---
                        provider_name  claims     charges    allowed       paid  paid_to_charge
0  Understory Regional Medical Center   10294  27357199.0  8433542.0  6634680.0           0.243
--- end of block 2 ---
              payer_type  paid_claims  avg_days_to_pay  max_days
0           Medicaid FFS        12432             37.6       150
1  Medicaid Managed Care        63360             33.2       157
2            Marketplace        44189             30.2       145
3             Commercial       141996             23.4       114
4     Medicare Advantage       162410             19.9       107
5           Medicare FFS       144133             15.5        73
--- end of block 3 ---
```
