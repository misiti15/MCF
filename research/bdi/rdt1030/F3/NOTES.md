# rdt1030 / F3 — 5-min Opening Range Break with Gap, break-even, 2 tries, index context: RESULTS

*Educational only — not financial advice.* Backtest only (2-year open history, TRAIN + VALID); nothing here is live or paper.

## Verdict: 0 of 24 counted configs pass. No finalist, no mask module.
- Configs scored by F3: **24** (18 pre-declared in PLAN.md + 6 rule-18 rework configs declared in the PLAN amendment before
  scoring). Bar: N = 2,000 + 108 (DESIGN) + 12 (F1/F2 rework) + 6 = 2,126, **t_req = 3.52**; WF >= 54%; avg R > 0 on TRAIN
  and VALID; >= 3 trades/session; up-day and down-day R > 0; above the random control.
- 348 sessions (TRAIN 2024-10, 2025-03..12; VALID 2026-01..03, 2026-07..2026-09-15). Locked block and HOLD months never loaded.
- Harness: the patched sim is a verbatim copy of ../F1/build.py `sim`; `build.py check` = 0.0 max diff vs scan_1028.sim
  with patches off. F4-18 parity (-0.0677R) was passed by F2 on the same frames/splits.
- Sanity (PLAN.md): trade counts, R/ATR (median 0.31) and cost/R (median 0.05-0.07) matched DESIGN 0.4 / F1-A.

## What the data says
- **No gross edge.** Gross R (net + cost) is -0.014 to +0.026 on every row; net R is -0.020 to -0.087.
- **The post's "30 points -> 2R" switch almost never fires on stocks** (0.1% of trades): the FVG-candle-1 stop is a median
  0.31 ATR_d, far wider than 30 NQ points (~0.085 ATR). So "BE at +1R" does nothing on the as-written row (exit_be 0.000).
- **The QQQ "context" gate does not remove market beta.** QQQ above its open at 10:00 is not an up day: every long row
  still loses 0.36-0.47R on SPY down days and every short row loses 0.30-0.46R on up days.
- **The 2nd trade is rare** (1-4% of trades inside 09:50-11:00; 9% with the all-day window) and only slightly less bad
  than trade 1 (F3-A: trade 1 -0.083/-0.058R, trade 2 -0.027/-0.023R L/S). "Stop after a win" changes nothing.
- **Closest row (still a clear fail): F3-RW1-S** (fixed 2R + skip if costs > 10% of R, short): -0.020R, t -0.49,
  TRAIN -0.046 / VALID +0.021, WF 50%, up/down-day -0.42 / +0.18. It is a down-market trade, not an edge.
- Live-support note: `mcf/execution/runner.py` supports same-setup re-entry (`live.same_setup_reentry`), but a cap of 2
  per symbol-day and the "close back inside first" re-arm are not in live; moot, since nothing passed.

