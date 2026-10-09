# BDI - Reddit day-trading strategies, seen through web search (2026-10-09)

*Educational only - not financial advice.*

Owner request (2026-10-09): find the day-trading strategies, setups and indicators that r/Daytrading, r/algotrading,
r/ai_trading, r/aitradingplaybook, r/RealDayTrading and similar subreddits have discussed over several years, so they
can be tested. This file is research notes and rule specs only. **No backtest was run.** A separate testing pass
follows.

## 0. Read this first: what was actually seen

- **Only search-engine snippets were seen. No full Reddit thread was read.**
  - Reddit and the archive APIs are blocked from this container.
  - The WebSearch tool does not apply `site:reddit.com` filters. Reddit content surfaced only as third-party mirror
    pages (redlib.*, lr.*.psf.lt, lr.sudovanilla.org, r.til.io, reddit.birdcat.cafe, reddit.sentinel-team.org,
    r.datuan.dev, red.127.pp.ua, redlib.groet-infra.nl).
  - **WebFetch failed with DNS errors (`getaddrinfo ENOTFOUND`) on every domain tried, Reddit mirrors and ordinary
    sites alike** (lr.psf.lt, reddit.sentinel-team.org, oneoption.com, daytradingtoolkit.com). So no page was opened
    in full, not even the non-Reddit summaries.
- **The search tool returns a model-written digest of the snippets, not the raw snippet text.** The quotes below are
  therefore close paraphrases and may be imprecise. Treat every "verdict" as a lead to test, not as evidence.
- **Coverage gaps:**
  - r/ai_trading and r/aitradingplaybook returned nothing that could be attributed to them.
  - r/options 0DTE returned only TradingView 0DTE scripts.
  - r/StockMarket and r/stocks returned no thread.
- **Most of the setup material is non-Reddit.** It comes from education/vendor blogs (daytradingtoolkit, tradezella,
  Bear Bull Traders, Warrior Trading, scanz, LuxAlgo), TradingView script pages, papers and forum threads, which the
  search engine returned for Reddit-flavoured queries. They are counted separately (column NR) so the Reddit share is
  visible.
- **Searches run: 47** (standard mode, 2 extended). Query families:
  - topic + subreddit name
  - mirror-style titles ("r/Daytrading • u/", "'21".."'25")
  - topic + year
  - non-Reddit summaries
- An earlier sweep (`research/reddit_research.json`, 2026-10-06) hit the same block. Its Reddit items are listed as
  R23.

