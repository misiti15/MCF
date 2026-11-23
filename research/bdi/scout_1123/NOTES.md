Educational only — not financial advice

# Outside-ideas scout — 2026-11-23 (Monday; light-to-moderate run, 1 idea tested)

Strictly read-only toward every source. No user names or personal data recorded. Reddit awaits the owner's "REDDIT-YES" (not tried, not worked around). Monday retries: SSRN and HN search (Algolia), both skipped after 2 failures, were retried once and failed again.

## Sources

| Source | Reachable | Items scanned | Notes |
|---|---|---|---|
| arXiv q-fin.TR / ST (export API) | yes | 40 (11-04..11-20) | On-topic only as context: "Trading Before a Committed Rebalance" (2611.25762, execution game, no rule), "Making sense of rule 605", EOD-reversal replication (2611.09286, seen 11-20). Rest LLM agents, energy, crypto, execution theory |
| Quantocracy | partial | 0 | Front page returns 200 but the post list is no longer in the static HTML (blog roll only); /feed/ empty. Not worked around |
| Quantpedia | yes | 6 | Nothing new since 11-17 (Black Friday deal, Peak of Everything, capacity of anomalies) |
| Robot Wealth | yes | 1 | No post since 10-13 |
| Alpha Architect | yes | 5 | Loans, illiquidity, cybersecurity, value/momentum — not intraday |
| Elite Trader | yes | 15 | Journals, futures, "NVDA the great short squeeze of the day" (chatter, no rule) |
| Hacker News front page | yes | 30 | One market headline (Nvidia CEO reinstated), no strategy items |
| Hacker News search (Algolia) | no (Monday retry) | 0 | connection refused again; skip, retry Monday 11-30 |
| TradingView ideas | yes | 23 titles | FX / gold / crypto chart calls, no US-stock rule specs |
| WebSearch | yes | 8 standard searches, ~110 links | trend-day detection, intraday momentum, SEC/exchange rule changes, new ETF launches, short-squeeze studies, trader rules |
| SSRN | no (Monday retry, 403) | 0 | skip; items seen via WebSearch summaries only |
| SEC / FINRA / exchange pages (direct) | no (proxy, 2nd run) | 0 | skip, retry Monday 11-30; notices via WebSearch |
| ETF issuers (Tradr, GraniteShares, ProShares, Direxion) | no (proxy, 2nd run) | 0 | skip, retry Monday 11-30; launches via WebSearch |
| MCF own gaps | yes | backlog 1,138 lines | used to dedupe by mechanism (research/bdi/GAPS.md does not exist) |

Reachable 10 of 14 tried (Quantocracy partial). Items about 120 + 8 web searches.

## Screened and dropped (already in the backlog by mechanism, or not testable)
- Trend-day detection (TICK / breadth / initial-balance extension, TraderFeed, TradingView IB scripts): covered by bdi1016-dayclass-direction-gate (84 configs), ix-gate, REGSW Phase 1 (GAP-U), wi-ib-narrow-extension, and tonight's L18 (counter-index gap-down shorts on SPY gap-up days: fails, t +0.31). Nothing new.
- First-half-hour → last-half-hour intraday momentum (Gao et al.; Baltussen et al.): intraday-momentum-paper exists.
- ORB on stocks in play (Zarattini et al.): 4 backlog lines exist.
- Generic gap-and-go / VWAP-reclaim guides: vague, course/marketing content; covered by bdi-rdt-r02, sat1031.
- **Market-structure news (no rule, context):** Anthropic (ANT) listed 11-19; 2x long / short single-stock ETFs (Tradr ANTT/ANTZ on Cboe from 11-23; GraniteShares AIL/ANS announced 11-17) — new leveraged products to watch for borrow and rebalance flow (LETF1 closing-flow continuation failed 11-20). Nasdaq 23-hour session approved April 2026, launch waits on SIP overnight hours; NYSE American extended-hours auction filing (SR-NYSEAMER-2026-34) pending. No closing-auction change found for November.

## Ideas kept (2) — both in research/backlog.jsonl
1. **scout-1123-day2-jump-fade (SQZR1) — TESTED, FAIL 0 of 8, parked.** Liquid stocks that jump ≥ 15% in a day reverse the next day; the effect sits in the most-shorted names (−3.25% top decile vs −0.30% overall; SSRN 2019361, PKU-hosted PDF, read via WebSearch summary; CXO short-squeeze timeline). A day-2 family MCF lacks, timely after NVDA ~+31% today. Mirror long (day 2 after a ≥ J% drop) tested as the long form.
2. **scout-1123-day2-jump-fade-si (SQZR2) — idea.** SQZR1 limited to top-decile crowding (FINRA short-volume ratio / short interest) plus a no-strong-index-up-day guard. Needs FINRA short-volume files (not on disk; finra.org blocked).

## Test — SQZR1 (research/bdi/scout_1123/sqzr_bt.py → sqzr_bt_out.txt)

