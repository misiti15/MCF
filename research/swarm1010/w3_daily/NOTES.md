# W3 (swarm 2026-10-10): daily bars since 2016 and longer-holding edges (overnight, 1-20 day)

*Educational only - not financial advice. Lab backtests on daily bars; nothing here is a live or paper result.*

Owner's question: "Can we pull more trade data from other sources?" Intraday 1-minute history is limited by disk
space, but daily bars are small and go back ten years. This study pulls them and asks whether holds from the close to
the next open, or of 1-20 days, have edges that are large relative to costs.

**Section 1 (the pre-declaration) was written before any configuration was scored.** Beforehand I only checked the
data: row counts, dates, and whether the daily OHLC matches the 1-minute cache for AMD/TSLA/PLTR in the last 15
sessions. No returns were computed by condition. Results are in section 2.

## 0. Data pulled (step 1)
- `download_daily.py` pulls Alpaca `/v2/stocks/bars` with `timeframe=1Day`, `feed=sip`, `adjustment=all` (split and
  dividend adjusted), from 2016-01-01 to 2026-10-09. It covers the 1,226 symbols of `research/lab_symbols.txt`. SPY, QQQ,
  IWM, DIA and the sector ETFs (XLK/XLF/XLE/XLV/XLI/XLY/XLP/XLU/XLB/XLRE/XLC, SMH, XBI, KRE, XHB, XRT, XME, GDX, IYR,
  TLT, GLD) were already in that list. It ran as a single process, in batches of 100 symbols, with a 0.35 s gap between
  pages.
- Output: `data/daily_2016.parquet` (git-ignored, zstd, about 60 MB, 2.91M rows, 2,708 sessions, 1,225 symbols). DOW
  returned no bars and is missing. Coverage per symbol is in `coverage_by_symbol.csv`; coverage per year is in
  `coverage_by_year.csv`, written by `study.py`.
- Check against the 1-minute cache (AMD, TSLA and PLTR, 2026-09-30..10-07): the daily open and close are the official
  opening and closing auction prints, which differ from the first and last 1-minute bar by a few cents. High and low
  match the regular session exactly. Fills at the open and close (MOO/MOC) are therefore the right model.
- **Coverage table** (`coverage_by_year.csv`):

  | year | symbols with bars | sessions | rows | SPY year (class) |
  |---|---|---|---|---|
  | 2016 | 945 | 252 | 235,899 | +13.0 % (up) |
  | 2017 | 968 | 251 | 240,152 | +21.7 % (up) |
  | 2018 | 995 | 251 | 246,078 | -5.0 % (down) |
  | 2019 | 1,027 | 252 | 254,593 | +31.1 % (up) |
  | 2020 | 1,063 | 253 | 262,991 | +18.5 % (up) |
  | 2021 | 1,113 | 252 | 274,623 | +28.6 % (up) |
  | 2022 | 1,134 | 251 | 281,954 | -18.2 % (down) |
  | 2023 | 1,149 | 250 | 285,220 | +26.2 % (up) |
  | 2024 | 1,177 | 252 | 293,556 | +24.9 % (up) |
  | 2025 | 1,203 | 250 | 297,305 | +17.7 % (up) |
  | 2026 YTD | 1,225 | 194 | 235,697 | +15.1 % (up) |

  - 926 symbols have bars from 2016-01-04 and 299 start later (IPOs and listings). **No symbol ends before 2026-10**:
    there are no delistings at all, so the sample is purely survivors.
  - On a median day, 816 stocks are eligible (see 1.2).
  - There are no flat years, so the year split is only up (9 years) against down (2018, 2022).
  - The month classes are terciles of SPY monthly returns, cut at +0.2 % and +3.0 %: 42 / 42 / 42 open months.
- `assets_meta.csv` comes from Alpaca `/v2/assets` (read-only). It holds the name, exchange and today's
  shortable/easy_to_borrow flags, and a regex ETF tag with 203 names, including leveraged and inverse funds. The stock
  families leave out ETF-tagged names.
