# rdt1030: owner-shared Reddit post (15-min ORB + FVG, IRL->ERL, "when not to trade") -> 6 setup families

Educational only — not financial advice.

137 configs scored (108 pre-declared + 29 dated rework rows), **0 pass** (BAR90 t >= 3.52 at N 2,137; WF >= 54%; > 0 on
TRAIN and VALID; >= 3 trades/session). Harness parity exact (CWT14 p05 -0.0677 / -0.0675). Locked block and HOLD never loaded.
Design: DESIGN.md. Per family: F1..F6/ (PLAN, NOTES, results.csv, scripts). Backlog: reddit-1030-orbfvg-f1..f6 (failed).

| family | best row | TRAIN / VALID | t | trades/session |
|---|---|---|---|---|
| F1 ORB15 + FVG break (as posted) | short, skip costs > 5% R | -0.051 / -0.004 | -1.15 | 66 |
| F2 + chop gates | long, active SPY prior day + low cost | +0.023 / +0.060 | +0.86 | 30 |
| F3 5-min ORB, BE, 2 tries, 2R | short, 2R, low cost | -0.046 / +0.021 | -0.49 | 54 |
| F4 IRL->ERL sweep + 15-min FVG | OR-low sweep long, QQQ up | +0.013 / +0.114 | +1.11 | 16 |
| F5 + one indicator | ORB15 short + order flow + low cost | -0.033 / +0.003 | -0.77 | 49 |
| F6 index-native (QQQ/SPY, 3x ETFs) | SPY PDH sweep short | t 1.17 best | | <= 0.6 |

Why: the post's entry has no gross edge on liquid stocks (gross ~0.000R; costs ~11% of R at FVG-candle stops vs 1-2% on NQ).
Every family splits by market direction (longs win on up days, lose ~0.2-0.3R on down days; shorts the mirror), the same pattern as
the pdl1030 swarms. The "don't trade chop" gates help a little (F2, F4 rework rows) but not near the bar.
