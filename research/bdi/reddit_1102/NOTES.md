Educational only — not financial advice.

# reddit_1102: Reddit setup scout (2026-11-02, weekend + Monday)

**Result: 2 ideas kept, both tested on two years, 0 pass.** 20 configurations were declared in PLAN.md before
scoring; 18 had trades and are all listed below (QQQ k3 long / short had none). BAR90 for N = 20 is 2.20 (full bar
2.45); the best t was −0.05, so **the locked block (2024-11-01..2025-02-28) was not scored and there is no DECISION.**
No config, setup, exit, ledger or docs/live file was changed. Read-only toward Reddit (RSS GETs only, no account).

**Rule changes in the window:** none apply. These are two-year backtests on the research cost model
(gates.py: 1c + 1 bp per side, time-of-day entry multiplier, +2c stops), not live records, so the live sizing / stop /
filter changes in research/ledger.jsonl (e.g. 10-28 position size, 10-29 BAR90, 10-30 cost filter) do not touch them.

## Sources
- Reddit RSS (`/r/<sub>/top/.rss?t=day|week`, `/new/.rss`, UA `mcf-research/0.1`), 12-15 s spacing, 3 passes for the
  HTTP 429s. Got: r/Daytrading (top day / week, new), r/Trading (top day / week, new), r/algotrading (top day / week,
  new), r/RealDayTrading (top day / week, new), r/quant (top week), r/StockMarket (top day), r/swingtrading (top week).
  r/ai_trading returned 404 on every try; r/daytrade stayed 429. Comment feeds read: 1xle3nm, 1xjucpo, 1xm1d9u
  (1xm8opp stayed 429). WebSearch was not needed.
- **558 unique posts; 303 dated 2026-10-30..11-02** (248 from 10-31 on). About 40 were read in full.

## Filter (what was dropped)
A thin weekend for rules: most posts were psychology, prop firms, P/L, platform / indicator promotion, FX / gold / BTC,
or "I tested N strategies, none passed" (r/Trading 1xkwq1k and 1xkgxvh, r/algotrading 1xkssyv and 1xlyqdy,
r/Daytrading 1xm16xo ICT Silver Bullet on NQ — 0 of 48). Dropped:
- r/Daytrading 1xl1rwf (NQ 15-min ORB, 18 years) and 1xm5dj2 ("ORB high first -> low gets swept"): futures, and the
  posters themselves show no edge over a coin flip; ORB + FVG is covered by rdt1030 (137 configs).
- r/Daytrading 1xm8opp (high-of-day failures, S/R, breakouts on 1-min): no rules.
- r/Trading 1xl3uol (low-float runner, overnight hold, "< 1 setup a month"): not intraday, no rules.
- r/Daytrading 1xldrag (17 NQ strategies, rules private), r/algotrading 1xl03f5 (breakout, rules private),
  r/algotrading 1xly1w6 (ES, no rules): rules withheld.
- r/Trading 1xkwq1k flow ideas (index adds, Russell reconstitution): daily / event, not intraday setups.
- r/algotrading 1xljdal is a public log of this project's own paper accounts; not a source.

