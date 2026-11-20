Educational only — not financial advice

# BEG-03 Gap-and-go continuation (long only): pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change.

## What is scored
- Setup: `beg03.py`, DESIGN.md B03 implemented as written. The plainest readings of ambiguous parts are marked [R] in
  the module docstring. The main ones:
  - "price $5-$200" is checked on the prior close; gap = 09:30 open / prior close - 1;
  - R20 = the bars 09:30..09:49; the buy-stop (R20 high + $0.01) can fill on the bars 09:50..10:59;
  - "only if the last close before the trigger is above VWAP": the order is armed for bar k only when the close of
    bar k-1 is above session VWAP; an unarmed bar cannot fill, and the order keeps working until 11:00;
  - "VWAP at signal" = VWAP at the close of bar k-1; the 0.4%-3% stop band is measured from the trigger price and an
    out-of-band bar is not armed (the order may arm on a later bar);
  - R = trigger - stop for the 2R target; the trail (1R behind the best price once the best is +1R) uses the real fill;
  - exit_by 12:00 = exit at the open of the 12:00 bar; one trade per symbol-day.
- Engine: `run.py`. Signals and exits on 1-minute bars (the setup is a 1-minute stop-entry setup). Costs, book and
  `stats()` imported unchanged from `research/ultimate_1119/top10/bench10.py`:
  - LR8 costs (entry (1c + 1 bp) x time-of-day multiplier; exit 1c + 1 bp except target limit fills; +2c on stops,
    trailing stops included; x3 extended tier for |gap| >= 20% or price < $5). Long only, so no borrow;
  - stop first; gap-through fills at the worse of open/stop after the entry bar; on the entry bar a stop touch fills
    at the stop (conservative, as engine.simulate); target fills only when traded through by $0.01;
  - testing-arena book (TESTING_RULES): cap 100, <= 3 lots per symbol, price >= $5, stop-cost filter 0.15R.
- RVOL20 = 09:30-09:49 volume / mean of the prior 14 sessions (min 5), the same day table as BEG-02 (T1 context from
  the lab frames point in time; the rolling mean never spans the locked gap, so the first sessions of 2024-10 and
  2025-03 have no RVOL and no trades). T2 uses the 469 cache_fresh names.

## Windows
- FIT = 2024-10 + 2025-03-01..2025-09-30. CHECK = 2025-10-01..2026-11-04, scored once for the base and once for the
  FIT-picked tweak. T2 = 2023-01-03..2024-09-13 (seen data, reference only). Locked block 2024-11-01..2025-02-28 never
  read.

## Control
- Random entries on the same symbol-days as the setup's trades: a market entry at the open of a random bar in
  09:50..10:59 (uniform), the same $ stop distance, 2R target, 1R trail and 12:00 exit. 5 seeds, booked the same way.

## Tweaks (step 3)
- At most 3 one-part tweaks, chosen after diagnosing the base's worst FIT losers on FIT only, written below before
  they are scored. Pick = best FIT avg R with >= 20 booked FIT trades; scored once on CHECK and once on T2.

## Verdict (research/ultimate_1119/top10/PLAN.md, testing-arena book)
- MEETS: all Tier A legs hold (T1 combined avg R >= -0.0383; T1 check >= -0.0464; w/o best day >= -0.0674 / -0.0781;
  total R/session >= -0.4862 / -0.5218; T2 avg R >= -0.1048; >= 20 trades on check and on T2).
- NEAR: not MEETS, but each failing leg is within 0.02R of its threshold (avg-R legs; R/session legs judged the same
  way in R units).
- FAIL: everything else. REALLY BAD reported as defined there.
- Configurations: base = 1, random control = 0 fitted, tweaks <= 3.

## Control note (added after the base was scored, before any tweak; no configuration fitted)
The pre-registered random control is biased upward for a stop-entry setup: it is drawn only on days where the
buy-stop later fills, and a random bar *before* the setup's fill knows a breakout is coming (those draws average
+0.63R on the base). Two extra controls are reported beside it, neither fitted: `after` (random bar at or after the
setup's own fill bar, same $ stop and exits; 3 seeds) and `univ` (every universe day, random bar in the window, the
setup's stop rule max(R20 low, VWAP) - $0.02 and band, no trigger condition; 3 seeds).

## Tweaks (pre-registered 2026-11-20, after the FIT-only diagnosis in diag.py and before any tweak was scored)
FIT diagnosis of the base (321 booked, avg R −0.058, gross −0.005, cost ~0.053R/trade):
- Exits: 114 full initial-stop losers cost −122R; 43 targets +67R; 105 12:00 time exits +19R (+0.19 each); 59 trail
  stops +0.29 each. Targets/time exits are not where the loss is; the losers are full stops held 15-60 min (not
  instant noise: only 5 within 5 min).
- **Entry timing is the clearest split:** fills 09:50-10:14 −0.01 (238 trades) vs 10:15-10:59 −0.20 (83 trades,
  −16.9R, nearly the whole loss). A breakout of the opening range that only comes after 10:15 is stale.
- Filter: gaps 3-5% are the weakest bucket (−0.124, 108 trades); gaps >= 5% −0.02.
- Stop: wide stops 1.8-3% of price −0.148 (167 trades); 1.2-1.8% +0.128.
- Most of the 25 worst losers are full stops; the biggest are wide-stop (2.2-3%) high-gap names (APLD, SOUN, ECHO,
  OSCR) and late fills.

The three one-part tweaks:
- **T1 `win1015`** (window): the buy-stop works on the bars 09:50..10:14 only (instead of ..10:59).
- **T2 `gap5`** (filter): gap >= +5.0% instead of +3.0%.
- **T3 `stopmax2`** (stop): the stop band's upper limit is 2.0% of price instead of 3.0%.
Pick = best FIT avg R with >= 20 booked FIT trades; scored once on CHECK and T2. Configurations: 1 base + 3 = 4.
