# refire1014: same-setup refire on the two-year history

*Educational only - not financial advice. Lab results on the open two-year history only; nothing here is a paper or
live result. Paper, backtest and live results are labelled separately (rule 7).*

Owner (2026-10-14): "If each setup has multiple opportunities in a day, unless it's specifically designed to only fire
during certain windows, let them go in as much as possible."

**Section 1 (pre-declaration) was written on 2026-10-14 before any configuration of this study was scored.**
Results go in section 2 and may not change section 1.

## 1. Pre-declaration

### 1.1 What is measured
`LabStrategy` (mcf/strategies/setups.py) fires a lab setup on the FIRST qualifying 5-minute decision bar of a
symbol-day. The new opt-in mode `refire` emits a signal on every qualifying decision bar inside the setup's window,
except that a signal blocks the next `refire_cooldown` decision bars of that setup on that symbol
(`refire_select`, shared by the live code and this scan). Live, same-setup re-entry on a new signal bar is already on
(`live.same_setup_reentry: true`, lot cap 3 per symbol), so refire is what would add trades.

Variants per setup (4 configurations per setup, all counted):
- `first`: first qualifying bar per symbol-day (current behaviour).
- `cd1`, `cd3`, `cd6`: refire with cooldown 1 / 3 / 6 decision bars (next signal no earlier than 10 / 20 / 35
  minutes after the previous one on a continuous qualifying run).

For each refire variant the trades split into the first signal of the symbol-day (identical to `first`) and the
**extras** (2nd+ signals). Reported per setup: n, trades/day, exp R after costs, day-clustered t for `first`, for each
variant in total, and for its extras alone; extras exp minus first exp.

### 1.2 Setups
Every enabled `type: lab` setup of the three accounts, configs as merged by `mcf.config` (config/default.yaml for
Primary; plus config/account_testing.yaml for Testing; plus config/account_testing2.yaml for Testing 2), each with its
module, YAML window and min_adv. A setup that runs in two accounts with the same module/window/min_adv is scored once.

### 1.3 Data, fills, costs
- Two-year lab frames `research/history2y/data/frames` via `research/history2y/lib.py`, open months only. The rule-19
  locked block (2024-11-01..2025-02-28) is never loaded; `MCF_HIST_ALLOW_LOCKED` is never set.
- Population: point-in-time adv20 >= the setup's min_adv, daily ATR > 0, decision bars (bar close) inside the setup
  window and inside 09:50-15:00 (as `LabStrategy.generate`).
- Fixed geometries (t1s1 / t05s1 / t1s05): the frames' per-bar lab outcome (entry at the decision-bar close,
  R = 0.25 x daily ATR, target/stop, flat 15:55) converted to production R with `gates.prod_r` and time-of-day entry
  costs (`gates.tod_cost_mult`) - the lab engine of stack1009 / RESCORE / swarm1013 B0.
- Testing 2 CWT modules and the Testing 1 LIQ modules are run on the frame plus the 09:35-09:45 rows from
  `research/bdi/cwt/test_b/data/headtail.parquet` (as research/bdi/cwt/live/verify.py), so their opening-range
  logic sees the open. LIQ rows also get the derived fromOpen / prior-day distances / ATR on those rows.
- Structural exits (GEOM "S": CWT09 x3, LIQ x2): simulated here on the 5-minute path (frame rows to 15:00, then the
  15:05-15:55 rows of headtail.parquet): stop first inside a bar, a bar whose open (proxy: prior close) is through the
  stop fills at that open, optional target as a limit, else flat at the 15:55 close. R = structural risk
  |entry - stop|. Costs: entry 1c + 1 bps x tod multiplier; target free; stop 1c + 1 bps + 2c; timed 1c + 1 bps.
  LIQ-pdl's live management (be_at_r / time stop) is NOT modelled (stated).
- RW6G1 (Primary and -FD): its VWAP +2 SD guard needs volume, which the frames do not carry. The guard is computed
  with the module's own `vwap_band_block` on 5-minute bars rebuilt from the SIP 1-minute cache (`data/cache_hist`)
  for the symbol-days where its base qualifies, locked block dropped on read (as swarm1013/backtest/bars.py).
- Portfolio limits (max positions, lot cap 3, same-side rule, daily loss stop) are NOT applied: these are setup-level
  lab numbers. Extras that overlap an open lot of the same setup would count toward the lot cap live.
- Survivorship caveat (rule 19): today's universe applied to the past.

