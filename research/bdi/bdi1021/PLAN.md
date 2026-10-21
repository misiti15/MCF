# bdi1021 - PLAN (written 2026-10-21 ~17:30 ET, BEFORE any configuration below was scored)

*Educational only - not financial advice. History backtests only (not paper, not live).*

## Why this test
- Owner chart reads (research/bdi/OWNER_CHART_READS.md): 10-15 week and 10-20 "S&P dips around 09:45-09:55, then a
  great buy". Today (10-21) did it a third time: SPY low -0.36% at 10:12, then +0.42% at 14:16; large caps rallied
  11:00-13:30 while the short books were open (nightly1021).
- longs1020 already tested the LONG side of this (index dip-bounce and dip-timed stock longs: 0 of 200 pass). The
  untested side is the SHORT book: today the opposite side of the shorts would have won (+94R at 1R/1R, per_trade_1021
  hindsight), but SPY's from-open at entry did NOT pick those trades out (shorts entered with SPY >= +0.25% did better,
  not worse). So the from-open gates of gates1021 (U1-U7) are the wrong shape for this day type.
- New state, known at the decision-bar close: "the index's low is in": SPY has printed its session low, bounced
  off it, and is back above its session VWAP. Hypothesis: short entries in that state do worse than the rest (and,
  mirrored, long entries after "the high is in" do worse).

## Data, split, costs (fixed; same as gates1021)
- The 49 covered live setups and their live-shaped signal tables from gates1021 (research/bdi/gates1021/setups_scored.csv;
  scratch `g1021/sig`, production R after costs, refire chains as live, R = 0.25 x daily ATR, 5-min exit path).
  Nothing is re-generated.
- SPY 1-minute SIP bars from data/cache_hist/1Min/SPY.parquet, read with pyarrow row filters that drop the locked
  block 2024-11-01..2025-02-28 at read time (as longs1020); every table asserts no locked date. MCF_HIST_ALLOW_LOCKED
  is never set. No holdout is scored.
- TRAIN = sessions <= 2025-12-31; VALID = 2026-01-01 onward (frames end 2026-10-07).
- State at a decision bar with close time `tod`: computed from SPY 1-minute bars that START before `tod` (i.e. closed
  by `tod`), from 09:30. low_so_far / time of that low, high_so_far / its time, session VWAP ((H+L+C)/3 x volume),
  last close.

## Configurations (fixed list; a gate BLOCKS entry in its state) - 4 per setup, hypothesised direction only
Short setups (36):
- S1 low by 10:30, SPY >= +0.30% above the session low, and above session VWAP
- S2 low by 10:30, SPY >= +0.50% above the low, and above VWAP
- S3 low any time so far, >= +0.30% above it, above VWAP
- S4 low any time so far, >= +0.50% above it, above VWAP
Long setups (13): the mirrors (high so far, SPY >= x% below it, below VWAP; "by 10:30" for L1/L2).
Count: 4 x 49 = **196 configurations**. Study bar max(1.5, sqrt(2 ln 196)) = 3.25. Direction-gate lineage
(gates1021 718 + 196 = 914): bar sqrt(2 ln 914) = **3.69**.

## Scoring (the gates1021 `evaluate` function, unchanged)
Per setup x gate, train / valid / all: blocked share, parent and gated avg R, delta per parent trade (day-clustered
t), same-minute random-control delta (how much is plain market beta), up / flat / down regime deltas, choppy-day delta.

## Verdict (pre-declared)
- **Stable split**: blocked >= 3% of trades in each split, delta > 0 in both, train delta t >= 2.0, valid >= 1.0.
- **Finalist**: stable split AND blocked <= 33% in each split AND all-data delta t >= 3.69 (lineage bar) AND delta
  minus the random-control delta > 0 in both splits (not only market beta) AND delta >= 0 in up and in down regimes.
- A finalist that leaves its setup negative after costs is reported as "improves a losing setup", never proposed for
  routing. No routing tonight in any case (owner decides G1 / N5 / N6 first); at most a backlog line.
- Every one of the 196 rows is written to results.csv, failures included.

## Descriptive (not configurations)
- Today 10-21 (paper/live, 1 session): each real short/long entry in the 5 accounts, with the S1-S4 / L1-L4 state at
  the entry minute (SPY 1-min SIP), and the live R in vs out of the state.
