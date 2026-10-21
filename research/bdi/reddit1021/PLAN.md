# reddit1021 — "untouched levels + 5m fib-retrace" (Reddit strategy, owner request 2026-10-21) — PLAN

*Written before anything is scored. Educational only — not financial advice. History backtests only (not paper, not live).*

## The strategy as posted (paraphrase)
Levels that have NOT been touched yet today: NY opening-range 15m high/low (09:30-09:45), London session H/L
(03:00-09:30), Asia session H/L (18:00-03:00), previous NY session H/L (09:30-17:00), untested swing highs/lows.
Window 09:45-11:30 ET. **Continuation:** a large-body 5m candle closes through a level with volume above the previous
candle's; enter on a retrace to 0.5 / 0.618 of that whole candle within the next two 5m candles; stop beyond the far
end of the candle; target 2R. **Reversal:** a 5m candle wicks through a level and closes strongly back, volume above
the previous candle's; same retrace entry; stop beyond the wick; 2R. Discretion (too-strong retrace, trend, nearby
S/R) is not modelled except the pre-declared trend filter below.

## Data, split, costs (fixed)
- He likely trades ES/NQ futures. We have US equity/ETF SIP bars only. **Asia session: not available for ETFs** (no
  trading 18:00-04:00). Proxy "AH" = the prior session's after-hours 16:00-20:00 H/L. **London proxy "PM"** = the
  04:00-09:30 premarket H/L. Both from a read-only Alpaca SIP fetch of extended-hours bars (`scripts/fetch_ext.py`;
  1-minute for SPY/QQQ, 30-minute for stocks — the H/L of 04:00-09:30 and 16:00-20:00 are exact on 30-minute bars).
- Regular-hours 1-minute bars from `data/cache_hist/1Min` via pyarrow row filters that drop the locked block before
  materialising; the extended-hours fetch never requests 2024-11-01..2025-02-28. Days whose prior session is locked
  (2025-03-03) have no PD/AH levels.
- TRAIN = sessions ≤ 2025-12-31 (2024-09-16..10-31, 2025-03..12). VALID = 2026-01-01 onward (to the last cached
  session). No holdout is scored.
- Costs always in (`mcf.research.gates`): per side 1c + 1 bps; entry side × time-of-day multiplier (fill minute);
  exit side free on a target (limit) fill; +2c on stop fills; ×3 on the extended tier (price < $5 or |gap| ≥ 20%).
  The limit entry is charged the full entry cost (conservative; no rebate). Stop-first inside every 1-minute bar; a bar
  opening through the stop fills at its open.

## Definitions (primary)
- 5m bars from 1-minute RTH bars (09:30 anchor). Bar "open" for the body test = the previous 5m close (the live lab
  frame has no bar open; within a liquid session this equals the true open to the cent almost always).
  ATR5 = the previous bar's 5m ATR (`heat_frame` atrPct: 14-bar mean true range, continuous across sessions).
- Levels: **OR** 09:30-09:45 H/L (active from 09:45); **PM** 04:00-09:30 H/L; **AH** prior 16:00-20:00 H/L;
  **PD** prior 09:30-16:00 H/L (the 16:00-17:00 hour of his "previous NY session" is inside AH);
  **SW** today's 5m pivot highs/lows (2 bars each side, usable once confirmed).
- **Untouched**: no RTH bar since the level became available (09:30; 09:45 for OR; confirmation for SW) has traded at
  it (low ≤ L ≤ high), up to the bar before the signal candle. One trade per level per day.
- Signal candle: 5m bar closing 09:50..11:30.
  - **Continuation (C)**: prior close on one side of an untouched level, close on the other; body ≥ 60% of range;
    range ≥ k·ATR5 (k = 1.5); volume > previous 5m bar's. Side = direction of the close.
  - **Reversal (R)**: the bar trades through an untouched level (high > L above / low < L below) and closes back on the
    original side, in the outer 35% of its range (short: close ≤ low + 0.35·range; long: close ≥ high − 0.35·range);
    range ≥ k·ATR5 (same k); volume > previous bar's.
  - A candle crossing several levels gives one signal (family label = first of PD, PM, AH, OR, SW).
