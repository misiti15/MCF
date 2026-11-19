Educational only — not financial advice

# Outside-ideas scout — 2026-11-19 (first run, light scan: Crunch Wave 2 running)

Scan, filter and log only; no tests tonight. Strictly read-only toward every source (no posts, votes, sign-ups or messages). No user names or personal data recorded.

## Sources tried

| Source | Reachable | How | Items scanned | Notes |
|---|---|---|---|---|
| arXiv q-fin.TR / ST / PM | yes | export.arxiv.org API, last 7 days | 20 unique | All LLM agents, portfolio construction, energy markets, factor seasonality; nothing intraday US-equity rule-based |
| SSRN | no | papers.ssrn.com returns 403 | 0 | One SSRN item seen via WebSearch (Heston-Korajczyk-Sadka periodicity revisit, SSRN 5749704, Nov 2025) — mechanism already in backlog (wi-same-halfhour, guild-1117-lasthalfhour-continuation) |
| Quantocracy | yes | daily list (front page) | 50 (about 30 from the last 7 days) | Main source tonight; linked substack / fx2owl / nulliusresearch pages blocked by the proxy, so only the summaries were read |
| Alpha Architect | no (direct) | blog + feed return 403 | 2 via Quantocracy | Illiquidity premium, value/momentum — not intraday |
| Robot Wealth | yes | RSS | 12 | No post since 2026-10-13; nothing new |
| Quantpedia | yes (curl) | RSS + article pages | 10 + 3 articles read | Correlation acceleration (kept), shorting leveraged ETFs (context, below), morning order flow (overnight hold, out of scope) |
| Reddit (Daytrading, algotrading, RealDayTrading, quant, StockMarket, swingtrading) | no | top/.rss?t=week, generic UA | 0 | 404 on 3 subs, 429 on 3; old.reddit redirects |
| Elite Trader | yes | forum RSS | 15 | FX EAs, journals, P/L posts — nothing testable |
| Hacker News | partial | front-page RSS ok; Algolia search blocked | 30 | No trading items |
| TradingView public ideas | yes | ideas page (titles only) | about 20 | Chart calls (triangles, double bottoms, BB squeeze) without rule specs |
| WebSearch (standard) | yes | 7 queries | about 95 result links, about 12 read | Trader-interview rules, microstructure changes, intraday-reversal regime papers |

Reachable: 8 of 12 (arXiv, Quantocracy, Robot Wealth, Quantpedia, Elite Trader, HN partial, TradingView, WebSearch). Items scanned: about 157 feed items + 7 web searches.

## Ideas kept (1)

1. **scout-1119-sector-corr-acceleration-gate** — cross-sector correlation-acceleration day gate for long mean-reversion families: gate ON for session t when the mean pairwise 20-day correlation of the 9 SPDR sector ETFs (closes through t-1) exceeds X x the 60-day mean (X 1.12-1.25 plateau in the source). Flags MCF's regime dependence: if the gate is on more often in 2023-24 than in 2025-26, it would explain part of why long MR failed then and worked now; and it targets the 11-19 failure mode where 13 of 14 losing lots were market beta, not idiosyncratic dips. Differs from the parked vol-level switch (regime1029 / p1_1029, 196 configs) by using correlation structure. Source: https://quantpedia.com/correlation-acceleration-detecting-market-stress-through-rising-etf-correlations/

## Seen and skipped (by mechanism)

- 5-minute ORB on ES (Nullius Research, https://nulliusresearch.substack.com/p/5-minute-opening-range-breakout-7217) — futures-only; ORB already covered (orb5, t2-orb15, bdi-rdt-r01-orb30).
- "Box theory" prior-day high/low fade on Nasdaq (Nullius, https://nulliusresearch.substack.com/p/box-theory-traded-blindly-3-of-4; 32.8% vs 75% claimed) — covered by obos-levels, CWT14 failed-break, bdi-reddit-pdhl-break-retest.
- Overnight-to-intraday gap reversal, stronger under market-wide uncertainty (2025 thesis via WebSearch; "day destroys the night") — gap fill (bdi-rdt-r05-gap-fill, 16 filter sets) and vol-regime gating (p1_1029, parked) already cover both halves.
- Stock vs sector residual reversion (NYSE price correlations, https://arxiv.org/pdf/2305.08241) — covered by sw-w2-rv-stock-etf.
- Quantpedia morning order-flow reversal on SPY (https://quantpedia.com/can-weakening-morning-order-flow-predict-spy-reversals/) — overnight / next-day hold, needs trade-at-bid/ask data; out of scope (flat by 15:55).
- News "move over in 30 minutes?" (fx2owl) — FX only, page blocked.
- Triple RSI / RSI(2) on SPY, Santa rally, pre-FOMC drift, Turtle/Donchian, 13F, insider, Congress copying — daily or longer.

## Context for open failure modes (not ideas)

- **Inverse-ETF shorts (rootcause_1119):** Quantpedia "Shorting Leveraged ETFs" (https://quantpedia.com/shorting-leveraged-etfs-the-role-of-borrowing-costs-and-rebalancing-in-volatility-decay-strategies/, 2026-10-23) — TQQQ/SQQQ short-pair returns are mostly eaten by borrow costs and concentrate in a few high-vol periods. Supports the proposed product-type guard (short setups never short market-inverse products); no new rule.
- **RSI warm-up bursts:** nothing found in outside sources.
- **Microstructure:** the SEC's 2024 tick-size / access-fee amendments (half-penny ticks for tick-constrained names) had a Nov 2026 compliance date that a June 2026 SEC action delayed; Rule 611 rescission proposed 2026-06-11 (Sidley, MoFo, MEMX via WebSearch). If ticks change, the spread part of the cost model for low-priced liquid names needs a re-check — housekeeping, not a setup.

## Links

- https://quantocracy.com/
- https://quantpedia.com/correlation-acceleration-detecting-market-stress-through-rising-etf-correlations/
- https://quantpedia.com/shorting-leveraged-etfs-the-role-of-borrowing-costs-and-rebalancing-in-volatility-decay-strategies/
- https://papers.ssrn.com/ab_id=5749704
- https://www.sidley.com/ja/insights/newsupdates/2026/06/sec-proposes-rescission-of-the-order-protection-rule
- https://flextrade.com/resources/secs-broader-reg-nms-overhaul-could-delay-access-fee-tick-sizes/

Educational only — not financial advice.
