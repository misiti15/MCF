# swing1022 - "15m swing level: break-and-retest / 3rd rejection to the next POI" (Reddit, owner request 2026-10-22) - PLAN

*Written before anything is scored (2026-10-22 ~03:30 UTC). Educational only - not financial advice. History backtests
only (not paper, not live). Builds on research/bdi/reddit1021 (data loaders, cost model, random control, bars).*

## The strategy as posted (u/0xf35, r/Daytrading, paraphrase)
Points of interest (POI): swing points (normal and liquidity sweeps), change of character, psychological (round)
levels, previous session high/low. On the 15-minute chart, before the open, mark the recent swing high and swing low
(exclude the first candle). (1) **Break and retest**: a 15m candle closes outside the level -> trade the retest of the
level in the breakout direction; target the next POI, at least 1:2 risk:reward. (2) **Rejection**: price rejects the
level twice (wicks through, closes back) -> enter on the 3rd rejection in the rejection direction; next POI, >= 1:2.
"Very little edge, but can be tuned." Discretion is not modelled.

## Data, split, costs (fixed; as reddit1021)
- Regular-hours 1-minute SIP bars `data/cache_hist/1Min` read with pyarrow row filters that drop the locked block
  2024-11-01..2025-02-28 before materialising (reddit1021 `common.load_rth`). Extended hours (IDX only): the
  read-only Alpaca SIP 1-minute fetch already on disk from reddit1021 (`ext_1Min`, never requested the locked block).
  Stocks have no extended-hours bars here (not re-fetched), so stock levels are regular-hours only.
- TRAIN = sessions <= 2025-12-31 (2024-09-16..10-31, 2025-03-03..12-31). VALID = 2026-01-02..last cached session
  (2026-10-16). No holdout is scored. Days whose prior session lies in the locked block (2025-03-03) get no
  prior-session levels; lookback never crosses the block.
- Costs always in (production model, `mcf.research.gates` / reddit1021 engine): per side 1c + 1 bps; entry side x the
  time-of-day multiplier of the fill minute; target (limit) exit free; +2c on stop fills; x3 on the extended tier
  (price < $5 or |gap| >= 20%). Stop-first in every 1-minute bar; a bar opening through the stop fills at its open.
  Limit entries fill only on a trade-through (a later 1-minute bar strictly beyond the limit), charged full entry cost.

## Definitions (primary)
- **15m bars** from 1-minute RTH bars, 09:30 anchor (26 per session). ATR15 = 14-bar mean true range of 15m bars,
  continuous across sessions, value of the previous bar.
- **Swing points (fractal N = 2)**: a 15m bar whose high is strictly above the highs of the N bars before and the N
  bars after it (low: strictly below); confirmed at the close of the N-th bar after it. Built on the continuous
  regular-hours 15m series (IDX variant: regular + extended-hours 15m bars 04:00-20:00).
- **The level pair** ("before the session opens, mark the recent swing high/low"): the most recent swing high and the
  most recent swing low confirmed before 09:30, looking back at most K = 5 sessions. The first candle of the session
  (09:30-09:45) is excluded: it can never be a break / rejection / retest candle; triggers start with the 09:45-10:00
  candle.
- **POI set (targets)**: every swing high/low confirmed in the K = 5 prior sessions plus today's 15m swings confirmed
  so far, prior-session high/low, today's premarket 04:00-09:30 high/low (IDX only, where data allows), and round
  numbers. Round-number step = the smallest of {0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25, 50, 100} that is >= 0.5% of
  the prior close (SPY/QQQ ~ $5).
- **Change of character (CHoCH)**: a break of the swing high when the last two swing highs before it were falling
  (or of the swing low when the last two swing lows were rising) = against the prior structure; otherwise a
  break of structure (BOS). Used as a filter knob.
- **Break and retest (BR)**: a 15m candle (close 10:00 onward) closes beyond the level with the previous 15m close at
  or on the other side -> side = breakout direction. Retest = within the next M = 4 15m candles, a candle whose low
  (long) / high (short) comes within tol = 0.1 x ATR15 of the level (or through it) and closes back on the breakout
  side; entry = market at that candle's close (lab-runnable: a 15m close is a 5m close). A 15m close back through the
  level before the retest cancels the setup. Stop = beyond the farther of the level and the retest wick by
  0.1 x ATR15 (min $0.01). One trade per level per day.
- **3rd rejection (REJ)**: a "rejection" = a 15m candle whose high trades above the swing high (low below the swing low)
  and closes back below (above) it. Count rejections of the level in today's session from the 09:45 candle on; a 15m
  close beyond the level ends the count (that is a break). On the 3rd rejection candle -> enter at its close in the
  rejection direction (short at the swing high, long at the swing low). Stop = beyond that candle's wick by
  0.1 x ATR15 (min $0.01).
