# Entry cutoff study: 15:00 vs 15:15 vs 15:30 (BDI "EC", 2026-10-11)

*Educational only - not financial advice. Lab results on history only; nothing here is a live or paper result.*

Owner question (2026-10-11): "Are both trading accounts meant to run only through 3pm? A 3:15 stop might still be worth
it." Today no lab/heat setup can enter after the 15:00 bar close (lab frames stop at 15:00; live code caps every window
at `min(1500, hi)` in mcf/strategies/setups.py), and every position is flattened at 15:55. Entries after 15:00 have never
been tested.

## 0. Pre-declaration (written 2026-10-11 BEFORE any trade after 15:00 was scored)

### 0.1 Data
- Open two-year history only (research/history2y, 2024-10-01..2026-10-07 minus the rule-19 locked block
  2024-11-01..2025-02-28). `MCF_HIST_ALLOW_LOCKED` is never set.
- **Late frames** (`build_late.py`): one pass over data/cache_hist/1Min, one process. Locked-block rows are dropped at
  load, before any computation (as research/bdi/timeofday/build_open.py). Per symbol: 5-minute resample, the SAME code
  path as mcf/research/setup_lab.build (heat_frame + extra_features + _outcomes_asym for t1s1/t05s1/t1s05, R = 0.25 x
  daily ATR, exits by the 15:55 bar close, 1c/side lab cost), point-in-time adv20 as build_frames.daily_table; the only
  change is the decision-bar filter: rows with bar close 15:05..15:30 are kept (written to data/late/), rows <= 15:00
  come from the existing frames unchanged. The RW6G1 VWAP +2 SD band guard is computed for 15:05..15:30 by the module's
  own vwap_band_block on full-day 5-minute bars (rows <= 15:00 use research/bdi/timeofday/data/block, as verify.py).
- **Warm-up exclusion:** because locked rows are dropped at load, the first sessions after the block see a prior day of
  2024-10-31 (gap, prior-day levels, 14-day ATR, adv20). The first 20 open sessions after the block (2025-03-03 ..
  2025-03-28) are excluded from EVERY bucket of this study (406 of 426 sessions remain), so all buckets compare on
  the same sessions.
- **Identity check (before scoring):** for >= 8 symbols, the late builder's own rows <= 15:00 (all 59 columns) must
  equal the stored history2y frames on months outside the warm-up (exact or float32-equal), and the <= 15:00 trades of
  a few setups (MF5, NS4, exhaustion_short, ST1-FD, RW6G1-FD) on the combined frame must equal the trades on the stored
  frames (verify.json / rescore n).

### 0.2 Setups (35)
- Primary, only setups whose window already ends at 15:00: exhaustion_short [1300,1500], MF5-flowsell-vwapup-rsi5hi
  [950,1500], NS4-pm-vwap-reclaim-oversold-short [1130,1500] (run as their -FD module & their own window: verify.json
  proves FD mask & source window == source mask). Heat setups and the other primary lab setups end before 15:00 and are
  not affected by a cutoff change.
- Testing: all 32 -FD setups of config/account_testing.yaml (30 lab + heat_fade_short-FD / heat_fade_long-FD), window
  [950,1500]. Heat FD scores carry their window inside regime_score(950, 1500); for the extension the copy is executed
  with 1530 in place of 1500 (in memory; modules not edited).
- Each keeps min_adv (point-in-time adv20), side, exit geometry and every non-time condition. prefilters are live
  speed-ups not applied by the lab (as verify.py / timeofday).

### 0.3 Trade sets (entry = bar close ET; one trade per symbol-day per setup = the first qualifying bar, as live)
- `current`: the setup's window [lo, 1500] (= rescore / verify.json numbers on the 406 sessions).
- `B14`: the `current` trades whose entry is 14:05-15:00 (tod 1405..1500) - the existing last hour of the book.
- `L1` (15:00-15:15): window [lo, 1515], trades with entry tod 1505..1515 - the INCREMENTAL trades (symbol-days that
  had no qualifying bar by 15:00). This is exactly what moving the cutoff to 15:15 adds.
