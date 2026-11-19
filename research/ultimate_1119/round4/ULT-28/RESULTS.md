Educational only — not financial advice

# ULT-28 EARN-GO — earnings reaction-day continuation with the gap (round 4) — **FAIL**

Research only: no setup, exit, config or account change. Nothing committed. **PARTLY CHECK-INFORMED** (PLAN sec. 0.6).
Any deployment would also **need an owner exception to the 4-day earnings blackout** (sec. 0.8). That question does not
come up: the candidate fails.

## Verdict
- **Fit pick 28a (G 3%, HOLD, surprise agrees, t1s1 cap45)** = fit **-0.022R** (n 358, 2.11/session, t -0.54).
  The pick can never reach TIER A, because the fit avg R is <= 0.
- **CHECK, scored once:** **-0.048R**. 696 trades, 2.52/session, w/o best day -0.064, total -33.7R
  (-0.122R/session), t -1.24.
- **Tier: FAIL.** TIER B would need fit > 0. All 5 grid configs eligible on fit (>= 2/session) are negative on fit,
  and all 12 configs are negative or ~0 on check.
- **The archive's EARN-GO figure (+0.346R) does not reproduce** on this chassis, with intraday entries from 09:50.
  The chassis is next-minute-open fills, LR8 costs, a x1.5 news-day surcharge before 10:30 and earnings-window
  borrow. The bias diagnostic strips those fixes, and even then the check pick is still -0.036.
- **The HOLD trigger does worse than random bars on the same names** in both halves: signal minus random is
  -0.113 (fit) and -0.092 (check). Random with-gap bars on these reaction-day names earn +0.091 (fit) and +0.044
  (check). That is a diagnostic only (see "Leads").

## Configurations tried
- This candidate: 12 grid + 1 bias diagnostic = **13** (as PLAN sec. 4).
- Cumulative N for the job = **996**, so the t bar is 3.716.
- The random-entry control and the non-earnings twin are reported but not counted.

## What was built
- **Module:** `research/ultimate_1119/modules/ULT-28.py`. It is live-ready with the same interface as round 1-3
  (LabStrategy `type: lab`, two entries in one file, "-S" = short, `context: [spy_fo]`).
  - The event source live is the allow-list `SYMBOLS` (YAML `symbols: module`): today's reaction-day names for that
    side, with the surprise sign applied under S "agree".
  - The list is built at import from a calendar parquet (`MCF_EARN_CAL`; earnings_yf columns) by the same
    `reaction_days()` function the backtest uses.
  - A missing calendar gives an empty list, so no trades (fail safe).
  - The NYSE session calendar is hardcoded (weekdays minus holidays). It matches all 446 frame sessions exactly, and
    it needs no market data, so look-ups never touch the locked block.
- **Smoke test:** `round4/ULT-28/test_module.py`, 3 tests, all pass. It covers:
  - calendar mapping: bmo gives the report day; amc gives the next session; a Friday amc gives Monday; dmh is
    excluded;
  - S filter and the fail-safe;
  - long and short under the live LabStrategy;
  - no signal on a faded gap, a small gap or a non-event name;
  - point-in-time truncation;
  - e_rd / e_surp gating, with a missing surprise excluded under "agree".
- **Backtest:** `round4/ULT-28/bt.py`, adapted from round3/ULT-26 (1-minute walk unchanged; stats from ULT-23).
  - Costs: LR8, plus x1.5 entry cost (entry bar < 10:30) and x1.5 exit cost (exit < 10:30) on reaction days.
  - Short borrow: 5 bp of notional on reaction days (8 bp < $20); twin shorts pay 1.2 / 3 bp. Shorts are ETB only.
  - Chassis as round 3: one lot per symbol, refire >= 30 min after the exit, max 2 per symbol-session, day cap 30,
    flat 15:50.
  - Event table: no shared `round4/earn.py` existed when this ran. The sec. 2 spec is implemented inside the module
    (`reaction_days`), so live and backtest use one code path.
  - Event volume (point-in-time counts only): reaction-day names per session are ~21 in season and ~3 off season.
    With ADV >= $30M and |gap| >= 3%, it is ~10 in season.
- **Locked block:** never read. The earnings file holds no rows dated 2024-11-01..2025-02-28. Events with RD in the
  block are dropped. pyarrow filters and `no_locked` asserts run on every frame, event and 1-minute load. Forbidden
  columns are dropped and asserted absent.
  - Side effect: amc reports dated 2025-02-27/28 are missing, so a few 2025-03-03 events are lost (conservative).
- **Order:** fitsel.json was frozen at 2026-11-19T08:52Z (sha256 of bt.py, the module and the earnings file) before
  any check frame, event row or trade was built. Check was scored once at 08:54Z, and the plateau ran after it.

