Educational only — not financial advice.

# UPDAY_1127 pre-registration (written 2026-11-27 evening, before any trade below was built or scored)

**Question (COVERAGE, mechanism).** Is there a LONG mechanism that pays on up / squeeze days without calling the day in
advance, and does it hedge Primary's (short-heavy) bad days? Context: BDI 11-27 (48/50 big movers set up 09:35-09:45,
long movers were names down from the open that rallied with the index; longs +14.3R vs shorts -115.2R across accounts),
11-25 (Primary's gap-down shorts squeezed after the morning). Research only: no change to config/, setups, exits,
assignments.json, decisions.json or the ledger. Optimism mindset; honest numbers; every config reported.

## Data, splits, guards
1-min RTH bars: data/cache_hist/1Min (1,226 symbols, 2024-09-16..2026-11-04) for FIT/CHECK; data/cache_fresh/1Min
(469 symbols, 2022-10-03..2024-09-13) for T2. FIT = 2024-10 + 2025-03..2025-09 (report only; nothing is tuned);
CHECK = 2025-10-01..2026-11-04; T2 = 2023-01-03..2024-09-13. EARLY (pre-2023): no single-stock minute data in the repo,
so not available (said so in the report). **Locked block 2024-11-01..2025-02-28 never read** (pyarrow filter at load +
assert on every output). Daily stats (ATR14 from RTH true range, adv20, prior close, 20-session return, rvol baseline)
are built from minute bars and reset at any > 7-calendar-day hole (first 20 sessions after a hole = warm-up).
Eligible symbol-day: adv20 >= $20M, ATR14 available, entry price >= $5, >= 15 of the 20 bars 09:30-09:49 present.
Point-in-time only. **Short interest / float are NOT available point-in-time** in the repo, so "heavily shorted" uses a
disclosed PROXY: prior 20-session return in the bottom 30% of that day's eligible names (crowded-short / downtrend
proxy) plus a gap down. This is a proxy, not short interest.

## Common trade rules
Long only. Signal on a 1-min bar close; entry at the NEXT bar's open; stop checked from the entry bar on (stop-first,
a bar opening through the stop fills at its open); time exit at the 15:55 bar close (last bar on half days). 1R =
entry - stop; trade only if risk >= 0.10% of price and risk <= 1.0 x ATR14. One entry per name per day per config.
Book cap: at most 10 trades per config per day (earliest entry first; ties by higher adv20). "TRAIL" exit = once
+1R is reached, stop trails 1R behind the best high (stop updated after each bar; checked on the next bar).
VWAP = session VWAP from 09:30 (typical price x volume).

## Configs (16) — three mechanisms
**SQZ (short-squeeze continuation in gap-down names that reclaim VWAP after 10:30)**
- S1 core: gap (09:30 open / prior RTH close - 1) <= -1.0%; crowding proxy (ret20 bottom 30% of day); every 1-min close
  09:50-10:29 below VWAP (shorts in control all morning); signal = first 1-min close > VWAP between 10:30 and 13:30;
  stop = session low so far - $0.01; exit 15:55.
- S2 = S1 without the crowding proxy (all gap-downs).  S3 = S1 with gap <= -3.0%.
- S4 = S1 + reclaim-bar volume >= 2x the median 1-min volume of the session so far (covering burst).
- S5 = S1 with TRAIL exit.  S6 = S1 with the signal window 10:30-12:00 only.
**RSL (relative-strength leaders on a weak open that reclaim the open)**
- R1 core: weak open = SPY 09:49 close vs 09:30 open <= -0.20%; stock RS = r50(stock) - r50(SPY) >= +0.50%
  (r50 = 09:49 close / 09:30 open - 1); stock traded below its own open in 09:30-09:49; signal = the 09:49 bar if its
  close > open, else first 1-min close > the 09:30 open between 09:50 and 11:30; stop = session low so far - $0.01;
  exit 15:55; top 10 per day by RS (replaces the earliest-first cap for R configs).
- R2 = R1 without the weak-open gate (any day).  R3 = R1 with RS >= +1.0%.  R4 = R1 with TRAIL exit.
- R5 = R1 with weak open SPY <= -0.40%.
**GUP (gap-up continuation, pullback to VWAP that holds)**
- G1 core: gap >= +2.0%; 09:49 close > VWAP; every 1-min close from 09:50 to the signal > VWAP; signal = first bar
  10:00-12:00 whose low <= VWAP x 1.001 and close > VWAP; stop = min(signal-bar low, VWAP) - 0.10 x ATR14; exit 15:55.
- G2 = G1 with gap >= +4.0%.  G3 = G1 + rvol (09:30-09:49 volume / median of the same window, prior 20 sessions) >= 2.
- G4 = G1 with TRAIL exit.  G5 = G1 on weak-open days only (SPY 09:49 vs open <= -0.20%).

**Count: 16 configs. Cumulative N ≈ 9,300 → ≈ 9,316.**

## Costs (always in)
LIVE-L main: research/primshorts_1126 cells_live.json, calib_live.predict_R(price bucket x exit kind; stop / market).
LR8 alongside: 1c + 1 bp per side, entry side x tod_cost_mult (mcf.research.gates), +2c on stop fills, 3x tier if
|gap| >= 20% or price < $5. Stress: entry one bar later (open of the bar after the entry bar, same stop) + 2 bp per
side (4 bp of entry / risk) on top of LIVE-L.

## Statistics and pass bars (per config; OOS = CHECK and T2)
Day series = mean LIVE-L R of that day's trades; day-clustered t over trading days with >= 1 trade.
Multiplicity: 16 configs → Bonferroni two-sided 0.05/16 → **t >= 2.96** on pooled OOS (CHECK + T2 days).
Lineage bar (cumulative N ≈ 9,316) ≈ t >= 4.3 is reported, descriptive.
PASS needs all of: (a) per-trade mean LIVE-L R > 0 on CHECK and on T2, each with >= 30 trades; (b) pooled OOS day t
>= 2.96; (c) OOS best-day share of total R < 50% and OOS avg R without the best day > 0; (d) OOS mean R above the
95th percentile of a size-matched random control (20 draws: each real trade replaced by a random eligible name on the
same day, same entry minute, same stop distance in % of price, same exit rule, same costs); (e) OOS stress mean > 0.
LEAD = (a), (c), (e) pass and pooled OOS t >= 2.0 but < 2.96 (or (d) misses). Else FAIL.

## Hedge / day-type reporting (descriptive, every config)
- Day types from SPY RTH open -> 15:59 close: UP > +0.25%, DOWN < -0.25%, FLAT otherwise; plus V-day (SPY 09:49 <=
  -0.20% vs open AND close > open — the 11-25 / 11-27 shape). Avg R/trade and R/day by type, per split.
- Correlation of the config's daily R (sum, 0 on no-trade days) with **Primary's bench daily R**: Primary 4 lots
  (L3-fromopen, RW3, RW5, NM-ETF; bench10 walked lots already built tonight under scratchpad/lbw/walk_t1.parquet,
  LIVE-L on shorts / LR8 on NM-ETF as every E4 study; simplified book = per-day cap 30 lots by entry minute, no
  latch — a disclosed simplification) on FIT + CHECK days (T1 only; T2 walk not available). Also the config's mean
  R/day on Primary's worst-quintile days vs other days. Negative correlation / positive R on Primary's bad days =
  hedge value.
- Live context: live dates are outside the bar cache (ends 2026-11-04); no live replay is promised.
