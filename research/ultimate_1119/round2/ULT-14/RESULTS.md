Educational only — not financial advice

# ULT-14 SNAP — sharp counter-move against an intact trend, LONG + SHORT (round 2)

**Tier: FAIL. Not TIER A, not B, not BEATS.** All 8 configurations lose on FIT after costs (-0.019 to -0.273R per
trade), so TIER A and TIER B are both out of reach (both need fit avg R > 0). The fit pick **14a** (14:00-15:00,
D 0.20 daily ATR, t05s1 cap45) was scored once on CHECK: **+0.004R/trade**. Without its best day it is -0.013. The
day-clustered t is 0.10, against a bar of 3.65. It traded 2.94 times per session, for +3.0R over 276 sessions. That is
flat. The long side is mildly positive (+0.047 check, -0.011 fit). The short side loses in both halves (-0.040 check,
-0.071 fit).

## In plain words
- We built the shared core of NM-ETF, ST7 and L3 directly. In names with ADV >= $50M and cost_r <= 0.08:
  - **Long:** buy a 15-minute drop of at least D daily ATRs while +DI(7) >= -DI(7), 19-bar buy pressure > 0, daily
    ATR >= 3% and SPY's 60-minute change > -0.40%.
  - **Short:** the mirror image, plus gap < +0.5%, 25 <= RSI5 < 90, SPY since 09:50 <= +0.20%, and easy-to-borrow.
- **The volume is there; the edge is not.** The 11:00-15:00 window gives 12/session on fit and 16.5/session on check.
  It loses in both halves (fit -0.090, check -0.023). The 14:00-15:00 window (the NM-ETF/L3 time) gives about
  3/session and is about flat on check.
- **The trigger barely beats random.** Random entries in the same names, sessions and sides earn -0.039 on fit
  (signal +0.003 better) and -0.024 on check (signal +0.028 better). Split by side:

  | side | fit: signal minus random | check: signal minus random |
  |---|---|---|
  | long | +0.022 | +0.051 |
  | short | -0.021 | +0.005 |

  So the short fade adds nothing over random entries. The long dip-buy adds a little, but it sits on a base that loses
  about 0.03R to costs.
- **The short side is the drag.** It is worst on SPY-up days: fit -0.29, check -0.33 (end-of-day label,
  reporting only). The SPY-since-09:50 <= +0.20% skip does not stop the tape from rallying later in the day.
- **Dropping the short side would not have rescued it.** The fit pick's long side is -0.011 on fit (-0.078 without its
  best day), and no long-only config was pre-registered. Read the long check figure (+0.047, t 1.08) only as a
  plateau note. It is not a candidate.
- **Nothing here is carried by one day, because there is nothing to carry.** The check best day (2026-07-29, +13.2R) is
  more than the whole +3.0R total (best-day share 433%, "1 day" tag). Without it, check total R is -10.2.

## Build (faithful to round2/PLAN.md sec. 3 "ULT-14")
- **Live module** `research/ultimate_1119/modules/ULT-14.py`.
  - It exposes `SIDE`, `GEOM`, `LAYERS`, `features()`, `trigger(r, sgn, d)` and `mask()`.
  - Indicators come from `mcf.research.arena.indicators.compute` (`ret3_atr`, `di_diff7`, `atr_d_pct`), the same call
    the WB4/ULT-12 modules make.
  - Constants are set to the fit pick 14a: WINDOW 14:00-15:00, D 0.20, GEOM t05s1.
  - Two sides, one file (the ULT-05 pattern): the side comes from the setup name. A name ending in "-S" / "-short" is
    the short side; anything else is the long side.
  - bt.py imports `features()` / `trigger()`, so the backtest and live share one code path.
  - YAML it would need (NOT written to any config): two entries `type: lab, module: research/ultimate_1119/modules/ULT-14.py,
    min_adv: 50000000, window: [1400, 1500], context: [spy_fo], refire: true, refire_cooldown: 0, geom: t05s1,
    time_stop_min: 45, time_stop_min_r: 99`, named e.g. `ULT-14-L` / `ULT-14-S`. The short side also needs the account's
    `shorts.require_easy_to_borrow`.
