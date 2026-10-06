# reweight: re-weighting MarcoFlow's 7 heat components

*Educational only, not financial advice.*

## What was searched
- score = sum(w_k * component_k) + w_bonus * alignment_bonus + w_tod * hours_since_09:50, with separate long and short scores and thresholds.
- Weights ran from -1 to 1 (tod from -10 to 10 per hour), with random sparsity, fixed seeds (1-4). Each config got a full threshold sweep (100-120 quantile thresholds, top 15-20%). Stats come from an exact vectorised replica of `evaluate()` (first qualifying bar per symbol-day; matches evaluate() to 4 dp).
- Robust objective on TRAIN ONLY. Round 1: min exp_r over the two train halves, with per_day 25-200 in each. Round 2: 0.5*min + 0.5*mean over 4 train day-blocks, with per_day 40-250. Then coordinate descent from the top random configs.
- About 4,000 random configs plus about 3,000 coordinate-descent steps, each with about 110 thresholds. That makes about 7,000 weight vectors, or about 800k (weights, threshold) pairs. 64 single-component sweeps came first.
- VALID was used only on 14 finalists (5+2 long, 5+2 short).

## Findings
- **Single components:** none has a stand-alone edge. The best univariate configs only "win" by entering every symbol at the 09:50 bar (market beta).
- **Longs: no viable long.** Every train-optimised long (train exp_r +0.08 to +0.16R) failed on valid (-0.07 to -0.32R). The valid window was a falling tape (any-bar r_long -0.137R), and no re-weighting of the components overcame it. The long fits are overfit to the train regime.
- **Shorts: a consistent, modest edge.** All the robust short fits share one shape:
  - +w on volumeHeat: low relative volume pushes toward a short.
  - +w on rsiHeat: high RSI/overbought pushes toward a short.
  - +w on momentumHeat and trendHeat: weak momentum or downtrend.
  - A small negative weight on priceActionHeat.
  - The alignment bonus near 0. **Dropping the bonus costs nothing**: the fitted w_bonus was 0 to 0.1, and the -0.38 in reweight_2 is the only exception.
  - A positive tod weight, so shorts trigger mostly early in the session.
- 4 of the 7 short finalists passed every viability rule on valid. The edge is small relative to noise: valid SE is about 0.035R and valid has only 13 days.
- **Caveat:** part of the short edge may be regime (the valid tape fell; short base +0.038R any-bar). Shorting every symbol at the 09:50 bar gives about -0.02R on train and +0.01 to +0.03R on valid. The candidates beat that on both splits, but by a margin the test split must confirm.

| file | side | train exp_r / n / pd / PF / succ | valid exp_r / n / pd / PF / succ |
|---|---|---|---|
| reweight_1 | short | +0.131 / 2478 / 67 / 1.33 / 0.528 | +0.066 / 720 / 55 / 1.15 / 0.529 |
| reweight_2 | short | +0.079 / 3982 / 108 / 1.20 / 0.471 | +0.046 / 935 / 72 / 1.11 / 0.487 |
| reweight_3 | short | +0.091 / 2132 / 58 / 1.22 / 0.518 | +0.046 / 659 / 51 / 1.10 / 0.534 |
| reweight_4 | long (NOT viable) | +0.075 / 2589 / 70 / 1.21 / 0.390 | -0.067 / 594 / 46 / 0.83 / 0.298 |

Base success rates: train long 0.270, short 0.281; valid long 0.276, short 0.345.
