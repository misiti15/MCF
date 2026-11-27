Educational only — not financial advice

# Outside-ideas scout — 2026-11-27 (Friday half day, after the close; normal run, 2 ideas tested)

Owner said "max out usage" tonight, so the test step ran. Tonight's waves are cited, not redone, and new ideas were deduped against them by mechanism: research/wave3_1127 (intraday momentum, stop floors, mover ranker, breadth gate, GEN siblings, QQQOPEN), research/wave4_1127 (index dip family, day-type, pairs vs sector ETF, gap-news direction, afternoon SPY direction), L3REFIRE-1127, BDI 11-27, and wave 5 (opendrive, longbook, upday, idxfwd, running). Strictly read-only toward every source; no user names or personal data recorded. Not Monday, so skipped sources were not retried.

## Sources

| Source | Reachable | Items scanned | Notes |
|---|---|---|---|
| arXiv q-fin.TR / ST (export API) | yes | 40 (11-06..11-25) | New: "Trading Before a Committed Rebalance" (execution game, no rule), "Do Candlestick Charts Suffice?" (China, daily), Rule 605 paper, global seasonality (futures). No intraday US rule |
| Quantocracy | yes | 25 | Answers 400 to a bare client; the normal browser user-agent loads it (a request header, not an access block). New: "month-end rebalancing" and "news release 30 minutes" (fx2owl, FX; host outside the session network), "When the market has no choice" (quantbeckman, blocked host), RSI2 / Donchian replications (daily) |
| Quantpedia | yes | 10 | Nothing new since 11-17 |
| Robot Wealth | yes | 12 | No post since 10-13 |
| Alpha Architect | yes (RSS) | 5 | Same posts as 11-26 |
| Elite Trader | yes | 15 | "RSI-5 provides evidence that any market can be timed" (no spec), 0DTE ledger, macro chatter |
| Hacker News front page | yes | 30 | No strategy items |
| TradingView ideas | yes | ~30 titles | Symbol tiles only |
| WebSearch (standard) | yes | 5 searches, ~50 links | ORB / relative strength rules, 2026 intraday-predictability papers, month-end pension rebalancing, NBER "Asymmetric Reversals", CESA intraday autocorrelation |
| nber.org, fernuni-hagen.de (one fetch each) | no | 0 | outside the session network; read via WebSearch summaries, not worked around |
| MCF own gaps | yes | backlog 1,194 lines | dedupe by mechanism |
| Skipped (not Monday) | — | — | SSRN, HN search, SEC/FINRA direct, ETF-issuer pages; Reddit awaits REDDIT-YES |

Reachable 10 of 10 regular sources tried (2 one-off paper hosts blocked). Items about 167 + 5 web searches.

## Screened and dropped
- ORB "stocks in play" (Zarattini et al.) and relative-strength-vs-SPY ORB filters: covered by the ORB / CWT families and OPENDRIVE-1127 tonight.
- Intraday momentum (Gao; first half hour → last half hour): failed tonight (WILDCARD-1127).
- End-of-day reversal after 2019 (arXiv, 11-06): already replicated (wi-eod-reversal, 2611.09286).
- Option half-day reversal (CFR 26-02): options only.
- Turn-of-month calendar: covered by sw-w3-calendar-near and ex30-TM5.

## Ideas kept (3) — all in research/backlog.jsonl
1. **scout-1127-mereb1-month-end-rebalance-close (MEREB1) — TESTED, FAIL 0 of 8, parked.** Month-end pension / balanced-fund rebalancing: after equities lagged bonds month-to-date, rebalancers must buy equities into the last session's close. Long side preferred; signal known before the open. New mechanism for MCF (forced calendar flow conditioned on equity-vs-bond MTD performance).
2. **scout-1127-asymrev1-idio-residual-reversal-long (ASYMREV1) — TESTED, FAIL 0 of 6, parked.** Baldi-Lanfranchi, Collin-Dufresne & Daniel (NBER 35840, 2026): beta residuals reverse, negative residual shocks faster than positive ones. Intraday long-only, one leg, unhedged (unlike the failed two-leg PAIRS tonight).
3. **scout-1127-midrev1-15min-idio-reversal-long (MIDREV1) — idea.** Baule, Schlie & Zhou (CESA WP 14): intraday autocorrelation is most negative at 15 minutes and stronger in smaller firms; continuation in large caps, under stress and in the first half hour. Short-hold long reversal in mid-caps from 10:00, stress days skipped. Cost risk flagged: test only if the gross edge clears about 0.10R.

