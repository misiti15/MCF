Educational only — not financial advice

# ULT-29 EARN-CONFL: gated confluence on an earnings reaction-day with-gap base (round 4), LONG + SHORT

**Tier: FAIL.** No pre-registered config may trade. The FIT base gate closed all 4 base × exit cells, so the setup trades
nothing, as PLAN sec. 3 says. The two diagnostics (gates ignored) also lose on CHECK. Tags: PARTLY CHECK-INFORMED;
**needs an owner exception to the earnings blackout** (`earnings_blackout_days: 4`, owner 2026-10-07).
Research only: no setup, exit, config or account change. Nothing committed.

## What was built (faithful to round4/PLAN.md sec. 3 "ULT-29")
- **Module:** `research/ultimate_1119/modules/ULT-29.py`. It is live-ready under `LabStrategy` (type lab, context
  [spy_fo], window [1000, 1300], `symbols: module`).
  - Two setups in one file: a name ending -S gives EB-S (short); any other name gives EB-L (long).
  - Exit H = GEOM t1s1; exit X = GEOM "S" (2u stop) + YAML time_stop_min 45.
  - `rd_events()` builds the reaction days (bmo = report day, amc = next session; dmh/unknown dropped; a repeat within
    10 sessions keeps the first). The backtest uses the same function.
  - As frozen, the module **never fires**: BASE_OPEN is all False and SURVIVE is empty.
- **Smoke test:** `round4/ULT-29/test_module.py`, 4 passed. It checks:
  - the frozen module never fires;
  - an opened copy fires under the live LabStrategy with a 2u stop;
  - names that are not reaction days are refused by `eligible()`;
  - it does not fire without SPY context, without a ≥ 2% gap, at cost_r > 0.08, or with no RD entry for today;
  - point-in-time truncation;
  - `rd_events()` handles bmo/amc and never jumps across a gap in the session list.
- **Backtest:** `round4/ULT-29/bt.py`. Chassis, 1-minute walk and statistics are the round-3 ULT-24 code, with these
  round-4 additions:
  - x1.5 entry/exit cost on reaction-day bars before 10:30;
  - borrow of 5 bp (8 bp if price < $20) on every earnings short; the non-earnings twin pays 1.2 / 3 bp;
  - ETB only, and no leveraged or inverse funds.
- **Earnings table:** `round4/data/earnings_yf.parquet`. Rows dated in the locked block are dropped before use, and
  `no_locked()` asserts on the table, frames, trade lists and 1-minute loads.
  - FIT has 2,525 reaction-day symbol-sessions (the plan expected about 2,540).
  - Only 708 symbol-sessions are base-eligible (gap ≥ 2%, ADV20 ≥ $30M, cost_r ≤ 0.08), about 4.2 per session.
- **Live caveats for Deploy (moot at FAIL):**
  - The live frame has no symbol column. Today's RD names must come from `ULT-29_rd.json` (built from a report-date +
    report-hour calendar) and enter through `symbols: module` / `eligible()`.
  - The module reads that file once at load, so the runner must reload it each session.
  - The live Nasdaq feed lacks the report hour.

## Base gate (FIT, scored before any trigger): ALL CLOSED
One random base-eligible bar per symbol-session (seed [1119, month, base]). A cell passes only if random avg R ≥ 0 in
both sub-halves A and B.

| base | exit | n | avg R | A avg R (n) | B avg R (n) | gross before costs | ex 04-03..04-09 | pass |
|---|---|---|---|---|---|---|---|---|
| EB-L | TX-45 | 349 | +0.037 | +0.070 (222) | −0.020 (127) | +0.058 | +0.037 | no |
| EB-L | t1s1 | 349 | −0.011 | +0.031 | −0.084 | +0.028 | −0.013 | no |
| EB-S | TX-45 | 359 | −0.029 | −0.047 (240) | +0.007 (119) | +0.023 | −0.027 | no |
| EB-S | t1s1 | 359 | −0.063 | −0.094 | −0.000 | +0.037 | −0.060 | no |

- EB-L under TX-45 is the closest. It is +0.037 overall and +0.070 in A, but −0.020 in B (n 127). That is the base
  "with a reason" falling just short.
- Under the pre-registered rule, the trigger gate was skipped, all 8 grid configs have 0 trades and there is no pick
  (`fitsel.json` pick = null, frozen 2026-11-19T08:53:34Z, before any check data).
- CHECK base random (reporting only, after the check score):
  - EB-L: TX-45 +0.002, t1s1 −0.003.
  - EB-S: TX-45 −0.037, t1s1 −0.096.
  - The gate was right: the earnings base is about 0 on the long side and negative on the short side after costs.

