# Escalation study (key `escalation`) — the "obvious shorts" of 2026-10-06

*Educational only — not financial advice.* Backtest results on the setup-lab frame (research/setups2/data), train
(to 2026-08-25, 40 sessions) and valid (2026-08-26..09-15, 14 sessions). Nothing dated >= 2026-09-16 was read, so
2026-10-06 itself could not be checked. Costs: lab costs (1c/share/side) in every number; `prod` columns subtract an
approximate production surcharge (+1 bps/side, +2c on stop exits; the 3c extended-tier surcharge is NOT modelled —
the auditor recomputes). Nothing here is tested live.

## Configurations tried: 243,027
Cartesian grids pre-declared in `search.py` (slots x windows x 3 geometries): gapfade 72,900 · failbo 62,208 ·
bottom 23,328 · mexh 23,328 · lowerhigh 19,683 · orbext 17,280 · lodbreak 15,552 · vwaploss 8,748.
Gate (task): train exp_r > 0, valid exp_r > 0, valid n >= 30, valid day-clustered t >= 1.5, valid plateau mean
(one-step neighbours) > 0, valid exp_r > same-window random baseline (all names and the family universe), train
exp_r > train baseline. 1,867 configurations passed (0.77%) — `passers.jsonl`. These configurations are heavily
correlated and the gate is two-sided, but with ~243k looks the passers are consistent with chance; every finalist
needs the locked holdouts.
Selection rule (fixed before looking at finalists): per family, among passers with valid ex-best-day > 0, prefer
a strict plateau (every one-step neighbour positive on valid), then rank by min(train t, valid t).

## Failures first
| idea | result |
|---|---|
| **D: short the 11:05 cluster's inverse** (gap-up, below open + VWAP), 10:00-11:00 / 10:30-11:30 / 11:00-12:00 | **0 passers.** Core rule valid: 10:00-11:00 +0.037R (t 0.6), 10:30-11:30 **-0.155R (t -1.9)**, 11:00-12:00 **-0.123R (t -1.5)**. <=2% of layered variants positive on valid in 10:30-12:00. |
| heat_fade_long signals traded SHORT (the literal "obvious short") | train -0.057R (t -1.2, n 2,144), valid **-0.116R (t -1.65, n 461)**. The long side is +0.028R / +0.085R. |
| E late (11:30-13:00) | 0 passers; core valid -0.072R (t -1.2). |
| A: ORB extension cap (long at HOD, above VWAP, capped vwap/fromOpen/rsi5/SMA20 extension) | **0 of 17,280 positive on valid**; core -0.12 to -0.15R valid. A cap does not rescue HOD breakout longs in this frame. |
| H: morning exhaustion short 09:50-11:30 (rsi5, SMA20 extension, bear_div, wick, climax) | 0 passers; core -0.04R train in every window. FCEL-type 09:50 fades are not an edge here. |
| I2: lower-high confirmation short | 0 passers (train positive in 1000-1300 t1s1 but ~0% valid). |
| F bottom long before 12:00 | core -0.12R train (t -2.9) 10:30-12:00; passers only 12:00-14:30. |

## Autopsy (autopsy.py, autopsy.json)
heat_fade_long (regime_5) rebuilt on the lab frame: train +0.028R (t 0.58, n 2,144, ex-best-day +0.005), valid
+0.085R (t 1.19, n 461). Winners vs losers: **no metric separates them** — every feature AUC is 0.45-0.55 and the
direction flips between train and valid (train: deeper fades/flow3=-1 did best; valid: higher rsi5 and bigger gap
did best). Orb-style first-hour HOD longs: -0.065R train / -0.061R valid; valid winners had stronger trend
(sma20 slope, emaDiff, gap>0: AUC 0.56-0.57) but the same features are ~0.5 on train.

## Finalists (lab costs; valid = 14 sessions)
| tag | side/geom | train exp (t, n) | valid exp (t, n, days) | ex-best | green | prod valid (t) | plateau mean/min | base valid |
|---|---|---|---|---|---|---|---|---|
| X-gapfade-early | short t1s05 0950-1030 | +0.149 (1.54, 143) | +0.274 (2.10, 31, 10) | +0.171 | 0.60 | +0.225 (1.69) | +0.216/+0.088 | -0.027 |
| X-gapfade-early-b | short t1s05 0950-1030 | +0.177 (2.10, 197) | +0.195 (2.06, 32, 11) | +0.156 | 0.73 | +0.154 (1.52) | +0.108/-0.070 | -0.027 |
| X-bottom-div | long t1s1 1200-1430 | +0.081 (1.51, 299) | +0.296 (2.56, 47, 12) | +0.261 | 0.75 | +0.275 (2.34) | +0.276/+0.017 | -0.127 |
| X-failbo | short t1s1 1000-1100 | +0.146 (1.71, 166) | +0.249 (1.94, 70, 12) | +0.146 | 0.50 | +0.213 (1.63) | +0.178/+0.042 | -0.035 |
| X-vwaploss-run | short t1s1 1000-1300 | +0.151 (1.93, 117) | +0.212 (2.13, 45, 10) | +0.184 | 0.80 | +0.168 (1.61) | +0.126/+0.002 | -0.016 |
| X-lodbreak-early | short t1s05 0950-1030 | +0.091 (1.16, 145) | +0.145 (1.51, 55, 14) | +0.061 | 0.36 | +0.082 (0.85) | +0.069/-0.084 | -0.027 |

Modules: `finalists/x_*.py` (SIDE, GEOM, LAYERS, mask(df) over lab-frame columns; `_common.py` derives ATR units
from fromOpen/close/atr_d). Re-scored from the modules by `verify.py` -> `finalists.json` (X-bottom-div differs by a
few trades from the grid because the module compares in float64; the module numbers are the ones reported).

Flags:
- X-failbo: 31 of 70 valid trades fell on 2026-09-03 (+11.8R); 6 of the last 7 valid days were red (valid half2 -0.27R).
- X-gapfade-early / -b: the train edge sits in train half1 (+0.32/+0.44R); train half2 is ~0 (-0.01R). Small valid n (31-32).
- X-lodbreak-early: green-day share 0.36, no strict plateau, fails at production costs (valid t 0.85).
- X-gapfade-early has 8 layers (high overfit risk); -b is the 6-layer version of the same idea (58 shared train symbol-days).
- X-bottom-div train t is 1.51 and its train half1 is ~0 (+0.003R).
- Production costs cut 0.02-0.06R; the auditor's exact restatement governs.

Run: `python research/primitives/escalation/search.py` (~2.5 min, ~2 GB), then `analyse.py`, `verify.py`, `autopsy.py`.
Full per-config results (`results_*.jsonl`, ~240 MB) are regenerated by search.py and git-ignored; gate passers are in `passers.jsonl`.
