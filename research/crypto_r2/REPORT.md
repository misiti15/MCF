Educational only — not financial advice
# Crypto round 2: slow bars, wide stops, realistic maker fills, event seeds (engine E5b 1-min fills, 2026-11-26)
**Verdict: no survivor.** 0 of 480 configs are eligible on FIT; all 10 frozen near-misses lose or fail on CHECK. Nothing goes to the backlog. LOCKED stays sealed. No rule, config or ledger changes apply: crypto is not live.
- **Pre-registered** in `PREREG.md` (sha256 cdf610e3…) before scoring, plus `PREREG_AMEND1.md` (fe2525c0…) before the v2 re-score. Both hashes are in `PREREG.sha256`.
- **Configs:** 400 random draws (ids 500-899, 1h/4h/1d bars) and 80 seed configs (5 ideas × 16). Scored twice (v1, then v2), so **N_cum = 1,460** with round 1. Noise bar 3.82.
- **v1 is void (a data finding):** its best near-miss (draw 742, 4h pullback) was +0.03R on FIT and +0.03R on CHECK (t 3.0), but it was all SHIB, whose targets filled on bad prints (highs 0.0040 vs a 0.000011 price).
  - Every alt has such prints. Since 2023, 49-88% of BTC minutes are zero-volume (quote-derived) bars.
  - Amendment 1 adds a trailing bad-print filter, and maker fills now need a real trade. v1 outputs are kept in `v1_badprints/`.
- **Costs fixed, edge gone:** the median cost is now **0.13R per trade** (round 1: 0.70R): 0.06R on 1d bars, 0.12R on 4h, 0.15-0.22R on 15m/1h. But the median gross edge is −0.01R.
  - 130 of 291 configs with ≥ 60 trades are gross-positive and 23 are net-positive. Best day t 2.61, against a bar of 3.82.
- **Seeds:** all 5 event ideas lose on FIT in all 16 configs each: flush −0.17R median, ORB −0.21R, Asia compression −0.24R, TSMOM −0.30R, BTC→lagging alt −0.25R.
- **Maker-fill effect** (195 maker configs): 64% of limit orders fill. Realistic fills cost −0.027R per trade against the round-1 "certain fill" assumption, because adverse selection takes the gross edge from +0.007R to −0.015R. They are still +0.038R better than taker entries.
- **Fee tiers** (sensitivity only): tier 2 gives 24 net-positive configs (max t 2.64), tier 3 gives 27 (max t 2.65). Neither reaches the bar.
- **Survivorship:** delisted pairs (MATIC, NEAR, ALGO, TRX, MKR…) are missing. This flatters longs on alts.

| id | v2 near-miss (long, information only) | FIT n | FIT avgR | FIT w/o best | FIT t | CHECK n | CHECK avgR | CHECK w/o best | CHECK t | cost R | rand pct FIT/CHK |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 515* | 1d RSI≥75 + 6-day breakout, mk 1ATR, s3ATR≥5% t2R h96 | 61 | +0.220 | +0.192 | 2.61 | 8 | −0.138 | −0.172 | −1.44 | 0.03 | 87/21% |
| 743* | 1d core, vol≥1.5x + BTC>EMA50, mk 0.5ATR, s≥4% t3R h168 | 90 | +0.194 | +0.176 | 2.44 | 40 | −0.045 | −0.098 | −0.84 | 0.04 | 95/57% |
| 545 | 1d BTC +3ATR/3d, mk 0.25ATR, s≥5% no tgt h168 | 89 | +0.273 | +0.129 | 1.88 | 30 | +0.029 | −0.574 (1 day) | 0.25 | 0.06 | 93/88% |
| 863 | 1d core, BTC +2ATR/3d + BTC up, s≥3% h24 | 101 | +0.051 | +0.032 | 1.78 | 25 | −0.005 | −0.022 | 0.70 | 0.04 | 98/69% |
| 623 | 1d ret +4ATR/6d, mk 0.5ATR, s≥4% t1.5R h24 | 176 | +0.053 | +0.040 | 1.75 | 42 | −0.052 | −0.073 | −0.93 | 0.03 | 97/39% |
| 855 | 1d ret +3ATR/12d, mk 0.5ATR, s≥5% t3R h96 | 510 | +0.110 | +0.090 | 1.68 | 105 | −0.300 | −0.365 | −0.72 | 0.10 | 98/24% |
| 861 | 1d core, BTC +3ATR/6d, s≥3% no tgt h168 | 70 | +0.249 | +0.147 | 1.54 | 12 | −0.033 | −0.457 | 0.66 | 0.13 | 90/73% |
| 869 | 1d core, wick + stretch↓ + pullback 3ATR, s≥4% t3R h168 | 63 | +0.115 | +0.069 | 1.38 | 31 | −0.038 | −0.170 | −0.83 | 0.06 | 77/76% |
| 688 | 4h core weekend, mid vol + >EMA200, s≥4% h168 | 147 | +0.183 | +0.035 (1 day 81%) | 1.09 | 45 | −0.316 | −0.514 | −2.31 | 0.14 | 86/45% |
| 797 | 1h weekday downtrend + BTC down, mk 0.5ATR, s≥4% t2R h24 | 6445 | −0.199 | −0.202 | 1.07 | 2587 | −0.200 | −0.207 | −0.12 | 0.15 | 11/42% |
\* seen once on CHECK in v1, so this is look 2. "rand pct" = share of random-entry reps (same windows, pair counts, entry and exits) that the setup beats.
- **Reading:** the FIT near-misses are 1d/4h "buy strength in an uptrend" longs. They beat random entries on FIT (77-98%) but not on CHECK. That fits riding the 2021/2023-24 bull market rather than timing.
- **Next (round 3, needs a fresh pre-registration):**
  1. Rebuild the price data from a cleaner source, e.g. Coinbase public candles, used for signals only, with fills and costs kept on Alpaca.
  2. Test regime-conditioned daily trend/momentum on BTC/ETH/SOL against a buy-and-hold baseline, not just random entries.
  3. Probe one or two flush variants on 1-min/5-min data with an external liquidation feed.
  4. Re-check r1 for bad prints (its 15m/60m targets may have filled on spikes; it was all negative anyway).
