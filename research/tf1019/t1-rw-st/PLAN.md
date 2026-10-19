# t1-rw-st - timeframe test of RW1-RW7 -FD, ST1-ST8 -FD, L3-* -FD, exhaustion_short-FD (pre-declared 2026-10-19 02:55 UTC)

Educational only - not financial advice.

Written before any number was looked at. Harness: `mcf.research.timeframes` (frames_tf, costs in: production-cost R,
time-of-day entry costs, first qualifying bar per symbol-day). Locked block 2024-11..2025-02 never loaded.

## Setups (19 parents, all from research/bdi/fullday/, window [950, 1500], each module's own SIDE/GEOM, specs.json min_adv)
RW1, RW2, RW3, RW4, RW5, RW6, RW7 (-FD); ST1..ST8 (-FD); L3-gap-slope-fromopen/-lowdist/-rsi5hi (-FD); exhaustion_short-FD.
RW6G1 is not in the task list and is not tested. Live prefilters (new_high_100m, gap_le) are live speed guards, not
research conditions (gap_le duplicates the L3 mask; new_high_100m is implied by bear_div) and are not applied.

## Configurations
- (a) module as-is on decision bars m in {1, 3, 5, 10, 15}: 19 x 5 = **95 configurations**. Universe = "core" (80 symbols
  with 1-minute frames) for a like-for-like comparison across all five timeframes. Nothing else is varied.
- (b) "time-equivalent" (bar-count lookbacks scaled by 5/m): **not run, 0 configurations**. None of these modules exposes a
  bar-count parameter: every lookback (RSI 14 / RSI 5, SMA20/50, SMA20 slope, 19-bar buyPressure, 20-bar divergence,
  volume ratio, heat components, flow3) is hard-coded in mcf.research.heat.heat_frame / setup_lab.extra_features and
  stored precomputed in the frames. Scaling needs a parametrised rebuild of the frames from 1-minute bars (disk is at
  3 GB free) - not simple; returned as a backlog item instead.
- N_lineage = prior lineage count (research/swarm1017 NOTES) + this study's tries of that lineage:
  MF (RW1, RW3, RW5, RW7) ~203,800 + 20; NS (RW4, RW6) ~114,400 + 10; exhaustion (RW2, exhaustion_short) ~967,100 + 10;
  ST ~227,400 + 40; L3 ~315,800 + 15. Bar = max(1.5, sqrt(2 ln N_lineage)) ~ 4.8-5.3.

## Samples
- Gates on the open history: train (2024-10 + 2025-03..2025-12) + valid (2026-01-01..2026-10-07).
- Forward 2026-10-08..10-16 (7 sessions) is reported only, never used to choose.

## Gates (a candidate must pass ALL on its own timeframe)
1. exp_r > 0 and day-clustered t >= bar(N_lineage); 2. train exp > 0 AND valid exp > 0; 3. regime: up AND down session
exp > 0, each n >= 30; 4. walk-forward share >= gates.WF_MIN_SHARE; 5. mean excess vs the random same-minute baseline > 0.
A passing version is written as a lab module (parent copy + BAR_MINUTES = m) under modules/. No config/ledger/backlog
writes.

## Lookback note (as-is)
Lookbacks are in bars: RSI14 spans 14 / 42 / 70 / 140 / 210 minutes on 1 / 3 / 5 / 10 / 15-minute bars; SMA50 spans
50 / 150 / 250 / 500 / 750 minutes (across sessions); 20-bar divergence 20 / 60 / 100 / 200 / 300 minutes.
