# Expected results: lab04_prior_authorization

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab04_prior_authorization
====================================================================================================
      yr request_type submission_channel  requests
0   2020      Medical                Fax         2
1   2020      Medical       Payer Portal         1
2   2021      Medical                Fax       438
3   2021      Medical       Payer Portal       242
4   2021      Medical              Phone        76
5   2021      Medical                ePA         8
6   2021     Pharmacy                Fax       155
7   2021     Pharmacy              Phone        46
8   2021     Pharmacy                ePA       102
9   2022      Medical                Fax       379
10  2022      Medical       Payer Portal       320
11  2022      Medical              Phone        71
12  2022      Medical                ePA        48
13  2022     Pharmacy                Fax       220
14  2022     Pharmacy              Phone        48
     yr request_type  requests  epa_share_pct
0  2021      Medical       764            1.0
1  2022      Medical       818            5.9
2  2023      Medical       794           13.7
3  2024      Medical       860           20.9
4  2025      Medical       815           23.4
5  2021     Pharmacy       303           33.7
6  2022     Pharmacy       486           44.9
7  2023     Pharmacy       627           62.7
8  2024     Pharmacy       786           73.8
9  2025     Pharmacy       921           78.6
--- end of block 1 ---
  submission_channel  requests  median_hours  approval_pct
0                ePA      2553           2.4          93.1
1              Phone       541          21.0          85.2
2       Payer Portal      1645          26.5          85.3
3                Fax      2438          75.7          82.3
  request_type submission_channel  requests  median_hours  approval_pct
0      Medical                ePA       536           2.3          94.4
1      Medical              Phone       318          21.3          86.2
2      Medical       Payer Portal      1645          26.5          85.3
3      Medical                Fax      1555          75.9          81.7
4     Pharmacy                ePA      2017           2.4          92.8
5     Pharmacy              Phone       223          20.2          83.9
6     Pharmacy                Fax       883          74.9          83.4
--- end of block 2 ---
                  practice_name           specialty  requests_2025  epa_share_pct
0      Gainesville Lung & Sleep         Pulmonology            397            7.1
1   Understory Heart & Vascular          Cardiology            139           12.9
2  Gainesville Heart & Vascular          Cardiology            133           15.8
3      Jones Medical Associates   Internal Medicine             20           25.0
4       Farrell Family Practice  Nurse Practitioner             14           35.7
--- end of block 3 ---
```
