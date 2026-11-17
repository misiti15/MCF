# UPDAY Workbench RESULTS — Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD`: up-day copies
Educational only — not financial advice. Mechanic 2026-11-17, built ~02:00-03:00 UTC (after hours). Research files only:
**no config change, no deploy.** Candidate list (Step A): `../CANDIDATES.md`. Diagnosis: `DIAGNOSIS.md`.

Owner batch 2026-11-17: rework the short setups so they hold up on UP-market days and in good market conditions. These are
copies of the SHORT setup, not conversions to longs. Base = the PARENT (as asked); WB4 (13:00 end + gap ≤ −3.2% + 75-min
hold, deployed Testing A 11-17) used as an alternative base, reported separately.

## Verdict
| copy | change | Session replay avg R | 2-year backtest avg R | verdict |
|---|---|---|---|---|
| parent | — | +0.059 | −0.048 | — |
| **`L3-gap-slope-fromopen-FD-WB5`** (R2d) | **parent + exit at the next 1-min open once SPY has risen +0.30% since entry + no new entries after 12:00 while SPY is > +0.15% above its 09:50 close** | **+0.087** | **−0.014** | **PASS — beats the parent in both tests; up days much better, down days roughly kept. Recommended up-day copy of the parent.** |
| WB4 (alt. base) | — | +0.173 | −0.027 | — |
| `L3-gap-slope-fromopen-FD-WB6` (V2) | WB4 + no entries before 11:00 while SPY > +0.15% above 09:50 | +0.171 (meets) | −0.030 (meets) | PASS on "meets" only — lifts up days in both tests, paid for by down/quiet days; not an overall improvement over WB4; not recommended |

Pass rule (RULES.md, owner 2026-11-16): meets or exceeds the base's avg R after costs in BOTH tests (meets = within 0.01R or
≥ 95%), not worse on avg R w/o best day by > 0.02R or on worst day by > 10%. Base's live record not used.

## Recommended copy: WB5 — parent vs copy, R per day type (day type = SPY 09:50 close → 16:00, ±0.25%)
| test | config | trades | avg R | w/o best day | worst day | R / session | up days avg R (n / total R) | down days | quiet days |
|---|---|---|---|---|---|---|---|---|---|
| Session replay | parent | 350 | +0.059 | −0.003 | −9.7 | +0.89 | −0.150 (100 / −15.0R) | −0.008 (71 / −0.6R) | +0.202 (179 / +36.1R) |
| Session replay | **WB5** | 321 | **+0.087** | **+0.028** | **−8.9** | **+1.22** | **−0.005 (73 / −0.3R)** | −0.033 (73 / −2.4R) | +0.175 (175 / +30.7R) |
| 2-year backtest | parent | 4,885 | −0.048 | −0.056 | −28.8 | −0.56 | −0.147 (2,051 / −300.8R) | +0.149 (1,369 / +204.1R) | −0.093 (1,465 / −135.8R) |
| 2-year backtest | **WB5** | 4,467 | **−0.014** | **−0.023** | **−22.7** | **−0.15** | **−0.102 (1,620 / −165.3R)** | +0.146 (1,481 / +216.3R) | −0.084 (1,366 / −114.7R) |
- **Trades kept:** 321 / 350 (92%) replay; 4,467 / 4,885 (91%) 2-year.
- **Down-day cost:** replay −0.008 → −0.033 R/trade (−1.8R over 6 down sessions); 2-year +0.149 → +0.146 R/trade, total
  +204 → +216R (freed book slots add trades). Up-day gain: +14.7R replay, +135.5R 2-year. Quiet days give back 5.4R in replay,
  gain 21R in 2-year.
