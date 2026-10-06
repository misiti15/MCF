# regime: conditioning MarcoFlow's Heat Score on market regime (educational only, not financial advice)

## Question
Does the heat concept work only in certain regimes, such as time of day, gap, distance from the open (fromOpen),
5-minute volatility (atrPct) or relative volume? If so, can a transparent re-weighted heat with at most two regime gates
give viable longs and shorts?

## Method
- All fitting used TRAIN only. I split train into 2 halves for the diagnostics and 4 day-blocks for the searches.
  The search objective was 0.5*min(block exp_r) + 0.5*mean(block exp_r), with per_day >= 25 in every block.
- I used a vectorised replica of `evaluate()` (first qualifying bar per symbol-day, every threshold in one pass).
  It matches evaluate() exactly.
- Diagnostics: per-regime first-bar results of the original heat at +/-30, half by half; per-timestamp-demeaned weekly
  ICs of every component in each regime; ridge fits per tod window, cross-validated half against half.
- Random search: 7 component weights plus fromOpen and gap terms in {-1,-.5,0,.5,1}, plus a cost penalty k in {0,1,2,4,8}.
  This ran over 5 tod windows x 5 second gates (none, fo+, fo-, gap+, gap-) x 2 sides, about 154 weight vectors each,
  so about 7,700 weight vectors, each with 40 quantile thresholds.
- Hand-built "regime heats": original heat, rev4 = rsiHeat+priceActionHeat-momentumHeat-vwapHeat,
  rev6 = rev4-trendHeat-macdHeat, revfo = rev4-fromOpen term, heat+fromOpen term.
  These ran over 7 windows x 5 gates x 4 cost weights x 2 sides, so 1,400 configs x 40 thresholds.
- Total: about 9,500 weight configurations (about 370k config/threshold pairs) on train.
  VALID was used once, on 17 finalists (regime_1..17), plus 4 gate-only reference checks.

## What the regimes show (train)
- **The cost term dominates everything.** Round-trip cost in R = 0.08/atr_d is the most stable predictor in every regime
  (ridge weight -40 to -75 vs <=50 for the best heat term, the same sign in every half and window).
  The original heat ignores it. I added it as a tradability term: -k*100*0.08/atr_d.
- **Time of day flips the sign of the trend terms.** Demeaned weekly ICs (x100, weeks positive out of 8):
  - 09:50-11:00: heat +1.3 (6/8), fromOpen +1.1 (6/8), vwapHeat +1.1 (5/8). Trend-following works a little.
  - 11:05-13:30: vwapHeat -3.5 (2/8), macdHeat -3.0, trendHeat -2.9, momentumHeat -1.4 (1/8). These are strongly mean-reverting.
  - 13:35-15:00: weaker reversion.
- **fromOpen < 0** is the most reverting state: vwapHeat -2.8 (1/8 weeks positive).
- Gap direction, atrPct terciles and volumeRatio regimes did not give stable sign changes for the heat itself.
- The original heat at +/-30 is negative in almost every regime and half, except morning shorts in low-cost names.
  The original-heat morning shorts (regime_11/12/13/15, train +0.12R) went to about 0 on valid.
- Gate-only references: shorting the lowest-cost names 09:50-11:00 with no heat term is already +0.08..+0.16R on train.
  On valid it was ~0..+0.03R. So the train edge of the morning shorts is largely time+cost.
  The heat terms added nothing on train but +0.08..+0.14R on valid (regime_9: +0.131 vs -0.007; regime_14: +0.107 vs +0.026).

## Results (official evaluate(), first bar per symbol-day)
Base success (any bar): long train 0.270 / valid 0.276; short train 0.281 / valid 0.345.

| file | side | score | train n / pd / succ / exp_r / PF | valid n / pd / succ / exp_r / PF | viable |
|---|---|---|---|---|---|
| regime_14 | short | revfo short, fromOpen<0, 09:50-11:00, k=8, T=2.8 | 4700 / 127 / .479 / +0.107 / 1.27 | 1398 / 108 / .496 / **+0.107** / 1.26 | yes |
| regime_9 | short | rev4 short, fromOpen<0, 09:50-10:30, k=8, T=11.3 | 1703 / 46 / .521 / +0.157 / 1.41 | 421 / 32 / .520 / **+0.131** / 1.32 | yes |
| regime_10 | short | rev6 short, fromOpen<0, 09:50-11:00, k=8, T=21.7 | 1560 / 42 / .502 / +0.128 / 1.32 | 383 / 30 / .520 / **+0.100** / 1.23 | yes |
| regime_5 | long | revfo long, gap>0, 11:05-13:30, k=4, T=57.5 | 1586 / 43 / .388 / +0.071 / 1.20 | 356 / 27 / .385 / +0.044 / 1.12 | yes (marginal) |
| regime_3 | long | rev4 long, gap>0, 11:05-13:30, k=2, T=51.5 | 1842 / 50 / .398 / +0.076 / 1.21 | 411 / 32 / .387 / +0.040 / 1.10 | yes (marginal) |
| regime_16 | short | random winner, fo<0, morning | 1620 / .190 | 289 / +0.094 | no (n<300) |
| regime_17 | short | random winner, gap>0, morning | 1700 / .141 | 261 / +0.069 | no (n<300) |
| regime_11/12/13/15 | short | ORIGINAL heat, morning (+gap-), cost | +0.12..+0.13 | -0.02..+0.01 | no |
| regime_1/2/4/6/7/8 | long | midday reversion / morning trend without the gap gate | +0.05..+0.12 | -0.07..-0.22 | no |

## Reading the winners
- **Short (regime_9/10/14): "fade the bounce of a stock that is red on the day, in the first hour."**
  - The stock trades below today's open (fromOpen<0).
  - The flipped heat says it is short-term stretched UP: RSI high (rsiHeat<0), high in its 20-bar range,
    positive momentum, above VWAP (rev6 adds EMA/MACD up).
  - The cost term restricts it to names with a large $ATR.
  - The original heat had these trend terms the other way round. That is why it carried no edge.
- **Long (regime_3/5): "buy the midday dip in a stock that gapped up."**
  - Gap>0, 11:05-13:30.
  - RSI low, low in range, negative momentum, below VWAP (revfo: also below the open).
  - Midday reversion without the gap-up gate failed badly on valid (a falling tape). The gap-up gate kept it positive (+0.04R),
    but this is barely over the +0.03R bar.

## Honest caveats
- Day-clustered SEs are large. Valid has 13 days, and the SE of the daily mean is about 0.08-0.09R for these candidates.
  No valid result is significant at the day level. Treat the test split as the real check.
- 17 finalists on valid: with 5 passes out of 17, some selection luck is likely.
- The cost term (k=8) does much of the work for the shorts, and morning low-cost shorts were positive on train even without heat.
  Valid was a falling tape (short base success 0.345 vs 0.281), which flatters every short.
- Longs: only the gap-up midday dip variants survived, and only marginally.
