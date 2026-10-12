# Testing 2 account: the CWT batch (owner-directed forward test, 2026-10-12)

*Educational only - not financial advice. Backtest numbers below are lab results on the open two-year history
(426 sessions; the locked block 2024-11-01..2025-02-28 is never loaded), costs in, R = 0.25 x daily ATR. Nothing here
is a paper or live result yet.*

## Failures first

- **None of these 30 setups passed the research gates.** Every CWT configuration failed: package A 566 of 566,
  package B 368 of 368, and package C has no intraday candidate (`../test_a/NOTES.md`, `../test_b/NOTES.md`,
  `../test_c/NOTES.md`).
- **24 of the 30 are negative after costs** on the open history.
- The 6 positive ones all have t below 1 (0.21-0.90). B1's positive rows rest on one day (2025-04-07), and A7's are
  positive only in down sessions.
- **Only 23 setups qualify under the selection rule. The other 7 are fills**, marked `[fill]`: the next eligible B3
  signals by expectancy, placed over the 4-per-family cap.
- **Package A engine artifact (found here; it affects the A7 T2 numbers).** Some A7 T2 shorts were entered with the
  signal close already above the structural stop. Package A then "stopped" them at a price below the entry and booked
  a gain: 22 of 589 trades (gap <= -10%) and 190 of 3,885 trades (gap <= -5%). The live module skips these signals,
  because the stop must sit beyond the entry. The honest live-tradable figures are **n 567, +0.131R** and **n 3,695,
  +0.032R**, not the scored +0.141 / +0.047. Other package A structural-exit (S) rows may carry the same artifact;
  the CWT-A owner should re-check `engine.sim` for stops on the wrong side of the entry.

The owner directed this account on 2026-10-12: a second paper account, "Testing 2", running "the best 30 setups found
from the CWT research, even if they are different variants of others", to collect forward data. This is that forward
test, not a promotion. Rule 20 (the Testing lifecycle) applies here as it does to Testing 1.

## How the 30 were chosen (`rank.py` -> `ranking.csv`)

The rule was fixed before choosing.

- **Pool:** every scored intraday configuration. Package A 566 + package B 368 + package C's 8 intraday rows =
  **942 configurations considered**.
- **Ranking:** by open-history expectancy after costs.
- **Eligibility:** a configuration counts only when all of these hold:
  - n >= 150;
  - the live LabStrategy can run it faithfully: a 5-minute bar-close entry in 09:50-15:00, a t1s1 / t05s1 / t1s05 or
    structural exit flat at 15:55, and only data the live frame carries (today's bars from 09:35, the prior-day
    high, low and close, daily ATR, the gap, and 60 prior 5-minute bars);
  - it is the best eligible exit and window of its signal. Two configurations with the same entry rule fire on the
    same symbol-day and would starve each other under one position per symbol.
- **Diversity:** at most 4 per family.
- **Result:** 175 configurations (35 distinct signals) are eligible, and the cap leaves **23**: B1 4, B2 4, B3 4 of
  16, B4 3, B5 4, A7 4. **Fewer than 30 qualify.** The 7 fills are the next B3 signals (-0.090..-0.096R), because no
  other family has eligible signals left.
- **Why the rest are out** (column `why_not` in `ranking.csv`):
  - data the live frame lacks:
    - rvol versus 20 prior sessions: A2, A8, A9, B6;
    - multi-day returns or 252-day highs: A1, B5-ret5, B7a;
    - 60-day beta and SPY's intraday path: A5, B7b;
  - stop-order or pre-09:50 entries: A3, A4, A6, the full-day A7 T2;
  - earnings-day versions, which the live earnings blackout blocks;
  - multi-day holds (package C);
  - n < 150.

## The 30

The windows are the full day (09:50-15:00) unless the best configuration of a signal was its guest-window version.
For A7, decisions start at 10:30, because its T1 fires only from 10:30 and the full-day T2 enters before 09:50.
Trades per day are open-history averages with one trade per symbol-day. `*` marks the artifact correction above.

