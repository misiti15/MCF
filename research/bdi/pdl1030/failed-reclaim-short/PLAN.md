# pdl1030 / failed-reclaim-short: pre-declaration (written before any configuration is scored)

*Educational only — not financial advice.*

Written 2026-10-30 ~05:25 UTC, before the 09:30 ET open and before any outcome of this family is computed. Research only:
nothing in config/, mcf/, ledger or backlog changes, and nothing is committed.

## Idea
The opposite trade to the Failed Prior-Day-Low Break Long. The long buys the reclaim of PDL; about half of those reclaims
fail and the day's low breaks again. This family shorts that failure (the "failed reclaim" / bull trap), using the same
signal pool, so the exposure comes from the same signal count (side flip of the same signal).

## Base and harness
- Signal pool: the unchanged CWT14 `S6.b3_any` p05 entries (PD level, long, p=0.05), adv20 >= 95M, signal 09:50-15:00,
  first signal per symbol-day (53,326 signals, 153.2/session). D1 uses the p10 pool. Read from the pdl1030/structure-exit
  cache (entry bar .. 15:55 5-minute paths + signal-time fields), which reproduces swarm15's parent rows exactly.
- Data: TRAIN = 2024-10, 2025-03..12. VALID = 2026-01..03, 2026-07..09-15. HOLD months (2026-04..06, 2026-09-16..10-07)
  and the locked block (2024-11..2025-02) are never loaded. Context (spy_fo, breadth) from lib.load_context for the same
  months only, rows after 2026-09-15 dropped.
- Costs (same as swarm15 / top5_1028 sim): entry 1c + 1 bp x time-of-day multiplier (3.8 / 2.1 / 1.4 / 1.0), market exits
  1c + 1 bp, +2c on stop exits, target limits free, x3 on the extended tier, flatten at the 15:55 close.
- Short simulator: mirror of the top5_1028 / sim2 long logic (stop checked first on each bar's high, then target on the
  low, then scale-out). Parity: P05/P10 via structure-exit sim2 must match swarm15 (p05 TRAIN -0.0677 / VALID -0.0675,
  p10 TV -0.0880) within 0.005R; my short sim on row A1 must match the pdl1030/tape-flip `Sb` leg (top5_1028 sim,
  side -1) within 0.005R on the same trades, else stop.

## Quantities (all known at the trigger bar's close = short entry time)
- Trigger bar k: the first bar after the signal bar with tod <= 15:00 that meets the trigger condition (known at its close).
  - TP: close < PDL (reclaim failed).
  - TL: close < LOD_sig (a new day low on a closing basis; LOD_sig = day low through the signal bar, <= PDL - 0.05A).
- e = close of bar k (short entry). A = daily ATR (known pre-open). RH = max high from the signal bar through bar k.
- Stops: F25 = e + 0.25A; SR = max(RH + 0.02A, e + 0.10A) (above the reclaim high); F75 = e + 0.75A. R unit = stop - e.
- Default exits (mirror of parent p05): target e - 0.5R, half off at e - 0.25R then stop to e, flatten 15:55.
- Round-trip cost estimate = [(0.01 + e*1e-4) x mult(tod_k) + 0.01 + e*1e-4] x tier / R.
- spy_fo, breadth: context row at (date, tod_k).
- bars_to_fail = k - signal bar (in 5-minute bars).

## Configurations (17, every one counted)
Parity: P05 (parent long p05), P10 (parent long p10).

A. Trigger x stop, default exits:
- A1 TP / F25 (same trade as tape-flip Sb without the tape gate; doubles as the short-sim parity check)
- A2 TL / F25
- A3 TP / SR
- A4 TL / SR
- A5 TL / F75
-> A* = the A row with the best TRAIN avg R.

B. Exits on A* (no scale-out unless stated):
- B1 target 1R
- B2 target 2R
- B3 no target, stop only, flatten 15:55
- B4 no target, stop moves to entry once MFE >= 1R, flatten 15:55
-> E* = best TRAIN avg R among {A*, B1..B4}.

C. Entry gates on E* (all known at the trigger close):
- C1 round-trip cost estimate <= 5% of R
- C2 SPY below its open (spy_fo < 0)
- C3 breadth < 0.5
- C4 C1 + (C2 or C3, whichever has the better TRAIN avg R)
- C5 fast failure: bars_to_fail <= 6 (trigger within 30 min of the signal)
-> BEST = best TRAIN avg R among all A/B/C rows that keep >= 25 trades/session.

D. D1 = BEST applied to the p10 signal pool.

## Bar
N = 121512 + 3 x 17 = 121563 -> t_day >= 0.9 x sqrt(2 ln N) = 4.355 (TRAIN+VALID, day-clustered).
Pass also needs: walk-forward >= 54% of the 17 TRAIN+VALID months positive (>= 10), avg R > 0 on TRAIN and on VALID
separately, beating the best parent p05 on both (TRAIN -0.0677, VALID -0.0675), and exposure >= 76.6 trades/session or
>= 25 trades/session. Reported per row: TRAIN / VALID avg R, t, trades/session, WF%, up/down-session R (SPY day sign),
avg R without the best day and that day's share of total R.