- **Smoke test** `round2/ULT-14/test_module.py` (3 passed). It checks that:
  - the long side fires under the live LabStrategy on a sharp drop in an uptrend at 14:00-14:10, with t05s1 levels
    (+0.5u / -1u) and t1s1 levels (+1u);
  - the short side fires on the mirror pattern, with short levels;
  - each side ignores the other side's pattern;
  - SPY -0.6% over the hour blocks the long, and SPY +0.5% since 09:50 blocks the short;
  - with no SPY context, neither side signals;
  - features do not change when later bars are removed (no look-ahead).
- **Build rules fixed before any fit scoring:**
  - (a) The long side has a tape rule of its own (SPY 60-min), so the chassis' universal SPY long filter is not added
    (PLAN sec. 2 exception). The universal short filters are kept: gap >= +0.5% excluded, RSI5 < 25 excluded. The
    spec's "gap <= +0.5%" is therefore applied as < +0.5%.
  - (b) "ret3 <= -D x atr_d" = `ret3_atr` <= -D: the 15-min change of 5-min closes, in prior-day daily ATRs.
  - (c) The ATR >= 3% floor applies to the long side only, as the spec states.
  - (d) If the SPY reference row is missing, the side does not fire. Both windows start >= 11:00, so this never
    binds.
- **Chassis:**
  - Intake: U2 (price >= $10, |gap| < 20%, atr_d > 0, cost_r <= 0.08, point-in-time ADV20 >= $50M).
  - Entry: the OPEN of the 1-minute bar that starts at the decision close.
  - Brackets: placed around the decision close (u = 0.25 dATR), with R per u (the actual risk, which here equals the
    0.25-dATR unit). Walked on 1-minute bars: stop first, gap-through at the worse of open/stop, target at the limit
    with no exit cost, 45-min time exit, flat 15:50.
  - Costs: LR8, plus **1.2 bp of entry notional borrow fee on every short**.
  - **Shorts ETB only** (data/universe.csv, today's flag): this removed 59 fit / 109 check superset short bars.
  - Lots: one lot per symbol shared by both sides, refire >= 30 min after the exit, max 2 per symbol-session, day cap
    30 over both sides (first by time, ties ADV20 desc).
  - The cap binds hard in volatile stretches. The fit pick has 459 trades capped vs 922 uncapped; the uncapped fit
    run is +0.040 but -0.024 without its best day, driven by the April 2025 crash days. Check: 812 capped vs 917
    uncapped (+0.010, t 0.21). For 11:00-15:00 (14e) the cap keeps 2,008 of 3,828 fit trades.
- **Data hygiene:**
  - Forbidden frame columns (win_*, r_long*, r_short*, any *heat*) are dropped before features are built, and this
    is asserted.
  - The locked block is never read: pyarrow filters on frame and 1-minute loads, `no_locked()` asserts, and
    MCF_HIST_ALLOW_LOCKED is refused.
  - Check data was built only after fitsel.json existed (asserted), and check_once.json is write-once (asserted).
- **Remaining biases (all favour the candidate):**
  - Survivorship: today's 1,226-name list, which flatters longs. The signal-minus-random figure is the
    survivorship-neutral read.
  - The ETB flag is today's, not point-in-time.
  - The borrow fee is a flat estimate.

## Selection (FIT only) — every configuration
**Rule** (PLAN sec. 5): pick the config with the highest fit total R minus its best fit day, among configs with >= 2.0
trades/session. Eligible configs: 14a, 14b, 14e, 14f, 14g, 14h. 14a is also the highest by plain fit total R among the
eligible configs, so the task's wording and PLAN's rule give the same pick. Best-day share is n/a on fit (every total
is < 0).

| cfg | window-D-exit | FIT /sess | FIT avg R | w/o best day | total R | total w/o best | worst day / trade-sess | t | SPY up / flat / down | ex 04-03..09 | A / B | long / short avg R (n) | CHECK plateau (after the single score): avg R / w/o best / t / per sess / long / short |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **14a** | 1400-1500, 0.20, t05s1 | 2.70 | -0.038 | -0.074 | -17.4 | **-31.9** | -4.09 | -0.61 | +0.046 / -0.098 / -0.041 | -0.024 | +0.001 / -0.082 | -0.011 (250) / -0.071 (209) | **+0.004 / -0.013 / 0.10 / 2.94 / +0.047 / -0.040** |
| 14b | 1400-1500, 0.20, t1s1 | 2.69 | -0.048 | -0.120 | -22.1 | -51.6 | -4.26 | -0.51 | -0.069 / -0.152 / +0.024 | -0.006 | +0.016 / -0.123 | -0.029 (249) / -0.071 (209) | +0.009 / -0.014 / 0.20 / 2.94 / +0.076 / -0.058 |
| 14c | 1400-1500, 0.30, t05s1 | 0.62 | -0.019 | -0.084 | -2.0 | -6.3 | -0.80 | -0.28 | +0.142 / -0.170 / -0.112 | -0.149 | +0.069 / -0.162 | +0.034 (70) / -0.125 (35) | +0.010 / -0.014 / 0.16 / 0.59 / +0.067 / -0.040 |
| 14d | 1400-1500, 0.30, t1s1 | 0.62 | -0.273 | -0.286 | -28.6 | -29.8 | -2.92 | -3.28 | -0.198 / -0.354 / -0.304 | -0.273 | -0.196 / -0.398 | -0.228 (70) / -0.362 (35) | +0.071 / +0.023 / 0.75 / 0.59 / +0.154 / -0.003 |
| 14e | 1100-1500, 0.20, t05s1 | 11.81 | -0.090 | -0.095 | -180.6 | -188.7 | -2.71 | -3.41 | -0.049 / -0.092 / -0.114 | -0.071 | -0.113 / -0.072 | -0.036 (816) / -0.127 (1192) | -0.023 / -0.026 / -1.62 / 16.5 / -0.016 / -0.030 |
| 14f | 1100-1500, 0.20, t1s1 | 11.79 | -0.105 | -0.113 | -209.6 | -223.5 | -2.85 | -3.17 | -0.087 / -0.092 / -0.126 | -0.071 | -0.149 / -0.070 | -0.076 (812) / -0.124 (1192) | -0.017 / -0.022 / -0.89 / 16.4 / -0.005 / -0.028 |
| 14g | 1100-1500, 0.30, t05s1 | 3.04 | -0.073 | -0.089 | -37.4 | -43.4 | -2.60 | -1.84 | +0.015 / -0.072 / -0.135 | -0.073 | -0.091 / -0.056 | -0.007 (203) / -0.115 (313) | -0.018 / -0.027 / -0.63 / 3.22 / +0.000 / -0.034 |
| 14h | 1100-1500, 0.30, t1s1 | 3.02 | -0.176 | -0.201 | -90.2 | -99.2 | -6.19 | -2.48 | -0.212 / -0.130 / -0.187 | -0.120 | -0.256 / -0.103 | -0.135 (202) / -0.202 (311) | -0.009 / -0.029 / -0.24 / 3.22 / -0.007 / -0.012 |

The fit pick's best fit day is 2025-04-10 (+14.5R) and its worst is 2025-04-04 (-17.9R). Without 2025-04-03..04-09, the
fit avg R is -0.024. The April 2025 crash week hurts this setup rather than carrying it.

Plateau read (diagnostic only, never used to re-select):
- No check config is a clear positive. Every check avg R lies in -0.023..+0.071, and every t is <= 0.75.
- 14d (+0.071 on check) was the worst fit config (-0.273, t -3.28) and trades 0.59/session.
- Across all 8 configs the long side beats the short side on both check and fit (8 of 8 each).

## The single CHECK score (fit-frozen 14a, fitsel.json frozen 2026-11-19T06:55:47Z, scored 06:57:40Z)

| metric | CHECK (276 sessions) | FIT (170 sessions) |
|---|---|---|
| trades / per session | 812 / **2.94** (190 sessions traded) | 459 / 2.70 |
| win rate | 0.607 | 0.601 |
| avg R (actual risk = 0.25-dATR units) | **+0.0038** | -0.0380 |
| avg R w/o best day | **-0.0130** (best 2026-07-29 +13.2R, share 433% → "1 day" tag) | -0.0743 |
| total R / per session | +3.05 / +0.011 | -17.4 / -0.102 |
| worst day / per trade-session | -16.7 (2026-04-23) / **-3.90** (bar -2.152) | -17.9 / -4.09 |
| day-clustered t | **0.10** (bar 3.65) | -0.61 |
| SPY up / flat / down (end-of-day label, reporting only) | +0.020 / -0.054 / +0.061 | +0.046 / -0.098 / -0.041 |
| without 2025-04-03..04-09 | +0.004 (no such days in check) | -0.024 |
| first / second half | -0.049 / +0.065 | A +0.001 / B -0.082 |
| long side | 407 tr, +0.047, w/o best +0.019 (share 63%, "1 day"), t 1.08 | 250 tr, -0.011 |
| short side | 405 tr, -0.040, w/o best -0.073, t -0.67; SPY-up days -0.326 | 209 tr, -0.071 |
| random control (same symbol-session-side, random bar in window, same exit) | -0.024 → signal +0.028 (long +0.051, short +0.005) | -0.039 → signal +0.003 (long +0.022, short -0.021) |
| bias diagnostic (signal-close fill, no borrow fee) | +0.021 (vs +0.004 with both fixes) | -0.014 (vs -0.038) |
| median hold / exit mix | 25 min / target 417, time 273, stop 122 | 18 min / target 245, time 128, stop 86 |
| uncapped (no day cap) | 917 tr, +0.010, w/o best -0.019, t 0.21 | 922 tr, +0.040, w/o best -0.024 |

**Bars:**
- TIER A needs fit avg R > 0 (fit is -0.038, fail), check w/o best day > 0 (-0.013, fail), check avg R > 0 (+0.004,
  pass) and >= 2/session (2.94, pass). Result: **not TIER A.**
- TIER B needs fit avg R > 0. Result: **not B.**
- BEATS: also fails on avg R, w/o best day, worst day/trade-session (-3.90 < -2.152) and t (0.10 < 3.65).
- **Verdict: FAIL.**

The two cheap bias fixes cost about 0.02R per trade on both halves (next-minute-open fill, plus the 1.2 bp borrow fee
on shorts). Without them, check would read +0.021. It would still be far from any bar.

## Configurations counted
- 9 for this candidate: 8 grid + 1 bias diagnostic. These were already in PLAN sec. 4's round-2 total of 92.
- Cumulative N stays **774**, so the t floor is sqrt(2 ln 774) = 3.65.
- The random controls and the check plateau are reported, not counted (PLAN sec. 4).
- No amendments.

## Rule-change context (owner 2026-11-02)
- The 2-year halves are scored with one fixed rule set (today's chassis), so no live rule change falls inside them.
- The evidence quoted in the spec spans ledger changes listed in round-1 RESULTS.md: 11-12 LR8 cost model, 10-28
  Primary sizing, 10-30 Testing cost filter, 11-17 TSZ1 half-size lots / SPYEXIT. This applies to the ST7 check +0.084,
  the L3 live +0.204, and NM-ETF.

## What it says for the next round
- The "common core" does not hold up as a broad, two-sided, ATR-scaled rule. What NM-ETF and L3 earn seems to sit in
  their own specifics: the ETF list, and the dip-buy side.
- **The short counter-trend fade is not worth pursuing in this form.** It adds nothing over random entries on either
  half, and it is badly hurt on SPY-up days.
- The long dip-buy beats random by +0.02 (fit) and +0.05 (check). That is the same pattern as round 1: the trigger
  adds a little, but the base loses to costs. It is not enough to force anything; the owner said no weak setups.

## Files
- `research/ultimate_1119/modules/ULT-14.py`: the live module, set to the fit pick.
- `research/ultimate_1119/round2/ULT-14/test_module.py`: the smoke test.
- `research/ultimate_1119/round2/ULT-14/bt.py`: the backtest.
- `research/ultimate_1119/round2/ULT-14/` json outputs: `fit_grid.json`, `fitsel.json`, `fit_random.json`,
  `check_once.json`, `check_plateau.json`.
- The trade lists and signal/walk parquet files were in the scratchpad and were deleted after scoring.

Educational only — not financial advice.