| # | setup (code) | family | side | exit | window | n | exp R | t | trades/day | parity |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CWT04-backside-lh-a25-short | B1 CWT04 backside | short | t1s1 | 10:30-15:00 | 152 | +0.186 | 0.90 | 0.4 | exact (152) |
| 2 | CWT04-backside-lh-a15-short | B1 CWT04 backside | short | t1s1 | 10:30-15:00 | 1,212 | +0.142 | 0.77 | 2.8 | exact (1,212) |
| 3 | CWT04-backside-vwaptest-a25-short | B1 CWT04 backside | short | t1s1 | 09:50-15:00 | 238 | -0.171 | -1.28 | 0.6 | exact (238) |
| 4 | CWT04-backside-vwaptest-a15-short | B1 CWT04 backside | short | t1s05 | 09:50-15:00 | 2,026 | -0.172 | -3.74 | 4.8 | exact (2,026) |
| 5 | CWT13-vwapstretch-z075-long | B2 CWT13 VWAP stretch | long | t1s1 | 09:50-15:00 | 3,933 | -0.046 | -1.52 | 9.2 | exact (3,933) |
| 6 | CWT13-vwapstretch-z05-long | B2 CWT13 VWAP stretch | long | t05s1 | 11:00-15:00 | 18,135 | -0.080 | -5.12 | 42.6 | exact (18,135) |
| 7 | CWT13-vwapstretch-z075-short | B2 CWT13 VWAP stretch | short | t1s1 | 11:00-15:00 | 2,614 | -0.077 | -1.73 | 6.1 | exact (2,614) |
| 8 | CWT13-vwapstretch-z05-short | B2 CWT13 VWAP stretch | short | t1s1 | 11:00-15:00 | 16,165 | -0.069 | -2.84 | 37.9 | exact (16,165) |
| 9 | CWT14-failbrk-pdl-p10-long | B3 CWT14 failed break | long | t05s1 | 09:50-15:00 | 37,499 | -0.086 | -8.75 | 88.0 | exact (37,499) |
| 10 | CWT14-failbrk-pdl-p05-long | B3 CWT14 failed break | long | t05s1 | 09:50-15:00 | 66,875 | -0.088 | -10.07 | 157.0 | exact (66,875) |
| 11 | CWT14-failbrk-pdh-p10-lowvol-short | B3 CWT14 failed break | short | t05s1 | 09:50-15:00 | 19,479 | -0.089 | -9.45 | 45.7 | exact (19,479) |
| 12 | CWT14-failbrk-orl-p10-lowvol-long | B3 CWT14 failed break | long | t05s1 | 09:50-15:00 | 31,676 | -0.089 | -7.82 | 74.4 | exact (31,676) |
| 13 | CWT12-coil-k6-long | B4 CWT12 coil/flag | long | t1s05 | 09:50-11:30 | 16,735 | -0.070 | -4.68 | 39.3 | exact (16,735) |
| 14 | CWT12-coil-k4-long | B4 CWT12 coil/flag | long | t05s1 | 09:50-11:30 | 44,505 | -0.075 | -5.91 | 104.5 | exact (44,505) |
| 15 | CWT12-flag-s1-long | B4 CWT12 coil/flag | long | t05s1 | 09:50-15:00 | 1,435 | -0.074 | -2.75 | 3.4 | exact (1,435) |
| 16 | CWT05-flush-m075-v5-long | B5 CWT05 panic flush | long | t05s1 | 09:50-15:00 | 584 | -0.088 | -1.94 | 1.4 | exact (584) |
| 17 | CWT05-flush-m05-v5-long | B5 CWT05 panic flush | long | t05s1 | 09:50-15:00 | 1,247 | -0.111 | -3.28 | 2.9 | exact (1,247) |
| 18 | CWT05-flush-m05-v3-long | B5 CWT05 panic flush | long | t05s1 | 09:50-15:00 | 3,807 | -0.136 | -4.84 | 8.9 | exact (3,807) |
| 19 | CWT05-flush-m075-v3-long | B5 CWT05 panic flush | long | t05s1 | 09:50-15:00 | 1,409 | -0.154 | -4.00 | 3.3 | exact (1,409) |
| 20 | CWT09-gapdn-bounce-g10-lowerhalf-short | A7 CWT09 gap-down bounce | short | S | 10:30-15:00 | 589 | +0.141 * | 0.78 | 1.4 | 564/589 |
| 21 | CWT09-gapdn-bounce-g5-lowerhalf-short | A7 CWT09 gap-down bounce | short | S | 10:30-15:00 | 3,885 | +0.047 * | 0.40 | 9.1 | 3,671/3,885 |
| 22 | CWT09-gapdn-vwaploss-g10-short | A7 CWT09 gap-down bounce | short | S | 10:30-15:00 | 551 | +0.041 | 0.21 | 1.3 | 550/551 |
| 23 | CWT09-gapdn-vwaploss-g5-short | A7 CWT09 gap-down bounce | short | t1s05 | 10:30-15:00 | 3,663 | -0.031 | -0.42 | 8.6 | 3,657/3,663 |
| 24 | CWT14-failbrk-orl-p05-lowvol-long [fill] | B3 CWT14 failed break | long | t05s1 | 09:50-15:00 | 74,014 | -0.090 | -9.35 | 173.7 | exact (74,014) |
| 25 | CWT14-failbrk-orl-p10-long [fill] | B3 CWT14 failed break | long | t05s1 | 09:50-12:00 | 39,989 | -0.091 | -7.05 | 93.9 | exact (39,989) |
| 26 | CWT14-failbrk-orl-p05-long [fill] | B3 CWT14 failed break | long | t05s1 | 09:50-15:00 | 105,023 | -0.093 | -10.05 | 246.5 | exact (105,023) |
| 27 | CWT14-failbrk-pdl-p10-lowvol-long [fill] | B3 CWT14 failed break | long | t05s1 | 09:50-15:00 | 20,080 | -0.095 | -8.85 | 47.1 | exact (20,080) |
| 28 | CWT14-failbrk-pdh-p05-lowvol-short [fill] | B3 CWT14 failed break | short | t05s1 | 09:50-15:00 | 43,876 | -0.095 | -11.57 | 103.0 | exact (43,876) |
| 29 | CWT14-failbrk-pdl-p05-lowvol-long [fill] | B3 CWT14 failed break | long | t05s1 | 09:50-15:00 | 44,026 | -0.096 | -10.03 | 103.3 | exact (44,026) |
| 30 | CWT14-failbrk-pdh-p10-short [fill] | B3 CWT14 failed break | short | t05s1 | 09:50-12:00 | 30,261 | -0.096 | -10.13 | 71.0 | exact (30,261) |