## Tests (pre-registered in the script headers, committed before either run)

Configs this run: **14** (MEREB1 8 + ASYMREV1 6). Testing bar on the run total: t ≥ 0.9 × max(1.5, sqrt(2 ln 14)) = **2.067** (within-lineage bars 1.835 and 1.704 also printed). Locked block 2024-11-01..2025-02-28 never read (dropped at load and asserted for minute and daily data; months whose MTD base fell in it skipped).

### MEREB1 (research/bdi/scout_1127/mereb_bt.py → mereb_bt_out.txt)
SPY 1-min 2016-01..2026-11-04 (2016-22 SIP bars from the QQQOPEN-1127 scratch, read-only; cache_fresh; cache_hist), 124 month-ends. SPY/TLT daily SIP bars fetched GET-only from Alpaca for the signal. LIVE-L costs first, LR8 alongside. Stop 0.25 × ATR14, no target, flat 15:55.

| Config | n | avg R | t | gross / LR8 | w/o best day | EARLY / T2 / RECENT | vs random non-event days | complement |
|---|---|---|---|---|---|---|---|---|
| L S<0 14:00 | 44 | +0.051 | 0.26 | +0.280 / +0.186 | −0.047 | −0.415 / +1.167 (9) / +0.478 (7) | 98th pct | −0.246 |
| L S<−2% 14:00 | 24 | +0.107 | 0.40 | +0.315 / +0.237 | −0.074 | −0.443 / +1.358 (6) / +0.154 (4) | 95th | −0.199 |
| L S<0 15:00 | 44 | −0.089 | −0.59 | +0.143 / +0.051 | −0.138 | −0.493 / +0.503 / +0.765 | 96th | −0.135 |
| L S<−2% 15:00 | 24 | −0.179 | −0.86 | +0.028 / −0.049 | −0.273 | −0.574 / +0.121 / +0.755 | 79th | −0.104 |
| S S>0 14:00 | 79 | −0.239 | −1.71 | +0.047 / −0.131 | −0.319 | −0.149 / −0.288 / −0.538 | 60th | −0.503 |
| S S>+2% 14:00 | 57 | −0.161 | −0.93 | +0.131 / −0.048 | −0.271 | −0.023 / −0.297 / −0.531 | 80th | −0.482 |
| S S>0 15:00 | 79 | −0.474 | −4.48 | −0.195 / −0.378 | −0.516 | −0.600 / −0.059 / −0.459 | 1st | −0.272 |
| S S>+2% 15:00 | 57 | −0.344 | −2.66 | −0.055 / −0.236 | −0.399 | −0.503 / +0.077 / −0.269 | 17th | −0.452 |

Unconditional SPY 14:00/15:00 → 15:55 legs on non-event days: −0.25..−0.29R after LIVE-L (gross about 0), i.e. LIVE-L costs on a 0.25-ATR SPY stop are about 0.27R per trade.

### ASYMREV1 (research/bdi/scout_1127/asymrev_bt.py → asymrev_bt_out.txt)
E2 2-year screen on the lab frames (446 sessions), production + time-of-day costs, t1s1, flat 15:55; adv20 ≥ $95M, price ≥ $5, non-ETP.

