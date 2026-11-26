Educational only — not financial advice.

# Crypto round 2: pre-registration (written 2026-11-26, before any round-2 scoring run)

Owner ask (2026-11-25): a crypto foundation with massive research and random setup generation. Research only:
no live changes, no config changes, no Alpaca trading or account endpoints. LOCKED (2026-05-26..2026-11-25) is not
read (the loader clips at its start).

## What changes from round 1
- **Engine "E5b crypto 1-min fills"** (`mcf/crypto/exec1m.py`). Signals are decided on 15m / 1h / 4h / 1d bars
  (built from 1-min). Fills and exits are simulated on the pair's real 1-min prints.
  - **Maker entry (realistic):** a limit buy at `close - off x ATR(tf)` rests for `expiry` minutes. It fills only
    if a later 1-min bar trades THROUGH it (low < limit; a touch does not fill), at the limit price. Unfilled
    orders are counted as missed. Maker fee, no spread, no slippage.
  - **Taker entry:** open of the first print after the decision; x3 slippage if that print is not in the first
    minute.
  - **Exits:** stop = taker (half-spread + slippage + 5 bps stop extra, gap fills at the open; on the maker fill
    minute the stop is assumed hit if that minute's low reaches it). Target = resting maker sell, fills only if
    traded through (high > target), never on the entry minute. Time stop = taker at the first print after the
    hold. Stop is checked before target.
  - **Stops are wide:** risk = max(stop_atr x ATR(tf), min_stop_pct x price), min_stop_pct in {3, 4, 5, 7}%.
  - **Holds:** 4 h to 7 days.
- **Costs:** base case = Alpaca fee tier 1 (maker 15 / taker 25 bps) + the sampled spread table
  (research/crypto_r1/spreads.json) + slippage as in round 1. Tiers 2 (12/22) and 3 (10/20) are reported as a
  SENSITIVITY only. They are never used to rank, choose or pass anything.
- **Universe:** core = BTC, ETH, SOL. Tier 2 = AVAX, DOGE, LINK, AAVE, UNI, LTC, BCH, DOT, XRP, SHIB. Each random
  draw picks core or core + tier 2. Pairs listed after 2024 add nothing to FIT.

## Configurations (all counted)
- **400 random draws**, seed 20261127, draw ids 500..899 (`mcf/crypto/generator2.generate`). Each draw: timeframe
  1h / 4h / 1d; 1-3 primitives (ret, stretch, breakout, pullback, rsi, trend, volsurge, zdrop, wick, btc_trend,
  btc_ret, volreg); session window and weekday / weekend; entry maker (p = 0.75: offset 0 / 0.25 / 0.5 / 1 ATR,
  life 1 or 4 bars) or taker; stop, stop floor, target (1.5 / 2 / 3R or none) and hold.
- **80 seed configs**, ids 900..979 (`generator2.seed_grid`). Five event ideas from MARKET_RESEARCH.md, each with
  2 variants x stop floor {3%, 5%} x exit {2R target + short hold, no target + long hold} x entry {maker at the
  close for 60 min, taker} = 16 configs:
  1. **flush** (15m): 1-bar drop <= -3.5 / -4.5 sigma, volume >= 3x, lower wick >= 50%; holds 12 h / 48 h.
  2. **orb_us** (15m, weekdays): close crosses above the 09:30-10:00 ET range high, 10:00-13:00 ET, volume >=
     1.5x / 3x, BTC above its own range mid (alts); holds 6 h / 24 h.
  3. **asia_comp** (15m): 00:00-07:00 UTC range <= 0.6 / 0.8 x its 20-day median; close crosses above its high
     between 07:00 UTC and 16:00 ET; holds 8 h / 24 h.
  4. **tsmom** (15m, weekdays; Shen/Urquhart/Wang): UTC-day return to the 09:30 ET open >= 0.5 / 1.0 sigma of its
     20-day history and volume so far above its 20-day median; long at the open; holds 6.5 h (US close) / 24 h.
  5. **btc_lag** (1h, tier-2 alts only): BTC 1-bar z >= 1.5 / 2.5; buy the alt that lagged BTC most on that bar
     (lag >= 1 sigma); holds 4 h / 24 h.
- **N_cum = 500 (round 1) + 480 = 980. Noise bar = sqrt(2 ln 980) = 3.71.**

## Eligibility (FIT only, 2021-01-01..2024-12-31, base costs)
All of: >= 60 trades; best-day share < 0.5; avg R without the best day > 0; day-clustered t >= 3.71.
Long only (Alpaca spot cannot short).

## Freezing and CHECK (2025-01-01..2026-05-25)
- Top 10 = eligible configs ranked by FIT day-clustered t, at most 3 per seed idea (random draws are uncapped).
- If fewer than 10 are eligible, the rest are filled by the best **near-misses** (>= 60 FIT trades, not eligible,
  ranked by FIT day t, same cap). Near-misses are **information only** and can never survive.
- If zero are eligible: report it, and freeze the 10 best near-misses for information only.
- `finalists.json` is written by the FIT run and frozen before CHECK is read. The 10 are scored ONCE on CHECK.
  CHECK counts as a first look for these new finalists (rule-18 rising bar, look 1).
- **CHECK survivor** (eligible finalists only): >= 20 CHECK trades, avg R > 0, avg R without the best day > 0,
  best-day share < 0.5, day t >= 1.0, and beats the random-entry baseline (above its mean in > 50% of reps).
  A survivor goes to research/backlog.jsonl as status "idea", tag "crypto". Nothing goes to trading.

## Comparison with random entries
For each finalist, on FIT and on CHECK: 100 reps of random entry bars drawn from the setup's own time filter
(window, days, seed clock gates), the same number of entries per pair, the same entry mode and exits. Report the
mean random avg R and the finalist's percentile.

## Also reported (never used to choose)
- Maker-fill effect: each config re-run with taker entries, with realistic maker entries, and with the round-1
  "naive" maker assumption (certain fill at the next open, maker fee). Fill rate of realistic maker orders.
- Tier 2 / tier 3 avg R and t; core (BTC/ETH/SOL) trades and avg R inside each config.
- Every finalist: FIT, CHECK, avg R w/o best day, trades, cost per trade in R.

## Known biases and disclosures
- **Survivorship:** pairs delisted before 2026-11 (MATIC, NEAR, ALGO, TRX, MKR and others) are missing. The
  universe is today's survivors, which flatters long setups on alts.
- Spreads before 2023 use each pair's earliest sampled year (2023), which is conservative for BTC/ETH.
- Day clustering uses the UTC entry day. No rule / config / ledger changes apply: crypto is not live.
- **Engine smoke test before this file:** 8 configs (draws 500-502 and one config of each seed) were run on FIT
  to check the engine. None was net positive (best +0.035R, t 0.88). No grammar, grid or rule was changed after it.
