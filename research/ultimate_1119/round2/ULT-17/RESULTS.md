Educational only — not financial advice

# ULT-17 SECTOR-LAG: sector-ETF lead-lag catch-up, LONG + SHORT (round 2)

**Tier: FAIL. Not BEATS, not TIER A, not TIER B.** All 8 configurations lose on FIT after costs (-0.011 to -0.032R per
trade), so TIER A and TIER B are out of reach (both need fit avg R > 0). The fit pick **17g** (sector move >= 0.25 x sector
daily ATR%, lag >= 0.20 x name daily ATR%, TX30) was scored once on CHECK:
- **-0.0096R per trade**, and -0.0125 without its best day;
- 18.3 trades per session, -48.4R over 276 sessions;
- day-clustered t -1.02, against a bar of 3.65.

The volume is there. The edge is not: the catch-up is too small to pay the round-trip cost.

## In plain words
- **The rule:** each name gets the sector ETF it tracked best over the prior 60 sessions. When that ETF makes a sharp
  15-minute move and the name has not followed, trade the name in the sector's direction. Exit on a 30- or 45-minute
  time stop.
- **It trades a lot:** 12-27 per session on fit, 18-30 per session on check. The 30/day cap binds for the loose settings.
- **The catch-up is real but tiny.**
  - Against random entries in the same names, sessions and sides, the signal is +0.029R better on fit and +0.012R better
    on check.
  - Random entries in this universe lose -0.046R (fit) and -0.023R (check), mostly to costs.
  - So the trigger only shrinks the loss. This is round 1's lesson again: a weak trigger on a base that loses to costs.
- **Most of the lag closes within one minute.** With the old signal-close fill and no borrow fee (bias diagnostic), the
  pick would show +0.0048 on check and +0.0002 on fit. The next-minute-open entry and the borrow fee cost about 0.015R
  per trade, which is about the whole edge.
- **Neither side carries it.**
  - Fit: the long side is -0.045 and the short side is +0.016. The short side's best day is 63% of its total ("1 day"
    tag), and its first half is -0.021.
  - Check: the sides flip. The long side is -0.002 and the short side is -0.019.
  - There is no stable side, and no stable tape either. SPY up/flat/down days (end-of-day label) give fit -0.034 /
    -0.020 / +0.004 and check +0.019 / -0.022 / -0.025.
- **Plateau (check, diagnostic only, never used to pick):** all 8 configs are between -0.017 and -0.002. The best is 17h
  (TX45 twin of the pick) at -0.0018, t -0.16. The long side of 17h is +0.011, but the long side was -0.048 on fit.
  Nothing here is near TIER A, let alone the +0.0836 bar.

## Build (faithful to round2/PLAN.md sec. 3 "ULT-17")
- **Live module** `research/ultimate_1119/modules/ULT-17.py`.
  - It exposes `SIDE`, `GEOM "S"`, `stop_price` (2u catastrophic stop), `LAYERS`, `SYMBOLS`, `features()`,
    `trigger(r, sgn, s, lmin)` and `mask()`. bt.py imports `features()` / `trigger()`, so live and backtest share one
    code path.
  - Constants are set to the fit pick 17g: S 0.25, LMIN 0.20, H 30. They were set 11 s after fitsel.json was frozen and
    before any check data was built. fitsel.json records the sha256 of the module both at the freeze and with the pick
    constants.
  - Two sides, one file. A setup name ending in "-S" / "-short" is the short side.
  - YAML it would need (NOT written anywhere): two `type: lab` entries with `module: research/ultimate_1119/modules/ULT-17.py`,
    `symbols: module`, `min_adv: 50000000`, `window: [1015, 1500]`, `context: [spy_fo]`, `refire: true`,
    `refire_cooldown: 0`, `geom: S`, `time_stop_min: 30`, `time_stop_min_r: 99`. The short side also needs the account's
    ETB rule.
- **Live gap:** the live lab frame has no `sec_fo` / `sec_atrp` / `sec_beta` columns. It would need a runner extension: a
  per-name sector map refreshed daily from prior sessions, plus the sector ETF's fromOpen per bar, built like
  lab_context's spy_fo. Without that extension the module fires nothing (fail safe, tested). ULT-11 has the same gap.
  It is moot, because the candidate fails.
