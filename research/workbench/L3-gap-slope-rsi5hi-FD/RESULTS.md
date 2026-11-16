# Workbench RESULTS — Gap-Down Rebound Overbought Short (all day) `L3-gap-slope-rsi5hi-FD` (On Deck) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16 (built ~13:10-14:30 ET, market hours: research files only; no config change, no deploy).

## Verdict
> **Recommended: `L3-gap-slope-rsi5hi-FD-WB4` = cost/R ≤ 0.05 + RSI(5) ≤ 90 + SMA20 slope ≤ 1.0** (three new entry clauses in the
> module; nothing else changes). Replay **+0.016 → +0.190R**, 2-year **+0.011 → +0.051R**; better in TRAIN, VALID and FWD; avg R
> w/o best day, worst day and total R all better in both tests. **PASS.** The sibling's parts (13:00 cut-off, 75-min max hold) were
> tested here and do NOT transfer: they lift the replay but lose on the 2-year (FAIL).

| copy | change (part) | replay avg R (parent +0.016) | 2-year avg R (parent +0.011) | w/o best day (replay / 2y; parent −0.108 / −0.017) | worst day (replay / 2y; parent −21.2 / −122.3R) | trades (replay / 2y; parent 327 / 6313) | verdict |
|---|---|---|---|---|---|---|---|
| `-WB1` | P16/P19 stop-exit cost ≤ 0.05 of 1R (module clause) | +0.061 | +0.033 | −0.063 / +0.011 | −10.0 / −64.1 | 210 / 3470 | PASS (contained in WB4) |
| `-WB2` | P11 SMA20 slope cap ≤ 1.0 | +0.061 | +0.018 | −0.060 / −0.013 | −16.9 / −91.2 | 266 / 5343 | PASS (contained in WB4) |
| `-WB3` | P9 RSI(5) cap ≤ 90 | +0.023 | +0.019 | −0.114 / −0.016 | −19.3 / −108.0 | 278 / 5397 | PASS (contained in WB4) |
| **`-WB4`** | **WB1 + WB2 + WB3** | **+0.190** | **+0.051** | **+0.079 / +0.021** | **−4.4 / −38.8** | 130 / 2374 | **PASS — recommended** |
| (sibling part) | P6 window ends 13:00 (V01) | +0.097 | −0.013 | −0.052 / −0.032 | −13.1 / −75.6 | 240 / 4167 | FAIL (2-year) |
| (sibling part) | P25 max hold 75 min (V04) | +0.051 | −0.001 | −0.027 / −0.030 | −10.0 / −124.6 | 327 / 6320 | FAIL (2-year) |

Pass rule (owner 2026-11-16): meets or exceeds the parent's avg R after costs in BOTH tests (meets = within 0.01R or ≥ 95%), and not
worse on avg R w/o best day by > 0.02R or on worst day by > 10%. Parent and copies scored by the identical pipeline; the parent's
live record is NOT used in the decision.

## Supervisor sign-off (WB4)
- **What changed:** three entry clauses, each a cap on something the parent left open — no thin-R names (stop-exit round trip
  2 × (1c + 1 bp) + 2c must be ≤ 5% of 1R, i.e. 1R ≥ ~$0.85 on a $20 stock), no RSI(5) above 90 (flat-top / parabolic pops), no
  near-vertical 20-bar slope above 1.0%. Exits, window, refire, sizing unchanged.
- **Why:** 4 of the 5 worst live trades were thin-R and/or RSI-100 bars; across 6,313 two-year trades those three slices are the
  ones that lose in most of replay / TRAIN / VALID / FWD. The gain is not only cost: gross R rises too (2y +0.028 → +0.064).
- **Overall before → after:** replay +0.016 → +0.190R (total +5.4 → +24.7R on 130 vs 327 trades; per session +0.24 → +1.12R),
  2-year +0.011 → +0.051R (total +67 → +120R on 2,374 vs 6,313 trades; TRAIN +0.008 → +0.075, VALID +0.020 → +0.031,
  FWD −0.066 → +0.096). Win 67 → 77% (replay) / 67 → 69% (2y); avg loss −0.93 → −0.81 / −0.94 → −0.88R; avg win unchanged
  (0.48-0.49R). Worst day −21.2 → −4.4R / −122.3 → −38.8R. Per $ traded 2y +5.1 → +10.3 bps.
