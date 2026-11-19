Educational only — not financial advice

# ULT-09 failed VWAP reclaim short on a weak tape — RESULTS: **FAIL**

Research only (ultimate_1119, PLAN.md sec. 3 "ULT-09"). No setup, exit, config or account change; nothing committed.

**Verdict: FAIL** under the pre-registered deploy bar (PLAN sec. 6). No grid config reaches 2 trades/session on fit
(best 1.71). The fit-selected config **09c (SPY since 09:50 ≤ −0.20%, window 10:30-15:20 → 15:00, t1s1 cap45)** was
positive on fit only because of one session (+0.067R/trade, **+0.012 without its best day, best-day share 85%**,
1.01 trades/session). Scored once on CHECK it is **−0.157R/trade, −0.185 without best day, 1.17 trades/session,
−50.6R total**. That misses TIER A (check > 0, ≥ 2/session) and TIER B (check > −0.02). Random entries on the same
symbol-sessions lose less (−0.070 on check), so the failed-reclaim trigger adds negative value on check.

## What was built
- **Module (live interface):** `research/ultimate_1119/modules/ULT-09-failed-vwap-reclaim-short.py` — `SIDE`, `GEOM`,
  `LAYERS`, `mask(df)`, `stop_price(f, i)` (GEOM "S" for TX45), same interface as the deployed workbench modules
  (L3-gap-slope-rsi5hi-FD-WB5) and ULT-01/04. Constants set to the fit-selected 09c. SPY gate from the runner's
  `spy_fo` context column (SPY since 09:50 = (1+fo)/(1+fo@09:50) − 1, NaN → no fire without a 09:50 row). The
  "closed above VWAP on one of the previous 3 bars" test uses `vwapDistPct > 0` on lags 1-3 of the same symbol-day,
  each required to be exactly 5/10/15 min earlier. Refire thinned from bars alone (2nd hit ≥ 15 bars after the 1st,
  max 2). YAML it would load with (NOT written into any config): `type: lab, module:
  research/ultimate_1119/modules/ULT-09-failed-vwap-reclaim-short.py, min_adv: 20000000, window: [1030, 1500],
  context: [spy_fo], refire: true, refire_cooldown: 0, time_stop_min: 45, time_stop_min_r: 99` (TX45: `geom: S`).
- **Smoke test:** `research/ultimate_1119/ULT-09-failed-vwap-reclaim-short/test_module.py` (passes): runs inside
  `mcf.strategies.setups.LabStrategy` with SPY context on a synthetic weak name (run-up, heavy-volume slide, 3-bar poke
  above VWAP, failure below VWAP while below the open and > 1.5% under the 5-min SMA20); fires once at the failure bar,
  t1s1 gives ±1R, geom S gives a 2R stop and no target; no signal without SPY context or on a rising tape.
- **Backtest:** `bt.py` / `score.py` (adapted from ULT-04: signals = the module's own `mask` on the lab frames with
  superset params S_T 0.00 / W 1030-1500, each config a sub-filter; exits walked on 1-minute bars as
  benchmark/bench.py; LR8 costs; chassis one lot per symbol, refire ≥ 30 min after exit, max 2 per symbol-session,
  day cap 30). Trade lists stay in the scratchpad (1.5 MB, regenerable).

### Faithfulness notes
- **Window end 15:20 → 15:00:** the lab frames and the live LabStrategy only evaluate decision bars 09:50-15:00, so the
  W 1030-1520 configs are effectively 10:30-15:00 (that is what the module can do live). Rule otherwise built as written.
- Refire: module bar-only chain = identical to the PLAN chassis (fit and check).
- Day cap 30 binds on a few sessions (fit 2025-04-03/04, check 2026-02-17 and 2026-03-03): uncapped diagnostic fit
  +0.230 (280 trades; the extra trades are almost all on 2025-04-03), check −0.177 (336).
- TX R is per unit of actual risk (2R stop), as bench.py and ULT-01/04. The selected config is t1s1.
- Point-in-time only: vwapDistPct, fromOpen, sma20_dist_pct (5-min SMA20), RSI5, gap, prior-day ATR/ADV20, SPY via
  spy_fo at the same bar close. The frames' end-of-trade label columns (win_*/r_*) are never read. SPY up/flat/down
  labels (09:30→15:59 ±0.30%) are for reporting only.
- Costs LR8. No borrow fee (caveat). Survivorship: today's 1,226-symbol list (roughly neutral-to-unfavourable for a short).

## Data / halves / locked block
FIT = 2024-10 + 2025-03-01..2025-09-30 (170 sessions). CHECK = 2025-10-01..2026-11-04 (275 sessions). The locked block
2024-11-01..2025-02-28 was never read (frames per open month only, pyarrow filters on 1-minute loads, asserts on every
frame / trade list / 1-minute load). `fitsel.json` frozen at 2026-11-19T05:40:44Z; check data first built at 05:41:00Z.

