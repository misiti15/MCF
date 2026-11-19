Educational only — not financial advice

# ULT-01 gap-down pop fade short ("Cell A core") — RESULTS: **FAIL**

Research only (ultimate_1119, PLAN.md sec. 3 "ULT-01"). No setup, exit, config or account change; nothing committed.

**Verdict: FAIL** under the pre-registered deploy bar (PLAN sec. 6). Every one of the 8 grid configs loses on the FIT half
after costs (best −0.047R/trade), so the candidate cannot reach TIER A or TIER B (both need fit avg R > 0). The
fit-selected config, scored once on CHECK, is −0.003R/trade (−0.008 without its best day), 6.3 trades/session.

## What was built
- **Module (live interface):** `research/ultimate_1119/modules/ULT-01-gapdn-pop-fade-short.py` — `SIDE`, `GEOM`,
  `LAYERS`, `mask(df)`, plus `stop_price(f, i)` for GEOM "S" (the same interface as the deployed workbench modules, e.g.
  L3-gap-slope-rsi5hi-FD-WB5 / RW3-…-WB3; SPY gate from the runner's `spy_fo` context column exactly as RW3-WB3).
  Constants set to the fit-selected config 01f (W 11:00-15:00, RSI_MIN 60, EXIT "X").
  It would load under the live engine with a YAML block like (NOT written into any config):
  `type: lab, module: research/ultimate_1119/modules/ULT-01-gapdn-pop-fade-short.py, min_adv: 20000000,
  window: [1100, 1500], context: [spy_fo], refire: true, refire_cooldown: 0, time_stop_min: 45, time_stop_min_r: 99`
  (geom "S" = 2R catastrophic stop + no target; the t1s1 variant = `geom: t1s1`).
- **Smoke test:** `research/ultimate_1119/ULT-01-gapdn-pop-fade-short/test_module.py` (passes): the module runs inside
  `mcf.strategies.setups.LabStrategy` with SPY context, fires inside its window on a synthetic gap-down pop, t1s1 gives
  ±1R levels, geom S gives a 2R stop and no target, and it fails safe (no signal) without SPY context.
- **Backtest:** `bt.py` (signals = the module's own `mask` on the lab frames, exits walked on 1-minute bars as
  benchmark/bench.py) and `score.py` (grid, frozen selection `fitsel.json`, single check score, random control,
  diagnostics). Trade lists stay in the scratchpad (regenerable, < 5 MB).

### Faithfulness notes (what differs from the PLAN text, and which way it leans)
- **Refire.** Backtest = PLAN chassis (one lot per symbol; refire only ≥ 30 min after the exit; max 2 per
  symbol-session). The live module cannot see exits, so it thins from bars alone: 2nd hit ≥ 75 min (15 bars) after the
  1st (= 45-min max hold + 30 min), max 2. Scored as a diagnostic: fit −0.046 vs −0.047, check −0.006 vs −0.003 —
  the same result.
- **Day cap 30** is account-side (not in the module); the uncapped run is reported as the counted diagnostic.
- **TX scoring unit.** TX45 R is per unit of actual risk (2R stop = 0.5 daily ATR), as bench.py's `cost_r` (÷ dn) and as
  live risk-based sizing books it. In 0.25-ATR units the TX figures are 2× (same sign); the selection consequence is
  shown under "Selection sensitivity" below (tier unchanged).
- **Costs:** LR8 research basis (entry (1c + 1bp) × tod mult; exit 1c + 1bp except target fills; +2c on stops); the
  intake's cost_r ≤ 0.10 uses the same stop-out round trip. No borrow fee (intraday; caveat), ETB not modelled.
- Point-in-time only: frames features are 5-minute bars closed at the decision bar (RSI5, dist_lod_atr = (close − low
  of day so far)/prior-day ATR, sma20_dist_pct = 5-min SMA20), prior-day ATR/ADV20, SPY via spy_fo at the same bar.
  The SPY up/flat/down label (09:30→15:59 ±0.30%) is used only for reporting.
- Survivorship: 1,226 lab symbols (today's list) — flatters longs; for a short it is roughly neutral-to-unfavourable.

## Data / halves / locked block
FIT = 2024-10 + 2025-03-01..2025-09-30 (170 sessions). CHECK = 2025-10-01..2026-11-04 (276 sessions, last cache day).
The locked block 2024-11-01..2025-02-28 was never scored: frames are loaded per open month only, 1-minute loads use
pyarrow filters that exclude it, and every frame / trade list / 1-minute load asserts no date in it. Disclosure: while
checking the 1-minute file format I opened SPY.parquet once without the filter and printed only its first 3 rows
(2024-09-16) and its last timestamp; no locked-block row was examined, computed on or scored.

## FIT half — all 8 grid configs (170 sessions; costs in)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 01a W13-R60-T | 437 | 2.57 | 0.467 | -0.110 | -0.130 | n/a (total<0) | -48.2 | -0.284 | -28.9 | 38 |
| 01b W13-R60-X | 430 | 2.53 | 0.472 | -0.075 | -0.086 | n/a | -32.3 | -0.190 | -21.1 | 45 |
| 01c W13-R70-T | 394 | 2.32 | 0.449 | -0.142 | -0.165 | n/a | -55.8 | -0.328 | -26.8 | 39 |
| 01d W13-R70-X | 390 | 2.29 | 0.451 | -0.099 | -0.111 | n/a | -38.4 | -0.226 | -18.7 | 45 |
| 01e W15-R60-T | 596 | 3.51 | 0.485 | -0.062 | -0.108 | n/a | -36.9 | -0.217 | -28.9 | 39 |
| **01f W15-R60-X** | 589 | 3.46 | 0.479 | -0.047 | -0.060 | n/a | **-27.4** | -0.161 | -21.1 | 45 |
| 01g W15-R70-T | 544 | 3.20 | 0.474 | -0.082 | -0.115 | n/a | -44.7 | -0.263 | -26.8 | 38 |
| 01h W15-R70-X | 538 | 3.16 | 0.461 | -0.066 | -0.078 | n/a | -35.7 | -0.210 | -18.7 | 45 |

SPY up / flat / down avg R (fit): 01a +0.004/−0.046/−0.164 · 01b +0.013/−0.031/−0.114 · 01c +0.029/−0.107/−0.200 ·
01d +0.020/−0.068/−0.141 · 01e −0.079/−0.026/−0.070 · **01f −0.050/+0.027/−0.072** · 01g −0.054/−0.062/−0.097 ·
01h −0.043/−0.001/−0.095. Avg R without the 2025-04-03..04-09 crash week: +0.043, +0.032, +0.016, +0.009, +0.056,
**+0.033**, +0.035, +0.011 — i.e. the fit losses sit in the crash week (shorting pops into the 04-09 squeeze), but the
pre-registered bar uses the whole half.

**Fit selection (PLAN sec. 5, frozen in `fitsel.json` before any check data was built):** all 8 configs reach ≥ 2
trades/session; highest fit total R = **01f W15-R60-X** (window 11:00-15:00, RSI5 ≥ 60, 45-min time exit with a 2R
catastrophic stop), −27.4R. It is also the best by avg R w/o best day (−0.060), so the task's "total R / avg R w/o best
day" reading picks the same config.
Selection sensitivity: scored in 0.25-ATR units instead of risk units, the TX configs' totals double (01f −54.8R) and
01e (t1s1, −36.9R) would be picked instead; 01e's check score is −0.013R (plateau table) — the tier is FAIL either way.

## CHECK half — the fit-selected config, scored ONCE (276 sessions)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 01f W15-R60-X | 1729 | 6.26 | 0.511 | **-0.003** | **-0.008** | n/a (total<0) | -5.6 | -0.020 | -9.1 | 45 |

- SPY day type (check): up −0.076 / flat −0.010 / **down +0.038** (regime dependence as every short fade in MCF).
- Check first half / second half: −0.012 / +0.005. Traded sessions 204 of 276; best day 2026-05-07.
- Monthly: Oct-25 +0.046, Nov −0.118, Dec −0.013, Jan-26 −0.024, Feb +0.002, Mar +0.032, Apr −0.045, May −0.056,
  Jun +0.034, Jul −0.028, Aug +0.049, Sep −0.070, **Oct-26 +0.159**, Nov (4 sessions) −0.029. The live Cell A evidence
  (Oct-Nov 2026) sits in the one strong month of the two years.

## Random-entry control (same symbol-sessions, random intake-U bar in the same window, same side and exit)

| half | ULT-01 01f avg R | random avg R | difference |
|---|---|---|---|
| FIT | -0.047 (589) | -0.107 (589) | +0.060 |
| CHECK | -0.003 (1729) | -0.069 (1729) | +0.066 |

The trigger (RSI5 pop + 0.5 ATR off the low + SMA20 band + SPY gate) adds a consistent ~+0.06R over a random bar in the
same gap-down name-sessions in BOTH halves — real selection value — but shorting gap-down names midday starts from a
base of about −0.07..−0.11R after costs, so the net stays at or below zero.

## Diagnostics (counted, never used for selection or the tier)
- Uncapped (no day cap), 01f: fit 1,312 trades, +0.047R, w/o best day +0.012, best-day share 0.79 **1 day**
  (the crash-week rebound days); check 1,917 trades, −0.011R, w/o best day −0.015. The fit "gain" is one-day noise.
- Module-chain refire (live thinning), 01f: fit −0.046R (589), check −0.006R (1,722).
- Check plateau (all 8 configs, diagnostic only): 01a −0.032, 01b −0.009, 01c −0.031, 01d −0.008, 01e −0.013,
  01f −0.003, 01g −0.008, 01h −0.004 (4.2-6.4 trades/session). No config is positive on check; TX ≥ t1s1 and
  W15 ≥ W13 in every pair on both halves (the two robust directions).

## Recorded-quote replay (third opinion)
Not run. The candidate already fails the fit half, so no replay result could change the tier; the recorded-quote
replay (research/reps2/nightly.py --replay) covers only 2026-11-18 so far (one session, ~1 h per run) — far too small
to rank anything, and it would be a fidelity check of a FAIL.

## Tier per PLAN sec. 6
| bar item | value | pass |
|---|---|---|
| check avg R > 0 | −0.003 | no |
| check avg R w/o best day > 0 | −0.008 | no |
| fit avg R > 0 | −0.047 | no |
| ≥ 2.0 trades/session on check | 6.26 | yes |
| no look-ahead | point-in-time features (code reviewed) | yes |
TIER B also needs fit avg R > 0 → **FAIL**. Benchmark (ST7-FD +0.262 R/session) not approached.

## Configurations tried
8 grid configs + 1 uncapped diagnostic (pre-registered) + 1 module-chain refire diagnostic = **10** (each scored on fit;
only 01f scored on check for the tier; the check plateau re-uses the same 8). Random controls are not candidates.
Prior evidence in this folder: 574 configs (live 230, movehunt long 104, short 240).

## What can be salvaged (optimistic, not inflated)
- The trigger's selection value (+0.06R over random, both halves) is real; what kills it is the short base rate in
  gap-down names on up/flat tapes. The only positive slice on check is SPY-down sessions (+0.038R) — an in-day
  "SPY already below its open" gate is exactly ULT-04's / ULT-10's routing, so this rule is a reasonable *component* of
  the down-tape branch there, not a standalone setup.
- Fades want room: the 45-min time exit with a 2R catastrophic stop beat t1s1 in every pair, both halves.
- The live Cell A record (+0.137R) is concentrated in Oct-Nov 2026; on two years the same condition is ≈ break-even.
  Per the owner ("I don't want to force weak setups"), nothing here should be deployed.

## Rule-change context (owner 2026-11-02)
The 2-year pipeline uses one fixed rule set; no live rule change falls inside its halves. The live evidence quoted in
the thesis (Cell A, Oct-Nov 2026) spans the LR8 live cost model start (2026-11-12 — also Cell A's best day, 69% share),
Testing 1/2 cost filter max_stop_cost_r 0.15 (10-30), Testing A-F half-size lots (11-17) and the SPYEXIT engine /
Workbench copies (11-17) (research/ledger.jsonl).

Files: `research/ultimate_1119/modules/ULT-01-gapdn-pop-fade-short.py`, and in
`research/ultimate_1119/ULT-01-gapdn-pop-fade-short/`: `bt.py`, `score.py`, `test_module.py`, `fitsel.json`,
`fit_grid.json`, `check_selected.json`, `RESULTS.md`.
