# BDI 2026-10-26: every trade of the 5 accounts, and both sides of the coil burst on two years of history

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7) from one shortened session (no
trades before ~10:39 ET, Gen from 12:02 ET: the missed schedule, not a setup property): a diagnosis, not evidence.
History numbers are **backtests** on the open two-year history (train ≤ 2025-12-31, valid 2026-01-01..10-07) with
production + time-of-day costs in. The locked block (2024-11-01..2025-02-28) was never read and no holdout was scored.
No config, setup, exit or assignment was changed, and no DECISION was added tonight.*

Already done today and **cited, not redone**: `nightly1026/` (P/L, poll coverage, autopsy, give-back, coil burst
history, LatAm basket, ST-P replay, DECISION D3) and `cf1026/`. Configurations today: bdi1026 **20** (12 burst-skip +
8 burst-fade), 0 pass.

## Failures first
1. **The nightly's coil burst-skip fails on history: 0 of 12** (`PLAN.md` written before scoring, `scan_coil.py`,
   `eval_burst.py`, `eval_out.txt`, `results.csv`). Coil Under the High (4 bars) (CWT12-coil-k4-long) and (6 bars)
   (CWT12-coil-k6-long), live geometry, 09:50-11:30, first signal per symbol-day:
   - Parent on two years: k4 n 44,505, −0.057 / −0.065R (train / valid); k6 n 16,735, −0.074 / −0.066R.
   - **Bursts are barely worse than single entries on two years.** k4 avg R by same-bar count (train / valid):
     1: −0.011 / −0.057 · 2-4: −0.062 / −0.056 · 5-9: −0.044 / −0.066 · 10-14: −0.064 / −0.065 · 15+: −0.068 / −0.067.
     The live −0.54R on 3 burst days (55 trades) is a sample effect.
   - Skipping bursts leaves a losing book in all 12 rows: k4 skip ≥ 10 keeps 42%, −0.048 / −0.063R; k4 cap 3 per bar
     keeps 35%, −0.054 / −0.061R; k6 skip ≥ 5 keeps 38%, −0.064 / −0.052R. Down sessions −0.15..−0.23R in every row.
     7 rows raise the kept avg R by only +0.001..+0.010R (weak near-misses, no routing).
   - **The "index at its high" variant is backwards:** coil-k4 entries with QQQ within 0.1 pt of its running high
     (and ≥ +0.5%) are the *better* ones (−0.033 / −0.043R vs −0.063 / −0.072R). Skipping them lowers the book.
   - Backlog `nightly-1026-coil-breadth-burst-skip` → **failed**. It supports D3 (both coil versions to the Graveyard).
2. **New idea, Coil Burst Fade (short), fails: 0 of 8** (`PLAN.md` addendum declared before the run, `scan_fade.py`,
   `eval_fade.py`, `eval_fade_out.txt`, `results_fade.csv`). Live 10-26 the opposite side of coil-k4 was +32.4R
   (52 trades). On two years, shorting the same signal (coil-k4 kernel, side flipped, no scale-out):
   - t1s1 all signals −0.070 / −0.036R (n 44,505, day-clustered t −2.74); bursts ≥ 15 −0.045 / −0.050R (n 15,225).
     t05s1 −0.070..−0.072 / −0.047..−0.050R. Above the same-minute random short by only +0.01..+0.02R.
   - Pure direction bet: up sessions −0.18..−0.26R, down +0.09..+0.31R — the exact mirror of the long (up +0.05..+0.09,
     down −0.15..−0.23). **Neither side of the coil signal clears costs.** New backlog entry
     `bdi1026-coil-burst-fade-short` (failed, 8 configs). The live opposite-side win was the fade from the 11:02 index high.
3. **Exit / management levers still flip with the day** (all accounts, Δ R vs the simulated bracket, SIP 1-min, costs
   in; `out_1026.txt`; 10-20..10-23 from bdi1023):

   | lever | 10-20..10-23 (4 days) | **10-26** | 5-day |
   |---|---|---|---|
   | breakeven at +0.5R | −20.0 | −2.8 | −22.8 |
   | +0.5R target | −29.6 | −15.0 | −44.6 |
   | +1R target | −24.0 | +11.1 | −12.9 |
   | 0.5R trail after +0.5R | +44.5 | +5.7 | **+50.2** |
   | hold to 15:55 | −147.6 | **+38.2** | −109.4 |
   | stop-and-reverse 1R/1R | −45.3 | −37.2 | −82.5 |
   | one re-entry after a stop | −2.8 | −14.4 | −17.2 |
   | opposite side 1R/1R | −62.1 | +27.8 | −34.3 |

   Trail ahead on 4 of 5 days (+50.2R) but the book-wide trail already failed on history (`t6-exit-overlay`,
   `sw-w4-book-exits`, `exit-cwt-trail-notarget`). Today's hold-to-close win is the 12:00-12:59 ET longs (bracket
   −5.8R → hold +54.8R, n 49) recovering into the close; the Gen lunch longs did the opposite (held, gave back $294).
   Stop-and-reverse is negative again (5-day −82.5R); re-entry after a stop −17.2R.
