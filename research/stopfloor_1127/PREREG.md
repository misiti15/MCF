Educational only — not financial advice

# STOPFLOOR-1127 pre-registration (written 2026-11-27 ~19:30 ET, before any outcome is scored)

Research only. No change to config/, setups, exits, docs/live/assignments.json, decisions.json or the ledger.

## Hypothesis
Very tight stops (stop width small versus price, spread or cents) are a cost-driven failure mode across setups: costs are a
large share of 1R, so these lots lose more R per trade than wider ones. Observed 11-27: Primary AHCO lots with 8-9 cent
stops (-2.66R open on -$54). Two targeted remedies: (a) skip entries whose stop is below a floor; (b) widen the stop to the
floor and resize so $ risk (1R) is unchanged (keeps the trade, i.e. playing time).

## Prior work in this lineage (read before writing this)
- p3_1029 A1/A2/A3 (stop >= $0.10 / $0.15, stop cost <= 0.15R): improvements on 2 yrs, explained as cost avoidance (removed
  trades had the same gross edge). A3 is live in Testing 1/2, Explore 1, Live Lab since 10-30 (ledger 2026-10-29 CF).
- cfprimary_1127 (tonight): CF-15 / CF-LL15 skip on the Primary book FAILS vs same-share random removal on CHECK.
  Salvage lead there: the selection gain sits in the tight-stop RW3/RW5 gap-down shorts.
- New here: the widen-and-resize remedy (b) (not tested before), bp- and spread-based floors, per-setup breadth on live.

## Data
- Bench: Primary's 4 setups' bench10 candidate lots (regsteer_1126 rs_cand.py output, scratch rsw/cand.parquet;
  L3-gap-slope-fromopen-FD, RW3, RW5 shorts t1s1; NM-ETF-late-dip-di-long t05s1), pre-book (every candidate lot, no caps
  = the testing-arena view). The 4 GEN setups in that file are excluded (their hold/trail exits are not in the walk).
  Exits re-walked on 1-minute bars (cache_hist from 2024-09-16, cache_fresh before) with the stopx_1127 BASE rule:
  stop on intrabar touch (gap-through at the worse of open/stop), target traded through by $0.01, stop first, flat 15:55.
  Parity: BASE must reproduce the cand exit minute on >= 99% of lots.
- Splits: FIT 2024-10 + 2025-03..09 (information only), CHECK 2025-10-01..2026-11-04, T2 2023-01..2024-09.
  Locked block 2024-11-01..2025-02-28 never read (asserted in every loader).
- Live: the cleaned primshorts_1126 live set (scratch ps_live, 10 journals, run 1, 10-14..11-25, R3C cleaning, exit-minute
  SIP bars), all accounts EXCEPT Graveyard. Live realized R per trade = decision-basis gross (ref price -> engine exit) minus
  the realized cost (calib_live.prep real_R). Spread = the signal's spread_bps at decision.
- Costs: LIVE-L (primshorts_1126 cells_live.json, cost_R = a/width_bps + b per price bucket x exit kind) is the primary
  basis for all 4 bench setups; LR8 research (bench10 add_r) shown as a second basis. Widened lots are costed at the widened
  risk (that is the mechanism being tested).

## Measurement (not configs)
Avg R after LIVE-L (and LR8; live: realized) by bins of stop width: bp of price (<25, 25-50, 50-75, 75-100, 100-150, 150-250,
250+), cents (<0.10, 0.10-0.20, 0.20-0.35, 0.35-0.60, 0.60+), and spreads (live only: <6, 6-8, 8-12, 12-20, 20+). Gross R
per bin shown to separate cost from edge.

## Configs (18 counted)
Bench (10): skip if width < X bp, X in {50, 75, 100}; skip if risk/share < $0.10, $0.20 (5).
            widen to X bp floor, X in {50, 75, 100}; widen to $0.10, $0.20 floor (5). Widen: new risk R' = max(risk, floor);
            stop' = entry - side*R', target' = entry + side*tmult*R' (R geometry kept); shares resized so $ risk is unchanged;
            R measured in units of R'. Same walk.
Live (8): skip if width < X bp (50/75/100), < k spreads (k 6/8/12), < $0.10 / $0.20. (Live widen cannot be walked: the
            1-min cache ends 11-04 and live exit bars are exit-minute only; not run, not counted.)
Cumulative N ~ 8,952 -> ~ 8,970. Lineage bar (t >= ~4.3) shown for reference.

## Pass bars (a config passes only if ALL hold; per-study multiplicity: 10 bench configs -> t >= 3.0)
1. Bench dR/day (sum over lots per session, config minus BASE, LIVE-L) > 0 on CHECK and on T2, paired day-clustered t >= 3.0
   on each.
2. Control: dR above the 95th percentile of 200 random controls on CHECK and T2. Skip: random skip of the same share of lots
   within setup x split. Widen: the same widening multipliers (R'/R) permuted at random across lots within setup x split
   (tests whether targeting the tight lots matters versus widening any lots).
3. One-big-day: best-day share of dR < 25% on each split; avg dR without the best day reported (> 0).
4. Per setup (remedy breadth): among setups with >= 5% of lots affected, >= 2/3 improve on both CHECK and T2, and none is
   worse by more than 0.02R per lot (over all its lots) on either split. Per-family table (gap-down shorts: L3, RW3, RW5;
   ETF long: NM-ETF). LR8 basis must have the same sign.
5. Live agreement (skip configs): non-Graveyard live trades the rule would skip have lower avg realized R than kept trades,
   and the skip beats the 95th pct of 500 same-share random skips (within setup) on live dR. Per-setup live table
   (how many setups improve / worsen, by how much). Widen configs: no live leg (stated).
The absolute level (post-remedy avg R positive on CHECK and T2) is reported; a remedy can pass while the book stays
negative, and the report says so.

## Reporting
Every config listed (pass/fail per bar), gross vs net decomposition, per-setup and per-family effect counts, best-day
share, rule changes in the live window from research/ledger.jsonl. Backlog proposal only if a config passes.
