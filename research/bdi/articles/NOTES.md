# BDI - article indicators and setups (2026-10-08)

*Educational only - not financial advice.*

## 0. Pre-declared grid (written BEFORE any feature was computed or scored)

Data: setup-lab frame `research/setups2/data/{train,valid}.parquet` (train 2026-06-30..08-25, 40 sessions;
valid 2026-08-26..09-15, 14 sessions) + new indicator columns built from `data/cache/1Min` resampled to 5 minutes,
read with a parquet filter `timestamp < 2026-09-16` (no later rows are loaded). `data/cache_q2` is not touched.
Live parity: every new indicator for day D is computed on (last 40 five-minute bars before D) + D's bars, exactly the
history `LabStrategy` sees (`prior5` = 40 bars), so warm-up limits seen in research are the ones live trading will see.

Scoring (as research/owner1008/scan_fast.py): first qualifying bar per symbol-day, entry at that bar's close,
outcomes r_{side}_{t1s1,t05s1,t1s05} (R = 0.25 x daily ATR, exits by 15:55), minus production haircut
(2 x 1 bps x price + 2c) / R. Day-clustered t. Windows: am 09:50-11:30, pm 11:30-15:00, all 09:50-15:00.

### Triggers (article side; 17 long + 17 short mirrors = 34)
| tag | long | short |
|---|---|---|
| macdx | MACD(12,26,9) line crosses above signal | crosses below |
| bbtouch | bar low <= lower Bollinger(20,2) | bar high >= upper band |
| squeeze | prior-bar BB width in lowest 20% of its last 60 bars and close > upper band | close < lower band |
| stochx | slow Stoch(14,3,3) %K crosses above %D with prior %K < 20 | %K crosses below %D with prior %K > 80 |
| dmix | ADX(14) >= 25 and +DI crosses above -DI | -DI crosses above +DI |
| obvdiv | low at 20-bar low while OBV is not at its 20-bar low (bullish divergence) | mirror at highs |
| emax | EMA9 crosses above EMA21 | below |
| smax | 5-min SMA20 crosses above SMA50 | below |
| rsix | RSI(14) crosses back above 30 | crosses back below 70 |
| vwapx | close crosses above VWAP | below |
| pivx | close crosses above classic pivot P (prior-day H/L/C) | below |
| s1bounce / r1reject | low <= S1 and close > S1 | high >= R1 and close < R1 |
| r1break / s1break | close crosses above R1 | close crosses below S1 |
| fib618 | up-leg today (HOD after LOD): low <= HOD - 0.618 x (HOD-LOD) and close above that level | mirror on a down-leg |
| aroonx | Aroon(25) up crosses above down | down above up |
| ichix | close crosses above the Ichimoku(9,26,52) cloud with Tenkan > Kijun | below cloud, Tenkan < Kijun |
| tkx | Tenkan crosses above Kijun | below |

### Families
- **F (faithful):** each trigger alone: 34 x 3 windows x 3 geoms = **306**.
- **C (contrarian):** each trigger alone, traded on the opposite side: **306**.
- **L1:** trigger + 1 filter (12 filters) = 34 x 12 x 9 = **3,672**.
- **L2:** trigger + 2 filters (66 pairs minus 2 contradictory = 64) = 34 x 64 x 9 = **19,584**.
- Total declared: **23,868** configurations. Configs with train n < 60 are counted as tried but unscored.

