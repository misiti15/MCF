# Testing 2 account: the CWT batch (owner-directed forward test, 2026-10-12)

*Educational only - not financial advice. Backtest numbers below are lab results on the open two-year history
(locked block 2024-11-01..2025-02-28 never loaded), costs in. Nothing here is a paper or live result yet.*

## Failures first

**None of these setups passed the research gates.** Every CWT configuration failed: package A 566 of 566, package B
368 of 368, package C has no intraday candidate (`../test_a/NOTES.md`, `../test_b/NOTES.md`, `../test_c/NOTES.md`).
Most of the chosen setups are **negative after costs** on the open history (17 of 19 in drop 1; the two positive ones
have t below 1 and rest on a few sessions - B1's positive rows are carried by 2025-04-07). The owner directed
(2026-10-12) a second paper account, "Testing 2", to run "the best 30 setups found from the CWT research, even if they
are different variants of others" to collect forward data. This is that forward test, not a promotion. Rule 20
(Testing lifecycle) applies to this account as to Testing 1.

## How the 30 were chosen (fixed before choosing; `rank.py` -> `ranking.csv`)

- Pool: every scored intraday configuration - package A 566, package B 368, package C intraday rows 8 = **942
  configurations considered**.
- Ranked by open-history expectancy after costs (R = 0.25 x daily ATR).
- Eligible only when: n >= 150; the live LabStrategy can run it faithfully (5-minute bar-close entries 09:50-15:00,
  fixed t1s1 / t05s1 / t1s05 exit flat at 15:55, only data the live frame carries); best eligible exit/window per
  signal (two configurations with the same entry rule fire on the same symbol-day and would starve each other under
  one position per symbol); at most 4 per family.
- Result: **151 configurations / 31 distinct signals are eligible, and the 4-per-family cap leaves 19** (B1 4, B2 4,
  B3 4 of 16, B4 3, B5 4). So **fewer than 30 qualify under the rule**. Drop 2 fills the remaining 11, each clearly
  labelled as a fill (see the plan below).
- Why the rest are out (column `why_not` in `ranking.csv`): structural exits (stop at a chart level, hold to the
  close) that LabStrategy cannot do yet; data the live frame lacks (rvol versus 20 prior sessions: A2, A8, A9, B6;
  multi-day returns / 252-day highs: A1, B5-ret5, B7a; 60-day beta and SPY's path: A5, B7b); stop-order or pre-09:50
  entries (A3, A4, A6); earnings-day versions (blocked live by the earnings blackout); n < 150.

## Drop 1: 19 setups, live parity verified (package B)

| setup (code) | family | side | exit | window | open-history n | exp R | t | trades/day |
|---|---|---|---|---|---|---|---|---|
| CWT04-backside-lh-a25-short | B1 CWT04 backside lower-high | short | t1s1 | 10:30-15:00 | 152 | +0.186 | 0.90 | 0.36 |
| CWT04-backside-lh-a15-short | B1 | short | t1s1 | 10:30-15:00 | 1,212 | +0.142 | 0.77 | 2.85 |
| CWT13-vwapstretch-z075-long | B2 CWT13 stretched from VWAP | long | t1s1 | 09:50-15:00 | 3,933 | -0.046 | -1.52 | 9.2 |
| CWT13-vwapstretch-z05-short | B2 | short | t1s1 | 11:00-15:00 | 16,165 | -0.069 | -2.84 | 37.9 |
| CWT12-coil-k6-long | B4 CWT12 coil / flag | long | t1s05 | 09:50-11:30 | 16,735 | -0.070 | -4.68 | 39.3 |
| CWT12-flag-s1-long | B4 | long | t05s1 | 09:50-15:00 | 1,435 | -0.074 | -2.75 | 3.4 |
| CWT12-coil-k4-long | B4 | long | t05s1 | 09:50-11:30 | 44,505 | -0.075 | -5.91 | 104.5 |
| CWT13-vwapstretch-z075-short | B2 | short | t1s1 | 11:00-15:00 | 2,614 | -0.077 | -1.73 | 6.1 |
| CWT13-vwapstretch-z05-long | B2 | long | t05s1 | 11:00-15:00 | 18,135 | -0.080 | -5.12 | 42.6 |
| CWT14-failbrk-pdl-p10-long | B3 CWT14 failed breakout | long | t05s1 | 09:50-15:00 | 37,499 | -0.086 | -8.75 | 88.0 |
| CWT05-flush-m075-v5-long | B5 CWT05 panic flush V | long | t05s1 | 09:50-15:00 | 584 | -0.088 | -1.94 | 1.4 |
| CWT14-failbrk-pdl-p05-long | B3 | long | t05s1 | 09:50-15:00 | 66,875 | -0.088 | -10.07 | 157.0 |
| CWT14-failbrk-pdh-p10-lowvol-short | B3 | short | t05s1 | 09:50-15:00 | 19,479 | -0.089 | -9.45 | 45.7 |
| CWT14-failbrk-orl-p10-lowvol-long | B3 | long | t05s1 | 09:50-15:00 | 31,676 | -0.089 | -7.82 | 74.4 |
| CWT05-flush-m05-v5-long | B5 | long | t05s1 | 09:50-15:00 | 1,247 | -0.111 | -3.28 | 2.9 |
| CWT05-flush-m05-v3-long | B5 | long | t05s1 | 09:50-15:00 | 3,807 | -0.136 | -4.84 | 8.9 |
| CWT05-flush-m075-v3-long | B5 | long | t05s1 | 09:50-15:00 | 1,409 | -0.154 | -4.00 | 3.3 |
| CWT04-backside-vwaptest-a25-short | B1 | short | t1s1 | 09:50-15:00 | 238 | -0.171 | -1.28 | 0.56 |
| CWT04-backside-vwaptest-a15-short | B1 | short | t1s05 | 09:50-15:00 | 2,026 | -0.172 | -3.74 | 4.8 |

Windows: full day 09:50-15:00 unless the best configuration of that signal was the guest-window version (then the
guest window, as scored). Trades/day are open-history averages over 426 sessions with one trade per symbol-day.

### Parity
- `verify.py` -> `verify.json`: each module's `mask` on the live-like frames (lab frame rows 09:50-15:00 plus the
  09:35-09:45 rows package B rebuilt from the 1-minute cache), first hit per symbol-day inside the YAML window exactly
  as `LabStrategy.generate`, compared with the scored trades (`../test_b/data/trades.npz`). **19 of 19 match trade
  for trade** (same symbol, date and entry bar; 0 missing, 0 extra; 269,726 trades in total); the expectancy over the
  matched trades equals the scored one.
- One deliberate detail: package B had no volumeRatio / vol_climax on its 09:35-09:45 rows, so the modules blank
  those two columns before 09:50 (live frames have them) to reproduce the scored version exactly.
- `spot_live.py` -> `spot_live.json`: real 1-minute bars through the live `LabStrategy.generate` (heat_frame on
  today's bars + 60 prior 5-minute bars, ctx levels): random scored trades must fire on the same bar, random
  symbol-days without a trade must not fire.

### Playing time
- One position per symbol across setups; `setup_order` lists the narrowest setups (fewest trades/day) first.
- `max_positions_per_strategy: 25` (Testing 1 uses 150) so the busy setups (B3, B4 coil: 40-157 signals/day) cannot
  fill the 400 slots and every setup gets entries.
- Nested variants (e.g. a2.5 inside a1.5, z0.75 inside z0.5) share symbol-days; the narrower one is ordered first, and
  rule 20 reporting counts the signals each one lost to a higher-priority setup.
- Caution: with this many negative-expectancy setups the account's 60R daily loss stop may end some sessions early;
  the playing-time monitor will show it ("daily loss" skips).

## Drop 2 plan (after the close): 11 more to reach 30, labelled as fills
1. **A7 CWT09 bad-news gap-down bounce short, outside the earnings blackout** (4 signals: gap <= -5% / -10% x T1 / T2,
   decision bars from 10:30). Their best exit is the structural one (stop at the first-hour high, hold to 15:55;
   T2 gap <= -10% +0.141R n 589, the highest-ranked eligible-by-data configuration in all of CWT) - this needs a small
   opt-in LabStrategy extension (module-supplied stop, no target) and a parity check of the live path on the package A
   trades. Universe: adv20 >= $1M in package A versus the live universe tiers; parity is reported on the live-tradable
   subset.
2. **B3 beyond the family cap** (the next 7 B3 signals by expectancy, -0.091..-0.100R), labelled "fill: over the
   4-per-family cap" because no other family has eligible signals left.

## Files
- `selection.py` (the batch), `build.py` (writes the modules), `cwt_live_lib.py` (signal code: ports of the scored
  kernels), `<NAME>.py` (one LabStrategy module per setup), `verify.py` / `verify.json` (parity), `spot_live.py` /
  `spot_live.json` (live path), `rank.py` / `ranking.csv` (all 942 configurations, eligibility, choice).
- `config/account_testing2.yaml`, `config/setup_names.yaml` (+ `docs/live/setup_names.json`).