- **Where it gives back:** (1) ~60% fewer trades — exposure drops; (2) it skips 4 of the 5 best live trades (OKLO, EWZ, RIOT,
  EMBJ) as well as 4 of the 5 worst; on the live record (diagnosis only) the kept 43 trades averaged +0.104R vs the dropped 95
  +0.114R — the live data do NOT confirm the cost/R part (live R on thin names is the most distorted by fill drift; RSI cap is
  live-confirmed); (3) still one-big-day heavy: replay best day 11-12 = 71% of total R, 2-year best day 2025-04-07 = 62%
  (`1 day` tag) — but w/o that day it is positive in both tests (+0.079 / +0.021) where the parent was negative (−0.108 / −0.017);
  (4) up-market days still ≈ 0 (2y up +0.003, flat +0.090, down +0.106); (5) paired-by-day t vs parent only +0.65 (replay) /
  +0.32 (2y) — below the counted bar 2.83 (55 configs); it passes on meet-or-exceed, not on significance.
- **Sign-off:** clear overall improvement after costs in both tests, every 2-year split and every tail measure; neighbours
  (cost 0.075, slope 0.85, RSI 85, + start 10:30, + price ≥ $20, + volume ≤ 2.5×) all land within ±0.02R — a plateau, not a
  tuned spike. Approved to leave the workbench.

## Ready to deploy after close (plan — NOT applied)
Testing account per rules 5 (not the parent's On Deck; twins rule) → **Testing E (`testinge`)**, FIRST in its priority order.
(Testing A already gets the sibling `L3-gap-slope-fromopen-FD-WB4`, a same-family gap-down fade short; Testing E spreads the family.)
1. `config/account_testinge.yaml`, under `strategies:` (block from `L3-gap-slope-rsi5hi-FD-WB4.yaml`):
   ```yaml
   L3-gap-slope-rsi5hi-FD-WB4:
     enabled: true
     refire: true
     refire_cooldown: 6
     type: lab
     module: research/workbench/L3-gap-slope-rsi5hi-FD/modules/L3-gap-slope-rsi5hi-FD-WB4.py
     min_adv: 0
     window: [950, 1500]
     prefilter: "gap_le:-2.6573517322540283"
     scale_out_r: null
     tags: [workbench, "parent:L3-gap-slope-rsi5hi-FD"]
   ```
   and put `L3-gap-slope-rsi5hi-FD-WB4` FIRST in `live.setup_order` (add the list if the account has none).
2. `config/setup_names.yaml`: `L3-gap-slope-rsi5hi-FD-WB4: {name: "Gap-Down Rebound Overbought Short (all day) — WB4: no thin-R names, RSI(5) ≤ 90, slope ≤ 1.0", side: short, what: "09:50-15:00: a stock that gapped down 2.7%+ is back above a rising 20-bar average (slope 0.6-1.0%) with RSI(5) 70-90, and 1R is at least 20x the stop-exit cost; short the pop. Target 0.5R, stop 1R, flat 15:55; re-fires after a 6-bar cooldown."}`
3. `research/ledger.jsonl`: id `2026-11-16-wb-l3-rsi5hi-wb4`, effective 2026-11-17, title "Workbench copy L3-gap-slope-rsi5hi-FD-WB4
   added to Testing E, first in setup_order (Mechanic PASS)", patch `{"strategies.L3-gap-slope-rsi5hi-FD-WB4 (testinge)": [null, "added, enabled"], "live.setup_order (testinge)": ["...", "WB4 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5"; then `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments`, `pytest -q`, commit, push after 16:05 ET (setup-freeze).
Notes: the parent stays in On Deck unchanged. Testing E runs ≤ 50 lots per setup (replay book 150; WB4 trades ~6/session in the
replay so the cap rarely binds) and keeps its own 0.15R cost filter (WB4's 0.05R clause is stricter, so it never binds).
The module's cost clause uses the signal-bar close and 1R = 0.25 × daily ATR (the setup's r_atr_frac); the runner's filter uses
the fill — the module clause is the stricter of the two by design.

## Method (identical for parent and every copy)
- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live in any account and
  passed the shortable+ETB check, 2026-10-13..11-13 (340 symbol-days, 22 sessions with signals). 1-min SIP bars (read-only GET) →
  lab frame (`mcf.report.engine.lab_frame` + daily priors as live). Copies only tighten conditions, so the universe covers them.
- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted), names
  shortable+ETB on ≥ 90% of the universe snapshots (E90 proxy, as the sibling). Splits TRAIN ≤ 2025-12-31, VALID 2026-01..10-05,
  FWD 10-06..11-04.
