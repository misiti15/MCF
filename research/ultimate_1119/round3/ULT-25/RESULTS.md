Educational only — not financial advice

# ULT-25 ULTRA-CHEAP — round 3 result: **FAIL** (CHECK-INFORMED)

Research only: no setup, exit, config or account change. Nothing committed. Pre-registration: round3/PLAN.md sec. 3 "ULT-25".

## Verdict in one paragraph
Trading only the cheapest names (cost_r <= 0.03 of a 0.25-ATR unit, ADV20 >= $300M, ATR% >= 2) did what it was meant
to do on volume: 6.6/session on fit and 14.5/session on check for the pick, 12-22/session in the 10:30 window. It did
not make the triggers pay. **All 12 configs were negative on FIT** (avg R -0.002 to -0.024). The fit pick 25l
(m 0.50, TX-45, 13:00-15:00) scored **-0.0065R on CHECK** (w/o best day -0.0078, day-clustered t -1.49). Every config
was negative on check as well (plateau, diagnostic only). Fit avg R < 0 rules out TIER A and TIER B. The design
assumed the short triggers carried a relative edge of +0.05-0.10R. They did not: TS-2 roll-over made up about 90% of
trades and lost in both halves, and signal minus same-name random was only +0.0003 (fit) / +0.0079 (check). Low
cost per R does not create an edge. It only stops costs from eating one that already exists.

## Build
- Module: `research/ultimate_1119/modules/ULT-25.py` (+ `ULT-25_symbols.json`, LEV / NONLEV lists built from fund names
  only by `round3/ULT-25/make_symbols.py` before any scoring). It is a two-sided, one-file module as in ULT-15: a setup
  name ending "-S" is the short side, which uses YAML `symbols: module` (non-LEV names). Live unit Ru is set by YAML
  `r_atr_frac = M`. TX-45 is GEOM "S" with `stop_price` at 2 Ru, `time_stop_min 45`.
- Smoke test: `round3/ULT-25/test_module.py`, 4 passed. It checks: both sides run under the live LabStrategy, the TX-45
  2 Ru stop, no SPY context -> no signal, the SPY 60-min / band filter blocks longs, a $20 name fails cost_r, the SPY
  since-09:50 rule blocks shorts, a LEV fund is never shorted, and point-in-time truncation for every feature and both
  side signals.
