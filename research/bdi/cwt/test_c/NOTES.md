# CWT package C (daily, swing and calendar setups): test run

*Educational only - not financial advice. Lab backtests on daily bars (plus three small pieces on the two-year 1-minute
history). Nothing here is a paper or live result. Guest claims from Chat with Traders are paraphrased in
`../CATALOG.md`; no transcript was opened for this work.*

The grid is the pre-declared package C of `../TESTPLAN.md` section 4 (117 configurations) plus the dated amendment
of 2026-10-12 (C8/C9 also on S6: +7, **total 124**). Section 1 below fixes the implementation details the plan left
open. It was written before any package C configuration was scored. Results are in section 2.

## 1. Implementation (fixed before scoring)

### 1.1 Data, splits, locked block
- Daily bars: `research/swarm1010/w3_daily/data/daily_2016.parquet` (Alpaca SIP, adjusted, 2016-01-04..2026-10-09),
  ETF tags from `assets_meta.csv`. S6 overlays use the loader of `research/bdi/saturday1010/new/lib.py` (parity with
  longhold's S6 daily returns is checked before use) plus the high/low columns of the same file.
- Splits (W3): train 2016-01..2022-12, valid1 2023-01..2024-10, valid2 2025-03..2026-10. S6 overlays use the
  longhold splits (train 2017-2020, valid 2021-2024.10, valid2 2025.03+) so they compare with S6's own record.
- **Locked block 2024-11-01..2025-02-28:** every outcome price (open, high, low, close) in it is set to NaN before any
  trade is simulated; a trade whose path reaches a locked row is dropped; no signal inside the block can trade.
  Look-back features (SMA200, RSI, 252-day high, AVWAP) may span the block, as inputs only (W3/longhold convention).
  The S6 simulator zeroes every locked-day return (longhold convention) and drops locked days from every statistic.
  The intraday pieces drop locked rows right after each symbol's 1-minute file is read.
- Eligible stock (point in time at the signal close): not ETF-tagged, close >= $5, 20-day median dollar volume
  >= $20M, >= 253 bars (saturday1010 lib). Index families (C5, C7) trade SPY/QQQ/IWM.

### 1.2 Fills and costs
- Cost per side: 1c/share + 1 bps of the fill price; shorts pay 3 %/yr borrow per calendar day held.
- MOC = signal-day close, MOO = next open. Limit buy at X: filled if the day's low <= X, at min(open, X). Buy stop
  at X: filled if the day's high >= X, at max(open, X). Sell limit (target) at X: filled if high >= X at max(open, X).
  Protective stop at X: filled if low <= X at min(open, X) (gap through the stop fills at the open).
- Inside a bar: open gap checks first, then stop before target (conservative). On an entry day filled intraday (limit
  or stop entry), the stop is checked against the whole day's range and the target is not checked (order unknown,
  conservative). MOC entries start their exit checks the next session.
- Close-based exits fill at that close. "k sessions" time stops exit at the close of session entry+k (for MOC
  entries, counted from the signal day).
- One position per symbol per configuration; no re-entry while it is open; the first qualifying signal wins.

