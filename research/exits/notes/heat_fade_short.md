# heat_fade_short — exit-rule study (2026-10-06)

*Educational only — not financial advice. Backtest on collected live-setup entries (SIP 1-minute), costs in. Not paper or live results.*

## Failures first
- **No exit variant beats the current exits in dollar terms on both train and valid. Recommendation: keep the current exits** (stop 1R = 0.25 x daily ATR, target 1R, flatten 15:55).
- 131 train configurations tried (grid 64 + grid2 39 + grid3 28; a few `time_stop_min_r: 0.0` rows are no-ops because MFE never goes below 0). At p = 0.05 about 6-7 false positives are expected by chance from that many.
- 9 finalists went to valid. **3 pass the mechanical gate (+0.03R on both splits, n unchanged, ex-best-day > 0), and all 3 are misleading**: they are `stop_mult` 0.55 / 0.6 / 0.65. A tighter stop shrinks the R unit. In this account sizing is capped by the slot (about $1,930 notional; the median stop is 1.2% of price, so about $24 at risk against a $250 risk cap, and the risk cap never binds), so a tighter stop does **not** buy more shares. In baseline-R units (exp_r x stop_mult) they come out **worse** than baseline on both splits (train 0.094-0.103 vs 0.107; valid 0.130-0.162 vs 0.180). Win rate also falls from 57% to 48-52%.
- The time-stop finalists looked good on train (+0.02 to +0.04R) and **fell apart on valid**. Dropping the target with a 15-20 min time stop gave -0.15R on valid (vs +0.18 baseline). The time-stop-only rule (20 min, MFE < 0.5R) gave 0.093 vs 0.180. Each of these is a train overfit.

## Baseline (current exits)
| split | n | win | exp_r (SE) | PF | green days | ex-best-day | avg min |
|---|---|---|---|---|---|---|---|
| train (to 08-25) | 649 | 57.0% | 0.107 (0.036) | 1.27 | 62.9% | 0.059 | 110 |
| valid (08-26..09-15) | 141 | 61.0% | 0.180 (0.079) | 1.48 | 71.4% | 0.082 | 96 |
The SE is per trade, not day-clustered. Same-day trades are correlated, so the true uncertainty is larger, and valid covers only about 14 trading days.

## Time in trade (train, current exits; `heat_fade_short_profile.py`)
- **Winners resolve fast.** Target hits: median 26 min (quartiles 14 / 74 min, 90th percentile 154). 171 of 313 targets hit within 30 min.
- **Losers take longer.** Stop hits: median 52 min (quartiles 22 / 91, 90th percentile 149).
- Open-trade drift (mark-to-market, no exits, gross): +0.02R at 5 min, +0.09 at 15, **+0.20 at 30 (peak)**, +0.16 at 60, then roughly 0.04-0.09 from 90 to 300 min. The fade does its work in the first 30-60 min. After that the average open trade goes nowhere, but it is not bleeding badly either.
- The 99 trades still open at 15:55 average +0.11R. Holding to the close is not a loser.
- **So time-based cutting does not help.** Trades that have not reached +0.5R by 20 min still carry part of the edge, and cutting them gave up more than it saved on valid. Earlier exit_by times (10:45-15:00) were all at or below baseline on train (11:15-11:30 was worst at about 0.06R), because the slow trades still produce late target hits. A wider target or no target (1.25-2R) is no better. Breakeven moves and trails are worse (0.06-0.10R): this setup needs room.

## Finalists (train / valid exp_r; baseline 0.107 / 0.180)
| variant | train | valid | in baseline-R units | verdict |
|---|---|---|---|---|
| stop_mult 0.55 | 0.182 | 0.236 | 0.100 / 0.130 | R gate pass, dollar FAIL |
| stop_mult 0.6 | 0.172 | 0.230 | 0.103 / 0.138 | R gate pass, dollar FAIL |
| stop_mult 0.65 | 0.145 | 0.249 | 0.094 / 0.162 | R gate pass, dollar FAIL |
| stop_mult 0.6 + TS 20m/0.5R | 0.170 | 0.129 | 0.102 / 0.077 | FAIL |
| TS 20m/0.5R, no target | 0.150 | -0.149 | same | FAIL (ex-best-day -0.19) |
| TS 15m/0.5R, no target | 0.143 | -0.154 | same | FAIL |
| TS 20m/0.5R, target 1.5R | 0.141 | 0.015 | same | FAIL |
| TS 30m/0.6R, target 1.5R | 0.146 | 0.017 | same | FAIL |
| TS 20m/0.5R (time-only reference) | 0.131 | 0.093 | same | FAIL (below train bar too) |

Files: `research/exits/candidates/heat_fade_short.json`, scripts `heat_fade_short_{profile,grid,grid2,grid3,valid}.py` in this folder. Test and Apr-Jun holdouts were not touched.
