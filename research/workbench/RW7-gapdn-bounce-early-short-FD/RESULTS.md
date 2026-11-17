# Workbench RESULTS — Gap-Down Early Bounce Short (all day) `RW7-gapdn-bounce-early-short-FD` (Testing F) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16 (research files only: no config change, no deploy).

## Verdict — supervisor sign-off
> **Recommended: `RW7-gapdn-bounce-early-short-FD-WB3`** — parent + two market-state gates measured after 09:50 (skip when
> SPY is up > +0.10% since the 09:50 close, or up > +0.20% over the last 30 minutes), gap < −0.5% (was < 0) and entries end
> 13:00 (was 15:00). **PASS — better than the parent in both tests on avg R, avg R w/o best day and worst day, positive after
> costs in both, and positive in every 2-year split except TRAIN (−0.008, parent −0.037).**

| copy | change | replay avg R (parent +0.029) | 2-year avg R (parent −0.019) | w/o best day (replay / 2y; parent −0.001 / −0.022) | worst day (replay / 2y; parent −30.4 / −54.7R) | trades (replay / 2y; parent 691 / 16,747) | verdict |
|---|---|---|---|---|---|---|---|
| WB1 | P6 window end 15:00 → 13:00 | **+0.063** | **−0.013** | +0.031 / −0.016 | −27.5 / −57.5 | 551 / 12,502 | PASS (contained in WB3) |
| WB2 | NEW gate: skip SPY > +0.10% since 09:50 | **+0.064** | **−0.006** | +0.025 / −0.011 | −24.6 / −56.6 | 470 / 10,669 | PASS (contained in WB3) |
| **WB3** | gates SPY since 09:50 ≤ +0.10% and last 30 min ≤ +0.20% + gap < −0.5% + end 13:00 | **+0.155** | **+0.023** | **+0.096 / +0.015** | **−16.7 / −37.1** | 316 / 4,488 | **PASS — recommended** |

Supervisor sign-off (what changed, why, before/after, where it gives back):
- **What / why.** The 2-year bench shows the parent's loss is day type: shorting gap-down bounces on days the market rallies
  (2y SPY-up days −0.235R on 5,417 trades). WB3 stops shorting once SPY has risen after 09:50 (two after-09:50 gates: since
  the 09:50 close, and over the last 30 minutes, which catches intraday squeezes on red days), drops shallow gaps (> −0.5%)
  and afternoon entries (live: after 13:00 −28.4R, shallow gaps −27.7R).
- **Overall before → after (identical pipeline, LR8 costs, Testing F book):** replay +0.029 → **+0.155R** (total +20.2 →
  **+49.0R** on fewer trades; w/o best day −0.001 → +0.096; the parent's replay total was ~all one day, 103%; WB3's best day is
  42%); 2-year −0.019 → **+0.023R** (−320R → +102R; w/o best day −0.022 → +0.015; worst day −54.7 → −37.1R); 2y splits TRAIN
  −0.037 → −0.008, VALID −0.004 → +0.030, FWD +0.010 → +0.130. Win 51.8 → 56.6% (replay), 50.4 → 53.0% (2y); avg win +0.79 →
  +0.83R, avg loss −0.84 → −0.88R (2y); median hold 100 → 110 min. Paired-by-day t vs parent: replay +0.68, 2-year +1.93.
- **Where it gives back:** (1) fewer trades — replay −54%, 2-year −73% (about 10 a day instead of 37 in the 2-year bench);
  (2) flat days turn slightly negative (2y +0.002 → −0.039 on 1,481) and the up-day trades it still takes are bad (−0.357R on
  722; the gate works by cutting up-day exposure 5,417 → 722, not by fixing those trades); (3) in the LIVE sessions the SPY
  gates removed net-positive trades (since-09:50 part +4.7R, 30-min part +5.5R), including the three best live trades (NVDA /
  APH / SPCX 11-05 11:35, SPY −1.6% on the day but +0.59% in the last 30 min). The live trades WB3 keeps were still +0.096R
  (177 trades, +17.0R) vs the parent's −0.021R.