## Diagnostic 1: trigger gate with the base gate ignored (FIT; added after the gate closed, before any check data)
Signal minus same-base random, TX-45, per sub-half. A trigger survives only if both are ≥ 0.

| trigger | n | avg R | A − random | B − random | survives |
|---|---|---|---|---|---|
| L1 VWAP-hold | 391 | −0.007 | −0.055 | −0.041 | no |
| L2 new high | 84 | −0.044 | −0.135 | +0.056 | no |
| L3 RSI5 reset | 253 | −0.007 | −0.072 | +0.001 | no |
| **L4 vol bar** | 70 | +0.088 | +0.038 | +0.057 | **yes** |
| S1 VWAP-hold | 409 | −0.055 | −0.025 | −0.031 | no |
| S2 new low | 27 | −0.205 | −0.213 | −0.020 | no |
| S3 RSI5 reset | 309 | −0.025 | −0.009 | +0.021 | no |
| S4 vol bar | 57 | −0.125 | −0.066 | −0.173 | no |

- Only 1 trigger survives (EB-L L4). Every config needs C ≥ 2, so diagnostic 1 also trades nothing.
- On CHECK, L4 did **not** hold: −0.043 vs random (n 194).

## Diagnostic 2: no gates at all (all 4 triggers per side; frozen in fitsel.json at 08:54:04Z, before any check data)
FIT grid. Pick rule: max (total R − best day) among configs with ≥ 2/session.

| cfg | label | /session | avg R | w/o best day | total R | total − best day | A | B | t |
|---|---|---|---|---|---|---|---|---|---|
| 29a | W1-C2-t1s1 | 2.27 | −0.066 | −0.077 | −25.3 | −29.2 | −0.081 | −0.024 | −1.68 |
| **29b** | **W1-C2-TX45** | **2.21** | **−0.004** | **−0.022** | **−1.3** | **−7.8** | −0.005 | +0.002 | −0.10 |
| 29c | W1-C3-t1s1 | 0.06 | +0.010 | −0.094 | +0.1 | −0.9 | −0.003 | +0.126 | 0.04 |
| 29d | W1-C3-TX45 | 0.06 | +0.189 | −0.071 | +1.9 | −0.6 | −0.071 | +2.53 | 0.64 |
| 29e | W3-C2-t1s1 | 3.37 | −0.046 | −0.056 | −26.4 | −30.4 | −0.052 | −0.033 | −1.43 |
| 29f | W3-C2-TX45 | 3.21 | −0.035 | −0.043 | −18.8 | −22.7 | −0.044 | −0.011 | −1.33 |
| 29g | W3-C3-t1s1 | 0.20 | +0.012 | −0.033 | +0.4 | −1.1 | +0.135 | −0.284 | 0.09 |
| 29h | W3-C3-TX45 | 0.20 | −0.041 | −0.119 | −1.4 | −3.9 | +0.006 | −0.154 | −0.31 |

C3 fires 0.06-0.2 per session, because the triggers rarely coincide. Every C2 config loses on FIT.

### Diagnostic pick 29b (W1-C2-TX45), FIT vs CHECK (CHECK scored once; DIAGNOSTIC, cannot set the tier)

| | FIT (170 sessions) | CHECK (276 sessions) |
|---|---|---|
| trades (/session) | 376 (2.21) | 817 (2.96) |
| win | 0.497 | 0.487 |
| avg R (per 2u) / per 0.25-dATR | −0.0035 / −0.007 | **−0.0236** / −0.047 |
| avg R w/o best day; best-day share | −0.022; n/a (total < 0) | −0.029; n/a (total < 0) |
| total R; R/session | −1.3; −0.008 | −19.3; −0.070 |
| worst day; worst day / trade-session | −3.96; −0.88 | −5.84; −1.10 |
| day-clustered t | −0.10 | −1.06 (bar 3.72) |
| long / short avg R (n) | +0.024 (170) / −0.026 (206) | −0.016 (372) / −0.030 (445) |
| long avg R w/o best day (best-day share) | +0.002 (0.91, **1 day**) | −0.027 |
| SPY up / flat / down | +0.015 / +0.014 / −0.035 | −0.008 / −0.017 / −0.055 |
| without 2025-04-03..04-09 | −0.002 (375) | n/a (no such dates) −0.024 |
| sub-halves A / B (fit); 1st / 2nd half (check) | −0.005 / +0.002 | −0.050 / −0.005 |
| earnings season / off-season (≥ 8 RD per session) | +0.004 (334) / −0.064 (42) | −0.026 (749) / +0.003 (68) |
| random control (same name and session, 10:00-13:00) | +0.011; signal − random −0.015 | +0.002; **signal − random −0.026** |
| bias diag (fill at signal close, no borrow, no surcharge) | +0.007 | −0.013 |
| median hold; exit mix | 45 min; time 333 / stop 43 | 45 min; time 720 / stop 97 |
| uncapped (no day cap) | same | same (the cap never binds) |

