# pdl1030c / ind2: does adding RSI(14) or order-flow rescue the two demoted PDL longs?

*Educational only — not financial advice.* Backtest only (open two-year history, costs in); nothing here is paper or live.

**Result: 0 of 14 pre-declared configurations pass. No row reaches t > 0.1, and no parent-exit row turns positive.**
All 14 configs were declared in PLAN.md before scoring; nothing was added afterwards. N = 121,635 + 5 x 14 = 121,705, BAR90 t >= 4.355.
TRAIN = 2024-10, 2025-03..12; VALID = 2026-01..03, 2026-07..09-15 (348 sessions). HOLD months and the locked block were never loaded.
Overlap with the 176 earlier pdl1030/pdl1030b rows: none (no earlier row used RSI(14), buyPressure or flow3). None skipped.

Parity is exact. p05 -0.0677 / -0.0675 (n 53,326, 153.2/session). p05-lowvol -0.0951 / -0.0948, TV -0.0950 (n 35,238, 101.3/session).
S3 matches swarm15: p05 -0.021 / -0.017, p05lv -0.028 / -0.027. p05 S3 + cost5 matches Q08: -0.0028 / -0.0084, 54.3/session.

## Every row (avg R after costs; t is day-clustered over TRAIN+VALID)
| id | rule | TRAIN | VALID | t | /sess | % parent kept | WF% | up-day | down-day | w/o best day |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | p05 + rsi <= 30 | -0.0619 | -0.0842 | -6.00 | 31.2 | 20% | 12 | +0.002 | -0.125 | -0.072 |
| A2 | p05 + rsi <= 40 | -0.0655 | -0.0704 | -7.69 | 77.5 | 51% | 12 | -0.001 | -0.122 | -0.069 |
| A3 | p05 + rsi > 50 | -0.0738 | -0.0516 | -5.81 | 27.8 | 18% | 6 | -0.009 | -0.138 | -0.070 |
| A4 | p05 + buyPressure > 0 | -0.0609 | -0.0694 | -7.97 | 60.4 | 39% | 6 | -0.010 | -0.122 | -0.067 |
| A5 | p05 + flow3 > 0 | -0.0653 | -0.0745 | -8.60 | 80.0 | 52% | 6 | -0.007 | -0.132 | -0.071 |
| A6 | p05 + buyPressure < -0.25 | -0.0763 | -0.0647 | -7.84 | 49.0 | 32% | 6 | -0.016 | -0.120 | -0.075 |
| A7 | p05 S3 + cost5 + buyPressure > 0 | +0.0050 | -0.0052 | +0.04 | 21.8 | 14% | 41 | +0.032 | -0.035 | -0.002 |
| B1 | p05lv + rsi <= 30 | -0.0806 | -0.1246 | -5.39 | 16.7 | 16% | 12 | +0.017 | -0.193 | -0.102 |
| B2 | p05lv + rsi <= 40 | -0.0875 | -0.1001 | -6.74 | 45.4 | 45% | 12 | +0.014 | -0.185 | -0.095 |
| B3 | p05lv + rsi > 50 | -0.1103 | -0.0746 | -6.00 | 22.0 | 22% | 6 | -0.002 | -0.212 | -0.102 |
| B4 | p05lv + buyPressure > 0 | -0.0865 | -0.0877 | -6.97 | 42.4 | 42% | 6 | +0.006 | -0.184 | -0.090 |
| B5 | p05lv + flow3 > 0 | -0.0979 | -0.0965 | -7.80 | 56.3 | 56% | 6 | +0.007 | -0.202 | -0.100 |
| B6 | p05lv + buyPressure < -0.25 | -0.1079 | -0.0990 | -7.64 | 30.7 | 30% | 12 | -0.026 | -0.176 | -0.108 |
| B7 | p05lv S3 + cost5 + buyPressure > 0 | -0.0058 | -0.0203 | -1.48 | 15.3 | 15% | 41 | +0.045 | -0.077 | -0.016 |

A7/B7 used the pre-declared selection rule: the highest TRAIN avg R among the parent-exit rows that keep at least 25 trades per session.
That picked buyPressure > 0 for both setups. B1 was excluded at 16.7/session.

## One-big-day / top-5-session check
Only A7 has total R > 0, and that total is about zero (+1.5R over 7,595 trades). The best session alone is 8.1x the total and the top 5 sessions are 21x.
Without its best day, A7 is -0.002; without its top 5, it is -0.005. A7's record is made of a handful of up days, with nothing underneath them.
Every other row loses in total, so a share is not defined. Their avg R without the best day (and without the top 5) is a little worse than the row's avg.

## What it means
- Neither indicator separates winners from losers on this signal. Across all 12 parent-exit rows, avg R moves by at most ~0.016R
  in either direction (A3 VALID -0.052 vs parent -0.068, but TRAIN is worse at -0.074). That is inside the noise, and the sign flips between splits.
- Oversold RSI (the live long use) helps slightly on up days but makes down days worse. Strong RSI is the reverse. Neither helps net.
- Buy-side flow (buyPressure > 0, flow3 > 0) is the "right" direction but only ~0.003-0.008R better than the parent. Sell-side flow is slightly worse, as expected.
- The down-session beta loss (-0.12 to -0.21R) is untouched by every indicator. The why/NOTES finding stands: no gross edge, and the loss is market beta plus costs.
- On the S3 + cost5 base, buyPressure > 0 brings p05 to about 0 (+0.0002 TV, t 0.04) at 21.8/session. That is below the 25/session floor
  and not better than Q08 on VALID. The lowvol version stays negative.

Files: PLAN.md, build.py, score.py, score_out.txt, results.csv. Cache: scratchpad pdl1030c/ind2/cache (13 MB).
Re-run: `python research/bdi/pdl1030c/ind2/build.py && python research/bdi/pdl1030c/ind2/score.py`.

*Educational only — not financial advice.*