- Same engine for both (the sibling's harness, `code/sim.py`): signals on 5-min bar close (gap ≤ −2.657, slope > 0.5965, RSI(5) > 70,
  09:50-15:00, price ≥ $5), LabStrategy refire chain (cooldown 6), entry at the signal-bar close, exits walked on 1-min bars (stop
  first; 0.5R target fills only when traded through by ≥ $0.01; flat 15:55), **LR8 costs** (entry 1 bp + SEC + TAF + CAT; stop
  max($0.02, 4 bps); time exit max($0.01, 1 bp); target at limit), the Testing 0.15R cost filter, On Deck book (≤ 150 open lots,
  ≤ 3 per symbol, no per-setup latch).
- Rule changes inside the replay window (ledger): Primary −2R latch (10-29), CF 0.15R (10-30), moves 10-30 / 11-11 (TEAM-6), LR1/3/5/7
  and LR8 (11-12), On Deck build (11-12). The backtests apply today's rules to every session, so these do not mix into the comparison.
- **Configs counted: 55** (22 one-part tweaks in round 1 declared before any score; rounds 2-4 declared after the previous round —
  `code/decl.py`). Counted bar for the paired-by-day t: max(1.5, sqrt(2 ln 55)) = 2.83 — **no config clears it**; 39 of 55 pass the
  meet-or-exceed rule (the parent sits near 0R, so "meets" is easy), 16 fail. Every config is in the table below.

## Shape (2-year unless noted; SPY open→close > +0.25% up / < −0.25% down)
| config | test | avg win | avg loss | median hold min | stop | target | time | up-day avg R (n) | flat | down |
|---|---|---|---|---|---|---|---|---|---|---|
| parent | replay | +0.484 | −0.932 | 32 | 26% | 65% | 9% | −0.172 (113) | +0.072 | −0.636 (15) |
| parent | 2y | +0.480 | −0.937 | 28 | 28% | 64% | 8% | −0.043 (3278) | +0.075 | +0.063 |
| WB1 cost/R | 2y | +0.478 | −0.902 | 33 | 26% | 65% | 9% | −0.022 | +0.083 | +0.092 |
| WB2 slope cap | 2y | +0.480 | −0.930 | 30 | 27% | 65% | 8% | −0.035 | +0.066 | +0.079 |
| WB3 RSI cap | 2y | +0.480 | −0.929 | 29 | 27% | 65% | 8% | −0.029 | +0.079 | +0.065 |
| WB4 | replay | +0.489 | −0.806 | 26.5 | 15% | 76% | 9% | +0.124 (29) | +0.163 | −1.020 (3) |
| WB4 | 2y | +0.476 | −0.879 | 37 | 24% | 65% | 11% | +0.003 (1170) | +0.090 | +0.106 |
| V01 13:00 end | 2y | +0.482 | −0.967 | 28 | 30% | 64% | 6% | −0.056 | +0.047 | +0.017 |
| V04 hold 75 | 2y | +0.451 | −0.739 | 28.5 | 21% | 54% | 25% | −0.023 | +0.021 | +0.024 |