- **Survivorship (important):** the universe is *today's* liquid list applied back to 2016.
  - Names that were delisted, acquired or became illiquid between 2016 and 2026 are absent, and today's winners are
    over-represented. The number of symbols with bars grows from about 920 in 2016 to 1,225 now (IPOs and listings).
  - This biases **long** mean reversion and dip buying upward most strongly in the early (train) years. A dip in a
    name that later died is not in the data.
  - Short results are biased the other way.
  - The two validation windows (2023+, 2025-03+) are only 1-3 years back, so they are much less affected. They carry
    the decision.

## 1. Pre-declaration (written before scoring)

### 1.1 Splits
| split | dates | use |
|---|---|---|
| train | 2016-01-04 .. 2022-12-31 | in-sample |
| valid1 | 2023-01-01 .. 2024-10-31 | validation |
| LOCKED | 2024-11-01 .. 2025-02-28 | **not used at all**. Any trade whose entry-to-exit window touches it is dropped before any statistic. Nothing is reported from it. The lead scores finalists on it once |
| valid2 | 2025-03-01 .. 2026-10-09 | second validation |

Features with lookbacks (SMA200, 52-week high, RSI) in March to May 2025 use prices from the locked block. These are
inputs, not outcomes. No return inside the locked block is computed or reported.

### 1.2 Eligible stocks (point in time)
A stock is eligible if it is not ETF-tagged, closes at $5 or more on the signal day, has a 20-day median dollar volume
of at least $20M (prior 20 sessions including today), and has at least 200 prior bars when SMA200 or a 52-week feature
is used.

### 1.3 Costs (always in)
- Per side: 1c/share + 1 bps of price. As a return: `0.01/price + 0.0001` at entry plus the same at exit, using each
  side's own price.
- Shorts also pay borrow at **3 % a year** for each calendar day held: 1 day for overnight, the calendar days between
  the entry and exit dates otherwise. Today's easy_to_borrow flag is not point in time, so it is not used as a filter.
- Fills are at the official open or close print (MOO/MOC). No extra slippage is charged on auction prints, which is
  optimistic for small names. The $20M ADV floor limits that.

### 1.4 Statistics
- The unit is one trade's net return in bps.
- A symbol cannot re-enter while its previous position in the same configuration is open. The time between trades is
  measured from entry to exit.
- **Clustered t:** trades are grouped in blocks of `max(1, 2*hold)` trading days by entry date (blocks of 1 day for
  overnight trades), and the clustered SE is the same formula as `gates.summary`. Overlap between neighbouring blocks
  remains for multi-day holds, so the t is slightly optimistic.
- **Excess:** the trade's gross return minus the mean gross return of all eligible stocks over the same entry and exit
  times. This separates a timing edge from "long stocks in a bull decade". It is reported for stock families. For long
  configurations, the candidate gate also requires excess > 0 in train and valid1.
- **Try-count bar:** `t_required(N) = max(1.5, sqrt(2 ln N))`. N is the configurations in the family (its lineage). The
  global N is also reported.

### 1.5 Regimes (step 3)
- **Year class** by SPY's calendar-year total return: up if > +10 %, down if < 0, flat otherwise. The partial year 2026
  is classed by its year-to-date return. 2024 is classed on its full year but excludes Nov-Dec trades.
- **Month class** by SPY's monthly return, cut at the terciles of all months outside the locked block. Each trade
  belongs to its entry month.
- **Day class** for overnight and 1-day holds: `gates.session_regimes` on the daily file. The cut points are terciles of
  the universe's median open-to-close return outside the locked block. Reported only.

### 1.6 Grid (pre-declared; every row counts)
**F1 overnight** (enter MOC on day t, exit MOO on day t+1), with a long and a short version of each condition:
- C0 every eligible stock, as the baseline
- intraday move on day t (close/open - 1) in the bottom or top cross-sectional decile of the day (2)
- close location in the day's range `(c-l)/(h-l)` below 0.1 or above 0.9 (2)
- RSI2 below 5 or above 95 (2)
- gap at day t's open versus the prior close of -3 % or less, or +3 % or more (2)
- day of week of the entry, Mon to Fri (5)
- last trading day of the month (1)