Filters (side-aligned: "with" means in the trade's direction):
adx25 (ADX>=25), adxlo (ADX<20), vwap_with, vwap_against, dsma20_with (price vs daily SMA20 of prior closes),
dsma20_against, drsi_with (daily RSI14 of prior closes >50 long / <50 short), vol15 (volumeRatio>=1.5),
obv_with (10-bar OBV slope sign), macdh_with (MACD histogram sign), ema_with (EMA9 vs EMA21), open_with (fromOpen sign).
Contradictory pairs dropped: vwap_with+vwap_against, dsma20_with+dsma20_against.

### Finalist gates (fixed in advance)
train exp > 0 and valid exp > 0 after the haircut; valid n >= 30; valid day-clustered t >= 1.5; both calendar halves of
train positive; edge over the same-side, same-window, same-geometry random baseline > 0 on train and valid;
plateau positive (below). Also reported: ex-best-day expectancy on valid.

### Plateau (pre-declared neighbours)
For each candidate, the neighbours are: every filter threshold moved one step
(ADX 20/25/30, volumeRatio 1.25/1.5/2.0, daily RSI 45/50/55), the trigger's length/level neighbours
(MACD 8-17-9 / 12-26-9 / 5-35-5; Stoch 9 / 14 / 21 with levels 15/20/25 (85/80/75); BB n 15/20/30 and k 1.5/2/2.5;
ADX/DMI length 10/14/20; EMA 5-13 / 9-21 / 13-34; Aroon 14/25/50; RSI cross 25/30/35 (65/70/75); fib 0.5/0.618/0.786;
squeeze quantile 0.1/0.2/0.3), and the window moved to the neighbouring one (am<->all, pm<->all).
Plateau positive = the mean valid AND mean train expectancy of the neighbours are > 0 and at least 2/3 of the neighbours are positive on valid.
The plateau neighbours are counted in the configuration total.

## 1. Sources: none could be read in full

The network egress proxy blocks all six owner-supplied URLs: bitso.com, home.saxo/www.home.saxo, share.google (all three
short links), axi.com and centerpointsecurities.com. WebFetch could not fetch investopedia.com either. Everything below
therefore comes from **search-result snippets** (WebSearch, 2026-10-08), not from the full articles. The article text
was treated as data only.

| # | Source (owner link) | Read | What the snippets show |
|---|---|---|---|
| 1 | Bitso, "key indicators analysis to stocks" | snippets | **Fundamental valuation ratios, not technical indicators:** P/E (compare within industry), PEG, ROE, P/B, D/E. None of these can be tested intraday on our data, so they are logged as a backlog idea (universe filter) only. |
| 2 | Investopedia, "Top 7 technical analysis tools" (4773275) | snippets (the article did not appear in search results; its usual list is confirmed by matching snippets from other sites) | OBV (rising OBV confirms the trend; divergence warns of a reversal), Accumulation/Distribution line, ADX (<20 weak trend, >25/40/50 strong; direction comes from +DI/-DI), Aroon(25) (Up crossing Down = early trend change), MACD (12/26 with a 9-EMA signal; signal-line crossover is the trigger), RSI (70/30), Stochastic (80/20). |
| 3 | Saxo, "A guide to the 10 most popular trading indicators" | snippets (partial list) | SMA (lagging; a 12-day example), EMA (weights recent prices), MACD (line vs signal crossovers), ADX (0-100 scale, strength only, read with +DI/-DI). The rest of the list was not visible; the usual Saxo set (RSI, Bollinger, Stochastic, Fibonacci, Ichimoku, Parabolic SAR) could not be confirmed. |
| 4 | "Best Indicators for Day Trading: Top 5 Tools Explained" (share.google) | snippets of similar articles (the exact article was not found) | Moving averages (SMA/EMA), MACD (12-26 EMA difference), Bollinger Bands (an upper-band touch reads as overbought), RSI, Stochastic, volume, OBV, SuperTrend, Ease of Movement. |
| 5 | "Best Technical Indicators for Day Trading (4 Best Indicators)" (share.google) | snippets (likely CenterPoint Securities or Optimus Futures; the four indicators themselves were not visible) | VWAP (the most-used intraday indicator; price reverts toward it), volume (confirms a move: rising volume in an uptrend), SMA/EMA, Bollinger (standard deviations around the SMA), MACD, Ichimoku cloud (support/resistance, momentum and trend in one view). |
| 6 | Axi UK, "Best Trading Indicators / 17 most used technical indicators" (share.google) | snippets (opening sections only) | MA (short-term MA crossing above long-term MA = possible uptrend), EMA, MACD (lagging). Also from a CMC Markets UK snippet that surfaced alongside it: ADX (strength without direction), Parabolic SAR, RSI and Stochastic (0-100 bounds). |
| + | Indicators named in the owner's brief | - | EMA 9/21 and 20/50 crosses, RSI 30/70, Bollinger squeeze/touch, Stochastic %K/%D at 20/80, ADX > 25, OBV divergence, VWAP, ATR, Fibonacci, Ichimoku, volume profile, pivot points, daily SMA20/50, daily RSI14. |

### Indicators and rules extracted (default settings used)
- **MACD(12,26,9):** the line crossing the signal line (long above, short below). Histogram sign used as a filter.
- **Bollinger(20,2):** band touch (lower = buy / upper = overbought), squeeze (low band width) then breakout, %B, band width.
- **Stochastic(14,3,3):** %K crossing %D below 20 (buy) or above 80 (sell).
- **ADX/DMI(14):** ADX > 25 marks a trend and < 20 a weak one; +DI/-DI crosses give the direction.
- **OBV:** slope confirming the move; divergence (price at a new extreme that OBV does not confirm).
- **A/D line (Chaikin):** column built (ad_slope) but not in the declared grid. Backlog.
- **Aroon(25):** Up/Down cross.
- **Moving averages:** EMA 9/21 cross; 5-minute SMA20/50 cross; daily SMA20 trend filter. Daily SMA50 (golden/death cross) cannot be tested: the cache starts 2026-06-15, so daily SMA50 is undefined on every train date and on most valid dates.
- **RSI(14):** a cross back above 30 (buy) or back below 70 (sell). **Daily RSI14** (Wilder, prior closes) used as a filter.
- **VWAP:** cross above/below.
- **Pivot points (classic, prior day):** P cross, S1 bounce / R1 rejection, R1/S1 breakout.
- **Fibonacci:** the 61.8% retracement of today's leg (HOD/LOD so far).
- **Ichimoku(9,26,52):** a break of the cloud with Tenkan>Kijun, and the TK cross.
- **ATR:** already the R unit (0.25 x daily ATR); not a trigger.
- **Volume:** volumeRatio >= 1.5 filter (already in the frame).
- Not testable here or not built: Parabolic SAR, SuperTrend, Ease of Movement, volume profile, P/E-type ratios. These are in the backlog.

## 2. What was built (step 2)
- `features.py::article_features(hist, prev_hlc, daily_closes)` is causal and computed on 5-minute bars. It produces 52 columns plus 26 `*_prev` twins (listed in its docstring):
  - MACD histogram (3 settings), Bollinger z for close/low/high (n 15/20/30), band width and its 60-bar percentile;
  - slow Stochastic %K/%D (9/14/21), ADX and +DI-DI (10/14/20, Wilder), OBV and A/D slopes, OBV divergence flags;
  - EMA 5/13, 9/21 and 13/34 spreads, the SMA20/50 spread, RSI14, VWAP distance;
  - Aroon 14/25/50, Ichimoku Tenkan-Kijun and cloud, classic pivots P/R1/S1, today's HOD/LOD/up-leg;
  - daily SMA20/SMA50 and daily Wilder RSI14 from prior closes.
- `build.py` runs it for all 1,225 symbols x 54 sessions with **live-parity history**: each day gets its prior 40 five-minute bars plus the day's own bars.
  - Output: `data/feat.parquet` (4,155,564 rows, exactly the frame's rows; git-ignored).
  - Sanity check: rsi14, vwapd and close equal the frame's rsi, vwapDistPct and close (correlation 1.000, max |diff| 0).
- Coverage (share of non-null rows), train / valid:
  - MACD, ADX, pivots: 100% / 100%.
  - Bollinger squeeze percentile: 92% / 92% (none before about 10:15).
  - **Ichimoku cloud: 46% / 46%.** It needs 78 bars, so it exists only after about 12:40. This makes the "all" and "pm" Ichimoku results identical.
  - Daily SMA20: 75% / 100%. Daily RSI14: 88% / 100%.
  - **Daily SMA50: 0% / 99.9%.** Untestable on train, so it was left out of the grid (backlog).
- Cross-check: `scan.py` reproduces `research/owner1008/scan.csv` on the shared VWAP-cross rule. For example, long t1s1 is -0.165R (n 42,976) here vs -0.164R (n 42,120) there. The n gap is the 09:50 crosses, which this run includes using the 09:45 bar, as live trading would.

## 3. Counts
- Declared configurations: **23,868** (F 306, C 306, L1 3,672, L2 19,584).
- Unscored because train n < 60: 1,305 (still counted as tried).
- Scored: 22,563.
- Plateau neighbours evaluated: 0, because no configuration reached the plateau step.
- **Total tried: 23,868.** At p = 0.05 we would expect about 1,190 false positives by chance; we got 1 configuration positive on both splits.

## 4. Results: failures first

**Verdict: 0 finalists. Every article rule fails as written, and so do all layered combinations.**

Gate-by-gate (number of the 22,563 scored configurations passing each gate on its own):
- train exp > 0: 38
- valid exp > 0: 183
- valid n >= 30: 22,488
- valid day-t >= 1.5: 8
- train half 1 > 0: 769; train half 2 > 0: 64
- edge over baseline on train: 8,503; on valid: 6,692

Jointly, only 1 configuration is positive on both splits with valid n >= 30, and it fails the t gate and the halves gate.

How the gates combine:
- Positive on both splits with valid n >= 30: 1 configuration (EMA9/21 cross short, below VWAP, below daily SMA20, 09:50-11:30, t1s1).
  - Train: +0.007R, t 0.09, n 390, half 2 negative.
  - Valid: +0.056R, t 0.36, n 158, ex-best-day -0.053R.
- None reaches valid t >= 1.5 while positive on train.

Why everything fails:
- The production haircut (median 0.051R, mean 0.072R per trade) is part of it.
- The bigger part is that the random same-window baseline is already deeply negative after costs: long -0.12 to -0.19R, short -0.09 to -0.11R per trade.
- Most article rules beat that baseline only marginally, or not at all. The long side is consistently worse than the short side in this window.

### Per family
| family | scored | train>0 | valid>0 | both>0 (any n) | edge>0 on both | best tr_exp | best va_exp |
|---|---|---|---|---|---|---|---|
| F (faithful) | 300 | 0 | 0 | 0 | 19 | -0.053 | -0.043 |
| C (contrarian) | 300 | 0 | 0 | 0 | 95 | -0.054 | -0.013 |
| L1 | 3,558 | 3 | 13 | 0 | 300 | 0.131 | 0.105 |
| L2 | 18,405 | 35 | 170 | 3 | 1,867 | 0.191 | 0.242 |

Notable patterns (not edges):
- **Contrarian beats faithful on the short side.** Fading long-side triggers (short after an Ichimoku cloud break up, a squeeze break up, an SMA20/50 golden cross, a TK cross, or a DMI cross up) is the least-bad family on valid: -0.01 to -0.04R at t1s1. This matches MCF's earlier finding that 5-minute up-signals tend to fail.
- **The best train results all come from the Bollinger squeeze, short, with volume >= 1.5x, 09:50-11:30.** Train is up to +0.19R, n 68-96, but driven by train half 1. All of these are negative on valid (n 24-28).
- **The best valid results come from Ichimoku cloud-break shorts below VWAP (afternoon).** Valid is +0.08 to +0.09R with t 2.3-2.5, but train is -0.15R. This is a regime flip, not an edge.
- **The largest edge over the random baseline on both splits:** SMA20/50 cross long, below daily SMA20, with daily RSI > 50 (AM, t05s1), at +0.13 / +0.10R over baseline. Its absolute expectancy is still negative (-0.02 / -0.05R).

The full tables follow: faithful and contrarian by trigger, every train-positive config, the top valid configs, the top edges over baseline, and the baselines. Every row is in results.csv.

### Faithful (article side), window 09:50-15:00: expectancy (R/trade after haircut) by geometry
| trigger | side | tr_exp_t05s1 | tr_exp_t1s05 | tr_exp_t1s1 | va_exp_t05s1 | va_exp_t1s05 | va_exp_t1s1 | tr_n | va_n |
|---|---|---|---|---|---|---|---|---|---|
| aroonx | long | -0.120 | -0.109 | -0.121 | -0.192 | -0.191 | -0.229 | 42194 | 15246 |
| aroonx | short | -0.091 | -0.085 | -0.076 | -0.110 | -0.112 | -0.093 | 42998 | 15185 |
| bbtouch | long | -0.161 | -0.138 | -0.169 | -0.142 | -0.158 | -0.146 | 44246 | 15646 |
| bbtouch | short | -0.139 | -0.114 | -0.110 | -0.093 | -0.087 | -0.050 | 44649 | 15008 |
| dmix | long | -0.119 | -0.109 | -0.113 | -0.198 | -0.199 | -0.239 | 18831 | 6760 |
| dmix | short | -0.102 | -0.097 | -0.085 | -0.117 | -0.128 | -0.102 | 19657 | 6462 |
| emax | long | -0.123 | -0.119 | -0.124 | -0.187 | -0.182 | -0.213 | 37076 | 13117 |
| emax | short | -0.092 | -0.085 | -0.078 | -0.132 | -0.137 | -0.123 | 38012 | 13140 |
| fib | long | -0.183 | -0.167 | -0.192 | -0.196 | -0.202 | -0.220 | 16938 | 5666 |
| fib | short | -0.123 | -0.101 | -0.085 | -0.121 | -0.122 | -0.100 | 19520 | 7367 |
| ichix | long | -0.146 | -0.139 | -0.146 | -0.217 | -0.219 | -0.249 | 9681 | 3197 |
| ichix | short | -0.105 | -0.092 | -0.097 | -0.113 | -0.109 | -0.083 | 9743 | 3389 |
| macdx | long | -0.126 | -0.110 | -0.116 | -0.168 | -0.152 | -0.185 | 47113 | 16700 |
| macdx | short | -0.103 | -0.089 | -0.081 | -0.118 | -0.120 | -0.097 | 47775 | 16661 |
| obvdiv | long | -0.162 | -0.152 | -0.169 | -0.143 | -0.142 | -0.148 | 41428 | 14757 |
| obvdiv | short | -0.141 | -0.121 | -0.126 | -0.093 | -0.091 | -0.056 | 41478 | 13846 |
| pivx | long | -0.155 | -0.133 | -0.161 | -0.192 | -0.175 | -0.201 | 16555 | 6236 |
| pivx | short | -0.088 | -0.081 | -0.062 | -0.145 | -0.148 | -0.138 | 16933 | 6324 |
| r1s1break | long | -0.152 | -0.135 | -0.154 | -0.226 | -0.183 | -0.234 | 13933 | 4063 |
| r1s1break | short | -0.096 | -0.095 | -0.081 | -0.155 | -0.160 | -0.150 | 13077 | 5569 |
| rsix | long | -0.150 | -0.129 | -0.143 | -0.163 | -0.156 | -0.175 | 40082 | 14548 |
| rsix | short | -0.123 | -0.104 | -0.100 | -0.112 | -0.102 | -0.080 | 40826 | 13464 |
| s1r1hold | long | -0.157 | -0.144 | -0.168 | -0.173 | -0.166 | -0.195 | 13791 | 5787 |
| s1r1hold | short | -0.112 | -0.092 | -0.082 | -0.098 | -0.087 | -0.062 | 14912 | 4457 |
| smax | long | -0.133 | -0.121 | -0.138 | -0.199 | -0.197 | -0.234 | 24315 | 9023 |
| smax | short | -0.112 | -0.103 | -0.111 | -0.162 | -0.157 | -0.162 | 25624 | 8299 |
| squeeze | long | -0.139 | -0.135 | -0.139 | -0.199 | -0.207 | -0.227 | 19854 | 6765 |
| squeeze | short | -0.109 | -0.103 | -0.100 | -0.125 | -0.139 | -0.121 | 20387 | 7603 |
| stochx | long | -0.163 | -0.147 | -0.168 | -0.141 | -0.138 | -0.141 | 45765 | 16389 |
| stochx | short | -0.132 | -0.114 | -0.112 | -0.117 | -0.110 | -0.084 | 46139 | 15812 |
| tkx | long | -0.139 | -0.117 | -0.137 | -0.199 | -0.199 | -0.236 | 45392 | 15897 |
| tkx | short | -0.091 | -0.083 | -0.075 | -0.125 | -0.125 | -0.125 | 45334 | 15944 |
| vwapx | long | -0.162 | -0.137 | -0.165 | -0.190 | -0.178 | -0.203 | 42976 | 15383 |
| vwapx | short | -0.093 | -0.085 | -0.058 | -0.155 | -0.152 | -0.141 | 43110 | 15366 |

### Contrarian (opposite side), window 09:50-15:00: expectancy (R/trade after haircut) by geometry
| trigger | side | tr_exp_t05s1 | tr_exp_t1s05 | tr_exp_t1s1 | va_exp_t05s1 | va_exp_t1s05 | va_exp_t1s1 | tr_n | va_n |
|---|---|---|---|---|---|---|---|---|---|
| aroonx | long | -0.148 | -0.143 | -0.157 | -0.168 | -0.170 | -0.186 | 42998 | 15185 |
| aroonx | short | -0.124 | -0.113 | -0.112 | -0.087 | -0.087 | -0.050 | 42194 | 15246 |
| bbtouch | long | -0.123 | -0.098 | -0.126 | -0.196 | -0.191 | -0.233 | 44649 | 15008 |
| bbtouch | short | -0.097 | -0.075 | -0.066 | -0.125 | -0.140 | -0.136 | 44246 | 15646 |
| dmix | long | -0.146 | -0.141 | -0.158 | -0.166 | -0.177 | -0.192 | 19657 | 6462 |
| dmix | short | -0.131 | -0.121 | -0.128 | -0.083 | -0.085 | -0.043 | 18831 | 6760 |
| emax | long | -0.150 | -0.143 | -0.157 | -0.146 | -0.151 | -0.160 | 38012 | 13140 |
| emax | short | -0.116 | -0.113 | -0.112 | -0.095 | -0.090 | -0.064 | 37076 | 13117 |
| fib | long | -0.143 | -0.121 | -0.158 | -0.181 | -0.182 | -0.200 | 19520 | 7367 |
| fib | short | -0.088 | -0.071 | -0.062 | -0.100 | -0.105 | -0.079 | 16938 | 5666 |
| ichix | long | -0.145 | -0.133 | -0.141 | -0.176 | -0.173 | -0.203 | 9743 | 3389 |
| ichix | short | -0.105 | -0.098 | -0.097 | -0.055 | -0.057 | -0.024 | 9681 | 3197 |
| macdx | long | -0.147 | -0.133 | -0.154 | -0.162 | -0.163 | -0.184 | 47775 | 16661 |
| macdx | short | -0.127 | -0.110 | -0.120 | -0.129 | -0.112 | -0.095 | 47113 | 16700 |
| obvdiv | long | -0.116 | -0.096 | -0.111 | -0.194 | -0.192 | -0.229 | 41478 | 13846 |
| obvdiv | short | -0.087 | -0.077 | -0.070 | -0.143 | -0.143 | -0.137 | 41428 | 14757 |
| pivx | long | -0.150 | -0.143 | -0.169 | -0.127 | -0.128 | -0.134 | 16933 | 6324 |
| pivx | short | -0.097 | -0.075 | -0.070 | -0.098 | -0.081 | -0.071 | 16555 | 6236 |
| r1s1break | long | -0.139 | -0.137 | -0.152 | -0.124 | -0.128 | -0.133 | 13077 | 5569 |
| r1s1break | short | -0.106 | -0.089 | -0.086 | -0.103 | -0.060 | -0.051 | 13933 | 4063 |
| rsix | long | -0.133 | -0.115 | -0.137 | -0.179 | -0.170 | -0.201 | 40826 | 13464 |
| rsix | short | -0.108 | -0.086 | -0.093 | -0.127 | -0.120 | -0.107 | 40082 | 14548 |
| s1r1hold | long | -0.150 | -0.129 | -0.159 | -0.199 | -0.188 | -0.223 | 14912 | 4457 |
| s1r1hold | short | -0.094 | -0.081 | -0.070 | -0.112 | -0.105 | -0.082 | 13791 | 5787 |
| smax | long | -0.136 | -0.127 | -0.128 | -0.131 | -0.125 | -0.125 | 25624 | 8299 |
| smax | short | -0.109 | -0.097 | -0.092 | -0.078 | -0.076 | -0.040 | 24315 | 9023 |
| squeeze | long | -0.128 | -0.122 | -0.131 | -0.141 | -0.157 | -0.161 | 20387 | 7603 |
| squeeze | short | -0.105 | -0.102 | -0.101 | -0.063 | -0.071 | -0.043 | 19854 | 6765 |
| stochx | long | -0.122 | -0.104 | -0.123 | -0.170 | -0.164 | -0.197 | 46139 | 15812 |
| stochx | short | -0.089 | -0.073 | -0.068 | -0.143 | -0.141 | -0.139 | 45765 | 16389 |
| tkx | long | -0.151 | -0.143 | -0.159 | -0.155 | -0.155 | -0.154 | 45334 | 15944 |
| tkx | short | -0.117 | -0.096 | -0.097 | -0.080 | -0.080 | -0.043 | 45392 | 15897 |
| vwapx | long | -0.153 | -0.144 | -0.179 | -0.134 | -0.131 | -0.144 | 43110 | 15366 |
| vwapx | short | -0.100 | -0.075 | -0.071 | -0.106 | -0.094 | -0.080 | 42976 | 15383 |

### Every configuration positive on train (all 38)
| family | trigger | side | filters | window | geom | tr_n | tr_exp | tr_t | tr_h1 | tr_h2 | va_n | va_exp | va_t | va_exbest | tr_edge | va_edge |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2 | squeeze | short | vol15+obv_with | am | t1s1 | 87 | 0.179 | 1.609 | 0.355 | -0.039 | 28 | -0.137 | -0.857 | -0.257 | 0.269 | -0.015 |
| L2 | squeeze | short | vol15+macdh_with | am | t1s1 | 68 | 0.191 | 1.555 | 0.363 | -0.086 | 24 | -0.054 | -0.301 | -0.185 | 0.281 | 0.068 |
| L2 | squeeze | short | vol15+obv_with | am | t05s1 | 87 | 0.091 | 1.309 | 0.164 | 0.001 | 28 | -0.220 | -1.875 | -0.290 | 0.202 | -0.075 |
| L2 | squeeze | short | vol15+macdh_with | am | t05s1 | 68 | 0.089 | 1.255 | 0.146 | -0.002 | 24 | -0.192 | -1.495 | -0.271 | 0.200 | -0.047 |
| L1 | squeeze | short | vol15 | am | t1s1 | 96 | 0.131 | 1.176 | 0.292 | -0.086 | 28 | -0.137 | -0.857 | -0.257 | 0.221 | -0.015 |
| L2 | squeeze | short | vwap_with+vol15 | am | t1s1 | 96 | 0.131 | 1.176 | 0.292 | -0.086 | 28 | -0.137 | -0.857 | -0.257 | 0.221 | -0.015 |
| L2 | squeeze | short | vol15+ema_with | am | t05s1 | 70 | 0.089 | 1.078 | 0.172 | -0.030 | 27 | -0.243 | -2.100 | -0.319 | 0.199 | -0.098 |
| L1 | squeeze | short | vol15 | am | t05s1 | 96 | 0.072 | 1.009 | 0.151 | -0.034 | 28 | -0.220 | -1.875 | -0.290 | 0.182 | -0.075 |
| L2 | squeeze | short | vwap_with+vol15 | am | t05s1 | 96 | 0.072 | 1.009 | 0.151 | -0.034 | 28 | -0.220 | -1.875 | -0.290 | 0.182 | -0.075 |
| L2 | squeeze | short | vol15+macdh_with | am | t1s05 | 68 | 0.107 | 0.935 | 0.165 | 0.013 | 24 | 0.036 | 0.263 | -0.082 | 0.199 | 0.164 |
| L2 | aroonx | short | adxlo+vwap_against | am | t1s1 | 129 | 0.059 | 0.906 | 0.024 | 0.095 | 54 | -0.035 | -0.198 | -0.157 | 0.149 | 0.087 |
| L2 | squeeze | short | adx25+vol15 | am | t1s1 | 64 | 0.131 | 0.871 | 0.192 | 0.053 | 17 | -0.163 | -0.758 | -0.311 | 0.221 | -0.041 |
| L2 | squeeze | short | vol15+ema_with | am | t1s1 | 70 | 0.121 | 0.870 | 0.292 | -0.120 | 27 | -0.176 | -1.068 | -0.306 | 0.211 | -0.054 |
| L2 | squeeze | short | vol15+obv_with | am | t1s05 | 87 | 0.083 | 0.864 | 0.153 | -0.004 | 28 | -0.007 | -0.054 | -0.111 | 0.175 | 0.121 |
| L2 | aroonx | long | vwap_against+dsma20_against | am | t1s1 | 231 | 0.109 | 0.800 | -0.301 | 0.256 | 144 | -0.291 | -3.311 | -0.332 | 0.255 | -0.133 |
| L2 | stochx | short | macdh_with+ema_with | am | t1s1 | 162 | 0.047 | 0.653 | 0.230 | -0.115 | 67 | -0.259 | -1.669 | -0.301 | 0.137 | -0.137 |
| L2 | squeeze | short | vol15+open_with | am | t1s1 | 73 | 0.089 | 0.648 | 0.227 | -0.108 | 24 | -0.130 | -0.713 | -0.272 | 0.179 | -0.008 |
| L2 | aroonx | long | adxlo+vwap_against | am | t1s1 | 133 | 0.098 | 0.644 | -0.190 | 0.251 | 42 | -0.285 | -1.292 | -0.375 | 0.244 | -0.127 |
| L2 | s1r1hold | short | adxlo+dsma20_against | am | t1s1 | 735 | 0.030 | 0.589 | 0.069 | 0.010 | 209 | -0.047 | -0.841 | -0.080 | 0.119 | 0.075 |
| L2 | squeeze | short | vwap_with+vol15 | am | t1s05 | 96 | 0.051 | 0.495 | 0.127 | -0.051 | 28 | -0.007 | -0.054 | -0.111 | 0.143 | 0.121 |
| L1 | squeeze | short | vol15 | am | t1s05 | 96 | 0.051 | 0.495 | 0.127 | -0.051 | 28 | -0.007 | -0.054 | -0.111 | 0.143 | 0.121 |
| L2 | squeeze | short | adx25+vol15 | am | t1s05 | 64 | 0.057 | 0.453 | 0.087 | 0.018 | 17 | 0.023 | 0.141 | -0.101 | 0.149 | 0.151 |
| L2 | s1r1hold | long | dsma20_against+ema_with | am | t1s1 | 136 | 0.057 | 0.447 | 0.220 | -0.127 | 113 | -0.275 | -2.278 | -0.322 | 0.203 | -0.117 |
| L2 | bbtouch | short | vwap_with+drsi_with | am | t1s1 | 2888 | 0.025 | 0.396 | 0.059 | -0.010 | 1444 | -0.071 | -1.017 | -0.103 | 0.115 | 0.050 |
| L2 | squeeze | short | vol15+open_with | am | t05s1 | 73 | 0.035 | 0.387 | 0.085 | -0.036 | 24 | -0.247 | -2.106 | -0.334 | 0.146 | -0.102 |
| L2 | aroonx | short | vwap_against+dsma20_against | am | t1s1 | 249 | 0.027 | 0.342 | 0.108 | -0.000 | 83 | -0.072 | -1.081 | -0.121 | 0.117 | 0.050 |
| L2 | squeeze | short | vol15+ema_with | am | t1s05 | 70 | 0.043 | 0.329 | 0.128 | -0.077 | 27 | -0.040 | -0.327 | -0.153 | 0.135 | 0.087 |
| L2 | s1r1hold | short | adxlo+vwap_with | am | t1s1 | 624 | 0.016 | 0.309 | 0.089 | -0.044 | 206 | -0.087 | -1.272 | -0.121 | 0.105 | 0.035 |
| L2 | stochx | long | macdh_with+ema_with | pm | t1s1 | 185 | 0.016 | 0.225 | -0.106 | 0.094 | 68 | -0.143 | -1.238 | -0.181 | 0.145 | 0.063 |
| L2 | dmix | long | vwap_against+dsma20_against | pm | t1s1 | 2181 | 0.017 | 0.167 | 0.010 | 0.023 | 1293 | -0.238 | -6.406 | -0.254 | 0.146 | -0.032 |
| L2 | tkx | short | adxlo+dsma20_against | am | t1s1 | 1795 | 0.007 | 0.160 | 0.071 | -0.021 | 551 | -0.160 | -2.729 | -0.186 | 0.097 | -0.038 |
| L2 | squeeze | short | vol15+open_with | am | t1s05 | 73 | 0.018 | 0.138 | 0.063 | -0.047 | 24 | -0.019 | -0.138 | -0.145 | 0.110 | 0.109 |
| L2 | stochx | long | macdh_with+ema_with | pm | t1s05 | 185 | 0.010 | 0.124 | -0.133 | 0.101 | 68 | -0.116 | -1.091 | -0.168 | 0.132 | 0.067 |
| L2 | smax | long | adx25+vwap_against | pm | t1s1 | 316 | 0.010 | 0.101 | -0.050 | 0.054 | 127 | -0.282 | -3.619 | -0.337 | 0.139 | -0.075 |
| L2 | emax | short | vwap_against+dsma20_against | am | t1s1 | 390 | 0.007 | 0.091 | 0.127 | -0.029 | 158 | 0.056 | 0.357 | -0.053 | 0.097 | 0.178 |
| L2 | s1r1hold | long | dsma20_against+ema_with | am | t05s1 | 136 | 0.006 | 0.066 | 0.110 | -0.110 | 113 | -0.228 | -2.337 | -0.282 | 0.150 | -0.075 |
| L2 | bbtouch | short | vwap_with+dsma20_with | am | t1s1 | 1866 | 0.001 | 0.009 | 0.014 | -0.008 | 1368 | -0.090 | -1.314 | -0.127 | 0.090 | 0.032 |
| L2 | s1r1hold | short | adxlo+open_with | am | t1s1 | 348 | 0.001 | 0.008 | 0.003 | -0.002 | 118 | -0.081 | -0.819 | -0.173 | 0.090 | 0.041 |

### Top 15 positive on valid (by valid day-t)
| family | trigger | side | filters | window | geom | tr_n | tr_exp | tr_t | tr_h1 | tr_h2 | va_n | va_exp | va_t | va_exbest | tr_edge | va_edge |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2 | ichix | short | vwap_against+drsi_with | all | t1s1 | 603 | -0.153 | -1.701 | -0.166 | -0.139 | 313 | 0.082 | 2.533 | 0.070 | -0.052 | 0.171 |
| L2 | ichix | short | vwap_against+drsi_with | pm | t1s1 | 603 | -0.153 | -1.701 | -0.166 | -0.139 | 313 | 0.082 | 2.533 | 0.070 | -0.046 | 0.155 |
| L2 | ichix | short | vwap_against+dsma20_with | pm | t1s1 | 599 | -0.145 | -1.678 | -0.173 | -0.122 | 402 | 0.091 | 2.352 | 0.067 | -0.039 | 0.164 |
| L2 | ichix | short | vwap_against+dsma20_with | all | t1s1 | 599 | -0.145 | -1.678 | -0.173 | -0.122 | 402 | 0.091 | 2.352 | 0.067 | -0.044 | 0.180 |
| L2 | rsix | short | ema_with+open_with | am | t1s1 | 651 | -0.181 | -2.256 | -0.179 | -0.183 | 346 | 0.125 | 1.866 | 0.091 | -0.092 | 0.247 |
| L2 | emax | short | vwap_against+drsi_with | am | t1s1 | 341 | -0.212 | -1.859 | -0.244 | -0.185 | 172 | 0.135 | 1.607 | 0.076 | -0.123 | 0.257 |
| L2 | r1s1break | short | vwap_against+dsma20_against | pm | t1s1 | 619 | -0.070 | -1.508 | 0.043 | -0.111 | 258 | 0.121 | 1.591 | 0.074 | 0.036 | 0.194 |
| L2 | obvdiv | long | vwap_with+macdh_with | am | t1s1 | 92 | -0.203 | -1.845 | -0.164 | -0.249 | 28 | 0.185 | 1.548 | 0.118 | -0.057 | 0.343 |
| L2 | ichix | short | vwap_against+obv_with | pm | t1s1 | 761 | -0.118 | -1.820 | -0.111 | -0.126 | 368 | 0.074 | 1.491 | 0.032 | -0.011 | 0.147 |
| L2 | ichix | short | vwap_against+obv_with | all | t1s1 | 761 | -0.118 | -1.820 | -0.111 | -0.126 | 368 | 0.074 | 1.491 | 0.032 | -0.017 | 0.163 |
| L2 | rsix | short | vwap_against+ema_with | pm | t1s1 | 836 | -0.137 | -1.957 | -0.130 | -0.142 | 433 | 0.120 | 1.476 | 0.070 | -0.030 | 0.193 |
| L2 | squeeze | long | adx25+vol15 | am | t1s1 | 63 | -0.241 | -1.339 | -0.229 | -0.259 | 15 | 0.180 | 1.440 | 0.123 | -0.095 | 0.339 |
| L2 | rsix | short | dsma20_against+ema_with | am | t1s1 | 465 | -0.151 | -1.765 | -0.221 | -0.129 | 242 | 0.160 | 1.378 | 0.070 | -0.061 | 0.282 |
| L2 | ichix | short | vwap_against+ema_with | all | t1s1 | 949 | -0.112 | -1.696 | -0.105 | -0.120 | 474 | 0.056 | 1.306 | 0.035 | -0.011 | 0.145 |
| L2 | ichix | short | vwap_against+ema_with | pm | t1s1 | 949 | -0.112 | -1.696 | -0.105 | -0.120 | 474 | 0.056 | 1.306 | 0.035 | -0.005 | 0.129 |

### Largest edge over the random same-window baseline on both splits (top 15 of 2263), absolute expectancy still negative
| family | trigger | side | filters | window | geom | tr_n | tr_exp | tr_t | tr_h1 | tr_h2 | va_n | va_exp | va_t | va_exbest | tr_edge | va_edge |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L2 | smax | long | dsma20_against+drsi_with | am | t05s1 | 140 | -0.018 | -0.331 | 0.059 | -0.129 | 77 | -0.052 | -0.406 | -0.105 | 0.126 | 0.101 |
| L2 | squeeze | long | vol15+macdh_with | am | t05s1 | 86 | -0.045 | -0.630 | -0.097 | 0.014 | 35 | -0.055 | -0.498 | -0.086 | 0.098 | 0.098 |
| L2 | emax | short | vwap_against+dsma20_against | am | t1s1 | 390 | 0.007 | 0.091 | 0.127 | -0.029 | 158 | 0.056 | 0.357 | -0.053 | 0.097 | 0.178 |
| L2 | aroonx | short | adxlo+vwap_against | am | t1s1 | 129 | 0.059 | 0.906 | 0.024 | 0.095 | 54 | -0.035 | -0.198 | -0.157 | 0.149 | 0.087 |
| L2 | smax | long | dsma20_against+drsi_with | am | t1s1 | 140 | -0.059 | -0.595 | 0.092 | -0.279 | 77 | -0.042 | -0.253 | -0.160 | 0.087 | 0.116 |
| L2 | squeeze | long | vol15+macdh_with | am | t1s1 | 86 | -0.064 | -0.577 | -0.141 | 0.025 | 35 | -0.056 | -0.452 | -0.116 | 0.082 | 0.103 |
| L2 | squeeze | long | vwap_with+vol15 | am | t05s1 | 115 | -0.025 | -0.394 | -0.091 | 0.050 | 37 | -0.071 | -0.694 | -0.101 | 0.118 | 0.082 |
| L2 | squeeze | long | vol15+obv_with | am | t05s1 | 108 | -0.022 | -0.339 | -0.072 | 0.035 | 37 | -0.071 | -0.694 | -0.101 | 0.122 | 0.082 |
| L1 | squeeze | long | vol15 | am | t05s1 | 115 | -0.025 | -0.394 | -0.091 | 0.050 | 37 | -0.071 | -0.694 | -0.101 | 0.118 | 0.082 |
| L2 | r1s1break | long | dsma20_against+drsi_with | am | t1s1 | 173 | -0.066 | -0.673 | 0.052 | -0.244 | 73 | -0.041 | -0.287 | -0.098 | 0.080 | 0.117 |
| L2 | squeeze | long | vol15+macdh_with | am | t1s05 | 86 | -0.047 | -0.531 | -0.110 | 0.025 | 35 | -0.036 | -0.340 | -0.106 | 0.078 | 0.100 |
| L2 | aroonx | short | adxlo+vwap_against | am | t05s1 | 129 | -0.034 | -0.576 | -0.064 | -0.003 | 54 | -0.018 | -0.222 | -0.075 | 0.077 | 0.127 |
| L2 | stochx | long | macdh_with+open_with | am | t1s05 | 378 | -0.049 | -0.424 | -0.073 | -0.008 | 226 | 0.015 | 0.082 | -0.268 | 0.076 | 0.151 |
| L2 | s1r1hold | short | adxlo+dsma20_against | am | t1s1 | 735 | 0.030 | 0.589 | 0.069 | 0.010 | 209 | -0.047 | -0.841 | -0.080 | 0.119 | 0.075 |
| L1 | squeeze | long | vol15 | am | t1s05 | 115 | -0.052 | -0.495 | -0.080 | -0.019 | 37 | -0.025 | -0.267 | -0.089 | 0.073 | 0.110 |

### Random baselines (window 09:50-15:00 shown in this table; each config is compared with its own window)
| side | geom | tr_base | va_base |
|---|---|---|---|
| long | t05s1 | -0.135 | -0.171 |
| long | t1s05 | -0.123 | -0.168 |
| long | t1s1 | -0.134 | -0.191 |
| short | t05s1 | -0.113 | -0.112 |
| short | t1s05 | -0.101 | -0.108 |
| short | t1s1 | -0.101 | -0.089 |

## 5. Finalists and modules
**None.** No configuration passed the pre-declared gates, so no `type: lab` module is shipped and nothing goes to the
locked holdouts. Nothing in config/default.yaml or the live runner was touched.
- The tooling for a later rework is ready. `gen_modules.py <results row>` writes a self-contained module (SIDE, GEOM, LAYERS, REQUIRES, mask(df)).
- It was verified on 3 rows: the generated mask reproduces the scan's n and expectancy exactly (390 / +0.0071, 19,520 / -0.0853, 9,681 / -0.0974). Those test modules went to scratch, not to the repo.
- **Deployment requirement for any future article-indicator module:** `LabStrategy.generate` must add the article columns.
  - The call is `f = f.join(article_features(hist, (ctx.prev_high, ctx.prev_low, ctx.prev_close), daily_closes).drop(columns=["close"]))`.
  - Pivots and intraday indicators need nothing new.
  - `d_sma20` can come from `ctx.sma20`.
  - `d_rsi14` and `d_sma50` need prior daily closes, which `DayContext` does not carry today.
  - Ichimoku needs `prior5` of at least 80 bars.

## 6. Caveats and deviations from the declared grid
- Sources were snippets only (section 1). Settings are the textbook defaults the snippets and the brief name. Article-specific variants could not be checked.
- The `adxlo` filter's plateau neighbours were set to 15/25. The declaration said "ADX 20/25/30"; 20 is adxlo's own default, so the neighbours had to differ. This had no effect because nothing reached the plateau step.
- Valid has only 14 sessions, and train has 40, from a single summer regime.
- The ex-best-day, halves, and baseline numbers for every scored row are in results.csv.

## 7. Files
- `features.py` builds the indicators (live parity).
- `build.py` writes `data/feat.parquet` (git-ignored).
- `scan.py` runs the declared grid and writes `results.csv`, `counts.json` and `plateau.csv` (empty: no plateau step ran).
- `report.py` renders the tables.
- `gen_modules.py` is the module writer.
- Backlog entries added: bdi-art-indicator-grid (failed, 23,868 configs), bdi-art-squeeze-vol-rework, bdi-art-ichimoku-warmup, bdi-art-daily-sma50, bdi-art-parabolic-sar, bdi-art-volume-profile, bdi-art-ad-divergence, bdi-art-prior-day-fib, bdi-art-supertrend-eom, bdi-art-valuation-filter.

Reproduce: `python research/bdi/articles/build.py && python research/bdi/articles/scan.py && (cd research/bdi/articles && python report.py)`.