## Every row (all fail). Avg R net of costs; best-day share blank because total R < 0.
| id | setup name | n/sess | win | avg W / L (R) | avg R | TRAIN | VALID | t_day | WF% | up / down-day R | w/o best day | ctrl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F3-A-L | 5-min Opening Range Break with Gap, break-even, 2 tries, QQQ context, Long | 68.7 | 0.496 | 0.81 / 0.95 | -0.082 | -0.060 | -0.124 | -2.81 | 20 | +0.037 / -0.381 | -0.099 | -0.077 |
| F3-A-S | 5-min Opening Range Break with Gap, break-even, 2 tries, QQQ context, Short | 66.6 | 0.504 | 0.83 / 0.96 | -0.057 | -0.093 | +0.005 | -1.75 | 10 | -0.394 / +0.114 | -0.066 | -0.077 |
| F3-B-L | 5-min ORB with Gap, BE, 2 tries, no index context, Long | 115.3 | 0.495 | 0.81 / 0.96 | -0.082 | -0.079 | -0.089 | -4.00 | 0 | +0.047 / -0.270 | -0.092 | -0.086 |
| F3-B-S | 5-min ORB with Gap, BE, 2 tries, no index context, Short | 117.0 | 0.490 | 0.82 / 0.96 | -0.087 | -0.111 | -0.049 | -3.85 | 0 | -0.303 / +0.103 | -0.092 | -0.095 |
| F3-C-L | 5-min ORB with Gap, 2 tries, QQQ context, earlier break-even (+0.5R), Long | 68.8 | 0.362 | 0.84 / 0.61 | -0.086 | -0.060 | -0.133 | -3.36 | 10 | +0.005 / -0.312 | -0.102 | -0.089 |
| F3-C-S | 5-min ORB with Gap, 2 tries, QQQ context, earlier break-even (+0.5R), Short | 66.8 | 0.369 | 0.87 / 0.61 | -0.064 | -0.091 | -0.018 | -2.33 | 20 | -0.330 / +0.071 | -0.072 | -0.089 |
| F3-D-L | 5-min ORB with Gap, BE, QQQ context, one try only, Long | 67.4 | 0.495 | 0.80 / 0.95 | -0.083 | -0.063 | -0.121 | -2.80 | 20 | +0.036 / -0.380 | -0.101 | -0.082 |
| F3-D-S | 5-min ORB with Gap, BE, QQQ context, one try only, Short | 65.3 | 0.503 | 0.83 / 0.96 | -0.058 | -0.092 | +0.002 | -1.77 | 20 | -0.393 / +0.112 | -0.067 | -0.079 |
| F3-E-L | 5-min ORB with Gap, BE, QQQ context, second try only after a loss, Long | 68.5 | 0.496 | 0.81 / 0.95 | -0.082 | -0.060 | -0.124 | -2.77 | 20 | +0.037 / -0.381 | -0.099 | -0.082 |
| F3-E-S | 5-min ORB with Gap, BE, QQQ context, second try only after a loss, Short | 66.5 | 0.504 | 0.83 / 0.96 | -0.057 | -0.093 | +0.005 | -1.75 | 10 | -0.394 / +0.115 | -0.066 | -0.079 |
| F3-F-L | 5-min ORB with Gap, BE, 2 tries, QQQ context, 2R on tight stops (<= 0.20 ATR), Long | 68.7 | 0.469 | 0.86 / 0.92 | -0.081 | -0.059 | -0.124 | -2.68 | 20 | +0.044 / -0.396 | -0.098 | -0.083 |
| F3-F-S | 5-min ORB with Gap, BE, 2 tries, QQQ context, 2R on tight stops (<= 0.20 ATR), Short | 66.6 | 0.480 | 0.88 / 0.93 | -0.059 | -0.094 | +0.001 | -1.77 | 10 | -0.402 / +0.116 | -0.068 | -0.079 |
| F3-G-L | 5-min ORB with Gap, BE, 2 tries, QQQ context, fixed 2R target, Long | 68.6 | 0.370 | 1.12 / 0.79 | -0.086 | -0.061 | -0.131 | -2.49 | 10 | +0.056 / -0.441 | -0.103 | -0.075 |
| F3-G-S | 5-min ORB with Gap, BE, 2 tries, QQQ context, fixed 2R target, Short | 66.6 | 0.362 | 1.22 / 0.77 | -0.051 | -0.086 | +0.008 | -1.27 | 20 | -0.460 / +0.157 | -0.064 | -0.079 |
| F3-H-L | 5-min ORB with Gap, BE, 2 tries, QQQ context, all-day window (to 15:00), Long | 90.7 | 0.498 | 0.80 / 0.96 | -0.082 | -0.069 | -0.106 | -3.45 | 10 | +0.020 / -0.386 | -0.094 | -0.081 |
| F3-H-S | 5-min ORB with Gap, BE, 2 tries, QQQ context, all-day window (to 15:00), Short | 92.4 | 0.496 | 0.82 / 0.97 | -0.078 | -0.106 | -0.025 | -2.88 | 10 | -0.420 / +0.062 | -0.085 | -0.085 |
| F3-I-L | 5-min ORB with Gap, BE, 2 tries, SPY-VWAP context, Long | 79.8 | 0.501 | 0.81 / 0.95 | -0.072 | -0.065 | -0.084 | -2.68 | 20 | +0.052 / -0.357 | -0.086 | -0.077 |
| F3-I-S | 5-min ORB with Gap, BE, 2 tries, SPY-VWAP context, Short | 77.0 | 0.492 | 0.83 / 0.96 | -0.081 | -0.109 | -0.036 | -2.58 | 10 | -0.436 / +0.116 | -0.089 | -0.086 |
| F3-RW1-L | 5-min ORB with Gap, 2R target, low-cost only, Long | 54.1 | 0.383 | 1.08 / 0.75 | -0.049 | -0.018 | -0.101 | -1.33 | 40 | +0.093 / -0.407 | -0.070 | -0.070 |
| F3-RW1-S | 5-min ORB with Gap, 2R target, low-cost only, Short | 53.6 | 0.372 | 1.18 / 0.73 | -0.020 | -0.046 | +0.021 | -0.49 | 50 | -0.416 / +0.183 | -0.033 | -0.076 |
| F3-RW2-L | 5-min ORB with Gap, BE, 2 tries, strong QQQ trend, Long | 36.4 | 0.513 | 0.81 / 0.96 | -0.051 | -0.034 | -0.079 | -1.19 | 10 | +0.046 / -0.474 | -0.082 | -0.059 |
| F3-RW2-S | 5-min ORB with Gap, BE, 2 tries, strong QQQ trend, Short | 35.4 | 0.501 | 0.84 / 0.96 | -0.058 | -0.122 | +0.035 | -1.25 | 30 | -0.434 / +0.091 | -0.070 | -0.083 |
| F3-RW3-L | 5-min ORB with Gap, BE, 2 tries, QQQ and SPY-VWAP agree, Long | 61.7 | 0.501 | 0.81 / 0.96 | -0.073 | -0.059 | -0.101 | -2.32 | 20 | +0.040 / -0.404 | -0.091 | -0.074 |
| F3-RW3-S | 5-min ORB with Gap, BE, 2 tries, QQQ and SPY-VWAP agree, Short | 58.6 | 0.507 | 0.83 / 0.96 | -0.052 | -0.090 | +0.015 | -1.43 | 10 | -0.447 / +0.132 | -0.062 | -0.080 |

Full columns (exit mix, cost/R, busiest-session share, trade-2 share and R, t by split, big up/down days) are in
`results.csv`; both sides of each system together (descriptive, not configs) in `both_sides_descriptive.csv`.

## Files
`PLAN.md` (pre-declaration + sanity + rework amendment), `build.py`, `score.py`, `rework_cfg.json`, `rework.json`,
`results.csv`, `both_sides_descriptive.csv`. Scratch parquet deleted after the report.
