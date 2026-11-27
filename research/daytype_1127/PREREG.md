# DAYTYPE-1127 — pre-registration (written 2026-11-27 ~21:35 UTC, before any score below was computed)

*Educational only — not financial advice.* Research only: no change to config/, setups, exits, assignments.json,
decisions.json, the ledger or the backlog. Broker / MarcoFlow: no calls. Alpaca market data: GET only (15-min bars for the
EARLY breadth sample; keys never printed).

## Question
ARENASTARS-1127 found that the arena's best GEN records (G05 / G07 / G37) were really bets on SPY's afternoon direction
spread over 30-100 stocks (+887R on days SPY moved >= 0.5% their way, -1,907R otherwise). Salvage idea (backlog, untested):
trade the same day-type as **one index position**. Does extreme breadth at 11:30 / 13:00, with or without an
afternoon-trend confirmation, predict SPY / QQQ's direction to 15:55 well enough to pay costs?
Optimistic hypothesis: breadth extremes + a trend confirmation pick afternoons that keep going. Prior (disclosed): the
wave-3 WILDCARD study found intraday momentum ~0 before costs; BREADTHGATE found breadth gates useless; so failure is the
base case unless the trend confirmation supplies the direction.

## Data
* SPY / QQQ SIP 1-minute RTH bars: 2016-01-04..2022-09-30 from the qqqopen_1127 raw fetch (scratch, not in git),
  2022-10-03..2024-09-13 `data/cache_fresh/1Min`, 2024-09-16..2026-11-04 `data/cache_hist/1Min`.
* Breadth (dt_breadth.py), arenastars_1127/t2ctx.py method: per 5-min bar END time, breadth_vwap = share of names with
  close > typical-price cumulative VWAP from the first regular bar; breadth_open = share with close > the day's 09:30 open.
  Universe = the 469 names of the T2 cache, read from the T2 cache and from cache_hist for the same 469 names (one
  universe for T2 / FIT / CHECK). Value at 11:30 = bar 11:25-11:30 close, known at 11:30:00 (no look-ahead).
* EARLY breadth (2016-01..2022-12): 15-min SIP bars (raw) for a seeded random sample of 130 of the 469 names (ETFs SPY /
  QQQ / leveraged excluded), fetched GET-only (dt_fetch15.py); same definitions on 15-min bars (VWAP from 15-min typical
  prices). Validated on T2 against the 469-name 5-min version (correlation and agreement on the 0.30 / 0.70 sides),
  reported before EARLY is scored. Survivorship (today's names back to 2016) disclosed.
* **Locked block 2024-11-01..2025-02-28 never read** (dropped and asserted in every script).

## Splits
EARLY 2016-01..2022-12 (extra out-of-sample) · T2 2023-01..2024-09-13 · FIT 2024-10 + 2025-03..09 (reported only) ·
CHECK 2025-10-01..2026-11-04. OOS pool = EARLY + T2 + CHECK.

## Trade (one index position per day at most)
* Signal at T in {11:30, 13:00}: LONG if breadth >= 0.70, SHORT if breadth <= 0.30 (follow the breadth, the arena bet).
* Trend confirmation TC (SPY, for both instruments): SPY's last 1-min close before T vs SPY's session VWAP (1-min
  typical price, 09:30..T-1) and SPY's 60-min slope (close at T-1 minus close at T-61). TC-long = above VWAP and slope > 0;
  TC-short = below VWAP and slope < 0. With TC on, a breadth signal trades only when TC agrees.
* TC-only configs: trade the TC direction every day it is defined (no breadth) — the "trend alone" control config.
* Entry: market at the open of the traded ETF's 1-min bar starting at T. Risk R = 1.0 x the ETF's ATR14 (mean true
  range of the prior 14 sessions, RTH, from the minute bars; prior-day info only). Stop = entry -/+ 1R, stop-first on
  1-min high/low, gap-through fills at the bar open. Exit: open of the 15:55 bar (half days: last bar - 4 min).
* Costs (always in): **LIVE-L** headline (primshorts_1126 cells_live.json, cost_R = a / stop_bps + b, bucket 100+ x exit
  kind market / stop); **LR8** alongside (qqqopen_1127 qo_score.costs formula, tod multiplier, +2c on stops, short
  borrow 1.2 bp); ETF-TIGHT (1 bp per side, +1c on stops) reported, never used for a pass.

## Configurations (counted): 24
* Breadth configs: measure {breadth_open, breadth_vwap} x T {11:30, 13:00} x TC {off, on} x instrument {SPY, QQQ} = 16.
* TC-only: T x instrument = 4.
* Threshold neighbours: the 2 breadth configs with the best FIT LIVE-L mean (>= 15 FIT trades) re-run at 0.25 / 0.75
  and 0.35 / 0.65 = 4.
Cumulative program N ~9,176 -> **~9,200** (lineage bar sqrt(2 ln N) ~ 4.27, reference only).

## Pass bars (each config, LIVE-L; all must hold)
1. Mean R > 0 on EARLY, T2 and CHECK separately; >= 30 trades on T2 and CHECK, >= 50 on EARLY.
2. OOS-pool t (one trade per day, so trade t = day-clustered t) >= **2.86** (one-sided Bonferroni 0.05 / 24).
3. OOS pool: best-day share of total R < 25 %; avg R without the best day > 0; CHECK avg w/o best day > 0.
4. Random-day control (size-matched): 500 draws of the same number of trades per split on random eligible days of the
   same split, same entry time / exit / stop rule, same long / short counts; config mean above the control's 95th pct.
5. Random-direction control: same days and entry times, direction drawn at random (500 draws); config mean above the
   95th pct (tests that the direction, not just the day choice, carries the edge).
6. Stress: entry +1 minute AND +2 bp per side extra: OOS-pool mean > 0 and t >= 2.0.
7. Breadth-with-TC configs: credited to breadth only if they beat the matching TC-only config on the same OOS days
   (paired, reported); otherwise the credit goes to the trend confirmation.
LR8 reported alongside; a LIVE-L pass that fails LR8 (or vice versa) is called out. Also reported: per-split n / mean / t,
win rate, long vs short, best day, year-by-year, average gross move in bp.

## Verdict
**PASS** if >= 1 config passes all bars. **LEAD** if a config is positive on all three OOS splits with OOS t >= 2.0 but misses
the multiplicity bar or one of bars 3-6. **FAIL** otherwise. Every config is listed (results.csv). Live window: none (no
live trades exist for this idea); rule-change notes are not applicable to a history replay of fixed rules.
