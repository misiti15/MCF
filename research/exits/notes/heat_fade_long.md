# heat_fade_long — exit-rule study (2026-10-06)

*Educational only — not financial advice. Backtest on collected live-setup entries (SIP 1-minute), costs in. Not paper, not live.*

## Failures first
**No finalist passed.** 10 finalists were taken from train to valid; all 10 beat the current exits on train by +0.03R or more,
and **all 10 did worse than the current exits on valid** (every one had exp_r_ex_best_day < 0 on valid). Nothing goes to the
locked test. Recommendation: keep the current exits (1R target, current stop, flatten at session end).

Configurations tried: **114 train runs** (55 in `heat_fade_long_grid.py`, 59 in `heat_fade_long_grid2.py`; about 3 repeat
earlier configs) plus 10 finalists on valid. At p=0.05 roughly 5-6 false positives are expected from 114 tries, and the train
gains (+0.03 to +0.06R) are about 1 standard error (train SE ~0.035R), consistent with noise/overfitting.

## Baseline (current live exits)
| split | n | win | exp_r | SE | ex-best-day | green days | avg min |
|---|---|---|---|---|---|---|---|
| train (Jul 8 - Aug 25) | 571 | 54.3% | +0.091 | 0.035 | +0.042 | 54% | 138 |
| valid (Aug 26 - Sep 15) | 116 | 50.0% | -0.025 | 0.079 | -0.072 | 38% (13 days) | 145 |

The baseline itself is already negative on valid; the setup's edge did not carry into valid.

## Finalists (train -> valid, exp_r after costs; n unchanged at 571 / 116 for all)
| variant | train exp_r (ex-best) | valid exp_r (ex-best) | pass |
|---|---|---|---|
| exit_by 15:00 | +0.123 (+0.075) | -0.081 (-0.109) | no |
| exit_by 14:45 | +0.118 (+0.069) | -0.061 (-0.086) | no |
| target 1.5R | +0.128 (+0.061) | -0.027 (-0.087) | no |
| target 1.5R + exit_by 15:00 | +0.142 (+0.081) | -0.075 (-0.116) | no |
| target 1.25R + exit_by 15:00 | +0.129 (+0.077) | -0.071 (-0.105) | no |
| target 1.75R + exit_by 15:00 | +0.142 (+0.075) | -0.075 (-0.123) | no |
| target 2.0R + exit_by 15:00 | +0.154 (+0.081) | -0.063 (-0.114) | no |
| target 1.5R + exit_by 14:45 | +0.136 (+0.074) | -0.059 (-0.095) | no |
| trail 0.6R after +0.6R, no target, exit_by 15:00 | +0.124 (+0.069) | -0.095 (-0.126) | no |
| time stop 120m if MFE < 0.5R + exit_by 15:00 | +0.121 (+0.074) | -0.047 (-0.076) | no |

Full numbers: `research/exits/candidates/heat_fade_long.json` (and `notes/heat_fade_long_valid_out.json`).

## What time in trade does (train, current exits; `heat_fade_long_profile.py`)
- Entries are 11:05-13:30 and resolve slowly. Targets (1R) hit at a median of 73 min (IQR 50-123); stops at a median of 55 min
  (IQR 30-123); 198 of 571 trades (35%) are still open at the session flatten (median 240 min) and average -0.07R.
- The sweet spot is 30-120 min: trades closing in 30-60 min average +0.24R, in 60-120 min +0.39R. Trades that close within
  15 min average -0.63R (fast stop-outs); those lasting over 240 min average -0.11R.
- **Early time stops hurt.** Trades are flat at 15-30 min (mark-to-market ~0.0R) but holding adds +0.11 to +0.13R from there.
  Cutting non-movers at 20-45 min lowers expectancy (e.g. 30 min / MFE < 0.3R: +0.007R vs +0.091R) because many trades with
  only +0.1-0.3R MFE at 30 min still go on to hit the target.
- **Holding past ~90-120 min stops paying.** For trades still open at 90 min, holding to the close adds +0.01R; at 120 min
  -0.04R. Trades with MFE < 0.3R at 60+ min end at -0.02 to -0.45R. This is why exit_by 15:00 and a 120 min / 0.5R time stop
  looked better on train.
- **But it did not hold on valid.** In valid, trades still open at the flatten averaged +0.06R (late-day drift went the other
  way), so cutting at 14:45-15:00 lowered expectancy by 0.04-0.06R. Valid is only 13 trading days (116 trades), so it cannot
  confirm or kill the late-day effect by itself, but the rules say a finalist must beat baseline on both splits and none did.
- Losers that are going to lose mostly show it early: MFE < 0.1R at 45 min -> final -0.35R (train), -0.49R (valid, n=10).
  A rule exiting only those was effectively tested as time_stop_min 45 / r 0.1 (+0.089R, no better than baseline) because the
  stop already takes most of them.

## Files
`heat_fade_long_grid.py`, `heat_fade_long_grid2.py` (train search), `heat_fade_long_valid.py` (finalists on valid, writes JSON),
`heat_fade_long_profile.py` (time-in-trade profile; valid run was descriptive only, after finalists were fixed).
