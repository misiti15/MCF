# reddit_1103 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Common rules (docs/RESEARCH_RULES.md), as reddit_1102: costs in (1c + 1 bp per side; entry side x
`gates.tod_cost_mult`, exit side free on a target limit, +2c on stop fills); next-bar-open entries; stop first when a
bar touches stop and target; locked block 2024-11-01..2025-02-28 never read (1-minute rows and daily rows dropped at
load, before any computation); old holdouts 2026-04..06 and >= 2026-09-16 dropped; earnings blackout
(`GD._blackout`) removed; one trade per symbol-day; day-clustered t; regime gate `gates.session_regimes` (up and down
both > 0); WF = share of months > 0 (>= 54%); TRAIN <= 2025-08-31 / VALID after; avg R without the best day and the
best-day share; R split by SPY day type (SPY open-to-close > +0.25% up, < -0.25% down, else quiet) for the QDAY focus.
**N = 8 (A) + 3 (B predictors) = 11 configurations -> full bar sqrt(2 ln 11) = 2.19, BAR90 = 1.97.** No post-hoc
configs. The locked block is scored only if a config clears every open-history gate.

## A — range-low volume-flip long with a "magnet" target (r/Daytrading 1xn4wdn, 2026-11-03, ABT +0.48R)
Data: data/cache_hist/1Min resampled to 5-minute bars 09:30-15:55. Universe: point-in-time top 250 non-ETF names by
prior-day adv20 (daily.parquet), blackout removed.
- Signal bar i (bar close 10:00..14:55): bars i-1 and i-2 bearish (close < open); key = the larger volume of the two;
  bar i bullish with body >= 50% of its range and volume >= m x key; bar i low in the bottom 30% of the session range
  so far (HOD/LOD from 09:30 through bar i).
- Context: `none`, or `quiet` = session range so far <= 0.75 x the stock's ATR14 (prior days) — the "range trade, no
  confirmed breakout" read.
- Entry: open of bar i+1. Stop: min low of bars i-2..i minus 1c. Skip R < 0.10% of price.
- Magnet = high of the highest-volume bullish 5-minute bar of the session through bar i; if it is < entry + 1R the
  session high so far is used; if that is also < entry + 1R, target = entry + 1R.
- Exits: `E1` (poster): half at +1R, rest stop moved to breakeven, rest target = magnet, else out 15:55 close;
  `E2`: whole position target = magnet, stop, else out 15:55.
- Grid: context {none, quiet} x m {1.2, 1.5} x exit {E1, E2} = **8 configs**, long only.
- Random control: per trade, 3 random entry bars (10:05..15:00 opens) on the same symbol-day, same $ stop distance,
  same exit rule and the same magnet price (or +1R if below); excess = trade R minus the mean of its controls.
- Also reported: magnet hit rate.

## B — pre-open "range regime" predictor, then fade the early move to VWAP (r/Trading 1xme54j, 2026-11-03, AVGO)
qd1-1103-quiet-so-far-index-fade asked for an ex-ante quiet-day predictor that beats the base rate by >= 15 points
before any fade is re-tested. Step 1 tests three pre-open predictors (known before 09:30) on daily bars, same universe
as A. Range day (label) = (high - low) <= 0.8 x ATR14 (prior days) and |close - open| <= 0.3 x ATR14.
- P1: prior day NR7 (range smallest of last 7) and |gap| <= 0.2 ATR.
- P2: prior day inside day and |gap| <= 0.2 ATR.
- P3: prior 5-day mean range / ATR14 in the stock's bottom 20% of its own past year and |gap| <= 0.2 ATR.
Gate: precision >= base rate + 15 points, TRAIN and VALID both, n >= 300. **Only a predictor that clears the gate goes
to step 2** (fade a 09:30-10:00 move >= 0.5 ATR back toward VWAP, stop at HOD/LOD so far, target VWAP, out 12:00;
declared now, 2 configs = side long/short, which would bring N to 13). If none clears, step 2 is not run.
