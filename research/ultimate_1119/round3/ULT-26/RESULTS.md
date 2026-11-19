Educational only — not financial advice

# ULT-26 WITH-GAP TREND: gap continuation only on a trend tape (round 3, D5): **FAIL**

Research only. Nothing enabled, committed or changed in any account. Not check-informed (PLAN sec. 0.5).
Pre-registration: round3/PLAN.md sec. 3 "ULT-26". The rules, grid, selection rule and bars were used exactly as written. No amendments.

## Verdict
- **CHECK (scored once, fit pick 26g G3-T0.50-t1s1cap45): avg R -0.0447 per trade after costs + borrow, w/o best day -0.0532,
  t -1.36, 7.84 trades/session, total -96.7R.** Fails every return bar. TIER B also fails (check below -0.02).
- **All 8 grid configs are negative on CHECK** (diagnostic only, never used to re-select): -0.016 to -0.049, both sides
  negative in every config. There is no plateau to salvage.
- The fit pick had warning signs before CHECK was scored: fit sub-half B -0.002 (A +0.084). Only 0.011R over its
  random control. Uncapped it was **-0.037** on fit. Its fit average came from the day cap (keep the first 30 trades of the
  day by time) on the volatile 2025-03..05 sessions.
- Lesson: the "trend day so far" layer as specified (SPY >= +-T from the open AND in the top/bottom 30% of its range)
  is true on ~50% of sessions at some bar (CHECK: 137 up-tape and 118 down-tape sessions of 276 at T 0.30). So it does not pick out
  trend days, and requiring the name's own range position >= 0.6 adds nothing. ULT-05's flat-tape loss is not fixed by
  this tape gate.

