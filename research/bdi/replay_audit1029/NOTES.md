Educational only — not financial advice.

# REPS replay audit 2026-10-29 (research rule 21): replay vs live, all 5 intraday accounts

**Verdict: FAIL.** The replay is not cleared as a filter. Per rule 21, **no replay result may be used yet, not even as a filter**, so
the dormant / low setup filter step was **not run**. Nothing was committed, and no config, setup, ledger or backlog file was changed.

Bar (rule 21): trade match ≥ 95% (same setup + symbol + entry/decision minute), avg R after costs within ±0.03 of live per account and
overall, and never optimistic (replay better than live by more than 0.03R fails).

## Headline (post-fix window 10-27..10-29 = the judging window; 3 sessions per account, 2,749 live trades)

| account | sessions | live trades | (in lab universe) | replay trades | matched (exact min) | **match %** | match % in lab universe | replay-only extras | live avg R (costs) | replay avg R (costs) | **gap** | result |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Primary | 3 | 88 | 85 | 83 | 72 | **81.8%** | 84.7% | 11 | −0.064 | −0.171 | **−0.107** | fail (match, gap) |
| Testing 1 | 3 | 525 | 464 | 484 | 416 | **79.2%** | 89.7% | 68 | −0.250 | −0.237 | +0.013 | fail (match) |
| Testing 2 | 3 | 657 | 603 | 621 | 542 | **82.5%** | 89.9% | 79 | −0.172 | −0.140 | **+0.032** | fail (match, optimistic) |
| Graveyard | 3 | 1,091 | 1,004 | 1,129 | 817 | **74.9%** | 81.4% | 312 | −0.188 | −0.136 | **+0.052** | fail (match, optimistic) |
| Gen | 3 | 388 | 310 | 292 | 239 | **61.6%** | 77.1% | 53 | −0.404 | −0.440 | **−0.036** | fail (match, gap) |
| **Overall** | 15 | **2,749** | 2,466 | 2,609 | 2,086 | **75.9%** | 84.6% | 523 | −0.223 | −0.191 | **+0.032** | **fail (match, optimistic)** |

±1-minute matching changes nothing (75.9%). Trade match is computed as matched trades / all live trades. Replay-only extras are listed
separately and are not in the denominator. Sample: 3 sessions, so the per-account R gaps are noisy (Primary has only 88 trades). The
match shortfall is structural, though, and does not depend on sample size (see causes).

### Pre-fix window 10-07..10-26 (live had the `len(bars) % 5` gate bug; reported, not judged)

| account | sessions | live trades | replay trades | match % | (in lab universe) | replay-only extras | of which "no live signal" (bug era) | live avg R | replay avg R | gap |
|---|---|---|---|---|---|---|---|---|---|---|
| Primary | 14 (10-07..) | 602 | 775 | 77.9% | 85.1% | 306 | 251 | −0.111 | −0.120 | −0.009 |
| Testing 1 | 12 (10-09..) | 2,797 | 3,204 | 75.8% | 80.1% | 1,085 | 797 | −0.167 | −0.133 | +0.034 |
| Testing 2 | 11 (10-12..) | 3,245 | 5,782 | 78.2% | 81.2% | 3,244 | 2,834 | −0.210 | −0.153 | +0.057 |
| Graveyard | 4 (10-21..) | 1,095 | 1,261 | 63.7% | 66.7% | 564 | 432 | −0.201 | −0.215 | −0.014 |
| Gen | 6 (10-19..) | 104 | 253 | 50.0% | 62.7% | 201 | 196 | −0.034 | −0.164 | −0.130 |
| Overall | 47 | 7,843 | 11,275 | 74.9% | 78.9% | 5,400 | 4,510 | −0.184 | −0.152 | +0.032 |

Not replayable at all: Primary 10-06 (no frozen `setups/2026-10-06.json` on `mcf-data`). The other accounts' journals start on the day
of their first frozen snapshot. All 17 sessions overall: 10,592 live vs 13,884 replay trades, match 75.2%, gap +0.035 (optimistic).
The replay runs today's code, which includes the GX1 fix. So before 10-27 it takes the ~44% of signals that live skipped
(research/ops/coverage1029.md), and those show up as "no live signal" extras. That is a live bug, not a replay error. It still means
the pre-fix window cannot be used for the R comparison: the replay trades a different set.

## Where the misses come from (post-fix, live trades with no replay match; 663 of 2,749)

| cause | Primary | T1 | T2 | Graveyard | Gen | total | does the replay model it? |
|---|---|---|---|---|---|---|---|
| symbol not in the replay universe (lab 1,226 names; live trades ~4,600) | 3 | 61 | 54 | 87 | 78 | **283** | **No.** The store has only lab-universe bars and priors |
| replay's spread draw skipped it, live's real quote did not | 12 | 43 | 53 | 88 | 32 | **228** | Statistically only: the spread is a deterministic draw from the live journaled spreads (no recorded quotes exist; the poll log has no quotes) |
| −2R / daily-loss latch fired at a different time (path dependent) | 0 | 0 | 0 | 58 | 0 | 58 | Yes (runner code), but it diverges once the earlier trades differ |
| lot cap / caps hit differently | 0 | 0 | 0 | 35 | 0 | 35 | Yes (code), path dependent |
| no replay signal at the decision minute (bar data differs: late / revised bars, breadth contexts over the lab universe) | 1 | 0 | 4 | 0 | 30 | 35 | No (no fetch latency or bar revisions; Gen contexts) |
| other (opposite side held, twin, another minute) | 0 | 5 | 4 | 6 | 9 | 24 | Yes (code) |