### 0.1 Reddit items seen (snippet level only)
| # | Subreddit / id | Title (as shown) | Date | What the snippet says |
|---|---|---|---|---|
| R1 | r/Daytrading 1iv3u3b ([mirror](https://reddit.birdcat.cafe/r/Daytrading/comments/1iv3u3b/how_i_became_profitable)) | How I became profitable | 2025-02-21 | ~6 years trading, 5 to profitability. The fix was discipline: a written rule set, a daily max loss, and signing off after a set number of losses. "The system is not what is holding you back." |
| R2 | r/Daytrading 11l5b5f, u/Double_Joseph ([mirror](https://r.til.io/r/Daytrading/comments/11l5b5f/my_simple_profitable_day_trading_strategy_that_i/)) | My simple profitable day trading strategy that I ... | 2023-03-07 | ES futures. The Williams **Alligator** is used as both stop and profit exit; "it is math". Commenters doubted it ("hot streak?") and challenged the claim that it cannot lose. |
| R3 | r/Daytrading 1ax73wi ([mirror](https://r.til.io/r/Daytrading/comments/1ax73wi/profitable_traders_what_clicked_for_you/krm6yed/?context=3)) | Profitable traders, what clicked for you | 2024-02-22 | The snippet had no setup detail. |
| R4 | r/Daytrading 1ip2061 ([mirror](https://lr.psf.lt/r/Daytrading/comments/1ip2061/is_day_trading_bullshit/mcrphq9)) | Is day trading bullshit??? | 2025-02-14 | "8 years, nothing to show". Commenters asked for specifics rather than "psychology". |
| R5 | sentinel snapshots 1sahup3 / 1sfyiug / 1sfy2bc ([1](https://reddit.sentinel-team.org/posts/1sahup3/snapshots/2026-04-02T23%3A51%3A56.55159Z), [2](https://reddit.sentinel-team.org/posts/1sfyiug/snapshots/2026-04-08T21%3A02%3A17.34334Z)); subreddit not shown, likely r/Daytrading | (5-year trader thread) | 2026-04 | **5-min entries, 15-min confirmation; at most 2 trades/day, the 2nd only if the 1st won.** Target moved from 2R to 2.4R after a data review. "The edge ... was executing it the same way every time." One commenter suspected a course pitch. |
| R6 | sentinel 1rfbgxv ([link](https://reddit.sentinel-team.org/posts/1rfbgxv/snapshots/2026-02-27T22%3A12%3A05.0165Z)), r/algotrading | Profitable with the same strategy > 1 year? | 2026-02 | "Day-trading strategies come and go with regimes; swing unchanged ~8 years". A breakout system did badly in 2023. Another poster keeps the same strategy and adjusts risk and size to volatility. |
| R7 | r/RealDayTrading 1k09xap ([mirror](https://redlib.hackliberty.org/r/RealDayTrading/comments/1k09xap/strategy_overview)) | Strategy overview (a user's wiki summary) | 2025-04-16 | **Market first**: longs only when SPY is bullish, shorts only when bearish, no trades when undecided. **RS/RW vs SPY in real time.** **No shorts above VWAP and no longs below VWAP on the 5-min chart.** Longs only above all major daily SMAs, shorts only below. Heikin-Ashi daily continuation. Entries 30-45 min after the open. One commenter: "maybe ChatGPT-written". |
| R8 | r/Daytrading ndaasa, u/HSeldon2020 ([mirror](https://reddit.birdcat.cafe/r/Daytrading/duplicates/ndaasa)) | (RS primer) | 2021-05-15 | Four cases: SPY up and stock stronger; SPY up and stock down; SPY down and stock weaker; SPY down and stock up. |
| R9 | r/RealDayTrading p3uxuo ([mirror](https://redlib.ssps.io/r/RealDayTrading/comments/p3uxuo/30k_challenge_week_3_update)) | 30k challenge week 3 update | 2021-08-13 | RS/RW to SPY ("not RSI or beta"). Explicitly avoids low-float gap-and-go. |
| R10 | r/RealDayTrading 149ucmd ([mirror](https://redlib.ssps.io/r/RealDayTrading/comments/149ucmd/live_day_trading/jo8sjqd/?context=3)) | Live day trading | 2023-06-15 | NVDA down >1% while SPY up ~4% (relative weakness). |
| R11 | oneoption.com/?p=1050 ("Originally written for r/RealDayTrading") | (RS rationale) | 2022-01-08 | When the market drops and the stock does not, institutions are likely buying it. |
| R12 | r/algotrading 1j9pxsr, u/Russ_CW ([mirror](https://red.127.pp.ua/r/algotrading/duplicates/1j9pxsr)) | (ORB backtest) | 2025-03-12 | First 15-min candle of the NY open. Python backtest on 5 years of S&P 500 CFD data. Stop at the range bottom, take-profit at 1.5:1. The result was not in the snippet. |
| R13 | sentinel 1qot5gp ([link](https://reddit.sentinel-team.org/posts/1qot5gp/snapshots/2026-01-28T17%3A51%3A57.95647Z)), r/Daytrading | Which day-trading setup do you actually use | 2026-01 | Answers: "price action"; and a **5-min opening range, max 1 trade per session, in a time window, backtested 6 years**. |
| R14 | r/Daytrading 1c76t6d ([mirror](https://r.til.io/r/Daytrading/comments/1c76t6d/long_road_to_get_here_but_im_green_for_15_days/)) | Long road to get here but I'm green for 15 days | 2024-04-18 | Ross Cameron follower; "1-minute bull flag". Comments: "Ross's style is super fast-paced and hard to execute"; "his points worked better for swing". |
| R15 | sentinel 1ptrl0x | (Ross-style thread) | 2025-12 | No usable detail. |
| R16 | r/Daytrading 1f6w20d ([mirror](https://lr.sudovanilla.org/r/Daytrading/comments/1f6w20d/it_looks_good_enough)) | It looks good enough | 2024-09-02 | 1-minute long-only system, about 1 year backtest, 50.62% win rate, fixed stop, 1:1 target. Commenters: one bull-trend year is not enough; test other regimes. |
| R17 | sentinel 1pnrgms, 1sf9ega, 1t4ac9p ([a](https://reddit.sentinel-team.org/posts/1pnrgms/snapshots/2025-12-16T15%3A52%3A02.12022Z), [b](https://reddit.sentinel-team.org/posts/1sf9ega/snapshots/2026-04-09T15%3A01%3A31.80847Z), [c](https://reddit.sentinel-team.org/posts/1t4ac9p/snapshots/2026-05-05T18%3A08%3A07.95291Z)), r/algotrading | ORB journal "day 148/157"; "a year of 5-min ORB profits" | 2025-12 .. 2026-05 | ORB futures journal: **breakeven after +10-15 pts, then trail on swing lows**; shorts only when price action was bearish before the OR formed. The full-year 5-min ORB profit claim drew "guru selling a course?" replies. |
| R18 | r/algotrading 1befm62 ([mirror](https://r.til.io/r/algotrading/comments/1befm62/spent_two_weeks_building_my_first_strategy_and/)) | Spent two weeks building my first strategy and ... | 2024-03-14 | RSI + Bollinger + SMA combination. "Even ETFs beat my strategy 2015-2024." |
| R19 | r/daytrade ([mirror](https://lr.sudovanilla.org/r/daytrade)) | (ORB statistics) | 2024-10-06 | ES "double break" of the OR (both sides taken) more than 60% of the time over 6 months (vendor post). |
| R20 | r/FuturesTrading 1b2gi87 ([mirror](https://redlib.hbubli.cc/r/FuturesTrading/comments/1b2gi87/nq_strategy_backtest)) | NQ strategy backtest | 2024-02-28 | No detail. |
| R21 | r/Trading 1u2iqyl ([mirror](https://redlib.groet-infra.nl/r/Trading/duplicates/1u2iqyl)) | (funded-accounts story) | 2026-06-10 | **15-min ORB + fair value gap** across five funded accounts, told as a lessons-learned story. |
| R22 | r/algotrading "rising" listing ([mirror](https://r.datuan.dev/r/algotrading/rising)) | (two post titles) | 2026 | "Not making any money" from AI-generated strategy ideas. Seven news-sentiment strategies all lose to an XBI benchmark. |
| R23 | earlier sweep (research/reddit_research.json) | r/algotrading 1sromc0 (Monday long + inside-bar breakout), 1t6ex5l (exit logic), 1r5al3o (scalping algo); r/Daytrading VWAP post | 2021-2026 | Snippet level only, as recorded on 2026-10-06. |

### 0.2 Main non-Reddit pages seen (snippet level), cited by short name below
- **ORB:**
  - Zarattini/Barbon/Aziz, "A Profitable Day Trading Strategy for the U.S. Equity Market" (stocks in play, 2016-2023).
    [unisg](https://alexandria.unisg.ch/handle/20.500.14171/122125), [concretum](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/)
  - QuantConnect replication (2016 only, 1,000 names). [QC](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)
  - MQL5 "ORB paper replicated on five indices: gross reproduced, net zero". [mql5](https://www.mql5.com/en/blogs/post/776235)
  - Backtests-not-Signals: ORB on MNQ, 2026. [substack](https://backtestsnotsignals.substack.com/p/opening-range-breakout-real-edge)
  - OptionAlpha 0DTE ORB (minimum OR width 0.2%). [optionalpha](https://optionalpha.com/blog/opening-range-breakout-0dte-options-trading-strategy-explained)
  - ProRealCode ORB thread ("<10% of stocks interesting"). [prorealcode](https://www.prorealcode.com/topic/orb/)
- **VWAP:**
  - Zarattini/Aziz VWAP trend on QQQ, 2018-2023. [concretum](https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/)
  - Tradezella, 4 VWAP setups (reclaim needs >= 15 min below VWAP, a strong close above it on above-average volume, then entry on the first pullback that holds; plus a +-2SD fade with a reversal candle, mid-session). [tradezella](https://www.tradezella.com/blog/vwap-trading-strategy)
  - Scanz (reclaim quality: heavy volume, shallow dip). [scanz](https://scanz.com/vwap-trading-strategy/)
  - Bear Bull Traders VWAP bounce/break (W bottom at VWAP; float > 20M, price > $5, spread < 10c). [BBT](https://members.bearbulltraders.com/?p=2614520)
  - LiberatedStockTrader: VWAP on 5-min candles had a 30% win rate on 30 Dow stocks over 68 days; on Heikin-Ashi it was "profitable". [LST](https://www.liberatedstocktrader.com/vwap-indicator/)
- **Gap:**
  - Gap-and-go pages: [daytradingtoolkit](https://daytradingtoolkit.com/strategies/gap-and-go-day-trading-strategy), [tradezella](https://www.tradezella.com/blog/gap-and-go-strategy), [Warrior](https://www.warriortrading.com/gap-go/), [scanz](https://scanz.com/gap-and-go-strategy/).
  - Gap fill and fade: [edgeful](https://intercom.help/edgeful/en/articles/14484835), QC TSLA/AAPL gap-fade runs ([1](https://quantconnect.com/terminal/cache/embedded_backtest_fc501a723c70ac483927fe5a1cc5c5db.html)).
- **Other setups:**
  - Red-to-green: [bullishbears](https://bullishbears.com/red-to-green-move-stocks/), [BBT forum](https://forums.bearbulltraders.com/topic/283-stuck-on-red-to-green/), [S&C sidebar](https://store.traders.com/v215sirestby.html)
  - ABCD / bull flag: [daytradingz ABCD](https://daytradingz.com/abcd-pattern/), [daytradingz flag](https://daytradingz.com/bull-flag-pattern/), [BBT ABCD](https://forums.bearbulltraders.com/topic/653-abcdflag-strategy/)
  - EMA: [kotakneo 9/20 pullback](https://www.kotakneo.com/stockshaala/scalping-trading-strategies/ema-pullback-scalping/), [sahi 9/21 cross](https://www.sahi.com/blogs/ema-scalping-strategy-the-9-21-crossover-setup-for-nifty-and-bank-nifty)
  - ICT: [TradingView ICT sweep scripts](https://kr.tradingview.com/script/hhAt4Q6Z-ICT-Liquidity-Sweep-Structure-JOAT/), [JadeCap silver bullet](https://it.tradingview.com/script/K6B5kxjJ-ICT-Silver-Bullet-JadeCap), [backtrex](https://backtrex.com/en/blog/ict-silver-bullet-strategy-trading-guide)
  - PDH/PDL break-retest: [tradezella](https://www.tradezella.com/strategies/break-retest), [daytradingtoolkit](https://daytradingtoolkit.com/strategies/prior-day-high-low-breakout-strategy)
  - 10 AM reversal: [daytradingtoolkit](https://daytradingtoolkit.com/strategies/10-am-reversal-day-trading-strategy), [MoneyShow](https://moneyshow.com/articles/daytraders-30678)
  - Parabolic and low-float: [parabolic](https://daytradingtoolkit.com/strategies/parabolic-reversal-short-strategy), [low float](https://daytradingtoolkit.com/strategies/low-float-runner-trading-strategy), [HOD scanner](https://tapeboard.com/scanner/hod-momentum-scanner)
  - Divergence: [babypips](https://forums.babypips.com/t/need-help-with-a-strategy/123747), [topdog](https://www.topdogtrading.com/macd-indicator-divergence-trading-strategy/)
  - RSI(2) intraday: [prorealcode](https://www.prorealcode.com/prorealtime-trading-strategies/rsi-2-strategy-larry-connors/?pnum=5)
  - Noise area (SPY): [concretum](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)
  - Lunch and first hour: [daytradingtoolkit](https://daytradingtoolkit.com/strategies/lunch-hour-day-trading-strategy), [tradingsim](https://tradingsim.com/blog/9-reasons-why-i-do-not-trade-during-lunch/?print=pdf)
  - Beginner setup lists: [curvedtrading 5 setups](https://curvedtrading.com/articles/en/trading/day-trading-strategies-for-beginners/)

## 1. Frequency table

**Counting rule:** distinct source pages that named the item in the snippets seen.
- R = Reddit items from section 0.1. NR = non-Reddit pages.
- TradingView or vendor pages that are copies of each other in other languages count once.
- These are counts of *what the search engine surfaced*, not of Reddit popularity. They are biased toward topics I
  searched for and toward vendor SEO pages.

| Rank | Strategy / setup / indicator | R | NR | Total | Representative sources (year) | Community verdicts seen (snippets) |
|---|---|---|---|---|---|---|
| 1 | Opening range breakout (5/15/30-min OR; "stocks in play" filter) | 7 | 14 | 21 | R12 (2025), R13 (2026), R17 (2025-26), R19 (2024), R21 (2026); Zarattini SIP paper (2024); MQL5 replication (2026) | "As posted it is a coin flip; the edge is in the filters." "Double break more than 60% of the time" on ES. "Gross reproduces, net zero after spread/slippage." "<10% of stocks worth it; indices better." "Simplest version beat the guru variants." A full-year claim met "guru selling a course?". |
| 2 | VWAP (all uses: side/trend filter, reclaim, bounce, +-2SD fade) | 2 | 18 | 20 | R7 (2025), R23 (2021); Concretum QQQ VWAP (2023); Tradezella; Scanz; BBT; LST | "Not a standalone signal; context." "Reactive, not predictive." 30% win rate on plain candles (LST). "Fades fail on trend days and high-range names." |
| 2a | - VWAP reclaim (dip below, close back above) | 0 | 6 | 6 | Tradezella, Scanz, daytradingtoolkit, curvedtrading, 2 TV scripts | Heavy volume and a shallow dip make the cleanest reclaim. Skip it if price falls back straight away. |
| 2b | - VWAP bounce / first pullback to VWAP in a trend | 0 | 5 | 5 | BBT (2025), daytradingtoolkit, Tradezella | "Only a narrow set of trending stocks." The stop should not sit exactly at VWAP (wicks pierce it). |
| 2c | - Side-of-VWAP trend following (ETF) | 1 | 4 | 5 | R7; Concretum QQQ (2018-23) | One paper only, on leveraged ETFs. |
| 2d | - +-2SD VWAP band fade / fade to VWAP | 0 | 4 | 4 | Tradezella, StockSharp, moomoo (failed new HOD -> VWAP) | "Mid-session only; never the first 30 min; fails on trend days." |
| 3 | Gap-and-go / premarket-high break | 2 | 11 | 13 | R9 (2021, avoided), R14 (2024); Warrior; Tradezella; daytradingtoolkit; Calhoun S&C (2011) | "Academic work says large gaps more often reverse." "Of 20+ gappers only 2-3 qualify." "Needs a catalyst, premarket volume and float." "Chasing late is the killer." |
| 4 | Time-of-day rules (trade the first hour, skip lunch, 11:00-15:30 "death zone" for 0DTE) | 2 | 9 | 11 | R5, R13 (2026); traders.com (2012); Benzinga (2013); tradingsim; daytradingtoolkit; 0DTE TV script | Lunch defined as 11:30-14:00 or 12:00-13:00. One NexusFi voice says chop can come at any hour. |
| 5 | Relative strength / weakness vs SPY (r/RealDayTrading) | 5 | 5 | 10 | R7 (2025), R8 (2021), R9 (2021), R10 (2023), R11 (2022); OneOption RRS; TV RRS script | "Only with the market's direction; sit out when SPY is undecided." "RS is not RSI or beta." "Not a full methodology on its own" (TV author). |
| 6 | 9/20/21 EMA pullback and 9/21 cross | 0 | 10 | 10 | kotakneo; sahi; quantifiedstrategies (daily); lilys (2-min 9/21); sozai (SMB 9 EMA) | "Only when the trend is obvious"; "stay out when the EMAs are tangled"; lagging. |
| 7 | ICT: fair value gap, liquidity sweep, silver bullet (10-11, 14-15 ET) | 1 | 8 | 9 | R21 (2026, 15-min ORB + FVG); JadeCap and TradingFinder TV scripts; backtrex; gist.ly ("25,000 silver bullet variants") | No independent evidence; scripts are marketing. "Unclear what to do if both sides are swept." 15-trade, 45-day video sample. |
| 8 | Mean reversion: RSI(2)/RSI extremes, Bollinger touch | 1 | 7 | 8 | R18 (2024); LuxAlgo RSI-2; ProRealCode (2016); QuantifiedStrategies QQQ | "Built for daily bars." "Catastrophic on 1-min." "Its popularity dried up." |
| 9 | Gap fade / gap fill to the prior close | 0 | 6 | 6 | Edgeful; QC TSLA (+, 2017-22) / AAPL (-) / universe (-83%); XAU weekend-gap study | "Gaps usually fill, but first run about 2x the gap against you; the fade's profit factor was < 0.5 with a 1-gap stop." |
| 10 | Red-to-green / green-to-red through the prior close | 0 | 6 | 6 | bullishbears; BBT forum; S&C sidebar (Singer); TV idea; Tradervue logs | "Works only for certain stocks." A failed trade log: "why would a down stock on a down day go green?" |
| 11 | PDH/PDL key levels: break and retest | 0 | 6 | 6 | Tradezella (break-retest, "no-trade zone"); 7-year break-and-retest video (lilys summaries); daytradingtoolkit | "Most meaningful in the first 60-90 min." "Don't enter on the break; the setup is the retest." |
| 12 | Parabolic / backside fade, short squeeze, low-float runner | 0 | 6 | 6 | daytradingtoolkit (2); CenterPoint (2); Tradezella small-cap short; TV "sell every spike" | "The highest-volume candle prints at the top." "Not a beginner system: halts, locates, borrow." |
| 13 | Inside bar / inside day breakout | 1 | 5 | 6 | R23 (2026); daytradingtoolkit inside day; Edgeful SPY; StockSharp; strategyquant | Small samples and vendor return claims only. |
| 14 | RSI / MACD divergence | 0 | 6 | 6 | Babypips; Topdog; Nadex; ProRealCode; TradingQnA | "Against a strong trend it hits one stop after another." "MACD divergence often doesn't work." "Early warning, not a trigger." |
| 15 | Bull flag / micro-pullback (Ross Cameron style) | 1 | 4 | 5 | R14 (2024); daytradingz; Warrior; BBT/Aziz notes | "Super fast, difficult to execute"; a 1-min pattern; low float. |
| 16 | HOD break with momentum scanner (low float, RVOL) | 0 | 5 | 5 | tapeboard HOD scanner; scanz; daytradingtoolkit; TV Ross float < 10M | Needs float data. "A gap without a catalyst is a common failure." |
| 17 | 10:00 AM reversal (also 10:30) | 0 | 5 | 5 | daytradingtoolkit; MoneyShow (Lange); S&C Calhoun (2023); NexusFi question; BBT 9:20 reversal | Chart observation only; no win-rate data. |
| 18 | ABCD pattern | 0 | 4 | 4 | daytradingz; Dukascopy; TV detector; BBT forum | BC usually retraces 38.2-78.6% of AB (61.8% the most common); volume should dry up on BC. Subjective; no stats. |
| 19 | Bollinger squeeze / BB + Heikin-Ashi | 0 | 4 | 4 | daytradingtoolkit squeeze (09:45-15:30); StockSharp (2); ProRealCode | Vendor return claims only. |
| 20 | Noise-area intraday momentum on SPY (Zarattini "Beat the Market") | 0 | 4 | 4 | Concretum; SFI; CXO; TV replication | TV replication: "results smaller, Sharpe very low"; validated on SPY only. |
| 21 | Trade management: max 1-2 trades/day, 2nd only after a win, daily max loss, BE then trail swing lows, fixed 1:1 to 2.4R | 4 | 1 | 5 | R1 (2025), R5 (2026), R16 (2024), R17 (2025-26) | Discipline matters more than the setup (R1, R5). |
| 22 | Order flow / tape / Level 2 | 0 | 4 | 4 | daytradingtoolkit L2; BBT; SMB; Udemy | "Spoofed size can vanish in 0.1 s"; course marketing. |
| 23 | Double bottom / higher low at VWAP ("W") | 0 | 3 | 3 | BBT VWAP bounce (2025); daytradingz | A confirmation, not a standalone signal. |
| 24 | Opening drive -> first pullback | 0 | 3 | 3 | daytradingtoolkit; TV "Opening Drive Quality"; curvedtrading | Weak when the drive "cannot extend" or the pullback is too deep. |
| 25 | Heikin-Ashi with VWAP / HA daily continuation | 1 | 1 | 2 | R7 (HA daily); LST (HA + VWAP) | One small blog test. |
| 26 | Supply / demand zones | 0 | 2 | 2 | OTA (MoneyShow); TV ES idea | Subjective drawing; no stats. |
| 27 | Williams Alligator as stop/exit | 1 | 0 | 1 | R2 (2023) | Commenters sceptical. |

Cross-cutting verdicts:
- **"Strategies stop working"**: intraday edges change with the regime (R6). A breakout system failed in 2023 (R6). The
  RSI(2) "edge dried up" (r-bloggers 2010).
- **"Needs Level 2 / tape"**: L2 pages and Ross-style small caps (R14).
- **"Works only in trending markets"**: EMA pullbacks, VWAP first pullback. VWAP fades and divergence are the mirror
  case: they "fail on trend days".
- **Costs**: the ORB replications reproduce the gross edge but net out to about zero after spread and slippage.

## 2. Lab conventions used in the specs (defaults unless a spec says otherwise)

- **Bars and windows:** 5-minute bars labelled by close time. Decisions at bar closes 09:50-15:00 (**full day
  first**). The am 09:50-11:30, mid 11:35-13:30 and pm 13:35-15:00 windows are reported only as a breakdown, never as
  the selection.
- **Population:** point-in-time adv20 >= 95M, the 2-year frames (`research/history2y`), regimes by
  `lib.regimes()`.
- **Entries:** entry at the signal bar's close. First qualifying bar per symbol-day per side, unless a re-entry
  variant is declared.
- **R and exits:** R = 0.25 x daily ATR(14) of prior sessions. Exits t1s1 (+1R / -1R), t05s1 (+0.5R / -1R), t1s05
  (+1R / -0.5R), and flat at 15:55. Production costs (`gates.prod_r`).
- **Structural exit (S):** added where the strategy has one. It is scored as a 4th exit, with the -1R stop kept as a
  disaster stop unless the spec gives a structural stop.
- **Long and short mirror:** "short mirror" = swap high/low, above/below and +/-.
- **Notation:**

| Symbol | Meaning |
|---|---|
| o, h, l, c, v | Bar i values |
| VWAP | Session VWAP from 09:30 |
| z | (c - VWAP) / ATRd |
| ATRd | Daily ATR |
| OR_k | High/low of the first k minutes (09:30 to 09:30+k) |
| HOD_i / LOD_i | High/low of the bars before i |
| PDH / PDL / PDC | Prior-day high / low / close |
| gap | open / PDC - 1 |
| fromOpen | c / open - 1 |
| vr | volumeRatio |
| e9 / e20 / e21 | 5-min EMAs |
| rsi / rsi5 | RSI(14) / RSI(5) |

  Column names follow the stack1009 frame (`vwapDistPct`, `fromOpen`, `gap`, `volumeRatio`, `dist_pdh_atr`,
  `dist_hod_atr`, `buyPressure`, `emaDiff`).
- **Data availability:**
  - Testable on our data: 5-minute frames with 1-minute bars for exits, daily priors, and SPY/QQQ bars.
  - **Not available:** premarket bars (none of the BDI notes uses them, and the roadmap lists a premarket scanner as
    not built), float, short interest/borrow, news/catalyst flags (Alpaca news is an open backlog idea), Level 2 and
    true bid/ask delta (only the tick-rule proxy exists).

## 3. Rule specs for the top 20 (plus the trade-management item)

"Coverage" points at our past tests:
- [ART] research/bdi/articles/NOTES.md
- [VID] research/bdi/videos/NOTES.md
- [STK] research/bdi/stack1009/NOTES.md
- [BL] research/backlog.jsonl id

### 1. Opening range breakout (ORB)
- **Rule (faithful, after 09:50):**
  - OR = OR_k with k in {5, 15, 30}.
  - Long: the first bar after 09:50 with c > OR_k high and the previous close <= OR_k high. Short mirror at the
    OR_k low.
  - Filters (Zarattini "stocks in play"): cumulative RVOL at 09:35 >= 2 (first-5-min volume / 14-day average for the
    same 5 minutes), price > $5, ATRd > $0.50, take the top-20 RVOL names per day.
  - OptionAlpha variant: OR width >= 0.2% of price.
- **Structural exit (S):** the stop at the opposite OR side (R12 uses a 1.5:1 target from it); or breakeven at +1R,
  then trail under the prior 2-bar swing low (R17); or the Zarattini 10% ATR stop held to 15:55.
- **Data:** all available. The OR forms before 09:50, which is fine because decisions fall after 09:50.
- **Coverage: HEAVILY TESTED.**
  - [BL] `t2-orb15` (retired; equal to random)
  - `orb5` (failed, -0.33R)
  - `t1-orb-exits` (stocks in play plus exit tests, failed)
  - `live-orb20_a` (live, thin)
  - [STK] "or" cross trigger both sides; `bdi-st-st1` (OR-low cross fade long, testing)
  - `nr7-orb` and `wi-ib-narrow-extension` (ideas)
- **NEW angle: the failed ORB ("double break", R19).**
  - Short when a bar closes back below OR_k high within m in {1, 2, 3} bars after a close above it, and price had
    gone at least 0.1 ATRd beyond the level. Long mirror at the OR low.
  - Structural target: the opposite OR side; stop at the extreme of the failed break.
  - Backlog: `bdi-reddit-orb-failed-break`.

### 2. VWAP family
- **2a VWAP reclaim (Tradezella/Scanz):**
  - Long when:
    - the stock was below VWAP for >= N consecutive closes, N in {3, 6} (>= 15/30 min);
    - the dip depth was min z over that run >= -0.75 ("shallow"; variant: any depth);
    - bar i closes above VWAP with vr >= 1.0 (variant 1.5).
  - Entry variant B: the first later bar whose low <= VWAP + 0.05 ATRd and close > VWAP (the "first pullback that
    holds").
  - Structural stop: the reclaim bar low, or VWAP - 0.1 ATRd. Structural exit: a close back below VWAP. Short mirror
    = VWAP loss.
  - Coverage: PARTIAL. [ART] `vwapx` (plain cross) failed. [STK] vwap cross with filters. NS3/RW4 "failed VWAP
    reclaim short" are finalists. Conti sweep-reclaim failed. **The time-below plus pullback-hold form is new**:
    `bdi-reddit-vwap-reclaim-hold`.
- **2b VWAP bounce / first pullback in a trend:**
  - Long when:
    - >= 80% of today's closes are above VWAP;
    - this is the first bar today with low <= VWAP + 0.05 ATRd;
    - c > VWAP;
    - vr < 1 on the pullback bars, then vr >= 1 on the trigger.
  - Coverage: TESTED, failed. `bdi-tg-p-pullback-vwap-long` failed (-0.085R, n 325k). [VID] JD / MP / ENVC / AVR all
    failed. `wi-vwap-first-pullback` is still an idea and is the same rule. **No new entry.**
  - The W-bottom variant is item 23 below.
- **2c Side-of-VWAP trend (ETF):** long QQQ/SPY while c > VWAP, flat or short below, with a +-0.1% band.
  Coverage: `wi-vwap-trend-etf` (idea, untested), [STK] vwap filters. **No new entry; run the existing idea.**
- **2d +-2SD band fade:** short when h >= VWAP + 2 sigma (volume-weighted SD), with the bar a reversal (c < o, upper
  wick >= 50%), 11:00-14:00 preferred. Target VWAP (S).
  Coverage: TESTED. [VID] `bdi-vid-envelopes` (ENVF) failed, AVF failed. **No new entry.**

### 3. Gap-and-go / premarket-high break
- **Faithful rule:** gap >= 2% (small caps: 10%). Buy the break of the premarket high at the open or on the first
  1-min candle high. Stop at the candle low or the PM low. Requires a catalyst and float < 10-20M (Ross).
- **Data:** premarket high/volume, float and catalyst: **NOT AVAILABLE**. Entries before 09:50 are outside our
  decision window. Low-float names are outside the adv20 >= 95M population.
- **Testable proxy (full day, after 09:50):**
  - Long when gap >= g (g in {1, 2, 4}%), c > VWAP, c > OR_15 high, and this is the first close above HOD_i after
    09:50 with vr >= 1.5.
  - Short mirror on gap-downs at LOD_i.
  - Structural exit: a close below VWAP, or below e9 after +0.5R.
- **Coverage: PARTIAL.**
  - [BL] `bdi-tod-open-0935-simple` (09:35-09:45 gap-go, failed: long +0.13 on up days / -0.25 on down days)
  - `bdi-rw-f1-extended-mover-events` (HOD/LOD breaks on extended movers, failed; longs never passed)
  - The L3 gap-down shorts are on probation (a different direction).
- **New entries:**
  - `bdi-reddit-gap-go-hod-fullday`: the full-day proxy.
  - `bdi-reddit-premarket-levels`: data idea; the faithful version needs extended-hours bars.

### 4. Time-of-day rules
- **Rule:** layer every setup with {first hour only 09:50-10:30, skip 11:30-14:00, skip 12:00-13:00, 0DTE "death
  zone" 11:00-15:30}.
- **Coverage: TESTED.** research/bdi/timeofday (owner policy: full day by default; time windows only when an
  out-of-sample check passes). `bdi-tod-*` entries. **No new entry.**

### 5. Relative strength / weakness vs SPY (r/RealDayTrading)
- **Rule (full day, both sides):**
  - Market gate: long only if SPY c > SPY VWAP and SPY e9 > e21 on 5-min; short mirror. Variant: no gate.
  - RRS (OneOption/Hari form) on n in {6, 12} bars (30/60 min):
    `RRS = (dC_stock - dC_spy / ATR_spy(5m,14) * ATR_stock(5m,14)) / ATR_stock(5m,14)`.
  - Long when RRS >= k (k in {0.5, 1, 2}), c > VWAP (the R7 rule), c > daily SMA20 and SMA50 of prior closes ("above
    all major daily SMAs"; SMA50 is feasible on the 2-year frames), and the time is >= 10:15 (R7 "30-45 min after
    the open").
  - Structural exit: a close back across VWAP, or RRS < 0.
- **Coverage: TESTED in narrow form.**
  - [BL] `t4-rel-strength` failed (1-min, top300, 10:00-11:30 only, SMA20 only, 30 configs)
  - `rw-t4_long_nomf` failed holdout look 1 (test -0.03R)
  - `rw-t4_long_vwapmf` and `rw-t4_both_sectormf` failed; `sector-rs` idea
- **Rework entry:** `bdi-reddit-rdt-rrs-fullday`.
  - Parent `t4-rel-strength`.
  - Differences from t4: ATR-normalised RRS, full day, 2-year frames, SMA50 now possible, both sides.
  - Holdouts: t4's descendant `rw-t4_long_nomf` used look 1, so this lineage starts at look 2 (t >= 1.5).

### 6. 9/20/21 EMA pullback and cross
- **Rule A (pullback):**
  - Long when e9 > e20 and both slope up over 3 bars, close > VWAP;
  - the pullback bar has low <= e9 and close >= e20 (the "9/20 zone");
  - trigger: the next bar's high > the pullback bar high with vr >= 1.
  - Exit S: 2R target, or a close below e9.
- **Rule B (cross):** e9 crosses e21 with vr >= 1 and the 15-min trend agreeing. Stop at the cross-bar low; 2:1.
- **Coverage: TESTED.**
  - [ART] `emax` failed on every geometry.
  - [VID] `bdi-vid-jdub` (0 of 16,200), `bdi-vid-bk-9ema-trail` failed; e9c1 exit tested.
  - [BL] `wi-ema-cross` is still an idea.
  - [STK] ema trigger; ST4 (emadn long) is testing.
- **No new entry.**

### 7. ICT: fair value gap, liquidity sweep, silver bullet
- **FVG retrace:**
  - Bullish FVG at bar j when l_j > h_{j-2} and the middle bar's range is >= 1.5 x its 20-bar mean ("displacement").
  - Long on the first later bar i (i - j <= 12) with l_i <= h_{j-2} + 0.5 x gap (the gap midpoint) and c_i > h_{j-2}.
  - Stop under l_{j-1}; or the standard R.
  - **Silver-bullet variant:** decisions only at 10:00-11:00 and 14:00-15:00 ET bar closes.
  - Short mirror.
- **Liquidity sweep ("turtle soup"):**
  - Short when h_i > L + 0.05 ATRd and c_i < L, with L in {PDH, OR_30 high, HOD over the prior 12 bars}.
  - Long mirror at PDL / OR low / LOD.
  - Structural target: the opposite side of the day range, or VWAP.
- **Data:** all available. "Premarket/overnight liquidity" levels need extended-hours bars (untestable part).
- **Coverage:**
  - Sweep at PDH/PDL is partly covered by [STK] `pdfail`.
  - VWAP sweep: [VID] `bdi-vid-sweep-delta` failed.
  - FVG: **NEW**, `bdi-reddit-ict-fvg-retrace`.
  - Sweep at OR/HOD levels: **NEW**, `bdi-reddit-level-sweep-reclaim`.

### 8. Mean reversion: RSI(2), RSI extremes, Bollinger touch
- **Rule:** long when RSI(2) <= 5 or 10, c < BB(20, 2) lower band, and the daily trend is up (c > daily SMA50). Exit
  S: RSI(2) > 70, or c > the 5-bar SMA. Short mirror.
- **Coverage: TESTED.**
  - [ART] `rsix` and `bbtouch` failed (-0.09 to -0.17R).
  - `obos-vwap-ma` and `obos-levels` failed; NS1 and ST3 are RSI(5) lineages; `x_bottom_div` failed.
- **No new entry.** If wanted, an RSI(2) layer is one more threshold on the existing grids.

### 9. Gap fade / gap fill
- **Rule:** short a gap-up >= g when, after 09:50, c < OR_15 low and c < VWAP. Target S = PDC (the fill). Stop at
  HOD. Long mirror.
- **Coverage: TESTED.** [BL] `x_gapfade_early_b` failed its holdout; `rw-wg1_pdl_fade` failed; P1/L2/L3 gap shorts
  failed, with three L3 versions on probation. **No new entry.** The snippet warning ("runs about 2x the gap first")
  argues for the structural exit only.

### 10. Red-to-green / green-to-red
- **Rule:** gap < -0.5%; the first bar after 09:50 with c > PDC and previous close <= PDC, vr >= 1.5. Target S = PDH
  (long) / PDL (short mirror on gap-ups). Stop at PDC - 0.1 ATRd.
- **Coverage:** [BL] `wi-red-to-green` (idea, **untested**, same rule). [STK] has no PDC-cross trigger. **Use the
  existing entry; no duplicate added.** Run it in the next pass.

### 11. PDH/PDL break and retest
- **Rule:**
  - Long: PDH broken earlier today (some close > PDH);
  - later bar i: l_i <= PDH + 0.05 ATRd and c_i > PDH (the retest holds);
  - at most 24 bars after the first break.
  - Stop at PDH - 0.1 ATRd. Target S = the 2R measured move.
  - Short mirror at PDL.
  - Variant: the same with the OR_30 high/low as the level.
- **Coverage:** [STK] `pdbrk` (the break itself) and `pdfail` (the failed break); ST5 (PDH break-up short) is
  testing. [ART] pivots (P/R1/S1) failed. **The retest-after-break entry is new:** `bdi-reddit-pdhl-break-retest`.

### 12. Parabolic / backside fade, short squeeze, low-float runner
- **Rule (testable part):**
  - Short when fromOpen >= 6%;
  - vr on the peak bar is the day's maximum;
  - the next bar or two make a lower high and c < e9;
  - "backside" variant: wait for c < VWAP.
  - Exit S: target VWAP.
- **Untestable:** float, borrow/locates, halts, multi-day "first red day".
- **Coverage: TESTED / LIVE.** `live-exhaustion_short`, `heat_fade_short`; [VID] VT volume top failed. NS2/RW6
  lineage shorts after SMA50 up-breaks. **No new entry.**

### 13. Inside bar / inside day
- **Rule:** an inside 5-min bar (h_i < h_{i-1}, l_i > l_{i-1}); long on a close above h_{i-1}. Inside-day variant:
  yesterday's range sits inside the day before, and today's break of PDH/PDL triggers.
- **Coverage: TESTED.** [BL] `t5-inside-bar` retired (-0.24R); `nr7-orb` idea. **No new entry.**

### 14. RSI / MACD divergence
- **Rule:** long when today's new 20-bar low has RSI(14) higher than at the prior 20-bar low and MACD histogram
  rising; trigger c > h_{i-1}. Short mirror.
- **Coverage: TESTED.** [BL] `x_bottom_div` failed its holdout; [ART] `obvdiv` failed; F3 `bull_div` failed.
  **No new entry.**

### 15. Bull flag (pole + flag)
- **Rule:**
  - Pole: c_{j} - l_{j-p} >= 1.0 x ATRd over p <= 3 bars with mean vr >= 1.5, inside the last 12 bars.
  - Flag: f in {2..6} bars after the pole high H; every flag bar's high <= H; flag low >= H - 0.5 x pole (<= 50%
    retrace); flag mean vr < pole mean vr.
  - Trigger: c_i > max flag high.
  - Stop: the flag low (structural), or the standard R.
  - Measured-move target S = the pole height.
  - Short mirror (bear flag).
- **Coverage:** [VID] `bdi-vid-micropullback-long` failed (no pole condition, kmax 1-3). [BL] `wi-intraday-vcp` is an
  idea (tight flag near HOD). **The pole + retrace geometry is new:** `bdi-reddit-bull-flag-pole`. The 1-min form
  needs 1-min entries (`bdi-vid-1min-entries`).

### 16. HOD break with a momentum scanner
- **Rule:** long when c > HOD_i (first time in >= 6 bars), fromOpen >= 3%, vr >= 2, cumulative RVOL >= 2.
- **Untestable:** float < 10M, news.
- **Coverage: TESTED.** F1 HOD/LOD-break events on extended movers failed; `wi-intraday-vcp` idea. **No new entry.**

### 17. 10:00 AM reversal
- **Rule:** at bar closes 10:00-10:35: the opening swing |fromOpen| >= 1.5% made its extreme in the last 3 bars;
  trigger: a close back through the prior bar's low (for an up swing) with vr >= 1.2. Short, target VWAP (S). Long
  mirror.
- **Coverage: PARTIAL.** [BL] `bdi-fade-opening-swing` (864 configs, 10:00-11:30; shorts beat the control but stayed
  negative after costs); research/bdi/timeofday. **No new entry**; the rework of that entry covers it.

### 18. ABCD
- **Rule:**
  - A = today's LOD (before B).
  - B = the highest high after A with B - A >= 1.0 ATRd.
  - C = the lowest low after B with retrace (B - C) / (B - A) in [0.382, 0.786] and C > A, made on lower average vr
    than the AB leg.
  - Trigger: the first close > B after C (the D leg starts).
  - Stop at C, or the standard R.
  - Target S: D = C + (B - A) (AB = CD).
  - Short mirror.
  - Variants: retrace bands [0.382, 0.618] / [0.5, 0.786]; trigger close > midpoint(B, C) (aggressive).
- **Coverage: NEW**, `bdi-reddit-abcd`. Nearest past test: [ART] `fib618` (a touch, not this structure) failed.

### 19. Bollinger squeeze / BB + Heikin-Ashi
- **Rule:** the squeeze (BB width in its lowest 20% of 60 bars, or BB inside Keltner) then c > the upper band, 09:45
  onward.
- **Coverage: TESTED.** [ART] `squeeze` failed; `bdi-art-squeeze-vol-rework` is queued. The HA part is in item 25.
  **No new entry.**

### 20. Noise-area intraday momentum (SPY/QQQ)
- **Rule:** the paper's bands (open +- 14-day mean absolute move-from-open at the same minute) with a VWAP trailing
  stop.
- **Coverage: TESTED.** [BL] `t7-noise-band` retired, `noise-band-simple` failed, `intraday-momentum-paper` idea.
  **No new entry.**

### 21 (management). Trade-count and loss discipline
- **Rules to test as risk overlays on live/probation setups:**
  - (a) per setup per symbol per day: a 2nd entry only if the 1st won (R5);
  - (b) per setup per day: stop after k in {1, 2, 3} losses (R1);
  - (c) breakeven at +0.5R / +1R, then trail the 2-bar swing low (R17).
- **Coverage:**
  - (c) is TESTED: `t6-exit-overlay` and `bdi-tg-exits-e1-e2` failed.
  - Account-level `max_daily_loss_r` exists (config/default.yaml 20R).
  - (a) and (b) per setup are **NEW**: `bdi-reddit-setup-day-loss-stop`. This is a risk overlay and still goes
    through the gates: it changes which trades are taken.

### Other new items, lower frequency
- **Double bottom ("W") at VWAP (BBT):**
  - Two lows within 0.1 ATRd of each other, both within 0.15 ATRd of VWAP, 3-12 bars apart.
  - Trigger: c > the high between them (the neckline), with c > VWAP.
  - Stop under the lower low. Target S = the neckline + the W height.
  - Short mirror ("M").
  - Backlog: `bdi-reddit-vwap-double-bottom`.
- **Heikin-Ashi + VWAP (LST, R7):**
  - Compute 5-min HA candles.
  - Long on the first green HA candle with no lower wick (HA open == HA low) while c > VWAP, after >= 2 red HA
    candles.
  - Exit S: the first red HA candle.
  - Short mirror.
  - Backlog: `bdi-reddit-ha-vwap`.
- **Alligator exit (R2):** Williams Alligator on 5-min bars (SMMA 13/8/5 shifted 8/5/3). Exit when c crosses the
  "teeth" (SMMA8) against the trade. An exit-only overlay on live setups: `bdi-reddit-alligator-exit`.
- **Supply/demand zones, order flow/L2:** untestable as stated. Subjective zones were partly covered by the [VID] BLK
  block-POC retest, which failed. True L2 is in the `bdi-vid-footprint` idea. No new entry.

## 4. New vs already tested: summary

| Rank | Item | Status in MCF | Backlog id(s) |
|---|---|---|---|
| 1 | ORB | Tested heavily (mostly failed; orb20_a live, thin). **New angle:** failed-break reversal | t2-orb15, orb5, t1-orb-exits, live-orb20_a, ST1; **bdi-reddit-orb-failed-break** |
| 2a | VWAP reclaim | Partial (plain cross failed; NS3 failed-reclaim short a finalist). **New:** time-below + pullback-hold | **bdi-reddit-vwap-reclaim-hold** |
| 2b | VWAP first pullback | Tested, failed | bdi-tg-p-pullback-vwap-long, wi-vwap-first-pullback (idea) |
| 2c | VWAP side trend on ETF | Idea, untested | wi-vwap-trend-etf |
| 2d | VWAP 2SD fade | Tested, failed | bdi-vid-envelopes |
| 3 | Gap-and-go | Partial (09:35-09:45 and HOD events failed). **New:** full-day proxy; faithful version blocked on premarket data | **bdi-reddit-gap-go-hod-fullday**, **bdi-reddit-premarket-levels** |
| 4 | Time-of-day rules | Tested (timeofday study) | bdi-tod-* |
| 5 | RS vs SPY (RDT) | Tested narrowly, failed. **Rework:** full-day ATR-normalised RRS with SMA50 | **bdi-reddit-rdt-rrs-fullday** (parent t4-rel-strength) |
| 6 | 9/20/21 EMA | Tested, failed | ART emax, bdi-vid-jdub, bdi-vid-bk-9ema-trail, wi-ema-cross |
| 7 | ICT FVG / sweep / silver bullet | **New** (VWAP sweep and PDH fail partly covered) | **bdi-reddit-ict-fvg-retrace**, **bdi-reddit-level-sweep-reclaim** |
| 8 | RSI(2) / BB mean reversion | Tested, failed | ART rsix/bbtouch, obos-* |
| 9 | Gap fade | Tested (L3 gap shorts on probation) | x_gapfade_early_b, L3-* |
| 10 | Red-to-green | Idea, **untested** | wi-red-to-green (existing) |
| 11 | PDH/PDL break-retest | Break and failed break covered (STK). **New:** the retest entry | **bdi-reddit-pdhl-break-retest** |
| 12 | Parabolic / backside fade | Tested / live | exhaustion_short, heat_fade_short, VID VT |
| 13 | Inside bar | Tested, retired | t5-inside-bar, nr7-orb |
| 14 | Divergence | Tested, failed | x_bottom_div, ART obvdiv |
| 15 | Bull flag | Micro-pullback failed. **New:** pole + flag geometry | **bdi-reddit-bull-flag-pole** |
| 16 | HOD momentum break | Tested, failed | bdi-rw-f1-extended-mover-events |
| 17 | 10 AM reversal | Partial | bdi-fade-opening-swing |
| 18 | ABCD | **New** | **bdi-reddit-abcd** |
| 19 | BB squeeze / HA | Tested, rework queued | bdi-art-squeeze-vol-rework |
| 20 | Noise area | Tested, failed | t7-noise-band, noise-band-simple |
| 21 | Trade-count / loss discipline | BE/trail tested and failed. **New:** per-setup day stop | **bdi-reddit-setup-day-loss-stop** |
| - | W at VWAP; HA + VWAP; Alligator exit | **New** (low frequency) | **bdi-reddit-vwap-double-bottom**, **bdi-reddit-ha-vwap**, **bdi-reddit-alligator-exit** |

**New backlog entries: 14.** All have status `idea` and `configs_tried` 0. One is a data item
(`bdi-reddit-premarket-levels`) and one is a rework (`bdi-reddit-rdt-rrs-fullday`).

**Suggested order for the testing pass:**
1. The cheap mechanical ones on existing frames: orb-failed-break, level-sweep-reclaim, pdhl-break-retest,
   vwap-reclaim-hold, gap-go-hod-fullday.
2. The existing `wi-red-to-green` idea.
3. The pattern geometries: abcd, bull-flag-pole, vwap-double-bottom.
4. ict-fvg-retrace, ha-vwap, rdt-rrs-fullday.
5. The overlays: setup-day-loss-stop, alligator-exit.

The configuration count must be declared before scoring (RESEARCH_RULES).
