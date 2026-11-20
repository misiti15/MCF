Educational only — not financial advice

# BEG-02 VWAP first pullback: pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change.

## What is scored
- Setup: `beg02.py`, DESIGN.md B02 implemented as written. Where the spec is ambiguous the module docstring marks the
  plainest reading with [R]. The main ones:
  - price >= $10 is checked on the prior close;
  - "price at 09:50" is the close of the 09:49 bar;
  - one look per symbol-day: the first pullback bar. If its target room is < 1.5R, there is no trade that day;
  - R and the 2R/1.5R target tests use the trigger-bar close (the price known at the decision). The fill is the next
    bar's open, and the booked R uses the real fill.
- Engine: `run.py`. Signals and exits use 1-minute bars, because the setup is defined on 1-minute bars. Everything
  else follows the bench10 "normal way":
  - LR8 costs (entry (1c + 1 bp) x time-of-day multiplier; exit 1c + 1 bp except target limit fills; +2c on stops;
    x3 extended tier), plus 1.2 bp borrow on shorts;
  - stop first, with a gap-through filling at the worse of open/stop; a target fills only when traded through by $0.01;
    flat at the 15:55 open;
  - the testing-arena book (TESTING_RULES): cap 100, <= 3 lots per symbol, price >= $5, ETB >= 90% for shorts, stop-cost
    filter 0.15R;
  - the same `stats()`: avg R, avg R w/o best day, best-day share, total R/session, day-clustered t, SPY day types.
- rank_rvol20 is mcf.backtest.engine's rule: the 09:30-09:49 volume / the mean of the prior 14 sessions (min 5),
  ranked among the day's U0 names (prior close >= $5, ADV20 >= $20M).
  - T1 daily context (ATR, ADV20, gap -> prev close) comes from the lab frames, point in time.
  - The rolling volume mean never spans the locked gap, so about the first 4 sessions of 2025-03 have no rank and
    no trades.
  - T2 ranks among the 469 cache_fresh symbols, a smaller universe, so top-50 is a wider cut there. T2 is reference
    only.

## Windows
- FIT = 2024-10 + 2025-03-01..2025-09-30.
- CHECK = 2025-10-01..2026-11-04, scored once for the base and once for the fit-picked tweak.
- T2 = 2023-01-03..2024-09-13. This data was seen before, so it is reference only.
- The locked block 2024-11-01..2025-02-28 is never read.

## Control
- Random entries: on the same symbol-days, with the same side, the same $ stop distance and the same target multiple
  as each setup trade.
- The entry minute is uniform over the signal window. The exits are the same.
- 5 seeds, booked the same way.

## Tweaks (step 3)
- At most 3 one-part tweaks.
- They are chosen after diagnosing the base's worst FIT losers, using FIT only.
- They are written into this file (section "Tweaks") before they are scored.
- The best FIT avg R wins, provided it has >= 20 FIT trades. It is scored once on CHECK and once on T2.

## Verdict (research/ultimate_1119/top10/PLAN.md, testing-arena book)
- MEETS: all Tier A legs hold (T1 combined avg R >= -0.0383; T1 check >= -0.0464; w/o best day >= -0.0674 / -0.0781;
  total R/session >= -0.4862 / -0.5218; T2 avg R >= -0.1048; >= 20 trades on check and on T2).
- NEAR: not MEETS, but each failing avg-R leg is within 0.02R of its threshold.
- FAIL: everything else.
- REALLY BAD is reported as defined there.
- Configurations: the base = 1, the random control = 0 fitted, the tweaks <= 3.

## Tweaks (pre-registered 2026-11-20, after the FIT-only diagnosis in diag.py and before any tweak was scored)
FIT diagnosis of the base (505 booked trades, avg R −0.146):
- **The stop is the failure.** 434 of 505 trades (86%) sit on the 0.15 x ATR floor, because the pullback bar is tiny.
- 167 trades stopped out within 5 minutes, for −113.7R. That is more than the whole −73.5R loss. Trades held
  15+ minutes are positive.
- Costs are ~0.10R a trade on these tight stops.
- 09:50-10:00 signals (−0.20) and 10:30-12:00 signals (−0.21 / −0.28) are weaker than 10:00-10:30 (−0.06).

The three one-part tweaks:
- **T1 `stop030`**: stop floor 0.30 x ATR instead of 0.15 x ATR (stop part).
- **T2 `stopx15`**: the stop distance (after the 0.15 x ATR floor) x 1.5 (stop part).
- **T3 `win1000`**: entries from the 10:00 signal bar instead of 09:50 (window part).

Under T1/T2 the targets (2R, min 1.5R room), the +0.5R time-stop test and the cost filter all scale with the wider
R, as written. Pick = best FIT avg R with >= 20 booked FIT trades. It is scored once on CHECK and T2. Configurations:
1 base + 3 tweaks = 4.
