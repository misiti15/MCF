# arena-index-etf (swarm 2026-10-17) - NOTES

*Educational only - not financial advice. History backtests only; nothing here is paper or live.*

## Failures first
- **73,743 configurations scored** (73,636 in the pre-declared search + 107 in the amendment neighbour grids;
  73,280 unique after removing triples that appear twice in a different order).
  - N_lineage = 266,882: arena 20,282 + am-long 23,032 + am-short 22,932 + mid-long 30,752 + mid-short 30,572
    + pm-both 61,440 + idxdip1015 1,134 + indexlink 2,995 + this folder.
  - Bar = max(1.5, sqrt(2 ln N)) = **5.00**.
- **Funnel.**
  - 3,078 configurations passed the TRAIN screen gate. Only 940 of them (31%) were positive on VALID.
  - 923 were valid-positive AND beat both random controls.
  - **1 passed quality_pass**; 354 were near-misses (everything except the t-bar), 346 of them unique.
- **TRAIN selection does not transfer well.**
  - Only 1.6% of single conditions (n >= 200) have exp > 0 after costs on TRAIN.
  - 96% of the stage-2 triples are train-positive, which is selection at work.
  - Fewer than a third of the train-gate survivors hold up on VALID.
- **The single quality pass is fragile. Do NOT treat it as live-ready.**
  - Setup: AR-ETF-late-dip-di-long = ret3 <= -0.80% & di_diff7 >= 0 & atr_d_pct >= 3.60, LONG, t05s1, bar close 14:00-15:00.
  - Train +0.250R (n 281, 69 sessions, t 5.10, just over the 5.00 bar). Valid **+0.029R** (n 190, t 0.50).
  - Regime (train+valid): up +0.20R, down +0.14R. But on VALID alone, down sessions are **-0.11R**.
  - Walk-forward 0.667. 1.1 trades/day on average, but it trades on only 152 of 426 sessions (up to 52 trades in one session).
  - Concentration: the best day carries 31% of P/L (an April 2025 crash session). Train t without the best day is still 5.2, but 2026Q2 is -0.156R (n 82).
  - 79% of trades are 3x funds (SOXS 76, SOXL 58, GDXU 46, TECL 29, ...).
  - Neighbours: with the ret3 threshold kept at -0.80%, every t05s1 neighbour is positive on train and valid, but valid t <= 1.1 (except points with n < 40). Changing the geometry to t1s05 breaks it. Moving ret3 to the ETF q05 (-0.45%) turns valid negative.
  - Verdict: it clears the formal gates by 0.1 t, and the clearance comes from TRAIN concentration. The validation is weak. Research and paper only.
- **The more convincing result is a near-miss, NOT a candidate:** AR-ETF-late-dip-adx-long (near_miss/).
  - Setup: ret3 <= -0.80% & adx7 >= 63.7, LONG, t05s1, 14:00-15:00.
  - Train +0.139R (n 362, t 2.41, far below the bar). Valid **+0.126R** (n 248, t 2.97).
  - Up and down sessions are positive in both splits (valid up +0.19R, down +0.10R). Walk-forward 0.857.
  - The best day carries 16% of P/L. Capped at 3 trades per session, valid is +0.08R. Without April 2025, train is +0.07R.
  - Its family holds across about 20 third filters (robust.csv: ret3 & adx7 & x, valid t 2-3.4). It is late-day only: the same pair in 11:00-14:00 is train -0.08R, and t1s05 fails.
  - The train t is too low for the bar. VALID was used to pick it, so VALID is no longer clean for it.
- **Concentration diagnostic (robust.py), run on the 346 unique near-misses:**
  - 83 configurations stay positive under all of these: no best day, a 3-per-day cap, no April 2025, up and down sessions, best-day share < 25%, wf >= 0.6.
  - 18 of those 83 have a valid t >= 2 without the best day.
  - The best days are mostly 2025-04-04, 04-07, 04-09 and 04-10.

## What the index-ETF universe looks like after costs
- ETF rows are about 2.26M (97 symbols that reach adv20 >= $95M; VOO/IVV/VTI/RSP/SPLG are not in the frames).
- Random ETF entries lose about -0.09 to -0.11R per trade after costs. For example, all-day short: -0.106R, n 29.6k.
  The same-minute ETF control is therefore strongly negative. Excess over random of +0.10 to +0.15R is common, while
  exp itself is only around 0.
- Where anything works, it is late in the day (14:00-15:00, t05s1 small target): 248 of the 346 near-misses are 14:00-15:00.
  Shorts are mostly gap-up / high-ADX fades.
- Clustering: leveraged pairs and same-underlying funds (SOXL/SOXS, TQQQ/SQQQ/QLD, SPXL/UPRO/SSO, TNA/TZA) fire on the
  same day. Day-clustered t accounts for that, but the effective sample is sessions (60-170), not trades.

## Live notes (both modules)
- All indicators are live-computable (arena compute, context=False). The modules match the engine trades exactly on a
  2025-04 parity check (25 of 25 trades).
- **Gap:** `LabStrategy.eligible()` has no symbol allow-list. These setups were scored on ETFs only. The modules apply
  `SYMBOLS` only when the frame has a `symbol` column, and the live frame is one symbol without that column. Live use
  therefore needs a `symbols:` filter on LabStrategy (a runner change) or an equivalent prefilter. Without one, the setup
  fires on about 1,100 stocks that were never scored.
- Exits: t05s1 (target 0.5R, stop 1R, R = 0.25 x daily ATR, flat at 15:55). These are the standard lab geometries; the live runner supports them.

## Setup / method
- PLAN.md (pre-declared, with 2 dated amendments).
- Universe: the list in common.py (US index, sector and leveraged/inverse equity ETFs; adv20 >= $95M at the row).
- Split: TRAIN = 2024-10 + 2025-03..2025-12, VALID = 2026-01-01..2026-10-07. The locked block 2024-11..2025-02 was
  never loaded.
- Costs: gates.prod_r with tod entry costs, x3 on the extended tier (arena.data.outcomes).
- One trade per symbol-day (the first qualifying bar). Statistics use the gates.summary convention, and engine.py reproduces combine.trades exactly.
- Controls, where both must be beaten on TRAIN and VALID:
  - c_*: same-minute mean over the full universe.
  - e_*: same-minute mean over the ETF universe.
- Stages:
  - Stage 0: 10,704 singles.
  - Stage 1: 45,360 pairs (30 triggers x 63 filters x 4 windows x 3 geometries x 2 sides).
  - Stage 2: 17,572 triples. Only the top 150 pairs per side by train t were extended.
  - Stage 3 (VALID + full gates): 3,078 configurations (not new).
  - Neighbour grids: 107.
  - Total: 10,704 + 45,360 + 17,572 + 107 = **73,743**.

## Files
- PLAN.md, common.py, build.py (scratch rows), engine.py, search.py (stages 0-2), stage3.py, robust.py, neighbors.py
- results.csv (every pre-declared configuration: train stats; valid and full gates where scored), finalists.json
  (near-miss tier), robust.csv, neighbors_a1.csv, neighbors_a2.csv, counts.json, trades_pass.csv, trades_nm.csv
- modules/AR-ETF-late-dip-di-long.py (quality pass, flagged fragile); near_miss/AR-ETF-late-dip-adx-long.py (NOT a candidate)