## Every configuration (ALL = whole test; TRAIN / VALID / FWD = 2-year avg R by split)
Configs counted: 55 (PARENT excluded; X10 re-run in round 4 counted once). Paired-by-day t bar max(1.5, sqrt(2 ln 55)) = 2.83.

| config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | TRAIN | VALID | FWD | t vs parent (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PARENT | 327 | +0.016 | -0.108 | -21.2 | 6313 | +0.011 | -0.017 | -122.3 | +0.008 | +0.020 | -0.066 | +0.00 / +0.00 | — |
| V01 window end 15:00->13:00 (P6) | 240 | +0.097 | -0.052 | -13.1 | 4167 | -0.013 | -0.032 | -75.6 | -0.006 | -0.022 | +0.017 | +1.24 / -0.76 | FAIL: 2y avg R -0.013 < parent +0.011 |
| V02 window end 15:00->14:00 (P6) | 266 | +0.037 | -0.116 | -16.7 | 5434 | -0.001 | -0.029 | -127.7 | -0.013 | +0.013 | -0.014 | +0.39 / -0.96 | FAIL: 2y avg R -0.001 < parent +0.011 |
| V03 window start 09:50->10:30 (P6/P7) | 320 | +0.020 | -0.104 | -21.2 | 6008 | +0.015 | -0.017 | -122.7 | +0.016 | +0.022 | -0.059 | +0.51 / +0.96 | PASS |
| V04 max hold 75 min (P25) | 327 | +0.051 | -0.027 | -10.0 | 6320 | -0.001 | -0.030 | -124.6 | +0.004 | -0.005 | -0.032 | +0.61 / -1.09 | FAIL: 2y avg R -0.001 < parent +0.011 |
| V05 max hold 60 min (P25) | 327 | +0.054 | -0.017 | -9.6 | 6320 | -0.004 | -0.032 | -115.8 | +0.004 | -0.010 | -0.027 | +0.56 / -1.10 | FAIL: 2y avg R -0.004 < parent +0.011 |
| V06 max hold 90 min (P25) | 327 | +0.043 | -0.043 | -10.0 | 6320 | +0.002 | -0.027 | -128.9 | +0.004 | +0.002 | -0.031 | +0.54 / -0.99 | PASS |
| V07 gap <=-2.66->-3.2 (P4+P10) | 282 | -0.015 | -0.151 | -18.0 | 4842 | +0.027 | -0.003 | -87.5 | +0.029 | +0.035 | -0.090 | -1.44 / +0.91 | FAIL: replay avg R -0.015 < parent +0.016; replay w/o best day -0.151 vs -0.108 |
| V08 slope >0.60->>0.70 (P11) | 252 | -0.006 | -0.134 | -20.4 | 4613 | +0.011 | -0.018 | -103.9 | +0.015 | +0.013 | -0.060 | -0.63 / -0.24 | FAIL: replay avg R -0.006 < parent +0.016; replay w/o best day -0.134 vs -0.108 |
| V09 RSI(5) >70->>80 (P9) | 232 | -0.031 | -0.116 | -19.7 | 4896 | +0.003 | -0.027 | -96.9 | -0.002 | +0.016 | -0.101 | -0.69 / -0.90 | FAIL: replay avg R -0.031 < parent +0.016 |
| V10 RSI(5) <100 (skip flat-top bars) (P9) | 316 | +0.028 | -0.097 | -18.0 | 6015 | +0.012 | -0.019 | -119.4 | +0.010 | +0.020 | -0.058 | +0.98 / +0.17 | PASS |
| V11 refire cooldown 6->3 bars (P8) | 394 | -0.006 | -0.119 | -26.7 | 7735 | -0.003 | -0.027 | -170.9 | -0.012 | +0.011 | -0.066 | -0.87 / -1.26 | FAIL: replay avg R -0.006 < parent +0.016; replay worst day -26.7R vs -21.2R; 2y avg R -0.003 < parent +0.011; 2y worst day -170.9R vs -122.3R |
| V12 refire cooldown 6->12 bars (P8) | 282 | +0.048 | -0.078 | -18.2 | 5035 | +0.004 | -0.024 | -78.2 | +0.006 | +0.012 | -0.091 | +1.27 / -0.58 | PASS |
| V13 lots per symbol 3->2 (P13) | 322 | +0.020 | -0.104 | -20.2 | 6225 | +0.011 | -0.017 | -119.3 | +0.010 | +0.018 | -0.060 | +0.66 / +0.01 | PASS |
| V14 lots per symbol 3->1 (P13) | 283 | +0.038 | -0.081 | -15.2 | 5442 | +0.014 | -0.018 | -78.8 | +0.028 | +0.004 | -0.030 | +0.65 / +0.15 | PASS |
| V15 geometry t05s1->t1s1 (target 1R) (P23) | 327 | +0.025 | -0.191 | -52.1 | 6204 | +0.042 | -0.004 | -129.2 | +0.080 | +0.016 | -0.103 | +0.07 / +1.18 | FAIL: replay w/o best day -0.191 vs -0.108; replay worst day -52.1R vs -21.2R |
| V16 geometry t05s1->t05s05 (stop 0.5R) (P22) | 327 | +0.062 | -0.027 | -6.5 | 6348 | -0.004 | -0.026 | -80.4 | -0.005 | -0.001 | -0.017 | +0.75 / -0.97 | FAIL: 2y avg R -0.004 < parent +0.011 |
| V17 1R 0.25->0.30 x ATR (P19) | 351 | +0.004 | -0.126 | -28.6 | 6540 | +0.018 | -0.010 | -120.0 | +0.025 | +0.021 | -0.102 | -0.46 / +1.17 | FAIL: replay avg R +0.004 < parent +0.016; replay worst day -28.6R vs -21.2R |
| V18 cost filter 0.15->0.10R (P16) | 275 | +0.050 | -0.063 | -12.8 | 5438 | +0.017 | -0.011 | -108.9 | +0.018 | +0.019 | -0.025 | +0.76 / +0.60 | PASS |
| V19 1R >= 1.0% of price (P1 intake) | 318 | +0.008 | -0.122 | -22.6 | 5709 | +0.012 | -0.015 | -118.0 | +0.009 | +0.023 | -0.087 | -1.86 / +0.14 | PASS |
| V20 skip SPY > +0.30% since 09:50 (gate) | 111 | -0.042 | -0.149 | -10.0 | 2915 | -0.019 | -0.047 | -125.0 | -0.080 | +0.034 | +0.033 | -0.25 / -0.62 | FAIL: replay avg R -0.042 < parent +0.016; replay w/o best day -0.149 vs -0.108; 2y avg R -0.019 < parent +0.011; 2y w/o best day -0.047 vs -0.017 |
| V21 skip SPY < -0.30% since 09:50 (gate) | 282 | -0.007 | -0.169 | -21.2 | 5692 | -0.004 | -0.037 | -117.7 | -0.026 | +0.023 | -0.076 | -1.07 / -1.19 | FAIL: replay avg R -0.007 < parent +0.016; replay w/o best day -0.169 vs -0.108; 2y avg R -0.004 < parent +0.011 |
| V22 price >= $5 -> >= $10 (P2) | 320 | +0.024 | -0.102 | -20.3 | 6260 | +0.011 | -0.016 | -117.3 | +0.008 | +0.020 | -0.058 | +1.66 / +0.33 | PASS |
| W01 cost filter 0.15->0.075R (P16) | 249 | +0.053 | -0.062 | -14.6 | 4704 | +0.021 | -0.005 | -89.6 | +0.026 | +0.021 | -0.045 | +0.68 / +0.40 | PASS |
| W02 cost filter 0.15->0.05R (P16) | 210 | +0.061 | -0.063 | -10.0 | 3470 | +0.033 | +0.011 | -64.1 | +0.039 | +0.032 | -0.009 | +0.41 / +0.35 | PASS |
| W03 RSI(5) <= 90 (P9 cap) | 278 | +0.023 | -0.114 | -19.3 | 5397 | +0.019 | -0.016 | -108.0 | +0.024 | +0.019 | -0.054 | +0.24 / +0.64 | PASS |
| W04 SMA20 slope <= 1.0 (P11 cap) | 266 | +0.061 | -0.060 | -16.9 | 5343 | +0.018 | -0.013 | -91.2 | +0.019 | +0.023 | -0.054 | +1.15 / +0.61 | PASS |
| W05 volumeRatio <= 2.5 (new sensor) | 324 | +0.013 | -0.114 | -21.2 | 6261 | +0.013 | -0.015 | -120.1 | +0.015 | +0.019 | -0.065 | -1.51 / +1.38 | PASS |
| W06 price >= $20 (P2) | 283 | +0.049 | -0.071 | -19.1 | 5703 | +0.016 | -0.013 | -94.3 | +0.019 | +0.018 | -0.040 | +1.07 / +0.66 | PASS |
| W07 VWAP dist <= 2% (new sensor) | 97 | +0.089 | -0.005 | -7.3 | 1869 | +0.036 | +0.007 | -24.4 | +0.067 | -0.003 | +0.133 | +0.09 / -0.00 | PASS |
| W08 max hold 30 min (P25) | 327 | +0.073 | +0.015 | -8.9 | 6325 | -0.005 | -0.031 | -85.3 | +0.008 | -0.018 | -0.009 | +0.62 / -0.79 | FAIL: 2y avg R -0.005 < parent +0.011 |
| W09 max hold 45 min (P25) | 327 | +0.061 | +0.002 | -9.5 | 6320 | -0.005 | -0.032 | -93.4 | +0.007 | -0.016 | -0.012 | +0.55 / -0.91 | FAIL: 2y avg R -0.005 < parent +0.011 |
| W10 30 min if best < 0.25R (P25) | 327 | +0.036 | -0.056 | -12.3 | 6321 | -0.001 | -0.029 | -98.9 | +0.016 | -0.015 | -0.035 | +0.49 / -0.83 | FAIL: 2y avg R -0.001 < parent +0.011 |
| W11 skip 13:00-14:00 bar closes (P6) | 304 | +0.056 | -0.068 | -18.3 | 5331 | +0.019 | -0.007 | -84.8 | +0.046 | -0.004 | -0.045 | +2.41 / +0.35 | PASS |
| W12 cf 0.10 + start 10:30 | 268 | +0.056 | -0.056 | -12.8 | 5178 | +0.022 | -0.011 | -109.4 | +0.029 | +0.019 | -0.009 | +0.83 / +1.30 | PASS |
| W13 cf 0.10 + RSI<100 + start 10:30 | 258 | +0.072 | -0.037 | -10.0 | 4954 | +0.024 | -0.011 | -107.1 | +0.033 | +0.017 | +0.010 | +0.91 / +1.05 | PASS |
| W14 cf 0.10 + RSI<100 + start 10:30 + vol<=2.5 | 255 | +0.070 | -0.041 | -9.6 | 4914 | +0.026 | -0.009 | -105.0 | +0.036 | +0.018 | +0.010 | +0.86 / +1.17 | PASS |
| X01 cf0.05 + slope<=1.0 | 167 | +0.128 | +0.007 | -6.3 | 2943 | +0.043 | +0.017 | -47.1 | +0.057 | +0.036 | +0.018 | +0.70 / +0.42 | PASS |
| X02 cf0.05 + slope<=1.0 + RSI<100 | 152 | +0.166 | +0.053 | -3.9 | 2760 | +0.039 | +0.012 | -44.5 | +0.061 | +0.023 | +0.038 | +0.77 / +0.26 | PASS |
| X03 cf0.05 + slope<=1.0 + RSI<100 + start 10:30 | 148 | +0.168 | +0.055 | -3.1 | 2644 | +0.045 | +0.013 | -44.5 | +0.072 | +0.026 | +0.048 | +0.74 / +0.36 | PASS |
| X04 X03 + skip 13:00-14:00 | 140 | +0.201 | +0.093 | -2.5 | 2147 | +0.025 | -0.004 | -33.4 | +0.070 | -0.008 | +0.050 | +0.85 / -0.08 | PASS |
| X05 X03 + max hold 30 | 148 | +0.175 | +0.118 | -1.3 | 2646 | +0.014 | -0.017 | -41.0 | +0.059 | -0.019 | +0.044 | +0.59 / -0.15 | PASS |
| X06 X03 + max hold 45 | 148 | +0.183 | +0.129 | -2.0 | 2646 | +0.015 | -0.019 | -33.9 | +0.067 | -0.025 | +0.064 | +0.64 / -0.15 | PASS |
| X07 cf0.075 + slope<=1.0 + RSI<100 + start 10:30 | 181 | +0.140 | +0.036 | -6.8 | 3559 | +0.034 | -0.002 | -62.6 | +0.053 | +0.019 | +0.022 | +0.93 / +0.52 | PASS |
| X08 X03 + VWAP dist <= 3% | 90 | +0.200 | +0.136 | -2.5 | 1822 | +0.035 | +0.003 | -36.9 | +0.081 | -0.002 | +0.133 | +0.33 / -0.02 | PASS |
| X09 X03 + lots per symbol 1 (tool only) | 132 | +0.172 | +0.060 | -3.1 | 2287 | +0.039 | -0.000 | -34.2 | +0.095 | -0.002 | +0.052 | +0.64 / +0.13 | PASS |
| X10 cf0.05 + RSI<=90 + slope<=1.0 | 130 | +0.190 | +0.079 | -4.4 | 2374 | +0.051 | +0.021 | -38.8 | +0.075 | +0.031 | +0.096 | +0.65 / +0.32 | PASS |
| X11 cf0.05 + slope<=1.0 + skip 13:00-14:00 | 159 | +0.165 | +0.050 | -5.9 | 2427 | +0.024 | +0.003 | -38.3 | +0.055 | +0.003 | +0.012 | +0.89 / -0.05 | PASS |
| X12 X03 + window end 13:00 | 107 | +0.266 | +0.146 | -1.0 | 1724 | +0.003 | -0.020 | -31.5 | +0.030 | -0.022 | +0.118 | +0.77 / -0.30 | PASS |
| Y01 X10 + start 10:30 | 127 | +0.195 | +0.082 | -3.3 | 2292 | +0.055 | +0.022 | -38.8 | +0.082 | +0.034 | +0.108 | +0.65 / +0.36 | PASS |
| Y02 X10 + price >= $20 | 125 | +0.215 | +0.109 | -3.1 | 2370 | +0.051 | +0.021 | -37.7 | +0.075 | +0.031 | +0.096 | +0.71 / +0.31 | PASS |
| Y03 X10 with cost/R 0.075 | 162 | +0.151 | +0.048 | -4.2 | 3219 | +0.037 | +0.002 | -54.7 | +0.058 | +0.018 | +0.065 | +0.79 / +0.42 | PASS |
| Y04 X10 + volumeRatio <= 2.5 | 130 | +0.190 | +0.079 | -4.4 | 2348 | +0.052 | +0.023 | -37.7 | +0.079 | +0.031 | +0.096 | +0.65 / +0.33 | PASS |
| Y05 X10 + max hold 45 | 130 | +0.175 | +0.112 | -2.6 | 2376 | +0.022 | -0.009 | -32.0 | +0.082 | -0.023 | +0.070 | +0.51 / -0.08 | PASS |
| Y06 X10 with slope cap 0.85 | 114 | +0.222 | +0.115 | -2.0 | 2051 | +0.050 | +0.023 | -32.1 | +0.062 | +0.038 | +0.120 | +0.66 / +0.20 | PASS |
| Y07 X10 with RSI cap 85 | 116 | +0.185 | +0.078 | -4.1 | 2087 | +0.049 | +0.019 | -33.0 | +0.084 | +0.025 | +0.071 | +0.52 / +0.20 | PASS |

Files: `results_all.csv` (every config × test × split), `extras.csv` (shape), `component_analysis.txt` (slices), `code/` (harness: cand2y, paths2y, fetch_replay, sim, load, go, decl, report). Educational only — not financial advice.
