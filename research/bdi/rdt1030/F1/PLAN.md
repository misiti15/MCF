# rdt1030 / F1 orb15-fvg-break: pre-declaration

*Educational only — not financial advice.*

Written 2026-10-30, before any configuration is scored. No outcome column has been read. Research only: no repo, config/,
mcf/, ledger or backlog writes, and nothing is committed.

Source: the owner's Reddit post of 2026-10-30, idea (1) "15-min ORB + FVG". The design is in `../DESIGN.md` (sections 0 and F1),
and this table is copied from it unchanged.

## Rule (F1-A, as written)
- **OR15:** ORH and ORL are the max high and min low of the 0935, 0940 and 0945 head rows. All three rows must be present,
  and the width must be at least 0.05 ATR_d.
- **Fresh break:** the first row today, with tod >= 0950, whose close is above ORH (long) or below ORL (short). Only that
  break counts. If it does not produce an FVG within the allowance, that side is done for the day.
- **Signal at row i, long:**
  - A bullish FVG completes at row i. Rows i-2, i-1 and i are consecutive 5-min rows.
  - The gap passes `low[i] - high[i-2] >= g × ATR_d` (g = 0.05) and is at least $0.02.
  - The break is at row i-1 or at row i, and `close[i] > ORH`.
  - The signal row is between 0955 and 1100. Only the first signal per symbol-day per side is taken.
- **Short:** the exact mirror below ORL.
- **Entry:** `close[i]`. **Stop:** `low[i-2]` (long) or `high[i-2]` (short), with no buffer.
- **Risk guard:** 0.03 <= R/ATR_d <= 1.0. A signal that fails the guard is skipped, and that side is done for the day.
- **Target:** 2R if R <= 0.085 ATR_d, else 1R. Flat at 15:55.
- **Universe:** adv20 >= $95M and atr_d > 0 on the signal row.

## Configurations (18 counted: 9 rows × long and short)
| row | change from F1-A | plain-English name |
|---|---|---|
| F1-A | as written | 15-min Opening Range Break with Gap (as posted) |
| F1-B | FVG g = 0.02 | ... with a small gap allowed |
| F1-C | FVG g = 0.10 | ... with a big gap required |
| F1-D | 2R switch at R <= 0.20 ATR_d | ... with 2R on the tighter third of stops |
| F1-E | always 1R | ... with a fixed 1R target |
| F1-F | always 2R | ... with a fixed 2R target |
| F1-G | round-trip cost <= 10% of R | ... skipped when costs exceed 10% of risk |
| F1-H | FVG may complete up to 3 rows after the break, with every close since the break beyond the level | ... with a late gap allowed |
| F1-I | signal window to 1500 | ... with an all-day window |

## Harness
- **Frames and splits:** `scan_1019.build_paths` 5-min frames with head rows (0935-0945) and tail rows to 1555. The `_cut`
  monkeypatches and asserts are copied from pdl1030/combo/build.py.
  - TRAIN is 2024-10 and 2025-03..12.
  - VALID is 2026-01..03 and 2026-07..2026-09-15.
  - The locked block and the HOLD months are never loaded.
- **Simulator:** a numba copy of the top5_1028 `sim` (stop-first, 5-min bars to 15:55), with the DESIGN 0.2 patches:
  - per-trade R and target multiple
  - 1c + 1 bp entry × ToD multiplier, and 1c + 1 bp on **every** exit, +2c on stop exits, all ×3 on the extended tier
  - gap-through stops fill at min(stop, high) for a long and max(stop, low) for a short
- **Sim check:** with the patches switched off, the copy must match `scan_1028.sim` exactly on one month of F1-A trades.
- **Random control:** for each trade, 5 random other universe symbols at the same signal row (seed 20261030), using the same
  side, the same R in ATR units, the same target multiple, the same sim and the same costs.

## Bar (BAR90, rules 21-22)
N = 2,000 + 108 (the swarm's pre-declared total) = 2,108, so t_req = 0.9 × sqrt(2 ln N) = 3.52. Every rework row is added to
N and t_req is recomputed.

A row passes only if all of these hold:
- day-clustered t >= t_req on TRAIN+VALID
- `gates.walk_forward` share of positive test months >= 54%
- avg R > 0 on TRAIN and on VALID separately
- >= 3 trades per session
- avg R > 0 on SPY up days and on SPY down days (SPY EOD fromOpen, a descriptive split)
- avg R above the random control

Reported for every row:
- n, trades/session, win rate, avg win and avg loss in R and their ratio
- TRAIN/VALID/all avg R and day t
- WF share and the simple share of positive months
- up/flat/down-day R (flat = |SPY day| < 0.25%)
- avg R without the best day and that day's share of the total
- busiest-session share, median cost/R, exit mix, control avg R

## Sanity check before scoring
F1-A's trades per session and its median R/ATR and cost/R are compared with DESIGN 0.4. That calibration gives about 0.27
long signals per liquid symbol-day before the fresh-break requirement and a median cost/R of 0.11. This check is printed
before any R column is read.

## Rework (rule 18)
Rework happens only after a row fails. Rework rows are new counted rows (neighbours, one condition removed, one condition
added), they are declared below as a dated amendment **before** they are scored, and N is raised to include them.

## Amendment 2026-10-30 (rework, rule 18; declared after the 18 rows failed, before any of these is scored)
All 18 rows failed. The strongest gradient was the cost floor: F1-G had the least negative avg R on both sides. Gross R
(net + cost) was about 0 on every row. Three neighbour rows (6 counted configs) are declared, which raises N to 2,114
(t_req 3.52). Market-direction gates are left to F2/F5 to avoid double counting.

| row | change | plain-English name |
|---|---|---|
| F1-RW1 | F1-G with the cost cap at 5% of R (neighbour) | 15-min ORB with Gap, skip if costs > 5% of risk |
| F1-RW2 | F1-C (FVG >= 0.10 ATR) + F1-G cost cap of 10% (one condition added) | 15-min ORB with Big Gap, low-cost only |
| F1-RW3 | F1-G + fixed 2R target (F1-F had the highest gross R) | 15-min ORB with Gap, low-cost, 2R target |
