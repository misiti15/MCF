# intraday_momentum — exit-rule study (time in trade)

*Educational only — not financial advice. Backtest on collected live-setup entries (SIP 1-minute), not live or paper results.*

**Result: no exit variant passed. Keep the current exits.** 0 of 10 finalists beat the current exits by +0.03R on both
train and valid. All 10 did worse than the current exits on valid. The test split (Sep 16 – Oct 5) was not touched.

- Entries unchanged: SPY/QQQ/IWM/DIA, direction set by the prev-close→10:00 return (|r| ≥ 0.25%), entry at 15:30.
  Current exits: stop 0.25 × ATR (median 33 bps train, 24 bps valid), no target, 50% scale-out at 1R, flat 15:55.
  **A trade lasts at most 25 minutes.** 133 of 133 trades ran to the end of the window (one valid trade was stopped).
- Costs in (harness = backtester fills: next-bar entries, stop-first inside a bar, slippage plus extra stop slippage).
- Train = Jul 8 – Aug 25 2026 (n=97 trades, 33 days). Valid = Aug 26 – Sep 15 2026 (n=36 trades, 12 days).
  The samples are small and trades on the same day are correlated (up to 4 index ETFs on one signal):
  the day-clustered SE of the mean is 0.074R on train and 0.118R on valid.
- **Configurations tried: 70 on train** (47 in `intraday_momentum_grid.py`, 23 neighbourhood checks in `intraday_momentum_grid2.py`).
  10 finalists went to valid once (`intraday_momentum_valid.py`). At p=0.05, about 3–4 of 70 would look good on train by chance alone.

## Baseline (current live exits)
| split | n | exp R | SE | PF | win | green days | ex-best-day | avg min | exits |
|---|---|---|---|---|---|---|---|---|---|
| train | 97 | −0.028 | 0.042 | 0.82 | 33% | 30% | −0.091 | 25 | time 93 / scaled+time 4 |
| valid | 36 | +0.033 | 0.076 | 1.20 | 47% | 50% | −0.032 | 25 | time 33 / scaled+time 2 / stop 1 |

The baseline is about break-even. Without its best day it is negative on both splits.
The bar for a pass was train ≥ +0.002 and valid ≥ +0.063, with n within 20% and ex-best-day > 0 on both.

## Finalists: all failed (n is 97 train and 36 valid for every one; exits hide no trades)
| variant | train exp R | train ex-best | valid exp R | valid SE | valid ex-best | valid avg min |
|---|---|---|---|---|---|---|
| exit 15:45 | +0.030 | −0.027 | −0.060 | 0.037 | −0.079 | 15 |
| exit 15:47 | +0.047 | −0.015 | −0.047 | 0.040 | −0.068 | 17 |
| exit 15:50 | +0.040 | −0.015 | −0.058 | 0.043 | −0.084 | 20 |
| target 0.2R | +0.008 | +0.002 | −0.024 | 0.047 | −0.038 | 14 |
| target 0.25R | +0.006 | −0.003 | +0.001 | 0.049 | −0.018 | 16 |
| exit 15:48 + target 0.25R | +0.019 | +0.011 | −0.011 | 0.037 | −0.029 | 13 |
| exit 15:50 + target 0.25R | +0.026 | +0.017 | −0.021 | 0.040 | −0.039 | 14 |
| exit 15:50 + target 0.4R | +0.017 | +0.003 | −0.045 | 0.045 | −0.071 | 18 |
| time stop 15m if best < 0.3R | +0.015 | −0.048 | −0.005 | 0.057 | −0.055 | 18 |
| exit 15:50 + time stop 10m / 0.1R | +0.033 | −0.022 | −0.047 | 0.037 | −0.073 | 16 |

Six of the 10 already had ex-best-day ≤ 0 on train. They were taken to valid as simple-rule checks (an earlier exit is the
plainest time-in-trade rule). The early-exit rules were knife-edges on train: 15:46–15:50 gave +0.035 to +0.047,
15:51 gave −0.005 and 15:52 gave −0.016. The target+exit combos were also knife-edges: at 15:50, target 0.25R gave +0.026,
target 0.3R gave +0.007 and target 0.2R gave +0.011.

## What time in trade does to this setup (baseline exits)
From `intraday_momentum_profile.py` (mark-to-market R at bar close vs. fill, gross of exit costs). Train decides.
Valid is descriptive only and was run after the finalists were fixed.
- **Costs are about 0.09R per round trip.** On train the gross mark-to-market at 15:54 averaged +0.060R, but the net result was −0.028R.
  The stop is narrow in price terms (≈ 24–33 bps), so a few cents of slippage on each side is a large part of R. The first
  minute after entry averages −0.04R on train. Most of the variants tried cannot get around this cost. Only the ones that
  cut costs on the losing side (an earlier exit, a small target) briefly look better.
- **Neither winners nor losers resolve inside the window.** The median trade reaches only +0.21R of favourable excursion (train)
  and −0.26R of adverse excursion. 20–22% of trades ever reach +0.5R. The stop (1R) and the 1R scale-out almost never trigger.
  The result is set by where the market sits at 15:55, not by the exit rules.
- **The path within the 25 minutes flips between the splits.** On train, gross P/L built until about 15:50 (+0.09R at minute 20)
  and then gave back a third of it in the last 5 minutes (+0.06R). That is why exiting at 15:46–15:50 looked better on train.
  On valid, the whole gain came in the last 5 minutes (−0.01R at minute 20 → +0.08R at minute 24). Exiting early there
  cut it out (−0.05 to −0.06R). The last minutes before the close (close auction imbalances) are where both the bleed and the
  gain came from, and they changed sign between the splits.
- **Trades behind at 10 minutes stayed behind.** On train, the 53 trades under water at 10 minutes ended at −0.17R net
  (gross change to the end −0.01R). On valid, the 20 such trades also ended at −0.17R (−0.01R). Holding them did not recover anything,
  but cutting them early did not save anything either: most of their loss was already there at 10 minutes, plus the exit cost.
  Trades ahead at 10 minutes ended at +0.14R (train) and +0.29R (valid). Holding them to 15:55 helped on valid (+0.15R gross)
  and was flat on train (+0.00R). Time stops at 5–15 minutes did not beat the baseline by the bar on train once ex-best-day was required.

## Recommendation
Keep the current intraday_momentum exits. No exit rule beat them out of sample, and every finalist was worse than them on valid.
This setup's problem is not its exits: the 25-minute window is short, about 0.09R per trade goes to costs, and the baseline is
break-even with no edge left without its best day (−0.09R train, −0.03R valid). Trimming the hold changes when in the last
minutes the trade is exposed. It does not change the edge. Any improvement would have to come from the entry/filter side
or from a wider stop sized so costs are a smaller share of R. A wider stop is not an exit improvement:
stop × 1.5 only rescales R toward zero (train −0.013R) because the stop is almost never hit.
