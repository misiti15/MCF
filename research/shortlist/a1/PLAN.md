# A1 — how much of the big moves Live misses is still left after 09:50 (Scout, frozen 2026-11-18 ~05:20 ET, BEFORE any outcome is read)
Educational only — not financial advice. Descriptive, **0 configs**, no bar. Lead lead-20261118-0300-1 / -0500-1; Skeptic -0750-1 / -0950-1.

Owner-level question: of the big moves Live misses, how much is still left to capture after 09:50, by side and by miss reason?

## Data
- Moves: the MCF Move Hunt catalogue `research/bdi/moves/moves.csv`, set 'all', earnings blackout excluded. That is 244 symbol-days
  with 5-min bars, from sessions 10-29 onward. The rows are HINDSIGHT-picked big moves, so this is a ceiling, not a precision.
- Bars: `fetch_a1.py` (#43 guard), 5-min SIP, 09:30-15:59 ET per session, in scratch a1_m5.csv.gz.
- Daily ATR: the catalogue's atr_pct_d (% of price). ETF flag: the name regex in MCF data/universe.csv, the same as SHORTUP's.
  ETFs are reported as their own row, not deduped (index ETFs repeat one market move).

## Measures (price at time T = close of the 5-min bar that ENDS at T)
- T0 = max(decision, 09:50) and P0 = price at T0.
- **End = 15:55** (the close of the 15:50 bar). Live is flat by 15:55, so the 16:00 close and auction are never used.
- `left_to_extreme` = the favourable move from P0 to the price at the move's own extreme time, in daily ATR; 0 if the extreme came at or before T0.
  `share_left` = left_to_extreme / move_atr.
- `left_mfe` = the best favourable excursion from P0 within [T0, 15:55] (highs for long, lows for short), in daily ATR.
- `mae_first` = the adverse excursion from P0 before that best point, in ATR (what a holder had to sit through).
- `close_left` = price at 15:55 vs P0, in ATR (signed by side).

## Report (one run, after 16:30 ET or any closed hour; every row printed)
Rows: side x miss bucket (caught / traded outside the move / no setup / wrong side only / skipped (any filter)) x ETF yes/no.
Columns: n, per day, the share of moves whose extreme comes after 09:50, mean and median left_to_extreme, mean share_left,
mean left_mfe, mean mae_first, mean close_left, and the counts per day with left_mfe >= 0.5 and >= 1.0 ATR.
Reading: a pool with >= 1 move/day still holding >= 1 ATR after 09:50 is worth a setup search (a NEW plan, with its own count and
a full in-play denominator). If < 0.5 ATR typically remains, the early moves are mostly spent before Live may trade.
No side line (dropped: hindsight movers make both sides look good; checklist 20).

## Amendment 1 (2026-11-18 ~07:20 ET, before any outcome; Skeptic skeptic-20261118-1150-1/-1151-2, Lead lead-20261118-0700-1)
- **Bug fix:** catalogue 'extreme' times are 1-min stamps, often off the 5-min grid (217 of 253). Each one now maps to the 5-min bar
  that CONTAINS it (end = floor to 5 min + 5, capped at 15:55). That bar's high (long) or low (short) is the level reached. Before
  the fix, off-grid extremes silently gave 0.
- The flag is now 'extreme after T0' (the measure's start), with 'after 09:50' printed beside it.
- The run prints how many catalogue symbols the ETF regex flags and the first 10 with their names, so 'Trust' banks/REITs show.
- Selftest adds an off-grid extreme (12:14 -> bar ending 12:15, expected 2.425 ATR, exact) and checks bar_end edge cases
  (12:14 -> 12:15, 12:15 -> 12:20, 15:58 -> capped 15:55). The early case uses 09:45 (inside the bar ending at T0 09:50 -> 0 left).

## Amendment 2 (2026-11-18 ~09:15 ET, Skeptic -1350-1 / Lead -0900-1): print the count of moves whose extreme bar is missing from the 5-min data (still 0 left; checklist 46), and note that share_left can exceed 100% (bar high/low vs the close-based move).
