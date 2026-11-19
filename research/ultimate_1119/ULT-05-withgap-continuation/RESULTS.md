Educational only — not financial advice

# ULT-05 with-the-gap continuation (two-sided) — RESULTS: **FAIL**

Research only (ultimate_1119, PLAN.md sec. 3 "ULT-05"). No setup, exit, config or account change; nothing committed.

**Verdict: FAIL** under the pre-registered deploy bar (PLAN sec. 6). All 8 grid configs lose on the FIT half after costs
(best −0.011R/trade), so neither TIER A nor TIER B is reachable (both need fit avg R > 0). The fit-selected config
**05h G3-W14-X**, scored once on CHECK: **−0.003R/trade** (−0.006 without its best day), 20.6 trades/session, −15.3R.
It is not better than random entries in the same names on fit (−0.011 vs −0.006) and only marginally better on check
(−0.003 vs −0.010). The volume target is met easily; the edge is not there.

## What was built
- **Module (live interface):** `research/ultimate_1119/modules/ULT-05-withgap-continuation.py` — `SIDE`, `GEOM`,
  `LAYERS`, `mask(df)`, `stop_price(f, i)` (GEOM "S"), same interface as the deployed workbench modules
  (L3-gap-slope-rsi5hi-FD-WB5 pattern; SPY gate from the runner's `spy_fo` context column as RW3-WB3 / ULT-01).
  Constants = the fit-selected 05h (G 3%, window 10:15-14:00 bar close, EXIT "X").
  **Two sides, one file:** `LabStrategy` takes one side per setup (`self.mod.SIDE`), so the module derives its side from
  the setup name the engine loads it under (`lab_<name>`; a name ending `-S` / `-short` = short, anything else = long).
  An account would carry two entries on the same file, e.g. (NOT written into any config):
  `ULT-05-L: {type: lab, module: research/ultimate_1119/modules/ULT-05-withgap-continuation.py, min_adv: 20000000,
  window: [1015, 1400], context: [spy_fo], refire: true, refire_cooldown: 0, time_stop_min: 45, time_stop_min_r: 99}`
  and the same block as `ULT-05-S`. (geom "S" = 2R catastrophic stop, no target; `geom: t1s1` for the T variant.)
- **Smoke test:** `research/ultimate_1119/ULT-05-withgap-continuation/test_module.py` (2 passed): under
  `mcf.strategies.setups.LabStrategy` with SPY context, the `-L` setup fires long and the `-S` setup fires short on a
  synthetic with-gap day inside the window, at most 2 signals ≥ 75 min apart, t1s1 gives ±1R, geom S a 2R stop and no
  target, the wrong-side setup stays silent, and no SPY context → no signal.
- **Backtest:** `bt.py` (signals = the module's own `side_mask` on the lab frames for both sides, exits walked on 1-minute
  bars as benchmark/bench.py) and `score.py` (grid, frozen `fitsel.json`, single check score, random control,
  diagnostics). Trade lists stay in the scratchpad (26 MB, regenerable), not in the repo.

### Faithfulness notes (where a choice was open, and which way it leans)
- **"atrPct"** is read literally as the frame column `atrPct` = 5-minute ATR(14) % of price (≈0.45% median), so "near
  VWAP" = within ≈0.2% of VWAP on the gap side. Because the PLAN's ULT-07 uses `atrPct >= 3`, which only makes sense as
  a *daily* ATR %, the daily reading (within 0.5 × daily ATR% of VWAP, ≈1.6%) was run as one counted diagnostic on 05h
  (fit only): 3,340 trades, −0.010R (w/o best day −0.016), −32.4R — the same answer. The ambiguity does not matter.
- **Refire:** backtest = PLAN chassis (one lot per symbol, refire ≥ 30 min after the exit, max 2 per symbol-session).
  The module thins from bars alone (2nd hit ≥ 15 bars after the 1st, max 2); module-chain diagnostic: fit −0.010 vs
  −0.011, check −0.003 vs −0.003 — identical.
- **Day cap 30** (both sides together) is account-side; it binds hard on check (uncapped 34/session). Uncapped is the
  counted diagnostic (worse: fit −0.067, check −0.008).
- **TX45 R** is per unit of actual risk (2R stop = 0.5 daily ATR), as bench.py and ULT-01..04; in 0.25-ATR units the TX
  figures double (same sign). Under that unit 05h's fit total is −49.8R, still above
  05f −50.6, 05g −65.3 and 05e −71.4 → still the fit pick; tier unchanged.
- **Costs:** LR8 research basis (entry (1c + 1bp) × tod mult; exit 1c + 1bp except target fills; +2c on stops); intake
  cost_r ≤ 0.10 with the same stop-out round trip. Borrow fees not modelled (shorts; caveat); ETB not modelled.
- **Point-in-time:** gap (today's open vs prior close), vwapDistPct / atrPct / buyPressure (19-bar) / RSI5 from 5-min
  bars closed at the decision bar, prior-day ATR / ADV20, SPY since the 09:50 bar close from `spy_fo` at the same bar.
  The SPY up/flat/down label (09:30→15:59 ±0.30%) is reporting only. Code reviewed: no look-ahead.
- **Survivorship:** 1,226 lab symbols (today's list) — flatters the long side.

## Data / halves / locked block
FIT = 2024-10 + 2025-03-01..2025-09-30 (170 sessions). CHECK = 2025-10-01..2026-11-04 (276 sessions, last cache day).
The locked block 2024-11-01..2025-02-28 was never read: frames are loaded per open month only, 1-minute loads use
pyarrow filters that exclude it, every frame / trade list / 1-minute load asserts no date in it, MCF_HIST_ALLOW_LOCKED
never set.

## FIT half — all 8 grid configs (170 sessions; costs in)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 05a G2-W13-T | 3208 | 18.87 | 0.487 | −0.041 | −0.048 | n/a (total<0) | −130.9 | −0.770 | −26.3 | 45 |
| 05b G2-W13-X | 3172 | 18.66 | 0.480 | −0.017 | −0.022 | n/a | −53.6 | −0.315 | −17.8 | 45 |
| 05c G2-W14-T | 3510 | 20.65 | 0.485 | −0.040 | −0.046 | n/a | −139.7 | −0.822 | −26.3 | 45 |
| 05d G2-W14-X | 3487 | 20.51 | 0.477 | −0.019 | −0.023 | n/a | −66.0 | −0.388 | −17.8 | 45 |
| 05e G3-W13-T | 2007 | 11.81 | 0.488 | −0.036 | −0.047 | n/a | −71.4 | −0.420 | −28.2 | 45 |
| 05f G3-W13-X | 1966 | 11.56 | 0.483 | −0.013 | −0.021 | n/a | −25.3 | −0.149 | −18.2 | 45 |
| 05g G3-W14-T | 2250 | 13.24 | 0.491 | −0.029 | −0.039 | n/a | −65.3 | −0.384 | −28.2 | 45 |
| **05h G3-W14-X** | 2218 | 13.05 | 0.486 | −0.011 | **−0.019** | n/a | **−24.9** | −0.147 | −18.2 | 45 |

SPY up / flat / down avg R (fit): 05a −0.010/−0.090/−0.024 · 05b +0.000/−0.046/−0.006 · 05c −0.016/−0.080/−0.021 ·
05d −0.003/−0.046/−0.006 · 05e +0.002/−0.117/−0.001 · 05f +0.022/−0.062/−0.005 · 05g +0.003/−0.106/+0.011 ·
**05h +0.021/−0.061/+0.002**. Flat sessions are the weak spot in every config (continuation needs a trending day).
Avg R ex the 2025-04-03..04-09 crash week: −0.039, −0.011, −0.038, −0.014, −0.039, −0.008, −0.032, **−0.007** — not a
crash-week artefact.

Side split (diagnostic only; both sides always traded together):

| config | long trades / avg R / sum | short trades / avg R / sum |
|---|---|---|
| 05a | 1860 / −0.061 / −113.3 | 1348 / −0.013 / −17.6 |
| 05b | 1835 / −0.030 / −55.5 | 1337 / +0.001 / +1.9 |
| 05c | 2043 / −0.057 / −116.1 | 1467 / −0.016 / −23.6 |
| 05d | 2028 / −0.031 / −63.6 | 1459 / −0.002 / −2.4 |
| 05e | 1168 / −0.071 / −82.6 | 839 / +0.013 / +11.3 |
| 05f | 1142 / −0.030 / −33.8 | 824 / +0.010 / +8.5 |
| 05g | 1320 / −0.059 / −77.6 | 930 / +0.013 / +12.3 |
| 05h | 1299 / −0.026 / −33.2 | 919 / +0.009 / +8.3 |

**Fit selection (PLAN sec. 5, frozen in `fitsel.json` at 2026-11-19T05:21:56Z before any check data was built):**
all 8 configs reach ≥ 2 trades/session; highest fit total R = **05h G3-W14-X** (−24.9R; 05f −25.3R is a near tie). It
is also the best by avg R w/o best day (−0.019), so the task's "total R / avg R w/o best day" reading picks the same.

## CHECK half — the fit-selected config, scored ONCE (276 sessions)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 05h G3-W14-X | 5688 | 20.61 | 0.498 | **−0.003** | **−0.006** | n/a (total<0) | −15.3 | −0.055 | −14.4 | 45 |

- Side split (check): long 3,349 trades +0.005 (+18.1R) / short 2,339 trades −0.014 (−33.4R) — the sides swapped
  sign versus fit (fit: long −0.026, short +0.009). No side carries a stable edge.
- SPY day type (check): up −0.003 / flat −0.001 / down −0.006 — flat across regimes, but flat around zero.
- Check first half / second half: −0.029 / +0.018. Traded sessions 274 of 276; best day 2026-11-04 (the last cache
  day; the 4 November sessions together +19.9R in 83 trades).
- Monthly avg R: Oct-25 −0.052, Nov −0.037, Dec −0.045, Jan-26 −0.026, Feb −0.018, Mar −0.030, Apr +0.030,
  May +0.066, Jun +0.019, Jul −0.059, Aug +0.014, Sep −0.012, Oct +0.032, Nov (4 sessions) +0.240. Six of the first six
  check months negative; the recent run is positive but short.

## Random-entry control (same symbol-sessions and side, random intake-U bar in 10:15-14:00, same exit)

| half | ULT-05 05h avg R | random avg R | difference |
|---|---|---|---|
| FIT | −0.011 (2218) | −0.006 (2218) | **−0.005** |
| CHECK | −0.003 (5688) | −0.010 (5688) | +0.007 |

The VWAP-hold + buy-pressure + tape layers add essentially nothing over a random bar in the same with-gap name-sessions
(negative on fit, +0.007 on check). The PLAN flagged this as the weak point ("the with-gap baseline is only about flat,
so the VWAP-hold and tape layers must add the edge"); they do not.

## Diagnostics (counted, never used for selection or the tier)
- Uncapped (no day cap), 05h: fit 4,079 trades (24.0/session), −0.067R, worst day −171.4R (crash week); check 9,438
  trades (34.2/session), −0.008R, w/o best day −0.011. The day cap helps; no hidden edge in the capped-out trades.
- Module-chain refire (live thinning), 05h: fit −0.010R (2,216), check −0.003R (5,685).
- Daily-ATR reading of "near VWAP", 05h, fit only: −0.010R (3,340 trades), w/o best day −0.016.
- Check plateau (all 8 configs, diagnostic only, never used to re-select):

| config | check trades | /session | avg R | avg R w/o best day | best-day share | total R | R/session |
|---|---|---|---|---|---|---|---|
| 05a G2-W13-T | 7144 | 25.88 | +0.011 | +0.008 | 0.31 | +80.4 | +0.291 |
| 05b G2-W13-X | 7108 | 25.75 | +0.009 | +0.006 | 0.36 | +67.5 | +0.244 |
| 05c G2-W14-T | 7375 | 26.72 | +0.010 | +0.006 | 0.35 | +71.6 | +0.259 |
| 05d G2-W14-X | 7348 | 26.62 | +0.009 | +0.006 | 0.37 | +66.8 | +0.242 |
| 05e G3-W13-T | 5426 | 19.66 | −0.008 | −0.013 | n/a | −45.1 | −0.163 |
| 05f G3-W13-X | 5371 | 19.46 | −0.003 | −0.006 | n/a | −15.8 | −0.057 |
| 05g G3-W14-T | 5736 | 20.78 | −0.009 | −0.013 | n/a | −51.2 | −0.186 |
| 05h G3-W14-X | 5688 | 20.61 | −0.003 | −0.006 | n/a | −15.3 | −0.055 |

  The G 2% configs are slightly positive on check (+0.009..+0.011R, +0.24..+0.29 R/session, no 1-day tag) but were the
  *worst* on fit (−0.017..−0.041). That is the Wave 1 pattern (sign flips between halves; selection noise), not a
  plateau, and per the pre-registration it cannot be used to re-select. +0.01R/trade is also well inside cost-model
  error (a 1c worse fill per side ≈ −0.01..−0.02R at these R sizes).

## Recorded-quote replay (third opinion): not run
The candidate fails the fit half, so no replay can change the tier, and the recorded-quote packs
(research/reps2/replay_quotes) hold one session (2026-11-18) — too few trades to say anything.

## Tier per PLAN sec. 6
| bar item | value | pass |
|---|---|---|
| check avg R > 0 | −0.003 | no |
| check avg R w/o best day > 0 | −0.006 | no |
| fit avg R > 0 | −0.011 | no |
| ≥ 2.0 trades/session on check | 20.61 | yes |
| no look-ahead | point-in-time features (code reviewed) | yes |
TIER B also needs fit avg R > 0 → **FAIL**. Benchmark (ST7-FD +0.262 R/session, +0.073 w/o best day) not approached.

## Configurations tried
8 grid configs + 1 uncapped diagnostic (pre-registered) + 1 module-chain refire diagnostic + 1 daily-ATR "near VWAP"
diagnostic = **11** (all scored on fit; only 05h scored on check for the tier; the check plateau re-uses the same 8).
Random controls are not candidates. Prior evidence in this folder: 574 configs (live 230, movehunt long 104, short 240).

## What can be salvaged (optimistic, not inflated)
- **Volume is not the problem:** 13-21 trades/session across the universe on both sides with costs ≤ 0.10R — this
  intake (|gap| ≥ 2-3%, cost filter, 10:15-14:00) is a good *universe* for the next mechanism to sit on.
- **TX45 beat t1s1 in all 4 pairs on fit** (on check only in the two G 3% pairs; at G 2% t1s1 edged it, +0.011 vs +0.009): with-gap names want room, like the fades.
- **Flat SPY sessions are the drag on fit** (−0.06..−0.12R in every config); a continuation rule needs a trending tape.
  An in-day "trend day so far" measure (e.g. SPY |since 09:30| or the name's own range expansion by 10:15) is the
  targeted next layer to test — a pre-registered round, not a re-tune of this one.
- The with-gap base rate (random control −0.006 / −0.010) is about flat after costs, confirming the archive; it beats
  fading gaps, but this pullback-to-VWAP trigger does not lift it. Per the owner ("I don't want to force weak setups"),
  nothing here should be deployed.

## Rule-change context (owner 2026-11-02)
The 2-year pipeline uses one fixed rule set; no live rule change applies inside its halves. The live evidence quoted in
the thesis spans live rule changes recorded in research/ledger.jsonl (Testing 1/2 cost filter max_stop_cost_r 0.15 from
10-30, LR8 live cost model from 11-12, Testing A-F half-size lots and the SPYEXIT engine / Workbench copies from 11-17).

Files: `research/ultimate_1119/modules/ULT-05-withgap-continuation.py`, and in
`research/ultimate_1119/ULT-05-withgap-continuation/`: `bt.py`, `score.py`, `test_module.py`, `fitsel.json`,
`fit_grid.json`, `check_selected.json`, `RESULTS.md`.
