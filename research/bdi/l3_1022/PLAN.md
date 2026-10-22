# l3_1022 PLAN - Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD): early Primary review (owner 2026-10-22 evening)

*Educational only - not financial advice. Written 2026-10-22 ~16:30 ET, before any variant was scored. Not changed
after scoring (any later addition is marked "added after PLAN" and counted).*

Builds on, does not redo: gates1021 (10-21 autopsy, 16 L3 tweaks, none passed), regime1022 (Bear +272R vs rest
-1,020R; 2-year as-run -0.031R/trade; no gate qualifies), top5_1021, research/replay/VALIDATION.md (5-bar gate,
gap.json / broad.json).

## Data and rules
- History: research/history2y lab frames (5-minute), open months only; the locked block 2024-11-01..2025-02-28 is
  never read (lib refuses it; every loader asserts it). No holdout is scored.
- TRAIN = sessions <= 2025-12-31, VALID = 2026-01-01..2026-10-07 (end of frames).
- Costs always in: production cost (1c + 1 bps per side, target exits free as limits, +2c on stops), time-of-day entry
  multiplier, x3 on the extended tier (|gap| >= 20% or price < $5) - exactly gates1021 `prod_r_tier`.
- Parent "as-run" = mask + window 09:50-15:00 + refire chain cooldown 1 + at most 3 open lots per symbol, exits on the
  5-minute path (stop first inside a bar), t1s1 (R = 0.25 x daily ATR, stop 1R, target 1R, else 15:55 close).
- Live = paper journals run 1: Primary (origin/mcf-data), Testing 1 (origin/mcf-data-testing), Testing 2, Graveyard.
  R after costs = pnl_adj / (|entry - stop| x shares) (regime1022 convention). Regime labels = regime1022 definitions
  (SPY open->close +-0.5%, range vs 20-day median); 10-22 from a read-only SIP fetch of SPY bars, else "unknown".

## Part 1 - live record (descriptive, not counted)
Primary-only and all accounts merged: trades, sessions, win% vs break-even win%, avg R, day-clustered t, last-4,
by day, by regime, lots per symbol-day (stacking), time of day (entry hour buckets).

## Part 2 - why live (+0.15R Testing 1) differs from the 2-year backtest (-0.031R) (descriptive, not counted)
(a) regime mix of live sessions vs history, re-weighting the 2-year per-regime avg R to the live mix;
(b) the 2-year backtest on the same live sessions is not possible (frames end 2026-10-07) - use the replay results
already on file (VALIDATION.md gap.json / broad.json) for the 5-bar gate, blocks and fills; run `python -m mcf.replay`
only if the 1-minute bar store is present (else say so);
(c) refire/stacking share of live trades and their R; (d) signals per day live vs backtest (selection by caps/skips).

## Part 3 - variant grid (pre-declared; 22 configurations, all scored, all reported)
Each variant changes ONE thing vs the parent (two pre-declared combos at the end). Filters keep the parent's exits.
| id | variant |
|---|---|
| P0 | parent as-run (reference, counted) |
| S1 | one lot per symbol (cap 1) |
| S2 | refire off (first signal per symbol-day) |
| S3 | refire cooldown 3 |
| S4 | refire cooldown 6 |
| W1 | entries from 10:30 |
| W2 | entries from 11:00 |
| W3 | entries until 14:00 |
| X1 | stop 1.5x wider, same $ risk (1 R = 1.5 x 0.25 ATR), target unchanged in price (0.667 new R) |
| X2 | stop 2x wider, same $ risk, target unchanged in price (0.5 new R) |
| X3 | time stop: exit at the close of the 12th bar after entry (60 min) if no stop/target |
| X4 | time stop 120 min (24 bars) |
| X5 | scale-out: half at +0.5R (limit), half to the 1R target with its stop moved to entry after the first half fills |
| G1 | gap band: only gap >= -10% (drop very large gap-downs) |
| G2 | gap band: only gap >= -6% |
| G3 | gap band: only gap <= -4% (drop the smallest gaps) |
| R1 | stock vs SPY: skip when fromOpen - SPY fromOpen > 8 (runaway recoveries) |
| R2 | stock vs SPY: only when fromOpen - SPY fromOpen >= 4.5 |
| V1 | skip when SPY is above its VWAP at entry |
| V2 | skip when SPY and QQQ are both above their VWAP at entry |
| C1 | combo: S1 + W1 |
| C2 | combo: S3 + V1 |

Random control: for each signal, one random symbol-row at the same date and minute (seed 20261022, eligible = atr > 0,
finite outcome, not the same symbol), shorted with the same exit rule and costs; a variant's control = the controls
of its kept trades.

## Pass rule (pre-declared). A variant can be recommended to REPLACE the parent only if ALL hold:
1. avg R after costs > 0 in TRAIN and in VALID, with >= 30 / 20 trades;
2. beats its random same-minute control (avg R) in TRAIN and in VALID;
3. no single day carries > 25% of its total R (total R > 0);
4. better than the parent: avg R higher in both periods, and day-clustered t of the per-day difference in total R
   (variant - parent, same days) >= bar;
5. not over-restrictive: keeps >= 50% of the parent's trades in both periods, and the trades it drops (filters) have
   avg R < 0 in both periods (it does not cut profitable trading).
Bars: study N = 22 -> max(1.5, sqrt(2 ln 22)) = 2.49; L3 lineage N = layering 11,178 + gates1021 718 + regime1022
384 + 22 = 12,302 -> sqrt(2 ln 12302) = 4.34. A replacement needs the lineage bar; meeting only the study bar with
1-3 = "near-miss" (Testing candidate via backlog, not a replacement).
Also reported per variant: Bear vs non-Bear avg R (does it keep the down-day strength and cut up-day losses?).

## Decision rule for the recommendation (pre-declared)
- REPLACE with variant X if a variant passes 1-5 at the lineage bar.
- DEMOTE to Testing 1 if no variant passes AND the 2-year as-run is negative in both periods AND the live-shaped
  replay on file / live Primary record is not positive (the regime1022 10-27 condition: Primary record below
  break-even). 
- KEEP otherwise (live evidence positive enough to wait for 10-27).
