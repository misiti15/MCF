Educational only — not financial advice

# ULT-03 RSI-collapse dip buy, broadened (ST7 chassis) — RESULTS: **FAIL**

Research only (ultimate_1119, PLAN.md sec. 3 "ULT-03"). No setup, exit, config or account change; nothing committed.

**Verdict: FAIL** under the pre-registered deploy bar (PLAN sec. 6). All 8 grid configs lose on the FIT half after
costs (best −0.019R/trade), so neither TIER A nor TIER B is reachable (both need fit avg R > 0). The fit-selected
config **03b** (RSI_MAX 30, ADV ≥ $20M, TX45), scored once on CHECK: **−0.006R/trade, −0.008 without its best day,
15.3 trades/session**. Volume came through as hoped (5× ST7-FD's 3.1/session) but the edge did not: the broadening
dilutes ST7's check-half +0.084 to about zero.

## What was built
- **Module (live interface):** `research/ultimate_1119/modules/ULT-03-rsicollapse-dip-long-broad.py` — `SIDE`, `GEOM`,
  `LAYERS`, `mask(df)`, `stop_price(f, i)` for GEOM "S" (same interface as the deployed workbench modules, e.g.
  L3-gap-slope-rsi5hi-FD-WB5, ST7-…-FD-WB1; SPY gate from the runner's `spy_fo` context column). Fails safe (no
  signal) without SPY context. It would load under the live engine with a YAML block like (NOT written into any config):
  `type: lab, module: research/ultimate_1119/modules/ULT-03-rsicollapse-dip-long-broad.py, min_adv: 20000000,
  window: [1015, 1500], context: [spy_fo], refire: true, refire_cooldown: 0, geom: S, time_stop_min: 45,
  time_stop_min_r: 99` (03b; the t1s1 variants use `geom: t1s1`). Module constants are set to 03b (RSI_MAX 30,
  EXIT "X"); the backtest overrides them to the superset (RSI_MAX 35, no thinning) and filters per config.
- **Smoke test:** `research/ultimate_1119/ULT-03-rsicollapse-dip-long-broad/test_module.py` (2 tests, pass): runs inside
  `mcf.strategies.setups.LabStrategy` with SPY context, fires inside the window on a synthetic RSI collapse with buy
  pressure, t1s1 gives ±1R, geom S gives a 2R stop and no target, no signal without SPY context; the SPY guard blocks
  "in −0.75..−0.30% band AND falling 30 min", allows band-but-rising and falling-but-outside-band.
- **Backtest:** `bt.py` (signals = the module's own `mask` on the lab frames, superset RSI_MAX 35 / ADV $20M, configs
  sub-filter; exits on 1-minute bars as benchmark/bench.py) and `score.py` (grid, frozen `fitsel.json` written before
  any check data was built, single check score `check_selected.json`, random control, diagnostics). Both adapted from
  ULT-01's scripts (long side). Trade lists were kept in the scratchpad only (regenerable, ~6 min) and deleted.

### Faithfulness notes (which way each leans)
- **Trigger reading.** "RSI14 crossed below 50 within the last 3 bars" = a cross (RSI14 < 50, the bar before ≥ 50, same
  session, consecutive 5-min bars) on the decision bar or one of the 2 bars before it; RSI14 ≤ RSI_MAX is required at
  the decision bar. fromOpen ≤ −1.0% (frames `fromOpen`), 19-bar `buyPressure` > 0, as ST7.
- **SPY gate.** spy_s930 = `spy_fo` (SPY % from its first 5-min open); spy_r30 = spy_fo now vs 6 bars (exactly 30 min)
  earlier. Missing 30-min history → no signal. Side effect: the lab frames start at the 09:50 bar, so at the **10:15**
  bar the 09:45 SPY row is absent and the backtest never fires at 10:15 (earliest backtest signal 10:20); live, the
  09:45 bar exists and 10:15 could fire. One of 58 window bars; it does not change the verdict.
- **Refire.** Backtest = PLAN chassis (one lot per symbol; refire ≥ 30 min after the exit; max 2 per symbol-session; day
  cap 30, first by time, ties ADV20 desc). The live module thins from bars alone (2nd hit ≥ 75 min after the 1st, max
  2). Module-chain diagnostic: check −0.007 vs −0.006, fit −0.019 vs −0.019 — same result.
- **TX scoring unit.** TX45 R is per unit of actual risk (2R stop = 0.5 daily ATR), as ULT-01 / bench.py `cost_r` (÷ dn).
  In 0.25-ATR units 03b is fit −0.038 / check −0.013 (same sign). Selection sensitivity: in 0.25-ATR units the fit
  totals of the X configs double (03b −60.8R) and **03a** (t1s1, −51.4R) would be picked; 03a's check score is −0.006
  (plateau table) — FAIL either way.
- **Costs** LR8 research basis (entry (1c + 1bp) × tod mult; exit 1c + 1bp except target fills; +2c on stops); intake
  cost_r ≤ 0.10 on the same stop-out round trip.
- Point-in-time only: 5-min features closed at the decision bar, prior-day ATR / ADV20, SPY at the same bar close. The
  SPY up/flat/down day label (09:30→15:59 ±0.30%) is used only for reporting.
- **Survivorship:** 1,226 lab symbols (today's list) — flatters longs; the true figures are likely a bit worse.

## Data / halves / locked block
FIT = 2024-10 + 2025-03-01..2025-09-30 (170 sessions). CHECK = 2025-10-01..2026-11-04 (276 sessions, last cache day).
The locked block 2024-11-01..2025-02-28 was never read: frames loaded per open month only, 1-minute loads use pyarrow
filters that exclude it, and every frame / trade list / 1-minute load asserts no date in it.

## FIT half — all 8 grid configs (170 sessions; costs in)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 03a R30-A20-T | 1619 | 9.52 | 0.501 | -0.032 | -0.051 | n/a (total<0) | -51.4 | -0.302 | -27.8 | 45 |
| **03b R30-A20-X** | 1619 | 9.52 | 0.500 | -0.019 | -0.028 | n/a | **-30.4** | -0.179 | -17.8 | 45 |
| 03c R30-A95-T | 1273 | 7.49 | 0.489 | -0.047 | -0.072 | n/a | -60.1 | -0.353 | -28.5 | 45 |
| 03d R30-A95-X | 1273 | 7.49 | 0.488 | -0.027 | -0.038 | n/a | -34.0 | -0.200 | -15.8 | 45 |
| 03e R35-A20-T | 3432 | 20.19 | 0.482 | -0.045 | -0.054 | n/a | -155.6 | -0.915 | -31.2 | 45 |
| 03f R35-A20-X | 3432 | 20.19 | 0.479 | -0.024 | -0.031 | n/a | -81.8 | -0.481 | -20.8 | 45 |
| 03g R35-A95-T | 2897 | 17.04 | 0.481 | -0.051 | -0.062 | n/a | -149.0 | -0.877 | -30.6 | 45 |
| 03h R35-A95-X | 2897 | 17.04 | 0.479 | -0.028 | -0.036 | n/a | -81.7 | -0.480 | -20.1 | 45 |

SPY up / flat / down avg R (fit): 03a +0.099/−0.032/−0.138 · **03b +0.036/−0.007/−0.075** · 03c +0.090/−0.033/−0.167 ·
03d +0.034/−0.015/−0.085 · 03e +0.063/−0.057/−0.135 · 03f +0.029/−0.024/−0.073 · 03g +0.052/−0.052/−0.142 ·
03h +0.027/−0.028/−0.077. Avg R without the 2025-04-03..04-09 crash week: −0.034, **−0.015**, −0.052, −0.023, −0.046,
−0.023, −0.054, −0.028 (the losses are not a crash-week artefact). Best day of every config: 2025-04-07. Traded on
168-170 of 170 sessions.

**Fit selection (PLAN sec. 5, frozen in `fitsel.json` before any check data was built):** all 8 configs reach ≥ 2
trades/session; highest fit total R = **03b R30-A20-X**, −30.4R. It is also the best by avg R w/o best day (−0.028), so
"total R / avg R w/o best day" picks the same config. Directions on fit: TX45 > t1s1 in every pair; RSI_MAX 30 > 35;
the $20M floor ≥ the $95M floor (broadening by ADV alone did not hurt).

## CHECK half — the fit-selected config, scored ONCE (276 sessions)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 03b R30-A20-X | 4212 | 15.26 | 0.509 | **-0.006** | **-0.008** | n/a (total<0) | -26.9 | -0.097 | -16.3 | 45 |

- SPY day type (check): up +0.015 / flat +0.002 / down −0.046 (fit: +0.036 / −0.007 / −0.075) — the falling-hour guard
  did not remove the down-day losses; "any market condition" is not met.
- Check first half / second half: −0.008 / −0.005. Traded sessions 276 of 276; best day 2026-06-17.
- Monthly avg R: Oct-25 −0.004, Nov −0.022, Dec +0.029, Jan-26 −0.052, Feb −0.027, Mar +0.019, Apr −0.010, May −0.013,
  Jun −0.032, Jul +0.021, Aug −0.023, Sep +0.013, Oct-26 +0.004, Nov (4 sessions) +0.044. 5 of 14 months positive.

## Random-entry control (same symbol-sessions, random intake-U bar in 10:15-15:00 with ADV ≥ floor, same side/exit)

| half | ULT-03 03b avg R | random avg R | difference |
|---|---|---|---|
| FIT | -0.019 (1619) | -0.077 (1619) | +0.058 |
| CHECK | -0.006 (4212) | -0.066 (4212) | +0.060 |

The trigger adds a steady ~+0.06R over a random bar in the same name-sessions in BOTH halves (real selection value,
almost identical to ULT-01's +0.06), but buying names that are already down > 1% on the day starts from about −0.07R
after costs, so the net is at or below zero.

## Diagnostics (counted, never used for selection or the tier)
- Uncapped (no day cap), 03b: fit 1,741 trades −0.020R (w/o best day −0.042); check 4,395 trades −0.007R (−0.008).
- Module-chain refire (live thinning), 03b: fit −0.019R (1,619), check −0.007R (4,211).
- **Why the broadening failed — ST7's own trigger inside this chassis** (cross on the decision bar itself, i.e. the
  RSI drops from ≥ 50 to ≤ RSI_MAX in ONE 5-min bar; everything else as ULT-03):
  | variant | fit n (/sess) | fit avg R | fit w/o best | check n (/sess) | check avg R | check w/o best | check best-day share | check SPY up/flat/down |
  |---|---|---|---|---|---|---|---|---|
  | cross-on-bar, RSI30, ADV20, TX45 | 158 (0.93) | -0.059 | -0.072 | 606 (2.20) | +0.045 | +0.036 | 0.21 | +0.028 / +0.040 / +0.076 |
  | cross-on-bar, RSI30, ADV95, t1s1 | 124 (0.73) | -0.115 | -0.142 | 514 (1.86) | +0.102 | +0.085 | 0.19 | +0.038 / +0.105 / +0.179 |
  The "within the last 3 bars" clause is what multiplied the volume (×7-10) and diluted the edge: slow grinds that reach
  RSI ≤ 30 two bars after the cross are not the same event as a one-bar collapse. But the one-bar version reproduces
  the ST7-FD benchmark's pattern exactly — **negative on fit (−0.06..−0.12), positive on check (+0.05..+0.10)** — so
  ST7's check edge itself is half-dependent, not a stable two-year effect. (These 2 configs were looked at after the
  check score; they cannot change the tier.)
- Check plateau (all 8 configs, diagnostic only): 03a −0.006, 03b −0.006, 03c −0.002, 03d −0.005, 03e −0.023,
  03f −0.014, 03g −0.019, 03h −0.012 (13-27 trades/session). No config positive on check; RSI_MAX 30 > 35 in every pair
  on both halves (the one robust direction).

## Recorded-quote replay (third opinion)
Not run. The candidate fails the fit half, so no replay result could change the tier, and the recorded-quote replay
(research/reps2/nightly.py --replay) holds only one session (research/reps2/replay_quotes/2026-11-18; ~1 h per run) —
too small to rank anything.

## Tier per PLAN sec. 6
| bar item | value | pass |
|---|---|---|
| check avg R > 0 | −0.006 | no |
| check avg R w/o best day > 0 | −0.008 | no |
| fit avg R > 0 | −0.019 | no |
| ≥ 2.0 trades/session on check | 15.26 | yes |
| no look-ahead | point-in-time features (code reviewed) | yes |
TIER B also needs fit avg R > 0 → **FAIL**. Benchmark (ST7-FD +0.262 R/session, +0.073 w/o best day) not approached
(03b −0.097 R/session).

## Configurations tried
8 grid configs + 1 uncapped diagnostic (pre-registered) + 1 module-chain refire diagnostic + 2 cross-on-bar diagnostics
= **12** (all scored on fit; only 03b scored on check for the tier; the check plateau re-uses the same 8). Random controls
are not candidates. Prior evidence work in this folder: 574 configs (live 230, movehunt long 104, short 240).

## What can be salvaged (optimistic, not inflated)
- The volume target is easy for this family (9-27 trades/session); the edge is the hard part.
- The trigger beats a random bar in the same names by ~+0.06R in both halves — a real ranking signal that could serve
  as a component (e.g. inside a routed book, or with a different base universe that does not start at −0.07R).
- The sharper one-bar collapse is the better event (check +0.05..+0.10), but it lost on fit; before it is broadened or
  promoted anywhere, it needs a reason why 2025-03..09 differed (it lost most on SPY-down days, −0.21..−0.41).
- Per the owner ("I don't want to force weak setups"), nothing here should be deployed.

## Rule-change context (owner 2026-11-02)
The 2-year pipeline uses one fixed rule set; no live rule change falls inside its halves. The ST7-FD live record cited
in the benchmark spans the LR8 live cost model start (2026-11-12), the Testing 1/2 cost filter max_stop_cost_r 0.15
(10-30), Testing A-F half-size lots (11-17), and the ST7-FD-WB1 workbench copy (SPY > +0.10% since 09:50 skip, Live
Lab, effective 11-17) (research/ledger.jsonl).

Files: `research/ultimate_1119/modules/ULT-03-rsicollapse-dip-long-broad.py`, and in
`research/ultimate_1119/ULT-03-rsicollapse-dip-long-broad/`: `bt.py`, `score.py`, `test_module.py`, `fitsel.json`,
`fit_grid.json`, `check_selected.json`, `RESULTS.md`.
