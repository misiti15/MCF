Educational only — not financial advice

# ULT-18 XS-MOMREV — cross-sectional momentum / reversal at fixed times, LONG + SHORT (round 2)

**Tier: FAIL. Not TIER A, not B, not BEATS.** All 8 configurations lose on FIT after costs (-0.021 to -0.028R per
trade), so TIER A and TIER B were already out of reach (both need fit avg R > 0). The fit pick **18e** (K2
sector-relative fromOpen, MOM, N 5, TX45) was scored once on CHECK: **-0.0205R per trade**, -0.0213 without its best day.
It traded **28.5 times per session** on all 276 sessions, for a total of -161.8R (-0.59R per session). The day-clustered
t is **-4.63**, against a bar of +3.65. **The volume is there; there is no edge.**

## In plain words
- At 11:00, 13:00 and 14:00 we ranked every liquid stock (non-ETF, ADV >= $200M, price >= $10, cost_r <= 0.06) by how
  far it had moved from its open. We then bought one end of the ranking and shorted the other, holding each trade
  45 minutes.
- **Momentum (buy the leaders, short the laggards) and reversal (the opposite) lose the same amount.** On fit, every
  config sits at -0.021 to -0.028R; on check, -0.018 to -0.024R. If distance from the open predicted the next 45 minutes
  in either direction, one of them would win and the other would lose. Here both lose by about the cost.
- **Before costs the pick is flat:** gross -0.004R on fit and -0.001R on check (R per 2u = actual risk). The round-trip
  cost is about 0.020R per trade (0.04 per 0.25-dATR unit), and that is the whole loss.
- **The ranking adds nothing over random names at the same moment.** Random eligible names at the same date, time and
  side earn -0.023 (fit) and -0.019 (check). The signal minus random is -0.002 on fit and -0.001 on check.
- **Nothing here is carried by one day.** Check best day +5.2R (2026-02-03); the total is negative, so the best-day share
  is n/a. Worst day -7.2R (2026-04-17), = -0.25 per trade-session. The loss is steady: first and second half of check
  are -0.020 and -0.021, and fit sub-halves A and B are -0.030 and -0.020.
- The evidence behind the idea does not carry over. WAVE1's "fromOpen persistence 0.39" is the sign-stability of a
  feature between halves, not a 45-minute return edge. EODREV1's +0.031 reversal was at 15:30 on a different universe.
  At these three times in liquid names, the 45-minute continuation or reversal is about zero before costs.

## Results (fit pick 18e K2-MOM-N5-TX45; R per actual risk = 2u, u = 0.25 x daily ATR; LR8 costs + 1.2 bp borrow on shorts)

| | FIT (170 sessions) | CHECK (276 sessions, scored once) |
|---|---|---|
| trades (/session) | 4,543 (26.7) | 7,878 (28.5) |
| sessions traded | 160 (the first 10 sessions of 2024-10 have no sector map yet, so K2 has no rank) | 276 |
| win rate | 0.471 | 0.466 |
| **avg R** (0.25-dATR units) | **-0.0250** (-0.050) | **-0.0205** (-0.041) |
| **avg R w/o best day** | -0.0270 | **-0.0213** |
| best day (R, share) | 2025-07-01 +8.3 (n/a, total < 0) | 2026-02-03 +5.2 (n/a, total < 0) |
| total R / per session | -113.5 / -0.668 | -161.8 / -0.586 |
| worst day / per trade-session | -5.2 (2025-09-30) / -0.184 | -7.2 (2026-04-17) / -0.251 |
| day-clustered t | -4.61 | **-4.63** (bar 3.65) |
| avg R without 2025-04-03..04-09 | -0.0229 | -0.0205 (window not in check) |
| first / second half (fit: sub-halves A / B) | -0.030 / -0.020 | -0.020 / -0.021 |
| SPY up / flat / down (end-of-day label, reporting only) | -0.029 / -0.017 / -0.029 | -0.023 / -0.023 / -0.014 |
| long side: n, avg R, t | 2,177, -0.017, -1.65 | 3,749, -0.017, -2.04 |
| short side: n, avg R, t | 2,366, -0.033, -3.33 | 4,129, -0.024, -3.25 |
| long SPY up / flat / down | +0.010 / -0.011 / -0.069 | +0.023 / -0.023 / -0.063 |
| short SPY up / flat / down | -0.069 / -0.023 / +0.001 | -0.067 / -0.023 / +0.024 |
| gross avg R (before costs) / cost per trade | -0.004 / 0.021 | -0.001 / 0.020 |
| by time 11:00 / 13:00 / 14:00 | -0.025 / -0.019 / -0.031 | -0.020 / -0.019 / -0.023 |
| exits | 4,429 time, 114 stop | 7,725 time, 153 stop |
| median hold | 45 min | 45 min |
| no 1-min path (dropped) | 28 | 15 |
| **same-moment random names** (signal minus random) | -0.023 (-0.002); long -0.006 (-0.011), short -0.039 (+0.006) | -0.019 (-0.001); long -0.023 (+0.006), short -0.016 (-0.008) |
| bias diagnostic: signal-close fill, no borrow | -0.022 | -0.017 |