- 2-year splits (avg R): TRAIN −0.060 → −0.011, VALID −0.058 → −0.036, FWD +0.112 → +0.156 — better in all three.
- Shape: win % 53.4 → 53.3 (replay) / 49.2 → 48.9 (2y); avg loss −0.90 → −0.81 / −0.96 → −0.85; avg win +0.90 → +0.87 /
  +0.89 → +0.86; median hold 83 → 78 / 46 → 36 min. The SPY exit fires on 13% (replay) / 19% (2-year) of trades, averaging
  −0.28 / −0.23R — losses cut short of the −1R stop. Replay best-day share 104% → 72%.
- Paired-by-day t vs parent: +0.91 (replay), +2.77 (2-year). Configs counted 42 → bar max(1.5, sqrt(2 ln 42)) = 2.73: the
  2-year clears it, the replay does not (23 sessions). Lineage incl. the first run / RERUN / L3LEASH (85 + 42 = 127): bar 3.11,
  not cleared. Passes on meet-or-exceed.

## Alternative base WB4: WB4 vs WB6 (V2), R per day type
| test | config | trades | avg R | w/o best day | worst day | up days | down days | quiet days |
|---|---|---|---|---|---|---|---|---|
| Session replay | WB4 | 236 | +0.173 | +0.134 | −7.3 | +0.152 (74 / +11.2R) | −0.126 (48 / −6.0R) | +0.313 (114 / +35.7R) |
| Session replay | WB6 | 262 | +0.171 | +0.136 | −7.3 | +0.169 (104 / +17.6R) | −0.126 (48 / −6.0R) | +0.302 (110 / +33.3R) |
| 2-year backtest | WB4 | 3,495 | −0.027 | −0.034 | −22.2 | −0.103 (1,468 / −150.9R) | +0.079 (918 / +72.5R) | −0.015 (1,109 / −16.3R) |
| 2-year backtest | WB6 | 3,493 | −0.030 | −0.036 | −22.9 | −0.093 (1,451 / −135.1R) | +0.066 (883 / +58.7R) | −0.024 (1,159 / −27.4R) |
WB6 splits: TRAIN −0.048 → −0.023, VALID −0.036 → −0.057, FWD +0.148 → +0.088 (mixed). Up days +6.4R / +15.8R, down days 0 /
−13.7R. Verdict: meets, not better; WB4's 75-min hold already removes most of the up-day damage (WB4 replay up days are
positive), and every SPY-exit form on WB4 cuts replay winners (W1-W3, Z5-Z6). No up-day copy of WB4 is recommended.

WB5 vs WB4 (for the owner): WB4 stays stronger in the Session replay (+0.173 vs +0.087), WB5 is better in the 2-year backtest
(−0.014 vs −0.027) and keeps the parent's down-day edge (2-year down +0.146 vs WB4 +0.079). They fix different things (WB4:
slow drifts and late entries; WB5: market lifting the stock after entry). Combining them was tried (W4 = WB4 + both WB5 parts):
replay +0.167 / w/o best day +0.111 (−0.023 vs WB4: fails the guard), 2-year −0.025 — not kept.