- `L2` (15:15-15:30): window [lo, 1530], trades with entry tod 1520..1530 (incremental on [lo, 1515]).
- `ext1515` = current + L1, `ext1530` = current + L1 + L2 (the extended setups as a whole).

### 0.4 Metrics (per setup x set; production costs incl. time-of-day entry costs, gates.lab_trades/prod_r)
n, n/day, win rate, exp R, day-clustered t, ex-best-day exp, up / down session exp (n) (gates.regime_split),
walk-forward positive share (gates.walk_forward, 3-month train / 1-month test, folds with n >= 10), exit mix (share
of trades that hit target, stop, or the 15:55 time exit; derived from win and lab R as in prod_r). Differences
L1 - B14 and L1 - current with a session-clustered SE (trades of both sets, per-session sums, paired by session).

### 0.5 Pooled book view (the owner's question)
- `pool_FD`: all 32 Testing -FD setups' trades concatenated per set (current, B14, L1, L2), day-clustered by session.
- `pool_FD_dedup`: the same, keeping only late (L1/L2) trades on symbol-days where no FD setup had an entry earlier
  that day (a conservative proxy for one-position-per-symbol).
- `pool_primary`: the 3 primary setups.

### 0.6 Configurations counted
35 setups x 2 extensions (to 15:15, to 15:30) = 70 per-setup configurations, + 2 pooled-FD + 2 pooled-FD-dedup +
2 pooled-primary = **76 configurations**. Try-count bar for this study: t >= max(1.5, sqrt(2 ln 76)) = 2.94.
Nothing is fitted: 15:15 and 15:30 are the owner's candidates, the buckets are fixed here.

### 0.7 Decision rules (declared before scoring)
- **Primary** (gates required, rule 19): a primary setup's window may be extended only if `ext1515` (or `ext1530`)
  passes gates.verdict == keep with N = the lineage's tries (rescore TRIES) + 76, AND its L-bucket alone has exp > 0.
  A setup that already fails the gates on its current window cannot pass by adding 15 minutes; then the verdict is
  "no change" regardless of the late bucket.
- **Testing** (owner-directed, lower bar; the account is a forward test of the full-day versions):
  - Book level: extend every Testing -FD window to [950, 1515] if pool_FD L1 has exp > 0 with day-clustered t >= 2.0,
    exp > 0 in up AND down sessions, walk-forward share >= 0.6, AND pool_FD_dedup L1 exp > 0. Likewise 15:30 for L2
    (both L1 and L2 must pass to go to 15:30).
  - "Not worse" (information only, not a reason to extend): L1 exp >= the book's current exp and L1 - current
    difference t > -1. If the late bucket is not worse than what the book already trades, the owner may still choose
    to extend for data collection; this is reported but the study's verdict follows the rule above.
  - Per setup: extend one -FD setup's window to 15:15 only if its L1 has n >= 30, exp > 0, day-clustered t >= 2.94
    (try-count bar), exp > 0 in up and down sessions (n >= 10 each) and walk-forward share >= 0.6 (folds with n >= 10;
    if fewer than 3 such folds, not met).
