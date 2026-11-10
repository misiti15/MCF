# stoplab B: per-trade stop width (k x each setup's own stop distance)

*Educational only — not financial advice.* Research only: nothing in config/, mcf/, setups, exits, docs/live or the ledger
is changed. Written 2026-11-10 against the pre-registration in `../PLAN.md` (grid B; B2 is a diagnostic, B3 the lab
test). B1 (full 1-min live re-walk with a parity gate) was **not run**. B2 does use 1-min bars, but only to carry
stop-exited trades past their old stop.

## Answer in one paragraph
Widening every stop does not hold up as a fix for the stop itself. On the 2-year lab (119 setups, 917k trades in
TRAIN+VALID, costs in, same $ risk), wider stops raise R per trade (k=1.5: +0.025R VALID, 80 of 117 setups better). But
that gain comes **almost all from size**: same $ risk means fewer shares, and most lab books lose (pooled base -0.06R).
Against the size-only control (same trade, old stop, size x 1/k), the stop effect is only +0.003..+0.006R. It is ~0 on
SPY-down days (t 0.1-0.6 for k=1.5) and appears only on up days. This is the same pattern the Guild's STOPW study found
(see below). Tighter stops (0.75 / 0.9) are worse in the lab for 98 / 90 of 117 setups.

**Per-setup choice is mostly noise:**
- Among the 45 setups that make money at k=1 on TRAIN, the TRAIN-best k validates in only 17 and worsens in 28.
  None passes.
- The 21 per-setup "passes" are all losing setups (CWT14 / CWT05 / CWT13 / CWT12, L3-lowdist, MF3-FD, NS2-FD, ST5-FD,
  L3-fromopen-FD). Their best k is 1.5, the edge of the grid. Only 8 clear the per-setup bar on the stop effect itself,
  and only CWT05-flush-m05-v3-long clears the study-wide bar of 2.88 (it is still negative at k=1.5).
- **L3-gap-slope-fromopen-FD (Primary)** is the one notable case:
  - Lab: avg R -0.023 / -0.006 at k=1 becomes +0.010 / +0.025 at k=1.5. Stop effect +0.029R/trade, t 2.52, plateau
    yes, best day 30%.
  - But the live approximation points the other way: d -0.10R at k=1.5, live best k = 1.0.
  - So it is a lead to re-test in B1, not a change.
- The live approximation (110 setups with >= 20 trades) agrees with the lab direction in 43 setups and disagrees in
  27. Its own choose→validate sign agreement is ~50%, which is chance.
- **No stop-width change is proposed.** -1R at the setup's own distance (k=1.0) stays.

## Data, harness, splits
- **Lab signals.**
  - 92 traded setups: the latch_1103 2-year lists (`/home/user/MCF/research/history2y/data/bt_lab1104/sig_*.parquet`),
    re-walked.
  - 29 more traded lab setups with a t/s geometry: signals rebuilt from the module mask and the config entry, using
    latch_1103 `bt_all.py` rules.
  - Coverage: 121 of the 178 traded setups with lab modules. 119 have TRAIN/VALID rows.
  - Not covered:
    - geometries the harness can't walk: hold 24, holdtr 23, S 7, S+ts2 1 (includes CWT09-gapdn-vwaploss-g10-short and
      the CWT14 R2A pair);
    - symbol allow-list 2 (includes NM-ETF-late-dip-di-long);
    - the 15 setups with no lab module (heat_fade_*, orb20_a, intraday_momentum, old windowed names).
  - All of these get the live approximation only. `inventory.csv` lists them.
- **Walk.** Same as `bt_all.walk`: 5-min path after the signal bar, stop checked first, flatten at 15:55. Target price is
  unchanged; stop = entry ∓ k·dn·R.
  - r_k = net points / (k·dn·R), so $ risk per trade stays constant.
  - Costs: production costs (entry 1c + 1 bps × time-of-day multiplier; non-target exits 1c + 1 bps; +2c on stops;
    ×3 on the extended tier).
  - **Parity:** at k=1.0 the walk reproduces the cached latch_1103 r exactly (mean |d| = 1.6e-8 on 38,398 rows,
    2024-10).
- **Splits.** TRAIN <= 2025-12 is where k is chosen. VALID = 2026-01..03 + 2026-07-01..09-15. HOLD (2026-04..06,
  2026-09-16 on) is dropped and never read.
  - The locked block 2024-11..2025-02 is never loaded (asserted; `MCF_HIST_ALLOW_LOCKED` unset).
