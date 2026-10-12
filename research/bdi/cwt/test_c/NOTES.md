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

### 1.5 Amendments made while scoring (dated 2026-10-12; no grid level, count or gate changed)
- **C8 follow-through state** (TESTPLAN amendment, before any return was scored): as written it was on 100 % of the
  time after March 2016; distribution days were added (on-share 39 %, about 30 on/off cycles).
- **Bug fix, intraday pieces:** the first intraday run mixed the raw (unadjusted) 1-minute cache with the adjusted
  daily file, a systematic -2..-4 % error per trade (SPY 2024-09-17: raw 563.10 vs adjusted 548.66). Minute bars are
  now scaled by adjusted daily close / raw last minute close of the same session (`intraday.adj_day`), and all eight
  intraday configurations were re-run. Only the corrected numbers are reported.
- **S6 parity:** the overlay simulator with no overlay reproduces longhold's S6 daily returns to 6e-9 (the reference
  file is float32), monthly active t on train+valid 3.25 as in longhold.
- **Cluster block (disclosure, verdicts unchanged):** "2 x median hold" was computed on each split's own trades
  (median hold 4 in train+valid1 -> blocks of 8 sessions). Using the whole-sample median (3 -> blocks of 6) the C1
  candidates' t falls to 3.12 and 2.98, under their 3.15 bar; see 2.3.

## 2. Results (124 configurations = 117 + 7 S6 overlays; failures first)

*Educational only - not financial advice. Backtests on daily bars (two-year 1-minute history for 8 configs), costs
in, locked block 2024-11..2025-02 in no figure. Net bps per trade unless stated. "Excess" = minus the equal-weighted
eligible universe over the same entry and exit (the random same-side same-window baseline).*

| family (configs) | candidate | near | fail | best by train+valid1 t | why it fails |
|---|---|---|---|---|---|
| C2 tight base breakout (20 = 16 daily + 4 intraday) | 0 | 8 | 12 | M10 B20 w8 SMA20: +57 / +56 / -155, t 1.8 | excess vs universe -55..-137 in valid1; down months -74..-164; intraday entry -12..-28 bps (n 431-538), t < 0 |
| C3 MA pullback (8) | 0 | 8 | 0 | SMA50 MOC 2nd close: +34 / +25 / +48, t 3.4 | all beta: excess -22..-61 in valid1, down months -51..-96, 2022 -55..-110 |
| C4 new-high + trailing stop (12) | 0 | 10 | 2 | N252 Donchian20: +169 / +97 / +415, t 2.3 | excess negative in valid1 (-65..-286), down months negative, 2022 -219..-615; brackets ~0 |
| C5 calendar (7) | 0 | 0 | 7 | Jan loser rebound q20: +624 / -57 / +198 (9 events) | FOMC eve: +9 / +8 / -23 (n 55/14/13), 13:55 exit n 14 -3 bps; IWM-SPY year-end 7/1/1 events, -253 in valid2; Jan rebound negative in valid1 and below the universe in valid1/valid2 |
| C6 event AVWAP (4) | 0 | 4 | 0 | 252-high anchor, AVWAP exit: +66 / +33 / +162, t 2.8 | excess -33..-59 in valid1, down months -32..-69, 2022 -63..-130 |
| C7 index streaks / day 3 / day 5 (10) | **1** | 4 | 5 | see 2.2 | day-3 short -24 / -22 in valid1/valid2; 3-down + 5-day hold loses -72 in down months; day 5 n 11; streak 4/5 t below bar or n < 20 |
| C1 oversold limit dip (28) | **2** | 21 | 5 | see 2.2 | shorts (4) fail: +47..+70 in train, -18..-68 in both validations; market-open exits ~0..+30 bps; most longs miss the 3.15 bar or valid1 t 1.5 |
| C8 regime gates on C1-C4 (12) | 0 | 9 | 3 | spy10 on C3 / C4 "improve" (+2..+25 bps each split) | the gated books still fail excess and down months; FTD and SPY>SMA200 lower C1's valid2 by 30-37 bps; spy200 on C4 is identical to C4 (it already has that filter) |
| C9 exit / sizing overlays on C1-C4 (16) | 0 | 12 | 4 | none improves | Kidd, two-close SMA20 and Keltner cut the winners: C4 -79..-359 bps per trade, C1 -21..-106; governor mixed (-18..+63); sma20x2 on C3 is identical to C3 |
| C8 + C9 on S6 (7) | 0 | - | 7 | Keltner: active -3..-9 %/yr vs S6 | no overlay improves S6 (2.4) |

