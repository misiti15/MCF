Educational only — not financial advice

# Outside-ideas scout — 2026-11-25 (Wednesday, after the close; normal run, 2 ideas tested)

Context used for judging: 11-25 was a midday short squeeze (SPY −0.6% → +2.1% from the open; shorts about −1,483R across accounts, longs +256R). Primary is about 80% short. Two "buy after the V" ideas already failed tonight (L19 −0.120R, VRL-1125 +0.036R) and are not re-proposed. The gap named: a long gate that predicts the CLOSE, not the moment. Strictly read-only toward every source; no user names or personal data recorded. Not Monday, so skipped sources were not retried.

## Sources

| Source | Reachable | Items scanned | Notes |
|---|---|---|---|
| arXiv q-fin.TR / ST / PM (export API) | yes | 40 (11-10..11-24) | New since 11-24: streaming portfolio optimisation, semivariance portfolios, correlation cleaning, "Trust and Lottery-Related Anomalies" (monthly). No intraday rules |
| Quantocracy | yes | 50 | New: "Fitting blunt instrument weights", "Minervini's trend template on the S&P 500", "Gold PM fix reversal", "Short the dollar in Asian hours", "Herding, anti-herding". All daily/FX/futures — dropped |
| Quantpedia | yes | 10 | Nothing new since 11-17 |
| Robot Wealth | yes | 12 | No post since 10-13 |
| Alpha Architect | yes (RSS) | 5 | Same 5 posts as 11-24 |
| Elite Trader | yes | 15 | "NVDA the great short squeeze of the day", "Can a backtest with 274 positions still owe its gains to a handful of trades?" (our one-big-day rule, no rule spec), 0DTE ledger, journals |
| Hacker News front page | yes | 30 | No strategy items |
| TradingView ideas | yes | ~30 titles | Symbol tiles only (indices, FX, crypto) |
| WebSearch (standard) | yes | 6 searches, ~85 links | close-predicting intraday studies, trader rules, SEC/exchange auction changes, new leveraged ETFs, overnight/intraday clientele papers |
| fmg.ac.uk (paper PDF, one fetch) | no | 0 | outside the session network; not worked around (read via WebSearch summary) |
| MCF own gaps | yes | backlog 1,184 lines | dedupe by mechanism |
| Skipped (not Monday) | — | — | SSRN, HN search, SEC/FINRA direct, ETF-issuer pages; Reddit awaits REDDIT-YES |

Reachable 10 of 10 regular sources tried (plus 1 one-off PDF host blocked). Items about 192 + 6 web searches.

## Screened and dropped
- Market intraday momentum (first / rest-of-day → last half hour, Gao et al., Baltussen et al.): covered by intraday-momentum-paper, bdi-tg-intraday-momentum (parked), beg-1120-mim-volday-gate (parked).
- Stock-level last-30-minute reversal (Notre Dame EOD paper): covered by wi-eod-reversal and the 2611.09286 replication.
- Same half-hour continuation (Heston-Korajczyk-Sadka): wi-same-halfhour, closed 11-17.
- Cross-firm overnight spillover that reverses intraday (JFQA 2025): a gap-fade short; covered by the gap-fade families and papers-1119-fade-intraday-component.
- Opening-volume ratio → last-half-hour direction (IJFS 2026): Chinese market only.
- Trader rule searches: TradingView/Tradervue chart posts, no explicit rule sets.
- **Market structure (context, no rule):** Texas Stock Exchange filing to change its opening/closing auctions (SEC 34-105837, proposed). Anthropic 2x products (Tradr ANTT/ANTZ, GraniteShares AIL/ANS) already noted 11-23. No closing-auction change for NYSE/Nasdaq found for November.

## Ideas kept (3) — all in research/backlog.jsonl
1. **scout-1125-ongate1-overnight-drift-gate (ONGATE1) — TESTED, FAIL 0 of 8, parked.** Lou, Polk & Skouras (2026, FMG DP961): smoothed past overnight market returns negatively forecast the intraday component. A pre-open gate that predicts the close — the gap named tonight.
2. **scout-1125-tow-intraday-long (TOWID1) — TESTED, FAIL 0 of 4, parked.** Tug of War (LPS, JFE 2019) at the session horizon: long stocks with strong trailing intraday-minus-overnight returns, or weak trailing overnight returns. Intraday form of the parked weekly ONID.
3. **scout-1125-ongate2-follow-overnight-drift (ONGATE2) — idea, post-hoc lead.** The sign-reversed form that ONGATE1's complement days showed (see below). Needs an independent sample (2023-24 SPY dailies, or a forward shadow), ≤ 2 configs.

## Test (research/bdi/scout_1125/onid_bt.py → onid_bt_out.txt)

Pre-registered in the script header before the run. E2 2-year screen on the lab frames (2024-10..2026-11-04, 446 sessions), production + time-of-day costs, locked block 2024-11-01..2025-02-28 never read (the trailing overnight series drops any pair across a > 5-day calendar gap). Exit t1s1 (stop 0.25 × daily ATR, 1R target), flat 15:55, entry 09:50 bar. **Configs 12** (ONGATE1 8, bar t 1.835; TOWID1 4, bar t 1.499; run-total bar 2.006). Controls: ONGATE1 vs 200 random draws of the same number of sessions for the same vehicle and side; TOWID1 vs random entry bars on the same symbol-days and vs the day-matched all-stock 09:50 long.

