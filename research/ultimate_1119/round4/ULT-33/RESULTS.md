Educational only — not financial advice

# ULT-33 EARN-GEO — cost geometry on earnings reaction-day moves (round 4) — **FAIL**

Research only: no setup, exit, config or account change. Nothing committed. **PARTLY CHECK-INFORMED** (PLAN sec. 0.6).
Any deployment would also **need an owner exception to the 4-day earnings blackout** (sec. 0.8). That question does not
come up, because the candidate fails.

## Verdict
- **All 12 grid configs are negative on FIT** (-0.023 to -0.114R). So no pick can reach TIER A or TIER B.
- **Fit pick 33l (m 1.0, t2s1, LMT)** was chosen by the PLAN sec. 5 rule (fit total R minus the best day, among configs
  with >= 2/session). Picking by plain fit total R gives the same config.
  - Fit: **-0.029R** (n 531, 3.12/session, t -1.16).
- **CHECK, scored once:** **-0.028R**. 1,051 trades, 3.81/session. Without the best day: -0.033. Total -29.6R
  (-0.107R/session). Day-clustered t -1.97 against a bar of 3.716.
- **Tier: FAIL.** All 12 configs are negative on check too (plateau below), so no cell was left behind.
- **The thesis fails at its premise.** Within a 45-minute hold, a reaction-day name does not travel 1-2 daily ATRs:
  - at m 1.0, 91-96% of trades end on the time exit; 33l hit its +2 Ru target **once** in 531 fit trades and never on
    check;
  - at m 0.5 / t2s1, the target is hit on 3-5% of trades.
  So widening R does cut cost per R: the loss per 0.25-dATR unit is about the same (-0.09..-0.12 R_u) at every m.
  But the drift before costs is ~0 or slightly negative, and there is no larger move inside the hold to capture.
- **The limit entry adds adverse selection, as on ordinary bars (ULT-16).**
  - Fill rate is 0.28-0.30. The limit sits 0.30 dATR (median 0.23) behind the decision close, at VWAP + 0.05 dATR.
  - On fit, LMT is worse than MKT in 5 of 6 (m, exit) pairs.
  - The orders that fill are the gaps that come back to VWAP, which tend to be the failing ones.

## Configurations tried
- This candidate: 12 grid + 1 bias diagnostic = **13**. These were already inside PLAN sec. 4's round-4 total.
- Cumulative N stays **996**, so the t bar is 3.716.
- The random-entry control and the non-earnings twin are reported, not counted.

## What was built
- **Module:** `research/ultimate_1119/modules/ULT-33.py`. It is live-ready with the round 1-4 interface: LabStrategy
  `type: lab`, two entries in one file ("-S" = short), `context: [spy_fo]`, `symbols: module`.
  - Calendar, `reaction_days()`, `today_symbols()` (S any) and the HOLD rule are reused from `modules/ULT-28.py`, so
    there is one code path.
  - Exit is GEOM "S" with `stop_price` = close - s x 1 Ru and `target_price` = close + s x K Ru. YAML adds
    time_stop_min 45, r_atr_frac = M and min_adv 100e6.
  - Module constants are set to the pick (M 1.0, K 2, ENTRY "LMT"). The header records the fit FAIL.
  - **Not live-expressible:** the LMT entry. LabStrategy / Signal only offer market and stop entries. Run as it
    stands, the module trades the MKT twin 33k (fit -0.023, check -0.029). Neither variant is deployable.
- **Smoke test:** `round4/ULT-33/test_module.py`, 3 tests, all pass. It covers:
  - the calendar allow-list and its fail-safe;
  - long and short under the live LabStrategy, with stop 1 Ru and target K Ru checked;
  - no signal on a non-event name, ADV < $100M, a faded gap or a gap < 3%;
  - point-in-time truncation;
  - the e_rd gate;
  - cost_r scaling with 1/m;
  - the limit price.
