Educational only — not financial advice

# ULT-04 down-tape pop fade short — RESULTS: **FAIL**

Research only (ultimate_1119, PLAN.md sec. 3 "ULT-04"). No setup, exit, config or account change; nothing committed.

**Verdict: FAIL** under the pre-registered deploy bar (PLAN sec. 6). The rule as written is very thin: no grid config
reaches 2 trades/session on fit (best 1.42). The fit-selected config **04j (SPY_T −0.50%, RSI_MIN 80, t1s1 cap45)**
was barely positive on fit (+0.023R/trade, −0.034 without its best day, 0.44 trades/session) and scored once on CHECK
is **−0.078R/trade, −0.129 without best day, 0.41 trades/session, −8.8R total**. That misses TIER A (needs check > 0
and ≥ 2/session) and TIER B (needs check > −0.02). Random entries in the same symbol-sessions beat it on both halves.

## What was built
- **Module (live interface):** `research/ultimate_1119/modules/ULT-04-downtape-pop-fade-short.py` — `SIDE`, `GEOM`,
  `LAYERS`, `mask(df)`, `stop_price(f, i)` (GEOM "S" for the TX exits), same interface as the deployed workbench
  modules (L3-gap-slope-rsi5hi-FD-WB5) and ULT-01. SPY gates come from the runner's `spy_fo` context column
  (SPY % from its 09:30 open = spy_s930); spy_r30 = (1 + fo_t)/(1 + fo_t−6 bars) − 1, NaN (no fire) unless the
  row 6 back is the same symbol-day exactly 30 minutes earlier. Constants set to the fit-selected 04j.
  YAML block it would load with (NOT written into any config): `type: lab, module:
  research/ultimate_1119/modules/ULT-04-downtape-pop-fade-short.py, min_adv: 20000000, window: [1030, 1430],
  context: [spy_fo], refire: true, refire_cooldown: 0, time_stop_min: 45, time_stop_min_r: 99` (TX30/TX45 variants:
  `geom: S`, time_stop_min 30/45).
- **Smoke test:** `research/ultimate_1119/ULT-04-downtape-pop-fade-short/test_module.py` (passes): runs inside
  `mcf.strategies.setups.LabStrategy` with SPY context, fires inside the window on a synthetic weak-name pop on a
  falling tape, t1s1 gives ±1R levels, geom S gives a 2R stop and no target, fails safe without SPY context and gives
  no signal on a rising tape.
- **Backtest:** `bt.py` / `score.py` (adapted from ULT-01: signals = the module's own `mask` on the lab frames with
  superset params SPY_T −0.30 / RSI 70, each config a sub-filter; exits walked on 1-minute bars as benchmark/bench.py;
  LR8 costs; chassis one lot per symbol, refire ≥ 30 min after exit, max 2 per symbol-session, day cap 30).
  Trade lists stay in the scratchpad (< 1 MB, regenerable).

### Faithfulness notes
- Refire: backtest uses the PLAN chassis; the live module thins from bars alone (2nd hit ≥ 15 bars after the 1st for
  T/X45, 12 bars for X30). Module-chain diagnostic = identical result (fit and check).
- Day cap 30 never bound (uncapped diagnostic = identical).
- TX R is per unit of actual risk (2R stop), as ULT-01/bench.py. The selected config is t1s1, so this does not affect
  selection; in 0.25-ATR units every TX config is still negative on fit.
- Point-in-time only: RSI5 (simple 5-period on 5-min closes), sma20_dist_pct (5-min SMA20), gap, prior-day ATR/ADV20,
  SPY via spy_fo at the same bar close. SPY up/flat/down labels (09:30→15:59 ±0.30%) are used for reporting only.
- Costs LR8 (entry (1c+1bp) × tod mult; exit 1c+1bp except target fills; +2c on stops). No borrow fee (caveat).
- Survivorship: today's 1,226-symbol list (roughly neutral-to-unfavourable for a short).

## Data / halves / locked block
FIT = 2024-10 + 2025-03-01..2025-09-30 (170 sessions). CHECK = 2025-10-01..2026-11-04 (276 sessions). The locked block
2024-11-01..2025-02-28 was never read: frames loaded per open month only, 1-minute loads use pyarrow filters that
exclude it, every frame / trade list / 1-minute load asserts no date in it. `fitsel.json` was frozen at
2026-11-19T05:13:54Z; the first check data were built at 05:14:38Z.

## Why so few trades (gate funnel, 2025-04, 10:30-14:30 intake-U rows)
787,314 intake rows → SPY ≤ −0.30% from open 287,162 → SPY 30-min ≤ 0 185,836 → gap ≤ +0.5% 120,577 → ≥ 1.5% below
SMA20 13,938 → RSI5 70-90 **175**. An overbought 5-bar pop almost always lifts the close back toward its 100-min SMA20,
so "RSI5 ≥ 70 AND ≥ 1.5% below SMA20" is a near-contradiction. The PLAN's ~4-8/session expectation was wrong by ~10×.