Every configuration with its fails is in `gates.csv`; every split, month class and year is in `results.csv`.
Configurations tried: 117 daily/two-year + 7 S6 = 124 (lineage bars in 1.4). Expected false passes at a flat
p = 0.05 would be about 6; the try-count bars are stricter than that.

### 2.1 Up / down markets, walk-forward, plateau (all configs)
- Down months (SPY bottom tercile) are where the daily long books die: 61 configurations fail the down-month gate and
  61 fail excess <= 0, i.e. their return is market beta in a bull decade (W3's finding again). 2018 and 2022 are
  negative for every C2, C3, C4 and C6 configuration.
- Walk-forward month share >= 0.6 fails in 72 configurations (C2/C4/C6 sit at 0.45-0.6).
- Plateaus: C1 longs are positive on every neighbour (+20..+116); C2 intraday, C7 day 5 have negative plateaus.

### 2.2 Candidates (every gate of 1.4 passes)
| id | rule | train | valid1 | valid2 | t tr+v1 / bar | excess tr / v1 / v2 | up / down months | 2018 / 2022 | WF | ex-best day | busiest |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **C1_L_rsi2_5_none_L5_sma5** | close > SMA200, Wilder RSI(2) < 5 -> next day buy limit 5 % below that close (fill min(open, limit)); sell at the first close > SMA5, max 5 sessions | +168 (n 1,318) | +155 (n 342, t 2.02) | +276 (n 565, t 3.62) | 4.13 / 3.15 | +142 / +111 / +183 | +244 / +180 | +57 / +51 | 0.71 | +172 | 3.7 % (2020-02-27) |
| **C1_L_rsi3_15_none_L3_sma5** | same with RSI(3) < 15 and a 3 % limit | +88 (n 4,492) | +82 (n 1,303, t 1.69) | +208 (n 1,756, t 4.45) | 3.52 / 3.15 | +98 / +58 / +129 | +178 / +83 | +28 / -2 | 0.81 | +105 | 1.8 % |
| **C7_streak3_upclose** | SPY, QQQ, IWM: buy the close of the 3rd consecutive down close; sell the first up close (cap 20) | +34 (n 247) | +43 (n 71, t 2.96) | +90 (n 64, t 3.43) | 3.20 / 2.15 | n/a (index) | +106 / +25 | -4 / +46 | 0.71 | +42 | 0.8 % |

Tightening diagnostics (`diag.py`, `diag.csv`; not counted, can only remove):
- 2x costs: C1 rsi2 +161 / +146 / +269 (t 2.96 on whole-sample blocks); C1 rsi3 +81 / +75 / +202; C7 +31 / +40 / +88.
  Average cost 7-8 bps per trade (C1), 3 bps (C7): costs are not binding.
- Top-300 names by dollar volume (less survivorship): C1 rsi2 +183 / +149 / +389; C1 rsi3 +87 / +63 / +259.
  2016 cohort only: +179 / +169 / +252 and +85 / +97 / +190.
- Fill type: the C1 edge is larger on gap-down fills at the open (+209..+455) than on intraday limit touches
  (+54..+254); both are positive in every split.
- C7 per instrument: QQQ +55 / +77 / +83 (t 3.5), SPY +28 / +46 / +88 (t 2.6), IWM +22 / +10 / +100 (t 1.4).

### 2.3 Caveats (read before believing these)
1. **The C1 candidates are a variant of a lineage that has failed the locked block twice** (W3 Connors MOO, -106 bps,
   look 1; sat1010 VIX-filtered rework, -103 bps, look 2). A limit 3-5 % below the close is the same "buy the
   oversold dip in an uptrend" bet, so they would be **look 3: t >= 2.0** there. Their valid1 t is 2.02 / 1.69 and
   2022 is flat at best.
2. **Cluster-block fragility (C1):** train+valid1 t over blocks of 1/2/4/6/8/10/20 sessions: rsi2-L5 3.46 / 3.35 /
   3.27 / 3.12 / 4.13 / 3.76 / 3.98; rsi3-L3 3.70 / 3.30 / 3.12 / 2.98 / 3.52 / 3.34 / 3.09 (monthly clusters 3.76 /
   3.15). The bar is 3.15, so rsi3-L3 is a pass only under the declared block and is a marginal candidate. C7 is
   stable: 3.07-3.52 against 2.15.
3. **Survivorship:** today's liquid list applied back to 2016, no delistings. Buying deep dips is the trade that
   survivorship flatters most; the top-300 and 2016-cohort checks keep the sign but cannot remove the bias.
4. **C7 is small and correlated:** 382 trades on three highly correlated ETFs (about 38 a year), 1.7-day average hold;
   IWM alone is weak (t 1.4). Index streak buying is old public knowledge.
5. 2x the plan's cost does not change any verdict, but limit fills on the touch are optimistic for queue position
   (a limit order at the low of the day may not fill); the gap-fill share (10-13 % of trades) carries a larger part of
   the C1 edge than its count.

### 2.4 Does any overlay improve S6 (`s6_overlays.py`, `s6_gates.csv`)? **No.**
S6 base (longhold split): active vs EW +26.8 / +24.8 / +60.9 %/yr, Sharpe 1.37 / 1.10 / 1.53, maxDD train+valid -44 %.

| overlay | active train / valid / valid2 (%/yr) | change vs S6 | Sharpe change | maxDD tr+v | t (bar 3.12) |
|---|---|---|---|---|---|
| C8 SPY > SMA200 (to cash) | +13.7 / +5.9 / +42.8 | -13 / -19 / -18 | -0.07 / -0.43 / -0.16 | -33 % | 1.12 |
| C8 SPY > SMA10 | -1.4 / +0.1 / +40.9 | -28 / -25 / -20 | -0.55 / -0.52 / +0.28 | -30 % | -0.09 |
| C8 follow-through state | +0.3 / +9.3 / +2.4 | -27 / -16 / -58 | -0.24 / -0.05 / -0.38 | -21 % | 0.69 |
| C9 two closes < SMA20 | +14.6 / -0.4 / +23.1 | -12 / -25 / -38 | +0.32 / -0.46 / -0.08 | -33 % | 0.91 |
| C9 Kidd 8/21 EMA | +9.8 / -6.0 / +11.2 | -17 / -31 / -50 | +0.20 / -0.68 / -0.35 | -34 % | 0.27 |
| C9 Keltner 3-ATR target | +22.0 / +21.9 / +52.1 | -5 / -3 / -9 | -0.10 / -0.05 / -0.12 | -44 % | 2.83 |
| C9 equity-curve governor (20 weeks) | +22.7 / +9.4 / +51.5 | -4 / -15 / -9 | +0.18 / -0.35 / +0.15 | -30 % | 2.04 |

Every overlay lowers the active return in all three splits; the regime gates and the governor make drawdowns
shallower (-21..-33 % vs -44 %) but at a larger cost in return than they save, and none raises Sharpe in all three
splits. This agrees with sat1010's crash-guard reworks (18 guards, all lowered S6's t). S6 stays as it is.

