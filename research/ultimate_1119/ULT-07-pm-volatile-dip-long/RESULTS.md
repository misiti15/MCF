Educational only — not financial advice

# ULT-07 afternoon volatile dip buy (NM-ETF WB4 chassis, broadened) — RESULTS

**Tier: FAIL.** Fit avg R is negative in all 8 grid configs. The fit-selected config (07a) is negative on check too:
-0.030 R per trade, -0.037 without the best day, 5.45 trades/session. It does beat random entries by +0.02 R (check)
and +0.07 R (fit), but not by enough to cover costs. Research only. Nothing is enabled, committed or changed in any account.

Pre-registration: research/ultimate_1119/PLAN.md sec. 3 "ULT-07", sec. 5 (selection), sec. 6 (deploy bar). No amendments.

## What was built
- Live-ready module: `research/ultimate_1119/modules/ULT-07-pm-volatile-dip-long.py`. It has the same interface as the
  deployed workbench / ULT modules (`SIDE`, `GEOM`, `WINDOW`, `LAYERS`, `mask(df)`, `stop_price(f, i)` for geom "S")
  and needs YAML `context: [spy_fo]`, `min_adv: 20000000`, `refire: true`, `refire_cooldown: 0`, `time_stop_min: 45`,
  `time_stop_min_r: 99`. Without SPY context it gives no signal (fail safe). The defaults are config 07a.
- Smoke test: `research/ultimate_1119/ULT-07-pm-volatile-dip-long/test_module.py` (passes). It checks that the module
  runs under the live `LabStrategy`, fires inside 14:00-15:00, gives t05s1 levels (+0.5R / -1R) and a 2R stop for
  geom S, blocks when SPY's 60-min return is <= -0.40%, and gives no signal without context.
- Backtest: `bt.py` (signals come from the module's own `mask` on the lab frames; 1-minute exit walk as in
  benchmark/bench.py, costs LR8) and `score.py` (fit grid, `fitsel.json` frozen before any check data was loaded, a
  single check score, random control, plateau diagnostic).

Rule as built (all point-in-time, at the decision 5-min bar close):
- Intake U: price >= $10, ADV20 >= $20M, |gap| < 20%, cost_r <= 0.10, R = 0.25 x prior daily ATR.
- daily ATR % of price >= A_MIN; (close - 09:30 open) / daily ATR <= -DROP.
- 19-bar buyPressure > 0.
- RSI(5) crossed up through 30 on this bar or the previous one.
- SPY 12-bar (60-min) return > -0.40%.
- Window 14:00-15:00 bar close.
- One lot per symbol, re-entry only 30 min after the exit, max 2 per symbol-session, day cap 30. Flat 15:50 (the last
  exit is at 15:45).