## FIT half — all 12 grid configs (170 sessions; costs in)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 04a S30-R70-T | 241 | 1.42 | 0.527 | -0.003 | -0.053 | n/a | -0.6 | -0.004 | -9.9 | 44 |
| 04b S30-R70-X30 | 240 | 1.41 | 0.517 | -0.018 | -0.062 | n/a | -4.2 | -0.025 | -17.7 | 30 |
| 04c S30-R70-X45 | 240 | 1.41 | 0.483 | -0.070 | -0.107 | n/a | -16.7 | -0.098 | -18.9 | 45 |
| 04d S30-R80-T | 93 | 0.55 | 0.527 | +0.005 | -0.041 | 7.68 **1 day** | +0.5 | +0.003 | -3.4 | 37 |
| 04e S30-R80-X30 | 93 | 0.55 | 0.505 | -0.026 | -0.063 | n/a | -2.4 | -0.014 | -5.5 | 30 |
| 04f S30-R80-X45 | 93 | 0.55 | 0.452 | -0.115 | -0.153 | n/a | -10.7 | -0.063 | -6.9 | 45 |
| 04g S50-R70-T | 190 | 1.12 | 0.521 | -0.056 | -0.133 | n/a | -10.6 | -0.062 | -9.9 | 44 |
| 04h S50-R70-X30 | 190 | 1.12 | 0.500 | -0.065 | -0.104 | n/a | -12.3 | -0.072 | -17.7 | 30 |
| 04i S50-R70-X45 | 190 | 1.12 | 0.468 | -0.129 | -0.181 | n/a | -24.5 | -0.144 | -18.9 | 45 |
| **04j S50-R80-T** | 74 | 0.44 | 0.568 | +0.023 | -0.034 | 2.21 **1 day** | **+1.7** | +0.010 | -3.5 | 40 |
| 04k S50-R80-X30 | 74 | 0.44 | 0.527 | -0.018 | -0.064 | n/a | -1.3 | -0.008 | -5.5 | 30 |
| 04l S50-R80-X45 | 74 | 0.44 | 0.514 | -0.096 | -0.144 | n/a | -7.1 | -0.042 | -6.9 | 45 |

Selection (PLAN sec. 5): no config ≥ 2/session → highest fit total R = **04j** (+1.7R; TIER B at best). Its positive
fit total is carried by one day (2025-04-10, share 221%); traded on 19 of 170 sessions; avg ex-April 3-9 +0.143.
Every config's avg R without its best day is negative on fit.
Fit SPY up/flat/down avg R (04j): −0.354 (n 1) / +0.026 (n 9) / +0.028 (n 64).

## CHECK half — fit-selected 04j, scored once (276 sessions)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 04j S50-R80-T | 113 | 0.41 | 0.478 | **-0.078** | **-0.129** | n/a (total < 0) | -8.8 | -0.032 | -13.2 | 45 |

- SPY up / flat / down avg R: **−0.839 (n 17) / −0.546 (n 3) / +0.077 (n 93)**. Traded on 33 sessions; best day
  2026-02-23; check first half −0.098, second half −0.003. March 2026 alone −12.5R (23 trades).
- Diagnostics (counted, not used): uncapped = identical; module bar-only refire chain = identical.

## Random-entry control (same symbol-sessions, random intake-U bar in 10:30-14:30, same side and exit)
| half | trades | avg R | avg R w/o best day | total R |
|---|---|---|---|---|
| fit | 74 | +0.056 (signal +0.023) | +0.003 | +4.1 |
| check | 113 | +0.034 (signal −0.078) | +0.001 | +3.8 |
The trigger (RSI5 80-90 pop) adds nothing over shorting the same weak names at a random time on the same sessions;
on check it is 0.11R/trade worse.

## Check plateau (diagnostic only, never used to re-select)
All 12 configs negative on check (−0.029..−0.088R/trade, every w/o-best-day negative). Best by total R: 04e S30-R80-X30
−5.7R. The broadest config 04a (1.96/session) is −0.055 (−29.6R).

## What the numbers say (optimistic read, honestly scored)
- The down-session thesis itself is not dead: on sessions that END down (end-of-day label, not tradable at entry)
  the shorts made +0.028 (fit) and +0.077 (check, n 93) for 04j, and +0.067 for 04a (n 424, check).
- The loss is all on sessions where SPY was down ≥ 0.3-0.5% from the open in mid-session and then **reversed** to
  finish flat/up: 04j −0.84R/trade on 17 such check trades, 04a −0.86 on 40 up-day trades and −0.31 on 77 flat-day.
  The in-day "down tape" state does not forecast the rest of the session well enough; the shorts sit right in the
  reversal (confirms "day-type forecasts fail" — the point-in-time version of the day type also fails here).
- Possible next-round ideas (backlog only, not tested, would be new configurations): a later window (time of day is
  the most persistent condition) where an established down tape reverses less often; a tape-reversal exit (flatten
  when SPY reclaims a fraction of its drop, as RW3-WB4 SPYEXIT); drop the SMA20 ≤ −1.5% gate (the near-contradiction
  with RSI5 ≥ 70) or replace it with distance-from-open in ATR units to get volume.

## Recorded-quote replay (third opinion): not run
The candidate fails the check half and trades ~0.4 times per session, so the replay of the recent live sessions
(research/reps2/nightly.py --replay; session packs available for very few days, ~1 h per run) would yield a handful
of trades at most and cannot change the tier.

## Configurations tried
12 grid configs (fit) + 2 diagnostics on the fit-selected config (uncapped, module-chain) = **14** counted for ULT-04;
1 check score of 04j; 12 check plateau rows (diagnostic) and 2 random controls (not candidates). Program total per
PLAN sec. 4: 94 configs plus 574 evidence configs.

## Rule-change context
Backtest only on the 2-year cache (2024-10..2026-11-04); no live trades of this rule exist, so no live rule / sizing
change (e.g. TSZ1 testing-account sizing from 2026-11-17) affects these figures.