- **Entry**: limit at the fib of the whole candle (long: high − f·range; short: low + f·range), f = 0.5, live for the
  next 10 one-minute bars (two 5m candles), else cancelled. **Trade-through fill (primary)**: a later 1-minute bar
  trades strictly beyond the limit; fill at the limit.
- **Stop**: candle low − buffer (long) / high + buffer (short), buffer = max($0.01, 0.02·range). R = |entry − stop|.
  In the fill minute only the stop is checked (stop-first; the target counts from the next minute).
- **Target** 2R (limit). **Flat 15:55**. One open position per symbol at a time (a signal is skipped while an earlier
  order or position on the symbol is live).

## Groups
- **IDX**: SPY + QQQ pooled, traded as themselves (per-ticker rows reported, descriptive only).
- **STK**: lab universe with adv20 ≥ $95M on the day (as the other setups), excluding SPY/QQQ.

## Configurations (counted; per group)
1. Base grid: type {C, R} × fib {0.5, 0.618} × target {1.5R, 2R, 3R} × exit {15:55, 11:30 time stop} = **24**.
   (11:30 time stop: exit at the 11:30 close, or 10 minutes after the fill if that is later.)
2. One-knob variants from each type's primary (fib 0.5, 2R, 15:55) = **20 × 2 = 40**:
   level family alone OR / PM / AH / PD / SW (5); volume filter off / > 1.5× previous / > 20-bar average (3);
   trend filter — trade only with the trend: close vs session VWAP, close vs 5m EMA20 (own symbol for IDX, SPY for
   STK) (2); any level, touched or not (1); first signal of the day only (1); candle-close buckets 09:50-10:15 /
   10:20-10:45 / 10:50-11:30 (3); k = 1.0 / 2.0 (2); touch-fill (1); market entry at the candle close, no retrace
   (1); "lab-runnable": entry at the close of the first 5m bar (of the next two) that trades through the fib (1).
3. Stage 2 (combinations, per type × group): the knobs among {volume, trend, freshness, first-of-day, k} whose
   one-knob variant raised TRAIN avg R by ≥ 0.02 over the primary while keeping ≥ 30% of its trades; the top 4 of them
   by train gain; all pairs (6) + the all-4 combination (1) = up to **7 × 2 × 2 = 28** (fewer if fewer knobs qualify;
   the count is what is actually scored).
- N ≤ 2 × (24 + 40) + 28 = **156**. Study bar max(1.5, sqrt(2 ln N)) ≈ 3.18. Also reported: the bar including the
  reddit1012liq level-sweep lineage (7,718), since the reversal half re-tests level sweeps.

## Controls (reported, not counted)
- **Random same-minute entry, same exit**: for every trade, a market entry at the close of the fill minute with the
  same side, the same R as a fraction of price, the same target multiple and exit rule — IDX: the same symbol on every
  other session of the same split (mean); STK: the same symbol on 20 other eligible sessions of the same split
  (seeded draw, mean). Excess = trade R − control R.
  *(Amended before any scoring: the STK control was first written as "3 other symbols on the same day"; that needs
  every symbol's minute bars in memory at once (~3 GB), so it is the same-symbol / same-minute / other-day control
  used for IDX.)*
- Also reported: **same signal, market entry at the candle close** (variant C19 above) — whether waiting for the
  retrace adds anything over simply entering on the signal candle.

## Bars (pre-declared)
- **Testing bar** (as longs1020): train and valid avg R > 0 after costs; both above the random control; valid
  day-clustered t ≥ 1.5; n_train ≥ 30 (IDX) / 150 (STK); open-history avg R without the best day > 0.
- **Research candidate**: Testing bar + open-history t ≥ the study bar + up and down sessions both > 0 (n ≥ 30 each)
  + walk-forward share of positive months ≥ 60%.
- Near-miss = fails exactly one Testing-bar condition, labelled as such. Every finalist is reported with its failures.

## Deliverables
NOTES.md (failures first, counts, bars), `results.csv` (every configuration), `finalists.csv`, a ≤ 200-word Reddit
reply, lab modules in `modules/` for viable/near-miss variants (LabStrategy contract: SIDE, GEOM, WINDOW, SYMBOLS,
mask(df), and for structural exits stop_price / target_price), module-vs-scan parity, `backlog_proposals.jsonl`.
Nothing in config/, mcf/, docs/, research/ledger.jsonl, research/backlog.jsonl or research/owner_inbox/ is edited.
