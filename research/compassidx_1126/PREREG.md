# COMPASSIDX-1126 pre-registration (2026-11-26; written after Step 0 on FIT only, before any CHECK / T2 / live score)

Educational only — not financial advice. Research only: no config, ledger, decisions.json or live change.

## Owner override of rule 26
Rule 26 lists day-type on/off switches and hedge promotions as "ask the owner first". On 2026-11-26 the owner asked for every
effort on Market Compass steering; that request lifts the rule-26 guard for this research (as in REGSTEER-1126). Any live
use still needs the owner's yes.

## Question
REGSTEER: the W60 first-confirmed side matches the close side on 70.4% of days, but steering setups by it adds ~+0.03R/day.
Does SPY itself keep moving the compass way from confirmation to 15:55, so that the index can be traded as an overlay/hedge?

## Data (ci_lib.py)
- SPY 1-min RTH bars from data/cache_fresh (T2) and data/cache_hist (FIT, CHECK) through regsteer_1126/rs_states.bars (pyarrow
  filter + assert: the locked block 2024-11-01..2025-02-28 is never read). W60 marks = REGSTEER's point-in-time rebuild
  (rs_states.py, 300/300 parity with compute()). Live window 10-23..11-25: compute() backfill marks (compass_rd_1126) and
  Alpaca SIP 1-min SPY (compass_rd_1126 idx_bars), information only.
- Splits: FIT 2024-10 + 2025-03..09 · CHECK 2025-10-01..2026-11-04 · T2 2023-01-03..2024-09-13. Every loader and scorer
  asserts no locked row. CHECK / T2 / LIVE scripts refuse to run unless PREREG.sha256 matches this file.

## Step 0 on FIT (seen; information only, step0_FIT.json)
First confirmation (any time) -> 15:55, signed: n 169, mean +13.1 bp, median +6.2 bp, hit 53.3%, t 1.91; 5 of 8 months
positive (2025-03 +36, 2025-04 +65; May-Sep ~0). Buckets: 10:00 +17.3 (94) · 10:15-10:30 +19.9 (13) · 10:45-11:30 +13.1 (49)
· 11:45-13:00 -24.2 (12). Up side +19.7 / down side +5.8. Session-extreme stop distance: median 37 bp, 10th pct 13 bp.

## Configs (2 counted; CI-3 skipped)
**CI-1 standalone overlay (1R per day).**
- Signal: the day's first W60 confirmation (|level| = 2) at a mark T in 10:00..13:00 (marks 600..780; 09:50 is the bound,
  the 09:45 mark cannot confirm). Days whose first confirmation is after 13:00: no trade.
- Entry: open of the 1-min bar at T+1 (compute() closes a mark at T+1), side = confirmed side.
- Stop: the session extreme opposite the call over bars before entry (low for a long, high for a short), distance capped at
  0.6% and floored at 0.15% of entry. The floor is added because 10% of FIT days have < 13 bp to the extreme, where LIVE-L
  cost alone is > 0.35R and size would explode; 0.15% is fixed here, not tuned. Stop fills at min(stop, bar open) (gap-through).
- Exit: 15:55 bar open, or the stop, or **exit (no flip)** at the open of bar T'+1 for the first later mark T' that is
  confirmed the other way (level = -2 x side). Why exit, not flip: COMPASS-LEARN found the compass does not forecast the
  next 30-120 min (51.8/51.1/50.0%), so a second, later confirmation carries no stronger evidence; a flip pays a second set
  of costs on a stop that is usually tight by then; one trade a day keeps risk at 1R/day.
- R = side x (exit - entry) / stop distance - LIVE-L cost (primshorts_1126 cells_live.json, $100+ bucket: a/width_bps + b,
  kind "stop" for stop exits, "market" for time/flip exits). Gross R and a 1 bp round-trip variant reported as information.
**CI-2 compass-signed hedge on Primary's book.**
- Book: Primary 4 (L3-gap-slope-fromopen-FD, RW3, RW5, NM-ETF-late-dip-di-long) candidate lots from REGSTEER (bench10,
  LIVE-L shorts / LR8 longs) run through primshorts_1126/booksim.sim_day with the Primary rules (<= 77 lots, 30 per setup,
  3 per symbol, burst brake, -2R latch, -20R halt on realised + open marks); open marks = 1-min close path less the lot's
  LIVE-L market cost (approximation; REGSTEER's cand has no gross R). Four contexts: a (live rules: L3 in, LATCH-OPEN off),
  b L3-OUT, c LATCH-OPEN, d L3-OUT + LATCH-OPEN.
- Overlay: on CI-1 signal days, from CI-1 entry until CI-1's exit (stop / flip / 15:55), at entry and then at each later
  15-min mark + 1 min, set the SPY position h (R per 1% SPY) to offset the book's net beta E = sum over open lots of
  side x beta x 0.01 x entry / risk (beta = 60-session daily beta, shrunk 0.67b + 0.33, clipped [-3, 3], default 1; squeeze_1125
  convention) **only when the compass side opposes E, and only up to flat** (h = side x |E|; h = 0 when E has the compass
  sign). P&L = h x SPY % move; cost 4.4 bp per unit notional traded (= LIVE-L $100+ market round trip at 60 bp width / 2).
  The overlay is outside the book's latch and halt.
- Pre-declared primary context for pass/fail: a. b, c, d are reported.
**CI-3: skipped.** On FIT the 10:15-11:30 bucket (+14.5 bp, n 62) is no better than the whole window (+13.3 bp, n 168),
so FIT gives no reason to declare it; REGSTEER's all-split buckets are not used (look-ahead).

## Try count and bars
Lineage N 8,891 (REGSTEER addendum A) + REGSTEER 7 + this study 2 = 8,900 -> sqrt(2 ln 8,900) = 4.26. Also reported: 2.0, 3.46.

## Pass bar (fixed now)
CI-1, all must hold:
1. Mean R/trade > 0 after LIVE-L costs on CHECK and on T2, day-clustered t >= 2 in each (one trade/day: day t = trade t).
2. Positive R in >= 60% of months (months with a trade) on CHECK and on T2 separately.
3. Best-day share (largest day R / total R) < 10% on each split.
4. Beats placebo P1 (random side per day, 1,000 draws, seed 1126; same entry minute, own session-extreme stop, exit at the
   real trade's time/flip minute or its own stop): CI-1 mean above the 95th percentile of draw means on each split.
5. Beats placebo P2 (side = prior session's close-vs-open side; same mechanics as P1): paired day t >= 2 on each split.
6. Selection-adjusted: pooled CHECK + T2 t reported vs 4.26 (strict) and 3.46 (C). A DECISION draft needs 1-5 and t >= 3.46.
CI-2 (context a): on CHECK and on T2, avg daily R improves by >= 20% of |baseline| and the worst-5-day sum improves by >= 20%
of |baseline|, both versus the same book without the overlay.
Goal metrics (C §4) for CI-1, baseline book and CI-2: red days per 21 sessions, worst-5 sum, 20-session rolling floor,
avg R/day without the best day. Live window 10-23..11-25: CI-1 from the backfilled live compass marks (information only).
If all pass: REPORT carries a DECISION draft (journal-only shadow first, then a small live index overlay in Primary, owner's
yes). Locked block not scored in this study.
