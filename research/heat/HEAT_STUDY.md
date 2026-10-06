# MarcoFlow heat score: re-weighting study (2026-10-06)

*Educational only — not financial advice.*

## Setup
- **Formula:** MarcoFlow's heat score (`lib/heat-tracker.ts`), ported to `mcf/research/heat.py` and recomputed on SIP 5-minute bars. MarcoFlow's own stored signals were not used, because they only kept |heat| ≥ 30.
- **Data:** 1,000 most liquid names, 63 sessions, 3.96M decision bars (09:50–15:00 ET).
- **Outcome:** +1R before −1R with R = 0.25 × daily ATR, measured after costs, first entry per symbol-day.
- **Splits by date:**

  | Split | Dates | How it was used |
  |---|---|---|
  | Train | Jul 8 – Aug 27 | fitting |
  | Valid | Aug 28 – Sep 16 | choosing finalists |
  | Test | Sep 17 – Oct 5 | locked; scored once, after the audit, on all 49 candidates |

- **Swarm:** five tuners took different approaches (component re-weighting, per-ingredient diagnosis, regularised linear models, regime conditioning, a gradient-boosting ceiling). Together they tried about 19,200 configurations. An auditor then re-ran every candidate and compared it against same-timestamp, cost-matched controls.

## Findings
1. **The original heat has no edge.** At ±30 it scores −0.044R long and −0.077R short on test, and it is negative on train too.
2. **Why:** MarcoFlow scored momentum, trend, MACD and VWAP as trend-following and RSI and price position as contrarian. At this horizon, all of them behave as mean reversion. The two halves cancel out.
3. **No long edge was found in general.** Every train-optimised long failed on valid.
4. **What survived:** the concept rewritten as a *consistent* reversion score, then gated by time of day and by a cost term in R.

| Candidate | Side | Rule | Train | Valid | Test (locked) | Audit |
|---|---|---|---|---|---|---|
| regime_9 | short | 09:50–10:30, stock below its open, fade the stretched-up bounce | +0.157R | +0.131R | **+0.046R** (n 626, PF 1.10) | keep |
| regime_14 | short | same family, wider window | +0.107R | +0.107R | +0.020R (n 1,849) | keep |
| regime_5 | long | 11:05–13:30, gap-up name stretched down, buy the reversion | +0.071R | +0.044R | **+0.159R** (n 533, PF 1.47) | doubtful (marginal on valid) |
| regime_3 | long | similar long | +0.076R | +0.040R | +0.150R | doubtful |
| reweight_1 | short | best plain re-weight | +0.131R | +0.066R | −0.040R | doubtful → failed |
| linear_model_9 | short | ridge model | +0.054R | +0.051R | −0.041R | reject → failed |

The market was different in each window. Valid fell, which flatters shorts. Test rose: a random short bar averaged −0.083R and a random long −0.012R. The survivors beat those baselines in both windows. The edge is still small: test standard errors are about 0.04R, and every window is a few weeks of one regime.

## Decision
- `heat_fade_short` (regime_9) and `heat_fade_long` (regime_5) **paper-trade only**, in the study's population: names with $125M+ ADV, in the windows above.
- They reach funds only through the promotion gates: 200+ trades over 6+ months out of sample.

Files:
- `candidates/` — every candidate
- `notes/` — each tuner's notes
- `test_results.csv` — train, valid and test for every candidate

## Live-code-path check
`HeatStrategy`, the code that trades live, was run through the 1-minute backtester. Fills were conservative: stops and targets resolved on 1-minute bars, plus slippage. The period was the test window, Sep 17 – Oct 5, on 1,226 symbols:
- heat_fade_long: 616 trades, success 44.6%, win rate 57.6%, **+0.128R**, PF 1.36, green days 69%. The lab measured +0.159R.
- heat_fade_short: 720 trades, success 46.1%, win rate 52.4%, **+0.040R**, PF 1.05, green days 77%. The lab measured +0.046R.

The deployed code reproduces the study.