## FIT grid (170 sessions; selection = max fit total R minus best day among configs >= 2.0/session)
| cfg | rule | /session | avg R | w/o best day | total R | t | A / B | long / short |
|---|---|---|---|---|---|---|---|---|
| **28a** | G3 HOLD agree t1s1 | 2.11 | -0.022 | -0.034 | -8.0 | -0.54 | +0.061 / -0.190 | +0.020 / -0.128 |
| 28b | G3 HOLD any t1s1 | 3.45 | -0.045 | -0.058 | -26.6 | -1.32 | +0.024 / -0.172 | +0.018 / -0.108 |
| 28c | G3 PUSH agree t1s1 | 0.19 | +0.039 | -0.028 | +1.3 | 0.25 | +0.026 / +0.088 | +0.110 / -0.215 |
| 28d | G3 PUSH any t1s1 | 0.29 | -0.019 | -0.086 | -1.0 | -0.15 | +0.095 / -0.313 | -0.010 / -0.038 |
| 28e | G5 HOLD agree t1s1 | 1.46 | +0.007 | -0.013 | +1.7 | 0.13 | +0.111 / -0.180 | +0.041 / -0.074 |
| 28f | G5 HOLD any t1s1 | 2.39 | -0.027 | -0.044 | -10.8 | -0.65 | +0.046 / -0.147 | +0.034 / -0.081 |
| 28g | G5 PUSH agree t1s1 | 0.14 | +0.078 | +0.024 | +1.8 | 0.43 | +0.051 / +0.177 | +0.127 / -0.096 |
| 28h | G5 PUSH any t1s1 | 0.20 | +0.019 | -0.021 | +0.6 | 0.12 | +0.118 / -0.220 | +0.036 / -0.013 |
| 28i | G3 HOLD any TX-45 | 3.32 | -0.030 | -0.043 | -17.2 | -0.91 | +0.018 / -0.119 | +0.034 / -0.093 |
| 28j | G3 PUSH any TX-45 | 0.29 | -0.099 | -0.153 | -5.0 | -1.00 | -0.095 / -0.109 | -0.077 / -0.143 |
| 28k | G5 HOLD any TX-45 | 2.31 | -0.052 | -0.062 | -20.2 | -1.29 | +0.028 / -0.182 | -0.012 / -0.087 |
| 28l | G5 PUSH any TX-45 | 0.20 | -0.070 | -0.148 | -2.4 | -0.53 | -0.063 / -0.087 | -0.083 / -0.046 |

- Eligible configs: 28a, 28b, 28f, 28i, 28k, and all five are negative.
- Expected volume was G3 ~3-6 and G5 ~2-4/session. Volume came in as planned: HOLD trades 2.1-3.5/session.
- PUSH is 5-10x thinner than planned (0.1-0.3/session). Its few positive fit cells (28c, 28g) are ~20-30 trades
  with t < 0.5.
- No fit trades fall in 2025-04-03..04-09 (off season), so the "without 04-03..04-09" figure equals the full
  figure (-0.0224).

## Fit pick 28a: FIT vs CHECK
| | FIT | CHECK (once) |
|---|---|---|
| trades (/session) | 358 (2.11) | 696 (2.52) |
| sessions traded | 64 of 170 | 117 of 276 |
| win | 0.508 | 0.500 |
| avg R (= per 0.25-dATR unit, t1s1) | **-0.0224** | **-0.0484** |
| avg R w/o best day | -0.0338 | -0.0637 |
| best day (share) | 2025-03-14 +3.9R (n/a, total < 0) | 2026-07-29 +9.7R (n/a, total < 0) |
| total R (R/session) | -8.0 (-0.047) | -33.7 (-0.122) |
| worst day (/ trade-session) | -3.84 (-0.69) | -10.82 (-1.82) |
| day-clustered t | -0.54 | -1.24 (bar 3.716) |
| w/o 2025-04-03..04-09 | -0.0224 | n/a (no such dates) |
| sub-halves A / B | +0.061 / -0.190 | — |
| first / second half | +0.040 / -0.121 | -0.088 / -0.012 |
| long / short | +0.020 (n 256) / -0.128 (n 102) | -0.075 (n 523) / +0.033 (n 173) |
| SPY up / flat / down | -0.032 / +0.087 / -0.093 | +0.001 / -0.096 / -0.034 |
| entry 09:50-10:25 / 10:30-11:25 / 11:30-12:30 | -0.021 / -0.013 / -0.051 | -0.097 / +0.014 / -0.096 |
| gap 3-5 / 5-10 / 10+ % | -0.088 / +0.025 / -0.027 | +0.019 / -0.104 / -0.041 |
| season / off-season sessions (>= 5 RD names) | -0.001 (n 347) / -0.70 (n 11) | -0.048 (n 666) / -0.053 (n 30) |
| median hold; exit mix | 13 min; target 147 / stop 133 / time 78 | 11 min; target 289 / stop 294 / time 113 |
| bias diagnostic (signal-close fill, no borrow, no surcharge) | -0.003 | -0.036 |
| same-name random control (avg R; signal minus random) | +0.091; **-0.113** | +0.044; **-0.092** |
| random long / short | +0.060 / +0.168 | +0.063 / -0.015 |
| non-earnings twin (same rule, no report in RD-5..RD+1) | -0.027 (9.8/session) | -0.024 (18.4/session) |

