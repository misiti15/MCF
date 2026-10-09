# BDI Reddit study 2026-10-09: years of Reddit day-trading talk, mined and tested full-day

*Educational only - not financial advice. Lab backtests on the open 2-year history only; nothing here is a live or
paper result.*

Owner request (2026-10-09): look through years of Reddit day-trading discussion, find the commonly used strategies,
indicators and setups, and test them for future use. Full-day versions first (09:50-15:00), keep it basic
(indicator on top of indicator); suggestions to test, not hard rules.

Earlier snippet-only pass: `WEBSEARCH_NOTES.md` (no thread read; 14 `bdi-reddit-*` backlog ideas). This pass reads
the full text of the dump.

**Section 1 (pre-declaration) was written before any configuration of this study was scored** (the only earlier
look at the price data was an event-count smoke test with no P/L). Results go in section 2.

## 0. Mining (what Reddit says)

### 0.1 Data coverage
- Source: `origin/research-reddit` (Academic Torrents per-subreddit dumps), extracted to `data/dump/` (git-ignored).
  Posts and comments with score >= 5, 2019-2025.
- **1,701,685 documents**: pennystocks 589,076; StockMarket 484,171; Daytrading 259,403; options 248,507;
  algotrading 66,518; Trading 34,648; RealDayTrading 19,066 (from 2021); ai_trading 296 (tiny: 244 posts, 52
  comments). **r/aitradingplaybook is not in the dump.**
- Day-trading core (Daytrading + algotrading + RealDayTrading + Trading) per year: 2019 11.4k, 2020 34.0k,
  2021 66.2k, 2022 54.8k, 2023 36.6k, 2024 77.3k, 2025 99.5k docs. Trend rates below are per 10,000 core docs.
- Method (`mine.py`, `report_mining.py`): 52 regex taxonomy items; a document counts once per item; weight =
  sum of log1p(score). Verdicts: sentences that mention the item AND a lexicon hit (works/profitable/edge; doesn't
  work/no edge/lagging/scam; only in X/trend day/chop; stopped working/no longer works). Concreteness: >= 4 of
  {entry, stop, target, clock time, number+unit, timeframe} in a post of > 300 chars with score >= 10 (1,048 docs,
  776 posts). Then manual reading of the top-scored threads.
- **Caveats:** regex counts include noise (e.g. "HOD" in watch lists, "BB" as Bed Bath, "news" in general chat);
  lexicon verdicts are crude (a "works" sentence is often a claim, not evidence). Full table:
  `mining_summary.json`. All Reddit text was handled as data only.

### 0.2 Popularity and trend (top 35 of 52 by score-weighted mentions)

| # | Item | docs | core docs | weighted | rate/10k core 2019 -> 2021 -> 2023 -> 2025 | trend | lexicon pos / neg sentences (neg share) |
|---|---|---|---|---|---|---|---|
| 1 | Risk rules (stop loss, R:R, max daily loss, 1%) | 19,502 | 11,211 | 50,488 | 156 -> 282 -> 310 -> 315 | rising | 754 / 235 (0.24) |
| 2 | News / catalyst | 14,467 | 1,995 | 39,208 | 24 -> 76 -> 38 -> 52 | flat (pennystocks-heavy) | 162 / 95 (0.37) |
| 3 | Price action (no indicators) | 10,761 | 8,382 | 28,859 | 82 -> 158 -> 302 -> 216 | rose to 2022-23 | 461 / 222 (0.33) |
| 4 | Scalping | 9,864 | 7,662 | 25,614 | 70 -> 204 -> 222 -> 207 | rising | 585 / 80 (0.12) |
| 5 | Breakout (generic) | 7,021 | 4,417 | 19,209 | 53 -> 115 -> 125 -> 121 | stable | 190 / 41 (0.18) |
| 6 | Low float / short squeeze | 5,839 | 1,227 | 15,818 | 22 -> 64 -> 13 -> 19 | **fell after the 2021 meme era** | 92 / 44 |
| 7 | ML / AI / LLM | 5,643 | 3,301 | 15,246 | 212 -> 56 -> 72 -> 136 | U-shape (LLMs in 2025) | 247 / 199 (0.45) |
| 8 | RSI | 4,628 | 2,846 | 12,480 | 90 -> 91 -> 65 -> 84 | flat | 211 / 105 (0.33) |
| 9 | First pullback / buy the dip | 4,575 | 777 | 12,443 | 7 -> 29 -> 15 -> 19 | flat | 46 / 12 |
| 10 | 0DTE options | 4,362 | 1,529 | 11,586 | 0 -> 8 -> 69 -> 53 | **rose from 2022** | 175 / 41 |
| 11 | Support / resistance, key levels | 4,109 | 3,554 | 11,438 | 49 -> 70 -> 120 -> 79 | peaked 2022 | 150 / 43 |
| 12 | VWAP | 3,533 | 3,006 | 9,686 | 39 -> 87 -> 72 -> 86 | stable-high (RDT 259/10k) | 98 / 32 (0.25) |
| 13 | Volume / RVOL | 3,422 | 1,966 | 9,191 | 29 -> 64 -> 48 -> 44 | flat | 53 / 18 |
| 14 | MACD | 2,853 | 1,933 | 7,797 | 46 -> 61 -> 36 -> 58 | flat | 127 / 81 (0.39, "lagging") |
| 15 | ICT / FVG / liquidity sweep / SMC | 2,981 | 2,825 | 7,628 | 2 -> 3 -> 86 -> 150 | **strongest riser (x50)** | 293 / 184 (0.39, "scam") |
| 16 | Candlestick patterns | 2,163 | 1,214 | 6,073 | 9 -> 24 -> 41 -> 27 | flat | 39 / 28 |
| 17 | Relative strength vs SPY | 1,798 | 1,630 | 5,202 | 5 -> 59 -> 44 -> 15 | **peaked 2022 with RDT** (RDT 673/10k) | 73 / 14 (0.16) |
| 18 | 50/200 SMA | 1,772 | 895 | 5,019 | 13 -> 28 -> 27 -> 13 | falling | 17 / 8 |
| 19 | Supply / demand zones | 1,819 | 1,161 | 4,836 | 6 -> 16 -> 50 -> 32 | rose to 2023 | 80 / 17 |
| 20 | Reversal / parabolic / backside | 1,760 | 773 | 4,815 | 10 -> 22 -> 26 -> 18 | flat | 32 / 17 |
| 21 | Opening drive / first hour | 1,665 | 1,072 | 4,610 | 19 -> 39 -> 21 -> 25 | flat | 51 / 8 |
| 22 | MA cross (EMA/SMA, golden cross) | 1,656 | 1,101 | 4,517 | 44 -> 29 -> 30 -> 30 | slowly falling | 90 / 48 (0.35) |
| 23 | 9/20/21 EMA | 1,531 | 1,350 | 4,187 | 10 -> 38 -> 52 -> 24 | peaked 2022 | 37 / 13 |
| 24 | Fibonacci | 1,482 | 1,142 | 4,004 | 18 -> 27 -> 26 -> 38 | flat-up | 97 / 40 |
| 25 | Momentum trading | 1,448 | 1,016 | 3,981 | 15 -> 48 -> 12 -> 27 | 2021 peak | 71 / 22 |
| 26 | Bollinger / squeeze / Keltner | 1,423 | 863 | 3,883 | 29 -> 28 -> 21 -> 19 | falling | 52 / 24 |
| 27 | RSI / MACD divergence | 1,273 | 885 | 3,612 | 25 -> 18 -> 23 -> 31 | flat | 52 / 7 (0.12) |
| 28 | Mean reversion | 1,320 | 1,040 | 3,492 | 50 -> 20 -> 32 -> 31 | falling (algotrading) | 114 / 33 |
| 29 | Volume profile / POC | 1,349 | 1,077 | 3,490 | 22 -> 16 -> 33 -> 34 | flat | 33 / 10 |
| 30 | Power hour | 1,234 | 372 | 3,177 | 3 -> 10 -> 9 -> 8 | flat | 21 / 6 |
| 31 | ATR stops | 1,140 | 1,033 | 2,994 | 19 -> 24 -> 31 -> 29 | flat | 47 / 14 |
| 32 | **Opening range breakout** | 1,062 | 976 | 2,906 | 4 -> 9 -> 7 -> **69** | **x7 jump in 2025** | 97 / 13 (0.12) |
| 33 | HOD / LOD break | 914 | 728 | 2,579 | 7 -> 24 -> 20 -> 9 | fell after 2022 | 12 / 5 |
| 34 | Gap and go | 864 | 685 | 2,560 | 19 -> 44 -> 8 -> 6 | **fell after 2021** | 22 / 6 |
| 35 | Stochastic | 894 | 678 | 2,402 | 60 -> 26 -> 14 -> 14 | **falling** | 32 / 31 (0.49) |

