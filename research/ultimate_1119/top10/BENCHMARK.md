# TOP-10 benchmark: the "normal filter way" (ultimate_1119, owner 2026-11-19)

*Educational only — not financial advice. Research only. No setup, exit, config, account or ledger change. Configurations
tried: **0 fitted**. The 10 setups (+ ST7-FD as an 11th reference row) were scored with their fixed live rules, booked
two ways (home-account book and testing-rules book). Job cumulative N stays ~1,882. The locked block
2024-11-01..2025-02-28 was never read.*

Files: `bench10.py` (engine), `live10.py` (live pick), `live_top10.json`, `benchmark.json`, `PLAN.md` (the
pre-registered admission rule, written before any variant was scored). Trade lists are in the session scratchpad
(`top10w/`, ~9 MB) and can be regenerated.

## 1. Which 10: the live leaderboard
Source: the journal export used by every ultimate_1119 round, 2026-10-06..11-18. All accounts are pooled, Primary
included. R is after costs on the one LR8 basis. Of 139 setups with >= 20 live trades, 127 are eligible. Twelve GEN-*
setups are excluded as one-day records: their best day is >= 50% of total R. Four of them would otherwise have ranked
in the top 10: GEN-261020-09 (+59.8R, share 121%), GEN-261021-02 (+20.0R, 166%), GEN-261026-03 (+10.6R, 56%) and
GEN-261027-08 (+7.4R, 93%).

| # total R | setup (home account now) | live trades | traded sessions | total R | avg R | # avg R | avg R w/o best day | best-day share | worst day |
|---|---|---|---|---|---|---|---|---|---|
| 1 | L3-gap-slope-fromopen-FD (Primary) | 397 | 24 | +80.9 | +0.204 | 5 | +0.156 | 0.39 | −13.7 |
| 2 | RW3-gapdn-rsi5pop-flowsell-short-FD (Primary) | 199 | 27 | +27.7 | +0.139 | 6 | +0.025 | 0.85 **1 day** | −10.2 |
| 3 | L3-gap-slope-lowdist-FD (Testing 1) | 109 | 19 | +25.2 | +0.231 | 2 | +0.091 | 0.72 **1 day** | −2.5 |
| 4 | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (Primary) | 206 | 27 | +22.7 | +0.110 | 7 | +0.022 | 0.83 **1 day** | −15.5 |
| 5 | L3-gap-slope-rsi5hi-FD (Testing 1) | 158 | 23 | +14.1 | +0.089 | 10 | +0.007 | 0.94 **1 day** | −3.6 |
| 6 | RW6-ns2-up3-short-FD (Live Lab / Testing C) | 197 | 25 | +11.3 | +0.057 | 12 | −0.222 | 3.38 **1 day** | −21.3 |
| 7 | NM-RWN4-ns2-spyup05-notfri-short (Testing F) | 40 | 2 | +8.9 | +0.223 | 3 | −0.066 | 1.06 **1 day** | −0.5 |
| 8 | CWT14-failbrk-orl-p10-long-WB5 (Testing D) | 75 | 2 | +7.7 | +0.103 | 9 | −0.199 | 1.10 **1 day** | −0.8 |
| 9 | NM-ETF-late-dip-di-long (Primary) | 30 | 14 | +7.4 | +0.248 | 1 | +0.235 | 0.18 | −0.6 |
| 10 | CWT09-gapdn-vwaploss-g10-short (Testing 1) | 24 | 13 | +5.2 | +0.218 | 4 | +0.141 | 0.49 | −1.4 |
| (11) | ST7-rsi50dn-long-pm-t1s1-FD (Primary), reference only | 50 | 18 | +4.0 | +0.081 | 11 | +0.002 | 0.98 **1 day** | −2.8 |