Faithfulness notes (two places where I had to interpret the spec):
1. **"atrPct" is read as daily ATR % of price** (atr_d / close; the NM-ETF chassis' `atr_d_pct` >= 3.6). The frame
   column `atrPct` is the 5-minute ATR (median 0.19% of price), so a 3-4% floor on it would select almost nothing.
   That cannot be the intent.
2. **The window is 14:00-15:00, not 14:00-15:15.** The lab frames end at the 15:00 bar close, and the live
   `LabStrategy` clamps tod <= 1500. So the effective window is the same live and in the backtest.
- Point-in-time review: RSI5, buyPressure and fromOpen come from closed 5-min bars. atr_d is the prior-day ATR.
  adv20 uses prior sessions only. spy_fo is taken at the same bar close. No end-of-day labels are used. Check:
  no look-ahead found.
- The PLAN's trigger (RSI5 turning up + ATR-unit drop) is **not** WB4's trigger (15-min drop ret3 <= -0.75% plus
  +DI/-DI). The ETF-list subset below shows that this difference matters on its own.

## Data / split
- FIT = 2024-10 + 2025-03..2025-09: 170 sessions. CHECK = 2025-10-01..2026-11-04: 276 sessions.
- The locked block 2024-11-01..2025-02-28 was never read. pyarrow filters exclude it, every frame, trade list and
  1-minute load asserts it is absent, and MCF_HIST_ALLOW_LOCKED was never set.
- Survivorship bias: today's 1,226-symbol list, which flatters longs. Borrow is not relevant (long only).
- TX45 is scored per unit of risk (2R catastrophic stop, divided by 2), the same as the sibling ULT candidates.

## Configurations
- 8 grid configs plus 1 uncapped diagnostic (the PLAN-counted 9).
- Also 2 extra diagnostics, never used for selection: the module's own bar-only refire chain, and the ETF-list subset.
- Total evaluated: 11. Plus 2 random-entry controls (fit and check), which are not counted as candidates.

## FIT grid (costs in)
| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold |
|---|---|---|---|---|---|---|---|---|---|---|
| 07a A3-D1-t05s1 | 431 | 2.54 | 0.538 | -0.042 | -0.058 | n/a (total < 0) | -18.3 | -0.108 | -12.7 | 37 |
| 07b A3-D1-TX45 | 420 | 2.47 | 0.414 | -0.069 | -0.078 | n/a | -29.1 | -0.171 | -12.1 | 45 |
| 07c A3-D1.5-t05s1 | 101 | 0.59 | 0.446 | -0.249 | -0.264 | n/a | -25.1 | -0.148 | -17.3 | 27 |
| 07d A3-D1.5-TX45 | 100 | 0.59 | 0.390 | -0.150 | -0.189 | n/a | -15.0 | -0.088 | -15.8 | 45 |
| 07e A4-D1-t05s1 | 214 | 1.26 | 0.486 | -0.127 | -0.154 | n/a | -27.2 | -0.160 | -15.1 | 38 |
| 07f A4-D1-TX45 | 208 | 1.22 | 0.356 | -0.143 | -0.154 | n/a | -29.8 | -0.175 | -17.4 | 45 |
| 07g A4-D1.5-t05s1 | 46 | 0.27 | 0.326 | -0.401 | -0.421 | n/a | -18.5 | -0.109 | -11.8 | 32 |
| 07h A4-D1.5-TX45 | 46 | 0.27 | 0.304 | -0.201 | -0.237 | n/a | -9.3 | -0.054 | -9.3 | 45 |

- Selection rule (PLAN sec. 5): highest fit total R among configs with >= 2 trades/session. Only 07a and 07b qualify,
  and **07a** wins. 07a is also the better of the two on avg R without the best day. Frozen in `fitsel.json` before
  check.
- 07a fit by SPY day type (up / flat / down): -0.011 / -0.058 / -0.044. Excluding the 2025-04-03..09 week: -0.050.
- Fit diagnostics for 07a:
  - Uncapped: 547 trades, -0.232 avg, -127.1 R. The worst day is -110 R (the April crash). The day cap is doing its job.
  - Module bar-only refire chain: 420 trades, -0.048, close to the chassis result, so live and backtest agree.
  - Random control: 431 trades, -0.116 avg, -49.8 R.

## CHECK — 07a scored once
| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold |
|---|---|---|---|---|---|---|---|---|---|---|
| 07a A3-D1-t05s1 | 1505 | 5.45 | 0.534 | **-0.030** | **-0.037** | n/a (total < 0) | -44.6 | -0.162 | -16.0 | 41 |

- SPY up / flat / down days: -0.023 / -0.017 / -0.040. Check halves H1 / H2: -0.018 / -0.040. Traded 239 of 276
  sessions. Best day 2026-02-04.
- Random entries (same symbol-sessions, a random intake bar in 14:00-15:00, same exit): 1505 trades, -0.050 avg,
  -0.060 w/o best day, -75.1 R. The signal beats random by **+0.020 R/trade** on check (+0.074 on fit). The timing
  carries some information, but not enough to pay the costs.
- Uncapped diagnostic: -0.026 (5.57/session). Module-chain diagnostic: -0.031.
- Monthly: 6 of 14 months are positive. The worst months are 2025-10 (-22.2 R), 2026-06 (-20.5 R) and 2026-09 (-17.5 R).

Deploy bar (PLAN sec. 6) for 07a:
| condition | needed | 07a | pass? |
|---|---|---|---|
| fit avg R | > 0 | -0.042 | no |
| check avg R | > 0 | -0.030 | no |
| check avg R w/o best day | > 0 | -0.037 | no |
| check trades/session | >= 2 | 5.45 | yes |
| look-ahead | none | none found | yes |

TIER B needs fit avg R > 0, and fit is -0.042, so the result is **FAIL**.
The benchmark comparison (beat ST7-FD at +0.262 R/session) does not apply.

## Plateau on check (diagnostic only, never used to re-select)
| config | trades | /session | avg R | avg R w/o best day | best-day share | total R |
|---|---|---|---|---|---|---|
| 07a | 1505 | 5.45 | -0.030 | -0.037 | n/a | -44.6 |
| 07b | 1480 | 5.36 | -0.004 | -0.016 | n/a | -6.4 |
| 07c | 375 | 1.36 | +0.013 | -0.007 | 1.55 (1 day) | +4.7 |
| 07d | 364 | 1.32 | +0.030 | -0.001 | 1.02 (1 day) | +11.0 |
| 07e | 899 | 3.26 | -0.011 | -0.026 | n/a | -10.0 |
| 07f | 884 | 3.20 | +0.016 | -0.006 | 1.34 (1 day) | +14.1 |
| 07g | 206 | 0.75 | +0.023 | -0.008 | 1.34 (1 day) | +4.7 |
| 07h | 203 | 0.74 | +0.055 | +0.009 | 0.85 (1 day) | +11.3 |

- The deeper-drop / higher-ATR / TX45 corner is mildly positive on check, but:
  - all of those configs were clearly negative on fit (-0.14 to -0.40);
  - every positive total depends on one day: the best day is >= 85% of total R, and the avg R without the best day is
    <= +0.009.
- This is the selection-noise pattern WAVE1 describes. It is **not** evidence of a plateau.

## Where does it lose? (diagnostics; salvage leads for a later round, not tuned here)
- **ETF list vs broadened universe (07a, same trigger):**
  - The ETF-list names alone: 27 fit trades, -0.010; 36 check trades, -0.078.
  - The non-ETF names: -0.045 fit, -0.028 check.
  - So broadening did not cause the loss. Even on WB4's own ETFs this RSI5-turn trigger does not reproduce WB4's
    +0.13. **WB4's edge does not carry over to this trigger.** A faithful broadening would keep WB4's own trigger
    (ret3 <= -0.75 plus di_diff7 >= -5) and change only the universe.
- **Time block (avg R):**

  | half | 14:00-14:25 | 14:30-14:55 | 15:00 |
  |---|---|---|---|
  | fit | -0.010 (240) | -0.116 (153) | +0.049 (38) |
  | check | -0.038 (806) | -0.031 (615) | +0.057 (84) |

  The 15:00 bar is positive in both halves, but the samples are small. The live note that 14:30-15:00 is the best
  block does not show up here.
- **Down days are the weakest in both halves.** The 60-min SPY guard does not remove that drag.

## Recorded-quote replay (third opinion)
Not run. The candidate fails on fit, so no replay result could change the tier. Also, the recorded-quote replay
(research/reps2/nightly.py --replay) holds only one session (research/reps2/replay_quotes/2026-11-18) and takes about
1 h per run. That is far too small a sample for a long-only 14:00-15:00 setup at about 5 trades/session.

## Rule-change context
- These are backtest figures on fixed rules, so no live rule change is mixed into them.
- The parent's evidence (NM-ETF WB4: 2y +0.130, replay +0.337, live +0.311) comes from the WB4 FREQ change of
  2026-11-17 (ret3 -0.75, di_diff7 >= -5, ret12 guard, refire). The live figure spans that change and the 11-17
  testing-account sizing change (TSZ1: R comparable, $ not).

## Files
- research/ultimate_1119/modules/ULT-07-pm-volatile-dip-long.py
- research/ultimate_1119/ULT-07-pm-volatile-dip-long/{bt.py, score.py, test_module.py, fitsel.json, fit_grid.json, check_selected.json}
- The intermediate parquet files (< 2 MB) were deleted after scoring. Re-run:
  `python bt.py WORK sig|walk fit|check` then `python score.py WORK fit|check`.
