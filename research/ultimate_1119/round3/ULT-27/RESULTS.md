Educational only — not financial advice

# ULT-27 PERIODICITY — round 3 result: **FAIL** (not check-informed)

Research only. No setup, exit, config or account change was made, and nothing was committed. Pre-registration: round3/PLAN.md sec. 3 "ULT-27".

## Verdict in one paragraph
The same-clock-half-hour persistence book (Heston, Korajczyk & Sadka 2010) delivered the volume it promised:
14-25 trades/session, long and short, on every tape. It has no tradable edge. **All 6 configs were negative on
FIT after costs** (avg R -0.018 to -0.024). Even before costs they were about zero (-0.001 to -0.007R per 2u). The
fit pick 27e (L 20, N 2) scored **-0.0171R on CHECK**: -0.0180 without its best day, total -79.1R (-0.29R/session),
day-clustered t -4.01. Every check config was negative (plateau, diagnostic only). The pick did worse than random
bars in the same names on check (signal minus random -0.011). The effect does exist cross-sectionally, but it is
tiny: the rank IC between P and the realised same-slot return on FIT is +0.006..+0.010 (t 1.4-2.2). That is roughly
+0.00R gross at the extremes, against about 0.017R of cost per trade. This matches the pre-registered honest prior
("a few bp, probably below cost"). Fit avg R < 0 rules out TIER A and TIER B. Nothing here is worth salvaging as a
setup. At most, P could serve as a weak tie-breaker feature, and even that is unproven.

## Build
- **Module:** `research/ultimate_1119/modules/ULT-27.py`. It is two-sided in one file, as ULT-25/26: a setup name
  ending "-S" is the short side. GEOM "S" uses a 2u catastrophic stop (`stop_price`), YAML `time_stop_min 30`,
  `context: [spy_fo]`, refire true with cooldown 0, window 1000-1500 and min_adv 200e6. The cross-sectional ranking
  cannot run inside a per-symbol live mask, so it is split in two:
  - **Pre-open:** `build_profile()` computes the scores and writes `ULT-27_profile.json` with the long/short list per
    slot. It uses `interval_returns`, `atr_pct`, `scores`, `preopen_ok` and `rank_lists`, the same functions the
    backtest calls for every session.
  - **In-day:** `mask()` checks that the symbol is listed at this slot and passes the in-day filters (`features`,
    `day_ok`). Live frames carry no symbol column, so the symbol comes from the runner's frame cache via
    `_infer_symbol`, as in ULT-21.
  - **Fail-safes:** no profile for today, an unknown symbol or no SPY context at the bar each give no signal.
- **Faithful-build notes**, both live-feasibility choices made before any scoring:
  - (a) Names are replaced by the next-ranked one only on pre-open filters: LEV list, ADV20 >= $200M, previous close
    >= $10, cost_r (previous close, atr_d, slot) <= 0.05, ETB for shorts, and the max-2-listings-per-symbol-session
    cap. A name that then fails an in-day filter is dropped, not replaced, because a per-symbol live module cannot see
    other names' in-day state:
    - longs: the universal long filter;
    - shorts: gap >= +0.5% or RSI5 < 25;
    - both: close < $10 or cost_r at the bar > 0.05.
    So 28-30% of listed rows did not trade, and trades/session are 14-25 instead of the planned 24/36. Volume is still
    far above the 2/session bar.
  - (b) The max-2-per-symbol-session chassis rule is applied at listing time (skip and replace), which keeps it
    deterministic live.
- **Point-in-time inputs:**
  - x = (C[t+29] / C[t-1] - 1) x 100 / ATR%_d.
  - ATR%_d = mean true range of the 14 prior sessions (min 5) / previous close, from daily bars computed per
    contiguous segment.
  - P = mean of x over the previous L sessions, needing >= ceil(0.7 L) valid days.
  - The locked block sits in the session sequence as 82 empty sessions, so no look-back reaches into it. 2024-10
    look-backs use 2024-09-16..09-30. The first 2025-03 sessions have too few valid days and give no signal.
