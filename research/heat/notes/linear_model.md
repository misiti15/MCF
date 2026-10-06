# linear_model — statistically re-weighted Heat Score (educational only — not financial advice)

## Method (fit on TRAIN only; valid used once, on 11 finalists)
1. Inputs: MarcoFlow's raw heat indicators (+ log volume ratios), split into positive/negative parts for the signed
   "stretch" terms (vwapDistPct, macdPct, emaDiff, momentum, fromOpen, gap), absolute values, the 7 original components,
   cost in R (0.08/atr_d), daily ATR % and time-of-day buckets. Winsorised at 0.5/99.5% of train, standardised (train mean/std).
2. Models: ridge on r_long / r_short, Lasso, logistic (L1/L2) on succ_*, and ridge on the per-timestamp-demeaned R
   (cross-sectional target, removes the market's direction). Stability was judged by fit-on-half / test-on-other-half and
   leave-one-train-quarter-out CV — never by valid.
3. Total configurations tried ≈ 1,640 (≈90 aborted first run + 288 + 384 + 384 (LOQO) + 72 (LOQO, abs features) + 179 + 125 + 105 grids + 11 finalists on valid).

## What the fits say (train)
* Univariate ICs: cost (−0.07 long / −0.08 short) is the strongest single feature. Next: **downside stretch is mean-reverting**
  (vwapDistPct_neg IC +0.040 on r_long, −0.032 on r_short; macdPct_neg +0.030; emaDiff_neg +0.026). Upside stretch carries
  almost nothing (vwapDistPct_pos +0.006 on r_short). Volume terms ≈ 0. MarcoFlow scores the trend terms trend-following → they
  cancel its contrarian RSI/price-position terms.
* Full-feature ridge/logistic on raw R: in-sample top-1% ≈ +0.02..+0.05R, but **out-of-half ≈ −0.05..−0.27R**. Coefficients flip
  sign between train quarters (heavy collinearity: momentum vs momentumHeat, emaDiff vs trendHeat). Logistic on success is worse
  (it picks low-variance names). Components-only models: no out-of-fold edge on either side.
* Cross-sectional ridge on stretch parts (alpha 1e5, cost ≤ 0.05R): the long tail (top 0.5%) had positive out-of-fold excess R
  in 4/4 train quarters (+0.04..+0.17R), giving the "fade-the-drop" weights (10 pts = 1 sd):
  `+7.2·vwapDist_neg +5.3·macd_neg −3.0·macd_pos +2.9·mom_pos −1.1·mom_neg +2.5·fromOpen_pos +1.4·ema_pos −0.9·ema_neg +0.3·vwapDist_pos`
  i.e. "well below VWAP with negative MACD, but short-term momentum already turning up".
* Short side: no robust cross-sectional signal. Out-of-fold excess for "fade the up-stretch" was negative in most folds.
  A "short the quiet gappers" (absolute-stretch) model had positive OOF excess but its success (0.24) is below the short base (0.28)
  — it only works because calm names rarely hit −1R. Not used.

## Finalists (official evaluate(); train → valid)
| file | side | train n / per_day / exp_r / PF / succ | valid n / exp_r / PF / succ |
|---|---|---|---|
| linear_model_1 | long, all day, cost≤.05, ≥45 | 1131 / 31 / +0.081 / 1.20 / 0.449 | 196 / −0.141 / 0.72 / 0.332 |
| linear_model_2 | long, 11–14h, ≥45 | 803 / 22 / +0.078 / 1.21 / 0.406 | 136 / −0.094 / 0.80 |
| linear_model_3 | long + abs terms, ≥45 | 986 / 27 / +0.070 / 1.17 / 0.442 | 140 / −0.136 / 0.71 |
| linear_model_4 | long, 11–14h, ≥30 | 1915 / 52 / +0.049 / 1.13 / 0.390 | 437 / −0.095 / 0.79 |
| linear_model_5 | long, 10–15h, ≥50 | 792 / 21 / +0.112 / 1.29 / 0.468 | 120 / −0.126 / 0.74 |
| linear_model_6 | long + abs, 10:30–14:30, ≥45 | 875 / 24 / +0.125 / 1.35 / 0.449 | 117 / −0.096 / 0.78 |
| linear_model_7 | long, 13–14:30, cost≤.03, ≥35 | 546 / 15 / +0.185 / 1.74 / 0.359 | 106 / −0.200 / 0.54 |
| linear_model_8 | long, ≥60 | 335 / 9 / +0.139 / 1.40 / 0.454 | 37 / +0.032 / 1.08 (n too small) |
| linear_model_9 | short (mirror ≤ −6), 10–15h, cost≤.015 | 11060 / 299 / +0.054 / 1.14 / 0.368 | 3325 / +0.052 / 1.13 / 0.384 |
| linear_model_10 | short (mirror ≤ −7), all day, cost≤.02 | 12498 / 338 / +0.047 / 1.13 / 0.366 | 3905 / +0.038 / 1.10 / 0.376 |
| linear_model_11 | short (mirror ≤ −8), cost≤.02 | 9551 / 258 / +0.030 / 1.08 / 0.332 | 2804 / +0.012 / 1.03 |
Base success: long 0.270 train / 0.276 valid; short 0.281 / 0.345.

## Honest verdict
* **Longs: none viable.** The fade-the-drop weights held across all four train quarters but lost on valid (down tape; long
  baseline −0.12R). Excess vs other eligible names at the same timestamp also turned negative on valid (−0.08R ± 0.06).
* **Shorts: linear_model_9 and _10 pass the numeric viability bar on train and valid, but the heat score is not the reason.**
  A no-signal reference — short every name with cost ≤ 0.015R at its first bar from 10:00 — scores +0.073R (train) and +0.068R
  (valid), better than the candidates. The candidates' excess vs eligible names at the same timestamp is +0.023R on train and
  ~0 (−0.00 / −0.01 ± 0.015) on valid. Their result comes from the cost gate (expensive-per-share, liquid names) plus a
  market-direction drift that favoured shorts in both periods. Treat them as "cost-gated market shorts", not a heat edge;
  they would be expected to lose in a rising tape.
* Lesson: once costs and market direction are taken out, a linear re-weighting of the heat inputs has at most a weak, unstable
  cross-sectional signal (mean reversion of downside stretch). Train has only 37 sessions, so the day-level market factor
  dominates every per-side result.
