# Autopsy of the 60 live paper trades (2026-10-06 and 2026-10-07), and the fixes they suggested

*Educational only — not financial advice. Live paper results, backtests (train/valid) and the two-day replays are labelled separately. The two live days are diagnosis only and not evidence (rule 7).*

## Failures first
- **78 configurations were tried on train/valid.** At p = 0.05 that is about 4 false positives by chance.
  - None of the owner's suggested safety nets passes:
    - −1.5% max loss
    - +0.5R take-profit
    - breakeven move
    - trailing stop
    - 1–2 minute entry delay
    - short-term RSI layer
    - re-entry after a stop
    - earlier exit for exhaustion_short
  - The "skip the extended / wide-range ORB" filters also fail.
- **The −1.5% max-loss cap loses money.** Across all four setups it lost **−$4,144 on train** (day-clustered t −1.51; $6.05 → $3.43 per trade) and **−$716 on valid** (t −2.59; $3.16 → $1.43 per trade).
  - Every cap level from 1% to 3% is negative on all four setups combined, on both splits.
  - Only heat_fade_short at 2.0% passes the gate, by **+$12.9 on valid**. Its neighbours fail (1.5% is −$233 on valid; 2.5% changes nothing on valid), so it fails rule 18's plateau test and is **not a finalist**.
- **The give-back exits fail again**, as they did in EXIT_STUDY's 489 configurations. These are breakeven at 0.5R or 0.75R, a 0.5R trail after +0.5R, and a 0.5R target, on each setup and on all four together.
  - For example, tp0.5 on all four setups: train −$4,124, valid −$162.
  - On the two live days tp0.5 would have helped (−8.1R instead of −12.0R, simulated on the same entries). That is the hindsight trap: the days that hurt look fixable, but the 44 backtest sessions say otherwise.
- **The flatten bug did not cause the losses.** 16 trades (10 on 10-06, 6 on 10-07) closed at 16:05–16:06 instead of 15:55.
  - At the 15:55 close they would have made **−$277 instead of −$265**.
  - 10-07 alone: −$148 at 15:55 vs −$179 live, so the bug cost $30 that day. 10-06: the late exits helped by $42.
  - **HESM at 15:55 would have closed at −0.54R / −$65, against −0.59R / −$71 live.**
  - PR #8 fixed the bug after the close on 10-07. The orb20_a backtest itself exits at 15:50 (`exit_by`).

## Live results being diagnosed
- 60 trades, 23 green, **−$382 in total**:
  - 10-06: 44 trades, 19 green, −$120.
  - 10-07: 16 trades, 4 green, −$262.
- By setup:

  | setup | trades | P/L | avg R |
  |---|---|---|---|
  | orb20_a | 7 | −$257 | −0.41 |
  | heat_fade_long | 30 | −$101 | −0.08 |
  | exhaustion_short | 4 | −$74 | −0.62 |
  | heat_fade_short | 19 | +$50 | −0.13 |

## Loss types (all 60 trades; one primary type each, multi-tags in `trades_autopsy.csv`)
Precedence: news/earnings, then stopped-then-reversed, wrong side after a big swing, gave back gains (MFE ≥ 0.5R), late hold (flattened red), never worked (MFE < 0.15R), small MFE then failed.

| primary type | orb20_a | heat_fade_short | heat_fade_long | exhaustion_short | all |
|---|---|---|---|---|---|
| news / earnings | **6** | 1 | 0 | 0 | 7 |
| stopped then reversed | 0 | 2 | 1 | 0 | 3 |
| wrong side after a big swing (≥3% move from the open; opposite 1R/1R would have won) | 0 | 0 | **8** | 1 | 9 |
| gave back gains | 0 | 1 | 1 | 1 | 3 |
| late hold (flattened red) | 0 | 0 | 6 | 2 | 8 |
| never worked | 0 | 2 | 1 | 0 | 3 |
| small MFE (0.15–0.5R) then failed | 0 | 4 | 0 | 0 | 4 |
| win | 1 | 9 | 13 | 0 | 23 |

- **Multi-tag counts** (one trade can carry several tags):
  - gave back gains: 10 (5 heat_fade_long, 2 orb, 2 heat_fade_short, 1 exhaustion)
  - never worked: 11
  - late hold: 12
  - wrong side after a swing: 12
  - news/earnings: 7
  - stopped then reversed: 3