- **Smoke test:** `round3/ULT-27/test_module.py`, 4 passed. It checks:
  - the profile from synthetic 1-min history lists the persistent up name long and the down name short;
  - a LEV fund is never listed, and the listing cap holds;
  - both sides run under the live LabStrategy, firing at the 10:00 decision bar with a 2u stop;
  - no SPY context or no profile gives no signal, and an unlisted name does not fire at the slot;
  - truncation: P never uses today's own interval or any later row, and features / filters are unchanged by
    truncation;
  - filter logic.
- **Backtest:** `round3/ULT-27/bt.py`, on the round-2/3 chassis:
  - Entry is the open of the next 1-min bar (LR8 entry cost). TX-30 exits at the close of minute entry+29, with a
    2u stop walked on 1-min bars and +2c on stops. R is per 2u, and r_u is per 0.25-dATR unit.
  - Shorts pay borrow (1.2 bp of entry notional, 3 bp under $20) and must be easy to borrow (today's flag).
  - Day cap 36, which never binds.
  - Forbidden frame columns are never loaded (asserted). Every load asserts the locked block is absent.
  - Stats, sub-halves and SPY day types are imported unchanged from ULT-23/bt.py.

## Configurations
| Item | count |
|---|---|
| Grid (6 configs) | 6 |
| Bias diagnostic | 1 |
| **Total counted** | **7** |

All 7 are inside round 3's pre-registered 101. Cumulative N = **880**, and the t bar is sqrt(2 ln 880) = **3.68**.

Reported but not counted, and neither decides anything:
- the random control;
- 3 rank-IC diagnostics, run after the fit freeze. If they were counted, N = 883 and the bar is unchanged at 3.68.

## FIT grid (170 sessions; R per 2u = actual risk; all costs and borrow in)
| cfg | label | tr/sess | avg R | gross avg R | w/o best day | total R | total − best day | A / B | long / short avg R | ex 04-03..04-09 | t (day-clust.) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 27a | L5-N2 | 16.17 | -0.0204 | -0.0031 | -0.0217 | -56.2 | -59.1 | -0.019 / -0.022 | -0.016 / -0.028 | -0.0201 | -3.79 |
| 27b | L5-N3 | 24.16 | -0.0197 | -0.0024 | -0.0206 | -81.0 | -84.0 | -0.016 / -0.024 | -0.016 / -0.026 | -0.0196 | -4.42 |
| 27c | L10-N2 | 15.77 | -0.0187 | -0.0018 | -0.0198 | -50.1 | -52.7 | -0.016 / -0.022 | -0.017 / -0.022 | -0.0207 | -3.47 |
| 27d | L10-N3 | 23.55 | -0.0236 | -0.0065 | -0.0248 | -94.4 | -98.8 | -0.024 / -0.023 | -0.020 / -0.029 | -0.0247 | -4.92 |
| **27e** | **L20-N2** | 14.24 | **-0.0177** | -0.0009 | -0.0197 | -42.9 | **-47.2** | -0.006 / -0.026 | -0.013 / -0.026 | -0.0199 | -3.23 |
| 27f | L20-N3 | 21.32 | -0.0181 | -0.0012 | -0.0196 | -65.5 | -70.4 | -0.013 / -0.022 | -0.013 / -0.026 | -0.0195 | -3.69 |

- All 6 configs reach >= 2/session.
- The pick by the pre-registered rule (max fit total R minus best fit day) is **27e**. The plain "fit total R" rule
  named in the task also picks 27e.
- 27e was frozen in `fitsel.json` at **2026-11-19T08:25:03Z**, before any check x, frame or trade was built. The file
  holds the sha256 of bt.py, the module and the LEV list.
- Fit pick detail:
  - Best fit day is 2025-04-04 (inside the tariff week). Best-day share is n/a because total R < 0.
  - Worst day -3.06R, which is -0.18 per trade-session.
  - SPY up / flat / down: -0.016 / -0.023 / -0.011.
  - By slot (gross): 10:00 -0.022, 11:00 -0.010, 12:00 +0.008, 13:00 +0.002, 14:00 +0.008, 15:00 +0.008. After
    costs every slot is negative.
  - Exit mix: 2,399 time exits and 21 stops. Median hold 30 min.

## CHECK — fit pick 27e scored once (276 sessions, 2025-10-01..2026-11-04)
| metric | value |
|---|---|
| trades / per session | 4,636 / **16.80** (long 10.59, short 6.20) |
| win rate | 0.475 |
| avg R after costs (per 2u) | **-0.0171** (per 0.25-dATR unit -0.0341) |
| gross avg R (no costs, no borrow) | -0.0008 |
| avg R w/o best day | **-0.0180** (best day 2025-10-01; best-day share n/a, total < 0) |
| total R / per session | -79.1 / -0.287 |
| worst day / per trade-session | -4.78 / -0.284 |
| day-clustered t | **-4.01** (bar 3.68) |
| long / short avg R | -0.0171 (t -2.90) / -0.0170 (t -2.71) |
| SPY up / flat / down | -0.002 / -0.016 / -0.039 |
| first / second half | -0.0158 / -0.0183 |
| without 2025-04-03..04-09 | no such dates in CHECK: -0.0171 |
| by slot | 10:00 -0.030, 11:00 -0.020, 12:00 -0.022, 13:00 -0.020, 14:00 -0.001, 15:00 -0.011 |
| exit mix / median hold | 4,593 time, 43 stop / 30 min |

**Bars:** check avg R <= 0, w/o best day <= 0 and fit avg R <= 0, so the result is **FAIL**: not TIER A, and not
TIER B (TIER B needs fit > 0). It also fails every BEATS condition: t is -4.01, and avg R is below +0.0836.

Check plateau (diagnostic, never used to re-select): all six configs are negative.

| cfg | label | avg R | t (day-clustered) |
|---|---|---|---|
| 27a | L5-N2 | -0.021 | -4.64 |
| 27b | L5-N3 | -0.017 | -4.37 |
| 27c | L10-N2 | -0.015 | -3.37 |
| 27d | L10-N3 | -0.015 | -4.08 |
| 27e | L20-N2 | -0.017 | -4.01 |
| 27f | L20-N3 | -0.014 | -3.79 |

Gross is -0.004 to +0.002 everywhere. `check_plateau.json` has the full numbers.

## Controls and diagnostics
- **Random control** (same symbol-session and side, a random 5-min bar 10:00-15:00, same TX-30 exit):

  | | random avg R | signal minus random | long | short |
  |---|---|---|---|---|
  | FIT | -0.0173 | +0.0018 | +0.005 | -0.004 |
  | CHECK | -0.0060 | **-0.0111** | -0.012 | -0.010 |

  Choosing the clock slot by past same-slot returns adds nothing over a random time in the same names.
- **Bias diagnostic** (fill at the signal close, no borrow fee):

  | | signal close, no borrow | with next-minute fill and borrow |
  |---|---|---|
  | FIT avg R | -0.0147 | -0.0177 |
  | CHECK avg R | -0.0139 | -0.0171 |

  The negative result does not come from the fill or borrow modelling.
- **Rank IC** (FIT, all non-LEV names, P vs the realised same-slot x, per date-slot Spearman):

  | L | mean IC | t |
  |---|---|---|
  | 5 | +0.009 | 2.2 |
  | 10 | +0.006 | 1.4 |
  | 20 | +0.010 | 2.2 |

  The HKS persistence is faintly present, but it is far too small to pay a ~0.017R round trip on a 30-min hold.
- **Known biases** all favour the candidate and do not change the verdict: today's symbol list (survivorship) and
  today's ETB flag.

## Rule-change context (owner 2026-11-02)
Both 2-year halves are scored with one fixed rule set (today's LR8 costs, round-2/3 chassis). No live rule change
falls inside them.

## Files
- `research/ultimate_1119/modules/ULT-27.py`
- `round3/ULT-27/bt.py`
- `round3/ULT-27/test_module.py`
- `round3/ULT-27/fit_grid.json`
- `round3/ULT-27/fitsel.json`
- `round3/ULT-27/fit_random.json`
- `round3/ULT-27/check_once.json`
- `round3/ULT-27/check_plateau.json`
- `round3/ULT-27/check_trades.csv.gz`

Intermediate x / signal / walk parquet files were in the scratchpad and have been deleted. They can be rebuilt with
`python bt.py WORK x|sig|walk fit|check`.

Educational only — not financial advice.
