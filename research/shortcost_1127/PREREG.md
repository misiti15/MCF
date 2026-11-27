Educational only — not financial advice.

# SHORTCOST-1127 pre-registration (written 2026-11-27 ~20:50 UTC, before any R outcome below was scored)

Research only: no config, setup, exit, assignments, decisions.json, ledger or backlog change. No broker / MarcoFlow call
(journals and bars already on disk). Locked block 2024-11-01..2025-02-28 is never read (asserted in every script).

## Question
LIVE-L (primshorts_1126, 32,131 live trades) says LR8 is too harsh on $5-20 names and too lenient overall (most on $100+
names and tight stops). Where are the cost-cheapest trading zones, and does restricting the tradable universe to them
(a cost-zone filter at signal time) raise net R by more than trading less at random?
Hypothesis (optimistic): a short-side cost-zone filter on the pre-trade LIVE-L cost estimate removes trades whose net R is
worse than average (cost is a true per-trade drag; gross R does not compensate), so the filtered book beats both the base
and a size-matched random removal on CHECK and T2, and several live setups improve.

## What was looked at before writing this (no outcomes)
Only the distribution of the pre-trade cost estimate (price and stop width, no exit or R) on live trades and history lots:
LIVE-L has a floor of about 0.07R (intercepts b = 0.00-0.10R), so the example bar "cost < 0.05R" keeps 0.3% of live shorts
and ~0% of history lots: it is infeasible and is NOT a config. Live shorts: c_ex median 0.107, 34% >= 0.12, 62% >= 0.10.

## Pre-trade cost estimate c_ex (fixed now)
c_ex = sum over exit kinds k of w_k x (a_{pb,k} / width_bps + b_{pb,k}), cells = research/primshorts_1126/cells_live.json
(fit on live 10-14..11-25), pb = price bucket of the decision price, width = |price - stop| in bps, fixed kind weights
w = stop 0.357 / market 0.283 / target 0.360 (all-live exit mix). Uses only what is known at signal time.
Caveat disclosed: the cells were fitted on the same live trades the live part reports on (in-sample for live; out of
sample for CHECK/T2 history, which never entered the fit).

## Configurations (N = 5)
| id | rule (applied to the candidate signals, before the account book, so freed slots can refill) |
|---|---|
| R1 | shorts only: skip if c_ex >= 0.12 |
| R2 | shorts only: skip if c_ex >= 0.10 |
| R3 | both sides: skip if c_ex >= 0.12 |
| R4 | shorts only: skip if price >= $100 and width < 100 bps (the zone LR8 under-charges most) |
| R5 | LIVE ONLY (history has no quotes): shorts only, skip if spread at signal > 15 bps |
Cumulative N about 8,952 -> about 8,957. Lineage bar for a lineage claim: t >= about 4.3 (stated; not this study's bar).

## Data and engines
- **Live (descriptive map + live replay):** primshorts_1126 pipeline (load_live.py -> live.parquet, exit-minute bars ->
  exitbars.parquet; calib_live.prep cleaning) copied into scratch (sha256 recorded in the report). Per trade: engine gross
  R = side x (engine exit - decision-bar close) / risk (stop -> worse of exit-minute open and stop; market -> exit-minute
  open; target -> target); **LIVE-L net** = gross - predicted LIVE-L cost (realised kind); **realised net** = gross -
  realised cost (fills, fees, 1.2 bp borrow); LR8 net for reference. Map dimensions: price band x spread band (<10,
  10-20, 20-35, 35+ bps at signal) x side x time of day (<10:30, 10:30-12, 12-14, >=14) x ETB status x family. ETB:
  executed shorts are all ETB at the time (Alpaca rejects HTB: "not shortable/ETB"); ETB status = share of the 26
  universe snapshots a name was ETB (etb_rate.parquet): always (1.0) vs marginal (<1.0). Exploratory map: cells n >= 200.
- **History (CHECK / T2 replay):** bench10 candidate lots (research/ultimate_1119/top10/bench10.py pipeline, regenerated
  tonight by arenastars_1127/as_gen.py, copied read-only into scratch): L3-gap-slope-fromopen-FD, RW3, RW5, NM-ETF (home
  Primary book: cap 30, <= 3 per symbol, -2R closed latch), G05, G07 (shorts) and G37 (long) (home testing book: cap 100,
  cost filter 0.15, <= 3 per symbol); price >= $5, shorts ETB >= 0.9 (bench10.book). Net R = gross - LIVE-L (realised
  kind; headline) and LR8 (bench10 add_r). The RND-* random-entry pools are reported as a universe control (cost filter
  on random entries).
- Splits: FIT 2024-10 + 2025-03..09 (reported, not judged), CHECK 2025-10-01..2026-11-04, T2 2023-01-03..2024-09-13.

## Controls
- **Size-matched random removal:** for each setup x split, remove the same fraction of candidate lots as the rule removes,
  at random (20 seeds), then the same book. Gain vs random = book R (rule) - mean book R (random).
- Base (no rule) for the sign of the effect.

## Pass bars (R1-R4; each on LIVE-L, on CHECK and on T2 separately; all must hold)
1. Book total R with the rule > base book total R (after costs), summed over the 7 history setups.
2. Gain vs size-matched random > 0 with day-clustered t >= 2.0 (per-day difference rule minus random mean; 5 configs x
   2 splits: both splits at t >= 2.0 is the multiplicity guard).
3. One-big-day: gain vs random without its best day > 0, best-day share of the gain < 50%.
4. Per-setup effect: of the setups the rule touches, at least 2/3 improve vs random on both splits, and none loses more
   than 0.02 R/trade vs base. Report every setup: improves / worsens / by how much (avg R per trade and total R).
5. Live direction check (not a gate on its own, but a contradiction fails): on live non-Graveyard trades the kept trades'
   LIVE-L net avg R >= all trades' avg R.
Also reported (not gates): absolute book R with the rule (does any setup or the book turn positive), LR8 view, FIT, RND
pools, avg R w/o best day and best-day share for every setup row, and which current live setups (assignments.json
2026-11-27, Graveyard excluded) flip from negative to positive LIVE-L net under each rule (no slot refill on live:
disclosed). R5 is judged on live only and can at most be a LEAD.
Verdict: PASS = a config meets all bars; LEAD = bars 1-3 on one split or live-only evidence; FAIL otherwise.
