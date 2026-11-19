Educational only — not financial advice

# ULT-08 afternoon overbought roll-over short — RESULTS: **FAIL**

Research only (ultimate_1119, PLAN.md sec. 3 "ULT-08"). No setup, exit, config or account change; nothing committed.

**Verdict: FAIL** under the pre-registered deploy bar (PLAN sec. 6). The rule is thin: no grid config reaches
2 trades/session on fit (best 0.94). The fit-selected config **08g (RUN 2.0 ATR, RSI_MIN 85, TX20)** was positive on
fit (+0.052R/trade, +0.027 without its best day, but only 57 trades / 0.34 per session, best-day share 76% = **1 day**)
and scored once on CHECK is **−0.053R/trade, −0.062 without best day, 0.45 trades/session, −6.6R total**. That misses
TIER A (check > 0, ≥ 2/session) and TIER B (check > −0.02). It still beats random entries in the same symbol-sessions on
both halves (check by +0.03R/trade), but random afternoon shorts in these names lose, so beating them is not enough.
As the PLAN expected: weakest-evidence candidate, FAIL.

## What was built
- **Module (live interface):** `research/ultimate_1119/modules/ULT-08-pm-overbought-rollover-short.py` — `SIDE`,
  `GEOM = "S"`, `LAYERS`, `mask(df)`, `stop_price(f, i)` (2R catastrophic stop above the decision close), same
  interface as the deployed workbench modules (L3-gap-slope-rsi5hi-FD-WB5) and ULT-04/07. Constants set to the
  fit-selected 08g. YAML block it would load with (NOT written into any config): `type: lab, module:
  research/ultimate_1119/modules/ULT-08-pm-overbought-rollover-short.py, side: short, geom: S, min_adv: 20000000,
  window: [1400, 1500], context: [spy_fo], refire: true, refire_cooldown: 0, time_stop_min: 20, time_stop_min_r: 99`.
- **Smoke test:** `research/ultimate_1119/ULT-08-pm-overbought-rollover-short/test_module.py` (passes): runs inside
  `mcf.strategies.setups.LabStrategy` with SPY context and geom S; fires short inside 14:00-15:00 on a synthetic
  extended name rolling over on a falling tape (2R stop, no target); no signal without SPY context, on a rising tape,
  or on a +1% gap-up day.
- **Backtest:** `bt.py` / `score.py` (adapted from ULT-04: signals = the module's own `mask` on the lab frames with
  superset params RUN 1.5 / RSI_MIN 80, each config a sub-filter; exits walked on 1-minute bars as benchmark/bench.py;
  LR8 costs; chassis one lot per symbol, refire ≥ 30 min after exit, max 2 per symbol-session, day cap 30).
  Outputs: `fitsel.json` (frozen), `fit_grid.json`, `check_selected.json`. Trade lists stayed in the scratchpad
  (< 1 MB) and were deleted.

### Faithfulness notes (where the PLAN text had to be interpreted)
- **Window:** PLAN 14:00-15:20, but the lab frames and the live LabStrategy both stop at the 15:00 bar close
  (setups.py clamps tod ≤ 1500), so the effective window is 14:00-15:00 live and in the backtest. Flat by 15:50 holds
  (last entry 15:00 + 30 min).
- **"RSI5 now lower (rsiSlope < 0)":** implemented as RSI(5) now < RSI(5) on the previous bar (exactly 5 min earlier,
  same session), with the previous bar ≥ RSI_MIN. The frame column `rsiSlope` is the 3-bar RSI(14) change, not an
  RSI5 slope; the thesis says "RSI5 turning down", so the RSI5 reading was used.
- `upper_wick` = upper-wick share of the decision 5-min bar (frame column; > 0 on ~75% of bars, so a weak filter).
- spy_r30 = (1 + spy_fo_t)/(1 + spy_fo_t−6 bars) − 1, NaN (no fire) unless the row 6 back is the same symbol-day
  exactly 30 min earlier (the 14:00 bar always has it). from_open_atr = (close − 09:30 open)/prior-day daily ATR.
- TX R is per unit of actual risk (2R stop) as ULT-01/04 and bench.py (live risk-based sizing); in 0.25-ATR units every
  figure is 2x. Costs LR8 (entry (1c+1bp) × tod mult; exit 1c+1bp; +2c on stops). No borrow fee (caveat; costlier
  in reality for hard-to-borrow extended names). Survivorship: today's 1,226-symbol list.
- Refire: backtest uses the PLAN chassis; the module thins from bars alone (2nd hit ≥ (hold + 30)/5 bars after the
  1st). Module-chain diagnostic identical on fit and check.

## Data / halves / locked block
FIT = 2024-10 + 2025-03-01..2025-09-30 (170 sessions). CHECK = 2025-10-01..2026-11-04 (276 sessions). The locked block
2024-11-01..2025-02-28 was never read: frames loaded per open month only, 1-minute loads use pyarrow filters that
exclude it, every frame / trade list / 1-minute load asserts no date in it. `fitsel.json` frozen at
2026-11-19T05:34:28Z; check data first built at 05:34:39Z.

## Why so few trades (gate funnel, 2025-07, 14:00-15:00 bars)
136,584 intake-U rows → gap ≤ +0.5% 101,112 → SPY 30-min ≤ 0 39,336 → from_open_atr ≥ 1.5: **449** (≥ 2.0: 134) →
prev RSI5 ≥ 80: 86 → RSI5 turning down: 50 → upper wick: 41. A name up ≥ 1.5 daily ATR from the open in the
afternoon while SPY is flat-to-falling and the name did not gap up is rare (~2 per session before RSI/refire). The
PLAN's ~3-10/session was too optimistic by ~3-10x.