That is 17 conditions x 2 sides = **34**.

**F2 Connors-style mean reversion** (stocks only):
- Long: close > SMA200 and RSI(n) < thr. Short mirror: close < SMA200 and RSI(n) > 100 - thr.
- n is 2 or 3; thr is 5 or 10.
- Entry at the close of day t (MOC) or at the next open (MOO).
- Exit at the close of t+1, t+3 or t+5 (or the same horizon counted from the MOO day), or the Connors exit: the first
  close above SMA5 (below it for shorts), capped at 10 sessions.

That is 2 sides x 2 x 2 x 2 x 4 = **64**.

**F3 momentum / 52-week high** (stocks, entry MOC on day t, exit at the close k sessions later, k = 5 or 20):
- 52wh_new: today's close >= the max close of the prior 252 sessions (long)
- 52wh_2pct: close >= 0.98 x the max high of the prior 252 sessions (long)
- mom20_top: top decile of 20-day return among eligible stocks (long)
- mom20_bot: bottom decile of 20-day return (short)
- rev5_bot: bottom decile of 5-day return (long, short-term reversal)
- rev5_top: top decile of 5-day return (short, short-term reversal)

That is 6 x 2 = **12**.

**F4 post-gap drift** (stocks):
- Gap at day t's open of +g or more (long) or -g or less (short), with g = 3 % or 6 %.
- Confirmation is either "any" or "the day closes in the gap's direction" (o2c has the same sign).
- Enter MOC on day t and exit at the close k sessions later, k = 1, 5 or 10.

That is 2 x 2 x 2 x 3 = **24**.

**F5 calendar** (instruments: SPY, QQQ, IWM and the equal-weighted eligible stocks EW):
- TOM: enter MOC on the 2nd-to-last trading day of the month, exit MOC on the 3rd trading day of the next month (4).
- DOW: hold one close-to-close day ending on Mon..Fri (20).
- ON: overnight holding of the instrument every day (4).
- All long.

That is **28**.

**Total N = 162.** The bars per family are t_required(34) = 2.66, (64) = 2.88, (12) = 2.23, (24) = 2.52 and
(28) = 2.58. Globally, t_required(162) = 3.19.

### 1.7 Gates (pre-declared; a "daily candidate" needs all of them)
1. Net expectancy > 0 in train, valid1 and valid2, with n >= 100 in each split. F5 has fewer trades, so it uses
   n >= 20 per split.
2. Clustered t on train+valid1 >= t_required(N_family).
3. Valid1 clustered t >= 1.5.
4. Long stock configurations also need excess > 0 in train and in valid1.
5. Regime: net expectancy > 0 in up months **and** in down months (train+valid1+valid2 pooled), each with n >= 30.
   Results by year class are reported.
6. Plateau: the mean net expectancy of the configuration's grid neighbours (one parameter one step away, same family,
   same side) is > 0 on train+valid1.

The verdict is **candidate** (all gates pass), **near** (exp > 0 in all three splits but another gate fails), or
**fail**.


### 1.8 Amendments (dated, made while scoring; no amendment changes a gate or a threshold)
- **2026-10-09, counting error.** F1 has 15 conditions (C0, 2 x o2c, 2 x clv, 2 x rsi2, 2 x gap, 5 x DOW, tom_last),
  not 17. That gives **30 configurations, not 34**. The **total N is 158**, not 162, and the F1 bar is t_required(30) = 2.61.
  `evaluate.py` uses the real counts.
- **Clarification of the F2 MOO horizon.** K1/K3/K5 exit at the close of session t+k counted from the *signal* day t,
  for both MOC and MOO entries. So MOO + K1 holds from the open to the close of day t+1.
