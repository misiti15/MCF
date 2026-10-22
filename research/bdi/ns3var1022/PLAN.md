# ns3var1022 - PLAN (written 2026-10-22 07:55 ET, before anything was scored)

*Educational only - not financial advice. Research only: no config, setup or exit change (market hours); any
proposal goes to the owner. Backtests on the open two-year lab frames (2024-10, 2025-03..2026-10-07). The locked block
2024-11-01..2025-02-28 is never read (history2y/lib refuses it; every loader asserts it). No holdout is scored.*

Owner 2026-10-22: "Demote NS3-FD as recommended ... Can we thoroughly test this setup and variants for any variant or
possible edit that might make it better for more market weather patterns?"

## Parent and reference rows
- **P0 = NS3-failed-vwap-reclaim-short-FD as run**: mask `vwap>0 & prev vwap<=0 & sma50_dist>0 & fromOpen<-2`, bar close
  09:50-15:00, adv20 >= 95M, short, t1s1 (R = 0.25 x daily ATR, flat by 15:55), refire chain cooldown 1
  (`mcf.strategies.setups.refire_select`), at most 3 open lots per symbol, lots exit on the 5-minute path.
  Must reproduce regime1022 / gates1021: 16,955 trades, -0.0147R.
- **P1 = the windowed parent NS3-failed-vwap-reclaim-short** (09:50-11:30, no refire), reference row (not counted).
- Costs always in: production cost (1c + 1 bps per side, exit side free on a target limit, +2c on stop fills),
  time-of-day entry multiplier, x3 on the extended tier (|gap| >= 20% or price < $5).
- TRAIN = sessions to 2025-12-31; VALID = 2026-01-01..2026-10-07.
- Regime labels: regime1022 `scripts/regime.py` (SPY session, hindsight): Bull o2c >= +0.5%, Bear <= -0.5%, Choppy
  |o2c| < 0.5% with range >= 20-day median, Quiet otherwise. Used to describe and judge, never as an entry input.
- Prior-day inputs use the REAL prior session (gates1021 lookahead correction).

## Exit simulator
One 5-minute-path simulator for every exit (entry at the signal bar close; stop-first when stop and target fall in
the same bar; timed exit at the last bar <= 15:55). Parity test before any variant is scored: t1s1 / t05s1 / t1s05 from
the simulator must equal the frames' lab outcome (production-cost R) on every parent signal.

## Part 1 - diagnosis of P0 (descriptive, not counted as configurations)
Splits of P0 trades (train / valid / 2 years; n, avg R, total R, day-clustered t): regime; time of day (6 buckets);
gap; relative strength vs SPY at entry (fromOpen - SPY fromOpen); 20-day return; 60-day beta to SPY; daily ATR%;
distance above VWAP at entry; bars below VWAP before the reclaim; volume ratio of the reclaim bar; entry #k of the day
per symbol (1, 2, 3+); day of week; SPY and QQQ above / below their own VWAP at entry; breadth falling / rising at
entry; peer median fromOpen (top-5 correlated names, train correlations). Where the losses sit on Bull and Choppy days
(same splits restricted to those days). Same-minute random shorts as the baseline for each split.