## FIT half — all 8 grid configs (170 sessions; costs in)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 08a RUN1.5-R80-X20 | 160 | 0.94 | 0.469 | -0.015 | -0.022 | n/a | -2.4 | -0.014 | -2.0 | 20 |
| 08b RUN1.5-R80-X30 | 159 | 0.94 | 0.346 | -0.081 | -0.091 | n/a | -12.9 | -0.076 | -9.4 | 30 |
| 08c RUN1.5-R85-X20 | 141 | 0.83 | 0.489 | -0.005 | -0.021 | n/a | -0.8 | -0.005 | -2.0 | 20 |
| 08d RUN1.5-R85-X30 | 140 | 0.82 | 0.364 | -0.081 | -0.092 | n/a | -11.3 | -0.067 | -8.9 | 30 |
| 08e RUN2-R80-X20 | 60 | 0.35 | 0.567 | +0.014 | -0.001 | 1.10 **1 day** | +0.8 | +0.005 | -2.0 | 20 |
| 08f RUN2-R80-X30 | 60 | 0.35 | 0.267 | -0.173 | -0.200 | n/a | -10.4 | -0.061 | -9.9 | 30 |
| **08g RUN2-R85-X20** | 57 | 0.34 | 0.649 | +0.052 | +0.027 | 0.76 **1 day** | **+3.0** | +0.018 | -2.0 | 20 |
| 08h RUN2-R85-X30 | 57 | 0.34 | 0.298 | -0.130 | -0.158 | n/a | -7.4 | -0.044 | -8.3 | 30 |

Selection (PLAN sec. 5): no config ≥ 2/session → highest fit total R = **08g** (+3.0R; TIER B at best). Traded on 21 of
170 sessions; best day 2025-04-09 (76% of total R); avg ex-April 3-9 +0.110. 105 of the 266 superset fit signals fell
in April 2025. Fit SPY up/flat/down avg R (08g, end-of-day label, reporting only): +0.093 / −0.065 / +0.047.
Fit gross (before costs) +0.073R/trade, costs 0.021R/trade.
Diagnostics (counted, not used): uncapped 62 trades, +0.048 (the day cap bound on one April day); module-chain identical.

## CHECK half — fit-selected 08g, scored once (276 sessions)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 08g RUN2-R85-X20 | 125 | 0.45 | 0.400 | **-0.053** | **-0.062** | n/a (total < 0) | -6.6 | -0.024 | -1.7 | 20 |

- SPY up / flat / down avg R: **−0.032 / −0.067 / −0.048** — negative on every day type.
- Check first half −0.091, second half +0.013. Traded on 67 sessions; best day 2026-06-29. Gross −0.028R/trade, costs
  0.024R/trade (the signal is negative before costs). January 2026 alone −4.8R (39 trades).
- Diagnostics (counted, not used): uncapped identical; module bar-only refire chain identical.

## Random-entry control (same symbol-sessions, random intake-U bar in 14:00-15:00, same side and exit)
| half | trades | avg R | avg R w/o best day | total R |
|---|---|---|---|---|
| fit | 57 | −0.157 (signal +0.052) | −0.172 | −8.9 |
| check | 125 | −0.083 (signal −0.053) | −0.104 | −10.4 |
The roll-over trigger (RSI5 turning down from ≥ 85, upper wick) does help versus shorting the same extended names at a
random afternoon bar (+0.21 fit, +0.03 check), but the baseline is so negative (extended names keep drifting up into
the close) that the trigger only shrinks the loss on check.

## Check plateau (diagnostic only, never used to re-select)
All 8 configs negative on check (−0.036..−0.060R/trade, every w/o-best-day negative, 0.45-1.57/session). The broadest
08a is −0.040 (−17.4R); the least-bad by total R is 08h RUN2-R85-X30 −5.2R. No neighbour of 08g survives.

## What the numbers say (optimistic read, honestly scored)
- The idea has a real but small *relative* signal: on both halves the confirmed roll-over beats a random entry on the
  same name/session. The problem is the absolute level: afternoon shorts of names up ≥ 1.5-2 ATR lose on average
  (random −0.08..−0.16R), consistent with the movehunt-short finding (extension predicts volatility, not direction).
- Fit 08g was a one-day record (2025-04-09, 76%) on 57 trades; the TX30 twins were deeply negative on fit, i.e. the
  "edge" lived in the first 20 minutes and in the tariff week. Check confirmed it did not generalise.
- Possible next-round ideas (backlog only, not tested; would be new configurations): use the trigger as a relative
  filter on a short book whose baseline is already positive (e.g. gap-down / down-tape names, ULT-01 / ULT-04
  universes) rather than on extended up-names; or as an exit signal for existing longs (sell the roll-over) instead of
  an entry.

## Recorded-quote replay (third opinion): not run
The candidate fails the check half and trades ~0.45 times per session in a 14:00-15:00 window; the replay of recent
live sessions (research/reps2/nightly.py --replay) would yield a handful of trades and cannot change the tier.

## Configurations tried
8 grid configs (fit) + 2 diagnostics on the fit-selected config (uncapped, module-chain) = **10** counted for ULT-08;
1 check score of 08g; 8 check plateau rows (diagnostic) and 2 random controls (not candidates). Program total per
PLAN sec. 4: 94 configs plus 574 evidence configs.

## Rule-change context
Backtest only on the 2-year cache (2024-10..2026-11-04); no live trades of this rule exist, so no live rule / sizing
change (e.g. TSZ1 testing-account sizing from 2026-11-17) affects these figures.