## Ideas (research/backlog.jsonl, tags reddit + scout)
| id | source | status |
|---|---|---|
| reddit-1102-open-candle-expansion | [r/Daytrading 1xle3nm](https://www.reddit.com/r/Daytrading/comments/1xle3nm/i_found_a_possible_nasdaq_opening_volatility_edge/) | failed (12 configs) |
| reddit-1102-vwap-bounce-1m-megacap | [r/Trading 1xjucpo](https://www.reddit.com/r/Trading/comments/1xjucpo/switching_to_1m_vwap_bounce_trading_from_smc_poi/) | failed (8 configs; variant of reddit-1029-rdt-volconfirm-bounce) |

## A — opening-candle range expansion (`a_open_candle.py`, `a_out.txt`, `a_results.csv`)
Opening frame research/bdi/timeofday/data/open (built without the locked block; asserted). First candle = 09:30-09:35
(checked against the 1-minute cache). rr = range / trailing 20-session median; enter the 09:35 close on the candle's
side, stop at its opposite extreme, out at 10:30. Entry cost 3.8x. Baseline = every eligible symbol-day at 09:35,
same side, stop one candle range away, same exit (stocks long −0.192R, short −0.203R).

| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | up / down | WF | stop % px |
|---|---|---|---|---|---|---|---|---|---|---|
| stocks long k1.5 | 23,233 | 68.7 | −0.147 | −5.62 | −0.173 / −0.133 | +0.031 (2.37) | −0.155 | +0.030 / −0.360 | 0% | 1.25 |
| stocks long k2 | 8,262 | 24.4 | −0.140 | −4.94 | −0.197 / −0.106 | +0.050 (2.90) | −0.151 | −0.016 / −0.322 | 12% | 1.57 |
| stocks long k3 | 1,469 | 4.4 | −0.114 | −3.34 | −0.186 / −0.062 | +0.095 (3.30) | −0.125 | −0.004 / −0.273 | 35% | 2.28 |
| stocks short k1.5 | 22,887 | 67.7 | −0.137 | −3.48 | −0.170 / −0.114 | +0.042 (2.35) | −0.160 | −0.363 / +0.075 | 12% | 1.26 |
| stocks short k2 | 8,695 | 25.7 | −0.112 | −2.04 | −0.121 / −0.104 | +0.060 (2.57) | −0.148 | −0.341 / +0.106 | 18% | 1.60 |
| stocks short k3 | 1,744 | 5.2 | −0.095 | −1.41 | −0.150 / −0.034 | +0.092 (2.53) | −0.122 | −0.332 / +0.085 | 29% | 2.26 |
| QQQ long k1.5 | 29 | 0.09 | −0.345 | −1.72 | −0.399 / −0.316 | −0.015 | −0.435 | +0.070 / −0.972 | 31% | 0.43 |
| QQQ long k2 | 8 | 0.02 | −0.463 | −1.94 | | −0.008 | −0.567 | | 20% | 0.59 |
| QQQ short k1.5 | 27 | 0.08 | −0.376 | −2.19 | −0.123 / −0.694 | −0.101 | −0.468 | −0.694 / +0.264 | 31% | 0.39 |
| QQQ short k2 | 8 | 0.02 | −0.245 | −0.78 | | −0.127 | −0.500 | | 33% | 0.45 |

(best-day share is not defined: every total R is negative.)
- **Fails.** Every arm is negative in TRAIN and VALID. On stocks the candle's direction does carry information against a
  same-minute random entry (+0.03..+0.09R, t 2.4-3.3, rising with k: a smooth slope, not a mined band — the commenter's
  suggested check), but it is far smaller than the 09:35 cost plus the day's direction: longs are flat on up days and
  −0.27..−0.36R on down days, shorts the mirror. Same picture as sat1031-open-gap-and-go-long and mh-1030.
- The poster's instrument (QQQ as the Nasdaq-100 proxy) gives 8-29 signals in the open two years — far too few, and
  negative. Their +0.177R on US100 CFD rests on a 0.9 bp cost, BID-only data and a few large winners (their own caveats).
- Caveat: the baseline's stop (one range away from the 09:35 close) is not the signal's exact stop geometry, so part of
  the excess may be stop placement; it does not change the verdict (absolute R < 0 everywhere).

## B — 1-minute VWAP bounce on mega caps (`b_vwap_bounce_1m.py`, `b_out.txt`, `b_results.csv`)
1-minute cache, locked block + old holdouts dropped at load. Universe: point-in-time top-30 non-ETF names by adv20,
then the 6 with the highest 09:30-09:44 $ volume (2,124 symbol-days over 354 sessions), blackout removed.

| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | up / down | WF | stopped |
|---|---|---|---|---|---|---|---|---|---|---|
| long V1 t2r | 517 | 1.46 | −0.217 | −3.24 | −0.216 / −0.217 | +0.019 (0.28) | −0.229 | +0.017 / −0.402 | 17% | 64% |
| long V1 h1130 | 517 | 1.46 | −0.118 | −0.88 | −0.339 / +0.075 | +0.277 (2.29) | −0.163 | +0.177 / −0.483 | 33% | 75% |
| long V1.5 t2r | 155 | 0.44 | −0.267 | −2.45 | −0.399 / −0.126 | +0.062 (0.53) | −0.293 | +0.017 / −0.606 | 33% | 64% |
| long V1.5 h1130 | 155 | 0.44 | −0.232 | −1.32 | −0.406 / −0.045 | +0.068 (0.43) | −0.308 | +0.031 / −0.612 | 39% | 70% |
| short V1 t2r | 426 | 1.20 | −0.168 | −2.28 | −0.355 / −0.027 | −0.004 (−0.05) | −0.182 | −0.051 / −0.142 | 22% | 62% |
| short V1 h1130 | 426 | 1.20 | −0.303 | −2.20 | −0.530 / −0.133 | +0.076 (0.55) | −0.382 | −0.493 / +0.192 | 17% | 79% |
| short V1.5 t2r | 110 | 0.31 | −0.007 | −0.05 | −0.226 / +0.162 | +0.238 (1.54) | −0.043 | −0.013 / −0.054 | 50% | 57% |
| short V1.5 h1130 | 110 | 0.31 | −0.362 | −1.65 | −0.538 / −0.225 | +0.137 (0.68) | −0.502 | −0.684 / +0.532 | 22% | 77% |

- **Fails.** No arm is positive overall; the median stop is 0.16-0.19% of price, so 1-minute structural stops sit in
  the noise (57-79% stopped) and the cost share is large. The one "excess" with t > 2 (long V1 h1130, +0.28R) comes from
  the random controls losing more, not from the setup making money. Same verdict as its 5-minute parent
  (reddit-1029-rdt-volconfirm-bounce).

## Next
- Nothing to promote. The only reusable finding is A's: the 09:30-09:35 candle's direction is a weak, cost-dominated
  signal of the next hour on stocks. It should be tried only inside a day-direction-neutral book (the open rework
  mh-1102-group-laggard-hedged), not as its own sweep.

Scratch (RSS / comment XML, parser) was in the session scratchpad and has been deleted.
