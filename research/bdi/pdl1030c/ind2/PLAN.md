# pdl1030c / ind2: add ONE live-setup indicator (RSI(14) or order-flow) to the two demoted PDL longs (pre-declaration)

*Educational only — not financial advice.*

Written 2026-10-30 14:23 UTC, before any configuration is scored. Research only: no config/, mcf/, ledger or backlog writes,
nothing committed. Lineage: CWT14 Failed Prior-Day-Low Break Longs. N_prior = 121,635 (pdl1030 + pdl1030b).

## Parents (demoted to the Graveyard 2026-10-30)
- **p05** = CWT14-failbrk-pdl-p05-long: S6.b3_any, PD level, side long, 0.05 ATR, no volume cap, exits t05 + scale 0.25R (so=0.25).
  Parity target TRAIN -0.0677 / VALID -0.0675 (n 53,326; 153.2/session).
- **p05lv** = CWT14-failbrk-pdl-p05-lowvol-long: same with reclaim-bar volumeRatio <= 1, so=0.0.
  Parity target TRAIN+VALID -0.0950 (n 35,238; 101.3/session).

## Overlap with earlier swarms (176 configs in pdl1030 / pdl1030b)
No earlier PDL row used RSI(14), buyPressure, flow3 or flow9prev (grep of all pdl1030*/ PLAN/NOTES/results). why/feat.py
carried rsi5 as a descriptive column only (0 configs). So no row below repeats an earlier row; none skipped.

## Indicators (all are the frame columns at the signal (reclaim) bar's close, so known at the signal-bar close)
- `rsi` = RSI(14) on 1-min bars.
- `buyPressure` = 19-bar signed-volume share; `flow3` = 3-bar version.

## Configurations (14, all scored, all reported)
Parent exits (each setup's own exits), for s in {p05, p05lv}:
| id (p05 / p05lv) | added condition | source (how live setups use it) |
|---|---|---|
| A1 / B1 | rsi <= 30 | oversold: NS4, NS5, ST7, ST7Q |
| A2 / B2 | rsi <= 40 | second live threshold: the 40 line (NS1, LD1, LD7) |
| A3 / B3 | rsi > 50 | opposite direction: "strong" (ST4, LD4) |
| A4 / B4 | buyPressure > 0 | buy-side confirmation on longs (ST7, ST7Q, LD3, LD5) |
| A5 / B5 | flow3 > 0 | 3-bar buy-side confirmation (ST8) |
| A6 / B6 | buyPressure < -0.25 | opposite direction: flow-sell (MF2-MF5 family) |

On the "S3 stop x3 same $ + cost <= 5% of R" base (pdl1030 symbol-quality Q08 construction):
| A7 | p05 S3 + cost5 + the best A1..A6 condition |
| B7 | p05lv S3 + cost5 + the best B1..B6 condition |

Selection rule for A7/B7 (fixed now): among the six parent-exit rows of that setup, the one with the highest **TRAIN** avg R
among rows keeping >= 25 trades/session; if none keeps 25/session, the highest TRAIN avg R overall. VALID is not used to select.
S3 = stop 3x (0.75 ATR) at the same $ risk, targets kept, r in the new R (swarm15). cost5 = round-trip cost estimate <= 5% of R1 = 0.25 ATR.
The no-indicator p05lv S3 + cost5 reference is not scored (keeps the 14-config cap); p05 S3 + cost5 = Q08 (-0.0028 / -0.0084, 54.3/session).
Rows with a missing indicator value do not trade.

## Harness
pdl1030/symbol-quality/build.py logic (kernel S6.b3_any, adv20 >= 95M, signal 09:50-15:00, first signal per symbol-day, top5_1028 `sim`,
costs in: 1c + 1 bp per side x time-of-day multiplier, +2c stop exits, x3 extended tier). TRAIN <= 2025-12 (2024-10, 2025-03..12);
VALID 2026-01..03 + 2026-07..09-15. HOLD months (2026-04..06, 2026-09-16..10-07) and the locked block 2024-11..2025-02 never loaded.

## Bar (rule 22, BAR90)
N = 121,635 + 5 x 14 = 121,705 -> t_TV >= 0.9 x sqrt(2 ln N) = 4.355. Walk-forward >= 54% months positive; avg R > 0 on TRAIN and on VALID;
beats its parent on both splits; >= 25 trades/session.
Reported per row: TRAIN / VALID avg R, day-clustered t, trades/session, % of parent trades kept, WF%, up/down-day R,
avg R w/o best day, best-day share, and share of total R in the top 5 sessions (owner's one-big-day concern).
