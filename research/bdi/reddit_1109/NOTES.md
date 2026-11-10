Educational only — not financial advice.

# reddit_1109: Reddit setup scout (2026-11-09)

**Result: 3 ideas kept, 2 tested, 0 pass.** 14 configurations were declared in PLAN.md before scoring (A 6 + B 8).
Full bar for N = 14 is max(1.5, sqrt(2 ln 14)) = 2.30, Testing bar (BAR90) 2.07; the best t was −0.53, so **the locked
block (2024-11-01..2025-02-28) was not scored and there is no DECISION.** No config, setup, exit, ledger or docs/live
file was changed. Read-only toward Reddit (RSS GETs only, no account, no posting, voting or messaging; no user names
recorded).

**Rule changes in the window:** none apply. This is a two-year backtest on the research cost model (gates.py: 1c +
1 bp per side, time-of-day entry multiplier, +2c stops), not a live record; the live changes in research/ledger.jsonl
(GX1 10-27, Primary size 10-28, −2R stop 10-29, CF 10-30, UNI1 11-04, ROLL1 11-05) do not touch it. Data: the 2-year
cache rebuilt 11-04 (research/bdi/1104/DATA.md); 485 symbols, 342 sessions (same frame as reddit_1105/1106).

## Sources
- Reddit RSS (UA `mcf-research/0.1`, 8 s spacing): top-day for r/Daytrading, r/Trading, r/algotrading, r/ai_trading,
  r/RealDayTrading (0 entries today), r/quant, r/StockMarket, r/swingtrading, r/daytrade (active intraday sub, as
  11-05); top-week for r/Daytrading, r/algotrading, r/RealDayTrading, r/daytrade, r/Trading, r/swingtrading, r/quant
  (to cover the weekend 11-07..11-08); `/new/` for r/Daytrading. WebSearch not needed. No new intraday sub found.
- **417 unique posts; 278 dated 2026-11-07..11-09** (319 from 11-06; 11-06 posts were covered by reddit_1106) —
  Daytrading 104, ai_trading 48, Trading 42, swingtrading 26, StockMarket 17, quant 17, algotrading 12,
  daytrade 11, RealDayTrading 1.
- Research Guild board (mcf-guild, board.jsonl) checked: tonight's Scout threads (SC1 event-gap hold, SC2 cross-asset,
  NH1 quiet-top continuation, STOPW) do not overlap these ideas.