- **Plateau neighbours.** F1 and F5 have no ordered parameters, so their plateau is N/A and counts as passed. The steps
  are:
  - F2: n 2<->3, thr 5<->10, entry C<->O, exit K1-K3-K5-SMA5
  - F3: k 5<->20
  - F4: g 3<->6, conf, k 1-5-10
  These were coded in `evaluate.py` after the trial run of F5 (calendar, which has no plateau) and before any F1-F4
  result existed. A key-matching bug at first gave F3 an empty neighbour set; it was fixed with no other change.

## 2. Results (158 configurations; failures first)

*Educational only - not financial advice.* All figures are net of costs, in bps per trade. "Excess" means minus the
equal-weighted eligible universe over the same entry and exit. The locked block 2024-11..2025-02 is not in any figure.

| verdict | F1 overnight (30) | F2 Connors (64) | F3 mom/52wh (12) | F4 gap drift (24) | F5 calendar (28) | total |
|---|---|---|---|---|---|---|
| fail | 29 | 35 | 4 | 17 | 19 | **104** |
| near | 1 | 26 | 7 | 7 | 9 | **50** |
| candidate | 0 | 3 | 1 | 0 | 0 | **4** |

### 2.1 Failures and near misses
- **F1 overnight (close to open): nothing survives costs.**
  - Long on every eligible stock: gross about +4 to +6 bps a night, net -2.2 / -0.6 / -0.1 bps (train / valid1 /
    valid2). The overnight drift that papers document is real but about the size of 1c + 1 bps a side.
  - The conditions (weak close, bottom-decile day, RSI2 < 5, gaps, day of week, month end) move it by only a few bps,
    and none is consistent across splits. Best: CLV < 0.1 long at +0.9 / +4.7 / +8.0, t 0.55 ("near").
  - Every short loses 5-40 bps a night.
  - On an index (F5 ON_SPY/QQQ/IWM) net is +0.5..+5 bps, t <= 1.6, and it fails in down months.
- **F2 shorts (32), all fail.**
  - Below SMA200 with RSI > 90/95, short 1-5 days: positive in train (+20..+75 bps, the 2018/2022 bears), then
    -12..-80 bps in both validations.
  - Shorting overbought names in downtrends does not generalise.
- **F2 longs, RSI2 variants and thr 10 (26 "near").**
  - Every long Connors variant is positive in all three splits: +1.5..+100 bps, rising with the hold.
  - Most fail the down-month gate or the bar (t_required(64) = 2.88). RSI2 < 10 enters too often, in falling markets.
  - The K1 (one-day) versions are only +2..+25 bps with t < 1.3. The edge needs the 3-5 day bounce.
- **F3:**
  - Momentum and 52-week-high longs make +13..+350 bps per trade, but almost all of it is market drift: the excess is
    negative in train or valid1, and they lose -60..-150 bps in down months. They are beta, not timing.
  - Every momentum and reversal short fails, at -40..-310 bps.
- **F4 post-gap drift:**
  - Up-gap longs held 5-10 days look large in valid1/valid2 (+75..+290 bps). They are weak in train (t <= 1.6) and lose
    heavily in down months, so they also look like beta and a recent-years effect.
  - Down-gap shorts fail.
  - One-day post-gap holds fail.
- **F5 calendar:**
  - Day of week: no weekday is consistent across the three splits except "ending Monday" (Friday close to Monday close)
    on SPY/QQQ/IWM, which has a recent effect (valid1/valid2 +18..+40 bps, train ~0, t <= 1.2) and fails the bar.
  - Turn of the month on SPY/QQQ: +25 / +9 / +66 bps (SPY), but only 19-21 trades per validation split and t <= 1.2.
    A known anomaly, but too few events to pass a try-count bar.

### 2.2 Candidates (all pre-declared gates pass)
Three configurations come from **one lineage** and are near duplicates: the same signal with different entry and exit
(MOC vs MOO, SMA5 exit vs 5 days). Treat them as **one idea, with the MOO + SMA5 version preferred for live** (see 3).
The fourth is a separate lineage.