- **The opposite side** (1R/1R from the same entry) would have hit its target first on 24 of the 37 losers. This is pure hindsight: in the population tests, no rule known at entry picks out those trades (below).
- **orb20_a lost entirely on news names.**
  - PENG and NEOG reported earnings the evening before, and the 4-day earnings blackout would have blocked both. That blackout was merged at 16:11 ET on 10-07, so it applies from 10-08.
  - HESM (Chevron stake sale and a 2027 EBITDA guide-down) and BKV (power-equipment contract) had material news that is not earnings. The blackout's earnings regex does not catch that kind of news.
  - On 10-06, CEG and LW were both inside earnings-window headlines.

## The owner's −1.5% question and the MarcoFlow "doesn't recover" statistic
- **MarcoFlow paper trades** (entries on or after 08-28, n = 2,123): once a trade was down ≥1%, only 6.1% closed green (n = 675). Down ≥0.5%: 13.9%.
  - **That figure is mechanical.** MarcoFlow's own stops sat at 0.8–1.5%, so a trade down 1% was usually stopped right there.
  - At signal level (fixed 1.5% stop, 4-hour horizon, n = 52,110): 27% of signals that went ≥1% against still finished positive. Their average finish was −0.73%, which is better than cutting at −1%. A tighter stop would have hurt there too.
- **MCF's own entries** (train and valid, before allocation, 1,990 trades):
  - Once down ≥1.5%, 23% still close green, and the average finish is −1.05% of notional. That is better than a −1.5% exit plus stop slippage, which is why the cap loses.
  - By setup:
    - exhaustion_short: down ≥1% → 45% still green, average **+0.12%**.
    - heat_fade_long: down ≥2% → 32% green.
    - heat_fade_short is the setup where deep drawdowns rarely recover: down ≥2% → 3.7% green. Even there the cap only breaks even, because those losses already sit near the stop.
- **Why HESM lost so much in percent:** orb20_a's stop is 0.5 × the 20-minute range. HESM's range was 11.9% wide (its 09:30 print at 36.05, then a −10% flush), so the stop sat 6.4% away.
  - The position was slot-capped at about $1,900, so the dollar loss is bounded by size, not by the stop. HESM lost $71 against the 0.25% risk cap of $250.
  - Wide ranges are not where orb20_a loses in the backtest. On train, ranges over 5% made +$4 to +$22 per trade, against −$5 to −$6.5 for 3–5% ranges. All 8 width filters fail (`orb_width_filters.csv`).

## The ten named 10-07 trades
R = fill-to-stop distance. MFE and MAE are measured from the fill while the trade was held. "Day MFE" runs to 15:55. The rule values are recomputed from SIP bars and match the journal's heat scores to 0.1.

**HESM (orb20_a short, 10:33, flattened 16:06): −0.59R, −$71. Never worked, on news.**
- **Why it fired:** a 20-minute range of 32.22–36.05 (the 36.05 is the opening print), rvol20 60×, 09:49 close below the open and below VWAP. It entered short on the 32.21 break.
- **Path:** MFE +0.03R (0.2%) after 1 minute. Then a slow grind higher: −0.72R (−4.6%) MAE, 33.39 at 15:00. At 15:55: −0.54R.
- **Exit alternatives:** none of +0.5R, +1R, breakeven or trail helps, because the trade never moved in favour. −0.55R. The 1.5% cap gives −0.26R.
- **Opposite side:** a long would have made about +0.5R by the close. No rule at entry pointed long: 5-minute RSI14 was 13, price −9.7% from the open and below VWAP, all bearish.
- **The owner's shorts at 09:46 and 10:26:** 09:46 → MFE +0.40R (10:33), close −0.18R. 10:26 → MFE +0.42R, close −0.16R. Both beat the live entry, which sold the low of the day at 10:33, but both still lose at 15:55. Neither time had a qualifying live rule: heat_fade_short's score was −84/−70 against a +11.3 threshold, and orb20 only fires on the range break.
- **What would have helped:** a news-day / range-shape guard. The range was set by one opening print. It is not testable without news history; see the backlog note.

**PENG (orb20_a long, 09:51, flattened 16:06): −0.51R, −$49. Earnings day.**
- **Why it fired:** a range of 09:30–09:49 that was 13% wide, rvol20 34×, the stock +11% from the open, RSI14 98, RSI5 100.
- **Path:** MFE +0.45R (+2.3%) at 09:56, which was the high of the day. MAE −0.78R (−4.0%). At 15:55: −0.46R.
- **Exit alternatives:** the 0.5R target was never reached, so the target and breakeven variants don't change the result (−0.47R).
- **Opposite side:** a short from 75.59 would have hit +1R at 13:33.
- **Hindsight check:** the heat short score on PENG was 68 (it fires at 11.3), but its 'below the open' gate was false because PENG was up 11%. So the rule could not trade it.
- **Population test:** "skip ORB longs with RSI14 > 85/90/95" and "skip |fromOpen| > 3/5/8%" all fail. Extended ORBs were profitable on train.
- **Was the trade supposed to last until 16:04?** No. orb20_a is designed to hold to 15:50/15:55 when neither stop nor target is hit, because its edge is the late-day drift. The extra 9–11 minutes was the flatten bug.
- **The real fix** is the earnings blackout, now live.

