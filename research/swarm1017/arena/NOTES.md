# Arena (swarm 2026-10-17) - NOTES

*Educational only - not financial advice. Backtest on history only; nothing here is paper or live.*

## Failures first
- **No single-indicator cell has an edge after costs.** 20,280 cells were scored on TRAIN (89 indicators x bins x
  3 windows x 2 sides x 3 geometries). The highest day-clustered t of production-cost expectancy is **1.01**,
  against a try-count bar of max(1.5, sqrt(2 ln 20,280)) = **4.45**. No cell reaches even t = 2 (0 of 20,280; about
  2.3% would under pure noise, and every cell here is negative-drift because of costs).
- Only 76 of 20,280 cells (0.37%) have exp_r > 0 after costs. Only **1** cell passes the loose screen filter
  (n >= 200, exp > 0, excess > 0, up > 0, down > 0, both train halves > 0): qqq_fromOpen >= q95 short t1s1 14:00-15:00,
  exp +0.028R, t 0.43, excess +0.001R. It sits on only 16 sessions and is research-only (context indicator).
- The best live-computable cell, **gap_atr <= -0.614 (gap down of more than 0.61 daily ATR), short t1s1, 14:00-15:00**,
  train +0.087R (n 4,829 sampled, t 1.01), is regime-dependent (up sessions -0.025R, down +0.272R) and decays
  (first half of train +0.181R, second half -0.054R). Scored end-to-end through combine.py on all symbol-days:
  train +0.071R (n 9,704, t 0.85), **valid -0.049R (n 9,830, t -1.02)**, up-regime -0.114R, walk-forward 35% of 17 folds
  positive -> fails. Adding vwap_atr <= 0: train +0.022R, valid -0.032R -> fails. (2 configurations; smoke_combo.json.)
- **Candidates: none.** Nothing is written to modules/. The arena is a tool; its screen is a hypothesis generator,
  and the honest finding is the same as research/swarm1010: no single point-in-time indicator on these 5-minute lab
  frames carries an edge that survives costs.

## What "beats random" means here (read before using the screen)
- Random baseline = mean production R of every universe bar at the same date and minute, same side and geometry.
  It is about -0.06 to -0.12R per trade (costs plus 15:55 time exits), see summary.txt.
- 58% of cells beat that baseline and 14% have t_excess > 2, but most of that excess is **side-neutral composition**:
  long and short cells of the same (indicator, bin, window, geometry) take the same first rows, and both beat the
  control (e.g. dist_round_atr low, i.e. names whose daily ATR is large relative to a round-number step, so costs are
  small in R: excess +0.03R for long AND short, exp_r still -0.08R). top300.csv therefore carries
  comp = (excess_long + excess_short)/2 and dir_excess = (excess_side - excess_other)/2; only dir_excess is direction.
  The largest directional excesses are ~+0.04..0.07R (gap_atr / gap low tails, short, 14:00-15:00), all regime-dependent.
- Context (ctx) cells condition on whole-market states, so they concentrate on few sessions (16-130 days): weak
  evidence even when n is large.

## Configurations counted
- Single-indicator screen: **20,280** cells (TRAIN, every other symbol-day). Arena lineage before this: 0 (new family;
  the broader intraday search in research/swarm1010 tried ~1.3M configurations on related features).
