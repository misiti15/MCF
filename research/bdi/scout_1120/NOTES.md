Educational only — not financial advice

# Outside-ideas scout — 2026-11-20 (second run, with test step)

Strictly read-only toward every source. No user names or personal data recorded. Reddit (incl. r/ai_trading, asked about today) is blocked for anonymous reads (403 / login redirect) and awaits the owner's "REDDIT-YES" for official API access: not tried, not worked around (SOURCES.md).

## Sources

| Source | Reachable | Items scanned | Notes |
|---|---|---|---|
| arXiv q-fin.TR / ST | yes | 40 (11-03..11-19) | One on-topic: 2611.09286 end-of-day reversal replication (context, below). Rest LLM agents, energy, crypto, execution theory |
| Quantocracy | yes | 50 (2 new since 11-19) | New: forced-flow podcast (vague), stock perps (crypto venue) |
| Quantpedia | yes | 10 | Nothing new since 11-16 (Peak of Everything: valuation, not intraday) |
| Robot Wealth | yes | 12 | No post since 10-13 |
| Alpha Architect | yes (blocked 11-19) | 5 | Illiquidity premium, value/momentum, loans — not intraday |
| Elite Trader | yes | 15 | Journals, futures bots, chatter |
| Hacker News | front page yes, search no | 30 | One market headline (Nasdaq erases 2026 gains), no strategy items |
| TradingView ideas | yes | 24 titles | Chart calls (double tops, triangles), no rule specs |
| WebSearch | yes | 8 standard + 1 extended | ~150 result links; LETF rebalancing, intraday momentum/reversal, down-day RS, market-structure notices |
| SSRN | no (403, 2nd run) | 0 | skip, retry Monday 11-23 |
| SEC / FINRA / exchange pages, ETF issuers (ProShares, Direxion) | no (proxy) | 0 | notices reached via WebSearch only |

Reachable 9 of 13. Items about 186 + 9 searches.

## Ideas kept (2) — both in research/backlog.jsonl

1. **scout-1120-letf-rebalance-close-long (LETF1) — TESTED, FAIL 0 of 4, parked.** Mechanism: leveraged / inverse ETPs rebalance near the close in the direction of the day's move, so a big move should extend into the close (Cheng-Madhavan / Rodier et al. 2012, Chan 2013 via CXO and QuantRocket; Aug 2026 JPMorgan note on ~$150B of rebalance selling via Advisor Perspectives). Chosen because it addresses three of today's live lessons at once: inverse / vol ETPs among the top long movers with no setup buying them (BDI), correlated leveraged-ETF long bursts (NM-ETF −12.6R), and late-day shorts riding index direction (lateqshort_1120) — LETF1 is the explicit, borrow-free form of that index-direction-into-the-close bet.
2. **scout-1120-spy-intraday-asymmetry-day-gate (ASYM1) — idea, descriptive check only.** Prior-day SPY intraday asymmetry A = ((H−O) − (O−L)) / (H−L); A(t−1) < 0 is followed by stronger session-t open→close returns (SSRN 6074846, read only via a WebSearch summary). A pre-open day gate for the long book (rootcause_1119: long losses were market beta).

## Test — LETF1 (research/bdi/scout_1120/letf_close_bt.py → letf_close_bt_out.txt)

Pre-registered in the script header before the run. E2 2-year screen on the lab frames (2024-10..2026-11-04, 446 sessions), production + time-of-day costs, locked block 2024-11-01..2025-02-28 never read. Rule: buy the equity LETF (33 in the lab, adv20 ≥ $95M, price ≥ $5) that is already up ≥ |L|·X % from the open at the entry bar; t1s1; flat 15:55. Grid X {0.75, 1.25} × entry {14:30, 15:00} = **4 configs** (Testing bar t 1.50, full bar 1.67).

| Config | n (per session) | avg R | t | w/o best day | TRAIN / VALID / LATE | SPY up / down / quiet | WF months + | bull / inverse |
|---|---|---|---|---|---|---|---|---|
| X0.75, 14:30 | 2,570 (5.8) | −0.092 | −2.87 | −0.098 | −0.084 / −0.087 / −0.234 | −0.011 / −0.134 / −0.212 | 23% | −0.053 / −0.173 |
| X0.75, 15:00 | 2,665 (6.0) | −0.046 | −1.50 | −0.051 | −0.017 / −0.049 / −0.316 | +0.004 / −0.057 / −0.145 | 45% | −0.014 / −0.108 |
| X1.25, 14:30 | 1,565 (3.5) | −0.093 | −2.47 | −0.101 | −0.081 / −0.096 / −0.183 | −0.037 / −0.112 / −0.188 | 23% | −0.071 / −0.144 |
| X1.25, 15:00 | 1,592 (3.6) | −0.035 | −0.98 | −0.044 | −0.013 / −0.027 / −0.294 | −0.003 / −0.038 / −0.106 | 45% | −0.018 / −0.076 |

