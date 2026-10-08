# Nightly 2026-10-07: three backlog hypotheses (backtest)

*Educational only — not financial advice. Backtest results, not paper or live results.*

**Verdict: all 9 configurations fail the gate. Nothing is proposed. `config/default.yaml` is unchanged.**

## Setup
- **Engine:** the production `Backtester` (`simulate` + `allocate`) with `config/default.yaml` and `build_strategies`.
  - Costs are included: 1 bp + 1c/share per side, 2c extra on stops, 3c on extended-tier names. Entries fill on the next bar, the stop is taken first when stop and target fall in the same bar, and gaps fill at the open.
- **Data:** `data/cache` read with `end='2026-09-16'`. No date on or after 2026-09-16 was read, and neither was `data/cache_q2`. No `MCF_*` environment variables were set.
  - Bars from 06-15 to 07-14 (the start of the cache) were used only to warm up prior-day statistics: ATR, ADV, rvol profile and the prior 5-minute bars.
  - Trades were counted on sessions 2026-07-15 to 09-15. **Train** runs to 08-25 (30 days) and **valid** runs from 08-26 to 09-15 (14 days).
- **Method:** `collect.py` saves every setup's candidate trades before allocation, with the variants added as separately named strategies. `analyse.py` then runs the production allocator once for each configuration.
  - Each variant replaces only its own setup's candidates.
  - For opposite_side_block, the rule is applied as a post-filter on the allocated base trade list, in time order.
- **Gate:** the variant needs higher portfolio total R and higher expectancy than base on train and on valid.
  - The valid day-clustered t of the paired daily difference must be at least 1.0.
  - The difference with the best day removed must stay above 0 on train and on valid.
- **Configurations tried: 9**, plus base.
  - At p = 0.05 about 0.45 false positives would be expected by chance. None passed.
  - No locked holdout was scored, because there was no finalist.

### A finding on the engine (housekeeping, not a strategy change)
- The `strategies.<setup>.window` setting for `heat` and `lab` setups is **only a live pre-filter**.
  - In the backtester, a full-day context is always evaluated. The time window that actually applies is the one hard-coded in the formula module: `regime_score(..., 950, 1030, ...)` in `research/heat/candidates/regime_9.py`, and `tod >= 1300 & tod <= 1500` in `volume_flip_1.py`.
  - So changing `window` in YAML would change live trading but **not** the backtest, and the two would drift apart.
  - For this study the window variants were made in the score and mask instead (`HeatStart` and `LabEnd` in `collect.py`).
  - Any future window change must be applied in both places.

## Failures (all configurations)

Portfolio = all live setups after allocation. "d" is the variant minus base, paired by day across all days in the split. Ex-best = the difference with the best day removed.

| config | split | n | exp R (se) | WR | total R | d total | d t (day) | d ex-best |
|---|---|---|---|---|---|---|---|---|
| **base** | train | 1626 | +0.109 (0.022) | 55.3% | +177.5 | | | |
| **base** | valid | 437 | +0.076 (0.042) | 53.5% | +33.0 | | | |
| hfs_start0955 | train | 1520 | +0.101 | 54.9% | +153.6 | −23.8 | −1.00 | −28.7 |
| hfs_start0955 | valid | 414 | +0.052 | 52.2% | +21.6 | −11.4 | −0.96 | −17.3 |
| hfs_start1000 | train | 1477 | +0.093 | 54.4% | +137.8 | −39.7 | −1.77 | −43.1 |
| hfs_start1000 | valid | 403 | +0.041 | 51.9% | +16.7 | −16.3 | −1.44 | −19.5 |
| hfs_range_k0.15 | train | 1365 | +0.101 | 54.7% | +137.8 | −39.7 | −1.73 | −47.0 |
| hfs_range_k0.15 | valid | 334 | +0.053 | 51.5% | +17.8 | −15.2 | −1.32 | −18.8 |
| hfs_range_k0.25 | train | 1559 | +0.104 | 55.0% | +162.1 | −15.4 | −2.05 | −17.5 |
| hfs_range_k0.25 | valid | 405 | +0.065 | 52.8% | +26.4 | −6.6 | −1.09 | −10.7 |
| opposite_side_block | train | 1608 | +0.109 | 55.3% | +174.6 | −2.9 | −0.69 | −4.0 |
| opposite_side_block | valid | 433 | +0.074 | 53.3% | +32.2 | −0.8 | −0.47 | −1.8 |
| orb20a_until1030 | train | 1607 | +0.108 | 55.3% | +173.1 | −4.4 | −0.89 | −5.8 |
| orb20a_until1030 | valid | 428 | +0.075 | 53.7% | +32.1 | −0.9 | −0.35 | −2.1 |
| orb20a_until1100 | train | 1617 | +0.109 | 55.3% | +177.0 | −0.5 | −0.16 | −1.8 |
| orb20a_until1100 | valid | 433 | +0.074 | 53.6% | +32.2 | −0.8 | −0.49 | −1.8 |
| exh_end1400 | train | 1474 | +0.084 | 53.5% | +123.4 | −54.0 | −1.07 | −60.6 |
| exh_end1400 | valid | 426 | +0.080 | 53.8% | +34.1 | +1.1 | +0.47 | −0.03 |
| exh_end1430 | train | 1548 | +0.084 | 53.7% | +130.8 | −46.7 | −0.97 | −49.8 |
| exh_end1430 | valid | 432 | +0.075 | 53.7% | +32.4 | −0.6 | −0.88 | −0.8 |