## 3. For the lead
- One-time locked scoring (not run by this worker): `python research/bdi/cwt/test_c/score_locked.py` (dry run with
  `--dry-run` writes nothing and sees no locked row). It scores trades entered 2024-11-01..2025-02-28 with the same
  code and costs, and applies look 3 (t >= 2.0) to the two C1 rows and look 1 (t >= 1.0) to C7. Recommendation under
  "at most one per lineage": **C1_L_rsi2_5_none_L5_sma5** (higher and more stable t than rsi3-L3) and
  **C7_streak3_upclose**.
- Live needs: like W3/longhold, a daily job outside market hours (signals after the close, next-day limit/GTC-day buy
  orders for C1, MOC orders for C7 entries and exits), positions exempt from the 15:55 flatten, its own paper account.
  Nothing in config/ or mcf/ was changed; no Testing YAML is staged (the intraday runner cannot hold overnight).

## 4. Files
`common.py` (data, engine, statistics), `families.py` (C1-C9 daily), `intraday.py` (C2 intraday, C5a 13:55, C7 day 5),
`s6_overlays.py`, `evaluate.py` -> `gates.csv` / `results.csv`, `diag.py` -> `diag.csv`, `score_locked.py` (lead),
`raw_s6.csv` / `s6_gates.csv`. `data/` (git-ignored parquet, about 33 MB): trades.

## Lead: one-time locked-block score (2026-10-12)
| id | look / bar | n | net bps | t (day) | verdict |
|---|---|---|---|---|---|
| C1_L_rsi2_5_none_L5_sma5 | 3 / t >= 2.0 | 111 | -104.9 | -0.84 | FAIL |
| C7_streak3_upclose | 1 / t >= 1.0 | 12 | +5.4 | 0.13 | FAIL |

C1_L_rsi3_15_none_L3_sma5 was not scored (one per lineage), so it remains unseen on the locked block.
The Connors dip-buy lineage has now failed the locked block three times, with almost the same loss each time (about -105 bps).
