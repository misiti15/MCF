# tf1019/primary - the 12 Primary setups on 1/3/5/10/15-minute decision bars

Run 2026-10-19 ~03:00 UTC (Sun 22:55-23:10 ET) per the pre-declared PLAN.md. Educational only - not financial advice.

**Result: 0 of 108 configurations pass. No timeframe rescues any Primary setup; no module is written to modules/.**

- Universe: the 80 "core" symbols (all five timeframes exist), min_adv 95M, config windows/geometries, production-cost R,
  first bar per symbol-day (RW6G1 refire not modelled). Train 2024-10 + 2025-03..12, valid 2026-01..10-07, forward
  10-08..10-16 (reported, not used). Locked block 2024-11..2025-02 never loaded (TE builder drops it at load).
- Configurations: 60 as-is + 48 time-equivalent = **108**. Bar: N_lineage ~ 82,000 (MF 82,068 / NS 81,430 / RW6G1 ~81,950,
  + 108) -> **t_required 4.76**; for this family alone (N=108) it would be 3.06. Best t of any config with n >= 30: 1.61
  (NS1 5-min, n 45). Every best-per-setup row fails train exp > 0 or the regime gate (n >= 30 in up AND down) anyway.
- Core-universe 5-min numbers differ from the ~1,200-symbol history2y numbers (80 symbols, so far fewer trades).
- **AS-IS on faster bars = more trades, worse R.** 1-min versions fire 3-8x as often (MF3-FD 4,721 trades) and are
  negative on train and valid for all 12 (t -0.95..-4.59); the excess over the random same-minute baseline is <= 0 for
  10 of 12. 10/15-min versions mostly fire too rarely to judge (n < 40 for MF1-MF4, NS1, NS4, RW6G1).
- **TIME-EQUIVALENT lookbacks do not reproduce the 5-min signal.** Scaling RSI14/RSI5/buyPressure19/SMA50/heat to the same
  clock span on 1-min bars compresses the indicators (RSI5 std 12 vs 26; buyPressure std 0.16 vs 0.27 in 2026-09), so the
  fixed thresholds (RSI5 > 70/80, bp < -0.25) almost never fire: 1-min TE n = 1-23 for 10 of 12 setups. On 10/15-min the
  TE versions fire more than 5-min but none is positive on both train and valid with t > 1.1.
- TE builder parity: at m=5 it reproduces frames_tf rsi/rsi5/buyPressure/sma50/heat exactly (max diff 0.0).

