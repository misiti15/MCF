Educational only — not financial advice.

# reddit_1030: Reddit setup scout (2026-10-30)

**Result: 1 new idea kept, 2 ideas tested on two years (the new one and yesterday's untested r/RealDayTrading idea),
0 pass. 10 configurations were scored (all listed below). BAR90 for N = 10 is 1.93; the best t was −2.97, so the locked
block (2024-11-01..2025-02-28) was not scored and there is no DECISION.** No config, setup, exit, ledger or docs/live
file was changed. Read-only toward Reddit (RSS GETs only). The owner-shared 15-min ORB + FVG / IRL→ERL post
(r/Trading 1xj2iho) is in research/bdi/rdt1030 and was not re-tested here.

## Sources
- Reddit RSS (`https://www.reddit.com/r/<sub>/{top,new,hot}/.rss`, UA `mcf-research/0.1`) worked, with heavy HTTP 429
  rate limiting; 3-4 passes with 7-15 s spacing got every feed except r/Stock_Picks (403). Feeds: top day / week and
  new for r/Daytrading, r/Trading, r/algotrading, r/ai_trading, r/RealDayTrading, r/quant, r/StockMarket,
  r/swingtrading, r/daytrade; top month for r/Daytrading, r/algotrading, r/RealDayTrading; hot r/Daytrading; top week
  for r/smallstreetbets, r/pennystocks and **r/TradingEdge (new source tried: market-news / premarket reports, no rules)**.
  Comment feeds read: 1x4yzux, 1xi1q9s, 1xeb4sm, 1xjmg9j.
- WebSearch (standard) was tried twice; as on 10-29 it returned no Reddit threads, so RSS is the source.
- **Posts scanned:** 473 unique posts; 307 dated 2026-10-27..10-30 (Daytrading 50, StockMarket 40, Trading 39,
  ai_trading 38, swingtrading 36, algotrading 21, smallstreetbets 20, daytrade 18, pennystocks 18, quant 14,
  TradingEdge 12, RealDayTrading 1). 18 matched >= 4 rule keywords; 31 were read in full.

## Filter (what was dropped)
A thin day for rules: the week was earnings + FOMC, and most posts were market news (Alphabet / Intel / Amazon
reactions), psychology, P/L, prop-firm, 0DTE / SPX credit spreads, gold / NQ / crypto, or tool promotion. Dropped:
- r/Daytrading 1xeb4sm (NQ, AMT): no trades in the first hour, then sweep of a prior high / low or GEX / value-area
  rejection, 1:2 RR — **duplicate by mechanism** of the sweep-reclaim family (bdi-rdt-r15-sweep failed,
  bdi-reddit-level-sweep-reclaim, CWT14 failed-break).
- r/swingtrading 1xjmg9j earnings read-through across a peer group — overlaps mh-1029-earnings-sympathy, and the
  post promotes a tool.
- r/algotrading 1x2owmo (100+ retail strategies with costs): daily / overnight findings (SPY dip-buy, month-end, residual
  momentum) — not intraday (its one intraday note, SPY 10:30→close negative 2023-26, is a drift statistic, not a setup).
- r/Trading 1xjdwyp (options "probability of touch" levels) and r/ai_trading 1xi7ye0 / 1xjrrdr (bot competition, rules
  withheld; "touch +0.5% above the open" rates without a random control) — vendor / no rules.
- r/swingtrading 1xgtsuq (only trade the last hour), r/Daytrading 1xje3qu (time-of-day "cup", rules withheld),
  r/Daytrading 1xj8v0z (gold Asian-session IFVG), 1xjmw8q (forex) — vague or not US stocks.

## Ideas (research/backlog.jsonl, tags reddit + scout)
| id | source | status |
|---|---|---|
| reddit-1030-rs-spydip-orh-long (new) | [r/RealDayTrading 1x4yzux, comment](https://www.reddit.com/r/RealDayTrading/comments/1x4yzux/whats_your_a_setup_in_each_market_condition_day/) | failed (4 configs) |
| reddit-1029-rdt-volconfirm-bounce (added 10-29, untested until today) | [r/RealDayTrading 1xi1q9s](https://www.reddit.com/r/RealDayTrading/comments/1xi1q9s/how_important_is_volume_for_confirmation_of_entry/) | failed (6 configs) |

## Tests (PLAN.md written before scoring; `make_modules.py`, `modules/`, `results.jsonl`)
Harness: research/bdi/pod1022/score_batch.py over the open two-year history, costs in (1c + 1 bp per side, time-of-day
multiplier, +2c stop fills, x3 extended tier), live earnings blackout removed, ADV20 >= $95M, long, GEOM S (structural
stop), same-minute random-entry control (hold), day-clustered t, regime1022 Bull / Bear sessions (hindsight labels).
TRAIN <= 2025-12-31, VALID 2026. WF = share of months with positive total R.

| config | n | avg R | t | train / valid | excess vs random | w/o best day | best-day share | Bull (n) | Bear (n) | WF months | trades/day |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RC1-volconfirm-ema8-vol-t2r | 197,874 | −0.237 | −14.49 | −0.246 / −0.228 | −0.131 | −0.240 | – | +0.107 (43,463) | −0.493 (34,436) | 0% | 464 |
| RC1-volconfirm-ema8-vol-hold | 197,874 | −0.269 | −9.73 | −0.264 / −0.274 | −0.162 | −0.275 | – | +0.333 | −0.687 | 0% | 464 |
| RC1-volconfirm-ema8-novol-hold (parent) | 222,843 | −0.241 | −9.18 | −0.231 / −0.251 | −0.124 | −0.246 | – | +0.348 | −0.676 | 0% | 523 |
| RC1-volconfirm-vwap-vol-t2r | 141,478 | −0.247 | −15.00 | −0.247 / −0.247 | −0.136 | −0.250 | – | +0.155 (25,451) | −0.495 (28,192) | 0% | 332 |
| RC1-volconfirm-vwap-vol-hold | 141,478 | −0.276 | −10.02 | −0.258 / −0.296 | −0.165 | −0.281 | – | +0.435 | −0.688 | 0% | 332 |
| RC1-volconfirm-vwap-novol-hold (parent) | 197,185 | −0.225 | −8.39 | −0.200 / −0.252 | −0.101 | −0.230 | – | +0.435 | −0.663 | 0% | 463 |
| RC2-rs-spydip-orh-d03-t2r | 5,629 | −0.146 | −4.84 | −0.143 / −0.148 | −0.035 | −0.154 | – | +0.307 (287) | −0.264 (2,698) | 14% | 13.2 |
| RC2-rs-spydip-orh-d03-hold | 5,629 | −0.178 | −4.84 | −0.162 / −0.190 | −0.067 | −0.187 | – | +0.646 | −0.359 | 10% | 13.2 |
| RC2-rs-spydip-orh-d06-t2r | 2,257 | −0.153 | −2.97 | −0.161 / −0.145 | −0.054 | −0.176 | – | +0.483 (89) | −0.236 (1,477) | 20% | 5.3 |
| RC2-rs-spydip-orh-d06-hold | 2,257 | −0.190 | −3.30 | −0.212 / −0.165 | −0.090 | −0.210 | – | +1.320 | −0.336 | 15% | 5.3 |

(best-day share is "–" because every total R is negative.)

- **RC1 volume-confirmed pullback bounce fails, and the volume sequence makes it worse.** The poster's filter (dry-up on
  the pullback to EMA8 / VWAP, bounce bar volume above it) loses more than the same pullback without it (EMA8 hold
  −0.269 vs −0.241R; VWAP hold −0.276 vs −0.225R). The 5-min pullback-in-an-RS-stock condition fires 330-520 times a
  day, so it is not the selective setup a discretionary trader picks; every arm wins in up sessions and loses in down
  sessions (market beta).
- **RC2 RS-during-SPY-pullback OR reclaim fails.** Below random in every arm, 10-20% positive months. About half the
  trades fall on Bear sessions: when SPY's pullback keeps going, the RS name follows it down. Bull sessions are positive
  (+0.31 to +1.32R) but on 89-287 trades and only knowable in hindsight. The comment's own "bull trend" condition
  (daily SPY regime) was not in the grid; a re-test would need a point-in-time daily trend gate.
- Limitations: no `open` / raw volume in the frames (green = close above prior close; volume = volumeRatio); "above the
  SMAs" uses the 5-min SMA50; the opening range is 09:30-09:50 (high of day at the 09:50 bar) because frames start
  at 09:50. Overlap with live setups (`--ref-config`) was not run since nothing passed.

## Next
- Nothing to promote. The RS-under-SPY-stress idea is the only one with a plausible gate left (point-in-time daily SPY
  trend); it should be tried only together with an existing daily-regime gate study, not as its own sweep.
- Scout runs: RSS keeps working but rate limits harder each night; use 10-15 s spacing and 3 passes. The 10-27..10-30
  feeds had very few rule posts (earnings week); top-month feeds and comment threads were the better source today.

Reproduce: `python research/bdi/reddit_1030/make_modules.py`, then
`python research/bdi/pod1022/score_batch.py research/bdi/reddit_1030/modules/RC*.py --out research/bdi/reddit_1030/results.jsonl --ref-cache '' --trades-dir <scratch>`.

Educational only — not financial advice.
