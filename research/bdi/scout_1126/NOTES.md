Educational only — not financial advice

# Outside-ideas scout — 2026-11-26 (Thursday, Thanksgiving; LIGHT run, test step skipped)

Light run: usage is tight after the 11-26 research day, so step 4 (testing) was skipped per the owner's condition (1). Context: consultants_1126 found MCF's setups are mostly index bets with a negative remainder after costs (regime steering, tape rules, SPY beta hedge and compass-index overlay all failed). So this run looked only for **stock-specific** edges (positive after removing the market move), long first. Strictly read-only; no user names recorded. Not Monday, so skipped sources were not retried.

## Sources

| Source | Reachable | Items scanned | Notes |
|---|---|---|---|
| arXiv q-fin.TR / ST / PM (export API) | yes | 40 (11-10..11-25) | New: Graph-Informed Deep Factor stat-arb (daily), "Trading Before a Committed Rebalance" (execution-game theory, no rule), rank-size weights, streaming optimisation. No intraday rules |
| Quantocracy | yes | 50 | New: "When the insiders and the news disagree" (idea 2), rough-vol model, Nasdaq vs S&P 40 years, news-release 30 minutes (FX), month-end dollar rebalancing (FX), part-time trader pt 7. Linked hosts (substack, fx2owl, quantbeckman) outside the session network — not worked around |
| Quantpedia | yes | 10 | Only a Black Friday promo since 11-17 |
| Robot Wealth | yes | 12 | No post since 10-13 |
| Alpha Architect | yes (RSS) | 5 | Same 5 posts |
| Elite Trader | yes | 15 | Risk-management lists, "100% win rate without stops", an AI day-trading video thread; no rule specs |
| Hacker News front page | yes | 30 | No strategy items |
| TradingView ideas | yes | ~30 titles | Symbol tiles (indices, FX, crypto) |
| WebSearch (standard) | yes | 4 searches, ~55 links | insider/news cross-signal, intraday earnings reaction, stock-vs-sector RS, S&P addition returns |
| MCF own gaps | yes | backlog 1,187 lines | dedupe by mechanism |
| Skipped (not Monday) | — | — | SSRN, HN search, SEC/FINRA direct, ETF-issuer pages; Reddit awaits REDDIT-YES |

Reachable 10 of 10 regular sources tried (plus 4 one-off article hosts from Quantocracy blocked by the session network). Items about 192 + 4 web searches.

## Screened and dropped
- Stock vs sector-ETF relative strength intraday: covered by sector-rs, sw-w2-rv-stock-etf, t4-rel-strength, R16 (parked).
- Intraday earnings reaction / sentiment reversal (Lund 2026 student paper, PEAD theses): covered by er-react-*, EVD1, cwt-a-a8, mh-1029-earnings-sympathy.
- FX news-release and month-end dollar rebalancing: FX only.
- "Trading Before a Committed Rebalance" (arXiv 2611.25762): theory, no rule; it supports the mechanism of idea 1.

## Ideas kept (2) — research/backlog.jsonl, status idea, not tested
1. **scout-1126-spx-add-flow-long (IDXADD1).** S&P 500 addition flow long: (A) first session after the announcement, long at 09:50 if price >= VWAP; (B) effective-date session, long at 14:30 ahead of index-fund closing demand; stop 0.25 x daily ATR, 1R, flat 15:55. Stock-specific forced-flow event; must be positive in excess of SPY at the same bars. Needs an announcement archive (S&P DJI press releases) reachable from the session network; forward shadow possible from the December rebalance.
2. **scout-1126-insider-cluster-buy-long (INSBUY1).** At least 2 distinct insiders' open-market Form 4 purchases, at least one filed since the prior 09:30, gives a long at 09:50 (A); divergence variant (B) only when the stock is down at least 5% vs SPY over 5 sessions; t1s1, flat 15:55. Needs EDGAR Form 4 history (sec.gov direct currently outside the session network).

Both carry 2 configs each, costs in, "must be positive after market adjustment" (excess vs SPY plus random-date controls), per-year split, w/o best day and best-day share.

Rule-change context: no figures are reported here and no live setup is involved, so ledger rule changes do not apply.

## Links
- https://tommijohnsen.substack.com/p/when-the-insiders-and-the-news-disagree (via WebSearch summary)
- https://247wallst.com/investing/2026/08/14/reddit-is-up-11-premarket-after-sp-500-addition-heres-how-other-new-sp-500-stocks-performed/
- https://global.morningstar.com/en-nd/funds/sp-500-bump-that-doesnt-last
- https://press.spglobal.com/2026-09-04-Bloom-Energy,-Illumina,-and-Everpure-Set-to-Join-S-P-500-Others-to-Join-S-P-100,-S-P-MidCap-400,-and-S-P-SmallCap-600
- http://arxiv.org/abs/2611.25762v1
- https://quantocracy.com/

Educational only — not financial advice.
