# Replay calibration scorecard — TRAIN v1, full-priors sessions 2026-10-27..2026-10-30

*Educational only — not financial advice. Calibrated session replay (mcf/replay/livecal.py, params_v2) vs the live paper journals; targets pre-registered in TARGETS.md; R after LR8 costs on each side's own fills.*

| account | sessions | live trades | replay trades | match (exact bar) | match ±1 min | extra | R bias (95% CI, session-clustered) | not optimistic | daily R corr | sign agree | skip-reason match | worst day | all targets |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | 4 | 103 | 99 | 90.3% FAIL | 90.3% | 5.8% FAIL | 0.0017 [-0.0316, 0.0350] PASS | PASS | 0.962 | 100% PASS | 91.4% FAIL | PASS | **FAIL** |
| testing | 4 | 568 | 550 | 90.5% FAIL | 90.5% | 6.3% FAIL | 0.0034 [-0.0043, 0.0112] PASS | PASS | 0.990 | 50% FAIL | 90.7% FAIL | PASS | **FAIL** |
| testing2 | 1 | 240 | 232 | 93.3% FAIL | 93.3% | 3.3% FAIL | 0.0211 [n/a, n/a] FAIL | FAIL | n/a | 100% FAIL | 91.3% FAIL | FAIL | **FAIL** |
| pooled | 4 | 911 | 881 | 91.2% FAIL | 91.2% | 5.5% FAIL | 0.0080 [-0.0017, 0.0177] PASS | PASS | 0.989 | 78% FAIL | 90.9% FAIL | FAIL | **FAIL** |

Live R vs replay R (sum, after LR8 costs): primary -5.9 vs -8.4; testing -114.4 vs -101.6; testing2 -47.3 vs -39.5; pooled -167.6 vs -149.5

## Biggest status mismatches (matched signals, live -> replay)

- **primary**: submitted:ok -> skipped:spread is #% of stop distance ×5; skipped:spread #bps > max -> skipped:spread is #% of stop distance ×4; skipped:spread is #% of stop distance -> submitted:ok ×4; submitted:ok -> skipped:spread #bps > max ×2; skipped:spread #bps > max -> submitted:ok ×2; submitted:ok -> skipped:setup daily loss limit ×2
- **testing**: submitted:ok -> skipped:spread #bps > max ×23; skipped:spread #bps > max -> skipped:spread is #% of stop distance ×21; skipped:spread is #% of stop distance -> submitted:ok ×18; submitted:ok -> skipped:spread is #% of stop distance ×15; skipped:spread #bps > max -> submitted:ok ×15; submitted:ok -> skipped:position mismatch ×5
- **testing2**: skipped:spread #bps > max -> skipped:spread is #% of stop distance ×7; submitted:ok -> skipped:spread is #% of stop distance ×7; submitted:ok -> skipped:spread #bps > max ×7; skipped:spread #bps > max -> submitted:ok ×5; skipped:spread is #% of stop distance -> submitted:ok ×2; skipped:spread is #% of stop distance -> skipped:spread #bps > max ×1

## Per setup (≥ 10 live trades: 20 setups, all listed)

| account | setup | live | replay | match | extra | live avg R | replay avg R | bias (matched) |
|---|---|---|---|---|---|---|---|---|
| primary | CWT14-failbrk-pdl-p10-lowvol-long | 34 | 33 | 97% | 0% | -0.078 | -0.061 | -0.017 |
| primary | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 17 | 14 | 82% | 0% | 0.011 | -0.039 | 0.061 |
| primary | MF4-h40-open-flowsell-FD | 13 | 12 | 77% | 15% | -0.300 | -0.214 | 0.001 |
| primary | RW3-gapdn-rsi5pop-flowsell-short-FD | 12 | 12 | 100% | 0% | -0.175 | -0.147 | 0.029 |
| testing | CWT14-failbrk-pdl-p05-long | 233 | 246 | 95% | 10% | -0.147 | -0.114 | 0.011 |
| testing | RW7-gapdn-bounce-early-short-FD | 92 | 89 | 92% | 4% | 0.035 | 0.040 | 0.011 |
| testing | L3-gap-slope-fromopen-FD | 48 | 36 | 73% | 2% | 0.228 | 0.492 | -0.029 |
| testing | MF3-open-flowsell-rsi5hi-FD | 35 | 32 | 89% | 3% | -0.638 | -0.678 | -0.005 |
| testing | exhaustion_short-FD | 21 | 20 | 95% | 0% | -0.237 | -0.268 | -0.029 |
| testing | RW4-ns3-adv150-short-FD | 20 | 21 | 95% | 10% | -0.693 | -0.720 | -0.008 |
| testing | exhaustion_short | 16 | 15 | 94% | 0% | -0.498 | -0.545 | -0.013 |
| testing | MF5-flowsell-vwapup-rsi5hi | 13 | 10 | 77% | 0% | -0.903 | -0.892 | 0.005 |
| testing | NS1-rsidip-rsi5pop-long-FD | 13 | 10 | 77% | 0% | 0.017 | -0.112 | -0.013 |
| testing | L3-gap-slope-lowdist-FD | 11 | 9 | 82% | 0% | -0.401 | -0.541 | -0.014 |
| testing | intraday_momentum | 10 | 6 | 60% | 0% | -0.498 | -0.306 | -0.003 |
| testing2 | CWT12-coil-k4-long | 74 | 69 | 89% | 4% | 0.052 | 0.141 | 0.023 |
| testing2 | CWT14-failbrk-pdl-p05-lowvol-long | 72 | 71 | 94% | 4% | -0.220 | -0.179 | 0.026 |
| testing2 | CWT14-failbrk-pdl-p10-long | 47 | 47 | 100% | 0% | -0.193 | -0.200 | -0.007 |
| testing2 | MF5-flowsell-vwapup-rsi5hi-FD | 14 | 14 | 100% | 0% | -1.006 | -1.010 | -0.005 |
| testing2 | exhaustion_short-FD | 13 | 13 | 92% | 8% | -0.537 | -0.614 | 0.011 |

## Daily R (account-session)

| account | day | live trades | replay trades | live R | replay R |
|---|---|---|---|---|---|
| primary | 2026-10-27 | 58 | 52 | +3.67 | +0.06 |
| primary | 2026-10-28 | 14 | 12 | +5.07 | +4.84 |
| primary | 2026-10-29 | 16 | 16 | -11.78 | -11.89 |
| primary | 2026-10-30 | 15 | 19 | -2.91 | -1.45 |
| testing | 2026-10-27 | 189 | 184 | -68.73 | -67.01 |
| testing | 2026-10-28 | 162 | 159 | -39.86 | -35.00 |
| testing | 2026-10-29 | 174 | 165 | -6.86 | +1.65 |
| testing | 2026-10-30 | 43 | 42 | +1.08 | -1.23 |
| testing2 | 2026-10-27 | 240 | 232 | -47.33 | -39.49 |

Educational only — not financial advice.
