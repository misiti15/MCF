# Diagnosis — Generated: Lunch New-Low Short (selling) `GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short` (Testing D; SHORT)
Educational only — not financial advice. Mechanic, 2026-11-16 (built 13:30-15:00 ET, during market hours: research files only,
no config touched, nothing deployed).

Engine: `..._engine.png` (P1..P28, blueprint `GEN-261026-03-...-short.md`). The engine view draws P25 as "stop 1.0R"; the
holdtr geometry also trails the stop 1R behind the best low once the trade is +1R (LabStrategy TRAIL, runner trail_r /
trail_after_r) — called **P25b trail** below.

**Few live trades: this job leans on the 2-year backtest, and says so.** Live evidence = all **21 live trades in 5
sessions** (10-26, 10-27, 10-29, 11-02, 11-03), every one in the Setup Generator account (Gen sizing, no cost filter).
None yet in Testing D (from session 11-12; no qualifying signal on 11-12 / 11-13 in the replay either). 41 live signals:
8 blocked by the Gen account halt, 7 not shortable / ETB, 4 spread checks, 1 rejected. Avg +0.379R, but **77% of the R came on one day
(10-27)** and two trades (PAYX +3.59R, FICO +3.32R) made 6.9 of the 8.0R; w/o the best day +0.129R. The 2-year backtest
of the parent as it now runs (Testing D cost filter, LR8 costs, 1-minute fills) is **−0.039R on 1,180 trades** — the
live record is a good streak on a near-zero-or-negative machine. The live record is NOT used in the pass decision.

Rule-change context inside the live window (research/ledger.jsonl): Gen caps 80 → 200 slots, 16 → 48 per setup
(2026-10-26 GX2, the first live day); generator paused after 10-28; temporary move Gen → Testing 2 for 11-09 / 11-10
(EXPO1109, no trades) and back; **graduated Gen → Testing D from session 11-12** (GEN-GRAD), where the 0.15R cost filter
applies (Gen had none) and the Testing D per-setup cap is 30 (11-12) → 50 (ROT1 spotlight 11-16..11-19); Gen sizing
change 11-12 (REPV-1); LR8 cost allowance from 11-12. All backtests below use LR8 costs and the Testing D cost filter
throughout, so setup results are not mixed with these changes.

Replay parity: the rebuilt replay (SIP 1-minute bars, lab frames as live, breadth_open from 5-minute universe bars)
reproduces **all 21 live trades** on the same symbol-day, 20 of 21 on the same signal bar (OXY 12:50 vs live 13:10); live
took 21 of the 85 replay trades on those 5 days (cost filter off, as Gen) (Gen halt, per-setup cap, ETB, spreads). Module parity: the three copies'
own `mask()` on rebuilt frames give exactly the harness's signals (54 / 80 / 38 of 54 / 80 / 38).