| id | rule | train | valid1 | valid2 | t (tr+v1) / bar | excess tr / v1 / v2 | up / flat / down months | down years (2018+2022) | WF share >0 | per session |
|---|---|---|---|---|---|---|---|---|---|---|
| **F2_rsi3_5_O_SMA5_L** | close > SMA200 and Wilder RSI(3) < 5 at the close -> buy the next open (MOO); sell at the first close > SMA5, max 10 sessions | +74.0 (n 3,223) | +65.1 (n 1,113, t 3.19) | +78.3 (n 898, t 3.00) | 5.07 / 2.88 | +20 / +28 / +16 | +115 / +89 / +51 | -0.5 (2018 +35, 2022 -61) | 0.74 | 3.4-4.3 |
| F2_rsi3_5_C_SMA5_L | same, but buy at that close (MOC) | +68.8 | +71.5 (t 3.61) | +91.3 (t 2.87) | 4.46 / 2.88 | +20 / +27 / +25 | +131 / +93 / +46 | -13.5 | 0.79 | 3.4-4.3 |
| F2_rsi3_5_O_K5_L | same entry as the first row; sell at the close of t+5 | +64.8 | +69.0 (t 2.05) | +71.4 (t 2.07) | 3.27 / 2.88 | +17 / +28 / +22 | +126 / +86 / +38 | -15.9 | 0.68 | 3.4-4.3 |
| **F3_rev5_bot_k20_L** | bottom decile of the 5-day return among eligible stocks with 200+ bars -> MOC, hold 20 sessions | +164 (n 25,191) | +189 (n 8,391, t 2.19) | +245 (n 8,196, t 2.31) | 3.56 / 2.23 | +30 / +22 / +48 | +354 / +118 / +68 | +11.6 (2018 +12, 2022 +11) | 0.67 | 16-21 |

Extra checks (`candidates.csv`; the same trades, nothing new tried):
- **Cost sensitivity.** Average cost is 6.3 bps per trade (Connors) and 7.5 bps (rev5). At 2x cost, Connors MOO+SMA5
  makes +65.6 bps (valid2 +72.8) and rev5 +178 bps. Costs are not the binding constraint here, unlike intraday.
- **Live-probation items that apply to daily holds:**
  - n >= 150: yes.
  - Walk-forward share >= 0.6: yes (0.67-0.79). On excess it is 0.52-0.63.
  - ex-best-session > 0: yes, +58..+183 bps.
  - Busiest session <= 10 % of trades: yes, 1.8 % (Connors, 2018-02-05) and 0.2 % (rev5).
  - Up and down months > 0: yes for all four.
- **Caveats (read before believing these):**
  1. **Survivorship.** Buying dips and losers on today's survivors is exactly the trade that survivorship flatters.
     Delisted losers are absent: no symbol in the file ends before 2026-10. Train (2016-2022) is the most biased. Valid2
     (2025-03+) is the least biased, and it is still positive: Connors +78 bps net / +16 excess, rev5 +245 / +48.
  2. **Most of the per-trade return is market drift.** For rev5, excess is only +22..+48 of +164..+245 bps. It is a
     high-beta long basket of about 400 open positions (16-21 entries a day x 20 days); the timing edge is the excess.
     For Connors, excess is about 30 % of the gross.
  3. **Bear years.** In 2022 Connors loses about 60 bps per trade (SMA200 does not protect a slow bear), and rev5 is
     roughly flat in 2018/2022. Up/down *months* pass; down *years* do not for Connors.
  4. **The MOC variant uses the close price in its own signal.** Live, it would have to run on a 15:50 snapshot. The
     MOO variant has no such problem.
  5. The clustered t ignores overlap between neighbouring blocks for multi-day holds, so it is somewhat optimistic.
  6. Connors-style RSI is published and widely traded. Its decay after publication is visible: 2023 is only +25 bps
     with t 0.9.