Pre-registered in the script header before the run. E2 2-year screen on the lab frames (2024-10..2026-11-04, 446 sessions), production + time-of-day costs, locked block 2024-11-01..2025-02-28 never read. Non-ETP names, adv20 ≥ $95M, price ≥ $5. Grid J {8%, 15%} × trigger {T0 09:50 bar, T1 first 09:50–11:00 bar below/above open and VWAP} × side {fade-short, fade-long} = **8 configs** (Testing bar t 1.835, full bar 2.04). Exit t1s1 (stop 0.25 × daily ATR), flat 15:55.

| Config | n (per session) | avg R | t | w/o best day | best day share | TRAIN / VALID / LATE | SPY down / up / up > 1% | excess vs day-matched |
|---|---|---|---|---|---|---|---|---|
| short J8 T0 | 4,971 (11.2) | −0.022 | −0.31 | −0.083 | n/a (total < 0) | +0.058 / −0.081 / −0.122 | +0.256 / −0.157 / −0.539 | +0.011 |
| short J8 T1 | 3,469 (7.8) | +0.021 | 0.29 | −0.048 | 303% | +0.084 / −0.026 / −0.149 | +0.245 / −0.079 / −0.506 | −0.002 |
| short J15 T0 | 1,091 (2.4) | +0.053 | 0.51 | −0.027 | 144% | +0.159 / −0.091 / +0.007 | +0.321 / −0.164 / −0.521 | +0.017 |
| **short J15 T1** | 782 (1.75) | **+0.122** | 1.38 | +0.045 | 69% (`1 day`) | +0.156 / +0.086 / −0.168 | +0.269 / −0.014 / −0.474 | +0.020 |
| long J8 T0 | 4,188 (9.4) | −0.152 | −2.38 | −0.195 | n/a | −0.166 / −0.136 / −0.170 | −0.447 / −0.038 / +0.447 | −0.039 |
| long J8 T1 | 2,662 (6.0) | −0.075 | −1.01 | −0.138 | n/a | −0.069 / −0.072 / −0.118 | −0.409 / −0.050 / +0.468 | −0.010 |
| long J15 T0 | 588 (1.3) | −0.236 | −3.45 | −0.249 | n/a | −0.349 / −0.070 / −0.157 | −0.479 / −0.090 / +0.643 | −0.034 |
| long J15 T1 | 343 (0.8) | −0.125 | −1.76 | −0.145 | n/a | −0.203 / −0.034 / −0.086 | −0.491 / +0.026 / +0.662 | +0.041 |

(SPY "up" = open→close +0.25..+1%; "up > 1%" counted separately. Excess = trade R minus the same-side 09:50 trade averaged over every eligible name that day.)

- **Every finalist reported; none passes.** Best: short J15 T1 +0.122R (t 1.38 < 1.835), w/o best day +0.045, the best session is 69% of total R (`1 day`), LATE (10-06..11-04) negative, walk-forward 50% positive months.
- **Random entries:** short configs beat the random-bar control (same symbol-days, 10:00–15:00, 200 draws; 100th pct), longs do not (0th pct). The control mixes later, cheaper bars, so it is a weak check; the day-matched baseline is the sharper one.
- **What it learned (optimistic read, honest numbers):** the jump itself adds almost nothing (+0.00..+0.04R over the day-matched baseline). Both sides are SPY-direction bets: day-2 fade shorts make +0.25..+0.32R on SPY down days and lose −0.47..−0.54R on SPY up > 1% days; the mirror longs lose −0.41..−0.49R on down days and make +0.45..+0.66R on up > 1% days. This is the same lesson as 11-23 (gap-down shorts fighting a +5% day) and rootcause_1119 (long losses = market beta): a stock-level short reason does not survive a strong index up-day. The salvage path is the crowding condition the source says carries the effect (SQZR2), not a looser grid.
- Rule-change context: backtests apply today's rules (costs, t1s1 geometry) to the whole window; no live setup is involved, so ledger rule changes inside the window do not affect these figures. Lab data ends 11-04.

## Links
- https://english.phbs.pku.edu.cn/uploadfile/2022/0329/20220329025242625.pdf (short-squeeze day-2 reversal, SSRN 2019361)
- https://cxoadvisory.com/short-selling/short-squeeze-timeline
- https://stocktwits.com/news-articles/business/others/tradr-s-leveraged-et-fs-on-anthropic-begin-trading-monday/cNbimI3R90s
- https://newsable.asianetnews.com/markets/graniteshares-introduces-2x-long-and-2x-short-anthropic-etfs-articleshow-syl19lu
- https://www.arnoldporter.com/en/perspectives/advisories/2026/04/sec-approves-nasdaq-proposal-to-expand-trading-hours?pdf=1
- https://www.sec.gov/file/34-106218 (NYSE American extended-hours auction filing)
- https://traderfeed.blogspot.com/2020/04/how-can-you-identify-trend-day-in-stock.html
- https://www3.nd.edu/~zda/intramom.pdf

Educational only — not financial advice.