### 1.4 Verdict per setup (fixed before scoring)
- **design-off** (refire stays off whatever the numbers; numbers still reported): setups built around one event or an
  opening window: MF1-MF4 Primary versions (MarcoFlow "open" / "945-1030" stacks, windows ending 10:30-11:00),
  CWT09 x4 (one gap-day bounce/VWAP-loss trade, stop at the 09:30-10:30 high), LIQ x2 (one sweep-and-reclaim of the
  opening range / prior-day low), CWT12 coil x2 (coil under the opening high, 09:50-11:30). No ORB, open-gap or
  fixed-time 15:30 setup is a `type: lab` setup (those are classic strategies, untouched by `refire`).
- For every other setup, per cooldown c in {1, 3, 6}:
  - **benefit** at c: extras n >= 30, extras exp R > 0 after costs, and extras exp R >= first exp R
    ("not worse than the first ones").
  - Recommended flag: refire on with the SMALLEST c that is a benefit (the owner wants as many entries as the data
    allow); otherwise off.
  - **neutral**: no c is a benefit, but some c has extras exp > 0 (positive but below the first signals, or n < 30).
  - **worse**: extras exp <= 0 at every c (with n >= 30 at some c), or no extras at all = no change.
- These are lab point estimates. Many setups have first-signal expectancy near zero (most Testing setups did not pass
  the gates); "not worse than the first ones" is not an edge claim. Total configurations: 4 per unique setup
  (reported in section 2). No holdout is scored.

## 2. Results (2026-10-14)

Run: `python research/bdi/refire1014/scan.py` (hits in the session scratchpad, deleted after the run) then
`python research/bdi/refire1014/report.py` -> `results.csv` (every number), `summary.json`, `table.md`.
426 open sessions (2024-10 .. 2026-10-07, locked block excluded). **74 unique setups x 4 variants = 296
configurations** (Primary 11, Testing 33, Testing 2 30; none shared with identical module/window/min_adv across
accounts except MF5, whose Primary and -FD versions have the same mask and window, so their rows are identical).
No holdout was scored. Lab numbers, not paper or live.