The side split by SPY day type is the usual tape exposure (longs win on up days, shorts on down days). That is an
end-of-day label, so it cannot be traded and it is not evidence.

**Bars:** TIER A fails because fit avg R is < 0, check avg R is < 0, and check w/o best day is < 0. Volume
(28.5/session >= 2) and no look-ahead pass. TIER B fails (fit avg R < 0). BEATS fails on every term except worst day
(-0.25 >= -2.152).

### Plateau (all 8 configs on check, after the single check score; never used to re-select)

| config | fit /sess | fit avg R | fit avg R w/o best | check /sess | check avg R | check w/o best | check t | check long / short |
|---|---|---|---|---|---|---|---|---|
| 18a K1-MOM-N5 | 28.5 | -0.028 | -0.030 | 28.5 | -0.022 | -0.023 | -4.54 | -0.016 / -0.027 |
| 18b K1-MOM-N10 | 56.2 | -0.022 | -0.024 | 57.0 | -0.018 | -0.019 | -4.97 | -0.013 / -0.022 |
| 18c K1-REV-N5 | 28.4 | -0.027 | -0.029 | 28.5 | -0.020 | -0.021 | -4.34 | -0.015 / -0.024 |
| 18d K1-REV-N10 | 56.3 | -0.026 | -0.027 | 57.0 | -0.022 | -0.022 | -6.20 | -0.020 / -0.023 |
| **18e K2-MOM-N5 (pick)** | 26.7 | -0.025 | -0.027 | 28.5 | -0.021 | -0.021 | -4.63 | -0.017 / -0.024 |
| 18f K2-MOM-N10 | 52.8 | -0.022 | -0.023 | 57.0 | -0.019 | -0.020 | -5.66 | -0.019 / -0.020 |
| 18g K2-REV-N5 | 26.7 | -0.027 | -0.029 | 28.6 | -0.018 | -0.019 | -4.13 | -0.018 / -0.018 |
| 18h K2-REV-N10 | 52.9 | -0.026 | -0.027 | 57.0 | -0.024 | -0.025 | -7.54 | -0.023 / -0.025 |

Every config is negative in both halves and on both sides, so the plateau is flat at minus the cost. Fit total R minus
the best day ranged from -121.9 (18e, picked) to -256.5 (18d). The N 10 configs lose more in total only because they
trade twice as much.

## Build (faithful to round2/PLAN.md sec. 3 "ULT-18")
- **Live module** `research/ultimate_1119/modules/ULT-18.py`.
  - It exposes `SIDE`, `GEOM "S"`, `LAYERS`, `features()`, `select_book()`, `set_book()`, `mask()` and `stop_price()`.
  - Two sides, one file: the side comes from the setup name ("-S" / "-short" = the short side).
  - The defaults are the fit pick (KEY k2, MOM, N 5).
  - bt.py imports `features()` and `select_book()`, so the backtest and the module share one code path for the keys,
    the eligibility and the book.
- **Live gap (the candidate fails anyway, but for the record):**
  - A LabStrategy mask sees one symbol's frame, so a cross-sectional rank needs a **runner hook**. Once per decision
    bucket the hook would call `select_book` on every polled name's frame and pass the cut-offs to `set_book`. That hook
    does not exist today.
  - Without a book the mask fails safe (no signal).
  - With K2, the live frame also lacks `sec_fo` / `sec_beta`. This is the same gap as ULT-11.
  - The YAML it would need (not written to any config): `type: lab`, `module: research/ultimate_1119/modules/ULT-18.py`,
    `window: [1100, 1400]`, `min_adv: 200000000`, `context: [spy_fo]`, `geom: S`, `time_stop_min: 45`,
    `time_stop_min_r: 99`, `refire: true`, `refire_cooldown: 0`, `symbols: module`. The short entry also needs
    `shorts.require_easy_to_borrow`.
- **Smoke test** `round2/ULT-18/test_module.py`: 3 passed. It checks that:
  - `select_book` gives the MOM and REV picks, replaces excluded and blocked names with the next eligible one, gives no
    book when the key is missing, and never puts a name on both sides;
  - under the live LabStrategy, the long side fires only at the 11:00 / 13:00 / 14:00 bars when the book's cut-off
    admits the name;
  - there is no signal without a book, with a cut-off above the name's key, or without SPY context;
  - the short side fires under REV and is blocked by gap >= +0.5%;
  - the 2u catastrophic stop is in place;
  - features do not change when later bars are removed (no look-ahead).