## Parity (`verify.json`, `spot_live.json`)

- **Package B (26 setups), on the lab frames: exact, trade for trade, all 26.** Same symbol, date and entry bar;
  0 missing; 0 extra; 626,995 trades. `verify.py` runs each module's mask on the live-like frame: the lab rows
  09:50-15:00 plus the 09:35-09:45 rows that package B rebuilt from the 1-minute cache. It then keeps the first hit
  in the YAML window, exactly as `LabStrategy.generate` does.
  - One detail was needed for exactness: package B had no volumeRatio / vol_climax on its 09:35-09:45 rows, so the
    modules blank those two columns before 09:50. Live frames do carry them.
- **Package B, live path (`spot_live.py`).** Real 1-minute bars go through the live `LabStrategy.generate`: heat_frame
  on today's bars plus the 60 prior 5-minute bars, with the ctx levels. 12 scored trades and 12 no-trade symbol-days
  per setup: **621 of 622 checks agree**. The one miss is CSX on 2025-07-03, a half-day session with prints after the
  13:00 close.
- **A7 (4 setups), live path on every candidate day (`verify_a.py`).** Package A ran on its own 1-minute engine, so
  the live `LabStrategy.generate` was run on raw 1-minute bars for all 4,164 candidate symbol-days: package A's
  universe and earnings filter, with gap <= -5%.
  - T1: 550 of 551 and 3,657 of 3,663 trades match. The rest are 5-minute bar shifts from 1-minute data gaps.
  - T2: 564 of 589 and 3,671 of 3,885 match. Every other T2 difference is either a bar shift (3 / 21) or one of the
    artifact trades (22 / 190), which live skips by design.
  - No extra live signals, and the structural stop equals package A's on every matched trade.

## Live mechanics and playing time

- **Structural exit (A7 `S`).** This is a small opt-in extension to `mcf/strategies/setups.py` LabStrategy:
  - a module with `GEOM = "S"` supplies `stop_price(f, i)`, here the 09:30-10:30 high;
  - there is no target, and the trade is flat at 15:55;
  - a signal whose stop is not beyond the entry is skipped;
  - every other module is unchanged.
  - Sizing uses the actual stop distance, so live R for these trades is the structural risk, not 0.25 x ATR.
- **Universe.** `min_adv` is the scored floor: package B $95M, package A $1M. The live universe tiers still apply
  (core >= $5M; the extended tier only when in play; `min_price` 5), so A7 trades fewer small names live than it did
  in the lab.
- **Playing time.**
  - One position per symbol across setups; `setup_order` lists the narrowest setups (fewest trades per day) first, so
    subsets are not starved by supersets.
  - `max_positions_per_strategy: 25` (Testing 1 uses 150), so the busy B3/B4 setups (40-250 signals a day) cannot
    fill the 400 slots.
  - Nested variants (a2.5 inside a1.5, z0.75 inside z0.5, gap 10% inside 5%, low-volume inside any-volume) share
    symbol-days. Rule 20 reporting counts the signals each one loses to a higher-priority setup.
- **Caution.** With this many negative-expectancy setups, the 60R daily loss stop may end some sessions early. The
  playing-time monitor reports this as "daily loss" skips.

## Drops

- **Drop 1** (merged 2026-10-12, PR #40, live on 2026-10-12 by owner override): the 19 package B setups.
- **Drop 2** (after the 2026-10-12 close): the A7 x4 with the LabStrategy structural exit, and the 7 B3 fills.

## Files

- `selection.py`: the batch.
- `build.py`: writes the modules, `config/account_testing2.yaml` and the names.
- `cwt_live_lib.py`: the signal code, ports of the scored rules.
- `<NAME>.py`: one LabStrategy module per setup.
- `verify.py` / `verify_a.py` -> `verify.json`: parity.
- `spot_live.py` -> `spot_live.json`: the live-path check.
- `rank.py` -> `ranking.csv`: all 942 configurations, with eligibility, choice and the fill flag.