- **Bars:**
  - check avg R > 0: no.
  - w/o best day > 0: no.
  - fit avg R > 0: no.
  - >= 2/session: yes.
  - BEATS: no on every count (avg R, w/o best day and t all fall short; worst day / trade-session -1.82 would pass).
- **Earnings vs no-news:** the reaction-day rule (-0.048) is no better than its non-earnings twin (-0.024).
  News does not rescue the with-gap HOLD entry on this chassis.
- **Sign flips:** the side sign flips between halves (long +0.02 then -0.075; short -0.128 then +0.033). That is the
  same instability round 1-3 rankers showed.

## CHECK plateau (diagnostic only, run after the single check score; never used to re-select)
| cfg | /session | avg R | w/o best day | t | long / short |
|---|---|---|---|---|---|
| 28a (pick) | 2.52 | -0.048 | -0.064 | -1.24 | -0.075 / +0.033 |
| 28b | 4.71 | -0.054 | -0.063 | -1.78 | -0.052 / -0.057 |
| 28c | 0.30 | -0.172 | -0.215 | -1.63 | -0.199 / -0.087 |
| 28d | 0.59 | -0.076 | -0.101 | -1.09 | -0.142 / -0.002 |
| 28e | 1.69 | -0.082 | -0.093 | -1.76 | -0.103 / -0.017 |
| 28f | 3.19 | -0.074 | -0.083 | -2.03 | -0.063 / -0.084 |
| 28g | 0.19 | -0.068 | -0.110 | -0.53 | -0.070 / -0.062 |
| 28h | 0.37 | +0.025 | -0.002 | 0.31 | +0.083 / -0.031 |
| 28i | 4.57 | -0.045 | -0.053 | -2.01 | -0.028 / -0.060 |
| 28j | 0.57 | -0.021 | -0.048 | -0.34 | -0.003 / -0.042 |
| 28k | 3.08 | -0.032 | -0.041 | -1.22 | -0.021 / -0.041 |
| 28l | 0.36 | +0.068 | +0.031 | 0.94 | +0.175 / -0.042 |

There is no plateau: 10 of 12 configs are negative. The two positive cells are 0.4/session with t < 1.

## Why it fails (mechanism read)
- **The HOLD trigger fires at the first bar >= 09:50 where the gap is holding.** On reaction days that is mostly the
  09:50-10:25 block, which loses (check -0.097). It is also the block with the widest spreads (x1.5 surcharge).
  The earliest "holding" read is the most crowded and the most likely to be the high or low of the morning.
- **Random bars later in the window, on the same names and side, do better** (+0.04..+0.09). So the information
  drift may exist, but buying the first confirmation at the open-hour extreme gives it back.
- **The surprise sign adds nothing stable.** Fit: agree -0.022 vs any -0.045. Check: -0.048 vs -0.054.

## Leads (optimistic next steps; each would need its own pre-registration and count; CHECK is now read for this idea)
1. **A later, random-like entry time on reaction-day names, with the gap.** The random control is positive in both
   halves (+0.091 fit, +0.044 check). But it is conditioned on sessions where HOLD fired, and its own t is unknown.
   A pre-registered "with-gap at 10:30-12:30, not at a fresh extreme" rule is the natural test. The best fit block,
   10:30-11:25, is also the only positive check block (+0.014).
2. **Reaction-day shorts on fit are -0.128 and random shorts are +0.168.** That points the same way as lead 1:
   entering shorts at the first VWAP-side bar is the problem, not the side.

## Files
- `research/ultimate_1119/modules/ULT-28.py`: module with the frozen pick 28a; CHECK FAIL in the header.
- `research/ultimate_1119/round4/ULT-28/`: bt.py, test_module.py, fit_grid.json, fitsel.json, fit_random.json
  (random control, uncapped stats, fit twin), check_once.json, check_plateau.json (incl. check twin),
  check_trades.csv.gz.
- Trade lists and walked parquet files were in the scratchpad and have been deleted.

## Rule-change context
- Both halves are scored under one fixed rule set: today's LR8 costs, the round-3/4 chassis, and the round-4
  surcharge and borrow fixes. No live rule change falls inside them.
- The live 4-day earnings blackout (owner 2026-10-07) was in force through the whole live record, so no live setup
  trades reaction days and there is no live comparison.

## Known biases (all favour the candidate)
- Today's symbol list (survivorship) flatters longs.
- The ETB flag is today's.
- The earnings table was fetched after the fact (rare date revisions are not modelled).
- The yfinance report hour is assumed to be correct.

Educational only — not financial advice.