- **Honest limits:** 65 configurations tried; no copy clears the configs-counted bar max(1.5, sqrt(2 ln 65)) = 2.89 (WB3
  2-year t 1.93; reported, not used to pass under the owner's 2026-11-16 clarified rule). WB3's 30-min threshold 0.20 was
  picked from neighbours after Round 3 (D10 at 0.10 also passes: +0.124 / +0.019). The replay is the parent's live-signal
  symbol-days, so P2 (ADV) could not be replayed. Ablation (Round 5): end 13:00 + gap alone (F1) +0.073 / −0.017; adding
  the since-09:50 gate (F3 = D3) +0.183 / +0.002; adding the 30-min gate instead (F2) +0.066 / +0.005; both (WB3) +0.155 / +0.023.

## Method (identical for parent and every copy) — harness reused from research/workbench/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD/code (itself from L3-gap-slope-fromopen-FD)
- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live (Testing 1
  run 1, any status except not shortable/ETB), 2026-10-12..11-13 (1,093 symbol-days, 25 sessions). 1-min SIP bars (read-only
  GET) → lab frame (`mcf.report.engine.lab_frame` + daily priors as live). Parent replay 691 trades +0.029R vs live 567 trades
  −0.021R; on the 393 trades in both, replay +0.056 vs live +0.019R (corr 0.93: entry slippage), the same for every copy.
- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted in
  cand2y.py / paths2y.py / load.py), ADV ≥ $95M, names shortable+ETB on ≥ 90% of universe snapshots (E90 proxy, same file as
  the RW5 / L3 jobs). Candidate superset trimmed to heat ≤ −15, bp < −0.10, 50 ≤ RSI(14) ≤ 70 for disk (every tested config
  is inside it). Splits TRAIN ≤ 2025-12-31, VALID 2026-01..10-05, FWD 10-06..11-04.
- Same engine for both: RW7 sensors on 5-min bar close (heat ≤ −20, buyPressure < −0.15, 55 ≤ RSI(14) ≤ 65, gap < 0), refire
  off, entry at the signal-bar close, price ≥ $5, exits on 1-min bars (stop first; target only when traded through by $0.01;
  flat 15:55), **LR8 costs**, Testing F's book (≤ 30 lots / setup, ≤ 3 per symbol, NO per-setup latch, account cost filter
  stop cost ≤ 0.15R ON for the parent and every copy). SPY gates from SPY 1-min closes (09:50 bar-close reference; 30-min
  reference never before 09:50). The parent's live record is NOT used in the pass decision.
- Module parity (WB modules vs bench mask on the replay frames, spy_fo rebuilt from SPY 1-min): WB2 993/996, WB1 1000/1000,
  WB3 513/516 bar hits; the misses are two symbol-days (MKL 11-11, SYRE 11-10) without a 09:50 5-min bar, where the module
  fails safe (no signal).

## Every configuration tried (65 + parent), including failures
Round 1 (V01-V32, one part each, declared in code/decl.py before any variant or 2-year score; V31/V32 added after the 10-trade
review, still before scoring), Round 2 (S1/S2 + combos C1-C13), Round 3 (D1-D11, incl. the NEW 30-min gate), Round 4 (E1-E6
neighbours of D10), Round 5 (F1-F3 ablation; F3 = D3 rerun, not counted twice). Pass rule (owner 2026-11-16): meets or
exceeds the parent's avg R in BOTH tests (meets = within 0.01R or ≥ 95%), and not worse on avg R w/o best day by > 0.02R or
on worst day by > 10%.