## Part 2 - pre-declared variant grid (every row counted; one or two knobs each)
Entry filters on top of P0 (filter applied inside the mask, then refire chain, then lot cap):
- A1 relative strength vs SPY (fromOpen - spy_fo) <= -3 / -4 / -5 (3)
- A2 at least N consecutive bars below VWAP before the reclaim, N = 3 / 6 / 12 (3)
- A3 reclaim size (vwapDistPct at entry) <= 0.10 / <= 0.25 / >= 0.25 (3)
- A4 volume ratio of the reclaim bar <= 1.0 / >= 1.5 (2)
- A5 lowest vwapDistPct of the 6 bars before the reclaim <= -1.0 / >= -0.5 (2)
- A6 daily ATR% <= 3 / <= 5 / >= 3 (3)
- A7 peer median fromOpen < 0 / < -1 (needs live code) (2)
- A8 SPY below its VWAP / QQQ below its VWAP / SPY above its VWAP / SPY fromOpen > 0 (4)
- A9 breadth falling (2-bar change < 0) / breadth <= 0.5 (2)
- A10 20-day return <= +10% / < 0 (2)
- A11 60-day beta <= 1.0 / skip beta >= 1.5 (2)
- A12 gap > -2% (not gapped down) / gap < 0 (2)
- A13 fromOpen threshold < -1.5 / < -3 / < -4 (3)
- A14 sma50 condition removed (1)
Exits on all P0 signals:
- B1 target 0.5R (t05s1) (1); B2 stop 0.5R (t1s05) (1)
- B3 time stop 30 / 60 / 120 minutes (3)
- B4 trailing 1R stop, no target (1); target 1R + 0.5R trail once +0.5R (1)
- B5 scale-out half at +0.35R, rest t1s1 (1); half at +0.5R, rest 1R target with stop to entry (1)
- B6 breakeven stop after +0.5R, target 1R (1)
- B7 stop 1.25x / 1.5x wider at the same $ risk, same price target (2); same, target scaled with the stop (2)
- B8 flat by 14:00 / 15:00 (2)
Re-fire rules:
- C1 first signal per symbol-day only (1); C2 cooldown 3 / 6 bars (2); C3 max lots per symbol 1 / 2 (2)
Window cuts:
- D1 no entries before 10:00; D2 none after 14:00; D3 10:00-14:00; D4 09:50-11:30 with refire; D5 11:30-15:00 only (5)
Inverse (long) ideas:
- E1 long at the NS3 signal bar (mirror, t1s1) (1)
- E2 long when the reclaim holds: price stays above VWAP for the next 2 bars, entry at the 2nd bar's close, t1s1 (1)
- E3 E2 only while SPY is above its VWAP (1); E4 E2 with target 0.5R (t05s1) (1)
Pairs (selected on TRAIN only, judged on VALID):
- F: the 3 best single entry/re-fire/window rows by TRAIN "vs random thinning" (> 0 required) x the 2 best exit rows by
  TRAIN avg R (6), plus the 3 pairs among those 3 entry rows (3). (9)

Count: A 34 + B 16 + C 5 + D 5 + E 4 + F 9 = **73 configurations**. Study bar max(1.5, sqrt(2 ln 73)) = 2.93.
NS3 lineage: swarm1017 rework-ns 165,764 + regime1022 gate lineage 1,254 (gates1021 718 + bdi1021 196 + regime1022 340)
+ 73 = 167,091 -> lineage bar sqrt(2 ln N) = 4.90. Anything added later is counted and reported as added.

## Part 3 - how each row is judged (pre-declared)
Reported per row, train and valid: n, kept %, avg R, total R, day-clustered t, avg R per regime (Bull / Bear / Choppy /
Quiet, 2 years and per period), worst day, mean of the worst 5% of days, largest single-day share of total R, excess vs
same-minute random entries (same side, same exit rule, a random adv >= 95M symbol at the same bar; plus the exact
all-symbol mean for lab geometries), "vs random thinning" (total R - P0 total x kept share), and the day-clustered t
of the per-day difference vs P0.

**"Better in more weather" (an edit of NS3-FD)** needs all of:
W1 avg R above P0 in train and in valid; W2 beats random thinning in train and valid; W3 over 2 years the Bull+Choppy
loss shrinks by >= 25% while the Bear-day total R keeps >= 75% of P0's; W4 keeps >= 50% of P0's trades;
W5 day-clustered t of the per-day difference vs P0 >= the lineage bar 4.90 (the study bar 2.93 is reported too).

**Merit as a setup of its own (owner's rule):** Testing bar = avg R > 0 in train and valid, beats same-minute random
in both, day-clustered t (2 years) >= 4.90 (lineage) - or the owner's near-miss rule: avg R > 0 after costs in BOTH train
and valid, beats random in both, >= 30 train / >= 20 valid trades, no single day > 25% of total R. A near-miss must
also not be a pure Bear-day bet: reported by regime. A variant meeting either gets a lab module in `modules/`
(module-vs-scan parity checked) and a DECISION in research/owner_inbox/2026-10-22.md; otherwise one FYI line.
Near-misses / rework ideas go to `backlog_proposals.jsonl` (not appended to research/backlog.jsonl).

Optional if time allows: replay a proposed module through the live code (`python -m mcf.replay run --alone`) on recent
sessions. The live 5-bar gate (research/replay/VALIDATION.md) is not modelled; the lab view evaluates every bar.
