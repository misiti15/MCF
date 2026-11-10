Educational only — not financial advice.

# obs-rcompass-live — the rolling compass on LIVE afternoon trades (Observer, 2026-11-10 ~02:00 ET)

Lead's request lead-20261109-2300-4: which setups does the owner most need switched off on flips? Descriptive, **0 configs**.
Flip definitions imported unchanged from Scout's frozen `research/rcompass/rcompass.py` (day_flips, classify, strict <); compass rows
from Builder's `research/compassbf/compass_2y.csv.gz`. Live paper trades, all 7 accounts, run_id 1, entries >= 12:00 ET,
10-06..11-09 (25 sessions, 4,682 afternoon trades). Net R as the owner sees it. `live_flip.py` -> `live_flip_out.txt`.

## Failures / caveats first
- **Live has almost no flips to learn from.** A morning reading (10:30/11:00 checkpoint) existed on 14 of 25 sessions; F1 and F2
  flipped on ONE day (11-02). Any F1/F2 statement from live is one anecdote. F3 'softened' on 8 of 14 days, as Scout's counts warned.
- A first run double-counted rows (non-unique index after concatenating journals); caught by a count check, fixed with an assert.
- The owner-named coil family (CWT12) has only 5 afternoon trades on reading days live: it mostly fires before noon, so it cannot be
  judged on afternoon flips from live data.

## The one flip day (11-02, M = UP, F1 12:30, F2 13:15)
Post-flip trades aligned with the morning side: 158 trades, **-85.3R** (-0.54 avg). By family: GEN -30.7 (58), heat -14.5 (15),
CWT14 -11.3 (28), NM -9.3 (25), CWT13 -7.0 (18). By account: GEN -30.7, Graveyard -24.7, Testing 2 -23.5, Testing -5.4, Primary -1.1.

## The bigger live pattern: trades AGAINST the morning reading, on days it held
| afternoon trades on reading days (F1 classes) | n | avg R | total |
|---|---|---|---|
| held day, aligned with M | 1,520 | +0.074 | +111.8R |
| held day, counter to M | 1,326 | **-0.072** | **-95.5R** |
| post-flip, aligned | 158 | -0.540 | -85.3R |
Counter-to-M afternoon trades lose about as much as the one flip day cost. They happen on every reading day, not on 1 in 25.
This is the same bet as GATE1/GATE2 (trade with the side SPY holds; Skeptic's N 2,605). Scout's frozen RCOMPASS plan already splits
aligned vs counter, so it gets measured on 2y with the random-standby and market-share controls. No new look is needed.