- Backtest: `round3/ULT-25/bt.py`, on the round-2/3 chassis. Entry is the open of the next 1-min bar (LR8 entry cost).
  Brackets sit around the decision close, walked on 1-min bars (stop first, gap-through at the worse price, target at
  the limit, +2c on stops). Time exit is at 45 min, flat 15:50. Shorts pay borrow (1.2 bp of entry notional, 3 bp under
  $20) and must be easy to borrow (data/universe.csv, today's flag). One lot per symbol across both sides, refire >= 30
  min after the exit, max 2 per symbol-session, day cap 30. Stats, sub-halves and SPY day types are imported unchanged
  from ULT-23/bt.py. Forbidden columns (win_*, r_long*, r_short*, *heat*) are dropped and asserted absent. Every load
  asserts that the locked block is never touched.
- One faithful-build note: the frames start at the 09:50 bar, so the "SPY 60-min change" is taken from the change since
  the 09:30 open for bar closes 10:30-10:45 (the 60-min-back bar does not exist there). This is point-in-time and
  documented in the module. It does not matter for the pick, whose window starts at 13:00.

## Configurations
12 grid + 1 bias diagnostic = **13 counted**, inside round 3's pre-registered 101. Cumulative N = **880**, t bar
sqrt(2 ln 880) = 3.68. The random controls are reported and not counted.

## FIT grid (170 sessions; R per actual risk; all costs and borrow in)
| cfg | label | tr/sess | avg R | w/o best day | total R | total − best day | A / B | long avg R (n) | short avg R |
|---|---|---|---|---|---|---|---|---|---|
| 25a | m0.25 t05s1 1030 | 11.94 | -0.0161 | -0.0216 | -32.6 | -43.1 | -0.010 / -0.023 | -0.008 (222) | -0.017 |
| 25b | m0.25 t05s1 1300 | 6.76 | -0.0229 | -0.0348 | -26.3 | -38.9 | -0.032 / -0.011 | +0.154 (102) | -0.040 |
| 25c | m0.25 t1s1 1030 | 11.88 | -0.0226 | -0.0309 | -45.6 | -61.5 | -0.015 / -0.031 | -0.060 | -0.018 |
| 25d | m0.25 t1s1 1300 | 6.69 | -0.0239 | -0.0416 | -27.2 | -46.1 | -0.027 / -0.020 | +0.149 | -0.041 |
| 25e | m0.25 TX45 1030 | 11.85 | -0.0192 | -0.0241 | -38.7 | -47.8 | -0.018 / -0.021 | -0.072 | -0.013 |
| 25f | m0.25 TX45 1300 | 6.63 | -0.0060 | -0.0188 | -6.8 | -20.6 | -0.003 / -0.010 | +0.231 | -0.030 |
| 25g | m0.50 t05s1 1030 | 11.87 | -0.0102 | -0.0146 | -20.7 | -29.0 | -0.006 / -0.015 | -0.025 | -0.008 |
| 25h | m0.50 t05s1 1300 | 6.67 | -0.0023 | -0.0132 | -2.7 | -14.6 | +0.006 / -0.013 | +0.181 | -0.021 |
| 25i | m0.50 t1s1 1030 | 11.85 | -0.0184 | -0.0232 | -37.0 | -46.1 | -0.016 / -0.021 | -0.059 | -0.014 |
| 25j | m0.50 t1s1 1300 | 6.64 | -0.0063 | -0.0200 | -7.1 | -22.0 | -0.003 / -0.010 | +0.231 | -0.030 |
| 25k | m0.50 TX45 1030 | 11.85 | -0.0085 | -0.0110 | -17.2 | -21.8 | -0.009 / -0.008 | -0.029 | -0.006 |
| **25l** | **m0.50 TX45 1300** | 6.63 | **-0.0023** | -0.0087 | -2.6 | **-9.6** | -0.002 / -0.003 | +0.116 (104) | -0.014 |

All 12 configs meet >= 2/session. The pick by the pre-registered rule (max fit total R minus best fit day) is **25l**.
The task's plain "fit total R" rule also picks 25l. Frozen in `fitsel.json` at 2026-11-19T08:04:46Z, before any check
frame was built. It holds sha256 of bt.py, of the module at freeze, of the module with the frozen constants (M 0.50,
EXIT X, WINDOW 13:00-15:00) and of the symbol lists.

Fit pick details: 1,127 trades, win 48%, total R -2.6, best day 2025-04-09 (+6.95R; no best-day share because the total
is negative), worst day -5.9 (-0.69 per trade-session), t -0.20, R per 0.25-dATR unit -0.0092. **Without
2025-04-03..04-09: -0.0128.** SPY up / flat / down days: -0.005 / -0.009 / +0.003. Median hold 45 min, all time exits.
By trigger (fit): collapse +0.065 (36), WB4-A dip +0.143 (68), TS-1 +0.036 (25), **TS-2 -0.012 (1,015)**.

## CHECK — scored ONCE on 25l (276 sessions, 2025-10-01..2026-11-04)
| metric | value |
|---|---|
| trades / per session | 4,008 / **14.52** (243 sessions traded) |
| win | 48.1% |
| **avg R (actual risk, per 2 Ru = 1 ATR)** | **-0.0065** |
| avg R per 0.25-dATR unit | -0.0259 |
| **avg R w/o best day** | **-0.0078** (best day 2026-04-23 +4.89R; no share because the total is negative) |
| total R / per session | -25.97 / -0.094 |
| worst day / per trade-session | -4.25 / -0.258 |
| **day-clustered t** | **-1.49** (bar 3.68) |
| first / second half | -0.0123 / -0.0026 |
| SPY up / flat / down days | -0.038 (533) / -0.005 (1,893) / +0.002 (1,582) |
| without 2025-04-03..04-09 | -0.0065 (check has no such dates) |
| side split | long -0.0017 (184, 0.67/session, t -0.13); short -0.0067 (3,824, 13.9/session, t -1.44) |
| by trigger | collapse -0.001 (125), dip -0.004 (59), TS-1 -0.031 (85), TS-2 -0.006 (3,777) |
| same-name random control | random -0.0143; **signal − random +0.0079** (long -0.0042, short +0.0085) |
| fit random control | random -0.0026; signal − random +0.0003 (long -0.059, short +0.006) |
| bias diagnostic (signal-close fill, no borrow) | fit -0.0006, check -0.0049 (fill + borrow cost ≈ 0.002R) |
| uncapped (no day cap 30) | 19.0/session, -0.0036 |
| exit mix | 4,007 time, 1 stop |

**Tier: FAIL.** Fit avg R -0.0023 is <= 0, which rules out TIER A and TIER B. Check avg R, check avg R w/o best day and
check total R per session are all negative, and t = -1.49. Of the BEATS bars, only volume (14.5/session) and the
worst-day bar (-0.258 >= -2.152) are met.

## CHECK plateau (diagnostic only, never used to re-select)
Every config is negative on check: -0.007 (25l) to -0.031 (25a), t -1.3 to -2.5. The long side is mildly positive in
the 10:30 window (+0.017..+0.051, about 0.6-1.3/session). The short side is negative in all 12 configs
(-0.008..-0.041). The wider unit (m 0.50) and TX-45 lose least, as the thesis expected for geometry. But they lose less
only because costs per R are smaller, not because a positive edge appears.

## What was learned (for the next round)
1. **The cheap universe is real and high volume.** About 12 names/day on fit and more on check (2025-26 has many
   $300+ high-ATR names: LITE, APP, GEV, ALAB, MDB, BE, MELI, CLS, STX, ...). Costs per R are about 0.01-0.03. This is a
   good chassis for a trigger that actually has an edge.
2. **TS-2 roll-over without a base is not an edge.** It is the bulk of the volume, and RSI5 >= 80 turning down with any
   upper wick fires constantly on strong names. Its relative edge over random is about +0.006-0.009R, not the +0.13
   seen inside ULT-15's gap-down / down-tape base. In the cheap universe, random shorts lose (-0.015..-0.021), so the
   short side here is a weak trigger on a losing base.
3. **The long triggers do not carry over to this universe.** Fit 13:00-15:00 longs looked strong (+0.116..+0.23 per
   trade, t 3.2, 0.6/session), but the check long side is about 0 and below its own random control (-0.004). The fit
   long edge was also below random on fit (random long +0.175). A strong-tape survivorship effect on high-ATR names is
   the likely reason. This is not a lead.
4. A follow-up that is not a re-tune of this grid would put the ULT-15-style **gated base** (gap-down, down tape) under
   the cheap universe's cost floor for shorts. This is a new pre-registered candidate, counted. ULT-25's own grid is
   closed.

## Bias and caveats
Today's symbol list (survivorship; it flatters longs). Today's easy-to-borrow flag. Borrow is a flat estimate (1.2 bp).
Fills are at the next 1-min open (the signal-close diagnostic is shown). CHECK-INFORMED (TS-1 / TS-2, collapse;
PLAN sec. 0.5). None of these can turn a negative fit and check into a pass.

## Rule-change context
Both halves are scored with one fixed rule set (today's LR8 costs, round-2/3 chassis). No live rule change falls inside
them (ledger changes 10-28 sizing, 10-30 Testing cost filter, 11-12 LR8, 11-17 TSZ1 / SPYEXIT all post-date or do not
apply to this research replay).

## Files
`round3/ULT-25/`: bt.py, make_symbols.py, test_module.py, fit_grid.json, fitsel.json, fit_random.json, check_once.json,
check_plateau.json, check_trades.csv.gz. `modules/ULT-25.py`, `modules/ULT-25_symbols.json`. The working parquet files
were deleted.

Educational only — not financial advice.
