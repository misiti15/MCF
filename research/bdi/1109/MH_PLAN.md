# MH1109-P1 — "in play, compass side" (pre-registered 2026-11-09, before any two-year number)

*Educational only — not financial advice. Research only; nothing in config/ or the trading path changes.*

**From the Move Hunt 11-09** (moves_1109_out.txt, precursors_1109_out.txt): on a trend-up day (W60 UP-confirmed at 10:00,
SPY +1.44 %) the biggest tradable long moves ran from the open to ~11:00 with almost no heat (MAE ≤ 0.08 ATR: MPWR, PL,
AVAV, FN, TSEM, IWP, VO, IWR ...) and the short list was inverse index ETPs (SOXS, SQQQ, QID, PSQ, SPXS, SPXU, SDS, SH).
The one precursor that recurs on every Move Hunt day scanned (11-05, 11-06, 11-09: top-quintile lift 2.9-4.2× long and
short) is **vol_exp = 5-min ATR / daily ATR ("in play")** — but MH1 (10-29) showed it predicts *size*, not *direction*.
This test takes the direction from the market compass instead of the stock.

**Rule (one configuration, both directions).** At the 10:00 lab bar (entry at its close):
- the W60 15-min compass at the 10:00 mark (research/bdi/hc1/comp15.py logic on research/bdi/hc1/state15.py hist, the
  same build as ECG1) is **UP-confirmed → long**, **DOWN-confirmed → short**; any other reading → no trade;
- the stock is in play: **vol_exp = atrPct / (atr_d / close × 100) ≥ 0.12** (MH1's lower cut);
- the stock is already moving the compass's way: **fromOpen > 0 for longs, < 0 for shorts**;
- adv20 ≥ $95M, close ≥ $5;
- **t1s1** (target and stop 0.25 × daily ATR, 15:55 flatten) = frame outcome `r_long_t1s1` / `r_short_t1s1`, re-costed to
  production costs as MH1106-P1 (entry + exit $0.01 + 1 bp × time-of-day multiplier, + $0.02 stop slippage on losers).

**Base rate:** every other liquid name at the same 10:00 bar on the same days, same side, geometry and costs.
Precision = win share; excess = class avg R − base avg R on the same day.

**Data:** lab frames + context, open months only (locked block 2024-11-01..2025-02-28 never read, asserted).
TRAIN ≤ 2025-12-31, VALID 2026-01-01..2026-11-04.

**Pass (Testing / Live Lab candidate, BAR90).** Lineage MH (MH1 2 + MH1106-P1 1 + this 1) N = 4 → full bar 1.67, BAR90 1.50.
avg R after costs > 0 in TRAIN and VALID; excess day-clustered t ≥ 1.50; positive avg R on SPY up AND down sessions
(open-to-close ±0.25 %); walk-forward positive months ≥ 54 %; avg R without the best day > 0 (share reported, flagged
≥ 50 %); n ≥ 300 on ≥ 30 days. **Light lane (Live Lab):** expectancy ≥ −0.02R in TRAIN and VALID with the excess t ≥ 1.50.
**Reported regardless:** QDAY split by SPY day type (up / down / quiet) and by side; SPY vs its open at 10:00 is fixed by
the compass side (UP → above), reported anyway; 11-09 in-sample check on the live frames.