Lower down: bull/bear flag 766 docs; lunch chop 610; gap fill/fade 625; premarket levels 619; pairs/stat-arb 610
(falling 30 -> 6); PDH/PDL 447; Heikin-Ashi 331; ADX 280; Ichimoku 229 (neg share 0.45); inside bar 203; explicit
"VWAP reclaim" 168; Supertrend 154; red-to-green 131; explicit "VWAP fade" 104; ABCD 101.

**Trend summary (rose / fell):** rose - ICT/SMC (2 -> 150 per 10k), ORB (flat ~8 until 2024, 69 in 2025, driven by
"5/15-min ORB + FVG" futures posts), 0DTE (from 2022), risk rules, scalping, supply/demand (to 2023), LLM/AI (2025).
Fell - gap-and-go and float/short-squeeze (2021 meme-era peak), relative strength (2022 RDT peak), stochastic,
pairs/stat-arb, 50/200 SMA, Bollinger, HOD-break talk. Flat - RSI, MACD, VWAP, divergence, mean reversion.

### 0.3 Community verdicts (lexicon counts + manual reading; short excerpts, ids are Reddit post ids)
- **Process over setup (the loudest verdict).** Risk rules carry the most weight; recurring advice: "max 2 trades a
  day; if the first wins, stop" (1o2o1f4, 1p1e22b), daily max loss, "ONLY trade with the trend ... take profit
  usually at 1:1" (1is1x4t, 1,707 pts). "The system is not what is holding you back" is the dominant tone.
- **ORB:** 0.12 neg share, the most positive item. "The 5-minute ORB set me free" (1onr2g6), "15-minute ORB for
  trend days" (1pffqaz), "ORB and bull flags work great" (io2ryef). Almost all concrete 2025 ORB posts are **NQ/ES
  futures with an FVG/imbalance confirmation on 1-min**, fixed 1-2R targets, max 2 trades/day (1o2o1f4 1,445 pts;
  1p1e22b 640; 1oiwwu0 443 "53% win rate, 3.21R avg"; 1p2q59i 428; 1oux8t1 310 "thrives during trending weeks").
- **VWAP:** context, not a signal: "Price often returns to VWAP on choppy days" (1jmsxuw); "a hold above VWAP and a
  clean take of the premarket high often becomes a trend day; fail twice at VWAP and it is gap-fade" (1oqvb48);
  "VWAP bounce: don't buy the first touch ... wait for a long wick, high volume" (1izfkaw).
- **MACD / MA crosses:** "lagging" is the top negative (lmk74n 930 pts). Yet the top-scored concrete post (1ia39vf,
  2,785 pts) is "break of the SMA on a 5-min chart confirmed by a MACD crossover". "We all know moving average
  crossovers are crap" (k4x9ft); an r/algotrading test vs a random baseline (1nq1jsu).
- **ICT / SMC:** polarised: popular in 2024-25 ("IFVG entries ... waiting for liquidity sweeps", 1do07up 647 pts)
  and called a scam ("RIP ICT - Your Scam is Complete" 1ftvp9q; "ICT has never been profitable" 1iz759b).
- **Relative strength (RDT):** "By far the set-up that was most profitable were stocks with Relative
  Strength/Weakness to SPY" (pcx5aj); "RS/RW works in an oscillating wave ... you enter just as it's about to fade"
  (18w1p7g, a decay/regime caveat).
- **Regime:** the most common qualifier everywhere is "trend day vs chop day": breakouts on momentum days, S/R on
  choppy days (mksjymp); "buy the dip works til it doesn't" (rq3koi); bear flags "either didn't work or gave a very
  small profit" (pwlf5a).
- **Gap and go:** "fine but not the only one" (moacgv); RDT: down gap-and-go days are choppier with bigger bounces
  (xy8756). Talk volume fell ~85% after 2021.
- **Decay ("stopped working")** sentences are rare (<= 8 per item); no item has a strong decay signal.

