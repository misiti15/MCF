Educational only — not financial advice.
# Crypto round 1: random setups on Alpaca spot (engine E5 crypto, 2026-11-26)
**Verdict: costs kill everything.** None of the 500 draws is net positive on FIT, so nothing goes to the backlog. LOCKED stays sealed.
- **Data:** Alpaca public 1-min bars for 30 USD pairs, 2021-01-01..2026-11-25, 1.0 GB (`data/crypto/`, gitignored). 9 pairs go back to 2021-01; 11 list in 2025-26, so they appear only in CHECK and LOCKED. 60-94% of minutes have a print (`python -m mcf.crypto.data --coverage`).
- **Costs (taker, per round trip):** 50 bps fees (tier 1, 25/25) + the full quoted spread + 4 bps slippage (+5 on stops, ×3 on bars with no print). Sampled Alpaca spreads: BTC/ETH 12-35 bps, alts 23-117 bps (`spreads.json`). That is about 0.65-1.7% all-in, a median **0.70R per trade** (1.06R on 15m bars, 0.39R on 60m), while the median gross edge is +0.00R.
- **Splits** (committed in 5db333d216 before any scoring): FIT 2021-01..2024-12; CHECK 2025-01..2026-05-25; LOCKED 2026-05-26..11-25, never read.
- **Draws:** N = 500 (seed 20261126): 432 long, plus 68 short flagged research-only (Alpaca is long-only). Of the 292 draws with ≥ 100 FIT trades, 147 are gross-positive, **0 net-positive**, 0 eligible. Best net day-clustered t = −0.33, against a noise bar of sqrt(2 ln 500) = **3.53**. With maker-fee entries (sensitivity only), 2 draws are net-positive, best t 2.08, still below the bar.
- **Finalists:** none was eligible. Under the fallback written into `run_r1.py` before CHECK was read, the 10 best long near-misses (ranked by min of avg R and avg R w/o best day) were frozen in `finalists.json` and scored once on CHECK, for information only.

| id | setup (long) | FIT n | FIT avgR | FIT w/o best | CHECK n | CHECK avgR | CHECK w/o best | CHECK maker | vs random pct |
|---|---|---|---|---|---|---|---|---|---|
| 31 | 15m Asia-open vol≥3x + just below round, s4 t6 h24 | 113 | −0.047 | −0.075 | 29 | −0.265 | −0.328 | −0.157 | 73% |
| 477 | 60m US weekday just above round, s3 t6 h24 | 1771 | −0.072 | −0.077 | 894 | −0.122 | −0.131 | −0.061 | 45% |
| 459 | 60m US weekday just above round, s4 t3 h12 | 1894 | −0.092 | −0.095 | 973 | −0.081 | −0.086 | −0.036 | 95% |
| 52 | 60m US 4h breakout + 3 ATR over VWAP + vol≥2x, s3 t4 h8 | 337 | −0.122 | −0.142 | 97 | −0.320 | −0.336 | −0.236 | 12% |
| 209 | 60m weekday just above round, s3 t4 h6 | 3905 | −0.166 | −0.170 | 1905 | −0.162 | −0.166 | −0.099 | 98% |
| 452 | 60m weekday RSI≤30, s4 t3 h4 | 6429 | −0.183 | −0.186 | 3584 | −0.124 | −0.127 | −0.071 | 100% |
| 228 | 60m weekday BTC +2 ATR/30m with alt lagging ≥2 ATR, s2 t3 h24 | 477 | −0.164 | −0.193 | 96 | −0.516 | −0.611 | −0.425 | 0% |
| 116 | 60m Asia-range break + below round, s4 t3 h2 | 673 | −0.193 | −0.196 | 348 | −0.163 | −0.167 | −0.106 | 93% |
| 373 | 60m US weekday uptrend + stretch≥3, s3 t2 h24 | 828 | −0.185 | −0.196 | 410 | −0.186 | −0.205 | −0.109 | 57% |
| 320 | 60m weekday above round, s2.5 t6 h6 | 5648 | −0.204 | −0.206 | 2736 | −0.200 | −0.204 | −0.123 | 99% |

- **CHECK:** all 10 lose after costs, taker and maker alike. 8 of 10 are gross-positive, but only +0.01 to +0.07R. Several beat random entries in the same windows (93-100th percentile), but random entries lose too (−0.11 to −0.42R). Best-day share is undefined when total R < 0. No rule or ledger changes apply, since crypto is not live.
- **What would change it** (each needs a gross edge above the 0.4-0.7R cost, or a lower cost per R): (1) maker-only entries, saving about 0.1-0.4R per trade; (2) 4h-to-daily holds with stops ≥ 3-5% of price, pushing costs below 0.15R; (3) fewer, larger events (flushes or impulses ≥ 3-5%) on the tightest pairs (BTC, ETH, SOL); (4) fee tier 3 (10/20 bps); (5) a venue with tighter books.
- **Next:** round 2 = maker-entry fills with realism (a trade must go through the limit price), 4h/daily timeframes, BTC/ETH/SOL first. Same splits; N keeps counting from 500.