- combine.py smoke run: 2 (scored train + valid; listed above).
- Lineage total N = 20,282 -> bar t >= 4.45. **Later agents must add their combo counts to this N** (a 2-condition
  combination built from screen cells inherits the screen's search).

## Setup
- Data: research/history2y/data/frames (5-minute lab frames, bar closes 09:50-15:00). Locked block 2024-11..2025-02
  never loaded (lib.load_month refuses it; MCF_HIST_ALLOW_LOCKED never set).
- Split: TRAIN = 2024-10 + 2025-03..2025-12 (234 sessions); VALID = 2026-01-01..2026-10-07. (VALID contains the older,
  no-longer-clean holdouts Apr-Jun 2026 and Sep 16-Oct 5 2026.) The screen uses TRAIN only.
- Universe: adv20 >= $95M. Sample for the screen: every other symbol-day, crc32('SYM|date') % 2 == 0 (6.11M rows);
  the random-control means are computed on the full universe before sampling. combine.py uses all symbol-days.
- Costs: gates.prod_r with time-of-day entry costs, x3 on the extended tier (|gap| >= 20% or price < $5).
  One trade per symbol-day (first qualifying bar in the window). Geometries t05s1 / t1s1 / t1s05, R = 0.25 x daily ATR,
  timed exit 15:55. Day-clustered t (gates.summary convention). Regime classes from research/history2y/lib.regimes().
- Windows: 09:50-11:00, 11:00-14:00, 14:00-15:30 (bar close lo <= tod < hi; frames end at 15:00).
- Bins: train deciles per (indicator, window) d01..d10 [lo, hi) + tails le_q05, le_q20, ge_q80, ge_q95; <= 12
  distinct values -> one bin per value.

## The arena (code)
- `mcf/research/arena/indicators.py` - 89 point-in-time indicators in 8 families (mom 13, mr 15, trend 12, vol 9,
  flow 14, struct 15, ctx 9 research-only, time 2). `compute(df, names=None, context=True)` works on a history frame
  or on the live LabStrategy frame (DatetimeIndex, one symbol): rows outside 09:50-15:00 are NaN so both see the same
  inputs. Limits: the frames carry 5-minute bars and no raw volume, so "1/3/5/15/30/60-bar returns" are 1/3/6/12
  five-minute bars (5-60 min), and volume indicators are built from the existing volume ratios (no true
  rvol-by-time-of-day); no sector map exists in the repo, so sector-ETF relative strength is not included
  (SPY/QQQ/IWM and universe breadth are). vol_climax is identical to volumeRatio in the frames and is not duplicated.
- `mcf/research/arena/data.py` - `load(names, split="train"|"valid"|"all", min_adv=95e6, sample=None,
  cache_dir=None, workers=1, context=True)` -> rows with r_<side>_<geom> (production R), c_<side>_<geom>
  (same-minute random control), the indicators, split, regime. ~25 s and ~3.5 GB peak per month per worker:
  keep workers=1 on this 15 GB box (the full train+valid load of 2 indicators took ~9 min).
- `mcf/research/arena/screen.py` - the single-indicator screen (`python -m mcf.research.arena.screen --cache <dir>
  --out research/swarm1017/arena --sample 2 --workers 1`, ~5 min after the ~5 min cache build).
- `mcf/research/arena/combine.py` - `evaluate_combo(A, conds, side, geom, window=(950, 1500), n_lineage=1,
  regimes=None) -> dict` with train/valid/all summaries (+ excess over random), regime split, walk-forward,
  t_required(n_lineage), `gates` and `quality_pass`; `trades(...)`, `combo_mask(...)`;
  `write_module(conds, side, geom, window, path, name, doc="", allow_context=False)` emits a lab module
  (SIDE, GEOM, WINDOW, CONDS, LAYERS, mask(df) that calls indicators.compute). Context indicators are refused by
  the writer (NaN in the live frame -> the setup would never fire).
- Tests: `python -m pytest -q tests/test_arena.py` (8 tests: point-in-time on synthetic bars by truncation and by
  perturbing future bars, live-frame parity, known values, screen statistics vs gates.summary, combine + module
  round trip).

## Files
- single_screen.parquet - every cell (indicator, family, live, window, bin, op, lo, hi, side, geom, n, days, exp_r,
  se, t, excess, t_excess, win_rate, exp_up, n_up, exp_down, n_down, exp_h1, exp_h2).
- top300.csv - the 300 cells with n >= 200 and days >= 60 ranked by train t of exp_r (closest to tradable; only 34
  of them have exp_r > 0), with comp and dir_excess.
- summary.txt (summarize.py), smoke_combo.json (smoke_combo.py), PLAN.md.

## Top cells per (side, window), ranked by train t (days >= 60; every one is below the 4.45 bar)
#### long 0950-1100
| indicator | bin | lo | hi | geom | n | days | exp_r | t | excess | dir_excess | exp_up | exp_down | exp_h1 | exp_h2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rv12 | ge_q95 | 0.600 | 0.600 | t1s1 | 5220 | 234 | 0.003 | 0.039 | 0.010 | -0.012 | 0.291 | -0.245 | 0.126 | -0.112 |
| gap | d01 | -inf | -1.245 | t1s1 | 9757 | 234 | 0.001 | 0.014 | 0.009 | -0.001 | 0.351 | -0.426 | -0.003 | 0.007 |
| ret12 | ge_q95 | 1.504 | 1.504 | t1s1 | 6247 | 234 | -0.001 | -0.016 | 0.017 | -0.000 | 0.242 | -0.372 | 0.017 | -0.016 |
| rv12 | ge_q95 | 0.600 | 0.600 | t1s05 | 5220 | 234 | -0.002 | -0.020 | 0.036 | -0.001 | 0.164 | -0.138 | 0.093 | -0.091 |
| gap_atr | d01 | -inf | -0.406 | t1s1 | 9764 | 233 | -0.003 | -0.045 | 0.004 | 0.021 | 0.346 | -0.396 | -0.004 | -0.002 |

#### long 1100-1400
| indicator | bin | lo | hi | geom | n | days | exp_r | t | excess | dir_excess | exp_up | exp_down | exp_h1 | exp_h2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| breadth_vwap | ge_q80 | 0.703 | 0.703 | t1s1 | 45392 | 108 | 0.030 | 0.837 | 0.004 | 0.004 | 0.176 | -0.401 | 0.048 | 0.008 |
| dist_pdh_atr | ge_q95 | 1.680 | 1.680 | t1s1 | 7700 | 232 | 0.034 | 0.682 | 0.010 | 0.011 | 0.139 | 0.022 | 0.105 | -0.039 |
| breadth_vwap | d10 | 0.774 | inf | t1s1 | 27931 | 66 | 0.027 | 0.550 | 0.002 | 0.002 | 0.122 | -0.483 | 0.023 | 0.035 |
| gap | d01 | -inf | -1.248 | t05s1 | 9724 | 234 | 0.021 | 0.549 | 0.030 | 0.022 | 0.146 | -0.049 | 0.066 | -0.049 |
| breadth_vwap | ge_q80 | 0.703 | 0.703 | t05s1 | 45392 | 108 | 0.013 | 0.522 | 0.004 | 0.002 | 0.108 | -0.202 | 0.028 | -0.007 |

#### long 1400-1530
| indicator | bin | lo | hi | geom | n | days | exp_r | t | excess | dir_excess | exp_up | exp_down | exp_h1 | exp_h2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| macd_hist | le_q05 | -0.085 | -0.085 | t1s1 | 13684 | 234 | 0.010 | 0.343 | 0.040 | 0.024 | 0.092 | -0.095 | 0.053 | -0.035 |
| macd_hist | le_q05 | -0.085 | -0.085 | t05s1 | 13684 | 234 | 0.004 | 0.183 | 0.029 | 0.016 | 0.069 | -0.062 | 0.036 | -0.030 |
| spy_ret3 | ge_q95 | 0.202 | 0.202 | t05s1 | 25611 | 60 | -0.003 | -0.077 | -0.002 | -0.002 | 0.064 | -0.105 | 0.034 | -0.070 |
| sma20_dist_pct | le_q05 | -0.606 | -0.606 | t1s1 | 15021 | 234 | -0.006 | -0.171 | 0.042 | 0.026 | 0.158 | -0.137 | 0.035 | -0.049 |
| ret12 | le_q05 | -0.849 | -0.849 | t1s1 | 15211 | 234 | -0.012 | -0.303 | 0.041 | 0.025 | 0.124 | -0.134 | 0.014 | -0.040 |

#### short 0950-1100
| indicator | bin | lo | hi | geom | n | days | exp_r | t | excess | dir_excess | exp_up | exp_down | exp_h1 | exp_h2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| iwm_fromOpen | d02 | -0.693 | -0.448 | t1s1 | 33640 | 81 | -0.010 | -0.280 | -0.004 | -0.004 | -0.454 | 0.138 | -0.039 | 0.018 |
| atr_d_pct | ge_q95 | 7.833 | 7.833 | t1s1 | 5058 | 234 | -0.024 | -0.583 | 0.075 | 0.040 | -0.295 | 0.268 | 0.006 | -0.058 |
| iwm_fromOpen | le_q20 | -0.448 | -0.448 | t1s1 | 34403 | 83 | -0.023 | -0.624 | -0.004 | -0.004 | -0.481 | 0.124 | -0.070 | 0.025 |
| sma20_slope_pct | le_q05 | -0.737 | -0.737 | t1s1 | 7389 | 234 | -0.047 | -0.718 | 0.058 | 0.034 | -0.409 | 0.227 | -0.051 | -0.043 |
| fromOpen | le_q05 | -2.096 | -2.096 | t1s1 | 9483 | 233 | -0.024 | -0.777 | 0.049 | 0.026 | -0.263 | 0.157 | -0.022 | -0.027 |

#### short 1100-1400
| indicator | bin | lo | hi | geom | n | days | exp_r | t | excess | dir_excess | exp_up | exp_down | exp_h1 | exp_h2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gap | ge_q95 | 2.151 | 2.151 | t1s1 | 4859 | 234 | 0.001 | 0.017 | 0.043 | 0.027 | -0.285 | 0.355 | 0.048 | -0.052 |
| gap | ge_q95 | 2.151 | 2.151 | t1s05 | 4859 | 234 | -0.018 | -0.313 | 0.040 | 0.014 | -0.227 | 0.227 | 0.015 | -0.056 |
| prev_range_atr | ge_q95 | 1.695 | 1.695 | t1s1 | 4873 | 227 | -0.053 | -0.504 | -0.003 | -0.009 | -0.391 | 0.227 | 0.046 | -0.160 |
| gap | ge_q95 | 2.151 | 2.151 | t05s1 | 4859 | 234 | -0.029 | -0.602 | 0.019 | 0.014 | -0.204 | 0.179 | 0.007 | -0.070 |
| prev_range_atr | le_q05 | 0.430 | 0.430 | t1s1 | 4898 | 225 | -0.052 | -0.922 | -0.025 | -0.023 | -0.452 | 0.272 | -0.046 | -0.059 |

#### short 1400-1530
| indicator | bin | lo | hi | geom | n | days | exp_r | t | excess | dir_excess | exp_up | exp_down | exp_h1 | exp_h2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gap_atr | le_q05 | -0.614 | -0.614 | t1s1 | 4829 | 232 | 0.087 | 1.012 | 0.055 | 0.072 | -0.025 | 0.272 | 0.181 | -0.054 |
| gap_atr | le_q05 | -0.614 | -0.614 | t05s1 | 4829 | 232 | 0.038 | 0.796 | 0.044 | 0.058 | -0.062 | 0.172 | 0.083 | -0.028 |
| gap | le_q05 | -2.128 | -2.128 | t1s1 | 4821 | 234 | 0.067 | 0.760 | 0.060 | 0.044 | -0.030 | 0.181 | 0.133 | -0.044 |
| gap | le_q05 | -2.128 | -2.128 | t05s1 | 4821 | 234 | 0.027 | 0.504 | 0.048 | 0.041 | -0.083 | 0.132 | 0.065 | -0.036 |
| gap_atr | le_q05 | -0.614 | -0.614 | t1s05 | 4829 | 232 | 0.017 | 0.261 | 0.038 | 0.058 | -0.075 | 0.157 | 0.092 | -0.094 |