### 0.4 Concrete rules transcribed from the most-upvoted rule posts
| Post (pts) | Market / tf | Entry | Stop | Target / time | Testable here? |
|---|---|---|---|---|---|
| 1ia39vf (2,785) | stocks, 5-min | close breaks above/below a "10-day" SMA, confirmed by a MACD crossover | - | scale out at +1/2/3% | yes, approx (SMA20, MACD line sign) -> R20 |
| 1o2o1f4 (1,445) | NQ, 5-min OR then 1-min | first 5-min candle = range; break; FVG forms outside the range; retrace into FVG + engulfing | beyond engulfing candle | fixed 2R; BE after internal liquidity; max 2/day, stop after a win | approx (OR30, 5-min FVG) -> R18 |
| 1oaa8t9 (1,016) | stocks/futures, 5-min | OR 15-30 min break; wait for a pullback to 50-61.8% of session low->high; MACD curl | below 78.6% | new high of day | yes -> R19 |
| 1ln0lpm (650) | NQ 1-min | price above 9 and 19 EMA; retest (touch) of the 9 EMA | below 19 EMA | recent high or 1:2-1:3 | approx (5-min, SMA20 touch with EMA9>EMA21) -> R09 |
| 1p1e22b (640) / 1p2q59i (428) / 1oux8t1 (310) / 1oiwwu0 (443) | NQ/ES | 5- or 15-min ORB + FVG/imbalance in the break direction | FVG candle | 1-2R by stop size | -> R18 |
| 1jwrkfm (614) | forex 1-min | 2+ trend candles after a momentum candle, small-body candle, break of its body | candle extreme | 2:1-4:1 | partly (bull flag R08 is the nearest) |
| 1is1x4t (1,707) | any | only with the trend, avoid overlapping bars, reversal bar near the 21 EMA | - | 1:1 | approx -> R09 |
| icro65 (336) | stocks | opening doji on a stock above its 50-day MA that touched its 200-day; next candle closes above the doji | doji open | 3R half, trail | no (daily MAs not in the live frame; first-candle rule needs the 09:35 bar) |
| 1hvwxps (1,171) | small caps | premarket volume >= highest daily volume | - | - | **no (premarket, float)** |
| 1n8dxub (1,625) | SPY 0DTE | after 10:00, fade PDH/PMH rejection with 2+ signals; 5-min hold, 20-30 min cap | -50% premium | +15-30% premium | **no (options, premarket)** |

## 1. Pre-declaration (written 2026-10-09 ~19:28 UTC, before scoring)

### 1.1 Data, population, costs
- Rows: `research/bdi/stack1009/data/base.npz` (built by `research/history2y/lib.py` with `MCF_HIST_ALLOW_LOCKED`
  unset: the rule-19 locked block 2024-11-01..2025-02-28 is not in it) + `data/extra.npz` (bar high/low, wicks,
  divergence flags; `prep_extra.py`, row-aligned and asserted). 426 open sessions, point-in-time adv20 >= 95M,
  bar closes 09:50-15:00. Survivorship caveat as RESCORE.md.
- Entry at the signal bar's close; **first qualifying bar per symbol-day** per configuration; R = 0.25 x daily ATR.
  Fixed exits t1s1 / t05s1 / t1s05 from the frames (exit by 15:55) with production costs (`gates.prod_r`).
- **Structural exit S** (where the strategy has one): simulated on the 5-min rows from the next bar: stop-first at
  -1R on the bar's low/high, then the structural target (a limit, no exit slippage), then the structural condition
  at a bar close, else flat at the **15:00** bar close (the lab rows stop at 15:00; the fixed exits hold to 15:55).
  Production costs: 1c + 1 bps per side (no exit-side cost on a target fill) + 2c on stops. 5-min resolution (no
  1-min path), so S is approximate and slightly coarser than the fixed exits.
- Regimes: `lib.regimes()` (up / flat / down terciles of the universe median open-to-close).

### 1.2 Live parity
Only live-frame columns (`heat_frame` + `setup_lab.extra_features` + today's `volume`): close/high/low, rsi, rsi5,
emaDiff, macdPct, volumeRatio, vwapDistPct, fromOpen, gap, atr_d, dist_pdh/pdl/hod/lod_atr, sma20/50 dist, sma20
slope, bull_div/bear_div, wicks, tod. Derived: VWAP = close/(1+vwapDistPct/100); z = (close-VWAP)/atr_d; day open =
close/(1+fromOpen/100); prior close PDC = open/(1+gap/100); HOD/LOD/PDH/PDL from the distance columns; opening
range = HOD/LOD at the 10:00 bar (OR30; OR5/OR15 are not computable on the history frames, which start at the 09:50
bar); SPY's z and move-from-open at the same bar (R16 and the `spy` filter; live needs SPY's frame - flagged).
Prev-bar values never cross a symbol-day. As in stack1009, a rule keyed to the previous bar can fire on the 09:50
bar live (09:35-09:45 rows exist live) but not in the scan; small, stated.
**Untestable, skipped or approximated:** premarket high/low and volume (no extended-hours bars) - gap-and-go uses
the gap and a break of the day's prior high instead; float / short interest / borrow (low-float squeeze not
tested); news / catalysts (no flag); Level 2 / tape; options/0DTE (not our instrument); volume profile / POC
(no intraday volume history in the lab rows - VWAP is the nearest proxy); supply/demand zones and generic S/R
(subjective drawing); daily 50/200 MAs (not in the live frame); EMA9/19/20 individually (emaDiff + SMA20 are the
proxies); MACD signal line (MACD line sign only); Bollinger squeeze (needs 20 bars of history the history frames
lack before ~11:30; tested in [ART], see 1.6).