- **Backtest:** `round4/ULT-33/bt.py`. It imports round4/ULT-28/bt.py for the event table, the locked-block guards,
  the stats, and the LR8 + surcharge + borrow cost function.
  - The superset holds every HOLD bar in 09:50-12:30 with |gap| >= 3%, ADV20 >= $100M and cost_r(m=1) <= 0.08.
    Each config then applies cost_r(m) = cost_r1 / m <= 0.08. That is why m 1.0 trades more names (4.9/session)
    than m 0.25 (2.9).
  - **MKT:** the ULT-28 chassis. Entry at the next-minute open, brackets around the decision close.
  - **LMT:** limit L = decision-bar VWAP + s x 0.05 x atr_d, working 15 minutes.
    - If the first minute opens through L, the order fills at that open (marketable).
    - Otherwise it fills at L on the first minute that trades **strictly** through L.
    - Brackets sit around the fill. On the fill minute only the stop counts (conservative).
    - The cap is 45 minutes from the fill.
    - The LR8 entry cost is charged at the fill minute, including the x1.5 surcharge before 10:30.
    - An unfilled order blocks the symbol for 15 minutes and is not an entry.
  - **Costs:** LR8, x1.5 entry/exit cost before 10:30 on reaction days, and short borrow of 5 bp (8 bp < $20) on
    reaction days or 1.2 / 3 bp on the twin. Shorts are ETB only.
  - **Chassis:** one lot per symbol, refire >= 30 min after the exit, max 2 per symbol-session, day cap 30, flat 15:49.
  - **R:** reported per actual risk (Ru = m x atr_d) and per 0.25-dATR unit (R_u).
- **Locked block:** never read. pyarrow filters and `no_locked` asserts run on every frame, event and 1-minute load,
  and events with RD in the block are dropped. Forbidden columns (win_*, r_long/short*, *heat*) are dropped and
  asserted absent.
- **Order of steps:**
  1. fitsel.json frozen at 2026-11-19T09:29:53Z, with sha256 of bt.py, the module and the earnings file.
  2. Module constants set to the pick, and their sha256 added to fitsel.json.
  3. Only then was the check superset built. Check was scored once at 09:31:32Z, and the plateau ran after it.

## FIT grid (170 sessions)
| cfg | rule | /session | avg R | w/o best day | total R | R_u (0.25 dATR) | fill | A / B | long / short | t | exit mix (stop / target / time) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 33a | m0.25 t1s1 MKT | 2.86 | -0.091 | -0.101 | -44.2 | -0.091 | 1.00 | -0.033 / -0.193 | -0.018 / -0.158 | -2.32 | 189 / 184 / 113 |
| 33b | m0.25 t1s1 LMT | 1.82 | -0.067 | -0.087 | -20.6 | -0.067 | 0.30 | +0.001 / -0.194 | +0.043 / -0.161 | -1.07 | 123 / 118 / 68 |
| 33c | m0.25 t2s1 MKT | 2.83 | -0.086 | -0.105 | -41.4 | -0.086 | 1.00 | -0.032 / -0.181 | -0.033 / -0.135 | -1.67 | 215 / 74 / 192 |
| 33d | m0.25 t2s1 LMT | 1.77 | -0.114 | -0.135 | -34.3 | -0.114 | 0.30 | -0.015 / -0.300 | -0.007 / -0.207 | -1.70 | 139 / 41 / 121 |
| 33e | m0.5 t1s1 MKT | 4.44 | -0.049 | -0.065 | -37.1 | -0.098 | 1.00 | -0.047 / -0.053 | +0.003 / -0.095 | -1.54 | 159 / 149 / 447 |
| 33f | m0.5 t1s1 LMT | 2.77 | -0.078 | -0.088 | -36.6 | -0.156 | 0.29 | -0.060 / -0.107 | -0.064 / -0.090 | -2.50 | 104 / 82 / 284 |
| 33g | m0.5 t2s1 MKT | 4.41 | -0.069 | -0.081 | -51.9 | -0.139 | 1.00 | -0.071 / -0.067 | -0.008 / -0.124 | -2.45 | 163 / 26 / 560 |
| 33h | m0.5 t2s1 LMT | 2.73 | -0.083 | -0.095 | -38.4 | -0.165 | 0.29 | -0.078 / -0.091 | -0.063 / -0.099 | -2.52 | 103 / 13 / 348 |
| 33i | m1 t1s1 MKT | 4.92 | -0.026 | -0.033 | -21.4 | -0.102 | 1.00 | -0.024 / -0.027 | -0.003 / -0.046 | -1.55 | 40 / 37 / 760 |
| 33j | m1 t1s1 LMT | 3.13 | -0.030 | -0.045 | -16.2 | -0.122 | 0.29 | -0.019 / -0.049 | -0.009 / -0.048 | -1.27 | 21 / 24 / 487 |
| 33k | m1 t2s1 MKT | 4.92 | -0.023 | -0.030 | -19.1 | -0.091 | 1.00 | -0.023 / -0.023 | +0.002 / -0.044 | -1.30 | 40 / 2 / 794 |
| **33l** | **m1 t2s1 LMT** | 3.12 | -0.029 | -0.043 | **-15.4** | -0.116 | 0.29 | -0.017 / -0.047 | -0.005 / -0.049 | -1.16 | 21 / 1 / 509 |