- **Smoke test** `round2/ULT-17/test_module.py` (8 passed). It checks that:
  - the module fails safe without the sector columns under the live LabStrategy;
  - with the sector columns injected (a simulated runner extension), it fires long when the sector jumps and the name
    lags, and short on the mirror, at 13:25-13:40;
  - it gives a 2u stop and no target;
  - the other side does not fire, and a name that already followed does not fire;
  - the universal long filter (SPY -0.30..-0.75% from its open and falling) blocks the long;
  - ETFs are excluded;
  - features do not change when later bars are removed (point-in-time).
- **Data and chassis:**
  - **Frames:** lab frames plus spy_fo context. Forbidden columns (win_*, r_long/r_short*, *heat*) are dropped and
    asserted absent before features are computed.
  - **Sector columns:** `sec_fo` is the sector ETF frame fromOpen at the same date/tod. `sec_atrp` is 100 x ETF atr_d /
    ETF close at the bar.
  - **Sector map:** ULT-11's `sector_map()`, imported unchanged (argmax corr over the prior <= 60 non-locked sessions,
    min 20, beta clipped [0.3, 3]). The FIT map uses daily rows <= 2025-09-30 only. The CHECK map was built only after
    the freeze.
  - **Sector coverage:** ~99% of eligible bars, except 2024-10 at 56%, because fewer than 20 prior daily sessions were
    available early in the month.
  - **Universe:** stocks only (the frozen ULT-12 "S" list), ADV20 >= $50M, U2 intake with cost_r <= 0.08, universal
    filters, shorts ETB only. 62 fit / 233 check short bars were dropped as non-ETB.
  - **Entry and exit:** entry at the next 1-minute open. The catastrophic 2u stop is set from the entry. The time exit is
    at entry + h - 1 minutes (flat 15:50). R is per 2u.
  - **Costs:** LR8 costs, plus 1.2 bp borrow on shorts.
  - **Position rules:** one lot per symbol across sides, refire >= 30 min after the exit, max 2 per symbol-session, day
    cap 30 (first by time, ties ADV20 desc).
- **Locked block 2024-11-01..2025-02-28:** never read. pyarrow filters are on the 1-minute and daily loads, and
  `no_locked()` asserts on every frame, sector map, signal, day list and 1-minute load. MCF_HIST_ALLOW_LOCKED is refused.

## FIT grid (2024-10 + 2025-03..09, 170 sessions; selection = fit total R minus best day among >= 2/session)
| cfg | label | tr/sess | avg R | w/o best day | total R | total w/o best | sub-half A | sub-half B | long avg (n) | short avg (n) |
|---|---|---|---|---|---|---|---|---|---|---|
| 17a | S0.15-L0.10-TX30 | 27.4 | -0.0279 | -0.0307 | -130.0 | -141.8 | -0.035 | -0.022 | -0.045 (2698) | -0.004 (1953) |
| 17b | S0.15-L0.10-TX45 | 27.4 | -0.0202 | -0.0239 | -93.8 | -110.5 | -0.031 | -0.011 | -0.041 (2698) | +0.009 (1953) |
| 17c | S0.15-L0.20-TX30 | 23.6 | -0.0322 | -0.0353 | -128.9 | -140.5 | -0.047 | -0.023 | -0.051 | -0.009 |
| 17d | S0.15-L0.20-TX45 | 23.6 | -0.0325 | -0.0354 | -130.4 | -140.7 | -0.042 | -0.026 | -0.053 | -0.008 |
| 17e | S0.25-L0.10-TX30 | 20.4 | -0.0226 | -0.0255 | -78.2 | -87.5 | -0.041 | -0.011 | -0.033 | -0.010 |
| 17f | S0.25-L0.10-TX45 | 20.4 | -0.0109 | -0.0155 | -37.9 | -53.1 | -0.027 | -0.001 | -0.037 | +0.021 |
| **17g** | **S0.25-L0.20-TX30** | **12.5** | **-0.0169** | **-0.0219** | **-36.1** | **-46.1** | -0.046 | -0.000 | -0.045 (1150) | +0.016 (981) |
| 17h | S0.25-L0.20-TX45 | 12.5 | -0.0187 | -0.0256 | -39.8 | -53.7 | -0.053 | +0.001 | -0.048 | +0.016 |