| Config | n (per session) | avg R | t | w/o best day | best-day share | TRAIN / VALID / LATE | SPY down / up / up > 1% | control |
|---|---|---|---|---|---|---|---|---|
| ON5 IDX LONG (ON5 < 0) | 540 (1.21) | −0.187 | −3.04 | −0.194 | n/a (total < 0) | −0.198 / −0.215 / +0.027 | −0.598 / +0.230 / +0.223 | 0th pct; other days +0.027 |
| ON5 IDX SHORT (ON5 > 0) | 783 (1.76) | −0.192 | −3.79 | −0.197 | n/a | −0.277 / −0.092 / +0.030 | +0.439 / −0.661 / −0.875 | 0th pct; other days +0.037 |
| ON5 STK LONG | 137,200 (308) | −0.116 | −5.04 | −0.121 | n/a | −0.162 / −0.085 / −0.069 | −0.295 / +0.037 / +0.185 | 0th pct; other days −0.056 |
| ON5 STK SHORT | 194,739 (437) | −0.118 | −6.22 | −0.121 | n/a | −0.163 / −0.073 / −0.036 | +0.109 / −0.252 / −0.552 | 0th pct; other days −0.052 |
| ON20 IDX LONG (ON20 < 0) | 300 (0.67) | −0.071 | −0.80 | −0.082 | n/a | +0.003 / −0.173 / +0.183 | −0.566 / +0.506 / +0.333 | 44th pct; other days −0.056 |
| ON20 IDX SHORT | 978 (2.19) | −0.105 | −2.33 | −0.108 | n/a | −0.159 / −0.047 / −0.060 | +0.450 / −0.540 / −0.916 | 37th pct; other days −0.075 |
| ON20 STK LONG | 76,220 (171) | −0.085 | −2.23 | −0.093 | n/a | −0.076 / −0.101 / −0.007 | −0.322 / +0.097 / +0.241 | 44th pct; other days −0.079 |
| ON20 STK SHORT | 247,656 (555) | −0.096 | −6.14 | −0.098 | n/a | −0.118 / −0.079 / −0.058 | +0.096 / −0.229 / −0.549 | 26th pct; other days −0.074 |
| TOWID1 K10 TOP | 33,150 (74) | −0.067 | −3.93 | −0.069 | n/a | −0.066 / −0.066 / −0.084 | −0.271 / +0.064 / +0.244 | excess +0.015R; random-bar 26th pct |
| TOWID1 K10 LOWON | 32,714 (73) | −0.067 | −3.69 | −0.070 | n/a | −0.056 / −0.083 / −0.019 | −0.324 / +0.101 / +0.314 | excess +0.016R; 26th pct |
| TOWID1 K20 TOP | 32,585 (73) | −0.061 | −3.51 | −0.063 | n/a | −0.054 / −0.069 / −0.056 | −0.283 / +0.062 / +0.326 | excess +0.019R; 83rd pct |
| TOWID1 K20 LOWON | 32,159 (72) | −0.073 | −3.95 | −0.075 | n/a | −0.071 / −0.076 / −0.058 | −0.322 / +0.085 / +0.331 | excess +0.007R; 16th pct |

(SPY "up" = open→close +0.25..+1%; "up > 1%" counted separately.)

- **Every finalist reported; none passes; nothing qualifies for Testing.** No DECISION card.
- **What it learned (optimistic read, honest numbers):**
  - The LPS sign does **not** hold at the session horizon in 2024-26. At K = 5 the intraday market **continued** the trailing overnight drift: index longs after a negative 5-day overnight drift −0.187R vs +0.027R on the other days; index shorts after a positive drift −0.192R vs +0.037R on the other days. That complement is the salvage lead ONGATE2 — post-hoc, so it is logged as an idea that needs an independent sample, not as evidence. At K = 20 there is no separation.
  - **Regime flag:** ON20 < 0 never occurred in the 2024 lab months (0% of sessions) vs 23-25% in 2025-26. The overnight-drift regime differs by period, a candidate input for the 2023-24 vs 2025-26 split of long mean-reversion (needs 2023-24 data to check).
  - TOWID1's stock selection adds only +0.007..+0.019R over the all-stock long; every long here is again an SPY-direction bet (down days −0.27..−0.32R, up > 1% days +0.24..+0.33R). Same lesson as L19 / VRL-1125 tonight: after costs the edge is index direction, so the open problem stays a pre-open or early read of the CLOSE.
- 11-19 failure modes (rootcause_1119): nothing new found tonight that explains them.
- Rule-change context: backtests apply today's rules (costs, t1s1 geometry) to the whole window; no live setup is involved, so ledger rule changes inside the window do not affect these figures. Lab data ends 11-04.

## Links
- https://www.fmg.ac.uk/sites/default/files/2026-07/DP961.pdf (LPS 2026; via WebSearch summary, not opened)
- https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
- https://personal.lse.ac.uk/loud/LouPolkSkouras.pdf
- https://www3.nd.edu/~zda/intramom.pdf ; https://www3.nd.edu/~zda/EOD.pdf
- https://jfqa.org/wp-content/uploads/2025/10/25681_Decoding_Spillover_JFQA_MS.pdf
- https://www.mdpi.com/2227-7072/14/2/47
- https://www.sec.gov/files/rules/sro/txse/2026/34-105837.pdf
- https://quantocracy.com/

Educational only — not financial advice.