CHECK plateau, no gates (reporting only), avg R:
- C2 configs: 29a −0.077, 29b −0.024, 29e −0.074, 29f −0.023.
- C3 configs: 29c −0.032, 29d +0.142 (18 trades), 29g −0.112, 29h −0.053.
- The only positive cell is 29d on 18 trades.

### Non-earnings twin (the 29b rule on gap ≥ 2% names with no report within −8..+4 calendar days)
| | FIT | CHECK |
|---|---|---|
| trades/session | 14.8 | 24.5 |
| avg R | +0.011 | +0.003 |
| avg R w/o best day | −0.001 | −0.001 |
| t | 0.47 | 0.24 |
| long / short avg R | −0.011 / +0.036 | −0.000 / +0.007 |

The twin does no worse than the earnings version (CHECK +0.003 vs −0.024). On this intraday 10:00-13:00 horizon,
**"news" does not carry an edge for these continuation triggers.** The higher costs on reaction days (surcharge and
5-8 bp borrow) make the earnings shorts worse.

## Bars
| bar | needed | result |
|---|---|---|
| TIER A: check avg R > 0 | > 0 | no trades (pre-registered); diagnostic −0.024 |
| check avg R w/o best day > 0 | > 0 | diagnostic −0.029 |
| fit avg R > 0 | > 0 | pre-registered: no trades; diagnostic −0.004 |
| ≥ 2 trades/session on check | ≥ 2 | pre-registered 0; diagnostic 2.96 |
| BEATS: avg R > +0.0836, w/o best day > +0.0734, R/session > 0, worst day/trade-session ≥ −2.152, t ≥ 3.72 | — | none met (t −1.06) |
| TIER B: fit > 0 and check > −0.02 | — | no |

**FAIL**, not deployable. It is not a weak setup forced through: the pre-registered rule closed it on FIT, and both
diagnostics confirm it on CHECK.

## Configurations counted
- Pre-registered: 20 (8 grid + 4 base gates + 8 trigger gates; the 8 pre-registered trigger gates were skipped because
  the bases were closed, but they stay counted).
- Diagnostic additions: +8 trigger-gate evaluations (base gate ignored) and +8 no-gates grid configs. The base-ignored
  grid traded nothing.
- Total: **36** for ULT-29, plus 1 bias diagnostic inside the round's 8.
- Cumulative N rises from 996 to **1,012** if the diagnostics are counted. sqrt(2 ln 1012) = 3.72; the t bar is
  unchanged at 2 decimals.

## Look-ahead / integrity
- Forbidden columns (win_*, r_*, *heat*) are dropped and asserted absent.
- Features use only the decision bar and earlier bars of the same session, plus spy_fo and prior-day ATR/ADV. The
  truncation test passes.
- The earnings fields used are the scheduled report date and session only; surprise is not used.
- The locked block is never read. The earnings rows dated in it are dropped. An amc report whose next listed session
  lies more than 5 days away (across the block) is dropped.
- fitsel.json was frozen before any check frame, event row or trade was built. The module sha256 is unchanged since
  the freeze.
- bt.py changed after the freeze in one line: `np.isin` became `pd.Series.isin` in the twin/frame filter, for speed.
  The semantics are identical, and the FIT signal counts were already built.
- Known biases that remain: today's symbol list (survivorship, flatters longs), fills at the next minute's open, and
  ETB from today's flag.

## Files (round4/ULT-29/)
- Gates: base_gate.json, trigger_gate.json, trigger_gate_diag_ungated.json.
- Fit grids: fit_grid.json (empty), fit_grid_diag_ungated.json (empty), fit_grid_diag_nogates.json.
- fitsel.json.
- CHECK: check_diag_nogates.json, check_trades_diag.csv.gz, check_plateau.json, check_gates_diag.json.
- fit_random_diag_nogates.json, twin_fit.json, twin_check.json.
- bt.py, test_module.py.
- Module: research/ultimate_1119/modules/ULT-29.py.

## Rule-change context
Both halves are scored with one fixed rule set: today's LR8 costs and the round-4 chassis. No live rule change falls
inside them. The live earnings blackout (4 days, owner 2026-10-07) was in force through the whole live record, so no
live setup has a reaction-day record to compare with.

Educational only — not financial advice.
