# LR6 entry-execution sweet spot: pre-declared plan (2026-11-11, written and committed before any policy is scored)

Research only. No config, workflow or order change. Educational only — not financial advice.

## Question
LR6 (research/live_ready/NOTES.md) proposes marketable-limit entries with a collar, cancel-unfilled after 60 s and a
15 s max quote age on Primary. Owner (11-11): find the sweet spot per setup, per market condition and per ticker before
any change.

## Data (fixed now)
- Every closed live paper entry in every account journal (`mcf-data*` branches, run kind `paper`), 2026-10-06..2026-11-10.
  11-11 is partial and has no bars: used for the cost tables only, never for scoring.
- Per trade: signal price `ref` (= `orders.entry_ref`), stop/target (absolute, set at signal), bid/ask/spread and
  quote age at signal (`meta`, quote age logged on ~79% of trades), paper fill price and time, exit price/time/reason,
  `pnl_adj` (current costs).
- 1-minute SIP bars: `data/cache_hist/1Min` (to 11-04; read with a date filter >= 2026-10-01, the 2024-11..2025-02
  locked block is never examined) + the Move Hunt day files for 11-05/06/09/10. No fetch during market hours.
- Universe (ADV, ATR%, name) from `origin/mcf-data:universe.csv`; compass c30 state from the live compass log; SPY bars.

## Units and costs
- R per signal, denominator = planned risk |ref − stop| (same for every policy). A missed entry scores 0 R.
- Costs in on every filled trade: today's stop allowance (pnl − pnl_adj) + SEC/TAF/CAT fees (LR8 rates).
- Baseline = today's market order (fill = the observed paper fill, which paid the quote).

## Fill model (1-minute bars; buy-normalised, shorts mirrored)
- Immediate (marketable) part: the order fills at the observed paper fill f if f <= limit L. f is the ask the paper
  engine took ~1.5 s after the signal.
- Resting part (f > L): it rests from the fill time to signal + cancel window W. It fills only if a minute in the window
  trades **through** L by >= 1 tick (live queue-safe; paper's fill-on-touch would be more generous).
  Point estimate: each minute's overlap with the window is its weight w, p_fill = 1 − Π(1 − w·I_through).
  Bounds: lower = whole minutes inside the window only; upper = any overlapping minute that trades through.
- A resting fill is at L. The trade keeps its observed exit if that exit came after the estimated fill time; otherwise
  the bracket is re-simulated on bars from the fill minute (stop first in a bar, target needs a 1-tick trade-through,
  flatten 15:55 close).
- Quote-age policy: skip the signal (0 R) if quote age > A. Trades without a logged quote age are left out of that test.
- Known limit: windows of 15/30 s and the first minute of 60 s are sub-minute; bars cannot say whether a through-trade
  came before or after the signal second. Results for those cells are reported with their bounds.

## Grid (45 configurations, fixed)
- M: market (baseline), 1.
- O: limit = ref ± {0 (pure limit at signal), 2, 5, 10, 20} bps × cancel {15, 30, 60, 120, 300} s = 25.
- K: limit = ref ± k × spread-at-signal, k ∈ {0.5, 1, 2} × cancel {15, 30, 60, 120, 300} s = 15.
- P: LR6 as written: ask/bid ± min(0.25 × planned risk, 20 bps), cancel 60 s = 1.
- Q: max quote age {5, 15, 60, 300} s with market entries = 4 (300 s = today's setting, so 3 new).
Segment dimensions (description only unless listed under selection): setup, family, side, entry style, time of day,
price, ADV quartile, ATR% tercile, spread at signal, ETF / leveraged ETF / stock, SPY from open at signal
(up > +0.3%, down < −0.3%, quiet), compass c30 state, volatility regime (prior-5-day SPY range tercile), momentum into
the signal (side × 3-minute return: with > +10 bps, against < −10 bps, flat), account.

## Measures per policy (and segment)
fill rate (with bounds), reps lost per session, mean slip saved on filled trades, baseline R of filled vs missed trades
(adverse selection), net R per signal and its change vs market, day-clustered t of the change, the change without its
best day and that day's share.

## Selection (train only), then one score on valid
- Train = 2026-10-06..10-30 (19 sessions); valid = 11-02..11-10 (7 sessions). No locked holdout exists for live fills;
  the next live sessions are the forward test.
- Rule set candidates are chosen on train, per segment, from the 41 entry policies (M, O, K, P):
  objective = max Δ net R per signal vs market **subject to fill rate >= 90%** (owner values reps); else market.
- Segmentations scored for a rule set: (a) one global policy; (b) by entry style; (c) by momentum-into-signal;
  (d) by spread bucket; (e) by price bucket; (f) by SPY condition; (g) per setup with shrinkage
  est = (n·setup + 50·family)/(n + 50), family shrunk to global with k = 100.
- Each rule set is scored once on valid: Δ net R per signal, fill rate, reps lost/session, per account, Primary apart,
  improve/worsen count per setup family (owner remedy rule), one-big-day check.
- A rule set is recommended only if valid Δ R per signal > 0 with day-clustered t >= 1 and fill rate >= 90%;
  otherwise the recommendation is the simplest safe collar (protection, not R).
- Quote-age (Q) is judged separately: R of the dropped trades vs kept, reps lost.
