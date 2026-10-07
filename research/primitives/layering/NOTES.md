# Layering stage: L2 pairs and L3 triples (key: `layering`)

*Educational only - not financial advice.* These are backtest results on the setup-lab frame, using train (06-30 to 08-25, 40 sessions) and valid (08-26 to 09-15, 14 sessions). Nothing dated on or after 2026-09-16 was read. Nothing here has been tested live or scored on a locked holdout.

Costs:
- Every number includes the lab cost of 1c per share per side.
- `prod` subtracts an approximate production surcharge: +1 bps per side and +2c on stop exits. The 3c extended-tier surcharge is **not** modelled, so the auditor restates these numbers exactly.

## What was run (rules fixed before the run, in `layer.py`)
- **Atoms:**
  - Every SHORT layer-1 survivor from the primitives stage, used in its own window. There are 90 metric/band/window cells.
  - The 9 MarcoFlow ingredient layers: heat <= -30 or -40, buyPressure < -0.25 or -0.15, vwapDistPct > 0.05, RSI5 > 70, RSI14 > 65, rsiSlope < -1, and the bearish RSI divergence.
  - The 5 short escalation X composites, each in its own window. Each one is paired with one extra atom.
- **Pairs:** two atoms with different columns, short side, all 3 exit geometries. Pairs are evaluated in each window where both atoms can live: W1, W2, W3, W4, W5, plus WO (09:50-11:00) and WALL (09:50-15:00) for the MarcoFlow layers.
- **Keep rule (the "real margin"):** the pair's train exp_r minus the better single layer's train exp_r must be at least max(0.03R, 0.5 x the pair's train day-clustered SE), **and** the pair's valid exp_r must be at least the better single layer's valid exp_r.
- **Finalist gate:**
  - train > 0, valid > 0, valid n >= 30, valid day-t >= 1.5;
  - plateau mean > 0 on both train and valid, where the plateau is every one-step neighbour band or threshold of each atom with the other atoms held fixed;
  - beats the same-side, same-window random baseline on both train and valid.
- **L3:** take the 25 best kept-and-gated pairs per window, ranked by min(train t, valid t), and add one more atom from the same pool. The same rules apply, except the "single layers" are replaced by the three sub-pairs AB, AC and BC.
- **Selection (`select.py`, rule fixed in advance):**
  - The gate must pass, both train halves must be > 0, valid ex-best-day must be > 0, valid day-t at prod cost must be >= 1.5, and there must be at least 8 valid days.
  - Rank by min(train t, valid t).
  - Keep a setup greedily only if its train+valid symbol-day trade set has Jaccard overlap <= 0.5 with every setup already kept. Stop at 8.

## Configurations tried: 11,178 (this stage)
| stage | configurations |
|---|---|
| singles | 1,350 |
| pairs | 6,237 |
| pair plateau neighbours | 496 |
| triples | 1,732 |
| triple plateau neighbours | 487 |
| X + atom pairs | 876 |

Pass counts:
- 685 configurations passed the keep rule and 244 passed the full gate (150 L2, 94 L3).
- 90 of those also passed the selection filters.

**Lineage total:**
- 11,178 here
- 12,030 from primitives
- 243,027 from escalation
- 8,012 from marcoflow

That is **274,247 configurations**.

## Failures first
- **This is one idea, not eight.** All 8 selected finalists, and the top 30 of the 90 filtered candidates, are W4 (13:00-14:30) shorts. Each one is "a name that gapped down or sits below the prior-day low, and has since bounced up into the early afternoon".
  - The Jaccard <= 0.5 dedupe removes near-copies, but the 8 finalists still share most of their days and are strongly correlated.
  - Treat them as variants of one setup family and run at most 1-2 live.
- **Valid samples are small.** Valid n ranges from 33 to 198, on 8-14 days. The best L3 has 41 valid trades on 11 days. Valid day-t of 3-6 on 11 days is fragile.
- **Train t is inflated by selection.** Train t of 3-4 was chosen out of 11k correlated looks. The train numbers for the finalists are therefore optimistic. The valid numbers are the less-biased read, and only the locked holdouts can confirm them.
- **The 3-layer plateaus are thin.**
  - `L3-gapV1+sma20slopepctD10+distlodatrV19` has a worst valid neighbour of +0.0003R.
  - Several W1 triples that passed the gate have a worst neighbour of -1.1R. They pass only on the plateau mean, and they are not selected.
- **No long setup.** Long atoms were not layered, because the primitives stage found no long survivors. X-bottom-div is long, so it is excluded.
- **WO, WALL and the MarcoFlow-only stacks:**
  - Only 4 WO configurations passed the gate, and none reached the selection.
  - The MarcoFlow ingredients only add value as a third layer on W4 (RSI5 > 70, RSI14 > 65, rsiSlope < -1).
- **X composites + one atom:** 1 gate passer (Xfailbo), not selected. Adding a layer to an already 5-8-layer X setup mostly shrinks the sample without a real train margin.
- **The window is not a plateau on the early side.** Starting the window at 12:30 instead of 13:00 lowers every finalist (for example, the top L2 goes from 0.214 to 0.095 on train). Starting at 13:30 or ending at 14:00/15:00 holds. This matches the primitives finding that the gap-down short fails in W3.
- **The 2nd-best W1 family was not selected** because the 8 slots went to W4 by rank. Its best member is `L3-flowsell+momentumD4+rsiD7-short-W1-t1s1`: train +0.169R (t 2.53), valid +0.289R (t 4.70, n 118), prod +0.234R, worst neighbour +0.047.
  - It is the only W1 triple with a positive worst neighbour and a large valid n.
  - If a non-W4 setup is wanted for diversity, it is the next candidate.

## What the layering found
- The primitives NOTES guessed that gap-downs which bounce into the afternoon fail as shorts. **The data says the opposite.**
  - Adding a bounce layer to the gap-down short fixes train half 2. Gap V1 alone is -0.02 to -0.07R in train half 2. The layered versions are +0.09 to +0.24R.
  - The bounce layers that work are: 5-min SMA20 slope in the top 10% or 5%, fromOpen +1.3 to +2.3%, more than 0.9% above VWAP, more than 0.78 ATR off the low, or RSI hot.
- In plain words: **short a gap-down name at 13:00-14:30 after it has rallied hard off its low, because the rally tends to fail.**
- Every finalist beats the time-of-day matched control: its edge over the mean of all names at the same bar is +0.10 to +0.31R on both splits.

## Finalists (8; lab costs; prod = approx production cost; plateau = neighbour mean, with the valid minimum in brackets)
| tag | geom | rule (13:00-14:30 ET bar close, short) | train exp (t, n, days) | valid exp (t, n, days) | valid prod (t) | ex-best | green | plateau tr / va (min) | margin vs parents (train) | edge vs tod (va) |
|---|---|---|---|---|---|---|---|---|---|---|
| L3-gapV1+sma20slopepctV20+rsi5hi-short-W4-t05s1 | t05s1 | gap <= -2.657%; sma20_slope_pct > 0.596; RSI5 > 70 | +0.244 (4.08, 402, 33) | +0.276 (5.53, 41, 11) | +0.262 (5.11) | +0.281 | 0.82 | +0.202 / +0.165 (+0.051) | +0.037 | +0.229 |
| L3-fromOpenD9+gapV1+vwapDistPctD10-short-W4-t1s1 | t1s1 | gap <= -2.657%; 1.30 < fromOpen <= 2.30%; vwapDistPct > 0.893% | +0.331 (3.70, 220, 33) | +0.412 (3.96, 78, 12) | +0.394 (3.76) | +0.560 | 0.83 | +0.205 / +0.375 (+0.207) | +0.167 | +0.262 |
| L3-distpdlatrV2+vwapDistPctD10+momfall-short-W4-t05s1 | t05s1 | -0.607 < dist_pdl_atr <= -0.359; vwapDistPct > 0.893%; rsiSlope < -1 | +0.224 (3.54, 197, 30) | +0.307 (6.62, 54, 8) | +0.288 (5.94) | +0.219 | 0.75 | +0.138 / +0.283 (+0.205) | +0.037 | +0.243 |
| L3-fromOpenD9+gapV1+rsiob-short-W4-t1s1 | t1s1 | gap <= -2.657%; 1.30 < fromOpen <= 2.30%; RSI14 > 65 | +0.273 (3.03, 194, 33) | +0.382 (3.13, 97, 14) | +0.362 (2.92) | +0.389 | 0.64 | +0.207 / +0.297 (+0.109) | +0.109 | +0.244 |
| L3-gapV1+sma20slopepctD10+distlodatrV19-short-W4-t1s1 | t1s1 | gap <= -2.657%; sma20_slope_pct > 0.372; 0.782 < dist_lod_atr <= 0.976 | +0.331 (3.01, 175, 24) | +0.381 (3.36, 33, 11) | +0.357 (3.07) | +0.330 | 0.82 | +0.245 / +0.175 (+0.000) | +0.118 | +0.270 |
| L2-gapV1+sma20slopepctD10-short-W4-t1s1 | t1s1 | gap <= -2.657%; sma20_slope_pct > 0.372 | +0.214 (2.97, 887, 40) | +0.254 (2.98, 137, 13) | +0.231 (2.65) | +0.158 | 0.62 | +0.074 / +0.292 (+0.268) | +0.099 | +0.120 |
| L2-fromOpenD9+gapV1-short-W4-t05s1 | t05s1 | gap <= -2.657%; 1.30 < fromOpen <= 2.30% | +0.137 (2.91, 463, 39) | +0.179 (2.70, 198, 14) | +0.160 (2.37) | +0.123 | 0.64 | +0.076 / +0.112 (+0.030) | +0.041 | +0.102 |
| L3-gapV1+sma20slopepctD10+fromOpenV20-short-W4-t1s1 | t1s1 | gap <= -2.657%; sma20_slope_pct > 0.372; fromOpen > 3.46% | +0.265 (2.65, 373, 37) | +0.311 (3.34, 60, 13) | +0.292 (3.09) | +0.155 | 0.54 | +0.207 / +0.203 (+0.148) | +0.051 | +0.158 |

Random baselines (same side and window, every bar): train -0.043R (t1s1) / -0.046R (t05s1); valid +0.029R / +0.002R.

Each module (`finalists/<tag>.py`) was re-scored through `mcf.research.setup_lab.evaluate` and reproduces n and exp_r exactly (`finalists.json` -> `verify`). The modules carry SIDE, GEOM, LAYERS and mask(df), so they can be deployed through the existing `type: lab` strategy once the lead has scored them on the locked holdouts and they have gone through the backlog and ledger.

## Files
- `layer.py`: the full L2/L3 search. It takes about 40 s and about 1.5 GB. It writes `results.csv` (every configuration) and `counts.json`.
- `select.py`: applies the selection rule, writes the modules, checks window-shift robustness and the tod-matched edge, verifies the modules through setup_lab, and writes `finalists.json`.
- `run.log`: the run log.

Run from the repo root: `python research/primitives/layering/layer.py && python research/primitives/layering/select.py`
