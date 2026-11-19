Educational only — not financial advice

# ULT-34 NO-NEWS REVERSAL — day-2 fade of an extreme prior-day move with no earnings (round 4) — **FAIL**

Research only: no setup, exit, config or account change. Nothing committed. **NOT check-informed** (PLAN sec. 0.6).
Respects the 4-day earnings blackout by construction (no report reacting in d-5..d+1), so no owner exception is needed.

## Verdict
- **Fit pick 34d (K 2.0, F = VO, TX-45)**: fit **-0.027R** (n 494, 2.91/session, t -0.49).
  - Only the K 2 configs (34a-34d) reach 2/session on fit, and all four are negative on fit (-0.027..-0.047).
  - So the pick cannot reach TIER A whatever CHECK says (fit avg R must be > 0).
- **CHECK, scored once (2026-11-19T09:35Z):** **-0.061R**.
  - 821 trades, 2.98/session (174 of 276 sessions traded).
  - Without the best day (2026-02-04): -0.066. Best-day share: n/a (total is negative).
  - Total **-50.0R** (-0.181R/session). Worst day -4.53R (-0.96 per trade-session).
  - Day-clustered t **-3.61** (bar 3.716). Win 44%.
  - Long -0.032 (n 335, t -1.11); short **-0.081** (n 486, t -3.77).
  - CHECK holds no 2025-04-03..04-09 dates, so the ex-April figure equals the main one (-0.061).
- **Tier: FAIL.** TIER B needs fit > 0; fit is -0.027.
- **The fade trigger does worse than a random bar on the same names, sessions and sides**, in both halves.
  - Fit: signal minus random **-0.065** (random +0.038, t 1.44).
  - Check: signal minus random **-0.058** (random -0.003, t -0.15).
  - That is the base-loses / trigger-hurts pattern of rounds 1-3 again. Here the trigger itself (VWAP side + not back
    through the open, in the fade direction) is what loses.
- **Plateau (CHECK, all 8 configs, diagnostic only, never used to re-select):** 8 of 8 are negative.
  - The range is -0.044 (34b) to -0.176 (34g). t runs from -1.8 to -3.6.
  - The best fit cell, 34g (K 3, VO, t1s1: fit +0.129, 0.69/session, t 1.85, best day 45% of R), falls to **-0.176**
    on check (n 121, t -2.43). It is a small-sample fit artefact, carried by the April 2025 tariff days.
- **Mechanism read.** A >= 2 daily-ATR close-to-close move with no scheduled news does **not** revert intraday on
  day 2 at 10:00-13:00 on this universe. If anything it keeps going, because the fade loses in both halves and the
  short side (fading up-moves) loses most. Chan's (2003) no-news reversal is a monthly-horizon, small-cap effect.
  It does not carry to a 45-minute intraday hold on liquid names after LR8 costs.