- **Size-only control** (the Guild's standard tool since 11-09): stop effect = r_k − r_1/k.
- **Pass bar (per setup), all required:**
  - k ≠ 1 chosen on TRAIN (n_train ≥ 30), with d > 0 in both TRAIN and VALID;
  - day-clustered VALID t ≥ 1.79 (max(1.5, √(2 ln 5))); the study-wide bar of 2.88 (N = 64) is reported too;
  - plateau: both neighbouring k beat k=1 (TRAIN and VALID);
  - stop effect > 0;
  - d still > 0 without the best VALID day.
  - "PASS+stop" additionally needs stop-effect t ≥ 1.79.
- **Configurations counted.**
  - B3: 5 multipliers × 119 setups = 595 setup-configs, counted as 5 grid rows in the study N = 64 (PLAN). The
    per-setup choice is from 5, giving a bar of 1.79.
  - B2 (diagnostic, not a candidate): 5 × 110.
  - Regime sensitivity: 5 × 2 (not counted).

## Global k (one multiplier for every lab setup with ≥ 30 VALID trades), d = r_k − r_1.0 per trade
| k | setups | pooled d TRAIN | pooled d VALID (t) | stop effect VALID (t) | setups better / worse VALID | sum gain / sum loss (R/trade) | worst setup | better / worse in BOTH splits | stop effect better / worse |
|---|---|---|---|---|---|---|---|---|---|
| 0.75 | 117 | -0.0369 | -0.0317 (-15.5) | -0.0125 (-4.8) | 19 / 98 | +0.36 / -3.84 | -0.175 | 5 / 82 | 18 / 99 |
| 0.9 | 117 | -0.0115 | -0.0110 (-14.1) | -0.0046 (-4.8) | 27 / 90 | +0.24 / -1.39 | -0.091 | 12 / 67 | 29 / 88 |
| 1.1 | 117 | +0.0091 | +0.0081 (10.3) | +0.0029 (3.6) | 81 / 36 | +0.94 / -0.39 | -0.042 | 60 / 17 | 82 / 35 |
| 1.25 | 117 | +0.0201 | +0.0155 (10.9) | +0.0040 (3.0) | 75 / 42 | +1.57 / -0.72 | -0.041 | 62 / 22 | 78 / 39 |
| 1.5 | 117 | +0.0316 | +0.0253 (10.8) | +0.0061 (3.1) | 80 / 37 | +2.20 / -1.24 | -0.091 | 65 / 23 | 82 / 35 |

### SPY up / down days (TRAIN and VALID): the stop effect for wider stops lives on up days only
| k | split | SPY day | d (t) | stop effect (t) |
|---|---|---|---|---|
| 0.75 | train | down | -0.0344 (-10.4) | -0.0059 (-1.4) |
| 0.75 | train | up | -0.0395 (-15.5) | -0.0153 (-4.3) |
| 0.75 | valid | down | -0.0282 (-10.8) | -0.0092 (-2.7) |
| 0.75 | valid | up | -0.0358 (-11.3) | -0.0164 (-4.0) |
| 1.1 | train | down | +0.0082 (8.0) | +0.0004 (0.4) |
| 1.1 | train | up | +0.0101 (11.8) | +0.0035 (4.0) |
| 1.1 | valid | down | +0.0078 (7.6) | +0.0026 (2.4) |
| 1.1 | valid | up | +0.0085 (6.9) | +0.0032 (2.6) |
| 1.25 | train | down | +0.0182 (8.0) | +0.0011 (0.5) |
| 1.25 | train | up | +0.0220 (11.4) | +0.0075 (4.3) |
| 1.25 | valid | down | +0.0141 (8.3) | +0.0026 (1.5) |
| 1.25 | valid | up | +0.0173 (7.3) | +0.0056 (2.7) |
| 1.5 | train | down | +0.0289 (7.5) | +0.0004 (0.1) |
| 1.5 | train | up | +0.0345 (11.2) | +0.0103 (3.9) |
| 1.5 | valid | down | +0.0206 (7.6) | +0.0016 (0.6) |
| 1.5 | valid | up | +0.0309 (7.9) | +0.0116 (4.4) |

- Pooled figures are trade-weighted, so CWT14 (most lab rows) dominates them. The per-setup counts above are the fair
  read.
- `global_k.csv` and `regime_k.csv` hold the numbers.

## Per-setup choice (Remedies table)
- **TRAIN-best k:** 0.75 in 15 setups, 0.9 in 12, 1.0 in 6, 1.1 in 9, 1.25 in 8, 1.5 in 69. 69 + 15 sit at the edge
  of the grid, which is a ramp, not a plateau.
- **113 setups pick k ≠ 1:**
  - VALID improves in 74 (sum +1.82 R/trade) and worsens in 39 (sum −1.26, worst −0.132).
  - The stop effect beyond size is > 0 in 61 and < 0 in 52.
- **TRAIN-positive setups (45):** VALID improves in 17 and worsens in 28. 0 pass.
- **TRAIN-negative setups (68):** VALID improves in 57 and worsens in 11. 21 pass. 63 of them pick 1.5, i.e. "trade the
  loser smaller".
- **Passes at the study-wide t of 2.88:** 13 on total d, 1 on the stop effect (CWT05-flush-m05-v3-long, still
  −0.039R at k=1.5).
- **Only 3 passers turn positive in both splits at their best k:**
  - L3-gap-slope-fromopen-FD: +0.010 / +0.025;
  - CWT05-flush-m075-v3-long: −0.132 / +0.023, so TRAIN is still negative;
  - ST5-pdbrkup-short-mid-t05s1-FD: −0.039 / +0.044, so TRAIN is still negative.
  - So L3-fromopen-FD is the only one positive in both.

## Live approximation (B2) — APPROXIMATE
- **What it covers:** 17,508 live paper trades from all 7 accounts, 10-06..11-09, run_id 1. The 76 scale-out exits are
  dropped.
- **Method:** same $ risk, target price unchanged.
  - k < 1: a trade is stopped if mae_r ≤ −k or it was a stop exit. Otherwise r = R/k (same exit, bigger size).
  - k > 1: non-stop exits give R/k. Stop exits are carried on on 1-min bars from the exit minute with the wider stop.
    4,915 of 6,708 were continued; the rest are after 11-04 or on an uncached symbol, and are dropped for k > 1.
  - New-exit costs and slippage: the setup's median.
- **Path order inside bars is unknown.** 2,668 of 6,708 stop exits show bar-mark mae_r > −1, so mae understates the true
  excursion. That biases k < 1 in favour of tight stops.
- **Short window:** ≤ 25 sessions.
- **Results:**
  - Best live k: 0.75 in 31 setups, 0.9 in 12, 1.0 in 11, 1.1 in 8, 1.25 in 13, 1.5 in 35.
  - Mean d per setup: k=0.75 −0.013, 0.9 −0.002, 1.1 −0.005, 1.25 −0.009, 1.5 −0.016. No multiplier helps on average.
  - Choose→validate sign agreement (first 60% / last 40% of sessions): 41..62 of ~103, i.e. chance.
  - Lab vs live direction (best k above / below 1): same 43, opposite 27, one neutral 11; 71 setups lack one side.
- `live_setup_k.csv` has the per-setup rows (dlv* = d vs live R; selv* = stop effect).

## Rule-change context (research/ledger.jsonl), live window 10-06..11-09
- Live scale-out fixes on 10-16 and 10-20.
- Per-setup daily stop:
  - on in T1/T2/Gen 10-19..10-22; latched from 10-23 (LL-LATCH), then ST-A switched it off in T1/T2/Gen on 10-23;
  - Graveyard at −2R from 10-21;
  - Primary at −2R latched from 10-29 (ST-P).
- Primary size ~$5k, then ~$4k from 10-28.
- BAR90 10-29; CF cost filter in T1/T2 10-30; R2A cap exemption 11-03; ROLL1 11-05; EXPO1109 11-09.
- These change which trades exist, not how a trade is re-walked: every k sees the same trades. B2 rows for k > 1 stop
  at 11-04, the end of the bar cache.

## Relation to the Research Guild's STOPW (mcf-guild board.jsonl, 2026-11-09)
- **What STOPW tested:** a minimum stop width in bps, D' = max(D, 60/80/100bp), only where stops are tight, at the same
  $ risk (Scout's frozen plan, family N 77).
- **Its result:**
  - Builder scored it: +0.013..+0.027R, but 85% of that was the size cut.
  - The stop effect was +0.002..+0.003R and negative on down days.
  - Lead closed STOPW as a stop remedy (lead-20261109-2100-1).
- **How this study differs:** it does not repeat that test. It scales every stop proportionally (both tighter and
  wider), per setup, with a train/validate choice, and it includes the live approximation.
- **Where it agrees:** it reaches the same verdict and finds the same down-day failure. That makes two independent
  harnesses with the same answer.
- **Lineage:** count it in the stop-width family (losers1102 wide-stop 1.5x, bdi1023, bdi-1008 exit geometry, STOPW).

## Priority setups (P1 = in Primary per setups.csv; P2 = Claude's Team list / MF2-MF4 / CWT12 / GEN-261027-01)
- **Verdict:**
  - "pass(size)" means it passes on total d, but the gain is mostly the size cut.
  - "PASS+stop" means the stop effect itself also clears t 1.79.
  - "edge" means the best k is at the end of the grid.
- **Live d columns** are the live approximation's d vs live R. "<20" means fewer than 20 live trades (shown for priority
  setups only).

| P | setup | lab n tr/va | lab R tr / va (k=1) | best k TRAIN | VALID d (t) | stop eff. VALID | plateau | verdict | live n (sess) | live R / w/o best day | live best k | live d k0.75 / k1.25 / k1.5 | lab vs live |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | heat_fade_short | not covered |  |  |  |  |  |  | 328 (23) | -0.20 / -0.30 | 1.5 | -0.01 / +0.04 / +0.08 |  |
| 1 | CWT14-failbrk-pdl-p10-lowvol-long | 12716/7764 | -0.091 / -0.095 | 1.5 | +0.036 (5.25) | +0.005 | edge,yes | pass(size) | 306 (21) | -0.08 / -0.10 | 1.1 | -0.03 / +0.00 / -0.01 | same |
| 1 | CWT13-vwapstretch-z05-long | 10162/5478 | -0.068 / -0.080 | 1.5 | +0.039 (3.53) | +0.013 | edge,yes | PASS+stop | 272 (19) | -0.15 / -0.20 | 1.5 | -0.05 / -0.00 / +0.03 | same |
| 1 | L3-gap-slope-fromopen-FD | 21045/12828 | -0.023 / -0.006 | 1.5 | +0.031 (2.08) | +0.029 | edge,yes | PASS+stop | 267 (18) | +0.16 / +0.05 | 1 | -0.02 / -0.05 / -0.10 | one-neutral |
| 1 | heat_fade_long | not covered |  |  |  |  |  |  | 235 (24) | -0.21 / -0.30 | 1.5 | -0.02 / +0.02 / +0.02 |  |
| 1 | MF3-open-flowsell-rsi5hi-FD | 5662/2964 | -0.099 / -0.054 | 1.5 | +0.026 (2.45) | +0.008 | edge,yes | pass(size) | 219 (21) | -0.20 / -0.25 | 1.5 | +0.04 / +0.02 / +0.05 | same |
| 1 | NS3-failed-vwap-reclaim-short-FD | 6929/6326 | -0.004 / -0.018 | 1.5 | +0.020 (1.15) | +0.014 | edge,yes | fail | 175 (18) | -0.14 / -0.21 | 1.25 | -0.04 / +0.06 / +0.05 | same |
| 1 | MF4-h40-open-flowsell-FD | 3633/2174 | -0.119 / -0.071 | 1.5 | +0.019 (2.20) | -0.005 | edge,yes | fail | 138 (21) | -0.23 / -0.28 | 0.75 | +0.01 / -0.02 / -0.02 | opposite |
| 1 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 2888/1611 | -0.054 / -0.078 | 1.5 | +0.025 (1.67) | -0.001 | edge,yes | fail | 133 (20) | +0.35 / +0.26 | 0.75 | +0.10 / -0.09 / -0.15 | opposite |
| 1 | MF2-open-rsimidhi-flowsell-FD | 2242/1807 | -0.055 / -0.194 | 1.5 | +0.036 (1.86) | -0.028 | edge,yes | fail | 125 (19) | +0.11 / -0.15 | 0.75 | +0.08 / -0.08 / -0.20 | opposite |
| 1 | RW3-gapdn-rsi5pop-flowsell-short-FD | 3118/1682 | -0.095 / -0.041 | 1.5 | +0.017 (1.28) | +0.003 | edge,yes | fail | 123 (20) | +0.41 / +0.26 | 1.1 | -0.01 / -0.05 / -0.11 | same |
| 1 | exhaustion_short | 2869/1674 | -0.061 / +0.078 | 1.5 | -0.015 (-0.67) | +0.011 | edge,no | fail | 106 (19) | -0.05 / -0.17 | 0.75 | +0.04 / -0.03 / -0.02 | opposite |
| 1 | L3-gap-slope-rsi5hi-FD | 5109/3274 | -0.084 / +0.011 | 1.5 | +0.007 (0.53) | +0.010 | edge,yes | fail | 91 (17) | +0.07 / -0.03 | 0.75 | +0.01 / -0.05 / -0.08 | opposite |
| 1 | MF5-flowsell-vwapup-rsi5hi | 3927/1737 | -0.096 / -0.001 | 1.5 | +0.010 (0.66) | +0.010 | edge,yes | fail | 89 (22) | -0.04 / -0.15 | 1.25 | +0.02 / +0.03 / +0.02 | same |
| 1 | NS2-sma50break-overbought-short | 1471/1118 | +0.031 / -0.046 | 1.1 | -0.002 (-0.20) | -0.006 | no | fail | 67 (9) | -0.33 / -0.37 | 0.75 | +0.05 / -0.04 / -0.05 | opposite |
| 1 | NS3-failed-vwap-reclaim-short | 573/458 | +0.063 / +0.166 | 1 |  |  |  | keep 1.0 | 67 (10) | -0.23 / -0.40 | 1.25 | -0.03 / +0.13 / +0.12 | one-neutral |
| 1 | MF3-open-flowsell-rsi5hi | 2382/1034 | -0.124 / -0.027 | 1.5 | +0.019 (0.85) | +0.010 | edge,yes | fail | 44 (10) | -0.02 / -0.12 | 0.75 | +0.07 / +0.04 / +0.05 | opposite |
| 1 | ST7-rsi50dn-long-pm-t1s1-FD | 371/370 | -0.062 / +0.100 | 1.5 | -0.028 (-1.08) | +0.006 | edge,no | fail | 37 (12) | +0.16 / +0.06 | 0.75 | +0.00 / -0.05 / -0.10 | opposite |
| 1 | orb20_a | not covered |  |  |  |  |  |  | 37 (17) | -0.12 / -0.30 | 1 | -0.05 / -0.07 / -0.09 |  |
| 1 | NS4-pm-vwap-reclaim-oversold-short | 629/523 | -0.255 / +0.021 | 1.5 | +0.007 (0.23) | +0.014 | edge,yes | fail | 36 (13) | -0.11 / -0.18 | 0.75 | +0.07 / -0.02 / +0.01 | opposite |
| 1 | NS5-sma50-flush-oversold-long | 665/388 | -0.174 / +0.163 | 0.9 | +0.025 (2.21) | +0.006 | yes | fail | 31 (12) | +0.06 / -0.00 | 0.75 | +0.09 / +0.02 / +0.02 | same |
| 1 | MF1-945-flowsell-vwapup | 1346/632 | -0.287 / +0.044 | 1.5 | -0.016 (-0.43) | -0.001 | edge,no | fail | 30 (13) | -0.36 / -0.44 | 0.75 | +0.04 / -0.04 / -0.02 | opposite |
| 1 | MF4-h40-open-flowsell | 1675/981 | -0.146 / -0.072 | 1.5 | +0.015 (1.12) | -0.009 | edge,yes | fail | 22 (7) | +0.05 / -0.03 | 1.5 | -0.23 / -0.06 / +0.02 | same |
| 1 | NS1-rsidip-rsi5pop-long | 167/169 | -0.008 / +0.041 | 1.5 | -0.031 (-1.21) | -0.018 | edge,no | fail | 22 (10) | +0.07 / -0.09 | 0.9 | -0.03 / +0.01 / -0.04 | opposite |
| 1 | MF2-open-rsimidhi-flowsell | 233/219 | -0.182 / -0.017 | 1.5 | -0.059 (-1.31) | -0.065 | edge,no | fail | 16 (6) <20 | -0.49 / -0.45 | 1.1 | +0.09 / +0.13 / +0.04 | same |
| 2 | CWT12-coil-k4-long | 7684/4636 | -0.066 / -0.097 | 1.5 | +0.037 (3.84) | +0.005 | edge,yes | pass(size) | 706 (21) | -0.08 / -0.10 | 1.25 | -0.02 / +0.02 / +0.02 | same |
| 2 | CWT12-coil-k6-long | 1772/1064 | -0.151 / -0.160 | 1.5 | +0.007 (0.32) | -0.046 | edge,yes | fail | 206 (18) | -0.12 / -0.22 | 0.75 | +0.06 / -0.06 / -0.06 | opposite |
| 2 | NM-ETF-late-dip-di-long | not covered |  |  |  |  |  |  | 17 (8) <20 | +0.31 / +0.28 | 0.9 | -0.05 / -0.06 / -0.10 |  |
| 2 | CWT09-gapdn-vwaploss-g10-short | not covered |  |  |  |  |  |  | 15 (8) <20 | +0.33 / +0.23 | 0.75 | +0.06 / -0.10 / -0.17 |  |
| 2 | GEN-261027-01-MACDhge0p12-Ret15mATRlem0... | 3511/1298 | +0.061 / -0.024 | 0.75 | -0.034 (-2.20) | -0.026 | edge,no | fail | 11 (4) <20 | +0.17 / +0.10 | 0.75 | +0.09 / -0.05 / -0.05 | same |


## All other setups (by live trade count)
| P | setup | lab n tr/va | lab R tr / va (k=1) | best k TRAIN | VALID d (t) | stop eff. VALID | plateau | verdict | live n (sess) | live R / w/o best day | live best k | live d k0.75 / k1.25 / k1.5 | lab vs live |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | CWT14-failbrk-orl-p05-long | 72790/41716 | -0.103 / -0.090 | 1.5 | +0.030 (6.56) | -0.000 | edge,yes | fail | 957 (21) | -0.15 / -0.17 | 1.5 | -0.05 / +0.02 / +0.03 | same |
| 3 | CWT14-failbrk-pdl-p05-long | 34897/20554 | -0.091 / -0.091 | 1.5 | +0.036 (7.30) | +0.006 | edge,yes | pass(size) | 852 (21) | -0.08 / -0.10 | 1.5 | -0.03 / +0.00 / +0.01 | same |
| 3 | CWT14-failbrk-orl-p05-lowvol-long | 54615/31699 | -0.099 / -0.088 | 1.5 | +0.030 (6.06) | +0.001 | edge,yes | pass(size) | 848 (21) | -0.18 / -0.20 | 1.5 | -0.05 / +0.03 / +0.05 | same |
| 3 | heat_fade_short-FD | not covered |  |  |  |  |  |  | 677 (21) | -0.07 / -0.11 | 0.9 | +0.01 / +0.01 / +0.00 |  |
| 3 | CWT14-failbrk-pdl-p05-lowvol-long | 24885/15042 | -0.092 / -0.094 | 1.5 | +0.036 (6.97) | +0.005 | edge,yes | pass(size) | 611 (21) | -0.12 / -0.14 | 1.5 | -0.03 / -0.00 / +0.02 | same |
| 3 | CWT14-failbrk-orl-p10-lowvol-long | 23972/13931 | -0.105 / -0.082 | 1.5 | +0.032 (5.22) | +0.005 | edge,yes | pass(size) | 556 (21) | -0.12 / -0.15 | 1.5 | -0.04 / +0.02 / +0.04 | same |
| 3 | CWT14-failbrk-orl-p10-long | 28857/17334 | -0.113 / -0.076 | 1.5 | +0.027 (4.39) | +0.001 | edge,yes | pass(size) | 543 (21) | -0.16 / -0.18 | 1.5 | -0.02 / +0.03 / +0.04 | same |
| 3 | CWT14-failbrk-pdl-p10-long | 19880/11687 | -0.091 / -0.087 | 1.5 | +0.034 (5.18) | +0.005 | edge,yes | pass(size) | 543 (21) | -0.09 / -0.12 | 1.1 | -0.02 / -0.00 / -0.01 | same |
| 3 | CWT14-failbrk-pdh-p05-lowvol-short | 25881/14496 | -0.112 / -0.068 | 1.5 | +0.034 (6.87) | +0.012 | edge,yes | PASS+stop | 473 (21) | -0.18 / -0.19 | 1.5 | -0.04 / +0.04 / +0.05 | same |
| 3 | CWT14-failbrk-pdh-p10-short | 16457/9604 | -0.105 / -0.049 | 1.5 | +0.030 (4.95) | +0.014 | edge,yes | PASS+stop | 464 (21) | -0.20 / -0.24 | 1.5 | -0.03 / +0.01 / +0.02 | same |
| 3 | RW7-gapdn-bounce-early-short-FD | 12964/7746 | -0.083 / -0.035 | 1.5 | +0.011 (1.14) | -0.001 | edge,yes | fail | 436 (19) | +0.06 / +0.03 | 0.9 | -0.01 / -0.01 / -0.02 | opposite |
| 3 | RW2-exhaustion-noon-adv150-short-FD | 9878/7098 | -0.100 / -0.019 | 1.5 | +0.011 (1.04) | +0.004 | edge,yes | fail | 426 (21) | -0.26 / -0.31 | 1.5 | -0.05 / +0.03 / +0.04 | same |
| 3 | LIQ-orl-sweep-open15-s25-long | not covered |  |  |  |  |  |  | 299 (20) | -0.11 / -0.18 | 1.25 | -0.06 / +0.03 / +0.02 |  |
| 3 | ST2-slope20up-long-am-t05s1-FD | 4243/4125 | -0.057 / +0.012 | 1.5 | +0.003 (0.26) | +0.007 | edge,no | fail | 256 (20) | -0.19 / -0.22 | 1.5 | -0.09 / +0.04 / +0.05 | same |
| 3 | heat_fade_long-FD | not covered |  |  |  |  |  |  | 243 (21) | -0.33 / -0.38 | 1.5 | -0.01 / +0.04 / +0.06 |  |
| 3 | CWT14-failbrk-pdh-p10-lowvol-short | 13003/7471 | -0.103 / -0.053 | 1.5 | +0.026 (3.94) | +0.008 | edge,yes | pass(size) | 230 (20) | -0.20 / -0.24 | 1.5 | -0.01 / +0.02 / +0.03 | same |
| 3 | GEN-261021-02-BarRngATRge0p14-PDLdistle... | 1884/1204 | +0.209 / +0.114 | 0.75 | -0.115 (-1.98) | -0.153 | edge,no | fail | 212 (4) | +0.04 / -0.22 | 0.75 | +0.03 / -0.06 / -0.09 | same |
| 3 | NS2-sma50break-overbought-short-FD | 3487/3001 | -0.045 / -0.081 | 1.5 | +0.031 (2.63) | +0.004 | edge,yes | pass(size) | 178 (20) | -0.28 / -0.32 | 1.1 | -0.06 / +0.01 / +0.01 | same |
| 3 | CWT13-vwapstretch-z05-short | 8572/4956 | -0.073 / -0.070 | 1.5 | +0.025 (2.26) | +0.002 | edge,yes | pass(size) | 173 (18) | -0.15 / -0.19 | 1.5 | -0.03 / +0.05 / +0.08 | same |
| 3 | exhaustion_short-FD | 12760/9033 | -0.110 / -0.028 | 1.5 | +0.015 (1.55) | +0.005 | edge,yes | fail | 170 (19) | -0.06 / -0.14 | 1 | -0.04 / -0.01 / -0.03 | one-neutral |
| 3 | GEN-261021-06-ORBfailUp-Gapge1p2-MID-BR... | not covered |  |  |  |  |  |  | 167 (8) | -0.25 / -0.39 | 1.5 | -0.02 / -0.00 / +0.03 |  |
| 3 | GEN-261029-08-Ret15mlem0p36-Flow3lem0p5... | not covered |  |  |  |  |  |  | 164 (4) | -0.37 / -0.79 | 0.9 | +0.00 / -0.05 / -0.10 |  |
| 3 | RW4-ns3-adv150-short-FD | 5494/5075 | +0.006 / -0.001 | 1.5 | +0.018 (0.93) | +0.018 | edge,yes | fail | 160 (19) | -0.20 / -0.26 | 1.25 | -0.05 / +0.05 / +0.05 | same |
| 3 | RW3S-gapdn-flowsell-short-FD | 14444/9919 | -0.075 / -0.027 | 1.5 | +0.015 (1.66) | +0.006 | edge,yes | fail | 143 (5) | -0.28 / -0.29 | 1 | -0.06 / -0.06 / -0.04 | one-neutral |
| 3 | CWT09-gapdn-bounce-g5-lowerhalf-short | not covered |  |  |  |  |  |  | 141 (15) | -0.02 / -0.11 | 0.75 | +0.04 / -0.06 / -0.09 |  |
| 3 | GEN-261020-07-RSIslopege19-LowWickge0p3... | not covered |  |  |  |  |  |  | 126 (6) | -0.31 / -0.49 | 0.75 | +0.04 / +0.01 / +0.03 |  |
| 3 | MF5-flowsell-vwapup-rsi5hi-FD | 3927/1737 | -0.096 / -0.001 | 1.5 | +0.010 (0.66) | +0.010 | edge,yes | fail | 120 (20) | -0.27 / -0.34 | 1.5 | +0.02 / +0.04 / +0.06 | same |
| 3 | MF1-945-flowsell-vwapup-FD | 5921/2752 | -0.201 / -0.129 | 1.5 | +0.041 (2.44) | -0.002 | edge,yes | fail | 110 (21) | -0.21 / -0.30 | 1 | -0.11 / -0.08 / -0.09 | one-neutral |
| 3 | RW1-gapdn-bounce-flowsell-short-FD | 3620/2182 | -0.073 / -0.011 | 1.5 | +0.001 (0.12) | -0.002 | edge,no | fail | 108 (20) | +0.09 / +0.04 | 1.25 | -0.02 / +0.01 / -0.02 | same |
| 3 | CWT09-gapdn-vwaploss-g5-short | 2239/1409 | -0.191 / -0.134 | 1.5 | +0.018 (0.64) | -0.026 | edge,yes | fail | 107 (14) | -0.06 / -0.41 | 0.9 | -0.23 / -0.10 / -0.11 | opposite |
| 3 | GEN-261021-07-VWAPxUp-ORBfailUp-AM-SPYg... | not covered |  |  |  |  |  |  | 103 (4) | -0.10 / -0.29 | 1 | -0.01 / -0.09 / -0.14 |  |
| 3 | RW6-ns2-up3-short-FD | 1967/1621 | +0.025 / -0.062 | 0.9 | -0.009 (-1.19) | -0.002 | no | fail | 103 (18) | -0.24 / -0.36 | 1.5 | -0.05 / +0.01 / +0.02 | opposite |
| 3 | GEN-261022-08-EMAdChglem0p094-Flow3ge1-... | not covered |  |  |  |  |  |  | 83 (5) | -0.29 / -0.57 | 0.75 | +0.06 / +0.00 / -0.06 |  |
| 3 | NS1-rsidip-rsi5pop-long-FD | 1008/874 | -0.075 / -0.064 | 1.5 | +0.011 (0.80) | -0.010 | edge,yes | fail | 82 (18) | -0.06 / -0.14 | 1.25 | -0.09 / +0.01 / +0.00 | same |
| 3 | CWT14-failbrk-pdl-p05-R2A-long | not covered |  |  |  |  |  |  | 75 (4) | -0.19 / -0.22 | 1.5 | -0.08 / +0.03 / +0.04 |  |
| 3 | GEN-261020-05-ORBfailDn-VWAPcrossesge4-... | not covered |  |  |  |  |  |  | 75 (7) | +0.02 / -0.02 | 1.1 | +0.01 / +0.04 / +0.03 |  |
| 3 | GEN-261020-09-EMAdChgge0p093-Z12lem0p82... | not covered |  |  |  |  |  |  | 73 (3) | +0.02 / -0.80 | 0.75 | +0.33 / +0.09 / +0.11 |  |
| 3 | L3-gap-slope-lowdist-FD | 2193/1215 | -0.149 / -0.093 | 1.5 | +0.058 (1.97) | +0.026 | edge,yes | pass(size) | 72 (14) | +0.07 / -0.07 | 1.25 | -0.03 / +0.00 / -0.01 | same |
| 3 | GEN-261026-05-Ret15mATRge0p042-FromPCAT... | not covered |  |  |  |  |  |  | 67 (6) | -0.92 / -0.97 | 1.5 | -0.09 / +0.12 / +0.18 |  |
| 3 | GEN-261026-07-Flow3ge0p56-BBpctge0p98-A... | not covered |  |  |  |  |  |  | 65 (3) | -0.04 / -0.13 | 0.75 | +0.03 / +0.02 / -0.03 |  |
| 3 | CWT05-flush-m05-v3-long | 1873/955 | -0.149 / -0.112 | 1.5 | +0.074 (3.49) | +0.036 | edge,yes | PASS+stop | 63 (15) | -0.17 / -0.24 | 0.75 | +0.03 / -0.01 / -0.02 | opposite |
| 3 | NS5-sma50-flush-oversold-long-FD | 1497/971 | -0.100 / +0.048 | 1 |  |  |  | keep 1.0 | 63 (20) | -0.32 / -0.42 | 1.5 | +0.03 / +0.05 / +0.09 | one-neutral |
| 3 | GEN-261022-09-Ret15mATRlem0p16-BarRngAT... | not covered |  |  |  |  |  |  | 57 (1) | -0.75 / +0.00 | 1 | -0.07 / -0.42 / -0.71 |  |
| 3 | GEN-261022-07-Z12lem1p9-FlowShiftlem0p9... | 1359/945 | +0.035 / -0.035 | 0.75 | -0.028 (-1.27) | -0.016 | edge,no | fail | 55 (7) | +0.18 / -0.21 | 0.9 | +0.00 / -0.08 / -0.12 | same |
| 3 | NM-AR-AM-gapdown-capitulation-long | 741/539 | +0.328 / +0.210 | 0.75 | +0.014 (0.35) | -0.056 | edge,yes | fail | 54 (8) | -0.45 / -0.59 | 1.5 | -0.02 / +0.04 / +0.12 | opposite |
| 3 | ST1-ordn-long-pm-t05s1-FD | 769/513 | -0.042 / -0.055 | 1.5 | +0.007 (0.44) | -0.011 | edge,no | fail | 54 (15) | -0.31 / -0.51 | 1 | -0.05 / -0.02 / -0.02 | one-neutral |
| 3 | GEN-261019-05-RSIslopelem9-PDLdistle0p1... | 895/795 | +0.067 / -0.077 | 1.5 | +0.013 (0.21) | -0.013 | edge,no | fail | 53 (2) | -1.00 / -1.00 | 1.25 | -0.03 / +0.11 / +0.07 | same |
| 3 | GEN-261028-08-Ret5mge0p21-SMA20dlem0p16... | not covered |  |  |  |  |  |  | 53 (2) | -0.26 / -0.26 | 1.5 | +0.05 / +0.05 / +0.11 |  |
| 3 | GEN-261028-09-FlowShiftlem0p65-ADX7le23... | 1530/564 | -0.007 / +0.020 | 1.5 | -0.016 (-0.60) | -0.009 | edge,no | fail | 53 (3) | -0.34 / -0.41 | 1.5 | +0.02 / -0.00 / +0.08 | same |
| 3 | GEN-261020-03-MACDhge0p079-BarsSinceLOD... | 963/333 | +0.084 / +0.022 | 1.25 | +0.007 (0.34) | +0.011 | yes | fail | 52 (2) | -0.73 / -1.16 | 0.9 | -0.03 / -0.08 / -0.01 | opposite |
| 3 | RW6G1-ns2-up3-vwap2sd-short-FD | not covered |  |  |  |  |  |  | 51 (15) | -0.03 / -0.17 | 0.9 | -0.04 / -0.01 / -0.02 |  |
| 3 | NM-HL-T75-pm-long | 893/591 | +0.052 / -0.003 | 0.75 | -0.012 (-0.60) | -0.011 | edge,no | fail | 50 (9) | -0.02 / -0.10 | 1.1 | -0.02 / +0.01 / +0.00 | opposite |
| 3 | GEN-261019-04-EMAdChgge0p15-RSI14le22-M... | 1177/811 | +0.112 / -0.001 | 0.9 | -0.007 (-0.61) | -0.007 | no | fail | 49 (5) | -0.13 / -0.50 | 0.75 | +0.08 / -0.13 / -0.21 | same |
| 3 | GEN-261022-05-MACDhge0p079-UpWickge0p71... | not covered |  |  |  |  |  |  | 49 (2) | -0.58 / -1.05 | 1.5 | -0.05 / +0.05 / +0.09 |  |
| 3 | intraday_momentum | not covered |  |  |  |  |  |  | 49 (19) | -0.35 / -0.38 | 1.5 | -0.07 / +0.07 / +0.12 |  |
| 3 | GEN-261029-06-EMAdChgge0p092-DayRngVsPr... | 4529/2274 | +0.020 / -0.027 | 1.5 | +0.023 (1.28) | +0.014 | edge,yes | fail | 48 (4) | -0.10 / -0.20 | 0.9 | -0.02 / -0.03 / -0.04 | opposite |
| 3 | GEN-261019-10-FlowShiftge0p42-SMA50dge1... | 2416/2038 | +0.010 / +0.058 | 1.1 | +0.000 (0.03) | +0.005 | yes | fail | 47 (7) | -0.03 / -0.33 | 0.75 | +0.11 / +0.04 / +0.05 | opposite |
| 3 | GEN-261027-05-VolRatioge1p5-ORLdistge0p... | 1289/663 | +0.051 / +0.025 | 1.1 | +0.007 (1.15) | +0.009 | no | fail | 47 (3) | -0.10 / -0.23 | 0.75 | +0.04 / -0.02 / -0.02 | opposite |
| 3 | GEN-261029-01-ORBfailUp-RSI14le41-ADX7l... | not covered |  |  |  |  |  |  | 45 (3) | -0.61 / -0.66 | 1.5 | -0.09 / +0.02 / +0.06 |  |
| 3 | NS3V1-am-widestop-short | 876/684 | +0.003 / +0.077 | 1.5 | -0.018 (-0.97) | +0.008 | edge,no | fail | 42 (6) | -0.28 / -0.51 | 1.5 | +0.00 / +0.01 / +0.04 | same |
| 3 | CWT13-vwapstretch-z075-long | 2391/1101 | -0.054 / +0.044 | 0.9 | -0.013 (-1.37) | -0.018 | no | fail | 40 (9) | -0.09 / -0.17 | 1 | -0.02 / -0.12 / -0.16 | one-neutral |
| 3 | GEN-261022-01-ORBfailUp-ATRdge7p9-Eff6g... | not covered |  |  |  |  |  |  | 40 (6) | -0.14 / -0.38 | 0.75 | +0.04 / -0.09 / -0.15 |  |
| 3 | GEN-261026-10-ORBfailDn-EMAdChglem0p051... | 11434/3186 | -0.004 / -0.001 | 1.5 | +0.003 (0.13) | +0.003 | edge,yes | fail | 39 (3) | -0.18 / -0.37 | 1.25 | -0.04 / +0.02 / +0.02 | same |
| 3 | GEN-261027-08-ORBfailDn-FromPCATRlem0p9... | not covered |  |  |  |  |  |  | 37 (2) | +0.20 / +0.16 | 1 | -0.00 / -0.07 / -0.11 |  |
| 3 | GEN-261026-06-NewLOD-SMA20slopelem0p28-... | 911/408 | +0.014 / +0.117 | 1.1 | +0.009 (0.94) | +0.020 | yes | fail | 35 (3) | +0.04 / -0.39 | 0.75 | +0.05 / -0.03 / -0.03 | opposite |
| 3 | ST4-emadn-long-am-t1s05-FD | 508/464 | -0.086 / +0.097 | 1.5 | -0.053 (-1.22) | -0.021 | edge,no | fail | 35 (11) | -0.07 / -0.38 | 1.1 | +0.01 / -0.02 / -0.03 | same |
| 3 | GEN-261027-06-ORBfailUp-BarsSinceLODle5... | not covered |  |  |  |  |  |  | 33 (3) | -0.35 / -0.46 | 1.1 | +0.08 / +0.14 / +0.04 |  |
| 3 | GEN-261029-02-RSI2le0-VWAPcrossesge9-Da... | not covered |  |  |  |  |  |  | 32 (5) | -0.23 / -0.26 | 1.5 | -0.08 / +0.01 / +0.02 |  |
| 3 | NS4-pm-vwap-reclaim-oversold-short-FD | 715/615 | -0.212 / -0.011 | 1.5 | +0.035 (1.22) | +0.031 | edge,yes | fail | 32 (13) | +0.07 / -0.08 | 0.75 | +0.17 / +0.01 / -0.04 | opposite |
| 3 | GEN-261028-02-VWAPxDn-NewLOD-AM-QQQgt0p... | 470/494 | +0.052 / +0.064 | 1.1 | -0.013 (-1.21) | -0.007 | no | fail | 31 (3) | -0.15 / -0.19 | 0.75 | +0.04 / -0.12 / -0.20 | opposite |
| 3 | GEN-261029-03-MACDhlem0p12-Ret5mlem0p06... | not covered |  |  |  |  |  |  | 30 (3) | -0.01 / -0.07 | 1.25 | -0.03 / +0.02 / +0.01 |  |
| 3 | GEN-261027-10-FlowShiftlem1p2-MACDhge0p... | not covered |  |  |  |  |  |  | 29 (3) | -0.58 / -0.74 | 0.9 | -0.11 / +0.01 / +0.00 |  |
| 3 | NM-MF3-qqqdn-gapdn-FD | 991/701 | -0.010 / +0.004 | 1.5 | +0.002 (0.12) | +0.004 | edge,no | fail | 26 (5) | +0.31 / -0.46 | 0.75 | +0.17 / -0.03 / -0.09 | opposite |
| 3 | CWT13-vwapstretch-z075-short | 1562/737 | -0.090 / -0.056 | 1.5 | +0.010 (0.46) | -0.009 | edge,no | fail | 25 (7) | -0.04 / -0.20 | 1 | -0.23 / -0.04 / -0.05 | one-neutral |
| 3 | GEN-261019-01-VWAPxUp-ATRdge3p6-FromPCA... | 572/336 | +0.135 / +0.177 | 1 |  |  |  | keep 1.0 | 25 (5) | -0.27 / -0.42 | 1.25 | -0.25 / +0.17 / +0.09 | one-neutral |
| 3 | GEN-261019-03-Ret15mATRlem0p12-FromOpen... | 1469/636 | +0.090 / +0.100 | 0.75 | -0.009 (-0.47) | -0.042 | edge,no | fail | 25 (6) | +0.22 / -0.09 | 0.9 | -0.06 / -0.07 / -0.11 | same |
| 3 | GEN-261027-09-ORBfailDn-Gapge2-Slope6ge... | 1197/890 | +0.033 / +0.069 | 1.5 | +0.010 (0.43) | +0.034 | edge,no | fail | 25 (3) | -0.63 / -0.82 | 1.5 | -0.19 / -0.06 / +0.02 | same |
| 3 | GEN-261023-03-RSI5le13-VWAPatrlem0p34-O... | not covered |  |  |  |  |  |  | 23 (4) | -0.31 / -0.47 | 0.75 | +0.19 / -0.11 / -0.22 |  |
| 3 | ST8-volspikedn-long-pm-t1s1-FD | 161/244 | -0.004 / +0.115 | 0.9 | -0.004 (-0.25) | -0.017 | no | fail | 22 (10) | -0.21 / -0.33 | 0.9 | -0.03 / -0.04 / -0.04 | same |
| 3 | CWT12-flag-s1-long | 808/374 | -0.031 / -0.128 | 1.5 | +0.028 (1.28) | -0.015 | edge,yes | fail | 21 (12) | -0.14 / -0.22 | 1.5 | -0.28 / -0.03 / +0.01 | same |
| 3 | GEN-261022-04-RSI2le0-Eff6ge0p83-SMA20d... | 548/280 | +0.119 / -0.045 | 0.9 | -0.037 (-1.63) | -0.032 | no | fail | 21 (4) | -0.76 / -0.84 | 0.75 | +0.00 / -0.01 / -0.01 | same |
| 3 | GEN-261023-04-EMAdChglem0p028-PDHdistle... | 404/247 | +0.092 / +0.048 | 1 |  |  |  | keep 1.0 | 21 (3) | -0.29 / -0.34 | 1.5 | -0.05 / +0.07 / +0.08 | one-neutral |
| 3 | GEN-261026-03-NewLOD-Flow3lem0p37-FromO... | not covered |  |  |  |  |  |  | 21 (5) | +0.38 / +0.13 | 0.75 | +0.00 / -0.17 / -0.16 |  |
| 3 | CWT05-flush-m075-v3-long | 716/317 | -0.169 / -0.087 | 1.5 | +0.110 (2.66) | +0.081 | edge,yes | PASS+stop | 20 (10) | -0.23 / -0.29 | 0.75 | +0.08 / +0.00 / -0.04 | opposite |
| 3 | CWT04-backside-lh-a15-short | 775/229 | +0.305 / -0.234 | 0.9 | -0.024 (-1.18) | +0.002 | no | fail |  |  |  |  |  |
| 3 | CWT04-backside-vwaptest-a15-short | 1199/412 | -0.431 / -0.232 | 1.5 | +0.074 (1.76) | -0.003 | edge,yes | fail |  |  |  |  |  |
| 3 | CWT05-flush-m05-v5-long | 641/341 | -0.112 / -0.104 | 1.5 | +0.074 (2.56) | +0.039 | edge,yes | PASS+stop |  |  |  |  |  |
| 3 | CWT05-flush-m075-v5-long | 316/149 | -0.105 / -0.012 | 1.5 | +0.058 (1.51) | +0.054 | edge,yes | fail |  |  |  |  |  |
| 3 | GEN-261019-02-BBpctle0p017-SMA20slopege... | 270/243 | +0.020 / -0.014 | 1.1 | -0.008 (-1.59) | -0.009 | no | fail |  |  |  |  |  |
| 3 | GEN-261019-07-VolRatioge2-UpWickge0p59-... | 860/351 | +0.035 / -0.042 | 1.25 | +0.018 (1.56) | +0.010 | no | fail |  |  |  |  |  |
| 3 | GEN-261019-09-EMAdChgge0p15-Since950ATR... | 560/242 | +0.035 / -0.073 | 1.25 | +0.003 (0.21) | -0.011 | yes | fail |  |  |  |  |  |
| 3 | GEN-261020-01-MACDhge0p12-RSI5le25-PM-B... | 757/348 | +0.137 / -0.131 | 0.75 | -0.047 (-1.04) | -0.003 | edge,no | fail |  |  |  |  |  |
| 3 | GEN-261020-04-MACDhge0p12-BullDiv-MID-S... | 313/290 | -0.027 / +0.037 | 1.5 | +0.008 (0.30) | +0.021 | edge,yes | fail |  |  |  |  |  |
| 3 | GEN-261020-08-FlowShiftlem0p41-Compress... | 189/46 | +0.411 / +0.257 | 0.75 | -0.093 (-0.52) | -0.179 | edge,no | fail |  |  |  |  |  |
| 3 | GEN-261021-03-RSI5le34-Ret15mATRge0p12-... | 436/125 | -0.005 / -0.009 | 1.5 | +0.039 (0.75) | +0.036 | edge,yes | fail |  |  |  |  |  |
| 3 | GEN-261021-05-RSIslopelem14-ORHdistge0p... | 492/181 | +0.215 / -0.048 | 0.9 | -0.068 (-1.75) | -0.062 | no | fail |  |  |  |  |  |
| 3 | GEN-261021-09-RSIslopelem19-ORHdistlem0... | 447/125 | -0.035 / +0.031 | 1.25 | +0.032 (0.64) | +0.038 | yes | fail |  |  |  |  |  |
| 3 | GEN-261021-10-MACDhge0p079-VWAPbarslem7... | 64/29 | +0.243 / +0.406 | 0.9 | -0.018 (-0.17) | -0.064 | no | fail |  |  |  |  |  |
| 3 | GEN-261022-02-ORBfailUp-EMAdChglem0p094... | 980/331 | +0.014 / +0.002 | 1.1 | -0.008 (-1.18) | -0.007 | no | fail |  |  |  |  |  |
| 3 | GEN-261022-03-NewHOD-Ret15mATRge0p12-SM... | 745/519 | +0.018 / +0.033 | 1.5 | +0.009 (0.46) | +0.020 | edge,yes | fail |  |  |  |  |  |
| 3 | GEN-261022-06-NewLOD-ORBfailUp-BuyPress... | 557/160 | +0.136 / +0.058 | 0.75 | -0.013 (-0.36) | -0.033 | edge,no | fail |  |  |  |  |  |
| 3 | GEN-261023-06-RSI7le38-Ret15mge0p54-EMA... | 227/173 | +0.155 / -0.084 | 1.1 | +0.048 (1.31) | +0.041 | yes | fail |  |  |  |  |  |
| 3 | GEN-261023-08-RSIslopelem5p5-VWAPcrosse... | 621/151 | +0.132 / +0.100 | 0.75 | -0.022 (-0.44) | -0.055 | edge,no | fail |  |  |  |  |  |
| 3 | GEN-261026-02-VolRatioge2-SMA20dlem0p58... | 806/212 | +0.036 / -0.043 | 0.9 | -0.014 (-1.02) | -0.009 | no | fail |  |  |  |  |  |
| 3 | GEN-261027-04-VWAPatrge0-Gaplem2-FromOp... | 1070/425 | +0.102 / +0.029 | 1.25 | +0.003 (0.18) | +0.009 | no | fail |  |  |  |  |  |
| 3 | GEN-261027-07-RSI14le35-FromOpenge2-AM-... | 697/603 | +0.064 / -0.072 | 0.9 | -0.026 (-1.52) | -0.018 | no | fail |  |  |  |  |  |
| 3 | GEN-261029-05-BearDiv-RSI14ge78-Compres... | 122/7 | +0.408 / +0.654 | 0.75 | -0.132 (-0.38) | -0.350 | edge,no | fail |  |  |  |  |  |
| 3 | GEN-261029-07-UpWickge0p59-DayRngVsPrev... | 770/341 | -0.006 / -0.032 | 1.25 | +0.011 (0.80) | +0.004 | yes | fail |  |  |  |  |  |
| 3 | GEN-261029-10-RSIslopege19-Ret5mlem0p21... | 65/38 | +0.368 / +0.337 | 0.9 | +0.007 (0.12) | -0.030 | yes | fail |  |  |  |  |  |
| 3 | NM-AMS-N1-quiet-morning-short | 195/139 | +0.184 / +0.046 | 1 |  |  |  | keep 1.0 |  |  |  |  |  |
| 3 | NM-PM-gapdn-above-pdh-rvol-short | 274/118 | +0.320 / +0.144 | 0.75 | +0.018 (0.35) | -0.030 | edge,yes | fail |  |  |  |  |  |
| 3 | NM-RWN3-ns3-spyup-early-short | 176/91 | +0.195 / +0.225 | 1.25 | -0.011 (-0.22) | +0.034 | no | fail |  |  |  |  |  |
| 3 | NM-RWN4-ns2-spyup05-notfri-short | 604/177 | +0.098 / -0.001 | 0.75 | -0.013 (-0.40) | -0.012 | edge,no | fail |  |  |  |  |  |
| 3 | NM-RWN5-ns3-mon-weakrs-short | 173/56 | +0.157 / +0.358 | 0.75 | -0.093 (-1.20) | -0.213 | edge,no | fail |  |  |  |  |  |
| 3 | NM-RWR1-exh150-gapdn-spyup-pm-short | 326/220 | +0.121 / +0.171 | 1.1 | -0.014 (-1.12) | +0.002 | no | fail |  |  |  |  |  |
| 3 | NM-RWR3-ns3-qqqup-early-short | 157/88 | +0.251 / +0.315 | 1 |  |  |  | keep 1.0 |  |  |  |  |  |
| 3 | NM-RWR4-ns2-up3-qqqup-slopedn-short | 383/173 | +0.121 / +0.053 | 0.75 | +0.003 (0.09) | -0.015 | edge,yes | fail |  |  |  |  |  |
| 3 | NM1-cwt09-g10-vwaploss-short | 181/105 | -0.028 / +0.335 | 1.5 | -0.085 (-1.49) | +0.027 | edge,no | fail |  |  |  |  |  |
| 3 | ST3-rsi5up-short-pm-t1s1-FD | 206/231 | -0.025 / +0.060 | 1.5 | -0.021 (-0.78) | -0.001 | edge,no | fail |  |  |  |  |  |
| 3 | ST5-pdbrkup-short-mid-t05s1-FD | 306/275 | -0.079 / -0.024 | 1.5 | +0.068 (2.01) | +0.060 | edge,yes | PASS+stop |  |  |  |  |  |
| 3 | ST6-volspikeup-short-mid-t1s1-FD | 215/312 | -0.094 / +0.012 | 1.5 | +0.029 (1.00) | +0.033 | edge,yes | fail |  |  |  |  |  |
| 3 | ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD | 183/230 | +0.092 / +0.172 | 1.25 | -0.034 (-1.34) | +0.001 | no | fail |  |  |  |  |  |


## Next steps (optimistic, and honest about the evidence)
1. **L3-gap-slope-fromopen-FD at k=1.25..1.5** is the one setup where the lab says a wider stop turns it positive in
   both splits, and the stop effect is real (t 2.5). Before any proposal:
   - run B1, the 1-min live re-walk with the parity gate;
   - score HOLD once.
   Since the live approximation disagrees, this goes to `research/backlog.jsonl` as a lead, not a decision.
2. **Where stops matter, the gain comes from size.** For losing setups (CWT14 family), "trade smaller" is a sizing or
   demotion question for the owner, not a stop fix.
3. **The 57 uncovered setups** (hold / holdtr / S geometries, GEN hold setups) need a harness that understands their
   exits before stop width can be judged.

## Files
- `bt_width.py`: the lab walk (scratch output in /dev/shm/stopw_b).
- `live_approx.py`: B2.
- `analyze.py`: scoring.
- `regime.py`: SPY up/down split.
- `tables.py`: the markdown tables.
- Outputs: `inventory.csv`, `lab_setup_k.csv`, `global_k.csv`, `regime_k.csv`, `live_setup_k.csv`, `priority.csv`,
  `out.txt`.
