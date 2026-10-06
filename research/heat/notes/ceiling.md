# ceiling — how much signal is in the heat ingredients at all? (educational only — not financial advice)

## Method
1. Features: 7 MarcoFlow components + 15 raw indicators + minutes since open + cost in R (0.08/atr_d) + daily ATR % (atr_d/close).
2. Model per side: sklearn HistGradientBoostingRegressor (depth 3, 8 leaves, lr 0.05, 150 iters, min_leaf 3000, l2 5),
   500k-row train samples, target clipped to ±1.5R. Targets: raw R, and R demeaned per timestamp ("xs", removes market direction).
   Feature sets: all / without cost & daily-ATR% / without cost, daily ATR, gap, 5m ATR, time. One run added market-context
   features (cross-sectional median fromOpen/VWAP dist/momentum/gap per bar).
3. Honest train estimate = out-of-fold: fit on train half 1 → predict half 2 and vice versa. Thresholds = OOF quantiles 95-99.9%.
   Final model fit on all train, scored on valid with the same thresholds (valid used as the ceiling read-out, as the task asks).
4. Distillation: linear regression of the full-train GBM prediction on 8 clipped terms (R² 0.52 short / 0.42 long), rounded weights,
   a 45-config train-only grid (3 variants × 3 cost gates × 5 thresholds, ranked by the worse train half), 4 finalists on valid.

Configurations tried: ~115 (GBM ceiling 48, market-context GBM 8, distillation read-outs 16, train grid 45, control 2; finalists 4).
Valid was looked at for the GBM ceiling read-outs (by design), 8 distillation read-outs and the 4 finalists.

## Ceiling results (official evaluate(), first bar per symbol-day)
| model | side | train OOF exp_r (q95..q99) | valid exp_r |
|---|---|---|---|
| xs, all features | long | -0.03 .. -0.02 (PF<1) | -0.11 .. -0.24 |
| xs, no cost/ATR | long | -0.07 .. -0.01 | -0.14 .. -0.24 |
| xs, technical only | long | -0.08 .. +0.04 (q99 only) | -0.07 .. -0.25 |
| raw R | long | -0.07 .. -0.04 | -0.09 .. -0.23 |
| xs, all features | short | -0.005 / +0.017 / +0.020 / -0.014 | +0.05 / +0.08 / +0.07 / +0.10 |
| xs, no cost/ATR | short | -0.04 | -0.01 .. -0.06 |
| xs, technical only | short | -0.08 .. -0.11 | -0.09 .. -0.42 |
| raw + market context | both | concentrates on 1-9 days (day-level bets), train OOF ≤ +0.04 then negative | not trusted |

**Plain answer: the tree model has no out-of-sample long edge at all, and on the short side its train OOF edge
(+0.02R at best) is below the +0.03R bar.** Once cost and daily volatility are removed from the inputs, nothing is left
on either side: the MarcoFlow indicators carry ~no transferable signal at these horizons.

What the short GBM uses (permutation importance on its own prediction): cost_r 1.52 ≫ daily ATR% 0.44 > gap 0.22 >
5m ATR 0.06 > vwapHeat 0.05 > time 0.04 > macdHeat 0.03; every other component < 0.03. The long GBM: daily ATR% 0.73,
cost 0.71, gap 0.28, time 0.12, vwapHeat 0.08 (it learnt "fade big drops in volatile names", which failed on valid: -0.11..-0.24R).

## Distilled heat-style short score (research/heat/candidates/_ceiling_common.py)
`core = 8 − 168·cost_R + 1.9·early − 6.6·clip(atrPct,0,1.5) + 0.9·clip(vwapDistPct,−1.5,2) + 0.2·macdHeat`,
early = clip((120 − minutes since 09:30)/60, 0, 2). Short when core ≥ threshold.

| file | rule | train n / per_day / succ / exp_r / PF | valid n / per_day / succ / exp_r / PF |
|---|---|---|---|
| ceiling_1 | core ≥ 8.16, cost ≤ 0.04R | 3692 / 99.8 / 0.420 / +0.032 (se 0.015) / 1.075 | 971 / 74.7 / 0.504 / +0.151 / 1.40 |
| ceiling_2 | full ≥ 7.23 | 6029 / 162.9 / 0.424 / +0.031 (se 0.012) / 1.072 | 1716 / 132 / 0.506 / +0.157 / 1.42 |
| ceiling_3 | core ≥ 7.69, cost ≤ 0.04R | 5542 / 149.8 / 0.413 / +0.023 / 1.053 | 1517 / 116.7 / 0.500 / +0.143 / 1.37 |
| ceiling_4 (CONTROL, not heat) | 8 − 168·cost + 1.9·early ≥ 9.25 | 10681 / 288.7 / 0.468 / +0.037 / 1.082 | 3160 / 243 / 0.506 / +0.096 / 1.23 |

Base success (any bar): short train 0.281 / valid 0.345; long 0.270 / 0.276.

Share of GBM performance kept: on valid at matched thresholds the distillate is *better* than the GBM (+0.14..0.18R vs
+0.03..0.08R), on train in-sample it keeps ~25% (+0.02..0.03 vs +0.12..0.16 in-sample GBM; the GBM's in-sample figure is
mostly overfit — its OOF figure is +0.02, which the distillate matches).

## Honest reading
* ceiling_1 and ceiling_2 pass every viability number on train and valid, but only just on train (+0.031/+0.032R, <2.5 se).
* The control with **no heat terms at all** (cheap-to-trade names, first two hours) does as well on train. So the "edge" is
  mostly (a) the cost term — selecting high-ATR, high-priced names where $0.02 round trip is a tiny fraction of R — and
  (b) shorting early in the session. The heat terms (VWAP stretch, MACD, calm 5-m ATR) add a little on valid only.
* Success vs base is flattered: success is strongly time-of-day dependent (short success 0.46 in the first 20-50 min vs 0.10 at
  the end), so an early-session score beats the all-bar base mechanically.
* Valid was a weak-market stretch (all-bar mean short R +0.038 vs −0.027 in train): the large valid numbers are mostly market
  drift. ~75-160 correlated shorts per day = one directional bet on the day; green_days 0.54-0.60 on train.
* Long side: nothing — the tree ceiling is negative on valid in every configuration. No long candidate.
