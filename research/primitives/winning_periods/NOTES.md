# Winning periods: can we keep the good stretches? (key `winning_periods`, 2026-10-07)

*Educational only - not financial advice. Backtest results, not paper or live results.*

**Data:** the production Backtester (`mcf.backtest.engine`, current `config/default.yaml`, 5 live setups) on data/cache
sessions 2026-07-15..09-15. Loaded with end <= 2026-09-16 and nothing locked was read.
**Split:** train = 07-15..08-25 (30 days), valid = 08-26..09-15 (14 days). 2,063 trades.
**Costs:** production costs are in every trade (1c + 1 bps per side, +2c on stops, 3c on extended-tier names). Every
forced flatten pays market slippage.
**Configurations tried:** 145 rules in total.
- 64 portfolio rules
- 1 per-setup window rule (picked on train)
- 35 per-setup concurrency caps
- 45 sleeve-level locks or give-backs

Separately, ~100 descriptive feature-quintile tables were looked at.

## Failures first
- **No rule passed the gate.** Each finalist needed train > 0, valid > 0, valid day-t >= 1.5, a positive plateau and
  a beat on the baseline (no rule). None met all of them.
- **Profit locks (`R-lock-X`, $50-600 and 1-8R):** all 13 lowered train P/L, by between -$3.4k and -$7.4k.
- **Give-back stops (`R-giveback-A-G`):** all 12 lowered train P/L. The best on valid was 200/50%, at +$272 with t 1.30,
  but it cost -$5.3k on train.
- **Stop new entries after +X (`R-nonew-X`):** all 7 negative on train.
- **Daily loss stop and clock stops:** all negative on train.
- **Time stops:** 11 of 12 were negative. A trade's MFE can come late: the median time to MFE is 52-56 min for orb20_a,
  heat_fade_long and exhaustion_short, and 19 min for heat_fade_short.
  - `R-timestop-120-0.5` was the only positive one: train +$584 (t 0.93), valid +$27 (t 0.12).
  - Its neighbours (90 min) are negative, so it is not on a plateau.
- **Per-setup 30-minute windows:** dropping the cells that were negative on train would have removed +$338 of valid
  P/L (86 trades, +0.10R each). The windows do not persist.
  - Example: heat_fade_long 12:00 was +0.49R (t 2.5) on train and -0.30R on valid.
  - Example: heat_fade_long 13:00 was -0.25R (t -2.2) on train and +0.14R on valid.
  - This supports the owner's doubt about narrow time windows.
- **Per-setup caps:** for heat_fade_short, a cap lifted train but lowered valid at every N. For the other setups, caps
  cut the best days.
- **Cold or hot setup stops** (stop a setup after its closed trades reach -K or +K R that day): negative on train.
- **Near-miss, `R-hfs-bank`:** heat_fade_short's sleeve is flattened, and blocked for the rest of the day, once its
  marked P/L gives back 30% from a peak of at least $200.
  - Train: +$2,733 (t 1.27).
  - Valid: +$37 (t 1.0). It triggered on only one valid day.
  - All 9 heat_fade_short sleeve variants are positive on train, but valid ranges from -$355 to +$63.
  - It fails the valid gate. Forward data is needed, so it is a backlog candidate only.

## What the data says (descriptive)
- **Green at some point, red at the close:** 15 of 44 days (34%). Of the days that peaked above +$200, 5 of 28 (18%)
  ended red.
  - Mean peak: $443. Mean close: $227.
  - The sum of daily peaks was $19.5k, against $10.0k actual. **That gap is hindsight:** the median peak time is 14:12,
    and no causal trigger captured it.
- **When the day peaks:**
  - 12 days peaked in the first hour (by 10:30), during the heat_fade_short window. 9 of them closed red.
  - On the 32 late-peak days, the mean close was +$510 on train and +$163 on valid.
  - You cannot know at 10:30 that the high is in.
- **A green morning does not predict a red afternoon.** P/L at 11:05 > 0 was followed by an afternoon mean of +$284
  (29 days), against +$43 after a red morning (15 days).
  - The 10-06 pattern (heat_fade_long losing after a green morning) appears on valid: -$22/day (n=10) against +$60
    (n=4).
  - It reverses on train: +$166 (n=19) against +$23 (n=11). It is not a rule.
- **What made the winning stretches:**
  - Many-signal, high-dispersion days. The Spearman correlation of daily P/L with trades per day is 0.35. The
    top-quartile trade-count days averaged +$643, against +$88 on other days.
  - The top 3 days (07-15, 07-17, 07-29) made $6,115 of the $9,979 total (61%).
  - exhaustion_short (+0.55R, n=154) and heat_fade_long (+0.25R, n=141) carried those days.
  - The market's direction from the open barely matters: Spearman 0.07.
- **Easiest metrics to track:**
  1. **The setup's own closed R today.**
     - heat_fade_long trades taken after its earlier trades net negative did better: +0.41R train (n=98), +0.27R
       valid (n=10). So cold-stops hurt.
     - heat_fade_short trades taken after its sleeve was already net positive did worse: -0.15R train (n=103),
       +0.006R valid (n=29). That is the basis of the near-miss above.
  2. **Crowding.** heat_fade_short entries with more than 11 same-side positions already open: -0.30R train, -0.08R
     valid.
  3. **Breadth with the trade's side** (share of the universe up from the open):
     - heat_fade_long is better when breadth is against it on train, but this is flat on valid.
     - It is not robust.

## Caveats
- **The live setups were selected on these same dates** (in the heat study and swarm train/valid), so their
  expectancy here is in-sample and inflated.
  - Train: exhaustion_short +0.27R, heat_fade_long +0.11R.
  - Valid: heat_fade_long -0.06R (n=108).
  - The rule comparisons are relative, but they inherit this bias.
- **Valid has only 14 days**, and few of them trigger the rules.
- **Freed slots are not re-used** in the rule simulations. Slots (160) rarely bind.
- **The earnings blackout is live-only.** The backtest does not apply it.
- **10-06 is used only descriptively.** It is live data inside the locked period.

## Files
| File | Contents |
|---|---|
| `run_bt.py`, `trades_live_setups.csv` | Engine trade list |
| `paths.py`, `trades_enriched.csv`, `day_paths.csv` | Time to MFE, minute paths, and the portfolio's intraday path per day |
| `analyse.py`, `rules_grid.csv`, `tod_by_setup.csv`, `setup_summary.csv`, `features_good_vs_bad.csv`, `feature_quintiles.csv`, `day_summary.csv`, `results.json` | Rules grid, time of day, setup summary, features and day shapes |
| `extra.py`, `caps_grid.csv`, `results_extra.json` | Caps, morning vs afternoon, concentration |
| `sleeve.py`, `sleeve_grid.csv` | Sleeve-level locks and give-backs |