Fit pick 17g in detail:
- **Basics:** 2,131 trades, win 49.1%, avg R -0.0169 (-0.034 in 0.25-dATR units), median hold 30 min.
- **Best day:** 2025-04-04 (share n/a, total negative).
- **Worst day:** -31.5 (2025-04), -2.05 per trade-session.
- **Day-clustered t:** -0.85.
- **Without 2025-04-03..04-09:** -0.0091.
- **Uncapped:** 23.3/session, -0.042.
- **Random control:** -0.046 (signal minus random +0.029; long -0.008, short +0.074).
- **Bias diagnostic** (signal-close fill, no borrow): +0.0002.

## CHECK (2025-10-01..2026-11-04, 276 sessions), scored ONCE on 17g
| metric | value |
|---|---|
| trades / per session | 5,047 / 18.29 (263 sessions traded) |
| win | 49.1% |
| avg R (actual risk, per 2u) / in 0.25-dATR units | **-0.0096** / -0.0192 |
| avg R w/o best day (2026-02-12, +14.2R) | **-0.0125** |
| best-day share | n/a (total negative) |
| total R / per session | -48.36 / -0.175 |
| worst day / per trade-session | -11.36 (2026-01-14) / -0.592 |
| day-clustered t (bar 3.65 at N = 774) | **-1.02** |
| without 2025-04-03..04-09 | -0.0096 (no such dates in check) |
| first / second half | -0.0081 / -0.0111 |
| SPY up / flat / down (EOD label, reporting only) | +0.019 / -0.022 / -0.025 |
| long (2,797) / short (2,250) | -0.0023 (t -0.17) / -0.0186 (t -1.26) |
| exit mix | time 4,912, stop 135 |
| uncapped | 25.7/session, -0.0105, t -1.27 |
| random control (same names/sessions/sides, random 10:15-15:00 bar) | -0.0226; signal minus random +0.012 (long +0.019, short +0.004) |
| bias diagnostic (signal-close fill, no borrow) | +0.0048 |
| sectors | all 22 used; top XLF 520, XLI 468, IWM 378, XLV 370, SMH 340, ARKK 330 |

Bars:
- **TIER A** fails on: check avg R <= 0, w/o best day <= 0, and fit avg R <= 0. Volume (>= 2/session) passes.
- **BEATS** also fails on avg R vs +0.0836, w/o best day vs +0.0734, R/session > 0, and t vs 3.65. The worst-day test
  passes: -0.59 vs -2.152.

## Configurations counted
9 for this candidate: 8 grid + 1 bias diagnostic, as pre-registered in PLAN sec. 4. The random controls are reported,
not counted. Cumulative N for the job stays at 774 as pre-registered for round 2. No amendments.

## Caveats
- **Survivorship:** today's symbol list flatters longs. The signal-minus-random figure is the survivorship-neutral read.
- **ETB flag:** it is today's flag, not point-in-time.
- **Borrow fee:** the 1.2 bp fee is an estimate.
- **Sector map:** it is noisy by construction (the pre-registered argmax-correlation rule maps e.g. INTU to XLF on some
  dates). A curated sector map is a possible next step, but it is not pre-registered and would be a new configuration.
  The small, unstable signal-minus-random edge (+0.01..+0.03) gives little reason to expect it to clear costs.
- **Rule-change context:** none. Both halves are scored with one fixed rule set. No live ledger change applies to this
  2-year replay.

## Files
- `research/ultimate_1119/modules/ULT-17.py`
- `research/ultimate_1119/round2/ULT-17/{bt.py, test_module.py, fitsel.json, fit_grid.json, fit_random.json,
  check_once.json, check_random.json, check_plateau.json}`
- The work dir (signals, walked trades) was deleted after scoring.

Educational only — not financial advice.
