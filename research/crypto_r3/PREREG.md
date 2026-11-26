Educational only — not financial advice.

# Crypto round 3: pre-registration (written 2026-11-26, before any round-3 scoring run)

Research only: no live changes, no config changes, no Alpaca trading or account endpoints (GET market data only,
no keys). LOCKED (2026-05-26..2026-11-25) is not read: the loader clips at its start. Splits unchanged:
FIT 2021-01-01..2024-12-31; CHECK 2025-01-01..2026-05-25. **CHECK is on its third look as a window** (r1, r2),
so the CHECK survival bar is raised to day t >= 1.5 (rule-18 look-2 level) for every round-3 config.

## 0. Clean data (engine change, `mcf/crypto/exec1m.clean_traded`)
- Raw Alpaca 1-min bars -> Amendment-1 bad-print filter (`clean_prints`, as round 2) -> **signal bars are built
  only from minutes with a real trade (volume > 0)**. Zero-volume (quote-derived) minutes never enter a signal bar.
  Empty buckets carry the last close and are flagged `filled`.
- Fills (as round 2, Amendment 1): a maker entry/target fills only on a traded minute that trades THROUGH the limit.
  Taker exits fill at the open of the first minute (traded or quote-derived) at/after the decision, paying
  half-spread (research/crypto_r1/spreads.json) + 2 bps slippage (x3 if that minute is not the first one) + fee.
- **Trades endpoint:** a probe of `/v1beta3/crypto/us/trades` (BTC 2024-06-03 14:00-14:10, all zero-volume bars)
  returned no trades, so trades = the volume > 0 bars. No trades data is downloaded (adds nothing; 0 MB).

## 1. Clean-bar re-check of earlier near-misses (information only, NOT counted as configs)
- Round 2: the 10 frozen v2 near-misses (finalists.json) re-scored on FIT and CHECK with signal bars from traded
  minutes only (fills unchanged). Round 1: the top 3 near-misses (ids 31, 477, 459) re-scored with the r1 engine
  on traded-only bars. No choice is made from these; they only show whether the near-misses depended on quote bars.

## 2. Daily trend test, BTC / ETH / SOL, long only (9 configs, ids 980-988)
Swing/daily, NOT intraday: outside MCF's intraday charter unless the owner widens scope.
- Daily UTC bars (clean, traded-only). Decision at each 00:00 UTC (close of day d). Indicators use history from
  2021-01-01 (warm-up: a 200-day MA is not defined until about 2021-07).
- Regime filter: close > SMA(L), **L in {50, 100, 200}** x 3 rules =
  - **A regime:** long while close > SMA(L); exit when close < SMA(L).
  - **B breakout:** enter when close > SMA(L) and close > the highest close of the prior 20 days; exit when
    close < SMA(L) or close < the lowest close of the prior 10 days.
  - **C pullback:** enter when close > SMA(L) and RSI(3) < 20; exit when RSI(3) > 70, close < SMA(L), or 10 days held.
- Entry (as round 2): maker limit buy at the decision close, life 1,440 min, filled only by a traded minute with
  low < limit, at the limit, maker fee 15 bps, no spread. A missed order is not chased: at the next decision the
  rule is evaluated again (A re-enters while the regime holds; B/C need a new trigger). Exit: taker, as section 0.
  No intraday stop. Open positions are closed at the split end (last price before it, taker costs).
- Fee tier 1 base. Taker-entry and tier 2/3 runs are a SENSITIVITY only, never used to choose.
- **Portfolio:** three sleeves of 1/3 of capital each, no rebalancing, cash earns 0. Daily equity at UTC closes.
  Reported per config and split: total return, CAGR, annualised Sharpe (daily, sqrt 365, rf 0), max drawdown,
  exposure, trades, maker fill rate, and the same for each pair.
- **Trade R** (for the round-2 rules): R unit = 3 x ATR(14, daily) / entry price at entry (notional; no stop is
  placed). r = net trade return / unit. Day-clustered t on the UTC entry day.
- **Benchmarks (both, on FIT and CHECK):**
  1. Buy-and-hold: the same three sleeves bought at the split start (taker costs) and held to its end.
  2. Random entries over the same exposure: 200 reps; per pair, the config's own holding durations (in days) are
     placed at random non-overlapping decision days in the split, entered and exited with the same maker/taker
     rules. Report the config's percentile on total return, Sharpe and avg R.

## 3. Intraday vol-regime test, BTC / ETH / SOL, long only (8 configs, ids 989-996)
- Hourly bars from clean traded-only minutes. Move m = log(close_h / close_{h-1}); the hour must have a real print.
- Big hour: |m| > the trailing 720-hour quantile q_p of |m| (prior real hours only, at least 360), **p in {0.99, 0.98}**
  (top 1% / top 2% hours).
- **cont:** big hour with m > 0 -> long. **rev:** big hour with m < 0 -> long. **Hold in {4 h, 24 h}**.
  2 x 2 x 2 = 8 configs.
- Exec (engine E5b, `exec1m.run`): maker limit at the decision close, life 60 min (traded-through fills), stop =
  max(3 x ATR(14, 1h), 3% of price) taker, no target, time exit taker. Fee tier 1.
- Random baseline: 100 reps of random real hours, same trades per pair, same plan.

## Counting, eligibility, CHECK
- **N_cum = 1,460 + 9 + 8 = 1,477; noise bar sqrt(2 ln 1477) = 3.82.**
- FIT eligibility (as round 2): >= 60 trades, best-day share < 0.5, avg R w/o best day > 0, day t >= 3.82.
- Because only 17 configs exist, **all 17 are scored ONCE on CHECK** and reported (non-eligible ones are information
  only and can never survive). Results of FIT are written to disk before the CHECK run starts.
- **CHECK survivor** (FIT-eligible only): >= 20 CHECK trades, avg R > 0, avg R w/o best day > 0, best-day share
  < 0.5, day t >= 1.5, beats random (> 50% of reps on avg R); trend configs must also have a CHECK Sharpe >= the
  buy-and-hold Sharpe. A survivor goes to research/backlog.jsonl as status "idea", tags crypto + swing/intraday.
- Known biases: survivorship (only today's listed pairs; BTC/ETH/SOL are the winners of 2021-26, which flatters any
  long, B&H most of all); spreads before 2023 use 2023; SOL had trades in only ~2% of 2024 minutes, so its signal
  bars are sparse and maker fills rare in 2024.
- **Engine smoke test:** none run before this file.