## The 5 worst and 5 best live trades
Sensor values recomputed from SIP bars with the module's own indicator code. from_pc = close vs prior close in daily
ATRs at the signal bar (WB1's new sensor). costR = Testing D stop-cost check ((2 x (1c + 1 bp) + 2c) / 1R; skip > 0.15).

| Trade (chart) | What happened | Part behind it | Catalogue part | What a small tweak does to THIS trade |
|---|---|---|---|---|
| worst1 JD 11-03 −1.14R (`_worst1_JD_2026-11-03.png`) | 12:00 signal: JD had **gapped up +2.05 ATR** and was still +1.15 ATR above the prior close; first new low of a gap-fade, 1R only $0.14 on a $27 stock; MFE +0.04R, back up to the stop at 13:34 | P11 measures the drop from the OPEN only, so a gap-up fade qualifies; P19 cost (0.34R) | Sensors / Intake | WB1 skips (from_pc +1.15) → +1.14R. Testing D cost filter also skips it (costR 0.34) |
| worst2 FISV 10-26 −1.13R (`_worst2_FISV_2026-10-26.png`) | 13:45 signal, last 15 min of the window; from_pc −1.61; MFE +0.12R, stopped 14:14 | P6 late window | Timer | WB2 / WB3 skip (after 13:00) → +1.13R; WB1 keeps it; Testing D cost filter skips it (0.17) |
| worst3 CCEP 10-29 −1.12R (`_worst3_CCEP_2026-10-29.png`) | 11:55 signal; gapped up +0.49 ATR, only −0.59 ATR vs prior close; MFE +0.19R, stopped 12:49 | P11 (gap-fade again) | Sensors | WB1 skips → +1.12R |
| worst4 TOST 10-26 −0.86R (`_worst4_TOST_2026-10-26.png`) | 12:30; −0.80 ATR vs prior close; drifted up all afternoon, flattened 15:55 | P11 (shallow day-drop) / P28 | Sensors | WB1 skips; cost filter skips (0.17) |
| worst5 CAVA 10-26 −0.27R (`_worst5_CAVA_2026-10-26.png`) | 12:30; −1.12 ATR vs prior close; MFE +0.61R then back up (replay: full stop −1.09R; live exited at 50.94, below the journal stop) | P25 stop / P11 | Stop / Sensors | WB1 skips. Stop / trail tweaks: none helps over 2 years |
| best1 PAYX 10-27 +3.59R (`_best1_PAYX_2026-10-27.png`) | 11:50; −1.35 ATR vs prior close; trended down into the close, flattened 15:55 | works as designed (P28 flat) | — | WB1 keeps; WB2 keeps |
| best2 FICO 10-26 +3.32R | 12:20; −2.75 ATR vs prior close (gap down −1.80 ATR); +4.58R MFE, trailed out (P25b) | works (trail) | — | WB1 keeps |
| best3 SU 10-27 +1.49R | 12:55; −1.03 ATR vs prior close | works | — | WB1 MISSES it (the filter costs some winners) |
| best4 XLB 11-03 +0.88R | 11:45; −1.33 ATR | works | — | WB1 keeps; Testing D cost filter would skip it (0.28) |
| best5 DKS 11-03 +0.84R | 12:20; −1.06 ATR | works | — | WB1 misses it |

**Live read:** the losers split into two kinds — **gap-up fades / shallow day-drops** (JD, CCEP, TOST: the stock is not
actually weak on the day, it only fell from a high open) and **late-window entries** (FISV 13:45). WB1 skips 4 of the 5
worst and keeps the 2 biggest winners: on these 21 trades it keeps 8 at +0.910R (+7.28R) and skips 13 at +0.052R (+0.68R).
WB2 skips 3 (−0.32R avg). Too few trades to decide anything — hence the 2-year test.

## All trades, component by component (2-year backtest, parent as it runs in Testing D: 1,180 trades, 230 sessions)
Train = open months to 2025-12 (479 trades, −0.025R), valid = 2026-01..10-16 (701 trades, −0.048R). Replay (15 sessions
10-26..11-13): 87 trades +0.044R, w/o best day −0.132R.
- **Exhaust (P25 stop / P25b trail / P28 flat 15:55):** stop 440 (37%) −1.152R (25% had been +0.5R first); trail 384
  (33%) +0.766R; 15:55 flat 353 (30%) +0.481R (median MFE +0.87R). Median hold 111 min. Every exhaust tweak loses in one
  test or both: stop 1.25R −0.086 / stop 0.75R −0.093; 1R 0.20 / 0.30 ATR −0.057 / −0.046; no trail −0.086; trail after
  +0.5R −0.046 (replay = parent); trail 0.5R −0.025 but replay +0.007 (from +0.044); trail 1.5R −0.068; target 2R / 1.5R
  −0.033 / −0.037 (replay lower); breakeven +0.5R −0.060; max hold 120 −0.032 (replay lower); exit at 60 min if MFE < 0.3R
  −0.038 / +0.006. Flat 15:00 passes (−0.024 / +0.089) and 14:30 too (−0.028 / +0.071), small. **The exhaust is not where it
  bleeds.**
- **Sensors — the clearest pattern: weakness vs the prior close.** P11 (fromOpen_atr <= −0.78) only measures the drop
  from today's open. Quartiles of close vs prior close (from_pc_atr) at the signal bar: <= −1.34 ATR **+0.129R** (train
  +0.179 / valid +0.094); −1.34..−1.01 −0.086; −1.01..−0.73 −0.133; > −0.73 −0.065. Same story from the gap: gap up
  > +0.25 ATR −0.142R (train −0.091 / valid −0.171). A stock already down hard on the day keeps falling through lunch; a
  gap-up stock that has only faded from its open snaps back. Threshold curve (`..._wb1_frompc_curve.png`): none −0.039,
  −0.8 −0.034, −1.0 −0.011, −1.1 +0.042, −1.2 +0.071, **−1.3 +0.090**, −1.4 +0.124, −1.5 +0.102, −1.75 +0.065, −2.0 +0.021
  (2-year); train and valid both positive from −1.1 to −1.5. −1.3 sits in the middle of the plateau.
  Other sensors: flow3 (P10) quartiles flat (−0.041 / −0.033): −0.50 −0.042, −0.25 −0.049; fromOpen (P11) −1.0 −0.060,
  −0.6 −0.067 (no monotone pattern); new_lod (P12) is the trigger, kept. Volume ratio <= 1.0 +0.019 (replay lower);
  below VWAP 0.5 ATR −0.019 (replay lower); below the prior-day low −0.057; ret12 <= −0.5% −0.034 / +0.070 (small);
  RSI(7) >= 20 −0.010 (replay −0.181); ATR% >= 2.5 −0.017 / +0.105 (replay worst day −6.25R); day range <= 1.5 ATR −0.046.
