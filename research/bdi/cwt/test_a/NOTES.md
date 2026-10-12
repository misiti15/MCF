# CWT package A (open, gap and in-play setups) - worker CWT-A

*Educational only - not financial advice. Lab backtests on the open two-year history; nothing here is a paper or
live result. Guest claims are unverified paraphrases; no transcript text is used.*

## 1. Implementation (fixed 2026-10-12 before any package A configuration was scored)

Grid: exactly TESTPLAN.md section 2 (A1 68, A2 96, A3 72, A4 32, A5 18, A6 64, A7 64, A8 80, A9 72 = **566**), with
the CWT-A amendment at the end of TESTPLAN.md. Code: `engine.py` (data, exits, costs, controls), `families.py`
(A1-A4, A6-A9), `a5.py` (A5), `run.py` (one pass, one process), `score.py` (gates and report).

- **Data.** `data/cache_hist/1Min` (SIP 1-minute, RTH 09:30-15:59) per symbol; locked-block rows (2024-11-01..
  2025-02-28) dropped right after each load. Daily context (prior close, ATR(14) = mean true range of the prior 14
  sessions, adv20, gap, run3/run5/upstreak, day-1/day-2 stats, 5-day high/low) is built from the same 1-minute bars,
  per contiguous segment, so March 2025 lookbacks never reach into the block (the first ~10 sessions of March 2025
  have no ATR and no trades). Features were checked against the lab frames (TSLA 2025-06-05: vwapDistPct,
  dist_hod_atr, atr_d, gap, adv20 identical). A5 uses the official daily bars (`w3_daily/data/daily_2016.parquet`,
  open = the auction print, rescaled to the 1-minute price scale by the day's high).
- **Decision bars** are 5-min bars labelled by their close (09:35 = the 09:30-09:35 bar). Bar-close signals enter at
  the open of the next minute (next-bar entry). Stop entries (A3, A4) fill at max(level, minute open) for buys
  (mirror for sells) on the first minute trading through the level.
- **Exits** run on 1-minute bars from the entry minute: stop first inside a minute, a gap through the stop fills at
  the minute's open, targets are limits filled at their price, flat at the 15:55 price (close of the 15:54 minute).
  ON (A1): stop active to 16:00, then exit at the next session's 09:35 (stop active 09:30-09:35, gap fills at the
  open). S2 (A8): stop active through day +2, else the day +2 close. Trades whose next session is missing (locked
  block, end of data) are dropped.
- **R** = 0.25 x daily ATR for every exit; the lab geometries use their own +-kR target/stop.
- **Costs.** Entry side (1c + 1 bps) x `gates.tod_cost_mult` (3.8x before 09:35, 2.1x to 09:50, 1.4x to 10:30) x tier;
  non-target exits (1c + 1 bps) x the same TOD multiplier (before 10:30) x tier; stop fills +2c x tier. Tier = 3x when
  |gap| >= 20%, open < $5 or adv20 < $5M. A5: entry at the auction print 2x, exit TOD multiplier; hedge leg costs in.
- **Universe.** adv20 >= $1M (point in time), open >= $1, ATR and prior close known.
- **Earnings.** Yahoo report dates (`research/bdi/earnings/data/earnings_yf.parquet`). E-out = no report date within
  +-4 business days (the live blackout rule). `earn_day` = report date (bmo / during market) or next business day
  (amc); unknown-time rows (53) excluded. Symbols without coverage count as E-out.
- **Controls (rule 6).** For each date, a deterministic 3% sample of the universe (crc32 of symbol|date) gives the
  outcome of entering at every 5-min bar 09:35-15:00, long and short, for t1s1 / t05s1 / t1s05 and hold-to-15:55.
  A trade's control is the mean of that sample at its date, entry bar, side and exit (structural / ON / S2 exits use
  hold-to-15:55). Reported: control expectancy and the paired difference (trade - control) with its day-clustered t.
  A5's control is the same-day, same-H mean open->H move of all top-300 names, signed by the trade's side, with the
  trade's own cost.
- **Gates** (`mcf/research/gates.py` + swarm1010 live-probation bar): n >= 150; exp > 0; day-clustered t >= 2.0
  (probation) and t >= max(1.5, sqrt(2 ln N)) for the lineage (N = the family's plan count, and separately plan +
  overlapping backlog lineage); exp > 0 in up and in down sessions (n >= 30 each); walk-forward positive share >= 0.6
  (3-month train / 1-month test, folds touching the locked block skipped); plateau = mean exp of the neighbours
  (configurations of the same family that differ in exactly one grid parameter, side excluded) > 0; ex-best-day > 0;
  busiest session <= 10% of trades.

## 2. Results (scored 2026-10-12; open two-year history, locked block never loaded)

> **Re-checked 2026-10-12 after the stop-side fix (`RECHECK_1012.md`).** 41 configurations (A1 S/ON, A6 S, A7 S) moved
> slightly worse and 1,640 trades were removed. The verdict is unchanged (566 of 566 fail). The A7 row now reads: 6
> configurations with exp > 0, best t 0.70 (cid 373: +0.131, n 566). `results.csv` is the post-fix version. The
> table below is the original scoring.

**Failures first: 566 of 566 configurations fail the live-probation bar. None passes its try-count t bar. No candidate,
no lab module.** Run: 1,226 symbols, 2,476,458 simulated trades (A1-A4, A6-A9) plus A5 (top-300 names), 831 s in one
process. All 566 configurations produced trades except 10 A8 `earn_day` / c 0.25 configurations, which had n = 0.
All numbers are R after production costs (R = 0.25 x daily ATR). Per-configuration table: `results.csv`; quarters in
`data/results.csv`.