Files: PLAN.md (pre-declared), te_build.py, run.py, results.csv (all 108 rows, every gate), grid.md (setup x timeframe:
n / train exp / valid exp / t). Scratch (TE columns, trades) deleted.
| setup | var | 1m | 3m | 5m | 10m | 15m |
|---|---|---|---|---|---|---|
| MF1 | asis | 225 / -0.13 / -0.05 / t -1.73 | 352 / -0.16 / +0.05 / t -1.57 | 90 / -0.13 / +0.03 / t -0.66 | 12 / -0.23 / +0.57 / t 0.16 | 1 /  / +0.91 / t na |
| MF1 | te | 12 / -0.18 / -0.31 / t -1.87 | 44 / +0.04 / -0.20 / t -0.66 | = as-is | 271 / -0.21 / +0.10 / t -1.99 | 155 / -0.21 / -0.03 / t -2.27 |
| MF2 | asis | 453 / -0.04 / -0.05 / t -0.95 | 108 / -0.07 / +0.08 / t 0.28 | 40 / -0.22 / -0.25 / t -2.43 | 2 / +0.95 / +0.99 / t 65.48 | 3 / -0.10 /  / t -0.22 |
| MF2 | te | 10 / -0.35 / -0.08 / t -1.24 | 37 / -0.12 / -0.17 / t -1.17 | = as-is | 43 / -0.28 / -0.08 / t -1.85 | 34 / -0.36 / +0.00 / t -0.9 |
| MF3 | asis | 724 / -0.16 / -0.09 / t -2.81 | 316 / -0.14 / +0.05 / t -1.01 | 172 / -0.08 / -0.11 / t -1.14 | 35 / -0.21 / +0.08 / t -0.51 | 16 / -0.39 / +0.48 / t -0.54 |
| MF3 | te | 1 /  / -1.31 / t na | 62 / -0.11 / -0.11 / t -0.9 | = as-is | 559 / -0.08 / -0.06 / t -1.52 | 525 / -0.05 / -0.10 / t -1.28 |
| MF4 | asis | 296 / -0.20 / -0.06 / t -3.25 | 294 / -0.17 / -0.04 / t -2.35 | 186 / -0.04 / -0.17 / t -1.78 | 35 / -0.11 / -0.06 / t -0.68 | 12 / -0.28 / -0.32 / t -1.22 |
| MF4 | te | 318 / -0.02 / +0.03 / t -0.03 | 223 / -0.01 / -0.01 / t -0.14 | = as-is | 349 / -0.14 / -0.04 / t -2.19 | 321 / -0.03 / -0.10 / t -1.25 |
| MF5 | asis | 1333 / -0.13 / -0.03 / t -3.43 | 472 / -0.13 / +0.03 / t -1.29 | 269 / -0.02 / -0.08 / t -0.77 | 135 / -0.17 / +0.06 / t -0.86 | 97 / -0.05 / +0.22 / t 0.34 |
| MF5 | te | 1 /  / -1.31 / t na | 94 / -0.13 / -0.03 / t -1.01 | = as-is | 1104 / -0.09 / -0.06 / t -2.45 | 840 / -0.04 / -0.01 / t -0.99 |
| MF3-FD | asis | 4721 / -0.10 / -0.07 / t -4.59 | 1178 / -0.08 / -0.05 / t -2.21 | 579 / -0.14 / +0.01 / t -1.89 | 268 / -0.02 / -0.02 / t -0.35 | 180 / -0.07 / -0.10 / t -1.08 |
| MF3-FD | te | 23 / -0.04 / -0.16 / t -0.66 | 298 / -0.19 / -0.06 / t -2.94 | = as-is | 1815 / -0.09 / -0.08 / t -3.24 | 1248 / -0.05 / -0.05 / t -1.61 |
| RW3-FD | asis | 2256 / -0.11 / -0.05 / t -2.93 | 621 / -0.16 / -0.04 / t -2.23 | 338 / -0.03 / -0.02 / t 0.06 | 154 / -0.07 / +0.01 / t -0.11 | 45 / -0.16 / +0.02 / t -0.76 |
| RW3-FD | te | 1 / -0.59 /  / t na | 124 / -0.14 / -0.22 / t -2.16 | = as-is | 898 / -0.14 / -0.01 / t -1.61 | 525 / -0.10 / -0.14 / t -2.57 |
| RW5-FD | asis | 3106 / -0.11 / -0.07 / t -3.62 | 716 / -0.07 / -0.02 / t -1.28 | 326 / -0.05 / -0.08 / t -0.93 | 142 / +0.00 / -0.27 / t -1.31 | 62 / -0.02 / -0.19 / t -1.05 |
| RW5-FD | te | 3 / +0.30 / +0.04 / t 0.67 | 130 / -0.08 / -0.04 / t -0.98 | = as-is | 1250 / -0.11 / -0.12 / t -3.28 | 673 / -0.06 / -0.08 / t -1.65 |
| NS1 | asis | 348 / -0.07 / -0.08 / t -1.81 | 138 / +0.21 / -0.01 / t 1.56 | 45 / +0.10 / +0.18 / t 1.61 | 10 / +0.11 / -0.02 / t 0.15 | 6 / -0.28 / -0.26 / t -0.87 |
| NS1 | te | 1 / -1.04 /  / t na | 27 / -0.13 / +0.20 / t -0.09 | = as-is | 138 / +0.17 / +0.03 / t 1.51 | 115 / -0.05 / +0.02 / t -0.1 |
| NS4 | asis | 328 / -0.09 / -0.01 / t -1.27 | 202 / +0.02 / -0.03 / t -0.09 | 137 / -0.17 / +0.11 / t -0.67 | 42 / +0.06 / +0.01 / t 0.15 | 15 / +0.19 / -0.15 / t -0.2 |
| NS4 | te | 1 /  / -0.63 / t na | 76 / -0.13 / +0.01 / t -0.63 | = as-is | 206 / -0.12 / -0.01 / t -1.58 | 202 / -0.10 / +0.01 / t -0.96 |
| NS5 | asis | 464 / -0.09 / -0.08 / t -1.38 | 249 / -0.11 / +0.05 / t -0.54 | 162 / -0.14 / +0.06 / t -0.51 | 67 / -0.49 / -0.20 / t -2.32 | 157 / -0.10 / -0.20 / t -1.46 |
| NS5 | te | 1 /  / -1.10 / t na | 80 / -0.24 / -0.04 / t -0.92 | = as-is | 296 / -0.10 / +0.10 / t -0.15 | 303 / -0.10 / -0.15 / t -1.51 |
| RW6G1 | asis | 609 / -0.19 / -0.13 / t -3.23 | 90 / +0.30 / -0.14 / t 0.37 | 73 / +0.12 / -0.03 / t 0.93 | 25 / -0.36 / +0.20 / t -0.94 | 30 / +0.22 / +0.05 / t -0.21 |
| RW6G1 | te | 10 / -0.38 / -0.71 / t -1.84 | 57 / -0.38 / +0.02 / t -1.06 | = as-is | 81 / -0.47 / -0.06 / t -1.8 | 56 / +0.18 / +0.16 / t 1.1 |
