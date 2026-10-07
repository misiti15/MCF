# MarcoFlow rule stacks, re-scored on the setup lab (key: marcoflow)

*Educational only — not financial advice. Backtest (lab) results only; nothing here is tested live.*

## Failures first
- **MarcoFlow's ranking does not predict MCF outcomes.** Corr(best Wilson LB, lab exp_r) = −0.02 on train, +0.05 on valid (4,743 recommended stack×side×geom configs with valid n ≥ 30).
- **Most mined stacks lose after MCF fills and costs.** Recommended stacks: 82% negative on train, 65% negative on valid (mean −0.055R / −0.032R; median valid at production cost −0.091R). MarcoFlow's own "avoid" stacks are worse (mean −0.076R / −0.058R), so the sign of its ranking holds weakly but the level does not.
- **Every long stack fails.** Only 11% of long configs are positive on train and 15% on valid. The long random baseline is −0.062R on train and −0.105R on valid (t1s1).
- **All 20 stacks MarcoFlow paper-traded (clean window, 8/28+) fail the gate in the lab.** Examples: heat-50+rsi-mid-high (paper −$598) long −0.08R/−0.14R; reg-neutral+flow-sell+rsi5-low (paper −$504) long −0.10R/−0.09R. open-first15+… cannot be scored at all because the lab frame starts at 09:50.
- **Multiple testing.** 7,014 stack configs; 5,358 have valid n ≥ 30. Of these, 211 (3.9%) reach valid day-t ≥ 1.5 and 1,403 reach day-t ≤ −1.5. The passer count is **below** what chance alone would give at zero mean (about 7%), so the finalists below are consistent with selection noise. Train day-t for every finalist is between 0.03 and 1.10; no finalist is significant on train.
- **At production cost, the finalists lose on train.** 15 of 16 finalists have negative train expectancy at production cost (−0.064R to −0.003R). The exception is MF-open-rsimidhi-flowsell (+0.041R, n 119). Train ex-best-day is negative for 10 of 16. So the "edge" is the valid window (8/26–9/15, 14 sessions), which may simply have suited shorts that faded strength.
- **MF-open-rsiob-flowsell is already flat on valid at production cost** (+0.002R).
- **Regime and asset layers can't be deployed.** mask(df) sees one symbol and no SPY. reg-* uses a proxy (SPY prior close vs 20-session mean and change), not MarcoFlow's SMA50 rule. reg-bull+flow-sell+rsi5-high short (valid +0.177R, t 12.9) rests on **3 valid days**, so it is not a finalist.

## What survived (16 distinct deployable masks, all SHORT)
The gate: train > 0, valid > 0, valid n ≥ 30, valid day-t ≥ 1.5, beats the same-side same-window random baseline, and plateau mean > 0 on both train and valid. The plateau covers each threshold ±1 step and a heat floor of 25 or 35 (338 neighbour configs).

Every survivor is one family: **a bearish heat signal (heat ≤ −30) with net selling flow (buyPressure < −0.25) while price is still extended** (above VWAP, RSI(5) > 70 or RSI(14) > 65), mostly in **09:50–11:00 ET**.

This is a "sellers distributing into strength" pattern. It runs against MarcoFlow's own "short the drop" lesson. The masks overlap heavily, so treat them as one idea with variants, not 16 independent edges. The full table is in `results.csv` (`finalist` column); the modules are `MF-*.py`, verified against `setup_lab.evaluate` in `finalists_verify.json`.

## Ingredients (single MarcoFlow layers, `ingredients.csv`)
No single layer is significant on train (|t| < 1.5 everywhere). These layers beat the window baseline on both splits for shorts and are worth layering:
- buyPressure < −0.25 / < −0.15 (flow-sell / flow-aligned)
- vwapDistPct > 0 (fade above VWAP)
- RSI(5) > 70
- RSI(14) slope < −1 (mom-aligned)
- the 09:50–11:00 window
- the heat ≤ −30 base
- rsi-diverge-bear (RSI(14) > 65 and RSI(5) < 60)

Long-side layers: none.

## Files
| File | What it holds |
|---|---|
| extract.py | 1,271 stacks from 84 StrategyReview runs, written to stacks.json |
| conds.py | the layer catalog mapped to lab columns, with mapping gaps documented |
| score.py | scores every stack and writes results.csv, ingredients.csv, plateau.csv and counts.json |
| make_modules.py | writes the MF-*.py modules and verifies them |

Configurations counted: 7,014 stack configs, 660 single-layer ingredient configs and 338 plateau neighbours, **8,012 in total**.

Production cost in `*_exp_r_prod` = lab r − (2 bps × price + 2c on stop fills) / R. The 3c extended-tier surcharge is not applied.
