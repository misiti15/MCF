# rdt1030 / F4 irl-erl: results

*Educational only — not financial advice.*

**Verdict: no row passes. 24 configs scored:** 17 candidate rows, 1 parity row and 6 rework rows from a dated amendment
in PLAN.md. **No finalist, so no mask module.**

This is the Reddit post's "IRL -> ERL" idea:
1. Price sweeps a liquidity level (the prior-day low or the 09:30-09:45 range low, or the mirror highs for shorts).
2. A large 15-minute displacement candle follows.
3. The first 15-minute fair value gap after the sweep is the entry.
4. The stop goes beyond the sweep extreme, and the target is the nearest liquidity (prior-day high or the pre-sweep session
   high), else 2R.

On our stocks it has **no edge over a random-symbol control**: the edge versus the control is between -0.05 and +0.02R on
every row. The result depends entirely on market direction:
- longs make +0.08 to +0.16R on SPY up days and lose 0.16 to 0.33R on down days
- shorts are the mirror

The stops under the sweep low are wide (median R about 0.6 ATR_d), so **about 80% of trades simply ride to the 15:55
flatten**. The liquidity target is rarely reached (4-7% of exits).

## Harness
- **Frames and splits:**
  - Frames come from `scan_1019.build_paths`: 0935-0945 head rows, 0950-1500 frame rows and tail rows to 15:55.
  - The `_cut` monkeypatches and asserts are copied from pdl1030/combo. Nothing from the locked block or the HOLD months was loaded.
  - 348 sessions in total: TRAIN 2024-10 and 2025-03..12, VALID 2026-01..03 and 2026-07..09-15.
- **Parity (F4-18):** CWT14 p05 long with the unpatched `scan_1028.sim` gives TRAIN -0.0677 and VALID -0.0675 (n = 53,326),
  an **exact** match (`parity.json`).
- **Sim check:** the patched copy (`build.py:sim`) with its patches off equals `scan_1028.sim` exactly. Max |diff| was
  0.0 on 20,000 trades (`python build.py check`).
- **Patches (DESIGN 0.2):**
  - per-trade R and target multiple (cap 4R)
  - 1c + 1 bp entry × the ToD multiplier
  - 1c + 1 bp on every exit including targets, +2c on stop exits, ×3 on the extended tier
  - gap-through stops fill at min(stop, high) for a long and max(stop, low) for a short
  - limit-fill entry price, with the fill bar checked for the stop only