- **Eligible (>= 2/session):** all configs except 33b and 33d.
- **Pick:** 33l is the least-bad by both total R minus best day (-21.8) and plain total R (-15.4).
- **Volume:** came in above plan. MKT ran 2.8-4.9/session (planned 2-4) and LMT 1.8-3.1 (planned 1-2.5).
- **2025-04-03..04-09:** no fit trades fall there (off season). The "without" figures equal the full figures.

## Fit pick 33l: FIT vs CHECK
| | FIT | CHECK (once) |
|---|---|---|
| trades (/session) | 531 (3.12) | 1,051 (3.81) |
| sessions traded | 99 of 170 | 173 of 276 |
| LMT orders, fill rate | 1,827, 0.291 | 3,761, 0.280 |
| win | 0.480 | 0.488 |
| avg R per actual risk (1 dATR) | **-0.0290** | **-0.0282** |
| avg R per 0.25-dATR unit | -0.116 | -0.113 |
| avg R w/o best day | -0.0430 | -0.0331 |
| best day (share) | 2024-10-31 +6.4R (n/a, total < 0) | 2026-11-04 +4.7R (n/a, total < 0) |
| total R (R/session) | -15.4 (-0.091) | -29.6 (-0.107) |
| worst day (/ trade-session) | -3.45 (-0.64) | -3.73 (-0.61) |
| day-clustered t | -1.16 | **-1.97** (bar 3.716) |
| w/o 2025-04-03..04-09 | -0.0290 (no trades in it) | n/a (no such dates) |
| sub-halves A / B | -0.017 / -0.047 | — |
| first / second half | -0.009 / -0.055 | -0.023 / -0.033 |
| long / short | -0.005 (n 238) / -0.049 (n 293) | -0.011 (n 528) / -0.045 (n 523, t -2.46) |
| SPY up / flat / down | -0.008 / -0.105 / +0.003 | -0.015 / -0.045 / -0.020 |
| entry 09:50-10:25 / 10:30-11:25 / 11:30-12:30 | -0.019 / -0.078 / -0.004 | -0.032 / -0.031 / -0.019 |
| gap 3-5 / 5-10 / 10+ % | +0.020 / -0.055 / -0.060 | -0.022 / -0.034 / -0.029 |
| season / off-season sessions (>= 5 RD names) | -0.029 (n 501) / -0.027 (n 30) | -0.032 (n 1,010) / +0.064 (n 41) |
| median hold; exit mix | 45 min; time 509 / stop 21 / target 1 | 45 min; time 1,014 / stop 37 / target 0 |
| bias diagnostic (no borrow, no surcharge) | -0.017 | -0.019 |
| random-entry control (same names/sessions/side, random bar 09:50-12:30, same LMT logic, VWAP from 1-min bars) | +0.006 (n 355 paired; fill 0.67); **signal minus random -0.153** | +0.021 (n 693; fill 0.66); **-0.160** |
| random long / short | +0.039 / -0.024 | -0.002 / +0.044 |
| non-earnings twin (same rule, no report in RD-5..RD+1) | -0.004 (10.0/session, t -0.22) | -0.010 (18.3/session, t -1.24) |

- **Bars:**
  - check avg R > 0: no.
  - w/o best day > 0: no.
  - fit avg R > 0: no.
  - >= 2/session: yes.
  - BEATS: no. avg R, w/o best day, R/session and t all fail. Only the worst-day bar (-0.61 >= -2.152) passes.
- **Signal minus random is computed on the pairs where both legs filled.** The signal leg of those pairs averages
  about -0.15, worse than the full pick's -0.029. Read the gap as "a limit placed at the HOLD bar is worse than one
  placed at a random bar". The random leg itself is ~0 (+0.006 / +0.021), not a usable edge.
- **Earnings vs no news:** reaction-day 33l (-0.028) is worse than its non-earnings twin (-0.010). As in ULT-28, the
  news day does not carry the HOLD entry on this chassis.