### 2.1 Failures and caveats first
- **No extras set is significant.** The best extras t is +1.58 (RW6G1 Primary, n 34); every other "benefit" has extras
  t <= 0.84. With 62 non-design setups x 3 cooldowns = 186 extras tests, ~9 would look positive at p 0.05 by chance;
  none here even reaches t 1.65. "Benefit" means only "2nd+ signals are not worse than the first ones after costs"
  (the owner's bar), not an edge.
- **Most "benefits" are not-worse-than-negative.** 12 of the 16 recommended setups have NEGATIVE first-signal
  expectancy; refire there adds trades at about zero expectancy (+0.00..+0.04R). 9 of the 16 have extras that turn
  <= 0 without their best day (`cd*_x_ex_best_day` in results.csv). Only RW6G1 (Primary) has a positive first signal
  (+0.263R, t 2.36) AND better extras (+0.410R, n 34, ex-best-day +0.057).
- **Testing 2 gets nothing:** every CWT setup's extras are negative (or below a positive first, CWT04-lh), and
  most CWT first signals are themselves negative (t down to -11).
- **Lab volume, not live volume.** Portfolio limits (max positions / per-setup sleeve / lot cap 3 / same-side rule /
  daily loss stop) are not applied. Extras overlapping an open lot of the same setup on the symbol use a lot slot
  live. Trades/day below are setup-level lab counts and overstate what an account can take (e.g. Testing's first
  signals alone are ~531/day in the lab against a 150-per-setup sleeve and 400 positions).
- **Parity:** first-of-day counts match the published module parity for CWT B-package setups (e.g. CWT14-orl-p05
  105,022 vs 105,023), LIQ-orl (13,334 vs 13,335), LIQ-pdl (158 vs 160) and RW6G1 (422 vs 424, +0.263 vs +0.26R).
  **CWT09 (package A) does not match** (CWT09-g5-bounce 5,044 vs 3,692 first signals): its live frame was verified on
  package A data with a different head/adv population. CWT09 is design-off, so this does not change a flag, but its
  numbers here are not parity-checked. Structural exits (CWT09 x3, LIQ x2) are simulated on 5-minute bars with an
  open proxy, and LIQ-pdl's be/time-stop management is not modelled.

### 2.2 Verdict counts (pre-declared rule, 1.4)
| | benefit | neutral | worse | total |
|---|---|---|---|---|
| all 74 setups | 17 | 8 | 49 | 74 |
| excluding the 12 design-off setups | 16 | 6 | 40 | 62 |

The one design-off "benefit" is LIQ-orl-sweep-open15-s25-long (extras +0.098R, t 1.16, n 392): left off by design.

### 2.3 Expected extra trades/day (lab, before account limits)
| account | lab setups | refire recommended | extra trades/day (recommended flags) | first signals/day | extras/day if every setup refired at cd1 |
|---|---|---|---|---|---|
| Primary | 11 | 3 (NS2, NS5, RW6G1) | +1.41 | 60.0 | +16.1 |
| Testing | 33 | 13 | +136.6 (L3-fromopen-FD alone +84.4, NS3-FD +17.8, RW4-FD +14.3) | 531.0 | +300.2 |
| Testing 2 | 30 | 0 | 0 | 1499.8 | +1033.7 |

### 2.4 Per-setup table
Columns: first-of-day trades/day, exp R after costs, day-clustered t; extras (2nd+ signals only) at cooldown 1 / 3 / 6
as trades/day, exp R, t; all signals at cd1 (exp, t); class; recommended flag. Accounts: P Primary, T1 Testing,
T2 Testing 2.

| setup | acct | geom | win | first n/day, exp, t | cd1 extras n/day, exp, t | cd3 extras | cd6 extras | cd1 all exp, t | class | refire |
|---|---|---|---|---|---|---|---|---|---|---|
| MF1-945-flowsell-vwapup | P | t1s05 | 950-1030 | +5.61, -0.078, -2.84 | +1.98, -0.193, -4.76 | +0.68, -0.147, -2.51 | +0.04, -0.456, -3.34 | -0.108, -3.89 | worse | off (design) |
| MF2-open-rsimidhi-flowsell | P | t1s05 | 950-1100 | +1.43, -0.032, -0.88 | +0.11, -0.112, -1.16 | +0.02, -0.349, -1.95 | +0.00, -0.540, - | -0.038, -1.04 | worse | off (design) |
| MF3-open-flowsell-rsi5hi | P | t1s1 | 950-1100 | +9.71, -0.085, -2.88 | +3.14, -0.142, -2.95 | +1.14, -0.174, -2.89 | +0.45, -0.219, -2.84 | -0.099, -3.19 | worse | off (design) |
| MF4-h40-open-flowsell | P | t05s1 | 950-1100 | +7.79, -0.097, -3.30 | +2.34, -0.178, -4.70 | +0.83, -0.194, -3.87 | +0.28, -0.193, -2.63 | -0.115, -4.25 | worse | off (design) |
| MF5-flowsell-vwapup-rsi5hi | P | t1s1 | 950-1500 | +16.03, -0.057, -2.64 | +4.94, -0.104, -3.05 | +1.73, -0.120, -2.70 | +0.71, -0.161, -2.94 | -0.068, -3.03 | worse | off |
| NS1-rsidip-rsi5pop-long | P | t05s1 | 950-1130 | +1.04, +0.032, +0.80 | +0.01, -0.207, -0.62 | +0.00, +0.473, - | +0.00, +0.473, - | +0.028, +0.72 | neutral | off |
| NS2-sma50break-overbought-short | P | t1s1 | 950-1130 | +7.33, +0.004, +0.07 | +1.08, +0.041, +0.46 | +0.56, +0.057, +0.68 | +0.18, +0.105, +0.76 | +0.009, +0.14 | benefit | on cd1 |
| NS3-failed-vwap-reclaim-short | P | t1s1 | 950-1130 | +3.54, +0.052, +1.17 | +1.85, +0.050, +0.96 | +1.24, +0.033, +0.60 | +0.69, +0.021, +0.29 | +0.051, +1.20 | neutral | off |
| NS4-pm-vwap-reclaim-oversold-short | P | t1s05 | 1130-1500 | +3.45, -0.065, -2.03 | +0.32, -0.075, -1.06 | +0.14, -0.057, -0.56 | +0.03, -0.111, -0.57 | -0.066, -1.97 | worse | off |
| NS5-sma50-flush-oversold-long | P | t1s1 | 950-1130 | +3.06, -0.040, -0.49 | +0.25, +0.077, +0.66 | +0.09, +0.213, +1.54 | +0.02, +0.643, +2.49 | -0.031, -0.38 | benefit | on cd1 |
| RW6G1-ns2-up3-vwap2sd-short | P | t1s1 | 950-1130 | +0.99, +0.263, +2.36 | +0.08, +0.410, +1.58 | +0.02, +0.159, +0.52 | +0.01, +0.472, +1.00 | +0.274, +2.33 | benefit | on cd1 |
| exhaustion_short | T1 | t1s1 | 1300-1500 | +14.02, -0.010, -0.32 | +3.39, +0.030, +0.64 | +1.31, +0.040, +0.68 | +0.83, +0.034, +0.45 | -0.002, -0.07 | benefit | on cd1 |
| exhaustion_short-FD | T1 | t1s1 | 950-1500 | +66.80, -0.062, -3.79 | +25.37, -0.051, -2.49 | +12.83, -0.042, -1.78 | +9.27, -0.025, -0.99 | -0.059, -3.66 | worse | off |
| MF1-945-flowsell-vwapup-FD | T1 | t1s05 | 950-1500 | +24.74, -0.079, -5.76 | +9.54, -0.107, -4.91 | +3.51, -0.123, -4.43 | +1.32, -0.153, -4.22 | -0.087, -5.96 | worse | off |
| MF2-open-rsimidhi-flowsell-FD | T1 | t1s05 | 950-1500 | +10.60, -0.047, -2.24 | +1.69, +0.003, +0.07 | +0.64, -0.034, -0.71 | +0.29, +0.004, +0.07 | -0.040, -1.90 | benefit | on cd1 |
| MF3-open-flowsell-rsi5hi-FD | T1 | t1s1 | 950-1500 | +24.80, -0.075, -4.32 | +6.69, -0.110, -3.90 | +2.49, -0.131, -3.75 | +1.20, -0.142, -3.46 | -0.083, -4.54 | worse | off |
| MF4-h40-open-flowsell-FD | T1 | t05s1 | 950-1500 | +17.07, -0.082, -4.71 | +6.15, -0.092, -3.78 | +2.81, -0.088, -2.92 | +1.49, -0.036, -1.06 | -0.085, -4.93 | worse | off |
| MF5-flowsell-vwapup-rsi5hi-FD | T1 | t1s1 | 950-1500 | +16.03, -0.057, -2.64 | +4.94, -0.104, -3.05 | +1.73, -0.120, -2.70 | +0.71, -0.161, -2.94 | -0.068, -3.03 | worse | off |
| NS1-rsidip-rsi5pop-long-FD | T1 | t05s1 | 950-1500 | +5.72, -0.068, -3.37 | +0.22, -0.047, -0.69 | +0.12, +0.044, +0.53 | +0.11, +0.030, +0.36 | -0.067, -3.32 | benefit | on cd3 |
| NS2-sma50break-overbought-short-FD | T1 | t1s1 | 950-1500 | +19.13, -0.055, -1.82 | +5.03, -0.038, -0.83 | +3.36, -0.025, -0.56 | +2.05, -0.013, -0.22 | -0.052, -1.60 | worse | off |
| NS3-failed-vwap-reclaim-short-FD | T1 | t1s1 | 950-1500 | +23.95, -0.028, -1.40 | +17.75, +0.024, +0.76 | +12.93, +0.026, +0.76 | +8.71, +0.026, +0.86 | -0.006, -0.27 | benefit | on cd1 |
| NS4-pm-vwap-reclaim-oversold-short-FD | T1 | t1s05 | 950-1500 | +3.97, -0.055, -1.91 | +0.45, -0.031, -0.51 | +0.21, -0.023, -0.28 | +0.05, -0.049, -0.32 | -0.053, -1.76 | worse | off |
| NS5-sma50-flush-oversold-long-FD | T1 | t1s1 | 950-1500 | +7.37, -0.043, -0.82 | +0.79, -0.059, -0.68 | +0.39, -0.091, -0.80 | +0.14, -0.089, -0.54 | -0.045, -0.82 | worse | off |
| RW6G1-ns2-up3-vwap2sd-short-FD | T1 | t1s1 | 950-1500 | +4.62, -0.012, -0.19 | +0.98, +0.010, +0.11 | +0.64, +0.026, +0.33 | +0.40, +0.111, +1.24 | -0.008, -0.12 | benefit | on cd1 |
| L3-gap-slope-rsi5hi-FD | T1 | t05s1 | 950-1500 | +13.41, -0.039, -1.15 | +31.06, -0.025, -0.56 | +16.24, -0.010, -0.21 | +10.08, +0.022, +0.45 | -0.029, -0.74 | benefit | on cd6 |
| L3-gap-slope-lowdist-FD | T1 | t1s1 | 950-1500 | +9.76, -0.104, -1.80 | +24.02, -0.032, -0.63 | +12.11, -0.036, -0.70 | +6.38, -0.030, -0.57 | -0.052, -1.11 | worse | off |
| L3-gap-slope-fromopen-FD | T1 | t1s1 | 950-1500 | +11.44, -0.042, -1.12 | +84.42, +0.025, +0.51 | +41.55, +0.026, +0.54 | +22.66, +0.037, +0.68 | +0.017, +0.36 | benefit | on cd1 |
| ST1-ordn-long-pm-t05s1-FD | T1 | t05s1 | 950-1500 | +3.81, -0.056, -2.09 | +0.29, -0.008, -0.11 | +0.25, +0.017, +0.25 | +0.22, +0.002, +0.02 | -0.052, -2.00 | benefit | on cd3 |
| ST2-slope20up-long-am-t05s1-FD | T1 | t05s1 | 950-1500 | +25.72, -0.016, -0.82 | +4.64, -0.064, -2.55 | +4.43, -0.065, -2.53 | +4.15, -0.062, -2.38 | -0.023, -1.27 | worse | off |
| ST3-rsi5up-short-pm-t1s1-FD | T1 | t1s1 | 950-1500 | +1.54, +0.016, +0.38 | +0.66, -0.037, -0.70 | +0.56, -0.029, -0.53 | +0.48, -0.030, -0.49 | +0.000, +0.00 | worse | off |
| ST4-emadn-long-am-t1s05-FD | T1 | t1s05 | 950-1500 | +3.05, +0.018, +0.59 | +0.06, -0.242, -1.41 | +0.06, -0.242, -1.41 | +0.06, -0.242, -1.41 | +0.013, +0.42 | neutral | off |
| ST5-pdbrkup-short-mid-t05s1-FD | T1 | t05s1 | 950-1500 | +1.00, -0.039, -0.91 | +1.06, -0.011, -0.25 | +0.82, +0.001, +0.03 | +0.60, +0.004, +0.07 | -0.025, -0.65 | benefit | on cd3 |
| ST6-volspikeup-short-mid-t1s1-FD | T1 | t1s1 | 950-1500 | +1.43, +0.024, +0.67 | +0.41, +0.039, +0.54 | +0.30, +0.009, +0.11 | +0.20, +0.098, +1.06 | +0.027, +0.75 | benefit | on cd1 |
| ST7-rsi50dn-long-pm-t1s1-FD | T1 | t1s1 | 950-1500 | +2.43, +0.033, +0.71 | +0.01, -0.175, -0.34 | +0.01, -0.175, -0.34 | +0.01, -0.175, -0.34 | +0.032, +0.70 | neutral | off |
| ST8-volspikedn-long-pm-t1s1-FD | T1 | t1s1 | 950-1500 | +1.24, +0.040, +0.82 | +0.12, -0.003, -0.02 | +0.06, -0.260, -1.70 | +0.04, -0.081, -0.39 | +0.036, +0.77 | worse | off |
| RW4-ns3-adv150-short-FD | T1 | t1s1 | 950-1500 | +18.94, -0.029, -1.35 | +14.34, +0.027, +0.84 | +10.40, +0.031, +0.88 | +7.03, +0.029, +0.95 | -0.005, -0.19 | benefit | on cd1 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | T1 | t1s1 | 950-1500 | +13.14, -0.058, -2.50 | +2.35, -0.052, -1.26 | +0.71, -0.050, -0.88 | +0.32, +0.028, +0.36 | -0.057, -2.35 | benefit | on cd6 |
| RW6-ns2-up3-short-FD | T1 | t1s1 | 950-1500 | +8.48, -0.021, -0.53 | +2.05, +0.032, +0.46 | +1.33, +0.052, +0.79 | +0.85, +0.085, +0.92 | -0.011, -0.24 | benefit | on cd1 |
| RW1-gapdn-bounce-flowsell-short-FD | T1 | t1s1 | 950-1500 | +17.55, -0.047, -2.25 | +4.24, -0.061, -1.98 | +1.76, -0.051, -1.30 | +0.89, -0.054, -1.16 | -0.050, -2.35 | worse | off |
| RW2-exhaustion-noon-adv150-short-FD | T1 | t1s1 | 950-1500 | +52.08, -0.059, -3.47 | +20.14, -0.033, -1.54 | +10.29, -0.020, -0.83 | +7.49, -0.008, -0.31 | -0.052, -3.14 | worse | off |
| RW3-gapdn-rsi5pop-flowsell-short-FD | T1 | t1s1 | 950-1500 | +14.07, -0.069, -3.16 | +3.26, -0.098, -2.62 | +1.22, -0.093, -1.86 | +0.69, -0.096, -1.65 | -0.074, -3.30 | worse | off |
| RW7-gapdn-bounce-early-short-FD | T1 | t1s1 | 950-1500 | +61.42, -0.058, -2.95 | +23.14, -0.060, -2.61 | +11.72, -0.048, -2.01 | +6.61, -0.034, -1.33 | -0.059, -2.95 | worse | off |
| LIQ-orl-sweep-open15-s25-long | T1 | S | 950-1500 | +31.30, -0.002, -0.05 | +0.92, +0.098, +1.16 | +0.92, +0.098, +1.16 | +0.83, +0.103, +1.19 | +0.001, +0.04 | benefit | off (design) |
| LIQ-pdl-sweep-open15-vwap-long | T1 | S | 950-1500 | +0.37, -0.096, -0.53 | +0.01, -0.932, -5.10 | +0.01, -0.932, -5.10 | +0.01, -1.125, -25.89 | -0.126, -0.70 | neutral | off (design) |
| CWT04-backside-lh-a25-short | T2 | t1s1 | 1030-1500 | +0.36, +0.206, +0.96 | +1.22, -0.175, -4.68 | +0.86, -0.066, -1.42 | +0.56, +0.120, +0.84 | -0.088, -1.61 | neutral | off |
| CWT04-backside-lh-a15-short | T2 | t1s1 | 1030-1500 | +2.85, +0.147, +0.79 | +8.91, -0.135, -4.13 | +6.11, -0.056, -2.65 | +4.03, +0.028, +0.44 | -0.067, -2.58 | neutral | off |
| CWT04-backside-vwaptest-a25-short | T2 | t1s1 | 950-1500 | +0.56, -0.154, -1.20 | +1.83, -0.270, -2.38 | +1.22, -0.193, -1.82 | +0.85, -0.126, -1.75 | -0.242, -2.08 | worse | off |
| CWT04-backside-vwaptest-a15-short | T2 | t1s05 | 950-1500 | +4.76, -0.165, -3.80 | +16.88, -0.186, -3.73 | +10.75, -0.184, -3.88 | +7.22, -0.139, -5.10 | -0.181, -3.74 | worse | off |
| CWT13-vwapstretch-z075-long | T2 | t1s1 | 950-1500 | +9.23, -0.045, -1.47 | +4.37, -0.123, -1.61 | +3.21, -0.119, -1.99 | +2.33, -0.145, -2.14 | -0.070, -1.77 | worse | off |
| CWT13-vwapstretch-z05-long | T2 | t05s1 | 1100-1500 | +42.57, -0.079, -5.08 | +31.81, -0.087, -2.87 | +23.43, -0.083, -3.31 | +16.27, -0.077, -2.55 | -0.082, -4.47 | worse | off |
| CWT13-vwapstretch-z075-short | T2 | t1s1 | 1100-1500 | +6.14, -0.076, -1.71 | +3.24, -0.071, -1.22 | +2.38, -0.097, -1.60 | +1.57, -0.116, -1.86 | -0.074, -1.73 | worse | off |
| CWT13-vwapstretch-z05-short | T2 | t1s1 | 1100-1500 | +37.95, -0.068, -2.81 | +32.95, -0.045, -1.69 | +24.04, -0.052, -1.87 | +16.33, -0.043, -1.52 | -0.058, -2.47 | worse | off |
| CWT14-failbrk-pdl-p10-long | T2 | t05s1 | 950-1500 | +88.03, -0.084, -8.55 | +22.00, -0.096, -7.41 | +17.50, -0.094, -6.81 | +11.70, -0.094, -5.79 | -0.086, -9.03 | worse | off |
| CWT14-failbrk-pdl-p05-long | T2 | t05s1 | 950-1500 | +156.98, -0.086, -9.84 | +91.33, -0.097, -9.28 | +67.82, -0.091, -8.10 | +47.01, -0.090, -7.35 | -0.090, -10.34 | worse | off |
| CWT14-failbrk-pdh-p10-lowvol-short | T2 | t05s1 | 950-1500 | +45.73, -0.088, -9.33 | +7.24, -0.078, -4.05 | +5.46, -0.074, -3.52 | +3.30, -0.097, -4.51 | -0.086, -9.07 | worse | off |
| CWT14-failbrk-orl-p10-lowvol-long | T2 | t05s1 | 950-1500 | +74.36, -0.088, -7.74 | +11.61, -0.078, -4.28 | +9.15, -0.081, -3.87 | +5.77, -0.089, -3.54 | -0.087, -7.63 | worse | off |
| CWT12-coil-k6-long | T2 | t1s05 | 950-1130 | +39.28, -0.070, -4.65 | +14.48, -0.070, -3.18 | +4.71, -0.081, -3.05 | +1.56, -0.072, -2.04 | -0.070, -4.37 | worse | off (design) |
| CWT12-coil-k4-long | T2 | t05s1 | 950-1130 | +104.47, -0.074, -5.85 | +43.85, -0.073, -4.20 | +18.75, -0.077, -3.73 | +9.34, -0.073, -3.19 | -0.074, -5.50 | worse | off (design) |
| CWT12-flag-s1-long | T2 | t05s1 | 950-1500 | +3.37, -0.073, -2.69 | +0.12, -0.073, -0.73 | +0.11, -0.063, -0.61 | +0.10, -0.126, -1.14 | -0.073, -2.77 | worse | off |
| CWT05-flush-m075-v5-long | T2 | t05s1 | 950-1500 | +1.37, -0.088, -1.94 | +6.40, -0.131, -5.05 | +4.51, -0.142, -4.82 | +2.96, -0.124, -3.89 | -0.124, -5.15 | worse | off |
| CWT05-flush-m05-v5-long | T2 | t05s1 | 950-1500 | +2.93, -0.107, -3.20 | +13.96, -0.093, -4.36 | +9.73, -0.093, -4.21 | +6.35, -0.081, -3.49 | -0.096, -4.79 | worse | off |
| CWT05-flush-m05-v3-long | T2 | t05s1 | 950-1500 | +8.94, -0.133, -4.73 | +51.67, -0.090, -4.27 | +36.18, -0.088, -4.31 | +24.02, -0.085, -4.25 | -0.096, -4.73 | worse | off |
| CWT05-flush-m075-v3-long | T2 | t05s1 | 950-1500 | +3.31, -0.152, -3.96 | +19.22, -0.127, -4.84 | +13.57, -0.132, -4.90 | +9.09, -0.118, -4.41 | -0.130, -5.21 | worse | off |
| CWT09-gapdn-bounce-g10-lowerhalf-short | T2 | S | 1030-1500 | +2.25, +0.048, +0.34 | +18.41, -0.128, -1.74 | +11.21, -0.202, -2.35 | +7.01, -0.210, -1.89 | -0.107, -1.46 | worse | off (design) |
| CWT09-gapdn-bounce-g5-lowerhalf-short | T2 | S | 1030-1500 | +11.84, -0.139, -1.07 | +100.16, -0.156, -2.83 | +60.78, -0.184, -3.40 | +38.08, -0.211, -2.93 | -0.160, -2.84 | worse | off (design) |
| CWT09-gapdn-vwaploss-g10-short | T2 | S | 1030-1500 | +2.20, +0.042, +0.59 | +34.55, +0.031, +1.02 | +17.47, +0.027, +0.85 | +9.76, +0.026, +0.88 | +0.032, +0.98 | neutral | off (design) |
| CWT09-gapdn-vwaploss-g5-short | T2 | t1s05 | 1030-1500 | +11.71, -0.029, -0.53 | +174.69, -0.059, -2.81 | +88.55, -0.064, -2.96 | +49.86, -0.057, -2.76 | -0.057, -2.72 | worse | off (design) |
| CWT14-failbrk-orl-p05-lowvol-long | T2 | t05s1 | 950-1500 | +173.74, -0.089, -9.26 | +67.40, -0.084, -6.68 | +49.32, -0.082, -6.14 | +32.43, -0.081, -5.55 | -0.088, -9.08 | worse | off |
| CWT14-failbrk-orl-p10-long | T2 | t05s1 | 950-1200 | +93.87, -0.089, -6.93 | +15.78, -0.087, -5.15 | +11.65, -0.085, -4.48 | +6.42, -0.082, -2.99 | -0.089, -7.08 | worse | off |
| CWT14-failbrk-orl-p05-long | T2 | t05s1 | 950-1500 | +246.53, -0.092, -9.89 | +133.84, -0.087, -8.39 | +101.58, -0.086, -7.86 | +70.51, -0.087, -7.22 | -0.090, -10.17 | worse | off |
| CWT14-failbrk-pdl-p10-lowvol-long | T2 | t05s1 | 950-1500 | +47.14, -0.093, -8.72 | +8.04, -0.085, -4.47 | +6.34, -0.073, -3.81 | +4.01, -0.094, -4.01 | -0.092, -8.68 | worse | off |
| CWT14-failbrk-pdh-p05-lowvol-short | T2 | t05s1 | 950-1500 | +103.00, -0.094, -11.44 | +41.12, -0.078, -7.85 | +29.34, -0.076, -7.11 | +19.05, -0.075, -6.41 | -0.089, -11.21 | worse | off |
| CWT14-failbrk-pdl-p05-lowvol-long | T2 | t05s1 | 950-1500 | +103.35, -0.094, -9.87 | +42.55, -0.088, -7.62 | +30.67, -0.078, -6.37 | +20.30, -0.080, -5.93 | -0.092, -9.84 | worse | off |
| CWT14-failbrk-pdh-p10-short | T2 | t05s1 | 950-1200 | +71.03, -0.093, -9.87 | +14.11, -0.086, -5.45 | +9.91, -0.084, -4.57 | +5.40, -0.080, -3.91 | -0.092, -9.83 | worse | off |

### 2.5 Recommended per-setup flags (NOT applied; config unchanged)
Refire on (smallest cooldown that passed the rule):
- Primary: NS2-sma50break-overbought-short cd1, NS5-sma50-flush-oversold-long cd1, RW6G1-ns2-up3-vwap2sd-short cd1.
- Testing: exhaustion_short cd1, MF2-open-rsimidhi-flowsell-FD cd1, NS1-rsidip-rsi5pop-long-FD cd3,
  NS3-failed-vwap-reclaim-short-FD cd1, RW6G1-ns2-up3-vwap2sd-short-FD cd1, L3-gap-slope-rsi5hi-FD cd6,
  L3-gap-slope-fromopen-FD cd1, ST1-ordn-long-pm-t05s1-FD cd3, ST5-pdbrkup-short-mid-t05s1-FD cd3,
  ST6-volspikeup-short-mid-t1s1-FD cd1, RW4-ns3-adv150-short-FD cd1, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD cd6,
  RW6-ns2-up3-short-FD cd1.
- Testing 2: none.
- Everything else off; the 12 design-off setups (MF1-MF4 Primary, CWT09 x4, LIQ x2, CWT12-coil x2) carry an explicit
  `refire: false` so a later account-level default cannot switch them on.

Lead's judgement call: given 2.1, a conservative reading is refire on only for RW6G1 (Primary), the only setup whose
first signal is positive and whose extras are better; the rule-based list above is what "not worse than the first
ones" gives. Either way this is a setup change: backlog first (rules 15-17), merged after the close, ledger entry.

### 2.6 Proposed config diff (do not apply before approval)
```diff
--- config/default.yaml
 live:
+  # LabStrategy refire (research/bdi/refire1014): account default for type: lab setups; a setup's own refire /
+  # refire_cooldown wins. Off: first qualifying bar per symbol-day only (unchanged behaviour).
+  lab_refire: false
+  lab_refire_cooldown: 1     # decision bars a refire signal blocks after it (1 = no two consecutive 5-min bars)
 strategies:
   MF1-945-flowsell-vwapup:
+    refire: false            # open-window design (refire1014 design-off)
   MF2-open-rsimidhi-flowsell:
+    refire: false
   MF3-open-flowsell-rsi5hi:
+    refire: false
   MF4-h40-open-flowsell:
+    refire: false
   NS2-sma50break-overbought-short:
+    refire: true             # refire1014: extras +0.041R n 461 vs first +0.004R
+    refire_cooldown: 1
   NS5-sma50-flush-oversold-long:
+    refire: true             # extras +0.077R n 105 vs first -0.040R
+    refire_cooldown: 1
   RW6G1-ns2-up3-vwap2sd-short:
+    refire: true             # extras +0.410R n 34 vs first +0.263R
+    refire_cooldown: 1
--- config/account_testing.yaml
 strategies:
+  exhaustion_short:                         {refire: true, refire_cooldown: 1}
+  MF2-open-rsimidhi-flowsell-FD:            {refire: true, refire_cooldown: 1}
+  NS1-rsidip-rsi5pop-long-FD:               {refire: true, refire_cooldown: 3}
+  NS3-failed-vwap-reclaim-short-FD:         {refire: true, refire_cooldown: 1}
+  RW6G1-ns2-up3-vwap2sd-short-FD:           {refire: true, refire_cooldown: 1}
+  L3-gap-slope-rsi5hi-FD:                   {refire: true, refire_cooldown: 6}
+  L3-gap-slope-fromopen-FD:                 {refire: true, refire_cooldown: 1}
+  ST1-ordn-long-pm-t05s1-FD:                {refire: true, refire_cooldown: 3}
+  ST5-pdbrkup-short-mid-t05s1-FD:           {refire: true, refire_cooldown: 3}
+  ST6-volspikeup-short-mid-t1s1-FD:         {refire: true, refire_cooldown: 1}
+  RW4-ns3-adv150-short-FD:                  {refire: true, refire_cooldown: 1}
+  RW5-heat30-flowsell-rsi5pop-gapdn-short-FD: {refire: true, refire_cooldown: 6}
+  RW6-ns2-up3-short-FD:                     {refire: true, refire_cooldown: 1}
+  LIQ-orl-sweep-open15-s25-long:            {refire: false}   # sweep-and-reclaim design
+  LIQ-pdl-sweep-open15-vwap-long:           {refire: false}
--- config/account_testing2.yaml
 strategies:
+  CWT09-gapdn-bounce-g10-lowerhalf-short:   {refire: false}   # one gap-day trade by design
+  CWT09-gapdn-bounce-g5-lowerhalf-short:    {refire: false}
+  CWT09-gapdn-vwaploss-g10-short:           {refire: false}
+  CWT09-gapdn-vwaploss-g5-short:            {refire: false}
+  CWT12-coil-k6-long:                       {refire: false}   # coil under the opening high
+  CWT12-coil-k4-long:                       {refire: false}
```
(The flags merge into the existing strategy entries; inline maps are shorthand for keys added to each entry.)