## 3. What the live system would need (spec; not implemented, nothing in config/ or mcf/ was touched)
The existing runner (`mcf/execution/runner.py`) is **intraday-only**. It trades 1-minute bars and **flattens all MCF
positions at `session.flatten_by`** (`flatten_mcf`). Nothing in MCF holds a position overnight, sends MOO/MOC
(`TimeInForce.OPG` / `CLS`) orders, or tracks a position across sessions. A daily strategy needs:
1. **A separate daily job, outside market hours.** About 16:30 ET it reads SIP daily bars (the same endpoint as
   `download_daily.py`, the last 260 sessions) and computes SMA200, SMA5, Wilder RSI(3), the 5-day return, the
   20-day median dollar volume, eligibility ($5, $20M ADV, not an ETF, 200+ bars), the signals, and the exits due.
2. **Orders.**
   - Entries and exits as MOO orders (`time_in_force=OPG`), submitted between 16:30 and 09:28 ET.
   - The MOC variant would instead need a 15:50 snapshot job with `CLS` orders, so prefer MOO.
   - Exits for the SMA5 rule are decided at the close and executed at the next open. **Note:** this differs from the
     backtest, which exits at the close; the open-exit version was not tested and would need its own run.
   - Exits for rev5/K5 are date-based. For an exact match with the backtest, the exits need CLS orders at 15:45-15:50,
     or the rule must be re-specified to exit MOO on t+k+1 and re-scored.
3. **Position separation.** Daily positions must be tagged (for example a client_order_id prefix `daily-`). They must
   be excluded from `flatten_mcf`, from the intraday risk caps and from reconcile, or else run on their own paper
   account. Otherwise the 15:55 flatten would close them on day 1.
4. **Risk and sizing.**
   - Connors: equal weight, up to about 5 new positions a day and 10-20 open, with a cap on positions per sector.
     There is no stop in the tested rule; a catastrophic stop would change the result and needs testing.
   - rev5: about 400 concurrent positions. That is only realistic as a small equal-weight basket or a top-N subset.
     Top-N was not tested; a subset is a new configuration.
5. **Journal/report.** Multi-day P/L, overnight gap risk, and corporate actions on a held position (the backtest uses
   adjusted bars).
6. **Testing staging.** The intraday lab-module contract in RULES.md (SIDE, GEOM, LAYERS, mask(df) on 5-minute
   frames) does not fit a daily-hold rule. No Testing YAML is staged, because the runner cannot execute it. Paper
   forward-testing needs the daily job first.
7. **Holdout.** The lead can score the locked block 2024-11..2025-02 once for `F2_rsi3_5_O_SMA5_L` and
   `F3_rev5_bot_k20_L`. Do that with `study.make_trades` after removing the NaN masking of `Cx`/`Ox` for those months.
   This study never computed it.

## 4. Files
- `download_daily.py`: the data pull.
- `data/daily_2016.parquet`: the bars (git-ignored).
- `data/trades_*.parquet`: candidate trades (git-ignored).
- `coverage_by_symbol.csv` and `coverage_by_year.csv`: coverage. `assets_meta.csv`: the ETF tags.
- `study.py`: the grid. `evaluate.py`: the gates, written to `gates.csv`. `candidates.py`: the extra checks, written
  to `candidates.csv`.
- `results.csv`: every configuration x split, regime and year (all numbers in this note). `regimes.json`: the year
  and month classes.

## Locked block (rule 19), scored ONCE by the lead 2026-10-09 (`score_locked.py`, `locked.json`)
Trades entered 2024-11-01..2025-02-28, same costs. Bar (look 1): exp > 0 and t >= 1.0. **Both fail.**
- F2_rsi3_5_O_SMA5_L (Connors dip buy): n 331, **-106 bps**/trade, t -1.64, win 54%, excess vs universe -43 bps.
- F3_rev5_bot_k20_L (weekly reversal basket): n 1,597, **-85 bps**/trade, t -1.08, excess +10 bps.
SPY was +4.4% over the block, so the losses are not a market-down artefact. Educational only - not financial advice.
