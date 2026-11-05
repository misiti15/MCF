Educational only — not financial advice.

# reddit_1105: Reddit setup scout (2026-11-05)

**Result: 2 ideas kept, both tested, 0 pass.** 12 configurations were declared in PLAN.md before scoring (A 8, B 4,
counted together). BAR90 for N = 12 is 2.01 (full bar 2.23); the best t was −1.02, so **the locked block
(2024-11-01..2025-02-28) was not scored and there is no DECISION.** No config, setup, exit, ledger or docs/live file
was changed. Read-only toward Reddit (RSS GETs only, no account, no posting, voting or messaging; no user names
recorded).

**Rule changes in the window:** none apply. These are two-year backtests on the research cost model (gates.py: 1c +
1 bp per side, time-of-day entry multiplier, +2c stops), not live records; the live changes in research/ledger.jsonl
(GX1 10-27, Primary size 10-28, −2R stop 10-29, CF 10-30, UNI1 11-04, ROLL1 11-05) do not touch them.
Data: the 2-year cache rebuilt 11-04 (research/bdi/1104/DATA.md); 485 symbols, 85,500 top-250 symbol-days, 342
sessions (two fewer than 11-04: first sessions after a dropped block now need a valid prior close).

## Sources
- Reddit RSS (`/r/<sub>/top/.rss?t=day`, r/Daytrading `/new/`, UA `mcf-research/0.1`, 9-25 s spacing, retries for
  HTTP 429). Got top-day: r/Daytrading, r/Trading, r/algotrading, r/quant, r/StockMarket, r/swingtrading, r/daytrade
  (active intraday sub); r/ai_trading and r/RealDayTrading stayed 429 on top-day and were read from top-week.
  Comment feeds read: 1xokdhq, 1xom7y4 (empty), 1xo3sdz, 1xou3un (1xooc76, 1xog090 stayed 429). WebSearch not needed.
- **154 unique posts; 131 dated 2026-11-04..11-05 (123 on 11-05)** — Daytrading 46, Trading 25, swingtrading 25,
  StockMarket 17, ai_trading 6, algotrading 4, daytrade 3, quant 3, RealDayTrading 2. Older posts (reddit_1103 /
  reddit_1104 windows: 1xn5p8m, 1xnsgqq, 1xnx9w3 etc.) not re-scored.

## Filter (what was dropped)
Crash day (SPY ≈ −3..−4%, QQQ ≈ −6%): most posts were selloff news, psychology, prop firms, brokers, P/L, gold / NQ /
crypto, AI-platform promotion. Dropped with a reason:
- r/algotrading 1xou3un (1-minute new lows ~4,200 vs 140 highs; S&P −4% days since 1950: next day +0.67% avg): a
  next-day bet on ~45 events in 76 years; a handful in the open 2-year history — not testable at this power.
- r/algotrading 1xo3sdz (momentum: ORB / PDH-PDL breaks with a trailing exit; narrow prior range → expansion): covered
  by nr7-orb, bdi-reddit-pdhl-break-retest, the ORB exit grids; 12-1 momentum is not intraday.
- r/Trading 1xog090 (bounce days vs runaway days from dealer positioning; pre-market tool unpublished, promoted):
  covered by reddit-1103-preopen-range-regime-vwap-revert.
- r/Trading 1xokdhq main post (trade the OR break or fail): covered by the ORB / OR-fail entries; a comment's claim
  (index OR up-breaks hold, down-breaks revert, 2019-21) is a direction effect it names itself.
- r/swingtrading 1xovnba (relative strength on a red tape): covered by ex30-XS2-leader-redtape-long,
  reddit-1030-rs-spydip-orh-long. r/Daytrading 1xooc76 (reversal entry models; question, comments 429), 1xoinev
  ("repetitive behavior", no rule), 1xowvj6 (video), 1xo63yp (screenshots), r/swingtrading 1xokrlo (empty).

