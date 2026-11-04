Educational only — not financial advice.

# reddit_1103: Reddit setup scout (2026-11-03)

**Result: 2 ideas kept, both tested, 0 pass.** 11 configurations were declared in PLAN.md before scoring (A: 8
backtest configs; B: 3 pre-open predictors). BAR90 for N = 11 is 1.97 (full bar 2.19); the best backtest t was −4.94
and no predictor cleared its gate, so **the locked block (2024-11-01..2025-02-28) was not scored and there is no
DECISION.** No config, setup, exit, ledger or docs/live file was changed. Read-only toward Reddit (RSS GETs only, no
account, no posting, voting or messaging).

**Rule changes in the window:** none apply. These are two-year backtests on the research cost model (gates.py: 1c +
1 bp per side, time-of-day entry multiplier, +2c stops), not live records; the live sizing / stop / filter changes in
research/ledger.jsonl (GX1 10-27, Primary size 10-28, −2R stop 10-29, CF 10-30) do not touch them.

## Sources
- Reddit RSS (`/r/<sub>/top/.rss?t=day|week`, `/new/.rss`, UA `mcf-research/0.1`), 12-20 s spacing, retries for
  HTTP 429. Got: r/Daytrading (top day / week, new), r/Trading (top day, new), r/algotrading (top day / week),
  r/RealDayTrading (top day), r/quant (top week), r/StockMarket (top day), r/swingtrading (top week), r/ai_trading
  (top week — it answered this time), r/daytrade (top week; active intraday sub, mostly link/image posts).
  r/algotrading new, r/RealDayTrading new and r/Trading top week stayed 429. 11 post comment feeds read in full
  (1xn5yrr, 1xn4wdn, 1xme54j, 1xn5ohs, 1xmmx7g, 1xmvv2w, 1xmraf6, 1xmy7f2, 1xn6fv6, 1xlcrkv, 1xmebc0).
- WebSearch (standard, 2 queries) returned only a third-party mirror with no November posts; not used.
- **233 unique posts; 152 dated 2026-11-01..11-03 (102 on 11-03)** — Daytrading 45, Trading 25, algotrading 18,
  daytrade 16, StockMarket 13, quant 12, ai_trading 11, swingtrading 11, RealDayTrading 1.

## Filter (what was dropped)
Election-day thin: most posts were psychology, prop firms, brokers, P/L, FX / gold / NQ / crypto, AI-platform
promotion, macro or earnings news. Dropped with a reason:
- r/algotrading 1xn5ohs (overnight-range sweep and reverse, CRT / Power of 3, 6 indices, 6,400 trades): the poster's
  own pre-registered test fails (−0.09R; SMT filter worse); mechanism covered by bdi-reddit-level-sweep-reclaim.
- r/Daytrading 1xn5yrr (TSLA: open above PDH, fail through PDC, long on the premarket-low reclaim): options, GEX
  levels, premarket low not in the lab frames; one trade.
- r/swingtrading 1xlcrkv (green names on a red tape lead the rebound): covered by ex30-XS2-leader-redtape-long,
  reddit-1030-rs-spydip-orh-long, bdi1027-index-reclaim-leaders-long.
- r/Daytrading 1xmvv2w (higher-timeframe trend filter), 1xn6fv6 (weekly / monthly VWAP bands), 1xmebc0 (four tests:
  random entry, false entry, narrative, ruin — matches RESEARCH_RULES already), 1xmy7f2 (low-float pump-and-dump,
  no rules), 1xmmx7g (video, no rules), 1xmraf6 (broker question).
- r/algotrading 1xmes0o / 1xljdal: public log of this project's own paper accounts; not a source.