## Filter (what was dropped)
Weekend + Monday (NVDA CEO news, post-election rally): mostly psychology, tool/journal promos ("Software Sunday"),
prop firms, brokers, P/L, AI stock-pick spam (r/ai_trading), futures/forex/gold/crypto. Dropped with a reason:
- r/Daytrading [1xrtr7c](https://www.reddit.com/r/Daytrading/comments/1xrtr7c/your_target_can_look_good_on_a_chart_but_how_much/)
  (ADR split by side of the open as a target-room check): covered by reddit-1104-session-room-pullback-long.
- r/Daytrading [1xqk040](https://www.reddit.com/r/Daytrading/comments/1xqk040/momentum_impulse_buy_strategy/)
  (breakout, retest, buy the impulse candle, sell in seconds): vague, scalping; covered by the ORB / retest families.
- r/Daytrading [1xqq06c](https://www.reddit.com/r/Daytrading/comments/1xqq06c/i_backtested_for_the_month_of_feb_only_4_entries/)
  (fib 0.6-0.7 + 15-min shift): ICT-style, covered by reddit-1030-orbfvg-f4 / bdi-art-prior-day-fib; 4 trades/month.
- r/Daytrading [1xqvjx1](https://www.reddit.com/r/Daytrading/comments/1xqvjx1/switched_from_7_trades_a_day_to_1_and_the_week/)
  (one trade a day, MFE capture): ES futures, no rule posted.
- r/StockMarket [1xrmm1q](https://www.reddit.com/r/StockMarket/comments/1xrmm1q/the_core_cpi_suprise_hasnt_predicted_spys/)
  (CPI surprise vs SPY direction, 10 days): no rule; data-day idea already in backlog (reddit-1106-dataday-wait-or-settle).
- r/Daytrading [1xs01x8](https://www.reddit.com/r/Daytrading/comments/1xs01x8/scalping_vwap_questions/) (VWAP scalping
  book): no rule; VWAP families cover it. r/Daytrading [1xrh23e](https://www.reddit.com/r/Daytrading/comments/1xrh23e/what_do_you_think_about_this_setup_and_entry/)
  (first red candle after a run, US100): index CFD, image only.
- r/Trading [1xqogjc](https://www.reddit.com/r/Trading/comments/1xqogjc/steves_simple_system_repetitive_behavior/)
  (repeat tests of AVWAP/EMA/POC): same poster as 11-06 1xp2b5y, no rule.
- r/Daytrading [1xqmm65](https://www.reddit.com/r/Daytrading/comments/1xqmm65/churning_and_chatting_2_the_dark_lord_trader_of/)
  (prop-trader interview): no rules. r/algotrading [1xri005](https://www.reddit.com/r/algotrading/comments/1xri005/backtesting_cameron_ross_strategy_no_real_results/)
  (small-cap gappers do not backtest): consistent with our small-cap/gapper results, nothing new.

## Ideas (research/backlog.jsonl, tags reddit + scout)
| id | source | status |
|---|---|---|
| reddit-1109-leader-daily-ema-pullback-intraday-long | [r/swingtrading 1xqieam](https://www.reddit.com/r/swingtrading/comments/1xqieam/how_to_trade_like_future_market_wizard_martin_luk/) | parked (6 configs) |
| reddit-1109-daily-inside-day-breakout | [r/Daytrading 1xrs4yu](https://www.reddit.com/r/Daytrading/comments/1xrs4yu/breakout_watchlist_inside_bars_gap_fills/) | parked (8 configs) |
| reddit-1109-chop-day-inside-pdr-lowvol-filter | [r/Daytrading 1xrifsz](https://www.reddit.com/r/Daytrading/comments/1xrifsz/how_do_you_guys_filter_out_choppylowvolume_days/) | idea (filter; needs a per-setup remedy report) |

Note on A's source: a trade study of a public trader; it ends with a link to the author's study tool. Only the rule
was taken (the post itself gives it in full).

## Results (`ab_tests.py`, `ab_out.txt`, `ab_results.csv`)
Random control = 3 same-symbol-day entries in the trigger window, same side, same $ R, same exit.

| config | n | /session | avg R | t | train / valid | excess vs random (t) | w/o best day | SPY up / down / quiet | WF | stopped | med R % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A T1 ORB15, close | 1,550 | 4.53 | −0.037 | −1.04 | +0.031 / −0.082 | −0.075 (−4.0) | −0.052 | +0.172 / −0.345 / −0.095 | 55% | 25% | 1.90 |
| A T1 ORB15, 2R | 1,550 | 4.53 | −0.018 | −0.53 | +0.036 / −0.055 | −0.068 (−3.8) | −0.031 | +0.191 / −0.331 / −0.074 | 64% | 25% | 1.90 |
| A T2 undercut-reclaim, close | 766 | 2.24 | −0.199 | −3.00 | −0.272 / −0.160 | +0.012 (+0.3) | −0.228 | +0.214 / −0.482 / −0.366 | 18% | 52% | 1.17 |
| A T2 undercut-reclaim, 2R | 766 | 2.24 | −0.184 | −3.67 | −0.155 / −0.200 | −0.027 (−0.7) | −0.199 | +0.107 / −0.402 / −0.282 | 9% | 49% | 1.17 |
| A T3 VWAP reclaim, close | 2,615 | 7.65 | −0.122 | −2.78 | −0.043 / −0.177 | −0.052 (−1.9) | −0.137 | +0.194 / −0.453 / −0.183 | 9% | 48% | 1.17 |
| A T3 VWAP reclaim, 2R | 2,615 | 7.65 | −0.100 | −2.57 | −0.026 / −0.152 | −0.033 (−1.3) | −0.109 | +0.162 / −0.394 / −0.136 | 18% | 47% | 1.17 |
| B long, mid stop, close | 5,062 | 14.80 | −0.027 | −0.84 | +0.020 / −0.066 | −0.075 (−3.0) | −0.042 | +0.265 / −0.371 / −0.135 | 24% | 29% | 1.32 |
| B long, mid stop, 2R | 5,062 | 14.80 | −0.019 | −0.67 | +0.027 / −0.058 | −0.071 (−3.4) | −0.032 | +0.254 / −0.334 / −0.128 | 35% | 29% | 1.32 |
| B long, far stop, close | 4,907 | 14.35 | −0.020 | −0.97 | +0.007 / −0.042 | −0.040 (−2.7) | −0.030 | +0.171 / −0.261 / −0.074 | 24% | 11% | 2.27 |
| B long, far stop, 2R | 4,907 | 14.35 | −0.020 | −0.98 | +0.008 / −0.043 | −0.038 (−2.5) | −0.030 | +0.169 / −0.261 / −0.072 | 24% | 11% | 2.27 |
| B short, mid stop, close | 4,701 | 13.75 | −0.046 | −1.30 | −0.087 / −0.014 | −0.105 (−4.0) | −0.061 | −0.435 / +0.267 / −0.042 | 24% | 30% | 1.40 |
| B short, mid stop, 2R | 4,701 | 13.75 | −0.039 | −1.21 | −0.072 / −0.014 | −0.106 (−4.0) | −0.051 | −0.406 / +0.254 / −0.034 | 29% | 30% | 1.40 |
| B short, far stop, close | 4,592 | 13.43 | −0.026 | −1.09 | −0.056 / −0.002 | −0.066 (−4.0) | −0.034 | −0.289 / +0.184 / −0.027 | 18% | 10% | 2.38 |
| B short, far stop, 2R | 4,592 | 13.43 | −0.025 | −1.06 | −0.054 / −0.002 | −0.067 (−4.0) | −0.032 | −0.286 / +0.183 / −0.025 | 24% | 10% | 2.38 |

(Best-day share undefined: every total R is negative. Regime gate fails on all 14. WF = share of open months > 0; A has
11 open months because the 60-session leader lookback needs unbroken history; B 17.)

- **A fails.** The leader + daily-EMA-pullback context gives plenty of events (2-8/session) but the intraday trades
  are a bet on the day's direction: +0.11..+0.21R on SPY-up days, −0.33..−0.48R on down days, negative on quiet days.
  ORB15 (T1) is the least bad and positive in TRAIN, but VALID is negative and it trails random entries by 0.07R
  (t −4). Undercut-reclaim (T2) matches random (+0.01R) — the trigger timing is fine, the context is not — at −0.2R.
  The swing part of the post (trail on the daily 9 EMA for days) cannot run in the intraday book.
- **B fails.** Breaking a daily inside-day range adds no timing (below same-side random by 0.04-0.11R in all 8);
  longs win on SPY-up days and shorts on SPY-down days, both lose on quiet days, so it is not a QDAY idea either.
- Salvage path (not tested, new pre-declared run needed): A's daily context as a day-direction-conditional long
  (only on compass-UP days), which is what the SPY split says it is — overlaps the dayclass gate ideas.

## Files
- `PLAN.md` (pre-declared grid), `ab_tests.py` (run from any directory; reads /home/user/MCF data), `ab_out.txt`,
  `ab_results.csv`.