## Ideas (research/backlog.jsonl, tags reddit + scout)
| id | source | status |
|---|---|---|
| reddit-1105-twice-defended-level-break | [r/Daytrading 1xom7y4](https://www.reddit.com/r/Daytrading/comments/1xom7y4/1282_shorting_crwv_after_the_election/) | parked (8 configs) |
| reddit-1105-gapup-holds-prior-close | [r/Trading 1xokdhq](https://www.reddit.com/r/Trading/comments/1xokdhq/do_you_trade_the_open_or_wait_for_the_first_15/) (comment) | parked (4 configs) |

## A — twice-defended level that weakens, then breaks (`ab_tests.py`, `ab_out.txt`, `ab_results.csv`)
Session low (high) touched in ≥ 2 episodes (bounce ≥ 0.30 ATR between them), last bounce weaker; 5-min close beyond
the level by 0.05 ATR (10:00..14:30). `break` = next bar open, stop beyond the failed bounce; `retest` (the BURST1
"wait for the bounce" variant) = first bar within 12 that comes back to the level and closes on the break side, stop
beyond the retest extreme. Target m x R. Random control = 3 same-symbol-day entries, same side, same $ R and target.

| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | SPY up / down / quiet | WF | stopped | med R % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| long break 1.5R | 14,742 | 43.1 | −0.058 | −2.59 | −0.053 / −0.062 | −0.181 (−12.1) | −0.067 | +0.158 / −0.307 / −0.174 | 18% | 41% | 0.90 |
| long break 2R | 14,742 | 43.1 | −0.072 | −2.77 | −0.061 / −0.079 | −0.196 (−11.7) | −0.083 | +0.170 / −0.357 / −0.197 | 12% | 42% | 0.90 |
| long retest 1.5R | 6,745 | 19.7 | −0.157 | −7.25 | −0.140 / −0.168 | −0.106 (−5.2) | −0.162 | −0.023 / −0.311 / −0.224 | 6% | 58% | 0.34 |
| long retest 2R | 6,745 | 19.7 | −0.172 | −6.59 | −0.175 / −0.170 | −0.131 (−5.4) | −0.179 | −0.003 / −0.371 / −0.254 | 0% | 63% | 0.34 |
| short break 1.5R | 15,532 | 45.4 | −0.030 | −1.06 | −0.040 / −0.023 | −0.188 (−10.0) | −0.042 | −0.343 / +0.181 / −0.106 | 41% | 41% | 0.95 |
| short break 2R | 15,532 | 45.4 | −0.033 | −1.02 | −0.046 / −0.025 | −0.202 (−10.2) | −0.050 | −0.365 / +0.194 / −0.120 | 41% | 42% | 0.95 |
| short retest 1.5R | 6,985 | 20.4 | −0.111 | −4.44 | −0.112 / −0.111 | −0.109 (−4.3) | −0.120 | −0.285 / +0.048 / −0.218 | 12% | 57% | 0.36 |
| short retest 2R | 6,985 | 20.4 | −0.110 | −3.60 | −0.115 / −0.106 | −0.158 (−5.6) | −0.122 | −0.348 / +0.086 / −0.222 | 18% | 62% | 0.36 |

## B — gap-up that holds the prior close through 09:45 (same files)
| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | SPY up / down / quiet | WF | stopped | med R % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gap ≥ 0.5%, hold | 16,759 | 49.0 | −0.086 | −2.52 | −0.057 / −0.105 | −0.023 (−1.0) | −0.098 | +0.266 / −0.437 / −0.138 | 24% | 35% | 1.66 |
| gap ≥ 0.5%, 2R | 16,759 | 49.0 | −0.075 | −2.47 | −0.047 / −0.092 | −0.021 (−1.0) | −0.083 | +0.226 / −0.379 / −0.116 | 18% | 34% | 1.66 |
| gap ≥ 1%, hold | 10,880 | 31.8 | −0.085 | −2.09 | −0.080 / −0.088 | −0.025 (−1.0) | −0.102 | +0.244 / −0.416 / −0.121 | 35% | 32% | 2.17 |
| gap ≥ 1%, 2R | 10,880 | 31.8 | −0.079 | −2.15 | −0.068 / −0.085 | −0.024 (−1.1) | −0.091 | +0.211 / −0.375 / −0.104 | 24% | 30% | 2.17 |

(SPY day type: SPY open-to-close > +0.25% up, < −0.25% down, else quiet. Best-day share is not defined: every total R
is negative. Universe-median regime gate fails on all 12. WF = share of 17 open months > 0.)

- **Both fail.** Every config is negative in TRAIN and VALID and below same-day random entries.
- **A is a day-direction bet, not a level edge:** longs win only on SPY-up days, shorts only on SPY-down days, and every
  config loses on quiet days (−0.10..−0.25R), so it is not a range-day idea. The poster's break entry does better than
  the retest here; the retest's stop is tight (0.34-0.36% of price, stopped 57-63%) and costs eat it. The BURST1
  "wait for the bounce" lesson does not carry over to this level-break proxy.
- **B:** the 15-minute "holds the prior close" check adds no timing value (≈ random later entries), and the stop at
  the prior close is wide (1.7-2.2%). Up-day only again.
- Not re-tested with a day-direction gate (post-hoc).

## Files
- `PLAN.md` (pre-declared grid), `ab_tests.py` (run from any directory; reads /home/user/MCF data), `ab_out.txt`,
  `ab_results.csv`.
