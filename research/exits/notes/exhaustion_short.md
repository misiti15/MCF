# exhaustion_short — exit-rule study (2026-10-06)

*Educational only — not financial advice. This is a backtest on collected live-setup entries (SIP 1-minute bars, Jul 8 – Sep 15 2026), with costs in. It is not a paper or live result. Entries are unchanged; only exits vary.*

## Failures first
- **The headline gains are concentrated in one day.** On train, every wider-target variant gets almost all of its improvement from **2026-07-29**. That one day holds 87 of the 386 train trades. Leave it out and the train gain is only +0.004 to +0.019R per trade, with day-clustered t < 0.8 (`exhaustion_short_daydelta2.py`). So the train evidence that wider targets help is weak, even though the headline numbers look large.
- **No target at all (hold to 15:55) fails on valid.** It scores 0.150 vs a baseline of 0.178, and on train it is +0.001R per trade once 07-29 is left out. Its whole +0.17R on train comes from that one day.
- **Time stops make this setup worse.** All 16 time-stop cells at 20–60 min score below baseline on train (0.04–0.20R vs 0.245), and most of them are negative once the best day is removed. Time stops at 90–120 min do nothing: the result stays at baseline ±0.01.
- **Earlier exit_by times also make it worse.** 15:00 gives 0.049R, 14:30 gives 0.100R and 15:30 gives 0.209R. Two of these lose trades too: 14:30 drops 94 trades and 15:00 drops 13.
- **Tighter stops look better in R but are worse in dollars.** stop_mult 0.75 shows 0.263R, but sizing is capped by the slot (the risk cap never binds), so a smaller R unit does not buy more shares. Measured in baseline-R units it is about 0.197, which is worse than baseline. A paired check gives −0.048R per trade on train and −0.048 on valid. Wider stops (1.25, 1.5) are worse even in raw R.
- **Valid is small.** It has 53 trades over 14 days, and the SE per trade is 0.11–0.15R. That is larger than every delta measured here.
- **Configurations tried:** 64 on train besides the baseline (46 cells in grid 1 including the baseline, 19 in grid 2). At p = 0.05, roughly 3 false positives are expected by chance. 8 finalists were scored once on valid. The test split and the Apr–Jun holdout were not touched.

## Baseline (current live exits: stop 1R = 0.25 × daily ATR, target 1R, flatten 15:55)
| split | n | win | exp_r (SE) | PF | green days | ex-best-day | avg min | exits |
|---|---|---|---|---|---|---|---|---|
| train (to 08-25, 33 days) | 386 | 66.3% | 0.245 (0.038) | 2.10 | 66.7% | 0.106 | 93 | 151 target / 63 stop / 172 time |
| valid (08-26..09-15, 14 days) | 53 | 64.2% | 0.178 (0.113) | 1.62 | 50.0% | 0.047 | 83 | 22 target / 13 stop / 18 time |

## Time in trade (train, `exhaustion_short_profile.py`)
- **Winners take about an hour.** Target hits have a median of 49 min (quartiles 29 / 95, 90th percentile 121).
- **Losers resolve at about the same pace.** Stop hits have a median of 54 min (quartiles 36 / 74). Stopped trades had little in their favour first: their median MFE was +0.20R.
- **Many trades never resolve.** 172 of 386 (45%) reach the 15:55 flatten without hitting either the stop or the target, and these average +0.11R. Entries come at 13:00–15:00, so the clock runs out before the trade does.
- **The drift keeps building until the close; it does not bleed.** Average open-trade R with no exits (gross, mark-to-market) runs −0.05 at 5 min, +0.03 at 15, +0.17 at 30, +0.34 at 60, +0.51 at 90, +0.56 at 120 and +0.62 at 180+. Part of this average comes from 07-29.
- **The first 30 minutes sort trades sharply.** Trades that are in profit at 30 min end at +0.75R on average with no target (n 239). Trades under water at 30 min end at −0.14R (n 147). Cutting the laggards with a time stop still hurts, though: they keep part of the edge, and the cut also exits slow winners.
- **In short:** holding longer helps this setup, and cutting on time bleeds it. The question is how far to let winners run. A 1R target exits before the afternoon drift finishes.

## Finalists (exp_r after costs; baseline 0.245 train / 0.178 valid). All keep n = 386 / 53.
| variant | train | valid | valid SE | valid ex-best-day | train delta ex 07-29 (t) | valid paired delta (day t, days +/-) | mechanical gate |
|---|---|---|---|---|---|---|---|
| target 1.25R | 0.286 | 0.215 | 0.124 | 0.074 | +0.004 (0.19) | +0.037 (2.74, 7/0) | pass |
| target 1.5R | 0.314 | 0.214 | 0.131 | 0.112 | +0.012 (0.49) | +0.036 (0.91, 6/1) | pass (valid by +0.0365) |
| target 1.75R | 0.346 | 0.269 | 0.142 | 0.149 | +0.019 (0.75) | +0.092 (2.32, 6/1) | pass |
| target 2.0R | 0.367 | 0.236 | 0.147 | 0.098 | +0.014 (0.53) | +0.059 (1.07, 5/2) | pass |
| no target | 0.414 | 0.150 | 0.132 | 0.029 | +0.001 (0.04) | −0.028 (−0.52, 3/4) | **FAIL** (valid) |
| target 2R + breakeven at 1R | 0.375 | 0.264 | 0.143 | 0.117 | +0.018 (0.68) | +0.086 (1.85, 5/2) | pass |
| target 2R + trail 1R after 1R | 0.374 | 0.267 | 0.140 | 0.105 | +0.007 (0.29) | +0.090 (2.30, 6/1) | pass |
| no target + trail 1R after 1R | 0.424 | 0.212 | 0.130 | 0.069 | +0.002 (0.09) | +0.034 (1.53, 4/3) | pass (valid by +0.034) |

**Knife-edge check.** On train, every target from 1.25R to 3R beats baseline, so the target ladder is a smooth slope and not a knife-edge. On valid, 1.25R through 2R all beat baseline.

## Recommendation
- **Score the simplest finalists on the locked holdouts:** target 1.5R and 1.75R, with 1.25R as the conservative neighbour. Leave the stop, breakeven and trail rules unchanged.
- **Treat the evidence as weak.**
  - Valid supports the change modestly and consistently: the paired per-day deltas are positive on 6–7 of 7 days that changed.
  - Train support depends on one day (07-29).
  - The breakeven and trail add-ons are more complex and add nothing robust over a plain wider target.
- **Do not adopt "no target" or any time stop.**
- **If the holdouts do not confirm the change, keep the current exits.**

Files: `research/exits/candidates/exhaustion_short.json`, plus these scripts in this folder: `exhaustion_short_{profile,grid,grid2,valid,daydelta,daydelta2}.py` and `exhaustion_short_valid_out.json`.
