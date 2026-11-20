Educational only — not financial advice

# BEG-10 Narrow-range day -> first-30-minute breakout: pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change.

## What is scored
- Setup: `beg10.py`, DESIGN.md B10 implemented as written. Where the spec is ambiguous, the module docstring marks the
  plainest reading with [R]. The main readings:
  - price >= $10 is checked on the prior close; ADV = point-in-time ADV20 >= $30M (U0's $20M is implied);
  - yesterday's range = the prior RTH session's high - low from the 1-minute bars; ATR = daily ATR14 at the prior close
    (the BEG-02 day tables). A prior session more than 5 calendar days back (only 2025-03-03, after the locked gap)
    gives no flag, so that day is skipped;
  - OR30 = high/low of the 09:30..09:59 bars; skip if its range > 0.8 x ATR;
  - the OCO pair is placed at the 09:59 bar close and works on the 10:00..12:29 bars ("valid until 12:30");
  - fill = max(open, trigger) (short: min). If one bar touches both triggers, the side whose trigger is nearer that
    bar's open fills. On a non-ETB name (ETB >= 90% of snapshots, the bench10 proxy) only the buy-stop is placed;
  - stop = OR30 midpoint (unrounded); target = trigger + 2 x (trigger - stop) (2R on the order price); the booked R uses
    the real fill. Flat at the 15:55 open. The stop is checked first, including on the fill bar (conservative);
  - one trade per symbol-day.
- Engine: `run.py`, following the bench10 "normal way" (as BEG-02/03/09):
  - LR8 costs (entry (1c + 1 bp) x time-of-day multiplier; exit 1c + 1 bp except target limit fills; +2c on stops;
    x3 extended tier), plus 1.2 bp borrow on shorts;
  - a target fills only when traded through by $0.01; gap-through stops fill at the worse of open/stop;
  - the testing-arena book (TESTING_RULES): cap 100, <= 3 lots per symbol, price >= $5, ETB >= 90% for shorts,
    stop-cost filter 0.15R;
  - the same `stats()`: avg R, avg R w/o best day, best-day share, total R/session, day-clustered t, SPY day types,
    plus long/short splits.
- T2 ADV/ATR/prev close are built from the 469-symbol cache_fresh 1-minute bars (BEG-02 tables); reference only.

## Windows
- FIT = 2024-10 + 2025-03-01..2025-09-30.
- CHECK = 2025-10-01..2026-11-04, scored once for the base and once for the fit-picked tweak.
- T2 = 2023-01-03..2024-09-13 (seen before; reference only).
- The locked block 2024-11-01..2025-02-28 is never read.

## Control (random entries, 0 fitted configurations)
- Every ARMED symbol-day (NR day, OR30 passes, OCO placed; filled or not). Side drawn at random (long, or short if
  ETB); entry at the open of a bar drawn uniformly from 10:00..12:29; the same $ stop distance (trigger to OR30
  midpoint) and the same 2R target; same exits, costs and book. 5 seeds.

## Tweaks (step 3)
- At most 3 one-part tweaks, chosen after diagnosing the base's worst FIT losers, using FIT only, written into this
  file (section "Tweaks") before they are scored.
- Pick = best FIT avg R with >= 20 booked FIT trades. Scored once on CHECK and once on T2.

## Verdict (research/ultimate_1119/top10/PLAN.md, testing-arena book)
- MEETS: all Tier A legs hold (T1 combined avg R >= -0.0383; T1 check >= -0.0464; w/o best day >= -0.0674 / -0.0781;
  total R/session >= -0.4862 / -0.5218; T2 avg R >= -0.1048; >= 20 trades on check and on T2).
- NEAR: not MEETS, but each failing avg-R leg is within 0.02R of its threshold.
- FAIL: everything else. REALLY BAD reported as defined there.
- Configurations: base = 1, random control = 0 fitted, tweaks <= 3.

## Tweaks (pre-registered 2026-11-20, after the FIT-only diagnosis in diag.py and before any tweak was scored)
FIT diagnosis of the base (13,733 booked trades, 80.8/session with the cap of 100 often binding; avg R −0.053, gross
+0.027, total −727.6R; base CHECK and T2 were also scored once as the base step requires, but nothing below uses them):
- **Fast stop-outs carry the loss.** 6,735 stops (49%) = −7,527R; 2,899 targets = +5,450R; 4,099 time exits at 15:55
  = +1,349R (avg +0.33). The worst 10% (1,373 trades, −1,658R) are all stop-outs, median hold 35 min, median risk
  0.17 x ATR (all trades 0.21), median cost 0.16R. Trades held > 2 h average +0.23R; trades stopped within 30 min
  average −0.55..−0.73R. The OR30-midpoint stop sits inside ordinary post-breakout noise.
- **Cost bites on the tight stops.** Cost-R > 0.10: 2,915 trades averaging −0.85R; risk < 0.15 x ATR averages −0.07..
  −0.12R.
- **Narrow opening ranges are worst.** OR30 < 0.2 x ATR: −0.135; 0.2-0.3: −0.064; 0.3-0.8: −0.03..−0.05.
- **Late fills are worse.** Fills 10:00-10:15: −0.03..−0.04 avg R; 10:15-11:00: −0.08; 11:30-12:30: −0.12.
- Shorts lose more than longs (−0.084 vs −0.028). Not used as a tweak (side split is not one of the spec's parts
  chosen here; reported in RESULTS as the remedy table).

The three one-part tweaks:
- **T1 `stopx15`** (stop part): the stop distance (trigger to OR30 midpoint) x 1.5; the 2R target scales with it.
- **T2 `win1015`** (window part): the OCO pair works on the 10:00..10:14 bars only (valid until 10:15, not 12:30).
- **T3 `ormin03`** (filter part): also skip the day if the OR30 range is < 0.3 x ATR.

Pick = best FIT avg R with >= 20 booked FIT trades; scored once on CHECK and once on T2. Configurations: 1 base +
3 tweaks = 4.