| family | configs | exp > 0 | exp > 0 and n >= 150 | t >= 2 | regime pass | WF >= 0.6 | median exp | best t (n) | best n>=150 config (exp, t, up / down) | median ctl exp | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A2 CWT01 gapper morning fade (short) | 96 | 0 | 0 | 0 | 0 | 0 | -0.533 | -2.24 (622) | G30 h1015 T2 t1s05 guest: -0.415, t -2.24, up -0.64 / down +0.17 | -0.161 | fail (worst family; gappers keep running in up sessions) |
| A9 CWT08 good-news gap dip buy (long) | 72 | 0 | 0 | 0 | 0 | 0 | -0.208 | -0.50 (497) | -0.100, t -0.50, up -0.05 / down -0.75 | -0.136 | fail |
| A5 CWT19 opening-print fair-value fade | 18 | 0 | 0 | 0 | 0 | 0 | -0.175 | -1.93 (5,105) | k0.75 H5 none: -0.121, t -1.93 | -0.168 | fail (the SPY hedge makes it worse: median -0.205 vs -0.148) |
| A6 CWT43 failed gap auction fade | 64 | 0 | 0 | 0 | 0 | 0 | -0.149 | -1.33 (12,589) | -0.061, t -1.33, up +0.13 / down -0.33 | -0.128 | fail |
| A1 CWT02 first red day short | 68 | 0 | 0 | 0 | 0 | 13 | -0.141 | -0.13 (172) | r3_30 T1 t05s1: -0.031, t -0.13, up +0.11 / down -0.14 | -0.157 | fail (beats its controls by +0.03 R median; ON and S exits worst) |
| A4 CWT06 gapper ORB, narrowing range / rvol gate | 32 | 9 | 9 | 0 | 0 | 0 | -0.135 | 0.77 (1,541) | b_rvol 2.5 short S full: +0.154, t 0.77, up -0.65 / down +0.68 | -0.121 | fail (gap-down shorts work only in down sessions) |
| A3 CWT10 prior-day high/low breakout | 72 | 14 | 4 | 0 | 4 | 6 | -0.136 | 1.84 (135) | q0.3 cat long t1s05 full: +0.096, t 1.32, up -0.02 / down +0.17 | -0.092 | fail (the catalyst subsets are small and noisy; the no-catalyst sets are -0.13 R over ~5-40k trades) |
| A7 CWT09 bad-news gap-down bounce short | 64 | 7 | 7 | 0 | 0 | 2 | -0.109 | 0.78 (589) | G10 out T1 S: +0.141, t 0.78, up -0.27 / down +0.37 | -0.092 | fail (regime: down-session effect only) |
| A8 CWT07 catalyst gap-and-go (long) | 80 | 28 | 0 | 8 | 0 | 0 | -0.072 | 3.19 (10) | none (max n 192: G3 out c0.40, all exp <= 0 at n >= 150) | -0.114 | fail (the t >= 2 rows are earn_day samples of n 10-18 from 8-12 sessions) |

- **Window.** Full day vs guest window changes little (median exp per family within 0.03 R); neither rescues any family.
- **Regime.** Every short-side gap family (A2, A4 short, A6 short, A7) is positive in down sessions and negative in up
  sessions; the long side mirrors it. Same pattern as the RESCORE: the session regime is only known at the close.
- **Controls (rule 6).** The same-time random entries lose about -0.09 to -0.17 R after costs. A1, A3 and A6 are a
  little better than their controls (median paired difference +0.03 / -0.04 / -0.01 R; best paired t 2.11 / 3.01 / 1.29
  over 68 / 72 / 64 configurations). Beating a losing control while staying negative is not an edge.
- **Earnings-day variants (blackout conflict).** `config/default.yaml` has `earnings_blackout_days: 4`, so every
  `earn_day` configuration (A7, A8, A9: 104 configurations) trades days the live system blocks; a pass would need an
  owner exception. A8 `earn_day` is the only positive pocket (24 of 40 configurations > 0, median +0.49 R), but its
  configurations have n 0-18 (290 trades summed over 40 overlapping configurations). That is too small to read: it is
  a data-collection idea, not a result. A7 / A9 `earn_day` are negative (median -0.126 / -0.146 R).
- **A2 descriptive (Edu's claims).** Universe gap >= 20% symbol-days with adv20 >= $1M: 229. Closed below their open:
  44.1% (claim about 76-77%). Session high set by 09:50: 41.9% (median high-of-day bar 10:25; IQR 09:35-14:30).
- **A1 day-3 failed push:** median n 63, all 8 configurations negative (best -0.097 R).
- **Caveats.** Survivorship bias (today's 1,226 names). No float, dilution, premarket or borrow data: short results on
  gappers and runners are "borrow unverified". The extended 3x tier covers 44% of A2 trades. TOD costs apply to entries
  before 10:30.

### Try-count bars (reported, none reached)
Plan-only bar / plan + overlapping lineage bar: A1 2.90 / 3.25, A2 3.02 / 5.00, A3 2.92 / 4.84, A4 2.63 / 3.63,
A5 2.40 / 2.40, A6 2.88 / 3.24, A7 2.88 / 4.76, A8 2.96 / 3.32, A9 2.92 / 4.44; the whole round as one lineage 3.73.
The best t in package A at n >= 150 is 1.32 (A3).

### Configurations tried
566 (A1 68, A2 96, A3 72, A4 32, A5 18, A6 64, A7 64, A8 80, A9 72), all reported in `results.csv`. No configuration was
added, dropped or re-windowed after scoring.