| copy | config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | t vs parent (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
|  | PARENT | 691 | +0.029 | -0.001 | -30.4 | 16747 | -0.019 | -0.022 | -54.7 | +0.00 / +0.00 | — |
|  | V01 ADV >= $150M (P2) | 691 | +0.029 | -0.001 | -30.4 | 13850 | -0.019 | -0.023 | -45.9 | +0.00 / +0.68 | PASS |
|  | V02 price >= $10 (P3) | 691 | +0.031 | +0.001 | -30.4 | 16745 | -0.019 | -0.022 | -54.7 | +0.74 / +0.12 | PASS |
|  | V03 window start 09:50->10:15 (P6/P7) | 685 | +0.027 | -0.002 | -30.3 | 16385 | -0.020 | -0.023 | -54.7 | -0.83 / -0.27 | PASS |
|  | V04 window start 09:50->11:00 (P6/P7) | 611 | +0.054 | +0.014 | -29.7 | 14182 | -0.023 | -0.027 | -53.7 | +2.28 / -0.06 | PASS |
|  | V05 window end 15:00->14:00 (P6) | 630 | +0.039 | +0.006 | -28.4 | 14867 | -0.020 | -0.023 | -55.7 | +0.87 / +0.41 | PASS |
| WB1 | V06 window end 15:00->13:00 (P6) | 551 | +0.063 | +0.031 | -27.5 | 12502 | -0.013 | -0.016 | -57.5 | +1.12 / +1.56 | PASS |
|  | V07 refire on, cooldown 6 (P8) | 732 | +0.029 | -0.001 | -30.6 | 17671 | -0.022 | -0.025 | -55.1 | +0.13 / -1.83 | PASS |
|  | V08 heat <= -25 (P9) | 400 | +0.039 | -0.011 | -17.6 | 8481 | -0.032 | -0.037 | -46.9 | -0.17 / +0.31 | FAIL — 2y avg R -0.032 < parent -0.019 |
|  | V09 buyPressure < -0.20 (P10) | 572 | +0.014 | -0.017 | -28.7 | 14007 | -0.017 | -0.020 | -45.2 | -1.11 / +1.20 | FAIL — replay avg R +0.014 < parent +0.029 |
|  | V10 RSI(14) 55-60 (P11 upper) | 484 | +0.018 | -0.021 | -19.8 | 10827 | -0.032 | -0.036 | -39.6 | -0.52 / -0.22 | FAIL — replay avg R +0.018 < parent +0.029; replay w/o best day -0.021 vs -0.001; 2y avg R -0.032 < parent -0.019 |
|  | V11 RSI(14) 55-62.5 (P11 upper) | 604 | +0.035 | +0.002 | -26.3 | 14186 | -0.023 | -0.026 | -50.4 | +0.06 / -0.11 | PASS |
|  | V12 RSI(14) 57-65 (P11 lower) | 614 | +0.021 | -0.013 | -29.8 | 15396 | -0.021 | -0.024 | -52.8 | -0.51 / +0.01 | PASS |
|  | V13 + RSI(5) <= 90 (P11 extra) | 664 | +0.036 | +0.005 | -30.6 | 16026 | -0.019 | -0.021 | -50.5 | +0.58 / +0.53 | PASS |
|  | V14 gap < -0.5% (P12) | 582 | +0.056 | +0.018 | -33.0 | 10625 | -0.016 | -0.020 | -54.6 | +0.73 / +1.28 | PASS |
|  | V15 gap < -1.5% (P12) | 358 | +0.132 | +0.070 | -13.2 | 5025 | -0.035 | -0.045 | -49.3 | +0.68 / +0.71 | FAIL — 2y avg R -0.035 < parent -0.019; 2y w/o best day -0.045 vs -0.022 |
|  | V16 lots/symbol 3 -> 1 (P15, tool) | 691 | +0.029 | -0.001 | -30.4 | 16747 | -0.019 | -0.022 | -54.7 | +0.00 / +0.00 | PASS |
|  | V17 latch -2R (P16, tool) | 603 | +0.010 | -0.024 | -23.9 | 13053 | -0.013 | -0.016 | -32.1 | -0.50 / +1.39 | FAIL — replay avg R +0.010 < parent +0.029; replay w/o best day -0.024 vs -0.001 |
|  | V18 cost filter 0.15 -> 0.10 (P18) | 596 | +0.015 | -0.019 | -29.7 | 14148 | -0.017 | -0.020 | -50.0 | -1.08 / +1.22 | FAIL — replay avg R +0.015 < parent +0.029 |
|  | V19 cost filter off (P18) | 849 | +0.018 | -0.005 | -29.3 | 19663 | -0.036 | -0.038 | -62.7 | -0.34 / -4.59 | FAIL — replay avg R +0.018 < parent +0.029; 2y avg R -0.036 < parent -0.019; 2y worst day -62.7 vs -54.7R |
|  | V20 1R 0.25 -> 0.30 ATR (P21) | 702 | +0.028 | +0.001 | -23.7 | 16334 | -0.013 | -0.016 | -53.1 | -0.07 / +1.30 | PASS |
|  | V21 stop 1.0 -> 1.25R (P24) | 670 | +0.035 | +0.003 | -28.0 | 16122 | -0.013 | -0.016 | -66.6 | +0.56 / +1.84 | FAIL — 2y worst day -66.6 vs -54.7R |
|  | V22 target 1.0 -> 0.8R (P25) | 709 | +0.022 | -0.003 | -29.8 | 17397 | -0.023 | -0.026 | -54.9 | -0.35 / -1.35 | PASS |
|  | V23 BE stop after +0.5R (P24 move) | 720 | -0.002 | -0.025 | -31.0 | 17810 | -0.033 | -0.036 | -51.9 | -1.61 / -3.71 | FAIL — replay avg R -0.002 < parent +0.029; replay w/o best day -0.025 vs -0.001; 2y avg R -0.033 < parent -0.019 |
|  | V24 max hold 120 min (P27) | 736 | -0.001 | -0.028 | -28.9 | 17913 | -0.022 | -0.025 | -54.6 | -0.94 / -0.74 | FAIL — replay avg R -0.001 < parent +0.029; replay w/o best day -0.028 vs -0.001 |
|  | V25 flat 15:55 -> 15:00 (P27, no live knob) | 692 | +0.053 | +0.021 | -24.4 | 16786 | -0.018 | -0.021 | -58.2 | +0.82 / +0.20 | PASS (no live knob) |
|  | V26 gate: skip SPY > +0.20% since 09:50 (new, sibling RW3/RW5) | 523 | +0.046 | +0.010 | -24.6 | 12522 | -0.010 | -0.014 | -56.7 | +0.10 / +1.44 | PASS |
|  | V27 gate: skip SPY above 09:30-09:50 high (new) | 494 | +0.053 | +0.016 | -24.6 | 11234 | -0.014 | -0.018 | -55.7 | +0.17 / +1.11 | PASS |
|  | V28 skip SMA20 slope > +0.20%/bar (new: stock trending up) | 678 | +0.044 | +0.015 | -29.2 | 16492 | -0.020 | -0.022 | -53.7 | +1.63 / -0.14 | PASS |
|  | V29 skip price > 1.0% below VWAP (new) | 596 | +0.044 | +0.013 | -31.9 | 15744 | -0.018 | -0.022 | -52.8 | +0.45 / +0.58 | PASS |
|  | V30 skip fromOpen > +1.0% (new: gap filled) | 637 | +0.033 | +0.000 | -27.9 | 15493 | -0.018 | -0.021 | -54.7 | +0.12 / +0.69 | PASS |
|  | V31 require fromOpen <= 0 (new: still below the open) | 517 | +0.043 | +0.005 | -23.0 | 11459 | -0.025 | -0.029 | -53.6 | +0.09 / +0.30 | PASS |
|  | V32 require fromOpen <= -1.0% (new: still >= 1% below the open) | 383 | +0.065 | +0.009 | -21.9 | 7944 | -0.028 | -0.033 | -40.8 | +0.13 / +0.56 | PASS |
|  | S1 skip SPY > +0.30% since 09:50 | 565 | +0.036 | +0.002 | -24.6 | 13789 | -0.014 | -0.018 | -55.7 | -0.00 / +1.03 | PASS |
| WB2 | S2 skip SPY > +0.10% since 09:50 | 470 | +0.064 | +0.025 | -24.6 | 10669 | -0.006 | -0.011 | -56.6 | +0.25 / +1.57 | PASS |
|  | C1 SPY gate + end 13:00 | 420 | +0.098 | +0.057 | -21.5 | 9346 | -0.006 | -0.010 | -57.5 | +0.52 / +1.58 | PASS |
|  | C2 C1 + gap < -0.5% | 370 | +0.146 | +0.096 | -15.4 | 5712 | -0.008 | -0.014 | -57.5 | +0.77 / +1.39 | PASS |
|  | C3 C1 + 1R 0.30 ATR | 426 | +0.082 | +0.045 | -18.7 | 9455 | -0.007 | -0.011 | -56.8 | +0.36 / +1.48 | PASS |
|  | C4 C1 + VWAP floor -1% | 367 | +0.095 | +0.050 | -19.9 | 8945 | -0.009 | -0.013 | -54.3 | +0.34 / +1.44 | PASS |
|  | C5 C1 + RSI(5) <= 90 | 402 | +0.112 | +0.067 | -21.5 | 8994 | -0.005 | -0.009 | -53.3 | +0.60 / +1.67 | PASS |
|  | C6 C2 + 1R 0.30 ATR | 369 | +0.136 | +0.096 | -14.8 | 5813 | -0.004 | -0.010 | -55.9 | +0.68 / +1.51 | PASS |
|  | C7 C2 + VWAP floor -1% + RSI(5) <= 90 | 295 | +0.174 | +0.108 | -12.2 | 5120 | -0.006 | -0.013 | -50.1 | +0.66 / +1.40 | PASS |
|  | C8 SPY gate + gap < -0.5% | 455 | +0.115 | +0.073 | -17.4 | 7782 | -0.002 | -0.008 | -55.5 | +0.75 / +1.73 | PASS |
|  | C9 SPY range gate + end 13:00 + gap < -0.5% | 346 | +0.151 | +0.097 | -15.4 | 5159 | -0.018 | -0.025 | -57.5 | +0.77 / +1.10 | PASS |
|  | C10 C2 + start 10:15 (sibling) | 367 | +0.145 | +0.094 | -15.4 | 5642 | -0.009 | -0.015 | -57.5 | +0.73 / +1.36 | PASS |
|  | C11 C2 + slope <= +0.05%/bar (MF2 sibling layer) | 346 | +0.163 | +0.112 | -15.3 | 5269 | -0.006 | -0.012 | -48.9 | +0.79 / +1.45 | PASS |
|  | C12 slope <= +0.05%/bar alone (MF2 sibling part) | 657 | +0.043 | +0.015 | -25.7 | 15105 | -0.021 | -0.024 | -46.1 | +0.90 / +0.00 | PASS |
|  | C13 SPY gate + end 14:00 + gap < -0.5% | 412 | +0.116 | +0.069 | -17.4 | 6858 | -0.013 | -0.020 | -55.5 | +0.65 / +1.27 | PASS |
|  | D1 gate 0.10 + end 13:00 + RSI(5) <= 90 | 355 | +0.141 | +0.092 | -21.5 | 7443 | +0.002 | -0.003 | -53.3 | +0.72 / +1.78 | PASS |
|  | D2 gate 0.10 + gap < -0.5% | 414 | +0.137 | +0.094 | -17.4 | 6722 | +0.006 | -0.001 | -56.5 | +0.89 / +1.91 | PASS |
|  | D3 gate 0.10 + end 13:00 + gap < -0.5% | 330 | +0.183 | +0.128 | -15.4 | 4788 | +0.003 | -0.005 | -57.5 | +0.93 / +1.58 | PASS |
|  | D4 D3 + VWAP floor -1% + RSI(5) <= 90 | 264 | +0.234 | +0.170 | -12.2 | 4272 | +0.003 | -0.005 | -50.1 | +0.92 / +1.53 | PASS |
|  | D5 gate 0.00 (skip any SPY rise since 09:50) | 408 | +0.061 | +0.016 | -24.6 | 8906 | -0.004 | -0.008 | -57.5 | +0.12 / +1.60 | PASS |
|  | D6 gate 0.10 + end 13:00 | 367 | +0.128 | +0.083 | -21.5 | 7732 | +0.001 | -0.004 | -57.5 | +0.66 / +1.75 | PASS |
|  | D7 D3 + slope <= +0.05%/bar | 309 | +0.191 | +0.136 | -15.3 | 4417 | +0.003 | -0.004 | -48.9 | +0.88 / +1.57 | PASS |
|  | D8 NEW gate: skip SPY up > +0.10% over the last 30 min (after 09:50) | 606 | +0.040 | -0.001 | -24.3 | 13727 | -0.006 | -0.009 | -40.6 | +0.19 / +2.13 | PASS |
|  | D9 D8 + SPY gate 0.20 since 09:50 | 482 | +0.022 | -0.018 | -24.3 | 10830 | -0.001 | -0.005 | -37.1 | -0.25 / +1.92 | PASS |
|  | D10 D3 + D8 30-min gate | 292 | +0.123 | +0.057 | -16.6 | 4092 | +0.019 | +0.011 | -36.8 | +0.37 / +1.77 | PASS |
|  | D11 D3 + RSI(5) <= 90 + slope <= 0.05 | 295 | +0.212 | +0.167 | -15.3 | 4249 | +0.007 | -0.002 | -45.6 | +0.95 / +1.61 | PASS |
|  | E1 D10 + RSI(5) <= 90 + slope <= 0.05 | 257 | +0.133 | +0.065 | -16.6 | 3585 | +0.023 | +0.013 | -33.6 | +0.30 / +1.76 | PASS |
|  | E2 D10 without gap < -0.5% (gates + end 13:00) | 335 | +0.081 | +0.028 | -22.3 | 6814 | +0.013 | +0.007 | -37.2 | +0.17 / +2.03 | PASS |
| WB3 | E3 D10 with 30-min gate 0.20 | 316 | +0.155 | +0.096 | -16.7 | 4488 | +0.023 | +0.015 | -37.1 | +0.68 / +1.93 | PASS |
|  | E4 D10 with end 14:00 | 334 | +0.081 | +0.026 | -18.6 | 5019 | +0.008 | -0.002 | -42.3 | +0.16 / +1.68 | PASS |
|  | E5 D10 with SPY-since-09:50 gate 0.20 | 323 | +0.098 | +0.036 | -16.6 | 4846 | +0.013 | +0.006 | -36.8 | +0.27 / +1.77 | PASS |
|  | E6 D10 + RSI(5) <= 90 | 280 | +0.139 | +0.074 | -16.6 | 3962 | +0.023 | +0.015 | -36.8 | +0.43 / +1.82 | PASS |
|  | F1 end 13:00 + gap < -0.5% (no SPY gates) | 474 | +0.073 | +0.030 | -30.5 | 7886 | -0.017 | -0.022 | -57.5 | +0.63 / +1.23 | PASS |
|  | F2 F1 + 30-min gate 0.20 only | 443 | +0.066 | +0.020 | -28.4 | 7118 | +0.005 | -0.000 | -40.5 | +0.47 / +2.07 | PASS |
|  | F3 F1 + since-09:50 gate 0.10 only | 330 | +0.183 | +0.128 | -15.4 | 4788 | +0.003 | -0.005 | -57.5 | +0.93 / +1.58 | PASS |

| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |
|---|---|---|---|
| PARENT | -0.037 (7973) | -0.004 (7883) | +0.010 (891) |
| V01 ADV >= $150M (P2) | -0.044 (6557) | -0.001 (6563) | +0.038 (730) |
| V02 price >= $10 (P3) | -0.037 (7972) | -0.004 (7882) | +0.010 (891) |
| V03 window start 09:50->10:15 (P6/P7) | -0.036 (7759) | -0.008 (7755) | +0.012 (871) |
| V04 window start 09:50->11:00 (P6/P7) | -0.036 (6664) | -0.015 (6740) | +0.021 (778) |
| V05 window end 15:00->14:00 (P6) | -0.042 (7062) | -0.003 (7041) | +0.018 (764) |
| V06 window end 15:00->13:00 (P6) | -0.045 (5919) | +0.013 (5948) | +0.033 (635) |
| V07 refire on, cooldown 6 (P8) | -0.038 (8452) | -0.008 (8287) | -0.007 (932) |
| V08 heat <= -25 (P9) | -0.052 (3739) | -0.024 (4268) | +0.059 (474) |
| V09 buyPressure < -0.20 (P10) | -0.036 (6586) | -0.003 (6701) | +0.033 (720) |
| V10 RSI(14) 55-60 (P11 upper) | -0.057 (4883) | -0.012 (5331) | -0.004 (613) |
| V11 RSI(14) 55-62.5 (P11 upper) | -0.045 (6588) | -0.006 (6826) | +0.017 (772) |
| V12 RSI(14) 57-65 (P11 lower) | -0.040 (7347) | -0.004 (7254) | +0.007 (795) |
| V13 + RSI(5) <= 90 (P11 extra) | -0.041 (7534) | -0.002 (7646) | +0.027 (846) |
| V14 gap < -0.5% (P12) | -0.047 (4390) | -0.001 (5569) | +0.065 (666) |
| V15 gap < -1.5% (P12) | -0.086 (1898) | -0.020 (2712) | +0.102 (415) |
| V16 lots/symbol 3 -> 1 (P15, tool) | -0.037 (7973) | -0.004 (7883) | +0.010 (891) |
| V17 latch -2R (P16, tool) | -0.047 (6080) | +0.022 (6312) | -0.023 (661) |
| V18 cost filter 0.15 -> 0.10 (P18) | -0.039 (6533) | +0.002 (6856) | +0.011 (759) |
| V19 cost filter off (P18) | -0.051 (9684) | -0.022 (8941) | -0.013 (1038) |
| V20 1R 0.25 -> 0.30 ATR (P21) | -0.030 (7892) | +0.005 (7568) | -0.018 (874) |
| V21 stop 1.0 -> 1.25R (P24) | -0.033 (7702) | +0.004 (7566) | +0.009 (854) |
| V22 target 1.0 -> 0.8R (P25) | -0.038 (8228) | -0.011 (8254) | +0.012 (915) |
| V23 BE stop after +0.5R (P24 move) | -0.050 (8408) | -0.024 (8471) | +0.038 (931) |
| V24 max hold 120 min (P27) | -0.043 (8455) | -0.008 (8530) | +0.054 (928) |
| V25 flat 15:55 -> 15:00 (P27, no live knob) | -0.039 (7988) | -0.007 (7905) | +0.080 (893) |
| V26 gate: skip SPY > +0.20% since 09:50 (new, sibling RW3/RW5) | -0.027 (6012) | +0.005 (5841) | +0.003 (669) |
| V27 gate: skip SPY above 09:30-09:50 high (new) | -0.027 (5264) | -0.002 (5372) | -0.004 (598) |
| V28 skip SMA20 slope > +0.20%/bar (new: stock trending up) | -0.036 (7874) | -0.006 (7740) | +0.014 (878) |
| V29 skip price > 1.0% below VWAP (new) | -0.046 (7556) | +0.004 (7382) | +0.035 (806) |
| V30 skip fromOpen > +1.0% (new: gap filled) | -0.035 (7437) | -0.004 (7242) | +0.015 (814) |
| V31 require fromOpen <= 0 (new: still below the open) | -0.042 (5062) | -0.016 (5748) | +0.034 (649) |
| V32 require fromOpen <= -1.0% (new: still >= 1% below the open) | -0.053 (3275) | -0.014 (4173) | +0.030 (496) |
| S1 skip SPY > +0.30% since 09:50 | -0.033 (6642) | +0.003 (6382) | +0.002 (765) |
| S2 skip SPY > +0.10% since 09:50 | -0.023 (5067) | +0.011 (5038) | -0.015 (564) |
| C1 SPY gate + end 13:00 | -0.033 (4471) | +0.019 (4374) | +0.013 (501) |
| C2 C1 + gap < -0.5% | -0.051 (2301) | +0.011 (3033) | +0.106 (378) |
| C3 C1 + 1R 0.30 ATR | -0.033 (4618) | +0.025 (4338) | -0.049 (499) |
| C4 C1 + VWAP floor -1% | -0.033 (4280) | +0.014 (4201) | +0.007 (464) |
| C5 C1 + RSI(5) <= 90 | -0.035 (4254) | +0.021 (4265) | +0.036 (475) |
| C6 C2 + 1R 0.30 ATR | -0.040 (2391) | +0.018 (3041) | +0.046 (381) |
| C7 C2 + VWAP floor -1% + RSI(5) <= 90 | -0.043 (2022) | +0.006 (2783) | +0.117 (315) |
| C8 SPY gate + gap < -0.5% | -0.033 (3144) | +0.012 (4130) | +0.071 (508) |
| C9 SPY range gate + end 13:00 + gap < -0.5% | -0.056 (2070) | -0.004 (2753) | +0.095 (336) |
| C10 C2 + start 10:15 (sibling) | -0.050 (2267) | +0.008 (3002) | +0.106 (373) |
| C11 C2 + slope <= +0.05%/bar (MF2 sibling layer) | -0.050 (2107) | +0.012 (2808) | +0.114 (354) |
| C12 slope <= +0.05%/bar alone (MF2 sibling part) | -0.036 (7059) | -0.011 (7212) | +0.014 (834) |
| C13 SPY gate + end 14:00 + gap < -0.5% | -0.047 (2747) | +0.002 (3684) | +0.085 (427) |
| D1 gate 0.10 + end 13:00 + RSI(5) <= 90 | -0.032 (3503) | +0.032 (3551) | +0.035 (389) |
| D2 gate 0.10 + gap < -0.5% | -0.030 (2656) | +0.025 (3624) | +0.079 (442) |
| D3 gate 0.10 + end 13:00 + gap < -0.5% | -0.051 (1906) | +0.027 (2566) | +0.124 (316) |
| D4 D3 + VWAP floor -1% + RSI(5) <= 90 | -0.049 (1659) | +0.022 (2354) | +0.149 (259) |
| D5 gate 0.00 (skip any SPY rise since 09:50) | -0.013 (4085) | +0.004 (4384) | +0.008 (437) |
| D6 gate 0.10 + end 13:00 | -0.028 (3671) | +0.029 (3652) | +0.002 (409) |
| D7 D3 + slope <= +0.05%/bar | -0.044 (1753) | +0.022 (2365) | +0.129 (299) |
| D8 NEW gate: skip SPY up > +0.10% over the last 30 min (after 09:50) | -0.016 (6273) | +0.003 (6656) | -0.004 (798) |
| D9 D8 + SPY gate 0.20 since 09:50 | -0.007 (5033) | +0.007 (5177) | -0.015 (620) |
| D10 D3 + D8 30-min gate | -0.000 (1554) | +0.019 (2261) | +0.128 (277) |
| D11 D3 + RSI(5) <= 90 + slope <= 0.05 | -0.046 (1677) | +0.026 (2290) | +0.165 (282) |
| E1 D10 + RSI(5) <= 90 + slope <= 0.05 | +0.007 (1357) | +0.019 (1985) | +0.142 (243) |
| E2 D10 without gap < -0.5% (gates + end 13:00) | +0.005 (3161) | +0.021 (3286) | +0.004 (367) |
| E3 D10 with 30-min gate 0.20 | -0.008 (1712) | +0.030 (2467) | +0.130 (309) |
| E4 D10 with end 14:00 | -0.018 (1869) | +0.013 (2824) | +0.105 (326) |
| E5 D10 with SPY-since-09:50 gate 0.20 | -0.001 (1861) | +0.014 (2646) | +0.083 (339) |
| E6 D10 + RSI(5) <= 90 | +0.000 (1502) | +0.024 (2196) | +0.152 (264) |
| F1 end 13:00 + gap < -0.5% (no SPY gates) | -0.060 (3251) | +0.003 (4154) | +0.104 (481) |
| F2 F1 + 30-min gate 0.20 only | -0.026 (2818) | +0.017 (3833) | +0.091 (467) |
| F3 F1 + since-09:50 gate 0.10 only | -0.051 (1906) | +0.027 (2566) | +0.124 (316) |

Notes: V01 (ADV) cannot be replayed, so its replay row equals the parent. V16 (1 lot/symbol) = parent (refire off). V17
(latch) is a backtest-only tool part. V25 (flat 15:00) has no per-setup live knob (runner flattens at 15:55 for all setups).
Passing parts NOT shipped: V02 / V13 / V28 / V30 (~0 gain), V05 (end 14:00, weaker than 13:00), V14 (gap −0.5%, folded into
WB3), V20 (1R 0.30: no gain in combos C3 / C6), V22 (target 0.8R: meets only), V26 / S1 (gate 0.20 / 0.30: 0.10 stronger),
V27 (range gate: weaker 2y), V29 (VWAP floor: one test), C1-C13 / D1-D11 / E1-E6 (weaker than E3 overall, or worse worst day
or TRAIN; E1 / E6 with RSI(5) ≤ 90 match E3 on 2y but lower replay). FAIL: V08 heat ≤ −25, V09 bp < −0.20, V10 RSI 55-60,
V15 gap < −1.5%, V17 latch −2R, V18 cost 0.10, V19 cost filter off, V21 stop 1.25R (2y worst day −66.6R), V23 BE after +0.5R,
V24 max hold 120 min.

## Shape (SPY day type open → close > +0.25% up / < −0.25% down; extras.csv)
| config | test | avg win | avg loss | median hold (min) | stop / target / time share | down avg R (n) | flat | up |
|---|---|---|---|---|---|---|---|---|
| PARENT | replay | +0.777 | −0.774 | 127 | 28 / 34 / 38% | +0.160 (238) | +0.005 (220) | −0.081 (233) |
| PARENT | 2y | +0.788 | −0.838 | 100 | 33 / 35 / 32% | +0.160 (5,895) | +0.002 (5,435) | −0.235 (5,417) |
| WB1 | 2y | +0.834 | −0.897 | 112 | 36 / 39 / 25% | +0.202 (4,226) | +0.008 (4,036) | −0.249 (4,240) |
| WB2 | 2y | +0.793 | −0.836 | 97 | 32 / 36 / 32% | +0.129 (5,316) | −0.044 (3,632) | −0.346 (1,721) |
| WB3 | replay | +0.856 | −0.761 | 140 | 24 / 45 / 31% | +0.308 (156) | +0.076 (88) | −0.079 (72) |
| WB3 | 2y | +0.828 | −0.884 | 110 | 35 / 40 / 25% | +0.183 (2,285) | −0.039 (1,481) | −0.357 (722) |

## Pending config change — "ready to deploy after close" (NOT applied)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective the next session. One copy only: **WB3**
(it contains WB2's gate and WB1's window; running them side by side would be near-twins). The parent stays in Testing F,
unchanged (Workbench rule 1; its Graveyard review 11-18 is separate). Destination: **Testing E** (`config/account_testinge.yaml`)
— a testing account that is not the parent's (twins rule); it has no RW-family / gap-down bounce short (Testing 1 has RW1, the
heavier-selling sibling), already runs `context: [spy_fo]` setups and has the same cost filter `max_stop_cost_r: 0.15`. If
another Workbench job has claimed the FIRST slot in Testing E tonight (GEN-261026-03 WB2 is recommended there), put WB3 right
after it (the main session orders Workbench copies). Note Testing E's spotlight cap is 50 lots / setup (bench: 30); WB3 averages
~10 trades a session in the 2-year bench, so the cap rarely binds.
1. Module: copy `research/workbench/RW7-gapdn-bounce-early-short-FD/modules/RW7-gapdn-bounce-early-short-FD-WB3.py` to
   `research/bdi/fullday/RW7-gapdn-bounce-early-short-FD-WB3.py`.
