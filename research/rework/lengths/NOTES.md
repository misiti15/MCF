# Rework: global indicator-length sweep (key `lengths`)

*Educational only — not financial advice. Backtest results on train/valid only; nothing here was scored on a locked holdout.*

**Question (owner):** would our setups be better with different indicator lengths, e.g. a 10-period RSI everywhere?
**Answer: no.** A 10-period (or 7-period) RSI applied to all setups is worse on valid. Pooled valid exp_r is −0.019R at RSI 10 and −0.044R at RSI 7, against +0.072R at the current RSI 14. The current lengths (RSI 14, SMA 20/50, ATR 14) are the best global setting on valid. This is partly by construction, because the thresholds were fitted at those lengths.

## Failures first
- **obos_levels_1, trend_pullback_2, trend_pullback_3, win_geometry_1, win_geometry_2, win_geometry_3:** no length setting passes the gate (valid t ≥ 1.5 with n ≥ 30 and a plateau). Results by setup:
  - win_geometry_3 (long): valid is ≤ 0 at every length.
  - obos_levels_1: best is RSI 21 / ATR 10, valid +0.119R with n 84 and t 0.99.
  - win_geometry_2: valid t peaks at 1.47 with n 69.
  - win_geometry_1: positive on train and valid at all 9 settings, but valid t ≤ 1.19.
- **Global settings (72):** none reaches valid t 1.5 pooled. The best is the current base, with t 1.36.
- **Shortening the SMA slots (10/20) or using a slow SMA of 100** pushes most setups to ~0 or below on valid.

## Finalists (3, all reported; each is a lengths variant of a setups2 candidate)
| id | rule change | train | valid | plateau |
|---|---|---|---|---|
| lengths_vf1_rsis7_atr20 | volume_flip_1: short RSI 5→7, ATR 14→20 | +0.190R n398 t1.42 | +0.184R n90 t2.03 (base +0.032R, ex-best-day +0.134R) | mean +0.143R, 7/7 positive |
| lengths_vf2_rsis3_fast10 | volume_flip_2: short RSI 5→3, SMA20→SMA10 | +0.139R n517 t1.90 (ex-best-day +0.051R) | +0.113R n88 t1.79 (base −0.030R) | mean +0.078R, all positive |
| lengths_tp1_atr20 (weak) | trend_pullback_1: ATR 14→20 (same trades, new R) | +0.064R n512 t0.85 (ex-best-day +0.006R) | +0.061R n203 t1.68 | mean +0.006R, NOT all positive |

Caveats:
- The vf1 variant shares 345/398 train and 69/90 valid trades with the live rule. It cannot be told apart from the live rule, which scores train +0.189R and valid +0.151R (t 2.01) on the same frame. The live lengths already sit on a plateau, so the recommendation is to keep them.
- The vf2 and tp1 lineages already used holdout look 1 (the setups2 test), so look 2 needs t ≥ 1.5.
- tp1 is the identical trade list that failed the test. It passes the gate only because the gate uses the plateau mean.

## Method
- `build.py` rebuilds the setups2 features from 1-minute data/cache bars. It reads only bars dated before 2026-09-16, through a pyarrow filter.
  - RSI {7,10,14,21}, short RSI {3,5,7,10}, 5-min SMA distance {10,20,50,100}, daily ATR {10,14,20}. ATR sets R, so outcomes are recomputed for each ATR length.
  - All 1,225 symbols with data were used; no subsample.
  - At the base lengths, the features match research/setups2/data exactly on overlapping rows.
- **Costs are the full config set:** 1c + 1 bps per side, 3c on extended-tier names, and +2c on stops. That is about 0.03R harsher than the setups2 frame. Entry and exit follow the setup_lab convention: entry at the signal bar close, stop first inside a bar, timed exit at 15:55.
- **Splits:** train is 2026-07-15..08-25 (30 sessions; the earlier sessions are ATR(20) warm-up). Valid is 08-26..09-15 (14 sessions).
- `lab.py` scores the following, with thresholds unchanged and only lengths moving:
  - a full factorial over each candidate's own length slots: (a) volume_flip_1/2, 144 each; (b) the other failed candidates.
  - (c) 72 global settings, each applying one length set to all 9 candidates at once.
  - Statistics: first bar per symbol-day, day-clustered t, ex-best-day, and a baseline of a random symbol at the same date and bar close, same side and same exit.
  - Plateau: the mean valid exp_r of the one-step neighbours.
- **Configurations tried:** 450 (378 candidate × setting + 72 global). At p = 0.05, expect about 22 false positives. Full grid: GRID.md; raw data: results.json.
