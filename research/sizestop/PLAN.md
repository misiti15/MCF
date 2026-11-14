# SIZESTOP (D1) — size-conditioned stop width: 1.5x wider stops on predicted-big days, same $ risk (FROZEN 2026-11-14 09:30 ET, not scored)
Educational only — not financial advice. Research only; no stop, sizing or execution change anywhere. Plan by Scout for Builder
to score AFTER MOMSIDE (Lead lead-20261114-0900-1/-3; Observer observer-20261114-0742-1; Skeptic skeptic-20261114-0850-1).
**Prior: low.** SIZETREND: big-gap days have +14% range after 10:00 but the same path efficiency (0.452), so the only mechanism
left is fewer noise stop-outs on wider-range days. STOPW: ~85% of unconditional widening gains were the size cut on a losing book.

## Rule (setups keep their own direction, entries and targets)
Predicted size, known at 09:30: g = |open / prior close - 1| / ATR%(name) (14-day mean true range / prior close, days < D;
NaN on the first session after the locked-block gap, checklist 8). Quintile of g across all lab names that day (point in time).
On trades whose name-day is in the chosen quintiles, the stop distance becomes D' = k x D at the same $ risk (fewer shares).
The target PRICE is unchanged; holdtr trails use D'. Other trades are untouched.
- **C1:** k = 1.5 on g quintiles 4-5.   **C2:** k = 1.5 on g quintile 5 only.   (2 configs)

## Sample and engine (the STOPW / BEREPLAY engine, unchanged)
Builder's research/bereplay 1-minute engine on the 2-year lab lists (research/history2y/data/bt_lab1104 + GEN hold/holdtr
lists), as in research/stopw/stopw.py. Locked block 2024-11-01..2025-02-28 dropped at read and asserted. Stop-first inside a
minute; a minute opening through the stop fills at its open; costs exactly as bt_all (stop exits +1c +1bp +2c).
LR8 does not apply (lab R, not journal pnl_adj).

## Controls (both REQUIRED; this is where earlier stop studies were fooled)
1. **Size-cut control** (stopw_sizectl.py logic): CTRL = BASE x D / D' on the changed trades (same trade, old stop, the smaller
   size). Stop effect = variant - CTRL. Without it the result is 'trade less on a losing book'.
2. **Random-day control (the conditioning test):** apply the same k to a random set of name-days with the SAME share of trades
   as the rule changes (stratified by setup x month), size-cut-controlled the same way, 200 draws. Conditioning effect = stop
   effect(rule) - mean stop effect(random). Unconditional widening is already known to help a little (STOPW). D1 must show that
   the gap condition picks the RIGHT days to widen.

## Scoring
Per config: conditioning effect (primary) and stop effect per trade, day-clustered t; ex-market (gross - TRAIN beta x SPY over
each leg's hold); TRAIN (<= 2025-09-30) / VALID; SPY up / down / quiet sums; w/o best day; per family x side n, better / worse,
worst delta. Mechanism counts on changed trades: stop-out share BASE vs variant, and give-up-then-recover (BASE stopped out,
then price reached the BASE target the same day) vs the random-day control.
## Counting, bar, pass
Family STOPW 77 + 2 = **79 -> BAR90 2.66** (on the conditioning-effect t).
Pass (lead for the arena; any live change is the owner's): conditioning effect t >= 2.66 AND > 0 in TRAIN and VALID;
down-session summed effect not worse than zero; >= 60% of families better (each reported, Remedies rule); w/o best day > 0;
give-up-then-recover share higher than under the random-day control. Otherwise closed. No grid over k or quintiles.
