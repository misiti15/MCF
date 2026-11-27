Educational only — not financial advice.

# OPENDRIVE_1127 pre-registration (written 2026-11-27 evening, before any feature, trade or score below was built)

**Question (BDI 11-27: 48 of 50 big movers were decidable 09:35-09:45, before the 09:50 entry floor).** Do opening-drive
entries at 09:35 / 09:40 / 09:45 on names flagged by a K6-style mover ranker (computed only from bars closed before the
decision time) capture more of the day's big movers and make more R after realistic early-session costs than the same
rules at 09:50? Research only: no config, setup, exit, assignments, decisions or ledger change.

## Data, splits
1-min RTH bars data/cache_hist/1Min (FIT/CHECK) and data/cache_fresh/1Min (EARLY/T2). No premarket bars: gap = 09:30
open vs prior RTH close. Locked block 2024-11-01..2025-02-28 never read (pyarrow filter + asserts in build.py and score.py).
FIT 2024-10 + 2025-03..2025-09 · CHECK 2025-10-01..2026-11-04 · T2 2023-01-03..2024-09-13 · EARLY 2022-10..2022-12
(cache_fresh starts 2022-10-03; after the 20-session warm-up only ~Nov-Dec 2022 remains; descriptive only).
Eligible symbol-day at decision time T: P_T (close of the last bar before T) >= $5, adv20 >= $20M, ATR14 known, >= 75%
of the bars 09:30..T-1 present, opening bar present, prior close known, same-window 20-day median volume > 0, SPY present,
last bar of the day present. Shorts need easy_to_borrow (data/universe.csv snapshot, not point-in-time; disclosed).

## Ranker at T (no new fitting on any target)
K6 inputs recomputed on the 09:30..T-1 window: gap = |gap|/atr% · rvol_T = volume(09:30..T-1) / 20-day median of the same
window · rng_T = window range / ATR · mv_T = |P_T − open| / ATR · idio_T = |r_T − SPY r_T| / atr% · pdr · log adv20 · atr%.
Transform log1p (dv as is), standardise with the FIT mean/sd of the same T, score with the **frozen MOVEHUNT_1127 K6
coefficients** (results.json logit_coef). List = top 20 eligible names per day at T.

## Direction rules (mechanism-based; applied to the top-20 list at T)
- **R1 DRIVE (opening-range drive with volume):** D = sign(P_T − open); P_T within the top 20% of the 09:30..T-1 range
  (long) / bottom 20% (short) and rvol_T >= 2.0. Mechanism: price held at the edge of the opening range on heavy volume
  = an unabsorbed order imbalance that keeps pushing.
- **R2 GAP-GO:** |gap| >= 0.5 × atr%, P_T still beyond the open in the gap direction (gap extending, not filling);
  trade the gap direction. Mechanism: news/earnings repricing that buyers/sellers keep extending.
- **R3 GAP-FILL:** |gap| >= 0.5 × atr%, P_T back through the open against the gap but the gap not yet fully filled;
  trade toward the prior close. Mechanism: overnight over-reaction that fails to extend reverts toward the prior close.
Entry at the open of the bar at T (09:35 / 09:40 / 09:45 / 09:50). Stop: the opposite extreme of the 09:30..T-1 range
∓ $0.01, widened so that risk >= 0.15 × ATR (a 5-minute range alone is often too tight to survive spread noise).
Stop checked on 1-min high/low from the entry bar (stop-first; a bar opening through the stop fills at its open).
Time exit at the 15:55 bar close (last bar on half days). One trade per name per rule per day.

## Configurations: 24 = 3 rules × 4 times (09:35, 09:40, 09:45, 09:50) × long/short
The 09:50 cells are the comparator (same rules at the current floor) and count in the 24.
Cumulative N before this wave ≈ 9,300 → ≈ 9,324.

## Costs (always in)
- **LIVE-L (main):** research/primshorts_1126 cells_live.json predict_R (price bucket × exit kind), **plus an early-entry
  surcharge** for T < 09:50. No live trade has ever entered before 09:49 (all 10 journals), so early slippage cannot be
  measured directly. Surcharge (bps of price on the entry side) = E × (m_T − 1), where E = the live mean signed entry
  slip at 09:50-09:59 (+1 bp fees) measured from the journals (slip_tod.py) and m_T = the larger of (a) the measured
  median 1-minute bar range (h−l)/c at the entry minute over the same at 09:50 (cache bars; a conservative spread proxy
  because it includes volatility) and (b) the gates.tod_cost_mult ratio vs 09:50 (09:35: 3.8/1.4, 09:40/09:45: 2.1/1.4).
  A **harsh** variant doubles the surcharge (reported).
- **LR8 (alongside):** bench10 add_r formula with gates.tod_cost_mult at the entry minute (3× tier for price < $5 or
  |gap| >= 20%, 2c extra on stop fills, 1.2 bp borrow on shorts).

## Metrics and pass bars (per config; T < 09:50 configs judged; 09:50 reported as comparator)
1. avg R/trade > 0 after costs (LIVE-L incl. surcharge, and LR8) on CHECK and on T2.
2. Day-clustered t (LIVE-L) >= **3.1 on CHECK** (Bonferroni for 24 configs, two-sided 5%) and >= 2.0 on T2.
3. One-big-day: avg R without the best day > 0 and best-day share < 50% on CHECK and T2.
4. Control: beats a size-matched random draw of eligible non-list names where the same rule fires at the same T
   (paired day diff > 0 on CHECK and T2, paired t >= 2.0 on CHECK).
5. Stress: entry +1 minute (open of the next bar, same stop) and +2 bp per side: avg > 0 on CHECK and T2.
Early-window verdict (the key question): an early config is "worth its extra cost" only if it passes 1-5 AND its avg
R/session beats its 09:50 sibling on CHECK and T2 (paired day diff > 0, CHECK paired t >= 2.0).
Capture: the day's big movers = top 2% of eligible names by |close − open| / ATR (also reported: top 2% by the move
still left from 09:35, |close − P_0935| / ATR). Capture@T = share of movers that are on the T list AND traded by any rule
in the mover's direction; R on those captured trades and on the wrong-way trades reported. Long and short separately.
Also reported: family split (gap >= / < 1 ATR, price buckets), FIT, EARLY.
Verdict: PASS if >= 1 early config clears 1-5 and the early-window test; LEAD if one clears 1-3 on CHECK and T2 but not
4-5/the sibling test, or the ranker capture rises materially earlier with R close to break-even; FAIL otherwise.
