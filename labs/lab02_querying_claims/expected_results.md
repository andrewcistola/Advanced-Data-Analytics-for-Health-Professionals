# Expected results: lab02_querying_claims

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab02_querying_claims
====================================================================================================
   claims_2025  members_2025
0       130264         19700
      claim_id drg_code  length_of_stay  payer_type  total_allowed
0  C0000575319      616             5.0  Commercial       58444.22
1  C0000630009      871             3.0  Commercial       35921.68
2  C0000535572      470             2.0  Commercial       35465.65
3  C0000525535      470             3.0  Commercial       35357.10
4  C0000630110      470             2.0  Commercial       35002.65
5  C0000619045      470             3.0  Commercial       34464.15
6  C0000565037      247             3.0  Commercial       33802.06
7  C0000535661      617             2.0  Commercial       33786.58
8  C0000630114      470             2.0  Commercial       33365.92
9  C0000525509      470             2.0  Commercial       32769.82
--- end of block 1 ---
                        provider_name  claims     charges    allowed       paid  paid_to_charge
0  Understory Regional Medical Center   10542  27581044.0  8688109.0  6767455.0           0.245
--- end of block 2 ---
              payer_type  paid_claims  avg_days_to_pay  max_days
0           Medicaid FFS        12352             37.5       141
1  Medicaid Managed Care        64920             33.1       150
2            Marketplace        45701             30.2       132
3             Commercial       144594             23.4       105
4     Medicare Advantage       165719             20.0       104
5           Medicare FFS       144868             15.5        83
--- end of block 3 ---
```