"# avg R" is the avg-R rank among the 127 eligible setups. The top 10 by avg R are the same set, except that
NM-RWR4-ns2-up3-qqqup-slopedn-short (#8 by avg R, +0.107, 32 trades, total R rank 12) replaces RW6-FD.

**Seven of the 10 live records carry the `1 day` tag.** NM-RWN4 and CWT14-orl-WB5 have only 2 traded sessions each.
Only NM-ETF-late-dip, L3-fromopen and CWT09-g10 have a live record that is not mostly one day.

**Rule-change context inside the live window 2026-10-06..11-18** (research/ledger.jsonl):
- refire option B, 10-14;
- L3-fromopen moved Testing 1 → Primary 10-20, back 10-22, then to Primary again 10-30;
- per-setup daily-stop latch 10-23, switched off in Testing 1/2 the same day;
- Primary position size ~$5k then ~$4k, per-setup cap 30, 10-28;
- Primary −2R per-setup latch 10-29;
- Testing 1/2 cost filter 0.15R 10-30;
- L3-rsi5hi to Primary 10-30, back to Testing 11-11;
- Explore 1 / Live Lab low-rep homes 11-05;
- TEAM-6 Primary, with NM-ETF moved Live Lab → Primary, 11-11;
- LR3 latch in cost R, and the LR8 live cost model, 11-12 (every live figure here is on the one LR8 basis);
- Testing D/E/F accounts 11-12;
- RW6 Graveyard → Live Lab 11-13 (it was in the Graveyard 10-21..11-13);
- Testing A-F half-size lots 11-17 (R comparable);
- Workbench copies (-WB*) and the SPYEXIT engine 11-17 (CWT14-orl-WB5 itself is a 11-17 Workbench copy, so its whole
  record falls after that date);
- GY-BENCH guests 11-18.

Live records pool every account a setup ran in. The backtests below apply today's rule set to every session, so no rule
change falls inside them.

## 2. Method: the "normal filter way" (bench10.py)
- **Signals.** The setup's live module `mask()`, YAML window (bar close 09:50..15:00), `min_adv` on point-in-time
  ADV20, gap prefilter, and the refire chain (`mcf.strategies.setups.refire_select`, the setup's own cooldown) or
  first hit per symbol-day, all from its **home account's** config block. The CWT modules get the 09:35-09:45 bars, as
  live. For T1 they come from `research/bdi/cwt/test_b/data/headtail.parquet`; for T2 they are built from the 1-minute
  bars. Structural stops/targets (CWT09, CWT14-WB5) come from the module's `stop_price` / `target_price`.
- **Exits.** Entry at the decision-bar close. The walk is minute by minute on 1-minute bars: stop first (a gap-through
  fills at the worse of open/stop); a target fills only when traded through by >= $0.01 (the Workbench rule); flat at
  the 15:55 open.
- **Costs.** LR8 research basis, as every round: entry (1c + 1 bp) × time-of-day multiplier; exit 1c + 1 bp except
  target limit fills; +2c on stops; ×3 extended tier. Shorts pay +1.2 bp of entry notional for borrow.
- **The live book. This is the fix for round 1's uncapped lab pipeline.** The rules come from mcf/execution/risk.py
  and runner.py with the merged account configs:
  - per-setup open-lot cap: Primary 30, Testing 1 150, Testing 2/C/D/F 100;
  - at most 3 lots per symbol (`max_lots_per_symbol` 3, same-setup re-entry allowed);
  - price at least $5;
  - Primary: −2R per-setup daily latch on realized cost-R;
  - testing accounts: the 0.15R stop-cost filter;
  - shorts only when easy to borrow (>= 90% of 26 universe snapshots 10-07..11-13, the Workbench's E90 proxy).

  The book cuts L3-fromopen from 42,844 raw signals (~96/session) to 4,839 trades (10.9/session). Live ran ~17 per
  traded session.
- **Tests.**
  - T1: the lab frames (1,199-1,226 symbols; survivorship bias). Fit = 2024-10 + 2025-03..09 (170 sessions), check =
    2025-10-01..2026-11-04 (276 sessions), and combined (446).
  - T2: 2023-01-03..2024-09-13 (427 sessions). Frames were built from `data/cache_fresh/1Min` with the history2y build
    (469 symbols with bars, 468 framed; the task's "484" is the download list). Context `spy_fo` comes from
    cache_fresh/ctx.parquet.
  - T3: the recorded-quote replay. Only 2026-11-18 exists.
- **SPY day type:** 09:30 open to 16:00 close; up >= +0.30%, down <= −0.30%.
- **Known biases, all stated and none fixed:**
  - the lab universe is ~1,200 names against ~4,200 live. Only 40-48% of the L3 family's live symbol-days in
    2026-10-06..11-04 are in the backtest;
  - no earnings blackout in the backtest (CWT09 live excludes earnings gaps);
  - no spread / quote-crosscheck / U9 skips;
  - ETB uses today's flags;
  - account-wide slot and buying-power limits are not modelled (per-setup books only).

## 3. Per setup per test (home-account book; R after costs)

### T1 combined (fit + check, 446 sessions)

| setup | home acct | trades | /session | win | avg R | avg R w/o best day | best-day share | total R/session | worst day | day-t | SPY up / flat / down avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L3-fromopen | primary | 4839 | 10.85 | 0.488 | -0.085 | -0.094 | n/a (total<0) | -0.922 | -30.5 | -2.84 | -0.210 / -0.052 / +0.056 |
| RW3-FD | primary | 5000 | 11.21 | 0.482 | -0.080 | -0.087 | n/a (total<0) | -0.899 | -20.5 | -3.41 | -0.313 / -0.051 / +0.099 |
| L3-lowdist | testing | 3035 | 6.80 | 0.470 | -0.107 | -0.133 | n/a (total<0) | -0.732 | -173.1 | -1.64 | -0.304 / +0.068 / +0.152 |
| RW5-FD | primary | 4627 | 10.37 | 0.491 | -0.076 | -0.082 | n/a (total<0) | -0.790 | -27.9 | -3.01 | -0.340 / -0.010 / +0.114 |
| L3-rsi5hi | testing | 6313 | 14.15 | 0.668 | -0.010 | -0.037 | n/a (total<0) | -0.137 | -127.8 | -0.23 | -0.066 / +0.063 / +0.034 |
| RW6-FD | livelab | 3454 | 7.74 | 0.496 | -0.031 | -0.058 | n/a (total<0) | -0.241 | -41.9 | -0.82 | -0.111 / +0.005 / +0.098 |
| NM-RWN4 | testingf | 696 | 1.56 | 0.730 | +0.070 | +0.025 | 0.69 **1 day** | +0.109 | -9.3 | 0.99 | +0.045 / +0.144 / +0.427 |
| CWT14-orl-WB5 | testingd | 17002 | 38.12 | 0.687 | -0.025 | -0.028 | n/a (total<0) | -0.971 | -42.4 | -2.55 | +0.075 / -0.023 / -0.203 |
| NM-ETF-late-dip | primary | 488 | 1.09 | 0.715 | +0.140 | +0.105 | 0.33 | +0.154 | -6.1 | 3.01 | +0.187 / +0.150 / +0.105 |
| CWT09-g10 | testing | 626 | 1.40 | 0.495 | +0.054 | -0.017 | 1.30 **1 day** | +0.076 | -8.2 | 0.67 | -0.234 / +0.171 / +0.169 |
| ST7-FD (ref, 11th) | primary | 1073 | 2.41 | 0.541 | +0.050 | +0.042 | 0.18 | +0.121 | -26.4 | 1.1 | +0.201 / +0.055 / -0.078 |
| **median of top 10** | | | 9.06 | | **-0.0283** | **-0.0474** | | **-0.4862** | | | |
| best of top 10 | | | | | +0.1403 | +0.1050 | | +0.1536 | | | |

### T1 fit (2024-10 + 2025-03..09, 170 sessions)

| setup | home acct | trades | /session | win | avg R | avg R w/o best day | best-day share | total R/session | worst day | day-t | SPY up / flat / down avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L3-fromopen | primary | 1488 | 8.75 | 0.464 | -0.134 | -0.155 | n/a (total<0) | -1.171 | -30.5 | -2.71 | -0.250 / -0.166 / +0.060 |
| RW3-FD | primary | 1753 | 10.31 | 0.447 | -0.139 | -0.153 | n/a (total<0) | -1.429 | -20.5 | -3.51 | -0.342 / -0.079 / +0.022 |
| L3-lowdist | testing | 1261 | 7.42 | 0.468 | -0.112 | -0.178 | n/a (total<0) | -0.831 | -173.1 | -0.78 | -0.443 / +0.147 / +0.186 |
| RW5-FD | primary | 1651 | 9.71 | 0.464 | -0.121 | -0.132 | n/a (total<0) | -1.172 | -27.9 | -2.93 | -0.406 / +0.001 / +0.094 |
| L3-rsi5hi | testing | 2268 | 13.34 | 0.694 | +0.010 | -0.076 | 7.02 **1 day** | +0.128 | -127.8 | 0.1 | +0.024 / +0.065 / -0.024 |
| RW6-FD | livelab | 1013 | 5.96 | 0.525 | +0.027 | -0.066 | 2.69 **1 day** | +0.162 | -18.0 | 0.36 | +0.021 / +0.004 / +0.069 |
| NM-RWN4 | testingf | 397 | 2.33 | 0.736 | +0.070 | -0.020 | 1.22 **1 day** | +0.162 | -9.3 | 0.72 | +0.045 / +0.013 / +0.422 |
| CWT14-orl-WB5 | testingd | 4287 | 25.22 | 0.684 | -0.029 | -0.036 | n/a (total<0) | -0.741 | -22.4 | -1.69 | +0.077 / -0.029 / -0.182 |
| NM-ETF-late-dip | primary | 226 | 1.33 | 0.823 | +0.256 | +0.200 | 0.39 | +0.340 | -2.8 | 4.35 | +0.243 / +0.184 / +0.279 |
| CWT09-g10 | testing | 221 | 1.30 | 0.507 | +0.053 | +0.009 | 0.86 **1 day** | +0.069 | -2.7 | 0.8 | -0.144 / +0.013 / +0.187 |
| ST7-FD (ref, 11th) | primary | 240 | 1.41 | 0.467 | -0.099 | -0.147 | n/a (total<0) | -0.140 | -26.4 | -0.75 | +0.486 / -0.038 / -0.386 |
| **median of top 10** | | | 8.09 | | **-0.0099** | **-0.0713** | | **-0.3358** | | | |
| best of top 10 | | | | | +0.2557 | +0.2004 | | +0.3399 | | | |

### T1 check (2025-10-01..2026-11-04, 276 sessions)

| setup | home acct | trades | /session | win | avg R | avg R w/o best day | best-day share | total R/session | worst day | day-t | SPY up / flat / down avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L3-fromopen | primary | 3351 | 12.14 | 0.498 | -0.063 | -0.075 | n/a (total<0) | -0.769 | -25.6 | -1.73 | -0.189 / -0.017 / +0.053 |
| RW3-FD | primary | 3247 | 11.76 | 0.500 | -0.049 | -0.059 | n/a (total<0) | -0.572 | -16.1 | -1.7 | -0.293 / -0.038 / +0.139 |
| L3-lowdist | testing | 1774 | 6.43 | 0.472 | -0.104 | -0.117 | n/a (total<0) | -0.670 | -50.3 | -2.37 | -0.224 / +0.051 / +0.064 |
| RW5-FD | primary | 2976 | 10.78 | 0.506 | -0.051 | -0.060 | n/a (total<0) | -0.555 | -19.3 | -1.62 | -0.293 / -0.016 / +0.123 |
| L3-rsi5hi | testing | 4045 | 14.66 | 0.653 | -0.020 | -0.034 | n/a (total<0) | -0.299 | -80.1 | -0.57 | -0.120 / +0.062 / +0.108 |
| RW6-FD | livelab | 2441 | 8.84 | 0.484 | -0.055 | -0.067 | n/a (total<0) | -0.488 | -41.9 | -1.44 | -0.194 / +0.005 / +0.109 |
| NM-RWN4 | testingf | 299 | 1.08 | 0.722 | +0.071 | -0.058 | 1.59 **1 day** | +0.077 | -7.6 | 0.68 | +0.044 / +0.256 / +0.451 |
| CWT14-orl-WB5 | testingd | 12715 | 46.07 | 0.688 | -0.024 | -0.027 | n/a (total<0) | -1.112 | -42.4 | -2.01 | +0.075 / -0.022 / -0.212 |
| NM-ETF-late-dip | primary | 262 | 0.95 | 0.622 | +0.041 | +0.028 | 0.35 | +0.039 | -6.1 | 0.82 | +0.098 / +0.143 / -0.070 |
| CWT09-g10 | testing | 405 | 1.47 | 0.489 | +0.054 | -0.056 | 2.00 **1 day** | +0.080 | -8.2 | 0.45 | -0.282 / +0.216 / +0.153 |
| ST7-FD (ref, 11th) | primary | 833 | 3.02 | 0.563 | +0.093 | +0.083 | 0.12 | +0.281 | -8.5 | 2.23 | +0.136 / +0.071 / +0.086 |
| **median of top 10** | | | 9.81 | | **-0.0364** | **-0.0581** | | **-0.5218** | | | |
| best of top 10 | | | | | +0.0709 | +0.0277 | | +0.0796 | | | |

### T2 (2023-01-03..2024-09-13, 427 sessions, 469-symbol cache)

| setup | home acct | trades | /session | win | avg R | avg R w/o best day | best-day share | total R/session | worst day | day-t | SPY up / flat / down avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| L3-fromopen | primary | 1451 | 3.40 | 0.491 | -0.120 | -0.128 | n/a (total<0) | -0.408 | -20.9 | -2.93 | -0.243 / -0.045 / +0.055 |
| RW3-FD | primary | 1701 | 3.98 | 0.477 | -0.105 | -0.112 | n/a (total<0) | -0.417 | -16.2 | -3.37 | -0.397 / -0.072 / +0.187 |
| L3-lowdist | testing | 410 | 0.96 | 0.480 | -0.086 | -0.125 | n/a (total<0) | -0.082 | -25.6 | -0.96 | -0.295 / +0.175 / +0.198 |
| RW5-FD | primary | 1891 | 4.43 | 0.453 | -0.143 | -0.149 | n/a (total<0) | -0.631 | -19.8 | -4.53 | -0.397 / -0.087 / +0.143 |
| L3-rsi5hi | testing | 845 | 1.98 | 0.615 | -0.084 | -0.103 | n/a (total<0) | -0.166 | -25.5 | -2.04 | -0.169 / -0.017 / +0.119 |
| RW6-FD | livelab | 605 | 1.42 | 0.534 | +0.034 | +0.010 | 0.71 **1 day** | +0.048 | -6.1 | 0.67 | -0.100 / +0.294 / +0.168 |
| NM-RWN4 | testingf | 104 | 0.24 | 0.654 | -0.049 | -0.103 | n/a (total<0) | -0.012 | -3.1 | -0.71 | -0.138 / +0.193 / +0.242 |
| CWT14-orl-WB5 | testingd | 4833 | 11.32 | 0.685 | -0.040 | -0.043 | n/a (total<0) | -0.450 | -20.1 | -2.56 | +0.067 / -0.013 / -0.263 |
| NM-ETF-late-dip | primary | 250 | 0.58 | 0.580 | -0.037 | -0.056 | n/a (total<0) | -0.021 | -8.2 | -0.59 | -0.167 / +0.002 / +0.032 |
| CWT09-g10 | testing | 192 | 0.45 | 0.359 | -0.181 | -0.209 | n/a (total<0) | -0.081 | -8.1 | -2.68 | -0.413 / -0.147 / +0.155 |
| ST7-FD (ref, 11th) | primary | 261 | 0.61 | 0.502 | -0.097 | -0.113 | n/a (total<0) | -0.059 | -7.7 | -1.28 | +0.330 / -0.122 / -0.398 |
| **median of top 10** | | | 1.70 | | **-0.0848** | **-0.1072** | | **-0.1242** | | | |
| best of top 10 | | | | | +0.0340 | +0.0102 | | +0.0481 | | | |

### Testing-rules view (every setup booked as a testing-arena setup: cap 100, cost filter 0.15R, no latch) — avg R / w/o best / R per session

| setup | T1 combined | T1 check | T2 |
|---|---|---|---|
| L3-fromopen | -0.070 / -0.076 / -2.054 (n 13109) | -0.071 / -0.082 / -2.106 (n 8183) | +0.045 / +0.018 / +0.208 (n 1975) |
| RW3-FD | -0.051 / -0.057 / -0.522 (n 4566) | -0.028 / -0.037 / -0.302 (n 3007) | -0.087 / -0.095 / -0.268 (n 1320) |
| L3-lowdist | -0.106 / -0.132 / -0.722 (n 3024) | -0.105 / -0.117 / -0.671 (n 1771) | -0.086 / -0.125 / -0.082 (n 410) |
| RW5-FD | -0.040 / -0.046 / -0.363 (n 4075) | -0.030 / -0.039 / -0.291 (n 2656) | -0.100 / -0.106 / -0.336 (n 1435) |
| L3-rsi5hi | -0.017 / -0.040 / -0.230 (n 6131) | -0.025 / -0.038 / -0.353 (n 3933) | -0.084 / -0.103 / -0.166 (n 845) |
| RW6-FD | -0.031 / -0.058 / -0.241 (n 3454) | -0.055 / -0.067 / -0.488 (n 2441) | +0.034 / +0.010 / +0.048 (n 605) |
| NM-RWN4 | +0.070 / +0.025 / +0.109 (n 696) | +0.071 / -0.058 / +0.077 (n 299) | -0.049 / -0.103 / -0.012 (n 104) |
| CWT14-orl-WB5 | -0.025 / -0.028 / -0.971 (n 17002) | -0.024 / -0.027 / -1.112 (n 12715) | -0.040 / -0.043 / -0.450 (n 4833) |
| NM-ETF-late-dip | +0.150 / +0.115 / +0.162 (n 482) | +0.049 / +0.035 / +0.045 (n 252) | -0.039 / -0.059 / -0.023 (n 245) |
| CWT09-g10 | +0.054 / -0.017 / +0.076 (n 626) | +0.054 / -0.056 / +0.080 (n 405) | -0.181 / -0.209 / -0.081 (n 192) |
| ST7-FD (ref, 11th) | +0.074 / +0.064 / +0.152 (n 919) | +0.121 / +0.109 / +0.316 (n 721) | -0.064 / -0.081 / -0.028 (n 184) |

### Coverage, raw signals vs booked, and the live overlap window (2026-10-06..11-04)

| setup | T1 raw signals | T1 booked | T2 raw | T2 booked | T2 symbols traded | live trades in overlap | live avg R | backtest trades | backtest avg R | live symbol-days found in backtest |
|---|---|---|---|---|---|---|---|---|---|---|
| L3-fromopen | 42844 | 4839 | 8492 | 1451 | 166 | 256 | +0.141 | 330 | +0.053 | 43% |
| RW3-FD | 6306 | 5000 | 1895 | 1701 | 363 | 104 | +0.262 | 269 | +0.086 | 83% |
| L3-lowdist | 4361 | 3035 | 822 | 410 | 164 | 59 | -0.009 | 145 | -0.212 | 48% |
| RW5-FD | 5879 | 4627 | 2151 | 1891 | 377 | 125 | +0.308 | 262 | +0.087 | 72% |
| L3-rsi5hi | 10462 | 6313 | 2002 | 845 | 160 | 85 | +0.075 | 260 | -0.089 | 40% |
| RW6-FD | 4734 | 3454 | 913 | 605 | 192 | 74 | -0.370 | 179 | -0.020 | 64% |
| NM-RWN4 | 953 | 696 | 132 | 104 | 86 | 8 | -0.066 | 41 | -0.012 | 62% |
| CWT14-orl-WB5 | 17017 | 17002 | 4833 | 4833 | 319 | 0 | — | 964 | -0.006 | — |
| NM-ETF-late-dip | 495 | 488 | 256 | 250 | 21 | 10 | +0.248 | 25 | +0.006 | 100% |
| CWT09-g10 | 1021 | 626 | 238 | 192 | 116 | 12 | +0.377 | 43 | +0.211 | 67% |
| ST7-FD (ref, 11th) | 1114 | 1073 | 262 | 261 | 185 | 35 | +0.079 | 85 | +0.175 | 91% |

### T3 — recorded-quote replay (research/reps2, 2026-11-18 only)

| setup | account | live trades | replay trades | match | live avg R | replay avg R |
|---|---|---|---|---|---|---|
| L3-fromopen | primary | 19 | 19 | 100% | -0.130 | -0.155 |
| RW3-FD | primary | 14 | 14 | 100% | -0.288 | -0.300 |
| L3-lowdist | testing | 1 | 1 | 100% | +0.951 | +1.053 |
| RW5-FD | primary | 8 | 8 | 100% | -0.039 | -0.105 |
| L3-rsi5hi | testing | 6 | 6 | 100% | +0.199 | +0.205 |
| RW6-FD | not in the replay (account not covered) | | | | | |
| NM-RWN4 | not in the replay (account not covered) | | | | | |
| CWT14-orl-WB5 | not in the replay (account not covered) | | | | | |
| NM-ETF-late-dip | primary | 3 | 3 | 100% | +0.026 | +0.006 |
| CWT09-g10 | testing | 2 | 2 | 100% | +0.246 | +0.281 |
| ST7-FD (ref, 11th) | primary | 1 | 1 | 100% | -0.562 | -0.554 |

## 4. The benchmark standard (median of the top 10; ST7-FD excluded)
| test | avg R median (best) | avg R w/o best day median (best) | total R/session median (best) | trades/session median |
|---|---|---|---|---|
| T1 combined | **−0.0283** (+0.1403 NM-ETF) | **−0.0474** (+0.1050 NM-ETF) | **−0.4862** (+0.1536 NM-ETF) | 9.06 |
| T1 fit | −0.0099 (+0.2557 NM-ETF) | −0.0713 (+0.2004) | −0.3358 (+0.3399) | 8.09 |
| T1 check | **−0.0364** (+0.0709 NM-RWN4) | **−0.0581** (+0.0277 NM-ETF) | **−0.5218** (+0.0796 CWT09) | 9.81 |
| T2 | **−0.0848** (+0.0340 RW6) | −0.1072 (+0.0102 RW6) | −0.1242 (+0.0481 RW6) | 1.70 |

The testing-rules book (cap 100, cost filter, no latch) gives nearly the same avg-R medians: −0.0283 combined,
−0.0262 check, −0.0664 T2. Its R/session medians are less negative: −0.302 / −0.328 / −0.082.

## 5. Reading it (honest, costs in)
- **The top 10 lose money in this engine.** Only 3 of 10 are positive on T1 combined: NM-ETF-late-dip +0.140 (t
  3.0), NM-RWN4 +0.070 and CWT09-g10 +0.054. NM-RWN4 and CWT09 are one-day records on T1, and both are negative on T2.
  Only RW6 is positive on T2 (+0.034, one-day). Every median is negative, so "meets the standard" means "backtests no
  worse than the setups that are winning live". It does not mean profitable in backtest.
- **Live vs backtest disagree sharply, as round 1 found.** This holds with the live caps in place.
  - In the overlap window 2026-10-06..11-04 the backtest agrees on sign for L3-fromopen (+0.053 vs live +0.141), RW3
    (+0.086 vs +0.262), RW5 (+0.087 vs +0.308), CWT09 (+0.211 vs +0.377) and ST7 (+0.175 vs +0.079). It is far below
    live on every one.
  - Over two years the same setups are clearly negative: L3-fromopen −0.085, RW3 −0.080, RW5 −0.076. The short
    family wins only on SPY-down days (+0.06..+0.15) and loses badly on SPY-up days (−0.21..−0.34).
  - This is the owner's point. Backtest weakness has not predicted live failure for these setups.
- **The pre-registered "REALLY BAD" rule would flag 4 of the 10 current live leaders:**
  - L3-fromopen (−0.085, t −2.84), RW3-FD (−0.080, t −3.41) and RW5-FD (−0.076, t −3.01) on leg 1;
  - L3-lowdist on leg 2 (fit −0.112, check −0.104, T2 −0.086).

  The live #1 setup would therefore have been rejected by that rule. This does not change the rule (it is binding for
  this job), but whoever applies it should know it. A variant flagged REALLY BAD sits in the same bucket as the
  setups now making the most money live.
- **The L3 testing-account books carry huge worst days:** L3-lowdist −173R and L3-rsi5hi −128R on one T1-fit day
  (the April 2025 rally, at 150 lots with no latch). Primary's −2R latch caps these at about −30R.
- **CWT14-orl-WB5 fires ~46 times a session on T1 check** (live: 75 trades in 2 sessions). It is near zero (−0.025)
  with a stable sign across fit, check and T2: long, positive on SPY-up days and negative on down days.
- **T3 is one session** (2026-11-18, 100% match). It cannot rank anything.
