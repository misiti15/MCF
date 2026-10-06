# orb20_a — exit-rule study (time in trade)

*Educational only — not financial advice. Backtest on collected live-setup entries (SIP 1-minute), not live or paper results.*

**Result: no exit variant passed. Keep the current exits.** 0 of 10 finalists beat the current exits by +0.03R on both
train and valid. The test split (Sep 16 – Oct 5) was not touched.

- Entries unchanged. Costs in (harness = backtester fills: next-bar entries, stop-first inside a bar, slippage plus extra stop slippage).
- Train = Jul 8 – Aug 25 2026 (n=249 trades). Valid = Aug 26 – Sep 15 2026 (n=102 trades).
- **Configurations tried: 100 on train** (52 single-rule in `orb20_a_grid.py`, 30 combinations in `orb20_a_grid2.py`, 18 neighbourhood checks in `orb20_a_grid3.py`).
  10 finalists went to valid (`orb20_a_valid.py`). At p=0.05, about 5 of 100 would look good on train by chance alone.
- Every train improvement is smaller than one standard error (train SE about 0.065R per trade). Valid SE is about 0.09R.

## Baseline (current live exits: stop 0.5 x range, target 0.75 x range = 1.5R, flat 15:55)
| split | n | exp R | SE | PF | win | ex-best-day | avg min | exits |
|---|---|---|---|---|---|---|---|---|
| train | 249 | +0.056 | 0.064 | 1.13 | 47% | +0.031 | 193 | time 98 / stop 85 / target 66 |
| valid | 102 | +0.050 | 0.094 | 1.13 | 45% | +0.011 | 228 | time 51 / stop 30 / target 21 |

The bar for a pass was train ≥ +0.086 and valid ≥ +0.080, with n within 20% and ex-best-day > 0 on both.

## Finalists: all failed (n is 249 train and 102 valid for every one; exits hide no trades)
| variant | train exp R | train ex-best | valid exp R | valid SE | valid ex-best | valid avg min |
|---|---|---|---|---|---|---|
| target 2.0R + time stop 90m if best < 0.4R | +0.105 | +0.078 | −0.013 | 0.092 | −0.041 | 182 |
| target 2.0R + time stop 75m / 0.4R | +0.097 | +0.071 | −0.016 | 0.092 | −0.046 | 172 |
| target 1.75R + time stop 90m / 0.5R | +0.095 | +0.066 | +0.013 | 0.089 | −0.015 | 159 |
| target 2.25R + time stop 90m / 0.4R | +0.099 | +0.076 | −0.004 | 0.095 | −0.037 | 184 |
| no target + time stop 90m / 0.5R | +0.093 | +0.068 | +0.011 | 0.110 | −0.039 | 190 |
| stop x1.3 + target 1.75R | +0.098 | +0.081 | −0.001 | 0.083 | −0.038 | 280 |
| stop x1.25 + target 1.75R | +0.092 | +0.074 | −0.003 | 0.086 | −0.041 | 270 |
| stop x1.3 + target 1.5R | +0.095 | +0.077 | −0.017 | 0.079 | −0.049 | 277 |
| target 2.0R alone (simple-rule check; already below the train bar) | +0.081 | +0.055 | +0.008 | 0.099 | −0.041 | 249 |
| time stop 90m / 0.5R alone (simple-rule check; already below the train bar) | +0.073 | +0.047 | +0.041 | 0.087 | +0.016 | 147 |

The best train variants were the worst on valid. That is the pattern of fitting noise. They were also knife-edges on train:
target 2.0R + 90m/0.5R gave +0.100, but 75m/0.5R gave +0.076 and 105m/0.5R gave +0.083. Changing the threshold from 0.4R to 0.6R took it from +0.105 to +0.075.

## What time in trade does to this setup (baseline exits)
From `orb20_a_time_profile.py`. Train decides; valid is descriptive only and was run after the finalists were fixed.
- **Losers resolve early and winners resolve late.** Train trades that closed within 30 minutes averaged −0.27R (n=41, 32% winners).
  Trades held more than 2 hours averaged +0.22R (n=141). Median time to a stop is 54 min on train and 78 min on valid.
  Median time to the target is 73 / 76 min. 39% (train) and 50% (valid) of trades never hit either and are flattened at 15:55,
  averaging +0.10 / +0.13R.
- **Holding on, on average, does not bleed.** Open trades gained about +0.03 to +0.09R between the 30/60/90/120-minute mark and the exit.
- **The bleed sits in stalled trades.** Trades that had not reached +0.5R by 30–60 minutes lost a further ~0.06–0.10R by the exit
  on both splits (train at 60m: −0.22 → −0.28R, n=86; valid at 60m: −0.15 → −0.26R, n=42).
  On valid, by 90 minutes this group had stopped bleeding (−0.14 → −0.13R, n=35). That is why the 90-minute time stop did not carry over.
  Trades that had reached +0.5R kept improving (train at 60m: +0.39 → +0.55R).
- Cutting time stops early (15–30 min) or exiting early in the day (11:30–15:00) hurt on train: every `exit_by` value was below baseline.
  The late-day drift is part of this setup's small edge. Breakeven stops and trailing stops at ≤ 1R also hurt (down to −0.045R),
  because pullbacks shake trades out before they reach the target.

## Recommendation
Keep the current orb20_a exits. No rule beat them out of sample. A time stop of about 60–90 minutes for trades that have not reached
+0.5R matches the economics (shorter holding, similar expectancy: valid +0.041 vs +0.050, avg 147 vs 228 min).
It is not a proven improvement and fails the +0.03R bar, so it is noted here only as a future idea to re-test on more data.
