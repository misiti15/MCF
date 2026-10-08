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
