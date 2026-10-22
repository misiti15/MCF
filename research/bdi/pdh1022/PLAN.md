# pdh1022 pre-declaration: rework of CWT14-failbrk-pdh-p10-short (owner 2026-10-22)

*Educational only - not financial advice.*

Written 2026-10-22 ~12:20 UTC (08:20 ET), **before any history configuration below was scored**. Results go in
`NOTES.md`; this file is not changed afterwards. Research only: no config / setup / exit change (market hours).

Owner (2026-10-22): p05-lowvol and p10-lowvol siblings to the Graveyard; keep "Failed Prior-Day-High Break Short
(0.1 ATR)" in Testing 1 and "rework the remaining setup with variants and changes to see if anything is slightly more
viable for testing". Merit rule for adding: pass the Testing bar, or a near-miss positive after costs in BOTH train and
valid, beating random in both, >= 30 / 20 trades, no single day > 25% of total R.

## 1. Parent (live config, Testing 1)
`cwt_live_lib.b3(level='PD', p=0.10, lowvol=False, side='short')`: price trades >= 0.10 x daily ATR above the prior-day
high, then a 5-minute bar closes back below it within 3 bars. Short at that bar's close; t05s1 (target 0.5R, stop 1R,
R = 0.25 x daily ATR), flat 15:55; window [950, 1200]; min_adv 95M; no scale-out; no refire (first signal per
symbol-day in the window).

## 2. Diagnosis (descriptive, not counted)
- **Live (paper, rule 7):** all CWT14-failbrk-pdh-p10-short rows in `reports/*.csv` on origin/mcf-data-testing and
  origin/mcf-data-testing2, run_id 1 (8 sessions 10-12..10-21). By regime (regime1022 labels), date, time of day,
  MFE/MAE, win/loss size, lots per symbol-day, exit reason.
- **History (parent):** by regime (Bull / Bear / Choppy / Quiet, regime1022 definition on SPY's lab daily bar), time of
  day, poke extension above PDH (max high in the excursion, ATR), bars to failure, poke / failure volume ratio, gap,
  RS vs SPY (stock fromOpen - SPY fromOpen), SPY vs VWAP, QQQ vs open, breadth level / slope, MFE / MAE and the
  win/loss asymmetry (losers that never reached +0.2R, winners' MAE).

## 3. Harness, data, costs, splits
`top5_1019/scan_1019.py` (build_paths with 09:35-09:45 head rows, `sim`, `base_ok`, `next_after`) and
`top5_1015/scan_1015.py` (random-control pool) unchanged; costs as every top-5 run (entry 1c + 1 bps x ToD multiplier,
limit target free, stops +2c, market exits 1c + 1 bps). A new short-PDH kernel (`scan.py:_b3s`) adds the poke row and
the excursion high to the parent state machine; **parity gate**: its flag == `cwt_live_lib.b3` on 2025-06, and the
parent P == `gates.lab_trades` / `scan_top5.trades` (mean |d| < 0.002R, >= 99% within 0.01R).
Open months only; the locked block 2024-11-01..2025-02-28 is never loaded (`MCF_HIST_ALLOW_LOCKED` never set).
TRAIN <= 2025-12; VALID 2026-01..03 + 07..09-15; HOLD (2026-04..06, 2026-09-16..10-07) scored once, only for a
variant that meets the Testing bar or the merit rule. Random control: 5 same-minute random symbols (adv >= 95M), same
mechanics and risk in ATR units, seed 20261022. Wider-stop rows at the same $ risk (target price fixed; r divided by
the stop multiple).

## 4. Grid, stage 1 (one knob per row; every row counts) - 36
| id | knob |
|---|---|
| D05 / D20 | break depth 0.05 / 0.20 ATR |
| C05 / C10 | failure bar closes >= 0.05 / 0.10 ATR below PDH |
| K1 | fast failure: back below PDH within 1 bar of the poke (parent 3) |
| LH | lower high: next bar's high < failure bar's high and its close < PDH; enter at that bar's close |
| VF | volume fade: failure-bar volumeRatio < poke-bar volumeRatio (NaN poke ratio -> no signal) |
| HV | poke bar volumeRatio >= 1 (the complement of the Graveyard lowvol sibling) |
| W1 | wait one bar (enter at the next bar's close) |
| XS / XD | poke extension (max high above PDH in the excursion) <= 0.30 ATR / > 0.30 ATR |
| T075 / T100 | target 0.75R / 1.0R |
| SO35 | scale out half at +0.35R, stop to breakeven |
| BE35 | breakeven after +0.35R |
| T100BE50 | target 1.0R + breakeven after +0.5R (owner's "BE after +0.5R"; with a 0.5R target it is a no-op) |
| TS30 / TS60 | time stop 30 min if best < +0.2R / 60 min if best < +0.25R |
| S125 / S150 | stop x1.25 / x1.5, same $ risk, target price unchanged |
| WF10 / WF1030 | window from 10:00 / 10:30 |
| WU11 | window until 11:00 |
| WU1430 | window extended to 14:30 |
| FF | first failure of the day only (the symbol-day's first b3 flag, head rows included, must be the entry) |
| RE | re-entry after exit, 30-min cooldown (lot-stacking check) |
| FSV | SPY below its VWAP at the signal bar (lab only; live context has no SPY VWAP -> needs an mcf change) |
| FSO | SPY below its open (context spy_fo < 0) |
| FQO | QQQ below its open (context qqq_fo < 0) |
| FBF | breadth falling: breadth now < breadth 3 bars earlier (context breadth) |
| FBL | breadth < 0.50 |
| FRS | stock RS weak: stock fromOpen < SPY fromOpen |
| G05 / G1 / G2 | skip gap-ups > 0.5% / 1% / 2% |

## 5. Grid, stage 2 (pairs, chosen on TRAIN only) - 12
- The 3 best stage-1 **entry / window / lot / filter** knobs by TRAIN exp (TRAIN n >= 1,000), each x {S150, SO35, T075}
  = 9.
- The 3 pairs among the 3 best TRAIN-ranked **filters** (FSV..G2) = 3 (skipped pairs are still counted).

**N (study) = 48.** Study bar max(1.5, sqrt(2 ln 48)) = **2.78**. CWT14 lineage N 121,396 + 48 -> bar **4.84**.

## 6. Bars (fixed now)
- **Testing bar:** exp > 0 on TRAIN and on VALID; VALID day-clustered t >= 2.78; TRAIN+VALID day-clustered t >= 4.84
  (lineage); excess over random > 0 on TRAIN and VALID; ex-best-day > 0. Then HOLD once.
- **Owner merit rule (near-miss):** exp > 0 after costs on TRAIN and on VALID, excess over random > 0 on TRAIN and on
  VALID, n_train >= 30 and n_valid >= 20, no single day > 25% of TRAIN+VALID total R. Then HOLD once (reported, not a
  gate unless negative by more than its own SE x 2).
- **Beats parent** (backlog `rework`): d > 0 on TRAIN and VALID and day-block bootstrap t_improve (1,000) >= 2.78.
- Every row reported in `results.csv`, failures first; by-regime (Bull / Bear / Choppy / Quiet) for every row.
- A passing variant gets a lab module in `modules/` (parity verified) and a DECISION line (P1 / P2) proposing it as a
  **new** Testing 1 setup. Otherwise one FYI line.