- **Every finalist reported; none passes.** No `1 day` issue (w/o best day is within 0.01R of the average: the losses are spread out, not one bad day).
- **Random entries:** the same symbol-days entered at a random bar 10:00–15:00 averaged +0.24..+0.30R (200 draws, rule at the 0th percentile). That control is biased upward — the symbol-days were picked *because* the ETP was already up at 14:30/15:00, so earlier entries ride the move — but the rule's raw t fails regardless.
- **What it says about today's lessons:** buying inverse funds late on down days is the worst pocket (−0.08..−0.17R). The inverse-ETP mover gap BDI sees is a morning / midday move, not closing-flow continuation; after 14:30 the move has more often been spent. LATE (10-06..11-04) is the worst split (−0.18..−0.32R): recent afternoons have reversed more than they extended — consistent with lateqshort_1120's finding that late shorts win only when the index keeps falling. Sector LETFs at 15:00 are the only non-negative pocket (+0.003 / +0.017R, n 502 / 319): not a pass, no salvage run (would be tailoring).
- **Remedies view:** n/a (not a remedy). No live, config or ledger change.

## Descriptive check — ASYM1 (asym_check.py → asym_check_out.txt, 1 config)

444 open sessions: A(t−1) < 0 → SPY o→c +0.086% (t 1.26), equal-weight lab names +0.112% (t 1.53); A(t−1) ≥ 0 → SPY −0.029%, EW −0.040%. Direction agrees with the source (gap ≈ +0.12–0.15 pt), but 2026 shows almost no difference (+0.002 vs +0.020). Worth one 4-config trade-list test on the top10 long setups (spec in the backlog line), no more.

## Seen and skipped (by mechanism)

- End-of-day reversal of intraday losers, 2023–26 replication (arXiv 2611.09286: 3.05 bps/day ex-mega-caps, ~0 in 2020–22, 2023 carries most of it) — already `wi-eod-reversal` (EODREV1 failed 11-18 as an entry; supports the exit form swing1118-L15). Its regime pattern (works in some years, zero in others) parallels MCF's long-MR regime split; no new rule.
- JPMorgan stock intraday momentum (buy above prior close by 1% on 5-min bars, flat at close; best for volatile names on volatile days; via Bloomberg/Advisor Perspectives) — covered by bdi-rdt-r06-red-green (128 configs), t7-noise-band, BEG-05 noise area / market momentum.
- Relative strength on market-down days (practitioner screens, Schaeffer's 12-event study) — covered by t4-rel-strength, bdi-rdt-r16, reddit-1030-rs-spydip-orh-long.
- "Asymmetric Reversals" (NBER w35840) — daily / weekly horizon.
- Forced-flow podcast (Trading the Breaking) — no rule.
- First-half-hour → last-half-hour (Gao et al.) — `intraday-momentum-paper` already in the backlog (idea).
- TradingView chart calls, Elite Trader futures bots — no testable US-stock intraday rule.

## Context (not ideas)

- **23/5 trading:** FINRA/Nasdaq TRF changes from 11-02 ahead of expanded hours on **2026-12-06**, with a market-wide circuit-breaker rule change before it (FINRA weekly 11-11). Overnight trading may change gap / opening dynamics that several setups key on (gap prefilters, ORB, L3 gap family) — worth a housekeeping watch after 12-06, not a setup.
- NYSE ETP closing-auction pricing tied to end-of-day NAV (March 2026 filing, effective on filing) — affects closing prints of ETPs, not our 15:55 flatten.

## Rule-change context

Backtests apply today's rules to every session, so no rule change falls inside them. The lab data ends 2026-11-04; the live rule changes of 11-05..11-20 (ledger: low-rep homes, LR8 cost model 11-12, Testing D/E/F 11-12, half-size Testing lots 11-17, Workbench / SPYEXIT 11-17) do not touch these figures.

## Links

- https://www.cxoadvisory.com/volatility-effects/front-running-leveraged-etfs-at-the-end-of-the-day
- https://quantrocket.com/blog/leveraged-etf-intraday-momentum
- https://www.advisorperspectives.com/articles/2026/08/10/leveraged-etf-boom-new-ways-profit-bursts-volatility
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6074846 (not read directly; SSRN blocked)
- http://arxiv.org/abs/2611.09286
- https://www.finra.org/compliance-tools/weekly-archive/11112026
- https://quantocracy.com/

Educational only — not financial advice.