## Configurations tried
- This candidate: 8 grid + 1 bias diagnostic = **9**, as PLAN sec. 4.
- Cumulative N for the job stays **996** (round 4's 115 already includes these 9), so the t bar is **3.716**.
- The random-entry control and the check plateau are reported, not counted.

## What was built
### Module (live-ready)
`research/ultimate_1119/modules/ULT-34.py` uses the round 1-4 interface: LabStrategy `type: lab`, two entries in one
file ("-S" = short), `context: [spy_fo]`, `symbols: module`. GEOM is "S" for TX-45 (2u catastrophic stop through
`stop_price`) or t1s1 for EXIT T. The constants are set to the fit pick (K 2, F VO, EXIT X).
- **Event source live:** the allow-list `SYMBOLS` = today's qualifying names for this side. It is built at import by
  `nonews_events()`, the same function the backtest uses, from two files:
  - the calendar `MCF_EARN_CAL` (symbol, date, session);
  - a daily-bar file `MCF_DAILY_BARS` (symbol, date, high, low, close). Only rows dated strictly before today are read.
  - ATR14 = mcf.features.atr (checked equal to the lab frame's `atr_d`: A 2025-06-02 3.408 = 3.408).
- **No news:** no report whose reaction session (amc -> next session) lies in d-5..d+1.
  - A stock not covered by the calendar is excluded (fail safe). ETFs need no calendar.
  - Leveraged / inverse / volatility funds (ULT-31 LEV list) are excluded from events.
- **Per-name |r1| live:** the live lab frame carries no symbol. So the gap rule (s x gap <= 0.5 x |r1|) looks |r1| up by
  the exact prior-day high / low fingerprint (prev_high = close + dist_pdh_atr x atr_d, prev_low = close -
  dist_pdl_atr x atr_d). No unique match means no signal.
- **Deploy gaps (moot, since FAIL):**
  - the runner persists no daily OHLC file;
  - the fingerprint needs the daily file and the runner's prev_high / prev_low to come from the same bars.

### Smoke test
`round4/ULT-34/test_module.py` holds 4 tests, all passing. They cover:
- **The allow-list:**
  - sides;
  - the earnings window edges d-5 and d+1 (in) vs d-6 and d+2 (out);
  - the uncovered-stock exclusion, the ETF pass and the LEV exclusion;
  - K too high;
  - fail-safe on each missing file.
- **Point-in-time daily:** changing today's bar leaves the list unchanged.
- **Under the live LabStrategy:**
  - long and short both fire inside 10:00-13:00, with stop distance 2u;
  - nothing fires on a non-event name, with no fingerprint match, on a still-falling tape, or on a gap that has
    already retraced more than half;
  - an r1 < 0 name never shorts.
- **Features:**
  - a truncation test;
  - e_ok / e_r1 / e_k gating: K, side, the gap rule, VO subset of V, the short RSI5 floor and the gap-up block.

### Backtest
`round4/ULT-34/bt.py` imports round4/ULT-30/bt.py unchanged (its `walk`, LR8 `cost_R` with borrow, `bind` and the random
control), which in turn imports ULT-28's 1-minute `walk_job` and the ULT-23 stats.
- **Chassis:** next-minute-open fills; one lot per symbol; refire >= 30 min after the exit; max 2 per symbol-session;
  day cap 30 (time, ADV20 desc); flat 15:50.
- **Shorts:** borrow 1.2 bp of notional (3 bp under $20), ETB by today's flag. There is no earnings surcharge, because
  no event is near earnings.
- **Locked block:**
  - r1 needs d-2 and d-1 to be consecutive sessions present in the data, so a look-back into the block is dropped. The
    first March session is 2025-03-05.
  - Event sessions inside the block are dropped. The `no_locked` assertion caught this on the first run, before any
    scoring.
  - Every frame, daily, 1-minute, earnings and trade load is asserted.
- **Event volume** (point-in-time, no outcomes): K2 names/session at 10:00 with ADV >= $50M were 13.1 on fit
  (49.6 in April 2025) and 8.5 on check. K3 names/session were 1.8 on fit and 1.0 on check.
  - K2 name-days dropped for news (the reaction days this candidate avoids): 797 on fit and 1,356 on check.

## Results
### FIT grid (170 sessions, all 8 configs)
| cfg | rule | trades | /sess | avg R | w/o best day | total R | t | ex 04-03..09 | A | B | long | short |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 34a | K2 V t1s1 | 627 | 3.69 | -0.047 | -0.064 | -29.3 | -0.82 | -0.024 | -0.122 | +0.016 | -0.051 | -0.044 |
| 34b | K2 V TX45 | 623 | 3.67 | -0.029 | -0.059 | -18.2 | -0.54 | -0.012 | -0.080 | +0.013 | -0.030 | -0.028 |
| 34c | K2 VO t1s1 | 500 | 2.94 | -0.028 | -0.054 | -13.7 | -0.44 | -0.007 | -0.070 | +0.009 | -0.005 | -0.045 |
| **34d** | **K2 VO TX45 (pick)** | 494 | 2.91 | **-0.027** | -0.054 | -13.5 | -0.49 | -0.003 | -0.075 | +0.013 | -0.025 | -0.029 |
| 34e | K3 V t1s1 | 163 | 0.96 | +0.073 | +0.024 | +12.0 | 0.74 | +0.125 | +0.073 | +0.075 | -0.014 | +0.202 |
| 34f | K3 V TX45 | 161 | 0.95 | +0.008 | -0.015 | +1.3 | 0.13 | +0.063 | -0.013 | +0.046 | -0.032 | +0.065 |
| 34g | K3 VO t1s1 | 118 | 0.69 | +0.129 | +0.083 | +15.2 | 1.85 | +0.186 | +0.149 | +0.093 | +0.015 | +0.250 |
| 34h | K3 VO TX45 | 116 | 0.68 | -0.132 | -0.190 | -15.3 | -0.90 | +0.076 | -0.212 | +0.004 | -0.332 | +0.076 |

Pick rule (PLAN sec. 5): the highest fit total R minus the best fit day, among configs with >= 2/session.
- That gives 34d at -25.06, just ahead of 34c at -25.40. The plain-total-R pick is also 34d.
- fitsel.json was frozen 2026-11-19T09:33:42Z, before any check frame was built.
- The module constants were then set to the pick, and that hash is recorded in fitsel.json too.

Pick 34d on fit, in more detail:
- 2.91/session; win 48%; avg R per 0.25-dATR unit -0.055; median hold 45 min; exits 462 time / 32 stop.
- Worst day -23.6R (2025-04 tariff week; -4.82 per trade-session). The best day is 2025-04-07, and the total is
  negative.
- **Without 2025-04-03..04-09: -0.003** (n 430).
- SPY-day split: up +0.093, flat +0.007, down **-0.238**.
- By size: K 2-3 -0.037 (n 430), K 3-5 +0.005 (54), K >= 5 +0.209 (10).
- Uncapped (no day cap of 30): 1,192 trades, -0.036.

### CHECK (276 sessions, pick 34d scored once)
| metric | value |
|---|---|
| trades / per session | 821 / 2.975 |
| win | 44.2% |
| avg R (per 2u) / per 0.25-dATR unit | **-0.0609** / -0.122 |
| avg R w/o best day (2026-02-04, +3.1R) | -0.0662 |
| best-day share | n/a (total < 0) |
| total R / per session | -49.97 / -0.181 |
| worst day / per trade-session | -4.53 / -0.959 |
| day-clustered t | **-3.61** (bar 3.716) |
| first / second half | -0.047 / -0.076 |
| long / short | -0.032 (t -1.11) / -0.081 (t -3.77) |
| SPY up / flat / down | -0.097 / -0.038 / -0.053 |
| by K: 2-3 / 3-5 / >= 5 | -0.049 (700) / -0.164 (105) / +0.104 (16) |
| by entry time 10:00-10:55 / 11:00-11:55 / 12:00-13:00 | -0.085 / -0.030 / -0.044 |
| exits | 791 time / 30 stop; median hold 45 min |
| random control (same name, session, side, exit) | -0.003 (t -0.15); signal minus random **-0.058** |
| bias diagnostic (signal-close fill, no borrow) | -0.057 (vs -0.061 with the fixes) |

### CHECK plateau (diagnostic only; never used to re-select)
| cfg | /sess | avg R | w/o best day | total R | t | long | short |
|---|---|---|---|---|---|---|---|
| 34a K2 V t1s1 | 4.13 | -0.087 | -0.095 | -99.5 | -3.50 | +0.022 | -0.152 |
| 34b K2 V TX45 | 4.09 | -0.044 | -0.052 | -49.8 | -2.43 | +0.011 | -0.077 |
| 34c K2 VO t1s1 | 3.01 | -0.094 | -0.101 | -77.9 | -3.49 | +0.019 | -0.170 |
| 34d K2 VO TX45 (pick) | 2.98 | -0.061 | -0.066 | -50.0 | -3.61 | -0.032 | -0.081 |
| 34e K3 V t1s1 | 0.59 | -0.121 | -0.153 | -19.9 | -1.77 | +0.111 | -0.220 |
| 34f K3 V TX45 | 0.59 | -0.085 | -0.098 | -14.0 | -2.33 | -0.052 | -0.099 |
| 34g K3 VO t1s1 | 0.44 | -0.176 | -0.208 | -21.3 | -2.43 | -0.010 | -0.249 |
| 34h K3 VO TX45 | 0.44 | -0.128 | -0.139 | -15.5 | -3.50 | -0.168 | -0.111 |

## What can be salvaged (optimism, honestly scoped)
- **The short side is the clear loser in both halves on check**: fading a no-news up-move loses -0.08..-0.25.
- The long side (buying a no-news down-move back above VWAP) is about flat on check under t1s1 (+0.011..+0.022 for K2)
  and slightly negative on fit.
  - That is not an edge after costs. It is, however, the opposite read to "news drifts / no-news reverts" at this
    horizon.
  - Any follow-up would test the **continuation** direction of no-news moves as its own pre-registered candidate. It
    must not be re-cut from this check data.
- K >= 5 rows are positive in both halves (fit +0.209 n 10; check +0.104 n 16). That is far too few to mean anything,
  and is noted only.
- Nothing here is deployable. The owner rule "no weak setups" applies.

## Known biases (all favour the candidate; it fails anyway)
- Today's symbol list (survivorship; flatters longs).
- Today's ETB flag for shorts.
- Borrow is estimated (1.2 / 3 bp).
- The calendar was fetched after the fact (rare date revisions are not modelled).
- Fills at the next-minute open, with LR8 costs. The signal-close diagnostic is only 0.004R better.

## Rule-change context (owner 2026-11-02)
- Both halves are scored with one fixed rule set: today's LR8 costs and the round-4 chassis. No live rule change
  (11-12 LR8, 10-28 Primary sizing, 10-30 Testing cost filter, 11-17 TSZ1 / SPYEXIT, setup moves) affects these
  figures.

## Files
- `research/ultimate_1119/modules/ULT-34.py`: the module, constants = the pick.
- `research/ultimate_1119/round4/ULT-34/`:
  - `bt.py`, `test_module.py`;
  - `fit_grid.json`, `fitsel.json`, `fit_random.json`;
  - `check_once.json`, `check_plateau.json`, `check_trades.csv.gz`;
  - this file.
- Scratch signal and walk parquet files were deleted after scoring.

Educational only — not financial advice.