2. `config/account_testinge.yaml`, under `strategies:` add
   ```yaml
   RW7-gapdn-bounce-early-short-FD-WB3:
     # Workbench copy of RW7-gapdn-bounce-early-short-FD (Testing F), Mechanic 2026-11-16: + skip when SPY is up > +0.10% since
     # 09:50 or > +0.20% over the last 30 min + gap < -0.5% + window to 13:00; research/workbench/RW7-.../RESULTS.md.
     enabled: true
     type: lab
     module: research/bdi/fullday/RW7-gapdn-bounce-early-short-FD-WB3.py
     min_adv: 95000000
     window: [950, 1300]
     context: [spy_fo]
     scale_out_r: null
     tags: [workbench, "parent:RW7-gapdn-bounce-early-short-FD"]
   ```
   (refire stays off, as the parent) and put `RW7-gapdn-bounce-early-short-FD-WB3` FIRST in `live.setup_order` (rule 5).
3. `config/setup_names.yaml`: `RW7-gapdn-bounce-early-short-FD-WB3: {name: "Gap-Down Early Bounce Short (all day) — WB3: SPY-after-09:50 gates + gap < -0.5% + end 13:00", side: short, what: "09:50-13:00: a stock gapped down > 0.5% with bearish heat and net selling bounces to RSI(14) 55-65; short the bounce unless SPY is up more than 0.10% since 09:50 or more than 0.20% over the last 30 minutes; target / stop 1R (0.25 ATR), flat 15:55."}`
4. `research/ledger.jsonl`: id `2026-11-16-wb-rw7-wb3`, effective next session, title "Workbench copy
   RW7-gapdn-bounce-early-short-FD-WB3 added to Testing E, first in setup_order (Mechanic pass)", patch
   `{"strategies.RW7-gapdn-bounce-early-short-FD-WB3 (testinge)": [null, "added, enabled"], "live.setup_order (testinge)": ["...", "WB3 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5"; then `python -m mcf.research.ledger check`.
5. Smoke test (the module needs the `spy_fo` context column; without it the mask fires nothing — fail safe), `python -m
   mcf.report.assignments` (docs/live/assignments.json in the same commit), `pytest -q`, commit, push after 16:05 ET (setup-freeze).
Note: live fills will be ~0.04R/trade below the bench (entry slippage, measured on the parent's matched trades).
