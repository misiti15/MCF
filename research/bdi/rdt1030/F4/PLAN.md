# rdt1030 / F4 irl-erl: pre-declaration

*Educational only — not financial advice.*

Written 2026-10-30, before any configuration is scored. No outcome column has been read. Research only: no repo, config/,
mcf/, ledger or backlog writes; nothing is committed.

Source: the owner's Reddit post of 2026-10-30, idea (2) "IRL -> ERL": price flushes a low (sell-side liquidity sweep),
displaces back up forming a higher-timeframe FVG; the first HTF FVG created is the entry; target fixed or the clear draw
on liquidity. Design: `../DESIGN.md` sections 0 and F4. The table below is copied from it unchanged.

## Rule (F4-01, long; shorts are the exact mirror with highs/lows swapped)
- **HTF bars:** 15-min bars aligned to 09:30 built from the 5-min rows (0935-0945 head rows + 0950-1500 frame rows):
  bar b ends at 0945, 1000, 1015, ... 1500. H = max high, L = min low, C = last 5-min close, O proxy = prior HTF close
  (`open_d = close/(1+fromOpen/100)` for the first bar). A bar is known at its last 5-min row. A bar counts only if all
  three of its 5-min rows are present.
- **Sweep:** PDL variant: the day opened above PDL (`open_d > PDL`) and the first 5-min row from 0935 with
  `low <= PDL - 0.05 ATR_d` is the sweep row. ORL variant: OR15 defined (three head rows, width >= 0.05 ATR_d) and the
  first row from 0950 with `low <= ORL - 0.05 ATR_d`. The sweep's HTF bar is s.
- **First HTF FVG after the sweep:** the first K (K-2 >= s, K - s <= 8, all three bars complete and consecutive) with
  `L[K] - H[K-2] >= 0.05 ATR_d` and >= $0.02. That FVG is the only candidate: it trades only if all of these hold,
  otherwise that side is finished for the day (literal "the first HTF FVG created is the entry"):
  - displacement: `C[K-1] - O[K-1] >= 0.20 ATR_d` (O[K-1] = C[K-2]);
  - `C[K] >` the swept level;
  - not void: `L[K-1] >=` the day's low through bar K-2 (no new low after the FVG's first candle);
  - the end of bar K is between 1015 and 1400.
- **Entry (formation):** C[K] at bar K's last 5-min row. **Stop:** SL - 0.02 ATR_d, SL = the day's low through bar K.
  **Risk guard:** 0.10 <= R/ATR_d <= 1.0, else skipped.
- **Target DOL:** the nearest of {PDH, the session high made before the sweep row} that is >= 1.0R above entry, capped
  at 4R; if neither qualifies, 2R. **2R rows:** always 2R.
- **Retrace entry:** after formation, a limit at the FVG top L[K]. It fills at L[K] on the first of the next 6 five-min rows
  (30 min) whose `low <= L[K] - 0.01`; the fill bar is checked for the stop, never the target. R, the risk guard and the
  target are re-measured from the fill price. The order is cancelled if, before the fill row, a row's high reaches the
  target price (computed from the fill price).
- **Short:** PDH (day opened below PDH) or ORH sweep `high >= level + 0.05 ATR_d`, bearish displacement
  `O[K-1] - C[K-1] >= 0.20 ATR_d`, bearish FVG `L[K-2] - H[K] >= 0.05 ATR_d`, `C[K] <` level, stop SH + 0.02 ATR_d,
  DOL = nearest of {PDL, pre-sweep session low}; retrace limit at H[K].
- **Universe:** adv20 >= $95M and atr_d > 0 on the entry row. One trade per symbol-day per row. Flat at 15:55.

## Configurations (18 counted)
| row | level, side | entry | target | other | plain-English name |
|---|---|---|---|---|---|
| F4-01 | PDL, L | formation | DOL | | Prior-Day-Low Sweep then 15-min Gap, Long (to liquidity) |
| F4-02 | PDL, L | formation | 2R | | Prior-Day-Low Sweep then 15-min Gap, Long (2R) |
| F4-03 | PDL, L | retrace | DOL | | Prior-Day-Low Sweep, buy the 15-min Gap retest, Long (to liquidity) |
| F4-04 | PDL, L | retrace | 2R | | Prior-Day-Low Sweep, buy the 15-min Gap retest, Long (2R) |
| F4-05 | ORL, L | formation | DOL | | Opening-Range-Low Sweep then 15-min Gap, Long (to liquidity) |
| F4-06 | ORL, L | formation | 2R | | Opening-Range-Low Sweep then 15-min Gap, Long (2R) |
| F4-07 | ORL, L | retrace | DOL | | Opening-Range-Low Sweep, buy the 15-min Gap retest, Long (to liquidity) |
| F4-08 | ORL, L | retrace | 2R | | Opening-Range-Low Sweep, buy the 15-min Gap retest, Long (2R) |
| F4-09 | PDH, S | formation | DOL | | Prior-Day-High Sweep then 15-min Gap, Short (to liquidity) |
| F4-10 | PDH, S | formation | 2R | | Prior-Day-High Sweep then 15-min Gap, Short (2R) |
| F4-11 | PDH, S | retrace | DOL | | Prior-Day-High Sweep, sell the 15-min Gap retest, Short (to liquidity) |
| F4-12 | ORH, S | formation | DOL | | Opening-Range-High Sweep then 15-min Gap, Short (to liquidity) |
| F4-13 | ORH, S | formation | 2R | | Opening-Range-High Sweep then 15-min Gap, Short (2R) |
| F4-14 | PDL, L | formation | DOL | displacement >= 0.30 ATR_d | PDL Sweep + strong 15-min push, Long |
| F4-15 | PDL, L | formation | DOL | HTF FVG >= 0.10 ATR_d (also defines "first") | PDL Sweep + big 15-min Gap, Long |
| F4-16 | PDL, L | formation | DOL | sweep = any trade-through (low < PDL) | PDL shallow-sweep then 15-min Gap, Long |
| F4-17 | PDL, L | formation | DOL | BE at +1R | PDL Sweep then 15-min Gap, Long, break-even at +1R |
| F4-18 | parity: CWT14 p05 long, unpatched `scan_1028.sim`, must give TRAIN -0.0677 / VALID -0.0675 (±0.002) | | | | harness check, not a candidate |

