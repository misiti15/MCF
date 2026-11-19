Educational only — not financial advice

# ULT-22 WB4-WIDE — WB4's trigger, more hours, ATR-scaled twin, basket ETFs only, LONG (round 3) — CHECK-INFORMED

**Tier: B (near miss, never deployed). Not TIER A, not BEATS.** The fit pick **22b** (WB4 ETF list, WB4's exact %
trigger, window 12:30-15:00) scored **+0.0035R/trade on check** (w/o best day **-0.0027**, best-day share 1.77 =
**1-day tag**, t = 0.11, 2.27 trades/session, total +2.2R over 276 sessions, worst day -14.0R = -4.87 per
trade-session). Fit was +0.104 (w/o best day +0.088, t 2.63, 2.44/session). Fit > 0 and check > -0.02 make it TIER B.
Configurations tried: 12 grid + 1 bias diagnostic = 13 (already inside the pre-registered cumulative N = 880; t bar 3.68).

## In plain words
- Goal of this build: keep the one edge that held out of sample (WB4's sharp 15-min dip on index/sector ETFs, 14:00-15:00)
  and lift it above 2 trades/session by opening earlier hours, adding an ATR-scaled twin, and a wider basket list.
- **Opening earlier hours is what kills it.** Inside the pick, the 14:00-15:00 trades still earn **+0.096R on check**
  (203 trades), but the new 12:30-13:55 trades lose **-0.041R** (424 trades). On fit the earlier hour was already much
  weaker (+0.038 vs +0.180). The extra volume comes from a part of the day where the dip does not revert.
- **The ATR-scaled trigger A adds no volume** on this list: WB4's ETFs are mostly 2-3x funds with ATR far above 3.6%,
  where -0.21 x ATR% is a *deeper* drop than -0.75%. A trades 0.55-1.3/session on fit vs 1.4-3.9 for P, and its
  1030 window is -0.088 on check.
- **EQB adds nothing on fit** (Q rows = W rows exactly): the extra equity-basket ETFs (EEM, EFA, EWZ, FXI, KWEB, ...)
  are unlevered with daily ATR 1-2%, below both ATR floors. The two fit rows they did produce (VT on 2025-04-10) were
  cut by the day cap of 30. On check Q adds a little and is slightly worse than W.
- The anchor 22a (exact WB4: list, %, 14:00-15:00) reproduces round 2 exactly: fit +0.219 / check +0.110, w/o best day
  +0.096, t 2.87, but **0.82 trades/session** — still not eligible, and still the real edge.
- Random entries on the same ETF-sessions and window: fit +0.053 (signal +0.051 better), check -0.016 (signal +0.020
  better). The trigger still beats random a little, but the pick as a whole is about zero after costs on check.
- Fit itself was regime-heavy: 358 of 414 fit trades are in sub-half A (2024-10, 2025-03..05: high-volatility months);
  sub-half B (2025-06..09) had 56 trades at +0.014. Without 2025-04-03..04-09 fit avg R drops from +0.104 to +0.069.

## Build (faithful to round3/PLAN.md sec. 3 "ULT-22")
- Live module `research/ultimate_1119/modules/ULT-22.py` + `ULT-22_symbols.json` (W = exact WB4 list 124 names,
  Q = EQB 167 names, copied verbatim from `modules/ULT-21_universe.json`, the round-3 universe frozen before any fit
  scoring; source sha256 recorded in the json). `features()` / `trigger()` call
  `mcf.research.arena.indicators.compute` (as WB4 / ULT-12); bt.py imports them (one code path backtest/live).
  Pick constants set (UNIV W, TRIG P, WINDOW 1230-1500) before freezing fitsel.json; the module sha at freeze is recorded.
- Smoke test `round3/ULT-22/test_module.py` (3 passed): fires under the live LabStrategy (`context: [spy_fo]`,
  `symbols: module`, min_adv 95M, geom t05s1), gives t05s1 levels, rejects a stock, applies the universal SPY long
  filter, fails safe without SPY context, features unchanged when later bars are removed (no look-ahead), and the
  P/A triggers with their ATR floors (3.6 / 2.4) and cost caps (0.10 / 0.08) behave as specified.
- Backtest `round3/ULT-22/bt.py` = round2/ULT-12/bt.py chassis with the ULT-22 superset (EQB, ADV20 >= $95M, 10:30-15:00,
  P or A) and the 12 sub-filter configs. Entry = OPEN of the 1-minute bar at the decision close (LR8 entry cost);
  t05s1 around the decision close, u = 0.25 x atr_d; 1-minute walk, stop first, gap-through, +2c stops, target no exit
  cost; 45-min cap, flat 15:50. One lot per symbol, refire >= 30 min after exit, max 2/symbol-session, day cap 30.
  Long only: no borrow fee needed. Forbidden frame columns dropped before features. Locked block never read
  (pyarrow filters, `no_locked()` asserts, MCF_HIST_ALLOW_LOCKED refused).
- Build notes: the live module's refire (2nd hit >= 6 bars after the 1st) is looser than the backtest's exit-based
  chain (as ULT-12). The day cap of 30 binds on fit (April 2025: 22b capped 414 vs uncapped 511 trades, uncapped fit avg
  +0.154); it never binds on check.

## Selection (FIT only) — every configuration
Rule (PLAN sec. 5): max fit total R minus the best fit day, among configs with >= 2.0 trades/session. Eligible: 22b, 22c,
22h, 22i (22h = 22b and 22i = 22c on fit; tie -> first listed). Pick **22b**. fitsel.json frozen 2026-11-19T07:49:52Z,
before any check frame was built.

| cfg | univ-trig-window | FIT /sess | avg R | w/o best | best share | total | total w/o best | t | ex 04-03..09 | A / B | CHECK plateau (after the single score): /sess, avg R, w/o best, t |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 22a | W-P-1400 (anchor) | 1.41 | +0.219 | +0.178 | 0.29 | 52.3 | 37.2 | 4.14 | +0.196 | +0.249 / -0.041 | 0.82, +0.110, +0.096, 2.87 |
| **22b** | **W-P-1230** | **2.44** | **+0.104** | **+0.088** | 0.20 | 43.2 | **34.5** | 2.63 | +0.069 | +0.119 / +0.014 | **2.27, +0.004, -0.003, 0.11** |
| 22c | W-P-1030 | 3.93 | +0.029 | +0.011 | 0.64 1 day | 19.2 | 6.8 | 0.78 | +0.003 | +0.040 / -0.039 | 4.81, -0.002, -0.005, -0.07 |
| 22d | W-A-1400 | 0.55 | +0.180 | +0.126 | 0.44 | 17.0 | 9.6 | 1.88 | +0.113 | +0.240 / -0.463 | 0.11, +0.201, +0.153, 1.86 |
| 22e | W-A-1230 | 0.84 | +0.118 | +0.053 | 0.63 1 day | 16.8 | 6.2 | 1.20 | +0.076 | +0.156 / -0.162 | 0.31, +0.005, -0.029, 0.03 |
| 22f | W-A-1030 | 1.28 | +0.089 | +0.053 | 0.49 | 19.4 | 9.8 | 1.53 | +0.001 | +0.156 / -0.224 | 0.78, -0.088, -0.108, -1.12 |
| 22g | Q-P-1400 | = 22a | | | | | | | | | 1.00, +0.082, +0.063, 2.15 |
| 22h | Q-P-1230 | = 22b | | | | | | | | | 2.74, -0.007, -0.015, -0.24 |
| 22i | Q-P-1030 | = 22c | | | | | | | | | 5.73, +0.002, -0.001, 0.09 |
| 22j | Q-A-1400 | = 22d | | | | | | | | | 0.12, +0.133, +0.066, 1.00 |
| 22k | Q-A-1230 | = 22e | | | | | | | | | 0.33, -0.040, -0.075, -0.30 |
| 22l | Q-A-1030 | = 22f | | | | | | | | | 0.84, -0.107, -0.130, -1.29 |

Plateau: every config with >= 2/session is about zero on check (-0.007..+0.004, |t| <= 0.24). Only the 14:00-15:00
rows are positive on check, all at <= 1.0/session. No config would have passed TIER A on check.

## The fit pick 22b, fit vs check (R per u = 0.25 dATR = actual risk)

| | FIT (170 sess) | CHECK (276 sess) |
|---|---|---|
| trades (/session) | 414 (2.44), 93 sessions traded | 627 (2.27), 218 sessions traded |
| win | 0.647 | 0.536 |
| avg R | +0.104 | **+0.0035** |
| avg R w/o best day | +0.088 | **-0.0027** |
| best day (R, share) | 2025-04-07 (+8.7, 0.20) | 2026-07-29 (+3.9, 1.77 — 1 day) |
| total R / per session | +43.2 / +0.254 | +2.2 / +0.008 |
| worst day / per trade-session | -5.24 / -1.18 | **-14.01 (2025-11-20) / -4.87** |
| day-clustered t | 2.63 | 0.11 (bar 3.68) |
| avg R without 2025-04-03..04-09 | +0.069 (319 trades) | n/a (no such dates) +0.0035 |
| SPY up / flat / down | +0.153 / +0.039 / +0.083 | +0.014 / -0.016 / +0.014 |
| first / second half | +0.130 / +0.037 | -0.001 / +0.008 |
| fit sub-halves A / B | +0.119 (358) / +0.014 (56) | |
| 12:30-13:55 vs 14:00-15:00 entries | +0.038 (221) / +0.180 (193) | **-0.041 (424) / +0.096 (203)** |
| median hold, exit mix | 32 min; 199 target / 37 stop / 178 time | 45 min; 207 target / 48 stop / 372 time |
| same-name random (signal - random) | +0.053 (+0.051) | -0.016 (+0.020) |
| bias diag: fill at signal close | +0.105 | +0.003 |
| largest names on check | SOXS 150 trades +5.0R, GDXU 124 -1.5R, SOXL 106 -6.6R, TECL 46 +2.3R; SQQQ 34 -5.0R | |

## Bars
- TIER A: check avg R > 0 (+0.0035 yes), w/o best day > 0 (**-0.0027 no**), fit > 0 (yes), >= 2/session (2.27 yes),
  no look-ahead (yes) -> **not TIER A**.
- BEATS: fails avg R (> 0.0836), w/o best (> 0.0734), worst day/trade-session (-4.87 < -2.152), t (0.11 < 3.68).
- TIER B (fit > 0 and check > -0.02): **yes -> B, never deployed.**

## What this teaches / next step
- WB4's edge is specific to the last hour (14:00-15:00). Widening time does not scale it; it dilutes it to zero.
  The ATR-scaled twin and the EQB list do not raise volume on the high-ATR names that carry the trigger.
- Volume for this edge will not come from WB4's own trigger on more hours or the same basket list. Possible salvage
  (backlog, not tested here): keep 14:00-15:00 and find *other* last-hour basket triggers, or combine the anchor with
  other independent last-hour setups as a book; the anchor alone stays a Testing-scale (0.8/session) setup, already live
  as WB4 (Testing E since 2026-11-17, after the CHECK window).

## Caveats and rule-change context
- CHECK-INFORMED (round3/PLAN.md sec. 0.5 i + WB4 parameters): even a pass would have needed a forward look.
- Survivorship (today's symbol list) flatters longs; signal-minus-random is the neutral read. No borrow fee needed (long).
- One fixed rule set over both halves (today's LR8 costs, round-3 chassis); no live rule change falls inside them.
  WB4 went live 2026-11-17, after CHECK ends (2026-11-04).

## Files
`modules/ULT-22.py`, `modules/ULT-22_symbols.json`, `round3/ULT-22/{bt.py, test_module.py, fit_grid.json,
fitsel.json, fit_random.json, check_once.json, check_plateau.json, check_trades.csv.gz}`.

Educational only — not financial advice.