## Honest caveats
- Still below zero over 2 years after costs (−0.014R); WB5 is a better car than the parent, not yet a proven profitable one.
- Replay has only 8 up sessions; the up-day gain there (−15.0R → −0.3R) rests on few days. The 2-year gain is broad (t 2.77).
- The 09:50→16:00 day label is for reporting; every gate/exit uses only SPY data known at that minute (09:50 anchor, entry anchor).
- The replay uses Primary's book (≤ 30 lots, ≤ 3 per symbol, −2R latch) for every config; testing accounts differ.
- **Not deployable today without code:** the runner has no SPY-since-entry exit (see "Runner spec" below). The entry part
  does NOT need new code: SPY % since the 09:50 close can be derived in a lab module from the existing `spy_fo` context column
  ((1 + spy_fo_now/100) / (1 + spy_fo_0950/100) − 1; the open anchor cancels — RW3-WB3's module already does this), so a
  `spy_950` column is optional (convenience/clarity only).
- Rule changes inside the replay window (ledger): LR1/LR3/LR5/LR7 + LR8 cost model (11-12), Primary −2R latch (10-29), Primary
  cap 30 (10-28), moves Testing 1 ↔ Primary (10-20, 10-22, 10-30), TEAM-6 (11-11). The replay applies today's rules to every
  session for every config, so they do not mix into the comparison.

## Runner spec — what WB5 needs (UPDAY 2026-11-17; research spec, not built)
1. **SPY-since-entry exit (required).** New optional per-setup keys `spy_exit_pct: float | null` (default null = off) and
   `spy_exit_only_losing: bool` (default false). Signal → managed lot carries them like `time_stop_min` (mcf/strategies/base.py
   `Signal`, LabStrategy config passthrough; runner `managed` dict keys at runner.py ~423 / ~1453). At entry fill the runner
   stores `spy0` = SPY's last 1-min close at the entry minute. In the managed-lot loop (runner.py ~745, next to the time stop),
   each poll: `move = (spy_last / spy0 − 1) × 100`; for a SHORT lot exit when `move ≥ spy_exit_pct` (for a LONG, mirror:
   `move ≤ −spy_exit_pct`), and, if `spy_exit_only_losing`, only while the lot is under water. Exit = market close of that lot via
   the time-stop path (`_lot_time_stop` / `close_mcf_position`), logged `SPY EXIT <sym>: SPY +x.xx% since entry`, exit_reason
   `spy_exit`. SPY bars: add "SPY" to the polled watchlist whenever any enabled setup has `spy_exit_pct` (same mechanism as
   `context_symbols`); stale/missing SPY → no exit (fail safe). Costs: LR8 market exit (max($0.01, 1 bp)).
2. **Backtest parity.** `mcf/backtest/engine.py` exit walk gets the same rule on SPY 1-min closes (bar t−1 close vs entry-minute
   close, exit at bar t open), so Session replay / 2-year replay match the bench (`code/sim3.py walk`).
3. **Entry part (no new code).** Module mask on `context: [spy_fo]`: skip when SPY since 09:50 > +0.15% and the bar is after 12:00.
4. Tests: managed-loop unit test (short exits at +0.30%, not at +0.29%; long mirror; only-losing flag; missing SPY → hold);
   engine parity test on a synthetic SPY path. Config then: `spy_exit_pct: 0.30` on the copy.
Used by: L3 WB5 (`spy_exit_pct: 0.30`, this file), RW3 WB4 (`0.30`, `../RW3-gapdn-rsi5pop-flowsell-short-FD/`), RW5 WB4 (`0.40`, `../RW5-heat30-flowsell-rsi5pop-gapdn-short-FD/`).

## Method (identical for parent, WB4 and every copy)
Engine = the RERUN bench (`../../L3-gap-slope-fromopen-FD/code/sim2.py`, reused) plus up-state layers (`code/sim3.py`, all off
by default; it reproduces the parent 350 / +0.059, 4,885 / −0.048 and WB4 236 / +0.173, 3,495 / −0.027 exactly). Session
replay 10-12..11-12 (384 ETB live-signal symbol-days, 23 sessions); 2-year backtest 2024-10..2026-11-04, locked block
2024-11-01..2025-02-28 never read (asserted), E90 borrow proxy, LR8 costs, 5-min signal-bar close entry, 1-min exit walk.
SPY 1-min: RERUN cache to 11-13 + read-only SIP GET 11-13..11-16. Up state U at the signal bar: U15 = SPY > +0.15% above its
09:50 close (other U definitions named per config). Size-down configs are R-weighted (avg R = Σ wR / Σ w).

## Every configuration (42; base in column 3; ROUND1-4 pre-declared in `code/decl3.py`, each round before its scores)
| # | config | base | replay n / avg R / w/o best / worst day | replay up / down / quiet | 2y n / avg R / w/o best / worst day | 2y up / down / quiet | verdict vs base |
|---|---|---|---|---|---|---|---|
| G1 | skip SPY>+0.25% since 09:50 | PARENT | 260 / -0.049 / -0.090 / -9.7 | -0.645 / -0.008 / +0.077 | 3450 / -0.049 / -0.061 / -28.8 | -0.204 / +0.145 / -0.131 | FAIL: replay avg R -0.049 < +0.059; replay w/o best day -0.090 vs -0.003 |
| G2 | skip SPY>+0.40% since 09:50 | PARENT | 338 / +0.052 / -0.013 / -9.7 | -0.178 / -0.008 / +0.193 | 4043 / -0.048 / -0.058 / -28.8 | -0.177 / +0.147 / -0.118 | PASS |
| G3 | skip SPY last-30m>+0.20% | PARENT | 403 / +0.097 / +0.030 / -9.7 | +0.097 / -0.048 / +0.156 | 4939 / -0.051 / -0.061 / -28.6 | -0.164 / +0.137 / -0.070 | PASS |
| G4 | skip SPY>+0.15% & rising 30m | PARENT | 393 / +0.019 / -0.029 / -27.9 | -0.058 / -0.008 / +0.114 | 4272 / -0.055 / -0.065 / -28.8 | -0.195 / +0.156 / -0.085 | FAIL: replay avg R +0.019 < +0.059; replay w/o best day -0.029 vs -0.003; replay worst day -27.9 vs -9.7 |
| S1 | half size SPY>+0.25% | PARENT | 360 / -0.006 / -0.051 / -9.7 | -0.274 / -0.008 / +0.117 | 5345 / -0.048 / -0.058 / -28.8 | -0.151 / +0.130 / -0.101 | FAIL: replay avg R -0.006 < +0.059; replay w/o best day -0.051 vs -0.003 |
| S2 | half size SPY last-30m>+0.20% | PARENT | 400 / +0.042 / -0.013 / -9.8 | -0.078 / -0.031 / +0.172 | 5320 / -0.045 / -0.055 / -23.0 | -0.133 / +0.144 / -0.092 | FAIL: replay avg R +0.042 < +0.059 |
| X1 | U15: max hold 60 | PARENT | 405 / +0.007 / -0.031 / -8.9 | -0.125 / -0.008 / +0.112 | 5277 / -0.039 / -0.046 / -28.8 | -0.098 / +0.112 / -0.086 | FAIL: replay avg R +0.007 < +0.059; replay w/o best day -0.031 vs -0.003 |
| X2 | U15: target 0.75R | PARENT | 375 / +0.040 / -0.001 / -9.7 | -0.079 / -0.008 / +0.139 | 5239 / -0.041 / -0.048 / -28.8 | -0.128 / +0.138 / -0.074 | FAIL: replay avg R +0.040 < +0.059 |
| X3 | U15: stop 0.8R | PARENT | 351 / +0.035 / -0.020 / -9.2 | -0.193 / -0.008 / +0.176 | 4878 / -0.055 / -0.063 / -28.8 | -0.129 / +0.115 / -0.096 | FAIL: replay avg R +0.035 < +0.059 |
| X4 | U15: half off at +0.5R | PARENT | 351 / +0.027 / -0.016 / -9.5 | -0.141 / -0.008 / +0.137 | 4987 / -0.041 / -0.048 / -28.8 | -0.116 / +0.127 / -0.086 | FAIL: replay avg R +0.027 < +0.059 |
| Y1 | exit if SPY +0.30% since entry | PARENT | 364 / +0.068 / +0.010 / -8.9 | -0.059 / -0.033 / +0.184 | 5153 / -0.017 / -0.024 / -22.7 | -0.088 / +0.147 / -0.077 | PASS |
| Y2 | exit if SPY +0.50% since entry | PARENT | 351 / +0.062 / +0.001 / -8.9 | -0.137 / -0.008 / +0.201 | 4933 / -0.031 / -0.039 / -22.5 | -0.115 / +0.149 / -0.081 | PASS |
| Y3 | exit if SPY +0.20% since entry | PARENT | 374 / +0.063 / +0.004 / -7.9 | -0.071 / -0.061 / +0.199 | 5335 / -0.022 / -0.028 / -21.3 | -0.072 / +0.118 / -0.089 | PASS |
| Q1 | U15: gap <= -5% | PARENT | 295 / -0.047 / -0.083 / -9.9 | -0.247 / -0.008 / +0.053 | 3908 / -0.049 / -0.060 / -28.8 | -0.181 / +0.155 / -0.116 | FAIL: replay avg R -0.047 < +0.059; replay w/o best day -0.083 vs -0.003 |
| Q2 | U15: fromOpen > 5 | PARENT | 314 / +0.012 / -0.035 / -9.7 | -0.048 / -0.008 / +0.062 | 4255 / -0.035 / -0.045 / -28.8 | -0.130 / +0.140 / -0.097 | FAIL: replay avg R +0.012 < +0.059; replay w/o best day -0.035 vs -0.003 |
| Q3 | U15: RS since 09:50 < 4% | PARENT | 349 / +0.043 / +0.015 / -8.9 | -0.039 / -0.008 / +0.131 | 4494 / -0.053 / -0.062 / -28.8 | -0.189 / +0.145 / -0.078 | FAIL: replay avg R +0.043 < +0.059 |
| T1 | U15: entries end 12:00 | PARENT | 313 / +0.087 / +0.026 / -9.7 | -0.095 / -0.008 / +0.200 | 4207 / -0.045 / -0.055 / -28.8 | -0.171 / +0.148 / -0.097 | PASS |
| T2 | SPY rising 30m>+0.10%: no entries before 10:30 | PARENT | 395 / +0.068 / +0.018 / -9.7 | +0.014 / -0.008 / +0.152 | 5142 / -0.050 / -0.059 / -28.8 | -0.148 / +0.145 / -0.075 | PASS |
| R2a | exit if SPY +0.40% since entry | PARENT | 350 / +0.068 / +0.007 / -8.9 | -0.101 / -0.006 / +0.189 | 4947 / -0.023 / -0.031 / -22.5 | -0.102 / +0.150 / -0.075 | PASS |
| R2b | exit if SPY +0.25% since entry | PARENT | 372 / +0.064 / +0.006 / -8.4 | -0.095 / -0.012 / +0.191 | 5232 / -0.017 / -0.024 / -20.7 | -0.075 / +0.135 / -0.086 | PASS |
| R2c | U15 trades only: exit if SPY +0.30% | PARENT | 356 / +0.066 / +0.007 / -9.7 | -0.088 / -0.008 / +0.187 | 4905 / -0.035 / -0.043 / -28.8 | -0.115 / +0.149 / -0.095 | PASS |
| R2d | Y1 + U15 entries end 12:00 | PARENT | 321 / +0.087 / +0.028 / -8.9 | -0.005 / -0.033 / +0.175 | 4467 / -0.014 / -0.023 / -22.7 | -0.102 / +0.146 / -0.084 | PASS |
| R2e | Y1 + SPY rising 30m>+0.10%: none before 10:30 | PARENT | 407 / +0.081 / +0.035 / -8.9 | +0.077 / -0.033 / +0.133 | 5354 / -0.019 / -0.027 / -22.2 | -0.093 / +0.152 / -0.063 | PASS |
| R2f | Y1 + skip SPY last-30m>+0.20% | PARENT | 415 / +0.113 / +0.051 / -8.9 | +0.147 / -0.072 / +0.153 | 5169 / -0.025 / -0.034 / -29.3 | -0.102 / +0.129 / -0.064 | PASS |
| W1 | WB4 + exit if SPY +0.30% since entry | WB4 | 241 / +0.151 / +0.108 / -7.3 | +0.091 / -0.120 / +0.303 | 3609 / -0.024 / -0.031 / -20.1 | -0.087 / +0.088 / -0.035 | FAIL: replay avg R +0.151 < +0.173; replay w/o best day +0.108 vs +0.134 |
| W2 | WB4 + exit if SPY +0.20% since entry | WB4 | 251 / +0.134 / +0.089 / -7.7 | +0.050 / -0.109 / +0.304 | 3672 / -0.029 / -0.033 / -18.8 | -0.084 / +0.075 / -0.040 | FAIL: replay avg R +0.134 < +0.173; replay w/o best day +0.089 vs +0.134 |
| W3 | WB4 + exit if SPY +0.40% since entry | WB4 | 238 / +0.162 / +0.121 / -7.3 | +0.131 / -0.126 / +0.301 | 3560 / -0.025 / -0.032 / -23.4 | -0.095 / +0.096 / -0.032 | FAIL: replay avg R +0.162 < +0.173 |
| W4 | WB4 + Y1 + U15 entries end 12:00 | WB4 | 215 / +0.167 / +0.111 / -7.3 | +0.135 / -0.120 / +0.306 | 3229 / -0.025 / -0.032 / -20.1 | -0.103 / +0.087 / -0.034 | FAIL: replay w/o best day +0.111 vs +0.134 |
| W5 | WB4 + skip SPY last-30m>+0.20% | WB4 | 315 / +0.101 / +0.062 / -19.1 | +0.029 / -0.121 / +0.310 | 3404 / -0.047 / -0.054 / -29.8 | -0.144 / +0.067 / -0.014 | FAIL: replay avg R +0.101 < +0.173; replay w/o best day +0.062 vs +0.134; replay worst day -19.1 vs -7.3; 2y avg R -0.047 < -0.027; 2y w/o best day -0.054 vs -0.034; 2y worst day -29.8 vs -22.2 |
| W6 | WB4 + SPY rising 30m>+0.10%: none before 10:30 | WB4 | 259 / +0.153 / +0.114 / -7.3 | +0.146 / -0.126 / +0.287 | 3512 / -0.029 / -0.036 / -30.3 | -0.095 / +0.080 / -0.024 | FAIL: replay avg R +0.153 < +0.173; 2y worst day -30.3 vs -22.2 |
| Z1 | exit if SPY +0.30% & short under water | PARENT | 363 / +0.065 / +0.007 / -8.9 | -0.072 / -0.027 / +0.184 | 5088 / -0.019 / -0.027 / -22.8 | -0.080 / +0.145 / -0.090 | PASS |
| Z2 | exit if SPY +0.20% & short under water | PARENT | 357 / +0.036 / -0.029 / -7.7 | -0.091 / -0.194 / +0.192 | 5060 / -0.020 / -0.028 / -21.3 | -0.068 / +0.124 / -0.107 | FAIL: replay avg R +0.036 < +0.059; replay w/o best day -0.029 vs -0.003 |
| Z3 | R2d with SPY exit at +0.40% | PARENT | 313 / +0.094 / +0.034 / -8.9 | -0.021 / -0.006 / +0.181 | 4267 / -0.022 / -0.031 / -22.5 | -0.122 / +0.150 / -0.081 | PASS |
| Z4 | Y1 + U15 entries end 11:30 | PARENT | 280 / +0.021 / -0.037 / -8.9 | -0.002 / -0.033 / +0.055 | 3998 / -0.004 / -0.012 / -22.7 | -0.099 / +0.137 / -0.066 | FAIL: replay avg R +0.021 < +0.059; replay w/o best day -0.037 vs -0.003 |
| Z5 | WB4 + exit if SPY +0.30% & under water | WB4 | 241 / +0.151 / +0.108 / -7.3 | +0.091 / -0.129 / +0.307 | 3576 / -0.025 / -0.031 / -22.3 | -0.088 / +0.083 / -0.031 | FAIL: replay avg R +0.151 < +0.173; replay w/o best day +0.108 vs +0.134 |
| Z6 | WB4 + exit if SPY +0.20% & under water | WB4 | 241 / +0.154 / +0.111 / -7.3 | +0.048 / -0.057 / +0.305 | 3629 / -0.029 / -0.034 / -18.6 | -0.085 / +0.079 / -0.045 | FAIL: replay avg R +0.154 < +0.173; replay w/o best day +0.111 vs +0.134 |
| Z7 | WB4 + exit if SPY +0.40% & under water | WB4 | 238 / +0.165 / +0.124 / -7.3 | +0.142 / -0.131 / +0.301 | 3541 / -0.025 / -0.031 / -23.4 | -0.093 / +0.093 / -0.030 | PASS |
| Z8 | R2d with under-water SPY exit | PARENT | 320 / +0.085 / +0.025 / -8.9 | -0.024 / -0.027 / +0.176 | 4407 / -0.017 / -0.025 / -22.8 | -0.100 / +0.144 / -0.088 | PASS |
| V1 | WB4 + U15: max hold 45 | WB4 | 250 / +0.140 / +0.097 / -7.3 | +0.106 / -0.126 / +0.271 | 3652 / -0.036 / -0.042 / -21.3 | -0.095 / +0.064 / -0.034 | FAIL: replay avg R +0.140 < +0.173; replay w/o best day +0.097 vs +0.134 |
| V2 | WB4 + U15: no entries before 11:00 | WB4 | 262 / +0.171 / +0.136 / -7.3 | +0.169 / -0.126 / +0.302 | 3493 / -0.030 / -0.036 / -22.9 | -0.093 / +0.067 / -0.024 | PASS |
| V3 | WB4 + U15: RS since 09:50 < 4% | WB4 | 260 / +0.059 / +0.002 / -17.6 | -0.053 / -0.126 / +0.281 | 3234 / -0.022 / -0.029 / -22.2 | -0.111 / +0.074 / -0.000 | FAIL: replay avg R +0.059 < +0.173; replay w/o best day +0.002 vs +0.134; replay worst day -17.6 vs -7.3 |
| V4 | WB4 + U15: target 0.75R | WB4 | 242 / +0.155 / +0.113 / -7.3 | +0.114 / -0.126 / +0.297 | 3674 / -0.031 / -0.037 / -22.2 | -0.103 / +0.076 / -0.017 | FAIL: replay avg R +0.155 < +0.173; replay w/o best day +0.113 vs +0.134 |

Passed but not chosen: G2 (no up-day gain), G3/T1/T2 (up days better in replay only; 2-year up days worse or flat), Y1-Y3,
R2a-R2c, Z1 (SPY exit alone: smaller replay gain than R2d), R2e (2-year −0.019 and up −0.093, but quiet days −0.133 replay),
R2f (best replay +0.113 but down days −0.072 replay / +0.129 2-year and 2-year worst day −29.3R: gives back the most down-day R),
Z3 (SPY exit at +0.40%: keeps down days exactly, smaller 2-year gain −0.022 / up −0.122), Z8 (under-water only: slightly behind
R2d), Z7 (meets WB4, replay up days lower). Failures: every skip gate on the market being up since 09:50 (G1, G4), size-down
(S1, S2), U-only exit tweaks (X1-X4), stricter U entry quality (Q1-Q3), U entries end 11:30 (Z4), and on WB4: W1-W6, Z5, Z6,
V1, V3, V4.

## Files
`code/` (sim3.py, load3.py, decl3.py, go3.py, diag.py, png.py, stepa.py, lt.py, spyday.py; run from a scratch dir holding the
RERUN inputs: replay_frames / replay_1min / cand2yx / paths2y / etb_rate + spy1m_all.parquet), `res_ROUND1-4.csv`,
`variants.jsonl` (42 rows), `diag_buckets.txt`, `L3-upday_daytype.png` (R per day type, both tests), `L3-upday_curves.png`.