**BKV (orb20_a long, 10:17, stopped 12:47): −1.00R, −$50. News day, wrong side after the swing.**
- **Why it fired:** a 5.2% range, rvol20 21×, +3.7% from the open, RSI14 82.
- **Path:** MFE +0.21R after 2 minutes. 10:19 was the high of the day. Then a slow fade to the stop. The 1.5% cap gives −0.65R.
- **Opposite side:** a short would have reached +1R at 13:29.
- **Hindsight check:** no rule at entry favoured the short except "already extended", which fails in the population tests.

**ILMN (heat_fade_short, 10:25, stopped 10:55): −1.16R, −$34. Small MFE then failed.**
- **Why it fired:** score 22.3 against the 11.3 threshold. fromOpen −1.3%, +1.1% above VWAP, a momentum bounce of +2.1 from the 260.45 low at 09:40, RSI5 59. Short-term RSI4 was 88, which supported the short.
- **Path:** MFE +0.33R (0.5%) after 11 minutes, then a rally to the stop. Later in the day the stock ran to 276.2 (11:31).
- **Opposite side:** a long would have hit +1R at 10:55. The long score at entry was −21.7, so nothing pointed long.
- **Self-diagnosis:** this was a fade of a V-bounce that kept going. That is the setup's normal tail (it stops out 38–44% of the time in backtest).

**CHTR (heat_fade_short, 09:50, stopped 09:53): −1.27R, −$32. Stopped, then the original side worked.**
- **Why it fired:** score 18.4. The 09:45–49 bar was +0.4% over VWAP, pricePosition 0.81, RSI5 81, the stock −0.4% from the open.
- **The stop:** 09:55 was the high of the day at 111.59. Fill-slippage on the stop added 0.27R (111.54 against 111.135).
- **What happened next:** CHTR then fell 4.7%, to 106.02 at 13:48.
- **The owner's +1/+2 minute entries:**

  | entry | result | MFE |
  |---|---|---|
  | +1 minute | +1R target at 10:15 | 2.7R |
  | +2 minutes | +1R target at 10:12 | — |
  | at the 09:55 close (score 39.4) | +1R at 10:05 | — |

- **Population test:** 1/2/3-minute delays on all heat_fade_short entries do not help. Train d = −$34 / +$64 / −$234; valid +$59 / −$97 / −$169; all |t| < 1. The earlier nightly found 09:55 and 10:00 starts worse (−$24/−$40 on train).
- **Re-entry:** one re-entry after a stop while the score still qualifies happens 18 times on train (+0.10R) and 7 times on valid (−0.25R). It fails.
- **Self-diagnosis:** bad luck at the bar level. No confidence filter is supported.

**ALAB (heat_fade_short, 10:25, stopped 13:08): −1.02R, −$27. Gave back gains (a near-miss on the target).**
- **Why it fired:** score 15.4, barely over the threshold. fromOpen −1.0%, +1.0% above VWAP, RSI14 36, RSI5 53, RSI4 65. It was in an earnings window (headline 10-06).
- **Path:** MFE +1.02R in fill-R after 28 minutes (low 367.48). The target was 0.14R lower, at 366.68, because the fill was 0.45 worse than the signal close. Then a steady rally from 371 to the stop, and on to 388 at 15:43.
- **Exit alternatives:** +0.5R → +0.48R; breakeven at 0.5R → −0.02R; trail → +0.21R.
- **Opposite side:** a long would have hit +1R at 13:08.
- **The owner's 4-period RSI idea:** RSI4 was 65, so it would not have flagged this trade. As a layer ("only short if RSI5 > 50/60/70/80") it fails on valid: the kept trades do no better than random subsets (p 0.50–0.83).