## Build
- Live-ready module `research/ultimate_1119/modules/ULT-26.py` (+ `ULT-26_symbols.json`: the LEV deny list and the NONLEV
  allow-list for the short entry, both copied from ULT-25's name-only lists). It has the same interface as rounds 1-2:
  `mask(df)`, `features`, `signal`, `stop_price`, GEOM, LAYERS. One file serves two sides ("-S" = short). It needs `context: [spy_fo]`
  and fails safe without it. Module constants now hold the frozen pick (G 3, T 0.50, EXIT T). bt.py passes g/t explicitly,
  so the backtest does not depend on them.
- SPY range position since 09:30: the history context has no SPY high/low and starts at 09:50, so it is computed from the
  5-minute spy_fo closes since 09:50 with the 09:30 open (0) included. It is the same table live and in the backtest (live rows
  09:35-09:45 are ignored). Caveat: it uses closes, not intrabar extremes. Name range position = dist_lod / (dist_lod + dist_hod) from
  the frame (session HOD/LOD so far). VWAP band = 0.5 x DAILY ATR% (plan text: atr_d%).
- Smoke test `round3/ULT-26/test_module.py`: 4 passed. It covers live LabStrategy both sides, geometry, no signal on
  flat / opposite tape or without a gap, no SPY context, LEV never shorted, a truncation (point-in-time) test, and the SPY range math.
- Backtest `round3/ULT-26/bt.py` (adapted from ULT-25's bt.py, stats from ULT-23's bt.py). Round-3 chassis: entry at the next 1-min open,
  LR8 costs, borrow 1.2 bp of notional (3 bp < $20) on shorts, shorts only ETB and never LEV, one lot/symbol, refire
  >= 30 min after exit, max 2/symbol-session, day cap 30 (first by time, ADV20 desc), flat 15:50, window 10:30-14:30.
  Forbidden columns (win_*, r_*, *heat*) are dropped and asserted absent. Locked block never read (no_locked asserts on frames, trades and 1-min).

## FIT grid (170 sessions; selection = max fit total R minus best day among configs >= 2/session)
| cfg | label | tr/sess | avg R | w/o best day | best-day share | total R | total w/o best | ex 04-03..09 | A | B | t | uncapped trades |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 26a | G2-T0.30-t1s1cap45 | 10.92 | +0.0172 | +0.0055 | 68% (1 day) | 31.9 | 10.1 | +0.0233 | +0.048 | -0.041 | 0.52 | 5681 |
| 26b | G2-T0.30-TX45 | 10.81 | -0.0000 | -0.0063 | — | -0.0 | -11.3 | +0.0198 | +0.014 | -0.027 | -0.00 | 5592 |
| 26c | G2-T0.50-t1s1cap45 | 7.90 | +0.0276 | +0.0182 | 36% | 37.1 | 23.9 | +0.0189 | +0.043 | -0.023 | 0.97 | 4716 |
| 26d | G2-T0.50-TX45 | 7.86 | +0.0031 | -0.0055 | 271% | 4.2 | -7.1 | +0.0129 | +0.013 | -0.029 | 0.11 | 4661 |
| 26e | G3-T0.30-t1s1cap45 | 7.55 | +0.0374 | +0.0210 | 45% | 48.0 | 26.4 | +0.0421 | +0.072 | -0.048 | 0.93 | 3011 |
| 26f | G3-T0.30-TX45 | 7.45 | -0.0031 | -0.0105 | — | -4.0 | -13.0 | +0.0298 | +0.008 | -0.033 | -0.09 | 2950 |
| **26g** | **G3-T0.50-t1s1cap45** | **5.72** | **+0.0681** | **+0.0538** | 23% | **66.2** | **50.7** | +0.0473 | +0.084 | **-0.002** | 2.11 | 2489 |
| 26h | G3-T0.50-TX45 | 5.67 | +0.0068 | -0.0012 | 117% | 6.5 | -1.1 | +0.0251 | +0.015 | -0.031 | 0.19 | 2455 |

All 8 eligible (>= 2/session). Pick 26g (the plain-total-R rule gives the same pick). fitsel.json frozen 2026-11-19T08:13:14Z,
before any CHECK frame was loaded (bt.py asserts it).
Fit pick detail: win 52.9%, best day 2025-04-03 (+15.5R, 23%), worst day -7.79 (-0.75 per trade-session), long +0.082
(3.2/sess) / short +0.050 (2.5/sess; w/o best day +0.015; ex 04-03..09 -0.007), SPY up/flat/down +0.124 / -0.031 /
+0.031, exit mix time 685 / target 177 / stop 110, median hold 45 min. **Without 2025-04-03..04-09: +0.0473.**
Fit first/second half +0.102 / +0.010. **Uncapped (no day cap): -0.0369, worst day -94R.** The fit result depends on the day cap.

## CHECK — fit pick 26g scored ONCE (276 sessions, 2025-10-01..2026-11-04)
| metric | value | bar |
|---|---|---|
| trades / per session | 2,163 / **7.84** (143 sessions traded) | >= 2 ok |
| avg R (actual risk = 0.25-dATR unit) | **-0.0447** | > 0 FAIL; BEATS > +0.0836 |
| avg R w/o best day (2026-10-14, +16.8R) | **-0.0532** | > 0 FAIL; BEATS > +0.0734 |
| best-day share | n/a (total negative) | |
| total R / per session | -96.7 / -0.350 | > 0 FAIL |
| worst day / per trade-session | -26.7 / -1.77 | >= -2.152 ok |
| day-clustered t | **-1.36** | >= 3.68 (N 880) FAIL |
| win | 47.2% | |
| long / short | -0.0363 (4.9/sess) / -0.0586 (3.0/sess, w/o best day -0.082) | |
| SPY up / flat / down day (EOD label) | -0.043 (1175) / -0.173 (301) / +0.008 (687) | |
| first / second half | -0.060 / -0.031 | |
| avg R without 2025-04-03..04-09 | -0.0447 (CHECK has no such dates) | |
| by entry hour 10/11/12/13/14 | -0.115 / +0.006 / -0.024 / -0.076 / +0.085 (n 600/626/349/457/131) | |
| exit mix / median hold | time 1593, stop 300, target 270 / 45 min | |
| uncapped (no day cap) | 14.8/sess, -0.0119, w/o best -0.029, worst day -102.9R | |
| bias diagnostic (fill at signal close, no borrow) | -0.0392 | still negative with the favourable biases |
| **tier** | **FAIL** | |

## Random-entry control (same symbol-sessions, sides and count; random decision bar 10:30-14:30; same exit)
- FIT: random +0.0591, signal minus random **+0.011** (long +0.017, short +0.004).
- CHECK: random +0.0694, signal minus random **-0.114** (long -0.099, short -0.140).
- Read with care. The control uses only sessions in which the signal fired, i.e. the name ended up holding its gap side
  on a trending tape at some point. A random bar earlier in such a session knows that the move is coming (look-ahead in the
  control, not in the candidate). So "random > 0" is not a tradable base. It does show that the pullback-to-VWAP entry
  inside those sessions is worse than an arbitrary time (adverse on CHECK).

## CHECK plateau (all 8 configs, diagnostic only)
| cfg | tr/sess | avg R | w/o best | t | long | short |
|---|---|---|---|---|---|---|
| 26a | 16.86 | -0.0365 | -0.0425 | -1.46 | -0.032 | -0.044 |
| 26b | 16.83 | -0.0163 | -0.0206 | -1.09 | -0.016 | -0.017 |
| 26c | 11.06 | -0.0490 | -0.0560 | -1.61 | -0.042 | -0.059 |
| 26d | 11.02 | -0.0299 | -0.0339 | -1.73 | -0.022 | -0.041 |
| 26e | 12.20 | -0.0317 | -0.0384 | -1.15 | -0.023 | -0.047 |
| 26f | 12.13 | -0.0184 | -0.0229 | -1.10 | -0.016 | -0.022 |
| 26g | 7.84 | -0.0447 | -0.0532 | -1.36 | -0.036 | -0.059 |
| 26h | 7.79 | -0.0329 | -0.0383 | -1.73 | -0.022 | -0.051 |

## Configurations
9 for this candidate (8 grid + 1 bias diagnostic), inside the round-3 budget of 101. Cumulative N after round 3 = 880
(t floor 3.68), unchanged.

## Known biases (all favour the candidate; it fails anyway)
Today's symbol list (survivorship, flatters longs), ETB flag as of today, borrow at a flat 1.2 / 3 bp (no hard-to-borrow
tiers). Bias diagnostic above: signal-close fill without borrow is still -0.039 on CHECK.

## Rule-change context (owner 2026-11-02)
Both halves are scored with one fixed rule set (today's LR8 costs, round-3 chassis). No live rule change applies. Live ledger
changes (11-12 LR8 cost model, 10-28 Primary sizing, 10-30 Testing cost filter, 11-17 TSZ1 / SPYEXIT, setup moves) are
not mixed into these figures.

## Remedy read (owner 2026-11-05)
The targeted remedy round 1 named for ULT-05 (a point-in-time trend-day layer) was tested here: 0 of 8 configs improve
ULT-05's check (-0.003). All 8 are worse by 0.013-0.046R, on both sides. Not worth a further variant on this
chassis. If the idea is revisited, the trend layer must be far more selective (it is true on about half of sessions), and the
entry should not be a VWAP pullback, which was the adverse part on CHECK.

## Files
`research/ultimate_1119/modules/ULT-26.py`, `modules/ULT-26_symbols.json`, `round3/ULT-26/{bt.py, test_module.py,
fit_grid.json, fitsel.json, fit_random.json, check_once.json, check_plateau.json, check_trades.csv.gz}`. Work parquet
files were deleted after scoring.

Educational only — not financial advice.
