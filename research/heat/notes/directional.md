# directional — re-weighting MarcoFlow's Heat Score (educational only — not financial advice)

## Approach
1. Train-only decile diagnostics for every component and raw indicator, for each side (scratch scripts, not committed).
2. Main finding: gross R(long) = -gross R(short) for each bar (exits are symmetric ±1R). So any edge has two parts:
   (a) cost: round-trip cost in R = 0.08 / atr_d. This is the biggest single "feature" (median 0.023R, top decile 0.18R),
   (b) a cross-sectional prediction of the bar's direction. Day-level market direction swamps everything (std of the daily mean R is 0.14).
3. Per-timestamp-demeaned ICs (8 train weeks): the only signs that held up week after week were **fade the downside stretch**:
   vwapDistPct_neg +0.029 (8/8 weeks +), macdPct_neg +0.028 (7/8), emaDiff_neg +0.026 (7/8), momentum_neg (7/8).
   Overall the momentum/trend/MACD/VWAP terms act as **mean reversion** at 5-min/≤6h horizons. MarcoFlow scored them
   trend-following, while RSI and price position were contrarian, so the original terms cancel → no edge. Volume terms ≈ no signal.
4. Built a "stretch heat" per side = VWAP-dist/0.6 + MACD%/0.35 + EMA9-21%/0.3 + momentum/0.5 (each clipped to [0,3]% in the fade direction),
   plus a time-of-day window term and a cost term (-100 outside). I grid-searched 4 weightings × 6 windows × 3 cost caps × 6 thresholds per side (864),
   and ranked configs by the worse of the two train halves (07-08..08-07 vs 08-10..08-27).
5. 12 finalists were scored on valid.

Configurations tried in total: ~950 (≈80 ridge/sweep exploratory + 864 grid + 12 finalists on valid).

## Results (official evaluate(), first bar per symbol-day)
| file | side | train n / exp_r / PF / succ | valid n / exp_r / PF / succ |
|---|---|---|---|
| directional_1..5 | long, oversold fade 11:00-13/14:00 | 1.6-2.0k / +0.06..+0.08 / 1.15-1.21 / 0.40-0.41 | 380-510 / **-0.03..-0.09** / <1 |
| directional_6 | short eq 13:00-14:30 c≤.05 th10 | 690 / +0.120 / 1.43 / 0.31 | 161 / +0.091 / 1.25 / 0.40 (n<300) |
| directional_8 | short vw 13:00-14:30 th12 | 900 / +0.105 / 1.37 / 0.29 | 206 / +0.120 / 1.36 (n<300) |
| directional_10 | short eq_rsi th12 | 897 / +0.098 / 1.35 / 0.29 | 201 / +0.129 / 1.38 (n<300) |
| **directional_11** | **short eq 13:00-14:30 c≤.05 th8** | **1308 / +0.071 / 1.23 / 0.283 (35/day)** | **306 / +0.159 / 1.50 / 0.42 (24/day)** |
| directional_12 | short tr 10:30-15:00 c≤.02 th8 | 4116 / +0.047 / 1.12 / 0.40 | 894 / -0.049 / 0.90 |

Base success (any bar): short train 0.281, valid 0.345 (13:00-14:30 window: 0.184 / 0.281); long train 0.270, valid 0.276.

## Honest verdict
* **Longs: none viable.** The dip-buy (fade-the-drop) edge was real on train but negative on valid (a down tape: baseline long -0.12R).
  It looks regime-dependent (works when the market bounces). Still better than the original heat on valid (-0.03..-0.09 vs -0.12).
* **Shorts: one candidate passes all thresholds on train and valid: directional_11** (fade a stock stretched UP vs VWAP/EMA/MACD/momentum,
  in the 13:00-14:30 ET window, only names where cost ≤ 0.05R). Caveats: train success 0.283 is barely above the 0.281 base (it is far above
  the window base, 0.18). Valid n=306 is just over the bar. Valid was a falling market that favours any short, and the sample is
  37+13 days, so SE clustered by day is larger than exp_r_se suggests. Treat it as a hypothesis for the locked test, not an edge.
* Lesson: the heat concept carries a signal only when its trend terms are flipped to **contrarian (fade the stretch)**, gated by time of day and cost.
  The volume terms add nothing.
