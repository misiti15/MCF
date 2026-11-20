# Target / R-geometry exits per family (giveback_1119/targets) — pre-registered plan

*Educational only — not financial advice.* Written 2026-11-20 before any variant was scored. Research only: no setup,
exit, config or ledger change. Builds on research/giveback_1119/map (pocket 1: far targets; t1s05 setups lose 43.6R per
100 trades after +0.8R; live targets > 1.2R from the fill: 3,100 trades, 993R given back).

## Prior results respected (not re-run)
- **Target from the fill** (Wave 2 Y3, research/crunch/wave2/exits): +0.026R/trade, t 1.58, halves +0.056/-0.010, FAIL,
  "do not re-try without new evidence". Geometry check done before scoring (no outcomes used): on live run 1 the target
  measured from the fill is *closer* than the signal-based ratio k (in every family with >= 20 trades the median
  target/risk from the fill is below k, e.g. 0.90 vs 1.00 for k = 1 setups, 0.42 vs 0.50 for CWT14; adverse
  slippage dominates, median slip +4 bp). Far targets (> 1.2R from the fill) come
  from the setups' own geometry (k = 2.0-2.5: LIQ, MF1, MF2, CWT09, NS4, ST4, orb20; CWT12 21%), not from anchoring.
  Re-anchoring to the fill would push most targets *farther*. So no fill-anchoring variant is justified: 0 configs.
- L16 near-target BE, book-wide BE, W5 X1-X3, Wave 2 trail-after-+1R: not re-run (stop moves are not this class).
- Wave 2 Y1 1.25x target on RW3/RW5 (optional): a larger target; this class tests closer / partial / no target.
- time_in_trade (sibling): checkpoint exits FAIL; the time-cap variant here (C6) is a fixed horizon with no target.

## Data
- **Scoring sample: 2-year lab.** bt_lab1104 lists, first signal per (setup, symbol, day), walked on cache_hist
  1-minute bars exactly as map/lab_paths.py (BEREPLAY: entry = signal-bar close, stop/target from live geometry
  GK, stop-first inside a bar, bars through the 15:54 minute, bt_all costs incl. tier x3 for |gap| >= 20 or px < 5).
  Locked block 2024-11-01..2025-02-28 filtered at read and asserted absent. Unit = stop distance.
- **Fit = sessions <= 2025-09-30, check = later** (scored once).
- **Live (descriptive only, never a pass input):** run 1, all 10 journals, 10-06..11-19 (map's de-duplicated trades,
  LR8 R), 1-minute SIP bars re-fetched read-only (map's fetch_bars.py), walked from the minute after entry to 15:55
  on the parent bracket and each variant; paired delta = variant - parent on the same engine; live per-trade cost
  (R_booked - R, i.e. LR8) subtracted from both arms. GEN hold setups (no target) are reported for C1/C2 only.

## Variants (fixed, nothing else searched) — 6 configs
Levels in stop units from the entry (fill). All keep the parent stop and the 15:54/15:55 flatten.
- **C1 PART06**: 50% exits at +0.6 (limit), the rest keeps the parent bracket. Only trades whose target > 0.6.
- **C2 PART08**: same at +0.8. Only trades whose target > 0.8.
- **C3 CAP10**: target = min(parent target, +1.0). Changes only targets > 1.0 (lab t1s05; live k >= 2 setups).
- **C4 CAP15**: target = min(parent target, +1.5). Changes only targets > 1.5.
- **C5 NOTGT-EOD**: no target; exit at the stop or the end-of-day flatten (time-exit-only).
- **C6 NOTGT-120**: no target; exit at the stop or at the close of the 120th minute after entry.
Rules inside a bar: stop first (a partial/cap level touched in the same bar as the stop does not fill).
**Costs:** parent conventions (target limit 0 exit cost, stop SL + px x BP + SX, flatten SL + px x BP) plus an extra
exit cost on every early exit: partial and cap limit fills pay SL + px x BP + 0.01/share (as a market exit plus the
early-exit allowance); the C6 time exit pays SL + px x BP + 0.01/share. C5's EOD flatten pays the parent flatten cost.

## Selection (fit half only), per family-side (family = setup prefix, x side)
For each family-side and config compute the paired delta (variant - parent) per trade. Adopt the fit-best config only
if: fit total delta > 0, fit day-clustered t >= 2.0, fit delta w/o its best day > 0, >= 100 changed fit trades.
Family-sides with no passing config keep the parent. Secondary (reported, not the primary verdict): each config
applied book-wide (all families), scored on check with per-family better/worse counts and sizes.

## Configs and bar
Per-family: 6 configs x F family-sides (F stated in RESULTS) + 6 book-wide. Lineage N = map 916 descriptive cells +
time_in_trade 2,664 + day_lock 16 + this class. Bar = max(1.5, sqrt(2 ln N)) on the paired check t (day-clustered).

## Pass rule (check half, scored once)
1. total R and avg R per trade improve after costs; 2. avg R w/o best day not worse; 3. best day's share of the paired
improvement < 50%; 4. more family-sides and setups better than worse (sizes reported); 5. paired t >= bar.
All five needed. Report every adopted config and the book-wide table; live descriptive table with rule changes inside
the window (research/ledger.jsonl, as listed by the map).
