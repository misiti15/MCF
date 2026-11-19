# SIDEHUNT — candidate SIDE inputs for in-play names at 09:50 (Scout, 2026-11-18 ~19:20 ET; Lead lead-20261118-1900-2). Plan only, 0 configs
Educational only — not financial advice. Context: A1 shows ~4.5 non-ETF missed moves/day still hold >= 1 ATR after 09:50 (ceiling,
selection-inflated: arcsine baseline 85%). Size is predictable (in-play, time of day); SIDE is the gap. Searched first: MCF
research/backlog.jsonl, research/bdi/ (incl. orderflow, reddit, precursors), guild research/.

## Ranked: untried or not yet tested after the 09:50 anchor
| rank | side input | status | prior | data | why this rank |
|---|---|---|---|---|---|
| 1 | **Relative strength vs SPY at 09:50** (strong -> long, weak -> short; the long MIRROR of the live RW 'relative weakness' shorts) | QUEUED by the owner, not run: t4-rel-strength (PARK1 11-15, re-test anchored after 09:50). Old result: all 30 negative in TRAIN; the 10:30-11:30 window +0.187R (t 1.82) in VALID vs a +0.048 baseline | moderate: the RW shorts are the guild's best live family; the long mirror is the open half | lab frames / m30 + SPY; cheap | the only candidate with any out-of-sample signal, and it is already in the owner's queue (route it, don't duplicate) |
| 2 | **Signed volume share 09:30-09:50** (up- vs down-volume; = `buyPressure`, 19-bar signed share) | USED live as 'flow-sell' in RW shorts and in GEN rules; never tested as a full-denominator side classifier, and its LONG side (heavy buying into in-play names) is untried | weak-moderate: works as a short filter inside RW; no evidence for longs | lab frames (column exists); cheap | builds on a live-proven feature; tests whether flow gives side beyond RW's own filters |
| 3 | **Position vs VWAP and the 09:30-09:50 range** (extended above -> short / below -> long, or the trend version) | Trend version failed (mh-1029 in-play continuation, 8 configs; mh-1109 compass side); reversal version mh-1105 failed on only 9 days. precursors.py one-day lifts for side labels: fo_atr 3.4x, dist_hod 3.0x, vwap_atr 2.9x (hindsight, single days) | weak: both directions have failed in pieces | precursors rows / lab frames; cheap | the feature exists; only a clean full-denominator side test is missing |
| 4 | **Quote imbalance (bid vs ask size) at 09:50** | The 1-second order-flow family is CLOSED (of-flow-1s: queue imbalance, OFI, CVD; 320 configs, lineage 676; gross +0.03..0.65 bps vs 3.5-4.7 bps spread). Never tested as a side for a 60-90 min move | weak: top-of-book size is fleeting at that horizon | Alpaca historical quotes (heavy fetch) or Live-recorded decision quotes since 11-18 (ledger 2026-11-17-record-live-quotes; forward only) | the horizon is new, but the evidence at short horizons is firmly negative |
| 5 | **Short borrow (easy-to-borrow / hard-to-borrow)** | Untried as a side. Borrow skips are virtual-only in Live (REPS1) | weak intraday (the short-interest literature is monthly) | no history (universe.csv is a 10-05 snapshot); needs a daily snapshot going forward | no data for a backtest; forward-only |

## CLOSED side inputs (do not re-propose)
Options flow (OPTFLOW); news direction (NEWSDIR, NEWSMID); premarket direction (D2); new highs (NH1); the 09:50 open drive (OD0950);
opening-range breakouts (t1-orb-exits, 489 configs); gap fade / continuation (many); peer leader / laggard (family 92); in-play +
Market Compass side (mh-1109); market-state direction (2,605 configs); 1-second order flow (of-flow-1s, 320); tick-rule delta
(bdi-vid-sweep-delta); VWAP fades / envelopes (bdi-vid-envelopes and the related lines); yesterday's late flow (Lead 11-18, 'none yet').

## What any pick must show (Skeptic's standard)
Full in-play denominator at 09:50 (precursors.py rows), side precision vs 50% and vs the competitor 'today's 09:30-09:50 side',
gross and ex-market, day-clustered, MDE printed, family N counted (MH/laggard lineage >= 104, BAR90 >= 2.74 for any rule).
Recommendation: #1 belongs to the owner's PK1 queue (ask the main session to run it under the 09:50 anchor). The guild's own pick is #2.