**Spread is the binding cause on the shared universe.** If the replay's spread decisions had agreed with live (a diagnostic ceiling,
not an audit number), post-fix in-universe match would be 98.8 / 98.9 / 98.7% (Primary / T1 / T2), but still 90.1% Graveyard and
87.4% Gen. Over all live trades it would be 95.5 / 87.4 / 90.6 / 83.0 / 69.8%. Even then, only Primary would clear 95%.

The replay-only extras post-fix (523) mirror this. 206 are live spread skips that the replay took, 121 live −2R latch skips
(Graveyard 118), 50 caps, 101 "no live signal" (data at the minute), 20 live broker rejects / unfilled, 25 other.

**Fills are not the problem.** On the 2,086 matched trades the R difference is −0.005 to +0.023 per account (Primary +0.001,
T1 −0.005, T2 +0.008, Graveyard +0.023, Gen −0.029), and the exit reason agrees on 96–99.6%. The avg-R gaps come from **which** trades
each side takes, not from how they fill. The spread skips are not random with respect to outcome: wide-spread names are the volatile
ones. The universe gap also leaves out ~10% of live trades on non-lab (thinner) names.

## Live-only skips and whether the replay models them

| live skip | modelled? | notes |
|---|---|---|
| spread (bps cap, % of stop) | partly | synthetic quote = last close ± a spread drawn from the live journaled spreads (my private `spreads.json`, built with `store.build_spreads`; the shared `data/replay` had none, so the default would have been a flat 2 bps that almost never skips). Counts agree in aggregate (post-fix live 985 vs replay 910 spread skips), but per signal they are close to independent draws |
| quote cross-check (dev / age / bar age) | in code, rarely fires | the synthetic quote sits on the last close and is 1 s old, so the dev and age checks almost never trip (live: 2 post-fix) |
| borrow / ETB | partly | I passed each session's own `universe.csv` flags (the harness default is `data/universe.csv` of 10-05). Live also checks the broker's asset flags intraday, so it skips far more: post-fix T1 563 live vs 118 replay, T2 202 vs 50, Graveyard 201 vs 88 |
| twin | yes | same code; counts agree (post-fix 94 live vs 102 replay) |
| −2R per-setup latch (Primary from 10-29; Graveyard own) | yes | same code and config-at-open; the trigger time diverges with the trade path (Graveyard) |
| halted / broker rejects (Alpaca `base_price` etc.) / unfilled | no | simulated broker never rejects; "halted" in the replay comes from bar gaps, not from the real tape |
| fetch latency, late or revised bars, poll gaps | no | the replay polls with zero latency on final SIP bars |

## What would be needed to pass (not done here; each is a harness change outside this folder)

1. **Universe:** fetch 1-minute bars plus 50 days of daily and 24 days of 5-minute history for the full live universe (~4,600 names),
   not only the 1,226 lab names. That recovers about 10% of live trades (283 of 2,749 post-fix).
2. **Quotes:** record the NBBO the runner sees at each signal (extend `live.log_poll_inputs` to quotes for signalled symbols), or
   fetch historical quotes at the decision second. Without real quotes, per-trade spread decisions cannot match, and the
   ceiling stays at ~84–91% on T1, T2 and Graveyard.
3. **Borrow:** log the intraday ETB answer per signal and replay from it.
4. Re-run this audit on ≥ 10 post-fix sessions. Three sessions are too few to judge the ±0.03R band. The match shortfall alone already
   fails the audit.

## Method

- `prep.py`: private replay store in the scratchpad (`MCF_REPLAY_STORE`). The shared `data/replay` is symlinked and never written.
  Read-only Alpaca market-data fetch of 10-27/28/29 1-minute SIP bars (lab universe, 1,222 symbols) and daily bars to 10-29.
  Live-prep priors (`build_priors`) for those days.
- `run.py`: every (account, session) through `mcf.replay.harness.run_session`, which is the real `PaperRunner`. Inputs: frozen
  `setups/<d>.json` from the account's data branch (`--as-live`), account limits and costs from the config committed before that
  session's 09:30, universe = lab ∩ that day's live `universe.csv` minus the earnings blackout of record, Alpaca-paper fills
  (half-spread market/stop, touch limits), and per-session ETB flags. 62 account-sessions, 0 errors, 0 missing modules. Speed per
  session on a loaded 4-core box: Primary 110–140 s, T1/T2/Graveyard 220–320 s, Gen 525–560 s.
- `compare.py`: matches live trades (journal `run_id=1`) to replay trades on (session, setup, symbol, decision minute). The decision
  minute is the entry signal's `info.bar_time`, else the client order id. Matching is greedy one-to-one, exact minute (±1 also
  reported). Avg R uses the journal `r_multiple` (paper fills) minus the production cost layer (config `costs`: 1 bp + $0.01/share per
  side, +$0.02/share on stop exits, no exit cost on target fills), applied identically to live and replay. Raw paper R in
  `results.json` (`live_avg_r` / `replay_avg_r`) gives the same signs of gap. Output: `results.json`, `compare_out.txt`.
- Configurations tried: 1 replay configuration (as live, paper fills). An earlier launch without `spreads.json` and ETB flags was
  killed before any session finished and is not reported.
- Reproduce: `MCF_REPLAY_STORE=<dir> python research/bdi/replay_audit1029/prep.py 2026-10-27 2026-10-29`, then
  `run.py 2026-10-07..2026-10-29 --jobs 4`, then `compare.py`.

## Filter step (dormant / low Testing 1/2 + Gen setups)

**Not run.** The audit failed, and rule 21 says no replay result is used until it passes. Valuing the tiers.csv setups
(research/bdi/p2_1029/tiers.csv) through this replay would break that rule.