### H1 nl-1007-0950-stopout (heat_fade_short): reject

Results for the setup on its own:

| config | train n / exp / WR / total | valid n / exp / WR / total |
|---|---|---|
| base | 520 / +0.047 / 53.8% / +24.5 | 141 / +0.180 / 61.0% / +25.4 |
| start 09:55 | 412 / +0.004 / 51.9% / +1.6 | 117 / +0.121 / 58.1% / +14.1 |
| start 10:00 | 367 / −0.038 / 49.9% / −13.9 | 105 / +0.087 / 57.1% / +9.2 |
| skip if 09:45-49 range > 0.15 ATR | 252 / −0.061 / 48.8% / −15.4 | 35 / +0.300 / 68.6% / +10.5 |
| skip if 09:45-49 range > 0.25 ATR | 452 / +0.020 / 52.4% / +9.0 | 108 / +0.175 / 61.1% / +18.9 |

- The premise does not hold in this window. heat_fade_short's earliest entries are its best, not its worst:

  | entries | train | valid |
  |---|---|---|
  | 09:50-10:00 | n 380, +0.075R, WR 55%, stopped 38%, median hold 37 min | n 96, +0.207R, stopped 35% |
  | 10:01 and later | n 140, −0.030R, stopped 44% | n 45, +0.124R |

  The 10-06 stop-outs (CHTR, AMD, INTU, SAP) look like a bad day rather than a pattern in this window.
- The range filter is defined as max high minus min low over the 09:45-09:49 one-minute bars, divided by the prior-day ATR(14). Its median across candidate name-days is 0.16 ATR (p25 0.12, p90 0.28), so k = 0.15 drops more than half the names.
- At k = 0.15, valid expectancy rises (+0.30R), but only on n = 35, and both train and total R get worse.
- No random-drop control was run for H1b, because the filter already loses to base.

### H2 nl-1007-opposite-side: reject

- The rule drops 18 trades in train (heat_fade_long 11, exhaustion_short 4, intraday_momentum 3) and 4 in valid (heat_fade_long 3, orb20_a 1).
- The dropped trades were winners on average: +0.16R in train and +0.20R in valid. Blocking them costs −2.9R in train and −0.8R in valid.
- Random-drop control (the same number of trades dropped at random within each setup and split, 2,000 runs): the rule's result sits at the 41st percentile in train and the 29th in valid. It is no better than dropping trades at random.
- Caveat: the rule is a post-filter. It does not re-allocate the slot a dropped trade frees, which has almost no effect with 160 slots.

### H3 nl-1007-late-holds: reject

- **orb20_a entry_until:**
  - 10:30: setup train 190 trades, +0.032R, total +6.1; valid 92, +0.047R, total +4.3.
  - 11:00: train 200, +0.050R, total +10.0; valid 97, +0.045R, total +4.4.
  - Base: train 209, +0.050R, total +10.5; valid 101, +0.051R, total +5.2.
  - Both cutoffs are slightly worse.
- **exhaustion_short window end:**
  - 14:00: train 181 trades, +0.201R, total +36.3; valid 40, +0.218R, total +8.7.
  - 14:30: train 255, +0.171R, total +43.6; valid 46, +0.152R, total +7.0.
  - Base: train 333, +0.271R, total +90.3; valid 51, +0.149R, total +7.6.
  - The late signals (14:00-15:00) carry most of the train R.
  - 14:00 is marginally better on valid (+1.1R, t 0.47), but its ex-best-day difference is −0.03 and train is −54R, so it is rejected.
- Trades still open at the cutoff did **not** lose on average in this window (see the next section). The 10-07 losses (6 open trades, −$178) were a single day.

## Context: base trades still open at the time exit (15:55; orb20_a exits at 15:50)

| setup | train share open / mean R when open (mean R otherwise) | valid share open / mean R when open (mean R otherwise) |
|---|---|---|
| heat_fade_short | 74/520 = 14.2% / +0.083 (+0.041) | 14/141 = 9.9% / +0.212 (+0.177) |
| heat_fade_long | 152/484 = 31.4% / −0.097 (+0.205) | 36/108 = 33.3% / +0.072 (−0.125) |
| exhaustion_short | 139/333 = 41.7% / +0.126 (+0.376) | 18/51 = 35.3% / +0.148 (+0.150) |
| orb20_a (15:50) | 84/209 = 40.2% / +0.129 (−0.003) | 50/101 = 49.5% / +0.136 (−0.031) |
| intraday_momentum | 80/80 = 100% / −0.014 | 35/36 = 97.2% / +0.065 (one stop, −1.08) |

- intraday_momentum enters at 15:30 by design, so its time exits are expected.
- heat_fade_long's train time exits are the only negative group (−0.097R). On valid they are positive.
- Exits for orb20_a and exhaustion_short were not tested here and would be a separate idea.

## Files
- `collect.py`: collects candidate trades with the production engine. Run as `python research/nightly/2026-10-07/collect.py heat|core CHUNK N`.
- `analyse.py`: allocates and scores each configuration and writes:
  - `results.csv`: every configuration by split and scope
  - `summary.json`: gate results, the H2 control and range-ratio quantiles
  - `late_holds.csv`
  - `hfs_buckets.csv`
  - `trades_<config>.csv`
- `cands_*.pkl`: the candidate trades before allocation (sessions 07-15 to 09-15).
- Runtime: about 35 minutes on 4 cores (4 heat chunks plus 1 core run).