- **Backtest** `round2/ULT-18/bt.py`. It reuses ULT-11's `sector_map` / `month_frame` and ULT-14's `stats` /
  `sub_halves`; there is no new infrastructure.
  - **Superset:** per moment, key and side, the 40 highest and 40 lowest eligible names, plus 10 random eligible names
    per side. A depth of 40 covers N 10, plus 2N blocked names, plus N names used on the other side, so the
    full-universe rank is reproduced exactly.
  - **Book:** built moment by moment with the chassis rules: one lot per symbol, refire only >= 30 min after the exit,
    max 2 per symbol-session. A name blocked from 13:00 into 14:00 is replaced by the next eligible name. Day cap 6N
    (never binding; asserted).
  - **Chassis:**
    - entry at the open of the 1-minute bar that starts at the decision close;
    - catastrophic stop 2u beyond the decision close; time exit at the close of minute entry+44; flat 15:50;
    - LR8 costs plus 1.2 bp borrow on shorts; shorts only easy-to-borrow (universe.csv, today's flag);
    - R per 2u.
  - Eligible names per moment: about 55-270 long and 36-165 short (fewer in low-volatility months, because of the
    cost_r cap).
- **Look-ahead guards:**
  - forbidden outcome / heat columns are dropped and asserted absent; the module source is asserted not to read them;
  - the keys use only the decision bar, the day's open, the prior-day ATR / ADV, the SPY context and the
    prior-session sector map (the fit map is built from daily rows <= 2025-09-30 only).
- **Locked block:**
  - never read: pyarrow filters on every 1-minute load, a date filter on daily.parquet, and `no_locked()` asserts on
    frames, the superset, walks and day lists;
  - MCF_HIST_ALLOW_LOCKED refused.
- **Order:**
  - FIT grid -> `fitsel.json` frozen at 2026-11-19T07:18:29Z (bt.py sha256 3fb5f0cc...; unchanged after);
  - fit random control;
  - then the check superset was built and walked;
  - check scored once at 07:20:34Z (`check_once.json`);
  - then the plateau.
  - One post-freeze edit: the module's default constant `KEY` was changed from "k1" to the fit pick "k2", so its sha
    differs from `sha256_module_at_freeze` (fe1593d6...). bt.py passes every config explicitly, so that constant never
    affects a backtest number.

## Notes, caveats, controls
- **The same-name random-TIME control is invalid for this candidate, and it is reported only to say why.** It draws a
  random 10:00-15:00 bar on the same symbol-session and side. It earns +0.036 (fit) and +0.054 (check), which would make
  the signal look 0.06-0.07 worse. But the names were picked *because* of their move by 11:00 / 13:00 / 14:00. A random
  earlier bar therefore trades the very move that got the name picked (check by hour: 10:00 +0.197, 11:00 +0.076,
  13:00 -0.006, 14:00 -0.019). That is look-ahead inside the control, not in the signal. The valid control is the
  same-moment random-names one in the table.
- **Biases left in, all favouring the candidate:**
  - today's symbol list (survivorship, flatters longs);
  - today's ETB flag (0 non-ETB short rows on fit; 13 on check, excluded);
  - borrow modelled only as a flat 1.2 bp.
  - The signal-close / no-borrow diagnostic shows the two fixed biases were worth about +0.003-0.004R per trade.
- **K2 sector-relative key:** 367 check name-moments had no sector map and were not ranked. On fit, the first 10
  sessions of 2024-10 had no K2 ranks at all, because the map needs 20 prior daily sessions. This handicapped K2's fit
  totals, and K2 was still the pick.
- Post-hoc diagnostics (gross R, by-time split, random-time breakdown) were computed after the single check score. They
  explain the result; they select nothing.

## Configurations
- Counted for ULT-18: **9** (8 grid + 1 bias diagnostic), as pre-registered in round2/PLAN.md sec. 4. Random-name and
  random-time controls and the post-hoc diagnostics above are reported, not counted.
- Cumulative N for the t bar: **774** (round 1 682 + round 2 92, the planned total), so the bar is sqrt(2 ln 774) = 3.65.

## Rule-change context (owner 2026-11-02)
The 2-year halves are scored with one fixed rule set (today's chassis), so no live rule change falls inside them. No
live-record figure is quoted here.

## Files
- Module: `research/ultimate_1119/modules/ULT-18.py` (reads `modules/ULT-12_symbols.json` "S" = the frozen non-ETF
  lab list).
- `round2/ULT-18/bt.py`, `test_module.py`, `fit_grid.json`, `fitsel.json`, `fit_random.json`, `check_once.json`,
  `check_plateau.json`.
- The superset / walked trade lists lived in the scratchpad work dir and were deleted after scoring (they can be
  regenerated with the bt.py stages).

Educational only — not financial advice.
