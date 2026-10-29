# p3_1029 - PLAN (written 2026-10-29 ~11:30 ET, after the live autopsy, BEFORE any two-year configuration was scored)

*Educational only — not financial advice. Two-year numbers are backtests; live numbers are paper.*

## Data, split, costs (fixed)
- Open two-year lab frames (`research/history2y/lib.load_month(..., context=True)`) + the 5-minute tail rows 15:05-15:55
  (`research/bdi/cwt/test_b/data/headtail.parquet`, filtered to the open months; the locked block 2024-11-01..2025-02-28
  is never read; `MCF_HIST_ALLOW_LOCKED` asserted unset; every trade table asserted free of locked dates).
- TRAIN = sessions <= 2025-12-31, VALID = 2026-01-01..2026-10-07. Regimes: `lib.regimes()`.
- Primary's current 8 setups (config/default.yaml enabled, docs/live/assignments.json): masks from their modules, their
  YAML window and min_adv, decision bars 09:50-15:00, first hit per symbol-day or the refire chain (MF2-FD, cooldown 1).
- Entry at the decision-bar close; stop / target = the setup's geometry on R = 0.25 x daily ATR; 5-minute path, stop
  checked first, flatten at the 15:55 bar close. Costs: 1c + 1 bp per side (entry side x `gates.tod_cost_mult`), exit side
  free on a target, +2c on stop exits, x3 on the extended tier (|gap| >= 20% or price < $5). R reported in live units
  (per unit of stop distance, = journal pnl_adj / $ risk).
- Portfolio ("parent"): one account, setups in `live.setup_order` priority within a poll, max 3 same-side lots per
  symbol, no opposite side while a lot is open, 30 open lots per setup, 77 open lots in all. ST-P (-2R latch) is live-only
  and is NOT modelled (backtests ignore it, config comment). Spread / ETB / participation skips are not modelled.

## Scoring (fixed)
- Per config: n, avg R, shrunk avg R (x n/(n+20)), day-clustered t, train / valid / up / down, w/o best day, best-day share,
  green-day share, and the rolling 10-session funding-gate pass rate (>= 7 of 10 green in R and best day <= 50% of net).
- Improvement = paired daily delta (config day total R - parent day total R), day-clustered t over all open sessions.
- **Pass** = delta t >= max(1.5, sqrt(2 ln N)) with N the lineage count below, delta > 0 in train AND valid, delta > 0 in
  up AND down sessions, shrunk avg R >= parent's in train and valid, and a positive neighbour (plateau).
- Holdout: at most ONE look at the locked block, only for a finalist that beats the parent on train AND valid in shrunk avg
  R and day-clustered t, and only if it passes the bar; otherwise no look.

## Lineage count N
Prior related configs counted in: sat1024-late-profit-lock 6 (stop raise from 15:00, failed), nightly-1027-flatten-1545
2 (live replay + bdi1027 descriptive). N = 8 + every config below.

## Bounded loop (pre-declared grids; at most 3 iterations; stop at the first iteration with a pass)
- **Iteration 1 (11):** A1 R >= $0.10/share, A2 R >= $0.15, A3 round-trip stop-exit cost <= 0.15R;
  B1 1 lot per symbol across setups, B2 1 entry per symbol per day across setups, B3 <= 2 open same-side lots per sector
  ETF, B4 <= 3 new entries per poll (priority order); C1 flatten 15:45, C2 flatten 15:30, C3 at the 15:00 close tighten
  the stop to 0.5R behind price (never loosen), C4 flatten 15:45 longs only.
- **Iteration 2 (12):** the neighbourhood of the best config (highest delta t) of each family:
  A: R >= $0.05 / 0.08 / 0.12 / 0.20 (or cost <= 0.08 / 0.10 / 0.20 / 0.25 if A3 is best);
  B: lots/symbol 2, poll cap 2 / 5, sector cap 1 / 3 (the four nearest the best B; 4 rows);
  C: flatten 15:40 / 15:50, tighten 0.25R / 0.75R at 15:00 (4 rows).
- **Iteration 3 (4):** pairs of the three iteration-2 family bests (3) and the triple (1).
- Max N = 8 + 11 + 12 + 4 = 35 (bar 2.67).

## Holdout look (added 2026-10-29 after iteration 1, BEFORE the look)
Iteration 1 had passes (A1, A2, A3 on the paired-delta bar); per the bounded loop no further iteration runs. One finalist
is chosen on VALID: **A3_cost015** (highest valid shrunk avg R and valid delta of the three). It is scored ONCE on the
locked block 2024-11-01..2025-02-28 together with the parent (`holdout.py`, the only script that sets
MCF_HIST_ALLOW_LOCKED, in its own process). Lineage look 1, so the holdout pass = paired daily delta > 0 with
day-clustered t >= 1.0, and A3 shrunk avg R >= the parent's. A pass would still not make the book positive; it only says
the cost filter's improvement holds out of sample.