## Harness
- Frames/splits: `scan_1019.build_paths`; `_cut` monkeypatches and asserts copied from pdl1030/combo/build.py.
  TRAIN 2024-10, 2025-03..12; VALID 2026-01..03, 2026-07..2026-09-15. Locked block and HOLD months never loaded.
- Simulator: numba copy of `scan_1028.sim` with DESIGN 0.2 patches (per-trade R and target multiple up to 4R; 1c+1bp
  entry × ToD multiplier; 1c+1bp on every exit incl. targets, +2c on stop/moved-stop exits; ×3 extended tier; gap-through
  stops at min(stop, high)/max(stop, low); limit-entry price with the fill bar checked for the stop only). With patches off
  it must equal `scan_1028.sim` exactly (`python build.py check`).
- Random control: per trade, 5 random other universe symbols at the same entry row (the fill row for retrace rows;
  entered at that row's close), seed 20261030, same side, same R in ATR units, same target multiple, same BE, same sim/costs.

## Bar (BAR90, rules 21-22)
N = 2,000 + 108 (swarm total) + any rework rows counted swarm-wide; t_req = 0.9 × max(1.5, sqrt(2 ln N)) = 3.52 at N = 2,108.
Pass needs: day-clustered t >= t_req; `gates.walk_forward` share >= 54%; avg R > 0 on TRAIN and VALID separately;
>= 3 trades/session; avg R > 0 on SPY up and down days; avg R above the random control. Every column of F1's report is
reported (n, trades/session, win rate, avg win/loss R, ratio, TRAIN/VALID/all, t, WF, up/flat/down, w/o best day + share,
busiest session share, median cost/R, exit mix, control).

## Sanity check before scoring
Print F4-01/F4-05/F4-09/F4-12 trades per session, median R/ATR, median cost/R, median entry time and DOL-vs-2R share
before any R column is read. Expectation: well under 3 trades/session for the PDL rows (a large-bodied 15-min candle
plus a 15-min FVG after a sweep is rare); this is a known trade-rate risk, reported, not tuned away.

## Rework (rule 18)
Only after a row fails, only as new counted rows declared here by a dated amendment before they are scored.

## Amendment 2026-10-30 (after all 17 candidate rows failed; parity F4-18 exact): 6 rework rows, counted
Observed failure mode (from the scored table, the reason for these rows): stops under the sweep extreme are wide
(median R about 0.6 ATR), so about 80% of trades end at the 15:55 flatten; avg R equals the random control; R splits
by market direction. Rework = one change each (rule 18):
| row | base | change | name |
|---|---|---|---|
| F4-RW1 | F4-05 (ORL L) | fixed 1R target | Opening-Range-Low Sweep then 15-min Gap, Long, fixed 1R |
| F4-RW2 | F4-01 (PDL L) | fixed 1R target | Prior-Day-Low Sweep then 15-min Gap, Long, fixed 1R |
| F4-RW3 | F4-05 (ORL L) | stop at the FVG's first 15-min candle low - 0.02 ATR (tighter), guard unchanged | Opening-Range-Low Sweep then 15-min Gap, Long, tight stop |
| F4-RW4 | F4-05 (ORL L) | index context: `qqq_fo >= +0.20%` at the entry row | Opening-Range-Low Sweep then 15-min Gap, Long, Nasdaq up |
| F4-RW5 | F4-12 (ORH S) | index context: `qqq_fo <= -0.20%` at the entry row | Opening-Range-High Sweep then 15-min Gap, Short, Nasdaq down |
| F4-RW6 | F4-01 (PDL L) | index context: `qqq_fo >= +0.20%` at the entry row | Prior-Day-Low Sweep then 15-min Gap, Long, Nasdaq up |
N becomes 2,000 + 108 + 6 (F1 rework) + 6 (this) = 2,120 (t_req 3.52; other families' rework rows raise it further at the lead's tally).
