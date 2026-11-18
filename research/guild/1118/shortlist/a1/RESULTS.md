# A1 — result (one run, 2026-11-18 ~17:40 ET, frozen plan + Amendments 1-2). Descriptive, 0 configs. Educational only — not financial advice.
Source: the Move Hunt catalogue (Live capture, 12 sessions 10-29..11-13 in the file), 253 non-blackout moves, 5-min SIP bars.
Output: a1_out.txt. Checks: 0 extreme bars missing; 0 unmeasured.

## Failures / caveats first
- **CEILING, not precision.** The rows are hindsight-picked big movers, so the clean paths (mae_first ~0.08 ATR) are partly selection.
- **The ETF regex mis-flags 5 names** (ARM, FUTU, BSP and WFRD: ADR / 'Ordinary Shares'; IVZ: Invesco Ltd). A strict-ETF re-split
  (reported apart, not the frozen table) changes per-day counts by <= 0.2 and the reading not at all.
- share_left can exceed 100%: the bar high/low vs the catalogue's close-based move_atr.

## Answer: the big moves Live misses are mostly STILL AHEAD at 09:50
- 99% of catalogued extremes come after T0 = max(decision, 09:50). On average **77% of the move is left** (1.17 ATR mean, 1.01
  median); best excursion by 15:55 is 1.34 ATR.
- Non-ETF moves with >= 1 ATR still available after 09:50: **3.4/day long + 4.8/day short** (strict-ETF split).
- Missed pools ('no setup signalled' + 'traded outside the move', non-ETF): 9.1 moves/day, **4.5/day with >= 1 ATR left**, mean left
  to extreme 1.05 ATR. Short-side 'no setup' holds the most (1.31 ATR mean, 1.4/day >= 1 ATR).
- Reading (pre-registered): >= 1 move/day still holding >= 1 ATR after 09:50 -> worth a setup search (a NEW plan, full in-play
  denominator, own count). The early moves are NOT spent by 09:50. The gap is FORESIGHT (which name, which side), not timing.
- Consequence for A-WT: 'wrong time' trades came after extremes that mostly arrive well after 09:50, so the lateness is relative to
  the move, not to the 09:50 rule.
