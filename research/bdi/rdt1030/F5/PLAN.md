# rdt1030 / F5 fvg-context — one indicator per row on two fixed base entries (PLAN, written before any score)

*Educational only — not financial advice.*

Written 2026-10-30 before any F5 outcome was computed. Source: `research/bdi/rdt1030/DESIGN.md` (section 0 harness and the
F5 table), copied unchanged. The base entries were fixed in DESIGN.md before any F1/F4 result existed (no selection
leakage). F1, F2 and F4 have since been scored by their own testers (all failed); F5 does not change its rows because of that.

## Base entries (reused code, not re-written)
- **F1-A** "15-min Opening Range Break with Gap" (both sides): entry code = `research/bdi/rdt1030/F2/build.py:kernel`
  (the F1-A builder that reproduced F1's own F1-A exactly: n 48,612 L / 48,807 S). OR15 from the 0935-0945 head rows;
  fresh close beyond ORH/ORL at tod >= 0950; a 5-min FVG (>= 0.05 ATR_d and >= $0.02) completing at the break row or
  the next row; signal 0955-1100; first per symbol-day per side; entry close[i]; stop low[i-2] / high[i-2]; 0.03 <= R/ATR_d
  <= 1.0; target 2R if R <= 0.085 ATR_d else 1R; flat 15:55.
- **F4-01** "Prior-Day-Low Sweep then 15-min Gap, Long (to liquidity)": entry code = `research/bdi/rdt1030/F4/build.py:run_signal("PDL", tmode=0, retrace=False)`
  — sweep >= 0.05 ATR_d through PDL (day opened above PDL), 15-min displacement body >= 0.20 ATR_d, first 15-min FVG
  (>= 0.05 ATR_d) after the sweep closing back above PDL within 8 HTF bars, entry at the FVG bar's close (1015-1400),
  stop sweep low - 0.02 ATR_d, target = nearest of {PDH, pre-sweep HOD} >= 1R away else 2R, cap 4R.
- Sanity check before scoring: the base rows built here must reproduce F1-A (n 48,612 / 48,807) and F4-01 (n 6,498)
  from the F1/F2/F4 folders. If not, stop and fix before reading any F5 row.

## F5 rows (indicator read at the signal row i, i.e. known at its close; side-relative; applied to the base trade, so each
## row is a subset of its base — a day whose base trade fails the gate is not re-tried later)
| row | base | indicator (L / S) | setup name |
|---|---|---|---|
| F5-I1 | F1-A L, S | VWAP side: `vwapDistPct` > 0 / < 0 | 15-min ORB with Gap + VWAP Side |
| F5-I2 | F1-A L, S | RSI(14) momentum: `rsi` >= 55 / <= 45 | 15-min ORB with Gap + RSI Momentum |
| F5-I3 | F1-A L, S | RSI(5) not exhausted: `rsi5` <= 90 / >= 10 | 15-min ORB with Gap + Not Overextended (RSI5) |
| F5-I4 | F1-A L, S | order flow: `buyPressure` >= +0.20 / <= -0.20 | 15-min ORB with Gap + Order Flow With You |
| F5-I5 | F1-A L, S | move from open: (close - open_d) / ATR_d >= +0.30 / <= -0.30 (open_d = close / (1 + fromOpen/100)) | 15-min ORB with Gap + Strong Move From Open |
| F5-I6 | F1-A L, S | SMA50 (5-min) side: `sma50_dist_pct` > 0 / < 0 | 15-min ORB with Gap + Above/Below SMA50 |
| F5-I7 | F1-A L, S | MarcoFlow heat: `heat` >= +10 / <= -20 | 15-min ORB with Gap + MarcoFlow Heat |
| F5-I8 | F1-A L, S | index context: lab `breadth` >= 0.60 / <= 0.40 (context row at the same date, tod) | 15-min ORB with Gap + Market Breadth |
| F5-J1 | F4-01 L | VWAP side: `vwapDistPct` > 0 | Prior-Day-Low Sweep then 15-min Gap + Above VWAP, Long |
| F5-J2 | F4-01 L | order flow: `buyPressure` >= +0.20 | Prior-Day-Low Sweep then 15-min Gap + Buyers In Control, Long |

**18 configs** (8 x 2 sides + 2). The base rows F1-A L/S and F4-01 L are reported only as reference parents (they are
F1's and F4's configs, not counted again). Missing indicator value -> trade dropped from that row (coverage reported).

## Simulator, costs, statistics (DESIGN 0.2 / 0.3, unchanged)
- Sims reused, not edited: F2's `sim` (F1-A trades) and F4's `sim(..., patched=True)` (F4-01 trades) — both are
  `scan_1028.sim` copied and patched: per-trade R and target multiple; entry 1c + 1 bp x ToD multiplier (1.4 before 10:30);
  every exit 1c + 1 bp incl. targets; +2c on stop / moved-stop exits; x3 extended tier (|gap| >= 20% or price < $5);
  gap-through stop fill min(stop, high) / max(stop, low). Harness parity (F4-18, CWT14 p05 = -0.0677) was matched exactly
  by F2 and F4 on the same frames; F5 re-uses their code and frames.
- Frames: `scan_1019.build_paths`, `_cut` monkeypatches (CUT 2026-09-15) and asserts from pdl1030/combo. TRAIN 2024-10,
  2025-03..12; VALID 2026-01..03, 2026-07..2026-09-15. Locked block 2024-11-01..2025-02-28 and HOLD months never loaded.
- Universe adv20 >= $95M on the signal row, atr_d > 0.
- Bar (BAR90): N = 2,000 + all configs in this swarm. At the time of writing the swarm count is 108 (DESIGN) + 6 (F1
  rework) + 6 (F2 rework) + 6 (F4 rework) + F3 rework (read from F3 folder at scoring time) + any F5 rework; t_req =
  0.9 x max(1.5, sqrt(2 ln N)) (~3.52). Pass = t_day >= t_req, gates.walk_forward share >= 54%, avg R > 0 TRAIN and VALID,
  >= 3 trades/session, SPY up-day and down-day R > 0, avg R above the random control (K = 5 random other universe symbols at
  the same signal bar, same side, same R in ATR units, same target multiple, seed 20261030).
- Reported per row: n, trades/session, win rate, avg win / avg loss (R), avg R TRAIN / VALID, t_day, WF share, up / flat /
  down-day R, avg R w/o best day + its share (flag >= 50%), busiest-session share, median cost/R, exit mix, control R,
  opportunity retained vs the base (trades kept, top-decile winners kept; >= 80% / >= 90% to be proposable as a filter).

Rework (rule 18) only after the 18 rows are scored, as new counted rows, declared in a dated amendment below before scoring.

## Amendment 2026-10-30 (rule 18 rework; declared after all 18 rows failed, before any of these is scored) — 5 new counted configs
All 18 rows failed (results.csv): every row is negative on TRAIN and VALID, the base reproduced exactly (F1-A L -0.0753 /
S -0.0741, n 48,612 / 48,807; F4-01 -0.0306, n 6,498). Indicators shift avg R by at most ~0.02R and none removes the
SPY up/down split. Rework rows (neighbours / one condition added; no new indicator families):
| row | rule | sides | setup name |
|---|---|---|---|
| F5-RW1 | F1-A + move from open >= +0.50 / <= -0.50 ATR_d (neighbour of I5) | L, S | 15-min ORB with Gap + Very Strong Move From Open |
| F5-RW2 | F1-A + I4 (buyPressure ±0.20) + round-trip cost <= 10% of R (F1-G cost floor added) | L, S | 15-min ORB with Gap + Order Flow + Low Cost |
| F5-RW3 | F4-01 + J1 + J2 together (VWAP side and buyPressure >= +0.20) | L | Prior-Day-Low Sweep then 15-min Gap + Above VWAP + Buyers In Control, Long |
N = 2,000 + 132 (swarm so far) + 5 = 2,137; t_req recomputed (3.52). No further rework is declared by F5.
