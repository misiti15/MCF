Educational only — not financial advice.

# reddit_1029: Reddit setup scout, first run (2026-10-29)

**Result: 3 ideas kept, 2 tested on two years, 0 pass. 12 configurations were scored (all reported below); BAR90 for
N = 12 is 2.01 and the best t was 0.56, so the locked block (2024-11-01..2025-02-28) was not scored and there is no
DECISION.** No config, setup, exit, ledger or docs/live file was changed. Read-only toward Reddit (RSS GETs only).

## Sources
- **Reddit RSS worked tonight** (`https://www.reddit.com/r/<sub>/{top,new}/.rss`, UA `mcf-research/0.1`; HTTP 200, with
  some rate-limit retries). Feeds: top week / month and new for r/Daytrading, r/Trading, r/algotrading, r/ai_trading,
  r/RealDayTrading, r/quant, r/StockMarket, r/swingtrading, r/daytrade (r/pennystocks returned nothing). Comment feeds
  were read for the 3 Bar Play post (the poster's exact rules and the in-play comment).
- WebSearch (standard) was tried twice for r/RealDayTrading and r/algotrading; `site:` did not take and no Reddit pages
  came back, so the RSS feeds are the source.
- **Posts scanned:** 1,286 unique posts in the feeds; 876 dated 2026-10-14..10-29 (Daytrading 205, Trading 171,
  StockMarket 130, swingtrading 118, algotrading 93, ai_trading 61, quant 57, daytrade 29, RealDayTrading 12).
  367 matched rule keywords (entry / stop / VWAP / ORB / backtest / setup ...); 42 were read in full.

## Filter (what was dropped)
Most posts were psychology, P/L screenshots, futures / gold / crypto / 0DTE, or tool and course promotion. Concrete
rules that were **dropped as duplicates by mechanism**: NQ 15-min ORB (algotrading 1xcdlfd; ORB family failed),
failed-breakdown reclaim with GEX (Trading 1xib0tx; CWT14 failed-break family), 4H order block + FVG (Daytrading
1xel320; ICT FVG failed), midday 11:30-12:30 long-to-close ML (algotrading 1xg8blg; its baseline is the long leg of
bdi1028-leader-laggard-spread and sat1024-pm-drift-continuation), VWAP-band 0DTE fades (Daytrading 1xdssle; poster's
own PF 0.79). Nothing on the Move Hunt gaps (09:35-09:45 opening drive, earnings sympathy) was posted with rules.

## Ideas kept (research/backlog.jsonl, tags reddit + scout)
| id | source | status |
|---|---|---|
| reddit-1029-3barplay | [r/Daytrading 1xhkikg](https://www.reddit.com/r/Daytrading/comments/1xhkikg/i_backtested_one_of_the_first_strategies_i_was/) | failed (8 configs) |
| reddit-1029-vwap2sd-absorb-long | [r/Trading 1xcgb79](https://www.reddit.com/r/Trading/comments/1xcgb79/quit_software_engineering_to_trade_futures_a_year/) (ES/NQ, adapted) | failed (4 configs) |
| reddit-1029-rdt-volconfirm-bounce | [r/RealDayTrading 1xi1q9s](https://www.reddit.com/r/RealDayTrading/comments/1xi1q9s/how_important_is_volume_for_confirmation_of_entry/) | idea, untested |

## Tests (PLAN.md written before scoring; `make_modules.py`, `modules/`, `results.jsonl`)
Harness: research/bdi/pod1022/score_batch.py over the open two-year history (21 open months), costs in (1c + 1 bp per
side, time-of-day multiplier, +2c stop fills, x3 extended tier), live earnings blackout removed, ADV20 >= $95M, long,
GEOM S (structural stop), same-minute random-entry control, day-clustered t, regime1022 up (Bull) / down (Bear)
sessions. TRAIN <= 2025-12-31, VALID 2026. WF = share of months with positive total R.

| config | n | avg R | t | train / valid | excess vs random | w/o best day | best-day share | Bull (n) | Bear (n) | WF months | trades/day |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RB1-3barplay-k2-all-hold | 2,153 | −0.343 | −5.30 | −0.364 / −0.321 | −0.223 | −0.375 | – | +0.099 (557) | −0.678 (318) | 19% | 5.05 |
| RB1-3barplay-k2-all-t2r | 2,153 | −0.306 | −5.18 | −0.312 / −0.299 | −0.186 | −0.354 | – | +0.017 (557) | −0.473 (318) | 14% | 5.05 |
| RB1-3barplay-k2-inplay-hold | 157 | −0.040 | −0.19 | −0.067 / −0.017 | +0.100 | −0.136 | – | −0.112 (49) | −0.175 (14) | 40% | 0.37 |
| RB1-3barplay-k2-inplay-t2r | 157 | −0.150 | −1.22 | −0.296 / −0.027 | −0.010 | −0.178 | – | −0.212 (49) | −0.141 (14) | 40% | 0.37 |
| RB1-3barplay-k3-all-hold | 466 | −0.146 | −0.86 | −0.199 / −0.078 | −0.041 | −0.285 | – | +0.255 (166) | −0.287 (43) | 29% | 1.09 |
| RB1-3barplay-k3-all-t2r | 466 | −0.120 | −0.67 | −0.064 / −0.192 | −0.015 | −0.306 | – | +0.377 (166) | −0.610 (43) | 14% | 1.09 |
| RB1-3barplay-k3-inplay-hold | 43 | **+0.215** | 0.56 | +0.079 / +0.333 | +0.398 | +0.025 | **89% (1 day)** | +0.586 (14) | −1.170 (2) | 47% | 0.10 |
| RB1-3barplay-k3-inplay-t2r | 43 | +0.106 | 0.43 | −0.126 / +0.307 | +0.289 | +0.015 | **86% (1 day)** | +0.282 (14) | −1.170 (2) | 53% | 0.10 |
| RB2-vwap2sd-absorb-flow3-hold | 156,505 | −0.194 | −5.99 | −0.191 / −0.198 | −0.102 | −0.212 | – | +0.502 | −0.588 | 5% | 367 |
| RB2-vwap2sd-absorb-flow3-vwap | 156,505 | −0.177 | −13.91 | −0.187 / −0.167 | −0.085 | −0.179 | – | +0.014 | −0.328 | 0% | 367 |
| RB2-vwap2sd-absorb-rsidiv-hold | 76,301 | −0.219 | −5.94 | −0.210 / −0.229 | −0.124 | −0.239 | – | +0.553 | −0.617 | 5% | 179 |
| RB2-vwap2sd-absorb-rsidiv-vwap | 76,301 | −0.205 | −12.99 | −0.203 / −0.209 | −0.110 | −0.208 | – | +0.029 | −0.377 | 0% | 179 |

- **3 Bar Play fails, as the poster found on 22 large caps.** The plain pattern loses −0.12 to −0.34R and is worse
  than random entries. The commenter's "in-play day" condition is the only thing that helps: K3 + in-play is +0.215R
  and beats random by +0.40R, but on 43 trades in two years (t 0.56, 0.10 trades/day), with 89% of its R from one day
  and −1.17R in down sessions. That is a one-day record, not evidence. Every 3BP config wins in up sessions and loses
  in down sessions (a market-direction bet, not timing).
- **VWAP −2SD absorption reversal fails clearly** (t −6 to −14, below random, 0-5% positive months). The z proxy fires
  very often (180-370 trades/day), so the 5-minute VWAP band is not the outlier filter the ES rule describes; tick
  delta is not in the frames, and the proxies (RSI divergence, flow3) add nothing.
- Limitations: frames start at the 09:50 bar, so the 3BP igniting bars of the opening drive (the Move Hunt's 09:35-09:45
  hole) could not be tested; there is no `open` or raw volume column (green bar = close above prior close and in the
  top 25% of range; volume = volumeRatio). Overlap with live setups (`--ref-config`) was not run since nothing passed.

## Next
- The 3BP in-play variant should be re-tested only once the opening frame exists (backlog mh-1029-open-drive-window);
  then the 09:35-09:45 igniting bars are where the pattern is traded. Freeze the K3-inplay rule as written here.
- reddit-1029-rdt-volconfirm-bounce is the one untested idea (spec in the backlog line).
- Next scout run: RSS works; keep the 2-second spacing and retries (r/RealDayTrading top-week came back empty).

Reproduce: `python research/bdi/reddit_1029/make_modules.py`, then
`python research/bdi/pod1022/score_batch.py research/bdi/reddit_1029/modules/RB*.py --out research/bdi/reddit_1029/results.jsonl --ref-cache '' --trades-dir <scratch>`.

Educational only — not financial advice.