## FIT half — all 8 grid configs (170 sessions; costs in)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 09a S−20-W1400-T | 165 | 0.97 | 0.570 | +0.061 | +0.002 | 0.98 **1 day** | +10.0 | +0.059 | −6.4 | 45 |
| 09b S−20-W1400-X | 165 | 0.97 | 0.515 | −0.029 | −0.069 | n/a | −4.8 | −0.028 | −16.7 | 45 |
| **09c S−20-W1520-T** | 171 | 1.01 | 0.573 | +0.067 | +0.012 | 0.85 **1 day** | **+11.5** | +0.068 | −6.4 | 45 |
| 09d S−20-W1520-X | 171 | 1.01 | 0.503 | −0.043 | −0.082 | n/a | −7.3 | −0.043 | −16.7 | 45 |
| 09e S+0-W1400-T | 285 | 1.68 | 0.509 | −0.042 | −0.082 | n/a | −12.0 | −0.070 | −14.7 | 45 |
| 09f S+0-W1400-X | 285 | 1.68 | 0.477 | −0.068 | −0.091 | n/a | −19.2 | −0.113 | −16.7 | 45 |
| 09g S+0-W1520-T | 291 | 1.71 | 0.512 | −0.036 | −0.075 | n/a | −10.4 | −0.061 | −14.7 | 45 |
| 09h S+0-W1520-X | 291 | 1.71 | 0.471 | −0.075 | −0.098 | n/a | −21.7 | −0.128 | −16.7 | 45 |

Selection (PLAN sec. 5): no config ≥ 2/session → highest fit total R = **09c** (+11.5R; TIER B at best). It is also
the best by avg R w/o best day (+0.012). Best day 2025-04-03 (+9.8R of +11.5R); traded on 36 of 170 sessions;
avg ex-April 3-9 +0.064 (127 trades). Fit SPY up/flat/down avg R: +0.294 (n 12) / −0.056 (n 14) / +0.061 (n 145).
Exits: 88 time, 46 target, 37 stop. Only the stricter tape gate (−0.20%) and t1s1 were positive on fit; S 0.00 and
every TX45 config were negative.

## CHECK half — fit-selected 09c, scored once (275 sessions)

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| 09c S−20-W1520-T | 322 | 1.17 | 0.413 | **−0.157** | **−0.185** | n/a (total < 0) | −50.6 | −0.183 | −27.9 | 43 |

- SPY up / flat / down avg R: **−0.793 (n 85) / +0.021 (n 62) / +0.089 (n 175)**. Traded on 72 sessions; best day
  2026-03-05; check first half −0.171, second half −0.123.
- Two sessions (2026-02-17 −27.9R, 2026-03-03 −26.7R, 30 trades each = day cap) carry the loss: without them
  262 trades, +0.015/trade, +4.0R. 40% of all trades fall on 7 sessions with ≥ 10 entries — the trigger fires in a
  herd when a morning sell-off reverses, which is exactly when the shorts get run over.
- Diagnostics (counted, not used): uncapped −0.177 (336 trades); module bar-only refire chain = identical.

## Random-entry control (same symbol-sessions, random intake-U bar in the config window, same side and exit)
| half | trades | avg R (signal) | avg R w/o best day | total R |
|---|---|---|---|---|
| fit | 171 | +0.016 (+0.067) | −0.003 | +2.8 |
| check | 322 | −0.070 (−0.157) | −0.097 | −22.4 |
On fit the trigger looked +0.05R better than random; on check it is 0.09R worse. The failed-reclaim timing is not an
edge; whatever the weak-name/weak-tape selection carries, the trigger concentrates entries into reversal sessions.

## Check plateau (diagnostic only, never used to re-select)
All 8 configs negative on check. S −0.20 configs −0.155..−0.157 (t1s1) and −0.085/−0.086 (TX45); the broader
S 0.00 configs are near flat: 09f/09h TX45 −0.001R/trade (2.72/session, w/o best day −0.014/−0.015), 09e/09g t1s1
−0.022/−0.023. The ordering reversed between halves (fit favoured the strict tape gate and t1s1; check favours the
loose gate and TX45) — the selection-noise pattern WAVE1 warned about.

## What the numbers say (optimistic read, honestly scored)
- Shorting weak names on sessions that END down works in both halves (+0.061 fit, +0.089 check for 09c); the loss is
  all on sessions where SPY was down ≥ 0.2% since 09:50 at entry and then reversed to finish up (−0.79R/trade on 85
  check trades). As in ULT-04, the point-in-time "down tape" does not forecast the rest of the session.
- The only near-breakeven region is the broad, loose-tape TX45 version (−0.001, 2.7/session) — not an edge, but the
  volume is there. Backlog ideas (not tested; each would be new configurations): a tape-reversal exit / herd brake
  (flatten or stop adding when SPY reclaims part of its drop, or cap entries per 5-min bar) since two herd days carry
  the whole check loss; replace the SMA20 gate with distance-from-open in ATR units (a persistent condition).

## Recorded-quote replay (third opinion): not run
The candidate fails the check half decisively and trades ~1 time per session; the replay of recent live sessions
(research/reps2/nightly.py --replay; few session packs, ~1 h per run) would give a handful of trades and cannot change
the tier.

## Configurations tried
8 grid configs (fit) + 2 diagnostics on the fit-selected config (uncapped, module-chain) = **10** counted for ULT-09;
1 check score of 09c; 8 check plateau rows (diagnostic) and 2 random controls (not candidates). Program total per
PLAN sec. 4: 94 configs plus 574 evidence configs.

## Rule-change context
Backtest only on the 2-year cache (2024-10..2026-11-04); no live trades of this rule exist, so no live rule / sizing
change (e.g. TSZ1 testing-account sizing from 2026-11-17) affects these figures.
