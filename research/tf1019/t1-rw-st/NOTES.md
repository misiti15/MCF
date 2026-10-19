# t1-rw-st results (2026-10-19, overnight timeframe swarm)

Educational only - not financial advice.

- Plan: PLAN.md (pre-declared before scoring). Script: run.py (grid), score.py (gates) -> results.csv (all 95 rows).
- **Configurations scored: 95** (19 setups x 5 timeframes, module as-is, core 80 symbols). Time-equivalent versions:
  0 (not simple; lookbacks are hard-coded in heat_frame / extra_features). Locked block not loaded.
- **Passing: 0 of 95.** Best t anywhere is 2.49 (ST8-FD on 5m, n 40) against a lineage bar of 4.83-5.25.
- Gates use train + valid (2024-10, 2025-03..2026-10-07). Forward 10-08..10-16 is in results.csv (exp_fw), report only.

## Best timeframe per setup (by t; descriptive only - none passes)
| setup | best TF | n | exp train / valid | t (bar) | up / down | excess vs random | 5m t |
|---|---|---|---|---|---|---|---|
| L3-fromopen-FD | 15m | 319 | +0.145 / +0.134 | 2.45 (5.03) | -0.005 / +0.607 | +0.125 | 1.32 |
| L3-lowdist-FD | 10m | 303 | -0.054 / +0.067 | 0.16 (5.03) | -0.015 / +0.206 | +0.083 | -0.39 |
| L3-rsi5hi-FD | 10m | 443 | -0.041 / +0.139 | 1.08 (5.03) | +0.066 / +0.025 | +0.065 | 0.57 |
| RW1-FD | 10m | 224 | +0.081 / +0.014 | 0.69 (4.95) | -0.108 / +0.223 | +0.043 | -1.58 |
| RW2-FD | 3m | 3220 | -0.013 / +0.000 | -0.20 (5.25) | -0.175 / +0.232 | +0.044 | -2.40 |
| RW3-FD | 5m | 322 | -0.025 / -0.016 | -0.38 (4.95) | -0.151 / +0.140 | +0.078 | -0.38 |
| RW4-FD | 15m | 326 | +0.051 / +0.016 | 0.45 (4.83) | -0.107 / +0.171 | +0.016 | -0.13 |
| RW5-FD | 5m | 321 | -0.047 / -0.076 | -1.11 (4.95) | -0.337 / +0.264 | -0.023 | -1.11 |
| RW6-FD | 5m | 421 | -0.002 / -0.052 | -0.51 (4.83) | -0.151 / +0.212 | -0.017 | -0.51 |
| RW7-FD | 10m | 1106 | -0.042 / -0.034 | -0.93 (4.95) | -0.166 / +0.081 | -0.000 | -1.79 |
| ST1-FD | 10m | 266 | +0.010 / +0.126 | 1.45 (4.97) | +0.167 / +0.156 | +0.106 | -0.98 |
| ST2-FD | 5m | 1300 | -0.016 / +0.027 | 0.31 (4.97) | +0.039 / -0.064 | +0.031 | 0.31 |
| ST3-FD | 15m | 41 | -0.225 / +0.389 | 1.14 (4.97) | -0.030 / +0.203 | +0.186 | -0.24 |
| ST4-FD | 5m | 165 | -0.047 / +0.119 | 0.55 (4.97) | +0.111 / -0.094 | +0.082 | 0.55 |
| ST5-FD | 1m | 70 | -0.082 / +0.151 | 0.35 (4.97) | +0.063 / +0.057 | +0.163 | -0.35 |
| ST6-FD | 5m | 37 | -0.181 / +0.126 | 0.01 (4.97) | +0.319 / -0.038 | +0.127 | 0.01 |
| ST7-FD | 5m | 78 | +0.199 / +0.047 | 1.06 (4.97) | +0.406 / +0.130 | +0.069 | 1.06 |
| ST8-FD | 5m | 40 | +0.112 / +0.330 | 2.49 (4.97) | +0.259 / +0.154 | +0.219 | 2.49 |
| exhaustion-FD | 3m | 3270 | -0.019 / +0.000 | -0.31 (5.25) | -0.178 / +0.229 | +0.043 | -2.41 |

## What the grid says
- 1-minute decision bars are the worst for every family: mean t -1.73 across the 19 setups (3m -0.79, 5m -0.31,
  10m -0.52, 15m -0.44). Only 1 of 19 setups has exp > 0 on 1m. More, noisier signals with 14-minute RSI windows.
- Every short (RW1-RW7, exhaustion) loses in up sessions on every timeframe. The timeframe does not fix that.
- Several setups beat the random same-minute entry (excess > 0, e.g. L3-fromopen 15m +0.125 t 3.09, ST1 10m +0.106
  t 2.61), but the random entry itself is negative after costs, so the edge over random does not make the trade pay.
- RW2-FD and exhaustion_short-FD are almost the same trades on the core (all core names have ADV >= 150M).
- Lookbacks are in bars (as-is): RSI14 = 14/42/70/140/210 minutes on 1/3/5/10/15m; SMA50 = 50..750 minutes; 20-bar
  divergence = 20..300 minutes. So "ST1 on 10m" is a different indicator set, not the same rule on a different clock.
