# Expected results: lab04_prior_authorization

Output of every code block in `solution.md`, run against the default database build (`python generate.py`, seed 42). Regenerate with `python labs/tools/run_solutions.py <db> --write`.

```text
====================================================================================================
lab04_prior_authorization
====================================================================================================
      yr request_type submission_channel  requests
0   2020      Medical                Fax         1
1   2020      Medical       Payer Portal         2
2   2021      Medical                Fax       408
3   2021      Medical       Payer Portal       268
4   2021      Medical              Phone        61
5   2021      Medical                ePA        16
6   2021     Pharmacy                Fax       178
7   2021     Pharmacy              Phone        37
8   2021     Pharmacy                ePA        86
9   2022      Medical                Fax       431
10  2022      Medical       Payer Portal       319
11  2022      Medical              Phone        70
12  2022      Medical                ePA        34
13  2022     Pharmacy                Fax       218
14  2022     Pharmacy              Phone        48
     yr request_type  requests  epa_share_pct
0  2021      Medical       753            2.1
1  2022      Medical       854            4.0
2  2023      Medical       809           12.9
3  2024      Medical       834           20.7
4  2025      Medical       814           22.0
5  2021     Pharmacy       301           28.6
6  2022     Pharmacy       485           45.2
7  2023     Pharmacy       632           63.8
8  2024     Pharmacy       772           79.5
9  2025     Pharmacy       916           77.9
--- end of block 1 ---
  submission_channel  requests  median_hours  approval_pct
0                ePA      2542           2.4          93.2
1              Phone       524          22.3          85.1
2       Payer Portal      1663          26.8          85.6
3                Fax      2444          76.7          82.2
  request_type submission_channel  requests  median_hours  approval_pct
0      Medical                ePA       506           3.0          92.7
1      Medical              Phone       310          21.6          85.5
2      Medical       Payer Portal      1663          26.8          85.6
3      Medical                Fax      1588          78.2          82.1
4     Pharmacy                ePA      2036           2.2          93.3
5     Pharmacy              Phone       214          22.7          84.6
6     Pharmacy                Fax       856          73.8          82.4
--- end of block 2 ---
                   practice_name          specialty  requests_2025  epa_share_pct
0       Gainesville Lung & Sleep        Pulmonology            388            4.9
1    Understory Heart & Vascular         Cardiology            120           12.5
2   Gainesville Heart & Vascular         Cardiology            154           20.1
3  Ocala Community Health Center  Internal Medicine             23           34.8
4       Jones Medical Associates  Internal Medicine             22           45.5
--- end of block 3 ---
```
