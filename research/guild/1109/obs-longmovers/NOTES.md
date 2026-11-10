Educational only — not financial advice.

# obs-longmovers — our long trades vs the Move Hunt long movers (Observer, 2026-11-09, market hours, journals only)

Lead's request lead-20261109-1058-3. Descriptive, **0 configs**. `longmovers.py` -> `longmovers_out.txt`.
150 tradable long movers (25/day, 10-29..11-05), long trades from all 7 account journals (run_id 1), caught window as moves.py.

## Failures first
- We caught **21 of 150 (14%)**, and only **3 of 67** that start at the 09:35 bar. 11-05 (crash day): 0 of 25.
- In-window long trades: 35, **+3.31R total, +0.09 avg** — we catch the name but little of the move (median MFE of catchers ~0.4R
  on movers of ~1.1 ATR).
- 26 missed movers were bought **only after their extreme**: 42 late long trades, **-23.2R** (-0.55 avg, median 58 min after the
  top); GEN owns -20.9R of it (one setup GEN-261021-05 -9.0R on 8).
- Small n, 6 sessions, one regime-heavy week; descriptive only.

## What the caught ones share (ex-ante values at the move's decision bar, from moves.csv; medians caught vs missed)
| | caught (21) | missed (129) |
|---|---|---|
| fromOpen % | **-1.72** | -0.02 |
| RSI(14) | **23** | 49 |
| VWAP dist % | -0.60 | -0.09 |
| dist to HOD (ATR) | 0.81 | **0.23** |
| gap % | -0.33 | +0.49 |
| rvol | 1.36 | 1.30 |

We catch long movers **only when they start as a reversal from a dip** (CWT14 failed-breakdown, CWT12 coil, VWAP-stretch: these are
the catchers). The typical long mover starts **flat on the day, near its high, RSI ~49** — a continuation / breakout from near HOD —
and no live long setup buys that. Same story as the morning's laggard hypothesis from another angle: our long book is a dip-buying
book; the up-moves that happen are mostly strength continuing.

## Suggested next (for Scout / Builder, not done)
A near-HOD long continuation rule (e.g. 10:00-11:30, name within 0.25 ATR of HOD, above VWAP, fromOpen >= 0, RSI 45-65, rvol >= 1.2,
SPY not down), scored vs same-minute random long entries in names with the same fromOpen bucket (excess t), up/down/quiet split.
Family check first: the backlog likely holds ORB / new-HOD long attempts (GEN NewHOD, orb20_a) — sum their N.