**CHTR (heat_fade_long, 11:05, stopped 13:35): −1.10R, −$23. Gave back gains.**
- **Why it fired:** long score 66.8 against 57.5. Gap +1.6%, −2.6% from the open, RSI14 18, pricePosition 0.00 (the low of the 20-bar range).
- **Path:** MFE +0.75R (+0.9%) at 11:58, then down to the stop. The low of the day came at 13:48.
- **Exit alternatives:** +0.5R → +0.47R; breakeven at 0.5R → −0.05R.
- **"Two minutes later":** a long at 11:07 would have reached MFE +0.96R and closed −0.1R at 15:55, just short of the target.
- **Self-diagnosis:** the same symbol was traded short at 09:50 and long at 11:05, and both lost. The opposite-side block was already tested in the nightly and fails.

**RIOT (exhaustion_short, 13:20, flattened 16:06): −0.57R, −$20. Small MFE, late hold.**
- **Why it fired:** RSI5 90.9, +1.14% above the 5-minute SMA20, bearish divergence 1, at 13:15.
- **Path:** MFE +0.42R at 13:42. At 15:55: −0.40R.
- **The owner's 10:55 and 12:37 shorts:** MFE +0.79R at 11:26 and +0.57R at 13:00. Both close about −0.8R at 15:55, so they would have needed a target or trail.
- **Rule check at those times:** no live rule was true. exhaustion_short's mask was false at 10:55 (RSI5 42) and at 12:35 (RSI5 100, but no bearish divergence, SMA20 distance 0.75), and it is outside its 13:00–15:00 window anyway.

**NEOG (orb20_a short, 10:00, flattened 16:06): −0.20R, −$16. Earnings day; gave back gains.**
- **Why it fired:** a 10.7% range, rvol20 8×, −7.3% from the open.
- **Path:** MFE +0.85R (+3.6%) after 14 minutes, at the low of the day, 11.37 at 10:14. Then it chopped between 11.4 and 11.8 all day. At 15:55: +0.04R (+$3).
- **The late fill:** the 16:06 after-hours fill at 11.89 is what turned it red. The 15:59 close was 11.68.
- **Exit alternatives:** +0.5R → +0.45R; trail → +0.27R.
- **Population test:** stop-losses and profit locks on orb20_a fail on train and valid. Breakeven at 0.5R is −$692 on train, −$276 on valid.
- **Self-diagnosis:** an earnings day, now blocked by the blackout.

**WHR (exhaustion_short, 13:10, flattened 16:06): −0.68R, −$15. Gave back gains, late hold.**
- **Why it fired:** RSI5 100, +1.11% above SMA20, bearish divergence at 13:05.
- **Path:** MFE +0.79R (+0.93%) at about 15:06. Still +0.56R at 15:20. Then a closing rip from 28.76 to 29.20 after 15:25. At 15:55: −0.59R.
- **Exit alternatives:** +0.5R → +0.42R; breakeven at 0.5R → −0.13R; trail → +0.16R.
- **Population test:** earlier time exits for exhaustion_short (15:30 / 15:00) cut expectancy on train and valid:

  | exit | train | valid |
  |---|---|---|
  | current | +0.28R | +0.18R |
  | 15:30 | +0.24R | +0.13R |
  | 15:00 | +0.06R | +0.12R |

  A 0.5R target is −$1,418 on train. EXIT_STUDY says the same: holding longer pays for this setup.

## Concrete fix that survived train/valid (one finalist, for the lead to score once on the holdouts)
- **hfl_deep4: heat_fade_long only when the stock is ≥4% below today's open at the setup's first signal bar.**
  - Module: `research/oct7/autopsy/candidates/regime_5_deep4.py`. It is not wired into the config.
  - **What it does:** it removes 59% of trades and makes the rest better:

    | split | trades | $/trade | R/trade (original R) | win rate | day-clustered t | random-subset p |
    |---|---|---|---|---|---|---|
    | train | 205 (base 497) | $16.09 (base $6.95) | +0.274 (base +0.109) | 64% | 1.79 | 0.000 |
    | valid | 33 (base 116) | $8.12 (base $0.80) | +0.295 (base −0.025) | 61% | 1.48 | 0.020 |

  - **Plateau:** 3% / 4% / 5% are all positive on both splits. 6% is weak on valid (13 trades).
  - **Caveats:**
    1. The threshold family was chosen after I saw a fromOpen bucket table that included valid. That is selection contamination.
    2. The best day carries 41–47% of the kept-set total.
    3. Train total dollars are slightly lower than base ($3,298 against $3,456), because trades are dropped and the slots are not reused.
    4. **Live 10-06 points the other way.** The ten heat_fade_long trades with a ≥4% drop lost −$144, while the other twenty made +$43. That is two days, so not evidence.
    5. It is a rework of a live setup, so it is look 2 of the heat_fade_long lineage: it needs day-clustered t ≥ 1.5 on both locked holdouts.