### 1.3 Family details the plan left open
- C1: RSI = Wilder (W3). "Max 5 sessions" = close of entry+5. Short mirror has no trend filter (plan as written).
- C2: base = the B sessions before the signal day (t-B..t-1); width = (max high - min low) / close(t-1); trigger
  close(t) > base high; trend and momentum tests at t; momentum = 63-day return in the top 10/20 % of eligible stocks
  that day. Exit check X at closes; stop = base low intraday; cap 40 sessions.
  Intraday variant: breakout days from the base configuration (M10, B10, w8 %) that fall in the open two-year
  history; buy the first 5-min close (09:35-15:55 bars) above the 5-min / 30-min opening-range high while price is
  above the base high; stop base low; exit X as daily (from that day's close on).
- C3: "low within 1 % of SMA k" = |low / SMA_k - 1| <= 1 %; SMA50 rising = SMA50(t) > SMA50(t-20). Buy stop at the
  signal day's high + 1c on the next day only. Stop = SMA_k(t) - ATR14(t), fixed. "Second close below SMA20" = the
  second (not necessarily consecutive) close below SMA20 after entry. 10-session time exit otherwise cap 60.
- C4: N-day high = close >= max close of the prior N sessions; volume >= 1.5 x mean of the prior 50 sessions.
  Donchian exits are intraday stops at the lowest low of the prior 20 / 50 sessions (updated daily). Bracket: +5 %
  limit / -7 % stop from the fill, time stop close of entry+5. Cap 250 sessions on Donchian exits.
- C5a: SPY bought at the close before each FOMC statement day; "prior-day return < 0" = that eve's close-to-close
  return. 13:55 exit = the 1-minute close of the 13:54 bar on the statement day (two-year history only).
  C5b: IWM long / SPY short, equal dollars, close of the first session on/after Dec 15 to the last December close.
  C5c: YTD return at the first session on/after Dec 15; buy the close of the first session on/after Dec 20, sell
  the close of the first session on/after Jan 15. Equal weight across the decile/quintile. Excess vs the EW
  eligible universe over the same dates.
- C6: earnings reaction day = report date if before the open or during market hours, the next session if after the
  close (`research/bdi/earnings/data/earnings_yf.parquet`, 2019+; unknown timing dropped). 252-day-high anchor = the
  session of the highest high of the last 252 sessions. AVWAP = cumulative typical price x volume / volume from the
  anchor session to t. Anchor must be >= 5 sessions before t. Signal: close(t-1) > AVWAP(t-1), low(t) within
  +-0.5 ATR14 of AVWAP(t), close(t) > AVWAP(t), close > SMA50. Buy next open; stop AVWAP(t) - ATR14 fixed. Exit:
  first close below the (updated) AVWAP, cap 60 | close of entry+10.
- C7: down-close streak >= N (first day it reaches N, no re-entry while held); exit first up close (cap 20) | close of
  entry+5. Day 3: close location >= 0.75 on days t-1 and t, both closes strictly inside the prior 20-day high-low
  range; short the open of t+1; exit that close | first down close (cap 10). Day 5: four consecutive lower lows on
  days t-3..t (each low < the previous day's low); on day t+1 (two-year 1-minute history) price trades below low(t)
  and then a 5-minute bar (09:35-15:00 decision bars) closes back above it -> buy that close; stop the day's low so
  far for exit "15:55" (hold to 15:55, stop at the session low at entry) and lab geometry t1s1 (R = 0.25 x daily ATR14).
- C8 base configurations (first listed): C1 RSI3<15, no regime, L 2 %, exit SMA5; C2 M10 B10 w8 % X SMA10; C3 SMA20,
  MOC, second close below SMA20; C4 N50, no volume, Donchian 20. FTD state on SPY: starts "off"; while off, a rally
  attempt starts on the first up close after the lowest low since it went off (an undercut of that low restarts the
  attempt); day 4 or later of the attempt with SPY up >= 1.25 % on volume above the prior day -> "on"; on until a close
  below the attempt's low, or (TESTPLAN amendment) 6+ distribution days (SPY down >= 0.2 % on higher volume) in the
  last 25 sessions; the distribution count restarts at each follow-through day.
- C9 on C1-C4 trades (added to the base exit, whichever comes first): two consecutive closes below SMA20 -> exit that
  close; Kidd: half exits at the first close below EMA8, the other half at the first close below EMA21 (base exit
  closes what is left; the trade's return is the mean of the halves, each paying its own costs); Keltner: sell limit at
  EMA20 + 3 x ATR14 from the prior close; governor: a trade's size is 0.5 when, at its entry date, the cumulative
  net return of the book's last trades closed before that date is below the mean of its last 20 values (needs >= 20
  closed trades; full size before). Governed books report size-weighted figures.

### 1.4 Statistics and gates (trade families C1-C7)
- Unit: one trade's net return (bps). Day-clustered t: trades grouped by entry date in blocks of max(1, 2 x median
  hold) sessions (W3). Excess = trade gross minus the mean gross of all eligible stocks over the same entry (open or
  close) and exit (open or close) prices; side-adjusted for shorts. This is the "random same-side same-window" baseline.
- Month classes: SPY month return terciles outside the locked block (W3 regimes); year classes as W3 (2018 and 2022
  are the down years).
- **Candidate** needs all of: (1) exp > 0 in train, valid1, valid2 with n >= 100 each (index/calendar: n >= 20);
  (2) day-clustered t on train+valid1 >= the lineage bar; (3) valid1 t >= 1.5; (4) stock families: excess > 0 in
  train and valid1; (5) exp > 0 in up months and in down months (n >= 30 each); (6) plateau: mean train+valid1 exp of
  the one-step grid neighbours > 0 (N/A for C5/C8/C9); (7) walk-forward: share of open months (with trades) whose
  mean net > 0 >= 0.6; (8) ex-best-entry-day exp > 0; (9) busiest entry day <= 10 % of trades; (10) n >= 150 overall.
  **near** = exp > 0 in all three splits but a gate fails; **fail** = the rest. Intraday pieces (two-year history
  only) are judged on the rule-19 gates (n >= 150, t bar, up and down sessions, walk-forward >= 0.6) and cannot pass
  gate (1).
- Lineage bars (plan count + overlapping backlog lineage): C1 28 + 64 (W3 F2) + 51 (sat1010 Connors reworks) = 143
  -> 3.15; C2 20 + 12 (W3 F3) = 32 -> 2.63; C3 8 -> 2.04; C4 12 + 8 (lh-52wh) = 20 -> 2.45; C5 7 -> 1.97; C6 4 -> 1.67
  (the intraday AVWAP video lineages are a different holding period and are not added; with them the bar would be
  above 5); C7 10 -> 2.15; C8 15 -> 2.33; C9 20 + 22 (sw-w4-book-exits) = 42 -> 2.73; S6 overlays 130 -> 3.12.
  Whole round as one lineage (1,058 = 1,051 + 7): 3.73.
- **Overlays (C8, C9) on C1-C4:** "improves" = exp higher than the base book in train, valid1 and valid2 and a higher
  train+valid1 t. An overlay is a candidate only if it improves its base and the overlaid book passes gates 1-5 and
  7-10 at the C8/C9 bar.
- **Overlays on S6:** longhold Tier A on the overlaid book (active vs EW > 0 in all three splits; monthly active t on
  train+valid >= 3.12; active > 0 in SPY-up and SPY-down months) **and** an improvement over S6: active higher in all
  three splits, or (Sharpe higher in all three splits and max drawdown on train+valid shallower).