| Config | n (per session) | avg R | t | w/o best day | TRAIN / VALID / LATE | SPY down / up / up > 1% | excess vs all-stock long |
|---|---|---|---|---|---|---|---|
| L CLOSE 11:00 | 3,648 (8.2) | −0.071 | −3.11 | −0.074 | −0.081 / −0.042 / −0.238 | −0.154 / +0.020 / +0.080 | +0.005 |
| L OPEN 11:00 | 2,924 (6.6) | −0.081 | −3.24 | −0.084 | −0.106 / −0.051 / −0.137 | −0.147 / −0.021 / +0.122 | −0.006 |
| L CLOSE 13:00 | 3,800 (8.5) | −0.067 | −2.91 | −0.069 | −0.097 / −0.038 / −0.073 | −0.231 / +0.028 / +0.184 | +0.007 |
| L OPEN 13:00 | 3,447 (7.7) | −0.080 | −3.59 | −0.083 | −0.087 / −0.074 / −0.086 | −0.235 / +0.031 / +0.110 | −0.001 |
| S mirror CLOSE 11:00 | 3,828 (8.6) | −0.076 | −3.55 | −0.079 | −0.122 / −0.021 / −0.192 | −0.009 / −0.140 / −0.196 | n/a |
| RAW-L control CLOSE 11:00 | 3,913 (8.8) | −0.063 | −2.73 | −0.066 | −0.065 / −0.028 / −0.321 | −0.140 / +0.043 / +0.080 | +0.015 |

The random-entry-bar control (same symbol-days, 10:00-15:00) is lower (−0.13..−0.32R) but that reflects hold length vs a fixed cost, not selection; it is not taken as evidence.

- **Every finalist reported; none passes; nothing qualifies for Testing.** No DECISION card.
- **What it learned (optimistic read, honest numbers):**
  - MEREB1's long side has the expected sign gross (+0.14..+0.32R) and beats random non-event days (95-98th pct), but LIVE-L costs on a one-hour SPY hold take about 0.27R, and the sign is not stable: negative in 2016-22 (t −2.6 at 14:00), positive 2022-26 on only 16 trades. The 2022+ flip is post-hoc and logged in the notes only; the next clean step is a forward shadow from the 2026-11-30 month-end (≤ 1 config), not a re-score. The short (sell-after-outperformance) side fails everywhere. A cheaper vehicle or a wider stop would cut the cost share, but that would be a new pre-registered test.
  - ASYMREV1: the beta residual adds nothing over raw losers intraday, and the paper's asymmetry does not show at this horizon (long −0.071 vs mirror short −0.076). Same lesson as 11-25 and tonight's waves: after costs the stock longs are SPY-direction bets (down days −0.15..−0.24R, up > 1% days +0.08..+0.18R).
- Regime flag (long MR 2023-24 vs 2025-26): nothing new; MEREB1's sign flip around 2022 is a separate calendar-flow regime, not the long mean-reversion split.
- 11-19 failure modes (rootcause_1119): nothing new found tonight that explains them.
- Rule-change context: backtests apply today's cost models and geometry to the whole window; no live setup is involved, so ledger rule changes inside the window do not affect these figures. Lab data ends 11-04.

## Links
- https://www.nber.org/papers/w35840 ; https://econpapers.repec.org/RePEc:chf:rpseri:rp2666 (via WebSearch summary)
- https://www.fernuni-hagen.de/igas/docs/cesa_wp_14.pdf ; https://optionmetrics.com/?p=2611 (via WebSearch summary)
- https://www.mnimarkets.com/articles/bnp-sketch-out-month-quarter-end-rebalancing-estimates-for-u-s-equities-bonds
- https://www.citadelsecurities.com/news-and-insights/global-market-intelligence/july/
- https://academic.oup.com/rfs/article/33/1/75/5494694 ; https://hulltactical.com/?p=1960
- http://arxiv.org/abs/2611.25762v1 ; http://arxiv.org/abs/2611.30584v1
- https://quantocracy.com/

Educational only — not financial advice.