- **Timer (P6 / P7):** by entry time 11:30-12:00 +0.011, 12:00-12:30 +0.022, 12:30-13:00 −0.045, 13:00-13:30 −0.031,
  **13:30-14:00 −0.207R (train −0.139 / valid −0.249)**. End 13:00 (WB2) −0.001 / +0.153; end 14:30 −0.071; start 11:00
  −0.026 / −0.011 (replay); start 12:00 −0.067.
- **Gates (P13 breadth_open > 0.5):** this gate carries the setup — off −0.147R on 5,322 trades, > 0.4 −0.110, > 0.6
  −0.064. Market state after 09:50 (owner direction rule: SPY % since the 09:50 bar close): <= 0 −0.006 / +0.258 but
  replay w/o best day −0.541; <= +0.3% −0.035 / −0.060; >= 0 −0.057. None kept. Day type (end-of-day label, diagnostic
  only): up −0.123R (662), flat −0.051 (399), down +0.474 (119).
- **Intake (P2 ADV / P19 cost filter):** ADV >= $250M −0.018 / +0.112 (passes, not spawned: smaller than WB1, 40% fewer
  trades); $200M / $300M −0.051 / −0.065 (2-year worse); $100M −0.048. Cost filter off (as Gen ran) −0.075 / +0.004 — the
  Testing D filter already helps; 0.10 −0.041 / +0.076 (about equal). Price > $400 −0.117R.
- **Entry (P21):** fill 2 minutes after the bar instead of 1: −0.047 / −0.024 — the edge is fill-sensitive.
- **Refire / caps (P9 / P15 / P16):** 5.1 trades per session, up to 28; worst day −9.58R (2026-05-18, 20 trades). A
  per-setup daily cap of 8 passes (−0.019 / +0.216; 5 −0.052 / +0.239; 12 −0.031 / +0.057), but there is no per-setup
  daily-cap knob live (only the account-wide `max_trades_per_day`) — backlog. 2 lots per symbol −0.046.
- **Removed vs kept by WB1 (2-year):** removed 822 trades at −0.132R (train −0.120 / valid −0.140), kept 359 at +0.090R
  (train +0.084 / valid +0.095); Welch t 2.92. The new sensor removes the dead weight in both halves.

## Candidate tweaks (one part each) → spawned
1. **WB1 — new sensor P11b: close vs prior close <= −1.3 daily ATRs** (short only names genuinely weak on the day).
2. **WB2 — P6/P7 window end 14:00 → 13:00** (drop the late-window bleed).
3. **WB3 — WB1 + WB2** (combo, counted as its own config).
Results and the decision: RESULTS.md.

## Fidelity notes (same for parent and copies)
- The 2-year frames carry no earnings blackout here (the generator's earnings file is not in this checkout), so earnings
  days are in for parent and copies alike; live skips them.
- Borrow (ETB / shortable), halts and spreads are not modelled (live skipped 7 of 41 signals as not shortable / ETB).
- Replay breadth_open is computed from 5-minute SIP bars of the universe file's names with ADV >= $20M (median 2,541
  names per bucket); on the 8 overlapping days it matches the 2-year context table within 0.011 on average (sign of
  > 0.5 agrees 93%; 10-28 differs, no live trade that day).