### 1.3 The 20 rule specs (long; the short is the exact mirror)
Selection = popularity (0.2) x concreteness (0.4, rule posts) x testability (1.2), ~15 asked; 20 kept because three
of them (R18-R20) are the highest-scored concrete posts. Main parameter p with its plateau grid in brackets.
| ID | Reddit item (rank) | Base trigger (long) | p [grid] | Structural exit S |
|---|---|---|---|---|
| R01 orb30 | ORB (#32, x7 in 2025) | first close above the 09:30-10:00 high + p ATR, after 10:00 | 0 [0, 0.1, 0.2] | close back inside the OR |
| R02 vwap-reclaim | VWAP (#12) reclaim | close crosses above VWAP after >= p consecutive closes below | 6 [3, 6, 12] | close back below VWAP |
| R03 vwap-fade | VWAP fade / mean reversion (#28) | after a close below VWAP - p ATR, the first close back above it | 1.0 [0.75, 1, 1.25] | close at/above VWAP (target) |
| R04 gap-go | gap and go (#34) | gap >= p % and the close breaks the prior HOD, first time | 2 [1, 2, 3] | close below VWAP |
| R05 gap-fill | gap fill / fade | gap <= -p %, close crosses above the day's open, first time | 2 [1, 2, 3] | target = prior close (fill) |
| R06 red-green | red-to-green | opened >= p % below the prior close; close crosses above it, first time | 0.5 [0, 0.5, 1] | close back below the prior close |
| R07 hod-break | HOD break (#33), breakout (#5) | close above the prior HOD set >= p bars earlier, from 10:00 | 6 [3, 6, 12] | close below VWAP |
| R08 bull-flag | bull flag | pole >= p ATR (low of bars i-12..i-4 to high of i-6..i-2), 2-bar flag below the pole high retracing <= 50%, close above the pole high | 0.5 [0.35, 0.5, 0.75] | close below the flag low |
| R09 ema20-pullback | 9/20 EMA (#23), first pullback (#9) | EMA9 > EMA21, SMA20 rising, low touches SMA20 + p ATR, close above SMA20; first per day | 0 [0, 0.1, 0.2] | close below SMA20 |
| R10 ema-cross | MA cross (#22) | emaDiff (EMA9 vs EMA21) crosses above +p | 0 [0, 0.05, 0.1] | crosses back below 0 |
| R11 rsi-os | RSI (#8) | RSI(14) crosses back above p on a stock green vs the prior close | 30 [25, 30, 35] | RSI back to 50 |
| R12 rsi-div | divergence (#27) | bull_div flag within the last p bars and the close crosses above the prior bar's high | 3 [1, 3, 6] | (none) |
| R13 macd-zero | MACD (#14) | MACD line crosses above +p (% of price) | 0 [0, 0.05, 0.1] | crosses back below 0 |
| R14 ict-fvg | ICT FVG (#15) | bullish 3-bar FVG >= p ATR earlier today; a bar dips into it (low <= gap top) from above and closes above the gap bottom | 0.1 [0.05, 0.1, 0.2] | close below the gap bottom |
| R15 sweep | ICT liquidity sweep (#15) | bar low below the prior LOD by >= p ATR, close back above it, from 10:00 | 0.05 [0, 0.05, 0.1] | close below the sweep low |
| R16 rel-strength | RS vs SPY (#17) | (stock move from open - SPY move from open, each in its daily ATR) crosses above +p | 1.0 [0.75, 1, 1.5] | close below VWAP |
| R17 pd-retest | PDH/PDL, S/R (#11) | after an earlier close above PDH today, low within p ATR of PDH and close above it (first retest) | 0.1 [0.05, 0.1, 0.2] | close below PDH |
| R18 orb-fvg | ORB + FVG (2025 rule posts) | R14 after an earlier OR30 break up | 0.1 [0.05, 0.1, 0.2] | as R14 |
| R19 orb-fib | ORB + Fib (1oaa8t9) | after an OR30 break up, low reaches the p retracement of LOD->HOD, close holds above 61.8%; first per day | 0.5 [0.382, 0.5, 0.618] | target = prior HOD; close below the 78.6% level |
| R20 sma-macd | SMA + MACD (1ia39vf) | close crosses above SMA20 with the MACD line > p | 0 [0, 0.05, 0.1] | close back below SMA20 |

### 1.4 Filters ("indicator on top of indicator"; at most 2; side-relative)
`rvol` volumeRatio >= 1.5 ("volume confirms"; grid 1.25/1.5/2); `vwap` long above / short below VWAP; `trend` SMA20
slope on the trade side; `spy` SPY on the trade side of its VWAP ("trade with the market", RDT); `inplay`
|fromOpen| >= 2% ("stocks in play"; grid 1.5/2/3). Filter sets: none, 5 singles, 10 pairs = 16.

### 1.5 Grid and counting
20 strategies x 2 sides x 16 filter sets x exits (3 fixed + S for the 19 with a structural exit) = **2,528
configurations**, full day 09:50-15:00, all scored and kept in `data/scan.csv`. Every cheap passer (below) gets its
plateau neighbours scored (the two other p values, and the other thresholds of a `rvol`/`inplay` filter it uses);
those are counted too. N = main grid + neighbours; t_required = max(1.5, sqrt(2 ln N)) (~3.96 for N ~ 2,600).
am/mid/pm breakdowns are reported for finalists only and never used for selection.

### 1.6 Live-probation bar (as stack1009; all must hold)
n >= 150; exp R > 0 in up AND down sessions; day-clustered t >= 2.0; walk-forward share >= 0.6 (locked months
excluded); plateau mean of the one-step neighbours > 0; ex-best-day exp > 0. Also required (stack1009 amendment A):
the busiest session holds <= 10% of the trades. "Cheap passers" = n, up, down, t, ex-best-day and busiest-day gates;
walk-forward and plateau are computed for them. Reported for every cheap passer: trades/day, win rate, t vs
t_required, verdict (`gates.verdict`), am/mid/pm, and a time-matched random-entry baseline (mean production R of
all rows at the same bar times, same side and exit). These are probation candidates, not "keep", unless t >=
t_required.

### 1.7 Overlap with past tests (referenced, not re-run identically)
Nothing below is an identical re-test: earlier tests were windowed (stack1009 am/mid/pm), on the old 40/14-session
train/valid split ([ART], [VID]), or on other populations. Closest relatives: R01 - stack1009 `or` family, t2-orb15,
orb5, live-orb20_a, ST1; R02 - plain VWAP cross ([ART] vwapx failed), NS3/NS4, bdi-reddit-vwap-reclaim-hold (this
tests it); R03 - stack1009 band10, bdi-vid-envelopes; R04 - bdi-reddit-gap-go-hod-fullday (this tests it); R05 -
L3 gap shorts (probation), x_gapfade_early_b; R06 - wi-red-to-green (this tests it); R07 - stack1009 hodlod,
bdi-rw-f1-extended-mover-events; R08 - bdi-reddit-bull-flag-pole (this tests it); R09 - bdi-tg-p-pullback-vwap-long,
wi-vwap-first-pullback; R10 - [ART] emax, stack1009 ema, bdi-vid-jdub, wi-ema-cross; R11 - [ART] rsix, stack1009
rsi14; R12 - x_bottom_div, [ART] obvdiv; R13 - [ART] macdx (signal-line cross), stack1009 macd; R14/R18 -
bdi-reddit-ict-fvg-retrace (this tests it); R15 - bdi-vid-sweep-delta, bdi-reddit-level-sweep-reclaim (this tests
the LOD/HOD version); R16 - t4-rel-strength, bdi-reddit-rdt-rrs-fullday (this tests it); R17 -
bdi-reddit-pdhl-break-retest (this tests it); R19 - [ART] fib618 (a touch, no ORB context); R20 - stack1009 sma20 +
macd_with stacks (windowed). Not re-tested (already done, results stand): Bollinger squeeze/touch ([ART] squeeze,
bbtouch failed; bdi-art-squeeze-vol-rework queued), stochastic, ADX/DMI, Ichimoku ([ART] all failed),
inside bar (t5-inside-bar retired), noise-area momentum (t7-noise-band retired), time-of-day rules
(research/bdi/timeofday).

### 1.8 Amendment A (2026-10-09 ~19:45 UTC, after the main grid of 2,528 configurations; those count)
The main grid produced **no cheap passer** (section 2). Per the lead's instruction ("or the best few if none"), the
best few are chosen by a rule fixed now: exp > 0, n >= 150, busiest session <= 10% of trades, a fixed exit (live
LabStrategy cannot run S) and no `spy` filter (live LabStrategy sees one symbol's frame), ranked by day-clustered t.
That gives 3 distinct configurations (R04 short rvol t1s1; R05 short rvol+trend t05s1; R03 long trend+inplay t1s1).
R19 long vwap+inplay t1s1 (the best live-implementable t, but 25% of its trades on one session) is scored the same
way for reference. For these 4: full gates (`gates.verdict`, walk-forward), plateau neighbours (counted in N),
am/mid/pm, time-matched baseline, and lab modules for the 3 (verification of mask == scan). They are reported as
what they are - not probation candidates.

## 2. Results (appended 2026-10-09 ~20:15 UTC; section 1 unchanged except the dated amendment A)

*Lab backtest on the open 2-year history only (not live, not paper). Production costs. Educational only - not
financial advice.*

### 2.1 Failures first
- **No configuration meets the live-probation bar. No configuration even meets the cheap gates** (n >= 150, exp > 0
  in up AND down sessions, t >= 2.0, ex-best-day > 0, busiest session <= 10%).
- **Configurations evaluated: 2,551** (main grid 2,528 + 23 neighbours for the best few). t_required =
  sqrt(2 ln 2551) = **3.96**. Best day-clustered t found: 2.08 (R03 short trend+inplay S, 64% of its trades on one
  session - the 2025-04 tariff crash/rebound); best with a busiest day <= 10%: **0.54** (R05 long vwap+spy S).
- Only 57 of 2,528 configurations (2.3%) have exp > 0 after costs; 12 are positive in both up and down sessions,
  2 of them with n >= 150, and those fail t (both < 0.9) and busiest-day.
- **Every base rule (no filter) is negative full-day on every fixed exit** (-0.01R to -0.20R, typically -0.07R to
  -0.10R, i.e. about the cost of trading); with the structural exit only R03 short (+0.022R), R05 long (+0.010R) and
  R05 short (+0.024R) are above zero, all with t <= 0.30: the time-matched random-entry baseline is -0.07R to -0.09R. The Reddit triggers do not separate from
  random entries at the same bar times.
- **The regime split is the whole story.** Every long variant is positive in up sessions and negative in down
  sessions; every short variant is the mirror (e.g. ORB30 long: up +0.128 / down -0.318; ORB30 short: up -0.320 /
  down +0.101). This is market beta, which the Reddit qualifier "only works on trend days / with the market"
  describes literally. The `spy` filter (SPY on the trade side of its VWAP at the bar) and `trend` filter do not
  remove it: knowing the session regime at the end of the day is what separates them, and that is not known at entry.
- Structural exits (S) do not rescue anything: 30 of 608 S configurations are positive, none with t >= 1.0 at a
  busiest day <= 10%.
- The three best-few modules (amendment A) **fail** every gate except n and busiest-day (2.3).
- Not done: locked block (the lead scores it once; nothing qualifies); no rework round (rule 18) - queued as
  backlog notes; Bollinger squeeze, stochastic, ADX, Ichimoku, inside bar, noise area and time-of-day were not
  re-tested (failed before, 1.7).

### 2.2 All 40 strategy-sides (results.csv; base = no filter, its best exit by t; best = best of 64 by t, n >= 150)
| strategy | side | exp > 0 | base | best of 64 |
|---|---|---|---|---|
| R12-rsi-div | short | 0/48 | t1s1: n 251773 (591/day), win 0.472, -0.091R, t -7.23; up -0.278 / flat -0.053 / down +0.109 | trend+inplay / t1s1: n 3952 (9.3/day), win 0.469, -0.084R, t -2.88; up -0.204 / down +0.036; ex-best-day -0.103; busiest day 3% |
| R20-sma-macd | long | 0/64 | t1s1: n 229309 (538/day), win 0.476, -0.090R, t -7.3; up +0.087 / flat -0.117 / down -0.296 | rvol+inplay / S: n 9463 (22.2/day), win 0.277, -0.049R, t -2.75; up +0.008 / down -0.127; ex-best-day -0.059; busiest day 1% |
| R11-rsi-os | short | 0/64 | t1s1: n 118472 (278/day), win 0.47, -0.089R, t -5.0; up -0.309 / flat -0.099 / down +0.110 | trend+spy / t1s1: n 15470 (36.3/day), win 0.482, -0.065R, t -2.66; up -0.328 / down +0.070; ex-best-day -0.071; busiest day 1% |
| R02-vwap-reclaim | short | 0/64 | t1s1: n 226200 (531/day), win 0.48, -0.077R, t -5.45; up -0.305 / flat -0.068 / down +0.143 | rvol+spy / t1s1: n 22203 (52.1/day), win 0.485, -0.054R, t -2.4; up -0.415 / down +0.108; ex-best-day -0.060; busiest day 2% |
| R09-ema20-pullback | short | 0/64 | t1s1: n 288104 (676/day), win 0.479, -0.083R, t -6.62; up -0.291 / flat -0.105 / down +0.110 | rvol+inplay / t1s1: n 4705 (11.0/day), win 0.475, -0.061R, t -2.39; up -0.189 / down +0.056; ex-best-day -0.075; busiest day 2% |
| R12-rsi-div | long | 0/48 | t1s1: n 241733 (567/day), win 0.474, -0.097R, t -7.62; up +0.104 / flat -0.069 / down -0.270 | trend+inplay / t1s1: n 3947 (9.3/day), win 0.469, -0.072R, t -2.31; up +0.094 / down -0.228; ex-best-day -0.095; busiest day 2% |
| R17-pd-retest | short | 0/64 | t1s1: n 118326 (278/day), win 0.488, -0.080R, t -5.33; up -0.316 / flat -0.112 / down +0.113 | spy+inplay / t1s1: n 13071 (30.7/day), win 0.488, -0.061R, t -2.29; up -0.384 / down +0.057; ex-best-day -0.073; busiest day 2% |
| R14-ict-fvg | short | 0/64 | S: n 102671 (241/day), win 0.327, -0.086R, t -4.42; up -0.260 / flat -0.123 / down +0.076 | spy+inplay / t1s1: n 18132 (42.6/day), win 0.498, -0.051R, t -2.14; up -0.264 / down +0.051; ex-best-day -0.061; busiest day 3% |
| R08-bull-flag | short | 0/64 | S: n 36220 (85/day), win 0.323, -0.147R, t -4.15; up -0.367 / flat -0.136 / down -0.039 | rvol+inplay / S: n 3146 (7.4/day), win 0.331, -0.115R, t -1.99; up -0.302 / down +0.018; ex-best-day -0.158; busiest day 6% |
| R18-orb-fvg | short | 0/64 | S: n 61706 (145/day), win 0.329, -0.089R, t -3.58; up -0.280 / flat -0.158 / down +0.068 | rvol+inplay / t1s1: n 5984 (14.0/day), win 0.489, -0.053R, t -1.89; up -0.180 / down +0.063; ex-best-day -0.071; busiest day 3% |
| R11-rsi-os | long | 0/64 | t1s1: n 120891 (284/day), win 0.475, -0.086R, t -5.75; up +0.085 / flat -0.092 / down -0.276 | rvol+inplay / t1s1: n 2904 (6.8/day), win 0.472, -0.067R, t -1.82; up +0.071 / down -0.201; ex-best-day -0.086; busiest day 3% |
| R07-hod-break | short | 0/64 | S: n 107344 (252/day), win 0.369, -0.086R, t -3.3; up -0.296 / flat -0.199 / down +0.088 | spy+inplay / S: n 21008 (49.3/day), win 0.391, -0.075R, t -1.74; up -0.378 / down +0.030; ex-best-day -0.103; busiest day 2% |
| R14-ict-fvg | long | 0/64 | S: n 101808 (239/day), win 0.34, -0.072R, t -3.81; up +0.122 / flat -0.118 / down -0.260 | spy+inplay / t1s1: n 19166 (45.0/day), win 0.503, -0.045R, t -1.74; up +0.052 / down -0.254; ex-best-day -0.059; busiest day 3% |
| R20-sma-macd | short | 0/64 | t1s1: n 223125 (524/day), win 0.478, -0.078R, t -5.68; up -0.298 / flat -0.114 / down +0.110 | spy+inplay / t1s1: n 28630 (67.2/day), win 0.483, -0.053R, t -1.71; up -0.358 / down +0.058; ex-best-day -0.066; busiest day 2% |
| R16-rel-strength | long | 0/64 | t1s1: n 41791 (98/day), win 0.48, -0.113R, t -5.78; up +0.079 / flat -0.072 / down -0.211 | rvol+spy / S: n 2647 (6.2/day), win 0.364, -0.067R, t -1.63; up +0.046 / down -0.211; ex-best-day -0.080; busiest day 2% |
| R02-vwap-reclaim | long | 0/64 | t1s1: n 222794 (523/day), win 0.483, -0.079R, t -5.6; up +0.145 / flat -0.073 / down -0.283 | rvol+inplay / S: n 4795 (11.3/day), win 0.259, -0.036R, t -1.63; up +0.093 / down -0.097; ex-best-day -0.051; busiest day 2% |
| R01-orb30 | short | 0/64 | t1s1: n 191181 (449/day), win 0.487, -0.081R, t -5.29; up -0.320 / flat -0.148 / down +0.101 | spy+inplay / t1s1: n 22824 (53.6/day), win 0.495, -0.047R, t -1.5; up -0.417 / down +0.090; ex-best-day -0.058; busiest day 2% |
| R18-orb-fvg | long | 0/64 | t1s1: n 59775 (140/day), win 0.5, -0.063R, t -3.69; up +0.121 / flat -0.142 / down -0.278 | spy+inplay / t1s1: n 13766 (32.3/day), win 0.497, -0.057R, t -1.49; up +0.032 / down -0.292; ex-best-day -0.078; busiest day 5% |
| R10-ema-cross | short | 0/64 | t1s1: n 295623 (694/day), win 0.478, -0.076R, t -5.98; up -0.273 / flat -0.087 / down +0.122 | rvol+inplay / S: n 7230 (17.0/day), win 0.362, -0.036R, t -1.43; up -0.105 / down +0.023; ex-best-day -0.047; busiest day 1% |
| R10-ema-cross | long | 0/64 | S: n 295267 (693/day), win 0.324, -0.081R, t -6.0; up +0.079 / flat -0.114 / down -0.209 | rvol+inplay / S: n 8007 (18.8/day), win 0.372, -0.035R, t -1.18; up +0.058 / down -0.117; ex-best-day -0.046; busiest day 2% |
| R19-orb-fib | short | 0/64 | t1s1: n 100419 (236/day), win 0.475, -0.094R, t -5.62; up -0.334 / flat -0.129 / down +0.120 | rvol+inplay / t1s1: n 1141 (2.7/day), win 0.493, -0.041R, t -0.93; up -0.258 / down +0.088; ex-best-day -0.069; busiest day 5% |
| R16-rel-strength | short | 0/64 | S: n 35999 (85/day), win 0.331, -0.099R, t -5.2; up -0.166 / flat -0.114 / down +0.107 | rvol+spy / S: n 2102 (4.9/day), win 0.353, -0.039R, t -0.86; up -0.086 / down +0.111; ex-best-day -0.055; busiest day 2% |
| R06-red-green | short | 0/64 | S: n 37785 (89/day), win 0.187, -0.076R, t -3.68; up -0.207 / flat -0.124 / down +0.033 | trend+inplay / S: n 4124 (9.7/day), win 0.218, -0.036R, t -0.75; up -0.148 / down +0.037; ex-best-day -0.078; busiest day 10% |
| R17-pd-retest | long | 0/64 | t1s1: n 124403 (292/day), win 0.488, -0.085R, t -6.35; up +0.109 / flat -0.138 / down -0.288 | rvol+inplay / t1s1: n 4395 (10.3/day), win 0.51, -0.024R, t -0.57; up +0.089 / down -0.229; ex-best-day -0.064; busiest day 6% |
| R15-sweep | long | 1/64 | S: n 63038 (148/day), win 0.301, -0.101R, t -4.89; up +0.222 / flat -0.071 / down -0.283 | trend+inplay / t1s1: n 1563 (3.7/day), win 0.51, -0.029R, t -0.54; up +0.070 / down -0.060; ex-best-day -0.040; busiest day 6% |
| R08-bull-flag | long | 0/64 | S: n 37191 (87/day), win 0.343, -0.123R, t -3.9; up +0.043 / flat -0.156 / down -0.379 | rvol+inplay / t1s1: n 3091 (7.3/day), win 0.52, -0.023R, t -0.51; up +0.100 / down -0.285; ex-best-day -0.059; busiest day 8% |
| R04-gap-go | long | 0/64 | t1s1: n 12615 (30/day), win 0.485, -0.079R, t -3.09; up +0.055 / flat -0.079 / down -0.277 | rvol+inplay / S: n 2085 (4.9/day), win 0.33, -0.011R, t -0.23; up +0.090 / down -0.239; ex-best-day -0.030; busiest day 1% |
| R13-macd-zero | long | 0/64 | S: n 249934 (587/day), win 0.346, -0.079R, t -5.28; up +0.090 / flat -0.119 / down -0.219 | rvol+inplay / S: n 5837 (13.7/day), win 0.393, -0.005R, t -0.1; up +0.138 / down -0.115; ex-best-day -0.037; busiest day 2% |
| R01-orb30 | long | 1/64 | t1s1: n 197074 (463/day), win 0.49, -0.080R, t -5.45; up +0.128 / flat -0.172 / down -0.318 | rvol+inplay / S: n 8144 (19.1/day), win 0.247, +0.001R, t 0.01; up +0.186 / down -0.243; ex-best-day -0.092; busiest day 4% |
| R07-hod-break | long | 1/64 | S: n 111182 (261/day), win 0.376, -0.099R, t -5.02; up +0.061 / flat -0.181 / down -0.308 | rvol+inplay / S: n 11412 (26.8/day), win 0.415, +0.001R, t 0.01; up +0.161 / down -0.213; ex-best-day -0.084; busiest day 4% |
| R06-red-green | long | 1/64 | t1s1: n 35803 (84/day), win 0.486, -0.074R, t -3.25; up +0.102 / flat -0.159 / down -0.310 | spy+inplay / t1s1: n 6165 (14.5/day), win 0.518, +0.004R, t 0.07; up +0.147 / down -0.329; ex-best-day -0.057; busiest day 10% |
| R13-macd-zero | short | 1/64 | S: n 250257 (587/day), win 0.336, -0.083R, t -5.65; up -0.230 / flat -0.129 / down +0.096 | rvol+inplay / S: n 5226 (12.3/day), win 0.383, +0.005R, t 0.17; up -0.061 / down +0.074; ex-best-day -0.012; busiest day 1% |
| R04-gap-go | short | 3/64 | t1s1: n 12059 (28/day), win 0.517, -0.010R, t -0.22; up -0.310 / flat -0.064 / down +0.186 | rvol / t1s1: n 3895 (9.1/day), win 0.52, +0.010R, t 0.23; up -0.244 / down +0.213; ex-best-day -0.015; busiest day 4% |
| R05-gap-fill | short | 7/64 | S: n 12566 (29/day), win 0.438, +0.024R, t 0.3; up -0.270 / flat -0.058 / down +0.333 | - / S: n 12566 (29.5/day), win 0.438, +0.024R, t 0.3; up -0.270 / down +0.333; ex-best-day -0.048; busiest day 3% |
| R03-vwap-fade | long | 5/64 | S: n 2390 (6/day), win 0.329, -0.074R, t -1.02; up +0.003 / flat +0.256 / down -0.283 | trend+inplay / S: n 151 (0.4/day), win 0.311, +0.054R, t 0.31; up -0.064 / down +0.056; ex-best-day -0.003; busiest day 7% |
| R09-ema20-pullback | long | 1/64 | t1s1: n 293632 (689/day), win 0.48, -0.088R, t -7.22; up +0.111 / flat -0.117 / down -0.293 | rvol+inplay / S: n 4973 (11.7/day), win 0.281, +0.078R, t 0.5; up +0.330 / down -0.150; ex-best-day -0.085; busiest day 4% |
| R05-gap-fill | long | 24/64 | S: n 11831 (28/day), win 0.431, +0.010R, t 0.13; up +0.387 / flat -0.136 / down -0.367 | vwap+spy / S: n 6377 (15.0/day), win 0.444, +0.059R, t 0.54; up +0.437 / down -0.515; ex-best-day -0.023; busiest day 5% |
| R15-sweep | short | 3/64 | S: n 55503 (130/day), win 0.287, -0.106R, t -4.68; up -0.286 / flat -0.067 / down +0.159 | trend+inplay / S: n 1638 (3.8/day), win 0.313, +0.195R, t 0.87; up +0.271 / down +0.252; ex-best-day -0.078; busiest day 21% |
| R19-orb-fib | long | 3/64 | t1s1: n 100552 (236/day), win 0.489, -0.081R, t -5.14; up +0.154 / flat -0.099 / down -0.322 | vwap+inplay / t1s1: n 1327 (3.1/day), win 0.561, +0.072R, t 1.37; up +0.170 / down -0.122; ex-best-day +0.025; busiest day 25% |
| R03-vwap-fade | short | 6/64 | S: n 2602 (6/day), win 0.349, +0.022R, t 0.11; up +0.030 / flat +0.018 / down -0.010 | trend+inplay / S: n 250 (0.6/day), win 0.436, +0.573R, t 2.08; up +0.881 / down -0.548; ex-best-day -0.170; busiest day 64% |

### 2.3 Best few (amendment A; full gates, N = 2,551, t_required 3.96)
| config | n | /day | win | exp R | t | up (n) | flat (n) | down (n) | WF share (folds) | ex-best-day | busiest day | plateau mean (min) | time-matched baseline | am / mid / pm exp | verdict | module |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R04-gap-go / short / rvol / t1s1 | 3895 | 9.14 | 0.5204 | +0.0095 | 0.23 | -0.244 (1031) | -0.082 (1089) | +0.213 (1775) | 0.529 (17) | -0.0154 | 4% | +0.0138 (-0.0174) | -0.0740 | +0.005 / +0.059 / -0.035 | rework (fails: t 0.23 < 3.961; regime (up and down must both be > 0); walk-forward share 0.529 < 0.6) | RD1 |
| R05-gap-fill / short / rvol+trend / t05s1 | 380 | 0.89 | 0.6526 | +0.0063 | 0.2 | -0.035 (95) | +0.012 (134) | +0.027 (151) | 0.429 (14) | -0.0013 | 4% | -0.0409 (-0.0764) | -0.0676 | +0.237 / +0.006 / -0.011 | rework (fails: t 0.2 < 3.961; regime (up and down must both be > 0); walk-forward share 0.429 < 0.6) | RD2 |
| R03-vwap-fade / long / trend+inplay / t1s1 | 151 | 0.35 | 0.543 | +0.0026 | 0.03 | -0.030 (49) | -0.086 (42) | +0.091 (60) | 0.5 (4) | -0.0172 | 7% | -0.0401 (-0.1089) | -0.0887 | -0.013 / +0.079 / +0.066 | rework (fails: t 0.03 < 3.961; regime (up and down must both be > 0); walk-forward share 0.5 < 0.6) | RD3 |
| R19-orb-fib / long / vwap+inplay / t1s1 | 1327 | 3.12 | 0.5607 | +0.0722 | 1.37 | +0.170 (809) | -0.029 (235) | -0.122 (283) | 0.375 (16) | +0.0247 | 25% | +0.0927 (-0.0246) | -0.0869 | +0.009 / +0.225 / +0.074 | rework (fails: t 1.37 < 3.961; regime (up and down must both be > 0); walk-forward share 0.375 < 0.6) | - |

Neighbours (plateau and each filter removed):
- R04-gap-go / short / rvol / t1s1: p=1.0 n 7678 -0.0174; p=3.0 n 2293 +0.0448; rvol=1.25 n 5383 -0.0043; rvol=2.0 n 1894 +0.0321; drop rvol n 12059 -0.0103
- R05-gap-fill / short / rvol+trend / t05s1: p=1.0 n 905 -0.0764; p=3.0 n 194 -0.0312; rvol=1.25 n 567 -0.0222; rvol=2.0 n 199 -0.0337; drop rvol n 1775 -0.0457; drop trend n 1611 -0.0256
- R03-vwap-fade / long / trend+inplay / t1s1: p=0.75 n 363 +0.0050; p=1.25 n 72 -0.1089; inplay=1.5 n 171 -0.0536; inplay=3.0 n 121 -0.0028; drop trend n 2039 -0.0778; drop inplay n 204 -0.0726
- R19-orb-fib / long / vwap+inplay / t1s1: p=0.382 n 6751 -0.0246; p=0.618 n 463 +0.2379; inplay=1.5 n 2266 +0.0181; inplay=3.0 n 627 +0.1396; drop vwap n 4887 -0.0040; drop inplay n 25538 -0.0817

R19 (ORB + Fib, the most-upvoted concrete ORB rule) is the only one with a hint: +0.072R, ex-best-day +0.025, deeper
retracement neighbour p = 0.618 +0.238R (n 463), and the mid window +0.225R (n 341) - but 25% of its trades fall on
one session, down sessions are -0.122R, walk-forward 0.375. It is a long-only, up-market trade; logged as a rework
idea (a regime gate known at entry), not a candidate.

### 2.4 Overlap with past results (consistent)
- ORB (R01/R18/R19): consistent with t2-orb15 / orb5 / t1-orb-exits failing and the stack1009 `or` family being
  negative at stage 1 in every window; Reddit's "ORB + FVG" model is NQ/ES futures on 1-min, which our 5-min stock
  universe cannot reproduce; the stock version is -0.06R (long) / -0.08R (short).
- MA cross, MACD, RSI levels, divergence (R10-R13, R20): consistent with [ART] emax/macdx/rsix/obvdiv (all negative
  on train and valid) and stack1009 stage 1.
- VWAP reclaim / fade (R02/R03): consistent with [ART] vwapx, bdi-vid-envelopes, stack1009 band10 (windowed
  stage 1 negative); the stack1009 survivors needed a large-move layer (|fromOpen| > 3%) and still fail the locked
  block except ST3/ST5.
- RS vs SPY (R16): consistent with t4-rel-strength (failed).
- Gap fade (R05): the short side's down-session strength (+0.333 S) matches the L3 gap shorts (probation) and
  their regime dependence noted in rule 19.

### 2.5 Files
- Mining: `mine.py`, `report_mining.py`, `mining_summary.json`, `show.py` (prints a post's text from the dump).
- Test: `prep_extra.py`, `engine.py`, `strategies.py`, `scan.py` (-> data/scan.csv, counts.json, finalists.json
  = empty: no cheap passer), `best_few.py` (-> best_few.json), `report.py` (-> results.csv), `verify.py`
  (-> verify.json: RD1-RD3 identical trades to the scan, 300/300 single-symbol-day live-shape checks each).
- Modules (best few, all FAIL the bar): `modules/RD1-gapgo-lodbreak-rvol-short-FD.py`,
  `modules/RD2-gapfill-openloss-rvol-slope-short-FD.py`, `modules/RD3-vwapfade-band1-slope-inplay-long-FD.py`;
  staged disabled in `account_testing_reddit.yaml` (config/* untouched).
- Backlog: 20 entries `bdi-rdt-r01-orb30` .. `bdi-rdt-r20-sma-macd` (status failed; those testing an earlier
  `bdi-reddit-*` / `wi-*` idea carry it as `parent`; RD1-RD3 carry `lab_module`).