## Recommendations for 10-08 (nothing below changes a setup or exit during market hours)
1. **Housekeeping, already shipped in PR #8:**
   - The earnings blackout. It would have removed PENG and NEOG, and the 10-06 earnings-window names CEG and LW.
   - The flatten fix.
   - **Verify at 15:55 today** that the flatten fires on time, and that the blackout source is "nasdaq" with complete = true. On 10-07 it fell back to Alpaca news (complete = false).
2. **Don't add the −1.5% stop, breakeven moves, trails or 0.5R targets.** All lose money on train or valid (78 configurations, plus EXIT_STUDY's 489).
3. **Backlog items:**
   - The hfl_deep4 finalist.
   - "News-day in-play guard for orb20_a": skip ORB on names with a same-day material headline, or where the range was set by the 09:30 print. It needs historical news to test.

## Configurations tried: 78 (all on sessions 2026-07-15..09-15; train ≤ 08-25, valid 08-26..09-15)

| family | configs | result |
|---|---|---|
| max-loss cap 1/1.5/2/2.5/3% × {4 setups, all 4} | 25 | fail. One gate pass (heat_fade_short 2%, +$13 on valid), off-plateau |
| give-back exits (breakeven 0.5/0.75, trail 0.5 after 0.5, target 0.5) × {4 setups, all 4} | 20 | fail |
| orb20_a range-width filters (%: 3/4/5/6/8; ATR: 0.5/0.75/1.0) | 8 | fail |
| heat_fade_short RSI5 layer (50/60/70/80) | 4 | fail |
| orb20_a RSI14 extreme in the trade's direction (85/90/95) | 3 | fail |
| orb20_a skip if \|fromOpen\| > 3/5/8% | 3 | fail |
| heat_fade_long skip fromOpen < −3/−4/−5/−6% | 4 | fail (it removes the best trades) |
| heat_fade_long keep only fromOpen ≤ −3/−4/−5/−6% | 4 | **finalist: −4%** (plateau −3 to −5) |
| heat_fade_short one re-entry after a stop (any score / stronger score) | 2 | fail (lab 5-minute outcome screen) |
| exhaustion_short time exit 15:30 / 15:00 | 2 | fail |
| heat_fade_short 1/2/3-minute entry delay | 3 | fail |

- The live-day what-ifs in `trades_autopsy.csv` (`wi_*`, `opp_*`, `r_at_1555`) are replays for diagnosis only, not tested configurations.

## Data and method
- **Journal:** a read-only copy of the primary paper journal.
- **Live-day bars:** SIP 1-minute bars fetched for 10-06 09:30 to 10-07 16:00 only, kept outside the repository.
- **No locked holdout data was read:** no date between 09-16 and 10-05, and nothing from `data/cache_q2`.
  - As a result, 10-06 rule values come from the journal.
  - Daily ATR for heat and lab setups is 4 × the journal R.
  - HESM's ATR is unknown.
- **Backtests:**
  - The production `simulate` and `Costs` (costs in, next-bar fills, stop first, gaps at the open).
  - Bars are loaded with `end=2026-09-16`.
  - Size = min($250 / per-share risk, $2,000 / price).
  - Results are in dollars and in the original R, to avoid the R-unit trap.
  - Entries come from `research/exits/data/signals.pkl` (before allocation, each setup scored on its own).
  - Entry features come from the setup-lab 5-minute frame (sessions before 09-16).

## Files
| file | contents |
|---|---|
| `autopsy.py` | per-trade replay of the 60 trades: MFE/MAE, what-ifs, opposite side, 15:55 close, entry features |
| `classify.py` | loss types and the flatten-bug table |
| `deep10.py` | the owner's alternative entry times; rule values around them |
| `test_fixes.py`, `analyse_fixes.py` | max-loss and exit families; recovery table; orb20_a width filters |
| `feature_filters.py`, `hfl_deep.py` | entry-feature filters; the finalist |
| `hfs_reentry.py` | heat_fade_short re-entry after a stop |
| `hfs_delay.py` | heat_fade_short entry delay |
| `exh_timeexit.py` | exhaustion_short earlier time exit |
| CSVs | `trades_autopsy.csv`, `owner_alternatives.csv`, `recovery_table.csv`, `fix_results.csv`, `orb_width_filters.csv`, `feature_filters.csv`, `hfl_deep.csv`, `hfs_reentry.csv`, `hfs_delay.csv` |