- Any extension also needs a code change (the `min(1500, hi)` cap in LabStrategy/HeatStrategy and the heat FD
  formulas' 1500), so it is a setup change: backlog first (rule 16), merged after the close, ledger entry.
- Report the 15:55-flatten share of late trades (a 15:15 entry has at most 40 minutes to reach target/stop).

## Results (scored 2026-10-11, after section 0 was written)

**Configurations scored: 76** (35 setups x 2 extensions + 6 pooled), as declared. Nothing fitted. 406 open sessions
(426 minus the 20 warm-up sessions). Files: `results.csv` (per setup x set, incl. L-B14 / L-current differences and the
primary gate verdicts), `pooled.csv`, `report.json` (identity checks, per-entry-bar pooled table), trades in
`data/trades.parquet` (git-ignored). Code: `build_late.py`, `scan.py`.

### Failures and caveats first
- **No setup and no pool meets its pre-declared extension rule.** Primary: all 3 fail the gates on the current
  window and on both extensions (verdict rework; exp <= 0 for MF5 / NS4, t far below 4.2-5.2, regime and walk-forward
  fail). Testing book: pooled L1 and L2 are negative (below). Per setup: 0 of 35 pass for 15:15, 0 of 35 for 15:30.
- **Not-worse check (information only) also fails, narrowly:** pooled FD L1 -0.052R vs the book's current -0.045R
  (difference -0.007R, session-clustered t -0.46). The late bucket is about as bad as the rest of the book, not better.
- **Most late trades are not decided by target or stop:** 74% of pooled FD L1 trades and 81% of L2 trades exit at the
  15:55 flatten (current window 28%, 14:05-15:00 bucket 58%). A late entry is mostly a 40-50 minute drift bet.
- **Costs:** time-of-day entry costs are 1.0x after 10:30 (gates.TOD_COST); late-session spreads were never measured
  (the spread calibration covered the open). If spreads widen into the close, late results are optimistic.
- Lab fills at the 5-minute bar close, as every lab study; closing-auction imbalance effects are not modelled.
- Warm-up: 20 sessions after the locked block excluded from every bucket (declared in 0.1). Survivorship as RESCORE.md.
- Late-frame identity: 10 symbols x 5 months x 59 columns of the late builder's <= 15:00 rows equal the stored
  frames; 2 of 245 symbol-months differ in ONE row by <= 2e-9 (rolling-sum float drift from a different series start;
  `identity_check.json`). On the combined frames, the <= 15:00 trades of the 15:15 / 15:30 runs equal the 15:00 run for
  all 35 setups, and every current n on all 426 sessions equals research/bdi/fullday/verify.json (e.g. exhaustion_short
  5,973, MF5 6,827, NS4 1,469, heat_fade_short-FD 75,136) - `report.json` identity.

### Pooled book (owner's question)
| Pool | set | n (/day) | exp R | day t | up exp (n) | down exp (n) | WF + share | exit target / stop / 15:55 |
|---|---|---|---|---|---|---|---|---|
| Testing 32 FD | current 09:50-15:00 | 291,041 (716.9) | -0.045 | -4.70 | -0.175 (96,218) | +0.073 (97,723) | 0.235 | 0.37 / 0.35 / 0.28 |
| Testing 32 FD | B14 14:05-15:00 | 41,204 (101.5) | -0.031 | -1.68 | -0.105 | +0.080 | 0.294 | 0.23 / 0.19 / 0.58 |
| Testing 32 FD | **L1 15:05-15:15** | 9,381 (23.1) | **-0.052** | -3.69 | -0.083 (2,886) | -0.016 (3,306) | 0.294 | 0.14 / 0.12 / 0.74 |
| Testing 32 FD | **L2 15:20-15:30** | 9,110 (22.4) | **-0.046** | -2.32 | -0.102 (2,872) | +0.007 (3,302) | 0.471 | 0.10 / 0.09 / 0.81 |
| Testing 32 FD | ext to 15:15 | 300,422 (740.0) | -0.045 | -4.83 | | | 0.235 | |
| Testing 32 FD | ext to 15:30 | 309,532 (762.4) | -0.045 | -4.90 | | | 0.235 | |
| Testing, one per symbol-day | L1 dedup | 3,099 (7.6) | -0.054 | -3.09 | -0.071 | -0.035 | 0.294 | 0.13 / 0.11 / 0.77 |
| Testing, one per symbol-day | L2 dedup | 2,967 (7.3) | -0.033 | -1.61 | -0.110 | +0.029 | 0.412 | 0.10 / 0.07 / 0.83 |
| Primary 3 (exh, MF5, NS4) | current | 13,361 (32.9) | -0.031 | -1.71 | -0.174 | +0.162 | 0.235 | 0.33 / 0.33 / 0.34 |
| Primary 3 | B14 | 3,185 (7.8) | -0.025 | -0.58 | -0.122 | +0.209 | 0.235 | |
| Primary 3 | **L1** | 738 (1.8) | **-0.085** | -2.89 | -0.121 | +0.117 | 0.188 | 0.11 / 0.18 / 0.71 |
| Primary 3 | **L2** | 805 (2.0) | **-0.163** | -4.02 | -0.211 | -0.010 | 0.188 | 0.07 / 0.19 / 0.73 |

Differences (session-clustered): Testing L1 - B14 -0.022 (t -1.11), L1 - current -0.007 (t -0.46), L2 - B14 -0.015
(t -0.60), L2 - current -0.001 (t -0.03). Primary L1 - current -0.054 (t -1.74), L2 - current -0.133 (t -3.09).
Pooled FD per entry bar: every bar 15:05..15:30 is negative (-0.027 .. -0.069R; t -0.97 .. -3.42); 14:10..15:00 are
negative too (-0.008 .. -0.093) - the last 90 minutes are uniformly slightly negative for this book.

### Per setup (L1 = 15:05-15:15 incremental, L2 = 15:20-15:30 incremental; exp R (day t) n)
| Setup | acct | current | B14 | L1 | L1 up / down (n) | L1 WF share/folds | L1 15:55 share | L2 | L2 15:55 share | L1-B14 (t) | rule |
|---|---|---|---|---|---|---|---|---|---|---|---|
| exhaustion_short | primary | +0.011 (0.34) 5411 | +0.011 (0.20) 2179 | -0.074 (-2.03) 519 | -0.089 / +0.112 (234/131) | 0.14/14 | 0.71 | -0.188 (-4.11) 630 | 0.73 | -0.085 (-1.35) | fail |
| MF5-flowsell-vwapup-rsi5hi | primary | -0.057 (-2.58) 6526 | -0.115 (-3.04) 466 | -0.143 (-2.58) 82 | -0.237 / +0.118 (38/13) | -/0 | 0.93 | -0.126 (-2.17) 68 | 0.93 | -0.027 (-0.42) | fail |
| NS4-pm-vwap-reclaim-oversold-short | primary | -0.070 (-2.16) 1424 | -0.095 (-1.64) 540 | -0.090 (-1.53) 137 | -0.161 / +0.158 (76/16) | 0.0/4 | 0.56 | -0.038 (-0.73) 107 | 0.61 | +0.005 (0.06) | fail |
| exhaustion_short-FD | testing | -0.058 (-3.40) 26968 | +0.011 (0.16) 1843 | -0.073 (-1.74) 434 | -0.094 / +0.105 (194/119) | 0.21/14 | 0.70 | -0.204 (-4.29) 548 | 0.74 | -0.084 (-1.18) | fail |
| MF1-945-flowsell-vwapup-FD | testing | -0.082 (-6.01) 10067 | -0.138 (-4.77) 613 | -0.129 (-2.79) 119 | -0.163 / +0.150 (58/15) | 0.0/1 | 0.75 | -0.119 (-2.41) 87 | 0.78 | +0.008 (0.15) | fail |
| MF2-open-rsimidhi-flowsell-FD | testing | -0.050 (-2.31) 4352 | -0.082 (-2.32) 693 | -0.137 (-2.26) 115 | -0.118 / -0.095 (33/42) | 0.0/2 | 0.55 | -0.183 (-3.01) 91 | 0.54 | -0.055 (-0.81) | fail |
| MF3-open-flowsell-rsi5hi-FD | testing | -0.074 (-4.20) 10119 | -0.090 (-2.91) 1205 | -0.147 (-2.93) 193 | -0.140 / -0.137 (67/54) | 0.0/7 | 0.85 | -0.071 (-1.28) 167 | 0.87 | -0.057 (-1.04) | fail |
| MF4-h40-open-flowsell-FD | testing | -0.081 (-4.48) 6973 | -0.111 (-3.80) 609 | -0.123 (-2.10) 95 | -0.126 / +0.063 (38/16) | 0.0/1 | 0.65 | -0.063 (-1.26) 84 | 0.68 | -0.013 (-0.19) | fail |
| MF5-flowsell-vwapup-rsi5hi-FD | testing | -0.057 (-2.58) 6526 | -0.115 (-3.04) 466 | -0.143 (-2.58) 82 | -0.237 / +0.118 (38/13) | -/0 | 0.93 | -0.126 (-2.17) 68 | 0.93 | -0.027 (-0.42) | fail |
| NS1-rsidip-rsi5pop-long-FD | testing | -0.070 (-3.41) 2374 | -0.037 (-1.27) 530 | -0.010 (-0.20) 143 | -0.029 / +0.109 (71/33) | 0.33/3 | 0.49 | -0.007 (-0.15) 125 | 0.63 | +0.027 (0.50) | fail |
| NS2-sma50break-overbought-short-FD | testing | -0.053 (-1.73) 7836 | -0.049 (-1.66) 2188 | -0.023 (-0.78) 712 | -0.082 / +0.060 (341/143) | 0.44/16 | 0.79 | -0.031 (-0.91) 652 | 0.86 | +0.026 (0.71) | fail |
| NS3-failed-vwap-reclaim-short-FD | testing | -0.023 (-1.13) 9656 | -0.031 (-0.86) 3785 | -0.063 (-1.93) 791 | -0.096 / -0.047 (167/305) | 0.41/17 | 0.75 | -0.027 (-0.89) 740 | 0.82 | -0.032 (-0.69) | fail |
| NS4-pm-vwap-reclaim-oversold-short-FD | testing | -0.060 (-2.07) 1645 | -0.096 (-1.66) 538 | -0.090 (-1.53) 137 | -0.161 / +0.158 (76/16) | 0.0/4 | 0.56 | -0.038 (-0.73) 107 | 0.61 | +0.006 (0.07) | fail |
| NS5-sma50-flush-oversold-long-FD | testing | -0.052 (-0.98) 3036 | -0.015 (-0.29) 714 | -0.020 (-0.38) 212 | +0.143 / -0.074 (52/100) | 0.33/9 | 0.78 | -0.079 (-1.97) 207 | 0.90 | -0.004 (-0.06) | fail |
| RW6G1-ns2-up3-vwap2sd-short-FD | testing | -0.004 (-0.06) 1892 | -0.052 (-1.60) 796 | +0.003 (0.08) 254 | -0.057 / +0.158 (116/60) | 0.69/13 | 0.81 | -0.049 (-0.96) 205 | 0.86 | +0.055 (1.08) | fail |
| L3-gap-slope-rsi5hi-FD | testing | -0.025 (-0.83) 5476 | +0.094 (1.35) 514 | -0.015 (-0.20) 87 | -0.008 / -0.090 (35/37) | 0.5/2 | 0.41 | -0.048 (-0.66) 113 | 0.49 | -0.109 (-1.10) | fail |
| L3-gap-slope-lowdist-FD | testing | -0.094 (-1.60) 3981 | +0.082 (0.62) 441 | -0.079 (-0.70) 93 | -0.113 / -0.058 (52/28) | 0.0/1 | 0.59 | +0.028 (0.42) 98 | 0.80 | -0.161 (-1.03) | fail |
| L3-gap-slope-fromopen-FD | testing | -0.035 (-0.96) 4662 | -0.022 (-0.25) 252 | +0.130 (1.77) 90 | +0.024 / +0.453 (61/18) | 1.0/1 | 0.73 | -0.078 (-0.60) 90 | 0.87 | +0.152 (1.33) | fail (t, WF folds) |
| ST1-ordn-long-pm-t05s1-FD | testing | -0.054 (-2.07) 1536 | +0.126 (2.92) 252 | -0.130 (-1.83) 68 | -0.145 / -0.238 (17/31) | 1.0/1 | 0.52 | -0.007 (-0.12) 71 | 0.65 | -0.256 (-3.23) | fail |
| ST2-slope20up-long-am-t05s1-FD | testing | -0.013 (-0.70) 10427 | -0.026 (-0.67) 2613 | -0.020 (-0.53) 615 | +0.062 / -0.048 (113/305) | 0.44/16 | 0.46 | -0.004 (-0.14) 613 | 0.59 | +0.006 (0.14) | fail |
| ST3-rsi5up-short-pm-t1s1-FD | testing | +0.013 (0.31) 637 | +0.135 (2.20) 166 | -0.010 (-0.12) 67 | -0.171 / +0.345 (14/15) | 0.0/2 | 0.76 | -0.038 (-0.47) 59 | 0.88 | -0.145 (-1.38) | fail |
| ST4-emadn-long-am-t1s05-FD | testing | +0.022 (0.70) 1238 | -0.078 (-2.14) 427 | -0.017 (-0.24) 108 | -0.092 / -0.133 (19/51) | 0.75/4 | 0.61 | -0.072 (-0.75) 101 | 0.54 | +0.061 (0.75) | fail |
| ST5-pdbrkup-short-mid-t05s1-FD | testing | -0.032 (-0.73) 406 | +0.004 (0.03) 19 | +0.285 (3.22) 4 | - / +0.322 (0/2) | -/0 | 0.50 | +0.003 1 | 1.00 | +0.282 (1.71) | fail (n 4) |
| ST6-volspikeup-short-mid-t1s1-FD | testing | +0.021 (0.57) 590 | -0.049 (-1.00) 242 | -0.027 (-0.37) 81 | -0.051 / +0.315 (11/16) | 0.0/2 | 0.80 | -0.068 (-1.38) 74 | 0.92 | +0.022 (0.28) | fail |
| ST7-rsi50dn-long-pm-t1s1-FD | testing | +0.032 (0.68) 998 | +0.153 (1.43) 111 | -0.030 (-0.23) 25 | +0.201 / +0.091 (3/12) | -/0 | 0.68 | -0.220 (-2.17) 24 | 0.92 | -0.183 (-1.09) | fail |
| ST8-volspikedn-long-pm-t1s1-FD | testing | +0.049 (0.98) 517 | +0.112 (2.02) 336 | -0.140 (-1.94) 141 | +0.111 / -0.239 (30/68) | 0.2/5 | 0.72 | -0.004 (-0.09) 194 | 0.81 | -0.252 (-2.87) | fail |
| RW4-ns3-adv150-short-FD | testing | -0.026 (-1.19) 7643 | -0.035 (-0.91) 2994 | -0.067 (-1.93) 621 | -0.088 / -0.040 (139/228) | 0.29/17 | 0.76 | -0.034 (-1.06) 553 | 0.84 | -0.032 (-0.65) | fail |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | testing | -0.055 (-2.35) 5318 | -0.066 (-1.91) 730 | -0.109 (-1.91) 122 | -0.213 / +0.061 (37/36) | 0.5/2 | 0.85 | -0.129 (-2.02) 108 | 0.92 | -0.043 (-0.68) | fail |
| RW6-ns2-up3-short-FD | testing | -0.019 (-0.47) 3492 | -0.027 (-0.84) 987 | -0.015 (-0.40) 344 | -0.091 / +0.108 (164/71) | 0.46/13 | 0.78 | -0.053 (-0.97) 303 | 0.84 | +0.013 (0.29) | fail |
| RW1-gapdn-bounce-flowsell-short-FD | testing | -0.047 (-2.17) 7084 | -0.036 (-0.95) 801 | -0.078 (-1.39) 124 | -0.153 / -0.031 (41/43) | 0.5/2 | 0.82 | -0.058 (-1.29) 115 | 0.91 | -0.042 (-0.64) | fail |
| RW2-exhaustion-noon-adv150-short-FD | testing | -0.056 (-3.17) 21023 | +0.018 (0.26) 1496 | -0.040 (-0.81) 333 | -0.094 / +0.189 (152/88) | 0.39/13 | 0.72 | -0.217 (-3.55) 429 | 0.76 | -0.057 (-0.77) | fail |
| RW3-gapdn-rsi5pop-flowsell-short-FD | testing | -0.072 (-3.21) 5666 | -0.081 (-2.29) 665 | -0.012 (-0.19) 107 | -0.100 / +0.171 (36/42) | 0.67/3 | 0.79 | -0.008 (-0.15) 82 | 0.94 | +0.069 (1.02) | fail |
| RW7-gapdn-bounce-early-short-FD | testing | -0.059 (-2.96) 24803 | -0.061 (-1.89) 3069 | -0.081 (-2.03) 543 | -0.210 / +0.046 (148/213) | 0.31/16 | 0.80 | -0.091 (-2.98) 463 | 0.91 | -0.020 (-0.46) | fail |
| heat_fade_short-FD | testing | -0.032 (-2.30) 71537 | -0.030 (-1.16) 9417 | -0.066 (-2.36) 1995 | -0.079 / -0.086 (481/776) | 0.47/17 | 0.83 | +0.002 (0.06) 2005 | 0.89 | -0.036 (-1.19) | fail |
| heat_fade_long-FD | testing | -0.033 (-1.30) 22563 | +0.043 (1.14) 1692 | +0.017 (0.41) 526 | +0.019 / +0.012 (82/310) | 0.39/13 | 0.72 | +0.078 (1.16) 533 | 0.79 | -0.027 (-0.44) | fail |

L1 exp > 0 in 4 of 35 setups and L2 in 4 of 35 (about what noise around a slightly negative mean gives); the best,
L3-gap-slope-fromopen-FD L1 +0.130R (t 1.77, n 90, 1 walk-forward fold), is below the try-count bar 2.94 and has too few
trades and folds. Primary gate verdicts (N = lineage tries + 76): exhaustion_short current / 15:15 / 15:30 = rework
(t 0.34 / 0.12 / -0.51 vs 5.23); MF5 rework (t -2.58 / -2.66 / -2.71 vs 4.24); NS4 rework (t -2.16 / -2.36 / -2.42 vs
4.22). Extending makes all three slightly worse.

## Verdict
- **Primary account: do not extend.** No primary setup passes the gates on any cutoff, and the 15:05-15:30 entries of
  exhaustion_short / MF5 / NS4 are worse than their existing trades (pooled L1 -0.085R, L2 -0.163R).
- **Testing account: do not extend (study rule).** The pooled late buckets are negative (L1 -0.052R t -3.69, L2 -0.046R
  t -2.32, also after one-per-symbol-day) and negative in up AND down sessions for L1; no single -FD setup qualifies.
  The late bucket is roughly as bad as the rest of the full-day book (difference t -0.46), so extending would add
  ~23 trades/day (~3%) of the same negative expectancy plus mostly 15:55-flatten exits. If the owner still wants the
  data (owner-directed forward test), it can be done, but it needs a code change, not only YAML (below).
- **Answer to the owner:** yes - today both accounts take no new entries after the 15:00 bar close (LabStrategy and
  HeatStrategy clamp every window with `min(1500, hi)`), and positions are flattened at 15:55. On two years of lab
  history, entries 15:05-15:30 lose about 0.05R per trade after costs for the Testing book and 0.08-0.16R for the
  primary setups that run to 15:00; three quarters of them are closed by the 15:55 flatten before reaching target or
  stop. A 15:15 cutoff is not worth it on this evidence.

### If the owner directs the Testing extension anyway (NOT proposed by this study)
Code (setup change; after the close; `setup-freeze` applies):
- mcf/strategies/setups.py lines ~349 and ~455: `min(1500, hi)` -> `min(1515, hi)` (HeatStrategy and LabStrategy
  generate), and the default window `(950, 1500)` stays; `eligible` already honours the YAML hi.
- research/bdi/fullday/heat_fade_short-FD.py / heat_fade_long-FD.py: `regime_score(df, ..., 950, 1500, ...)` ->
  `950, 1515` (the heat score carries the window; YAML alone does not widen it).
- The primary YAML keeps `[1300, 1500]`, `[950, 1500]`, `[1130, 1500]`, so the code change alone does not move the
  primary account.
YAML (config/account_testing.yaml), every one of the 32 -FD entries:
```yaml
    window: [950, 1515]     # was [950, 1500]; owner-directed late-entry forward test (research/bdi/cutoff)
```
Ledger text (only if approved):
- what changes: "Testing account only: the 32 full-day (-FD) setups may enter on 5-minute bars closing up to 15:15
  ET instead of 15:00. Exits unchanged (same target/stop, flatten at 15:55). Primary account unchanged."
- what you should see: "About 23 more Testing trades per day (~3% more), entered 15:05-15:15, about three in four of
  them closed by the 15:55 flatten rather than target or stop. Lab history expects them to lose about 0.05R each after
  costs (-0.052R, t -3.7, n 9,381 over 406 sessions), i.e. roughly -1.2R per day for the account; the
  rest of the book is unaffected."