## Ideas (research/backlog.jsonl, tags reddit + scout)
| id | source | status |
|---|---|---|
| reddit-1103-range-low-volflip-magnet-long | [r/Daytrading 1xn4wdn](https://www.reddit.com/r/Daytrading/comments/1xn4wdn/abt_day_trade_review_a_range_trade_048r_and_a/) | parked (8 configs) |
| reddit-1103-preopen-range-regime-vwap-revert | [r/Trading 1xme54j](https://www.reddit.com/r/Trading/comments/1xme54j/avgo_setup_for_tuesday_range_regime_or_vwap/) | parked (3 predictors; step 2 not run) |

## A — range-low volume-flip long, magnet target (`a_range_volflip.py`, `a_out.txt`, `a_results.csv`)
5-minute bars from the 1-minute SIP cache; locked block and old holdouts dropped at load; top-250 non-ETF names by
prior-day adv20, blackout removed (484 symbols, 74,239 symbol-days, 344 sessions). Long only, next-bar-open entry,
stop below the 3-bar low, R ≥ 0.10% of price. Random control = 3 same-symbol-day entries, same $ stop and magnet.

| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | SPY up / down / quiet | WF | stopped | magnet hit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none m1.2 E1 | 15,404 | 44.8 | −0.181 | −10.23 | −0.182 / −0.181 | +0.117 (9.61) | −0.186 | +0.044 / −0.321 / −0.199 | 0% | 49% | 14% |
| none m1.2 E2 | 15,404 | 44.8 | −0.202 | −6.80 | −0.218 / −0.190 | +0.147 (9.07) | −0.210 | +0.196 / −0.449 / −0.232 | 6% | 67% | 17% |
| none m1.5 E1 | 8,627 | 25.1 | −0.160 | −7.52 | −0.156 / −0.164 | +0.131 (8.88) | −0.167 | +0.056 / −0.302 / −0.169 | 0% | 48% | 14% |
| none m1.5 E2 | 8,627 | 25.1 | −0.174 | −4.94 | −0.182 / −0.167 | +0.161 (7.59) | −0.183 | +0.209 / −0.433 / −0.177 | 6% | 66% | 17% |
| quiet m1.2 E1 | 9,605 | 27.9 | −0.193 | −10.36 | −0.173 / −0.209 | +0.090 (5.72) | −0.196 | +0.007 / −0.349 / −0.200 | 0% | 49% | 18% |
| quiet m1.2 E2 | 9,605 | 27.9 | −0.213 | −7.30 | −0.183 / −0.236 | +0.107 (5.19) | −0.220 | +0.145 / −0.469 / −0.252 | 12% | 67% | 21% |
| quiet m1.5 E1 | 5,338 | 15.5 | −0.168 | −7.65 | −0.139 / −0.193 | +0.089 (5.18) | −0.173 | +0.026 / −0.325 / −0.176 | 12% | 48% | 18% |
| quiet m1.5 E2 | 5,338 | 15.5 | −0.181 | −5.30 | −0.140 / −0.217 | +0.123 (5.17) | −0.189 | +0.179 / −0.460 / −0.209 | 24% | 66% | 21% |

(SPY day type: SPY open-to-close > +0.25% up, < −0.25% down, else quiet; n quiet-day trades 1,785-4,919. Best-day
share is not defined: every total R is negative. Universe-median regime gate: up +0.03..+0.24, down −0.33..−0.49 —
fails everywhere.)
- **Fails.** Every config loses in TRAIN and VALID, in down and in quiet SPY days; only SPY-up days are positive.
  The quiet-so-far context — the poster's "range trade" read — does not help. The median stop is 0.30% of price and
  half to two thirds of trades are stopped; the "magnet" (high of the session's highest-volume bullish bar) is reached
  on only 14-21% of trades.
- The positive excess over random entries (+0.09..+0.16R, t 5-10) comes from the controls losing more with the same
  tight stop at random minutes, not from the setup making money (same pattern as reddit_1102 B).

## B — pre-open range-regime predictor (`b_range_predictor.py`, `b_out.txt`, `b_results.csv`)
Label: range day = (high − low) ≤ 0.8 ATR14 and |close − open| ≤ 0.3 ATR14. Gate: precision ≥ base + 15 points in
TRAIN and VALID, n ≥ 300 (the bar qd1-1103 set).

| predictor | TRAIN n | TRAIN prec / base | lift | VALID n | VALID prec / base | lift | gate |
|---|---|---|---|---|---|---|---|
| P1 prior NR7 + gap ≤ 0.2 ATR | 3,209 | 0.474 / 0.359 | +11.5 | 4,062 | 0.436 / 0.327 | +10.9 | fail |
| P2 prior inside day + small gap | 2,337 | 0.401 / 0.359 | +4.1 | 2,813 | 0.377 / 0.327 | +5.0 | fail |
| P3 5-day range/ATR in own bottom 20% + small gap | 747 | 0.487 / 0.359 | +12.8 | 5,596 | 0.467 / 0.327 | +14.0 | fail |

- **Fails the gate; step 2 (the VWAP fade) was not run.** Pre-open compression does raise the chance of a range day
  (+11..+14 points for NR7 / low-range streaks), but not to the +15 points set before qd1's fade may be re-tested.
  Small gap alone adds only +4 points. Caveat: ATR / NR7 windows straddle the dropped blocks at their edges (rows are
  removed, not interpolated), which affects a few weeks around each block.

## Next
- Nothing to promote. The one reusable finding is B's: NR7 / low-range streaks lift the range-day rate by ~11-14
  points. A single combined predictor (P1 and P3) is the only re-try worth one look, counted against this lineage
  (N would be 12), and only as a filter for a both-direction fade, never as its own long setup.

Scratch (RSS / comment XML, parser) was in the session scratchpad and has been deleted.