4. **Opposite side: no rule known at entry.** Longs entered while SPY was not down −0.25% lost (−0.298R live, opposite
   +0.217R, n 248) and shorts entered with SPY up ≥ +0.25% made money (+0.122R live) — today's up-then-fade tape; the
   same flags sorted the other way on 10-22 and 10-23. Nothing to propose.
5. **Owner chart reads:** nothing new (OWNER_CHART_READS.md unchanged).

## What was done
1. **Every trade, 511 of 511 with bars** (`trades_bdi.py`, bdi1023's script unchanged, on `nightly1026/trades.csv` +
   the nightly's SIP 1-min bars for 297 symbols): context at entry, MFE / MAE / time to MFE, the what-ifs above,
   opposite side with hindsight flags, loss type → `per_trade_1026.csv`, `by_setup_1026.csv`, `out_1026.txt`.
   - R after costs, live: Primary −3.4R (22), Testing 1 +9.9R (136), Testing 2 −28.9R (136), Graveyard −18.1R (193),
     Generator −1.5R (24). Total −41.9R (10-23: +2.6R).
   - **Long vs short:** longs −74.0R (248), shorts +32.1R (263) — mirror of 10-23 (longs +22.9R, shorts −20.3R).
   - Best: L3-gap-slope-fromopen-FD (T1) +10.4R, exhaustion_short (T1) +9.6R, L3-gap-slope-rsi5hi-FD (T2) +8.0R.
     Worst: CWT12-coil-k4-long (T2) −29.8R (25 of 52 never worked), RW2-exhaustion-noon-adv150-short-FD (GY) −9.1R,
     CWT14-failbrk-pdl-p05-long (T1) −8.6R.
2. **patterns.csv:** +240 loser rows for 10-26 (3,376 → 3,616; `merge_patterns.py`, idempotent by date). Loss mix vs
   10-12..10-23: **never worked 33.8% (was 23.1%)**, wrong side after a big swing 20.0% (15.9%), late hold 15.8%
   (11.6%), small MFE 15.8% (20.9%), gave back 10.0% (15.8%), stopped then reversed 4.6% (12.7%). Today's losses were
   entries (bursts at the 11:02 high), not exits.
3. **Give-back** (nightly1026, not recomputed): Primary +$61 → −$39 (CWT13-vwapstretch-z05-long's first day);
   T2 −$220 by 11:39 (coil burst); Gen −$294 from 13:58 (lunch longs held to 15:55, trail never armed). The burst
   explanation for T2 does not survive two years (above); Gen's mechanism is `sat1024-late-profit-lock` (failed).
4. **Recurring patterns (≥ 3 of the last 10 sessions):** CWT14 pdl/orl longs never-worked (11 days), RW2-FD small MFE
   (11), heat_fade_short-FD never-worked / gave-back (10-11), L3-fromopen-FD wrong side after a big swing (9) — all
   already in the backlog (top5 tunes, `bdi1015-short-index-up-veto`, `nightly-1019-index-chase-veto`, LL-LATCH). Not
   re-added.
5. **Backlog:** `nightly-1026-coil-breadth-burst-skip` → failed (12 configs); new `bdi1026-coil-burst-fade-short`
   (failed, 8 configs). `research/BACKLOG.md` regenerated.

## vs yesterday (10-23)
10-23: 30 configurations, 0 pass, a book-wide tight-stop near-miss. 10-26: 20 configurations, 0 pass. Learned: the
coil signal has no edge on either side after costs — it is a market-direction bet (long wins up sessions, short wins
down sessions), so neither burst filters nor a fade rescue it; the evidence now points to D3 for both versions.

## Queued
- `nightly-1026-country-gap-basket-cap`: needs a country / region map and CWT09 in the history cache (not started).
- `gb-1019-noise-floor-stop` widen-to-floor at the same $ risk; `bdi1022-short-cluster-profit-lock` (from 10-22/23).
- Add the CWT14 / CWT09 families to the history signal cache (CWT12 now runs via `scan_coil.py`).

Files: `PLAN.md`, `scan_coil.py`, `eval_burst.py`, `eval_out.txt`, `results.csv`, `scan_fade.py`, `eval_fade.py`,
`eval_fade_out.txt`, `results_fade.csv`, `counts.json`, `trades_bdi.py`, `merge_patterns.py`, `per_trade_1026.csv`,
`patterns_1026.csv`, `by_setup_1026.csv`, `out_1026.txt`. Scans write to the scratchpad (not in git).

Educational only — not financial advice.