- **Random control:** 5 random other universe symbols at the same entry row (the fill row for retrace rows, entered at
  that row's close), seed 20261030, with the same side, R in ATR units, target multiple and BE.
- **Base-row sanity check** (2025-06, signal features only, run before any R was read):

  | row | trades/session | median R/ATR | median cost/R | median entry |
  |---|---|---|---|---|
  | F4-01 | 19.4 | 0.65 | 0.030 | 10:45 |
  | F4-05 | 35.3 | 0.58 | 0.033 | 11:00 |
  | F4-09 | 18.4 | 0.57 | 0.034 | 11:00 |
  | F4-12 | 29.7 | 0.50 | 0.041 | 11:15 |

  Costs are small here (about 3% of R, against 11% in F1) because the stops are wide. **This setup's problem is gross
  edge, not costs.**
- **"First FVG" is literal.** The first 15-minute FVG (gap >= g ATR) after the sweep, within 8 HTF bars, is the only
  candidate. If it fails the displacement, close-back, no-new-low or 10:15-14:00 window check, that side is done for the day.

## Bar
- N = 2,000 + 108 (the swarm) + 6 (F1 rework) + 6 (F4 rework) = **2,120**, so t_req = **3.52**. The lead adds other
  families' rework rows.
- A pass needs all of the following:
  - t_day >= 3.52
  - WF >= 54%
  - avg R > 0 on TRAIN and on VALID
  - >= 3 trades per session
  - R > 0 on up days and on down days
  - R above the control

## Results (every column: results.csv)
| id | name | n | tr/sess | TRAIN | VALID | all | t_day | WF% | win% | avgW/avgL R | up-day | down-day | w/o best day | control | 15:55 exits |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F4-01-L | Prior-Day-Low Sweep then 15-min Gap (to liquidity), Long | 6,498 | 18.7 | -0.042 | -0.014 | -0.031 | -1.18 | 50 | 49.2 | 0.51/0.55 | +0.099 | -0.183 | -0.038 | -0.030 | 81% |
| F4-02-L | ... (2R), Long | 6,498 | 18.7 | -0.044 | -0.020 | -0.034 | -1.31 | 50 | 49.0 | 0.51/0.55 | +0.094 | -0.185 | -0.041 | -0.030 | 84% |
| F4-03-L | Prior-Day-Low Sweep, buy the 15-min Gap retest (to liquidity), Long | 3,290 | 9.5 | -0.090 | -0.053 | -0.075 | -2.13 | 40 | 46.4 | 0.59/0.65 | +0.093 | -0.237 | -0.080 | -0.048 | 73% |
| F4-04-L | ... retest (2R), Long | 3,294 | 9.5 | -0.090 | -0.063 | -0.079 | -2.28 | 40 | 45.9 | 0.59/0.65 | +0.086 | -0.239 | -0.084 | -0.055 | 76% |
| F4-05-L | Opening-Range-Low Sweep then 15-min Gap (to liquidity), Long | 12,660 | 36.4 | -0.033 | -0.005 | -0.022 | -0.70 | 40 | 48.2 | 0.58/0.59 | +0.145 | -0.221 | -0.040 | -0.024 | 79% |
| F4-06-L | ... (2R), Long | 12,660 | 36.4 | -0.035 | +0.002 | -0.020 | -0.61 | 40 | 48.1 | 0.59/0.58 | +0.151 | -0.223 | -0.040 | -0.021 | 80% |
| F4-07-L | Opening-Range-Low Sweep, buy the 15-min Gap retest (to liquidity), Long | 6,082 | 17.5 | -0.101 | -0.082 | -0.093 | -3.06 | 30 | 44.2 | 0.67/0.70 | +0.103 | -0.268 | -0.106 | -0.050 | 67% |
| F4-08-L | ... retest (2R), Long | 6,087 | 17.5 | -0.100 | -0.074 | -0.090 | -2.81 | 30 | 44.0 | 0.68/0.70 | +0.111 | -0.268 | -0.104 | -0.042 | 70% |
| F4-09-S | Prior-Day-High Sweep then 15-min Gap (to liquidity), Short | 6,936 | 19.9 | -0.065 | -0.050 | -0.059 | -2.50 | 10 | 43.8 | 0.55/0.54 | -0.228 | +0.075 | -0.070 | -0.043 | 82% |
| F4-10-S | ... (2R), Short | 6,936 | 19.9 | -0.069 | -0.053 | -0.063 | -2.59 | 10 | 43.6 | 0.55/0.54 | -0.235 | +0.074 | -0.074 | -0.043 | 84% |
| F4-11-S | Prior-Day-High Sweep, sell the 15-min Gap retest (to liquidity), Short | 3,582 | 10.3 | -0.130 | -0.077 | -0.110 | -3.92 | 20 | 42.4 | 0.61/0.64 | -0.285 | +0.049 | -0.123 | -0.065 | 73% |
| F4-12-S | Opening-Range-High Sweep then 15-min Gap (to liquidity), Short | 12,977 | 37.3 | -0.076 | -0.039 | -0.063 | -1.92 | 30 | 44.3 | 0.61/0.60 | -0.265 | +0.110 | -0.078 | -0.053 | 76% |
| F4-13-S | ... (2R), Short | 12,977 | 37.3 | -0.074 | -0.038 | -0.061 | -1.79 | 30 | 44.1 | 0.62/0.60 | -0.266 | +0.114 | -0.079 | -0.055 | 78% |
| F4-14-L | PDL Sweep + strong 15-min push (0.30 ATR), Long | 2,292 | 6.6 | -0.082 | -0.021 | -0.056 | -1.48 | 50 | 48.0 | 0.49/0.56 | +0.103 | -0.226 | -0.064 | -0.048 | 81% |
| F4-15-L | PDL Sweep then big 15-min Gap (0.10 ATR), Long | 4,945 | 14.2 | -0.036 | -0.006 | -0.024 | -0.96 | 50 | 49.0 | 0.49/0.52 | +0.088 | -0.164 | -0.031 | -0.026 | 84% |
| F4-16-L | PDL shallow sweep (any trade-through), Long | 7,688 | 22.1 | -0.045 | -0.026 | -0.037 | -1.51 | 40 | 48.8 | 0.51/0.56 | +0.089 | -0.191 | -0.044 | -0.038 | 81% |
| F4-17-L | PDL Sweep then 15-min Gap, break-even at +1R, Long | 6,498 | 18.7 | -0.043 | -0.013 | -0.030 | -1.17 | 50 | 48.7 | 0.51/0.54 | +0.098 | -0.182 | -0.038 | -0.027 | 80% |
| F4-18 | parity (CWT14 p05, unpatched sim) | 53,326 | — | -0.0677 | -0.0675 | — | — | — | — | — | — | — | — | — | — |

**Rework (amendment, after all rows failed):**

| id | name | n | tr/sess | TRAIN | VALID | all | t_day | WF% | win% | up-day | down-day | w/o best day | best-day share | control |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F4-RW1-L | ORL Sweep then 15-min Gap, fixed 1R, Long | 12,660 | 36.4 | -0.034 | -0.020 | -0.029 | -1.07 | 50 | 49.1 | +0.127 | -0.214 | -0.041 | — | -0.025 |
| F4-RW2-L | PDL Sweep then 15-min Gap, fixed 1R, Long | 6,498 | 18.7 | -0.037 | -0.015 | -0.028 | -1.10 | 50 | 49.9 | +0.100 | -0.178 | -0.035 | — | -0.035 |
| F4-RW3-L | ORL Sweep then 15-min Gap, tight stop (FVG candle 1), Long | 12,938 | 37.2 | -0.041 | -0.001 | -0.024 | -0.71 | 40 | 47.8 | +0.159 | -0.245 | -0.044 | — | -0.024 |
| F4-RW4-L | ORL Sweep then 15-min Gap, Nasdaq up (QQQ >= +0.20%), Long | 5,535 | 15.9 | +0.013 | +0.114 | +0.060 | 1.11 | 50 | 52.6 | +0.157 | **-0.328** | +0.020 | **67% (1 day)** | +0.040 |
| F4-RW5-S | ORH Sweep then 15-min Gap, Nasdaq down (QQQ <= -0.20%), Short | 5,953 | 17.1 | -0.016 | +0.033 | +0.001 | 0.02 | 50 | 47.9 | -0.415 | +0.109 | -0.031 | (1 day) | -0.009 |
| F4-RW6-L | PDL Sweep then 15-min Gap, Nasdaq up (QQQ >= +0.20%), Long | 2,764 | 7.9 | -0.038 | +0.052 | +0.001 | 0.02 | 60 | 51.7 | +0.082 | -0.304 | -0.013 | (1 day) | +0.011 |

## Reading
- **The base gross edge is about zero.** Gross ≈ net + mean cost/R is -0.04 to +0.02R, and every row sits within ±0.05R of
  its own random control. The sweep, displacement and 15-minute FVG structure picks stocks no better than chance at the
  same minute.
- **Retrace (limit at the gap edge) entries are worse** than formation entries by 0.04-0.07R on every pair, below the
  control. This is adverse selection: the fills that come back to the gap are the ones that keep going against you.
- **The best-looking row, F4-RW4** (the ORL sweep long only when QQQ is up >= 0.20%), reaches +0.060R, but:
  - t is only 1.11, against 3.52
  - 67% of its total R comes from one day (2026-03-09)
  - it loses 0.33R on SPY down days
  - it beats its control by only +0.019R
  
  It is market beta selected by the gate, not the setup. **RW5**, the mirror short gated on QQQ down, is flat.
- **Target choice** (DOL vs 2R vs 1R) and **break-even** move results by less than 0.01R, because 70-84% of trades never
  reach either the stop or the target before 15:55.
- **This agrees with pdl1030** (PDL sweep-reclaim has no gross edge), R14/R18 and F1. Adding the 15-minute
  displacement-plus-FVG confirmation does not create the edge.

## For F5
The F4-01 entry code is `build.run_signal(seg_arrays(fh, ds), "PDL", 0, False)`, plus the `univ` filter in `month_job`. It
returns the fh entry rows, the entry price (NaN = close), R, the target multiple, the sweep row and the side.

## Files
- `PLAN.md`: the pre-declaration and the rework amendment
- `build.py`: signals, sim, control, parity, check and sanity
- `score.py`
- `rework.json`
- `results.csv`: every row, every column
- `parity.json`

The scratch parquet was deleted after scoring.