- **Target (primary)**: the next POI beyond the entry in the trade direction (POIs closer than 0.1 x ATR15 to the
  entry are ignored); if it is closer than 2R, **skip the trade** (strict reading of "target the next POI with at least
  1:2"). Limit at the POI (free exit). Flat 15:55.
- **Window (primary)**: entry candle closes 10:00..11:30. One open position per symbol at a time.

## Groups
- **IDX**: SPY + QQQ pooled. **LEV**: SPXL + TQQQ pooled, each on its own bars and levels (execution check: costs per
  unit risk are lower on 3x ETFs). **STK**: lab universe (reddit1021 stk_syms, 1,198 names) on days with adv20 >=
  $95M, SPY/QQQ excluded.

## Configurations (counted; per group, both types BR and REJ)
Primary (1 per type). One-knob variants from each type's primary (26 per type; +1 for IDX/LEV):
1. swing N = 1 / 3 (2)
2. trigger levels: + prior-session H/L / + round numbers / + today's 15m swings (3)
3. BR: retest tol 0 / 0.25 ATR15 (2); REJ: a "rejection" may also be a touch within 0.1 ATR15 / wick needs >= 0.1
   ATR15 through (2)
4. BR: retest window M = 2 / 8 (2); REJ: enter on the 2nd / 4th rejection (2)
5. entry as a resting limit (BR: at the level + tol after the break close, live M candles; REJ: at the level after the
   2nd rejection, live to window end), trade-through fill, stop beyond the level by 0.1 ATR15 (1)
6. target: fixed 1.5R / 2R / 3R; first POI >= 2R (skip closer POIs); next POI >= 1.5R (5)
7. stop buffer 0 ($0.01) / 0.25 ATR15 (2)
8. window full day: entry candle closes to 15:00 (1)
9. volume: trigger candle (BR: break candle; REJ: entry candle) volume > 1.0x / > 1.5x its 20-bar 15m average (2)
10. trend: SPY close vs its session VWAP / vs its open at the entry candle, trade only with it (2)
11. long only / short only (2)
12. fresh levels only (BR: no 15m bar before the break touched the level today; REJ: no 15m close beyond the level
    in the 5 prior sessions after it formed) (1)
13. CHoCH only / BOS only (2)  [REJ: rejection of a level that formed against / with the prior structure]
14. IDX/LEV only: swings from regular + extended-hours 15m bars (1)
= 1 + 26 (+1) per type -> IDX 56, LEV 56, STK 54.
**Stage 2** (per type x group): knobs (any above) whose one-knob variant raised TRAIN avg R by >= 0.02 over the primary
and kept >= 30% of its trades; top 3 by train gain, at most one per knob family; the 3 pairs + the triple = up to
4 per type x group = up to 24.
N <= 166 + 24 = **190**. Study bar max(1.5, sqrt(2 ln N)) ~ 3.24. **Lineage bar** (swing / level studies of the Reddit
lineage: + reddit1021's 183) N <= 373 -> ~3.44; with reddit1012liq (7,718) also reported (~4.25).

## Controls (reported, not counted)
Random same-minute entry: for every trade, a market entry at the close of the same fill minute on other sessions of
the same split (IDX/LEV: 60 sessions; STK: 20 sessions of the same symbol, seeded), same side, same R as a fraction of
price, the same target multiple (the trade's realised target distance in R) and exit rule. Excess = trade R - control.

## Bars (pre-declared, as reddit1021 / longs1020)
- **Testing bar**: train and valid avg R > 0 after costs; both above the random control; valid day-clustered t >= 1.5;
  n_train >= 30 (IDX/LEV) / 150 (STK); open-history avg R without the best day > 0.
- **Research candidate**: Testing bar + open-history t >= the study bar + up and down sessions both > 0 (n >= 30
  each) + walk-forward share of positive months >= 60%.
- Near-miss = fails exactly one Testing-bar condition. Every finalist is reported with its failures.
- **Testing accounts**: a Testing-bar pass gets a lab module (GEOM "S", stop_price / target_price, module-vs-scan
  parity) and a live setup (type lab, tags [observation, swing1022]) in the testing account that fits (Testing 2 for
  index ETFs). If none passes, at most 3 clear near-misses may be added as observation, never one that loses on both
  train and valid; the module must be runnable on the live frame (today's 5m bars + prior-day H/L) - a variant that
  needs prior-session swing points or premarket bars is not runnable live without new context and is reported only.

## Deliverables
NOTES.md (verdict up top, failures first, counts, bars, Reddit reply), results.csv (every configuration),
finalists.csv, modules/ + parity json for anything added.