## CHECK plateau (diagnostic only, run after the single check score; never used to re-select)
| cfg | /session | avg R | w/o best day | R_u | fill | t | long / short |
|---|---|---|---|---|---|---|---|
| 33a | 4.03 | -0.054 | -0.063 | -0.054 | 1.00 | -1.70 | -0.054 / -0.054 |
| 33b | 2.53 | -0.038 | -0.053 | -0.038 | 0.28 | -1.01 | -0.013 / -0.060 |
| 33c | 3.98 | -0.087 | -0.097 | -0.087 | 1.00 | -2.20 | -0.057 / -0.114 |
| 33d | 2.46 | -0.074 | -0.093 | -0.074 | 0.28 | -1.52 | -0.054 / -0.093 |
| 33e | 5.45 | -0.056 | -0.063 | -0.111 | 1.00 | -2.98 | -0.048 / -0.063 |
| 33f | 3.48 | -0.071 | -0.079 | -0.142 | 0.28 | -2.83 | -0.049 / -0.093 |
| 33g | 5.42 | -0.055 | -0.065 | -0.111 | 1.00 | -2.58 | -0.052 / -0.059 |
| 33h | 3.44 | -0.065 | -0.076 | -0.131 | 0.28 | -2.23 | -0.034 / -0.095 |
| 33i | 5.92 | -0.027 | -0.031 | -0.109 | 1.00 | -2.61 | -0.021 / -0.034 |
| 33j | 3.81 | -0.027 | -0.032 | -0.110 | 0.28 | -1.93 | -0.009 / -0.046 |
| 33k | 5.91 | -0.029 | -0.032 | -0.114 | 1.00 | -2.71 | -0.023 / -0.034 |
| 33l (pick) | 3.81 | -0.028 | -0.033 | -0.113 | 0.28 | -1.97 | -0.011 / -0.045 |

All 12 configs are negative on check, on both the long and the short side. There is no plateau.

## Why it fails (mechanism read)
- **Cost geometry works as arithmetic, but the edge it was meant to scale is absent.**
  - Moving from m 0.25 to 1.0 cuts costs from ~0.06-0.09R to ~0.02R.
  - But the per-0.25-dATR result stays near -0.10 R_u at every m, which is about the round-trip cost.
  - The HOLD entry's gross drift over 45 minutes is ~0, and the "2-4 dATR move" mostly happened **before 09:50**
    (in the gap and the opening range). It is not still ahead of a 09:50+ entry.
- **2:1 targets are almost never reached at m >= 0.5,** so t2s1 is in effect a 45-minute time exit.
- **Shorts are the weaker side in both halves:** fit -0.049, check -0.045 (t -2.46). That is consistent with ULT-28
  and partly reflects the 5 / 8 bp borrow estimate.

## Leads (optimistic; each would need its own pre-registration and count; CHECK is now read for this idea)
- None for EARN-GEO itself: the geometry lever has now been tried on ordinary bars (ULT-16, ULT-25) and on news days,
  and it is flat in every case.
- The one weak thread is the gap 3-5% long side. It is +0.020 on fit (33l) and 33b long is +0.043, but check
  33b long is -0.013. That is too thin to pursue.

## Files
- `research/ultimate_1119/modules/ULT-33.py`: the module, with constants set to the pick 33l and the FIT/CHECK FAIL
  recorded in the header.
- `research/ultimate_1119/round4/ULT-33/`: bt.py, test_module.py, fit_grid.json, fitsel.json, fit_random.json
  (random control, uncapped, fit twin), check_once.json, check_plateau.json (incl. check twin), check_trades.csv.gz.
- The walked superset parquet files (45 MB, scratchpad) have been deleted.

## Rule-change context
- Both halves are scored under one fixed rule set: today's LR8 costs, the round-3/4 chassis, and the round-4
  surcharge and borrow fixes. No live rule change falls inside them.
- The live 4-day earnings blackout (owner 2026-10-07) was in force through the whole live record, so there is no live
  comparison.

## Known biases (all favour the candidate, and it still fails)
- Today's symbol list (survivorship) flatters longs.
- The ETB flag is today's.
- The earnings table was fetched after the fact.
- The yfinance report hour is assumed to be correct.
- MKT fills at the next-minute open; LMT fills at the limit when price trades strictly through it. No queue position
  is modelled beyond that.

Educational only — not financial advice.
