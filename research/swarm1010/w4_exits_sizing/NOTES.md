# W4 (swarm 2026-10-10): book-level exits, sizing and process rules

*Educational only - not financial advice. Lab backtests on the open two-year history only; nothing here is a live or
paper result.*

Brief (lead, 2026-10-09): improve the BOOK rather than add entries. (1) volatility sizing / sit-out using the
magnitude signals regime1009 found (SPY ATR%, SPY opening-range width, dispersion predict the SIZE of the rest-of-day
move, not its direction), plus per-setup daily loss stops and max-trades-per-setup-per-day (Reddit study item 21);
(2) exits across ALL setups at once on 1-minute bars; (3) heat_fade_short: any exit / size variant that makes it
robust. Report which book-level rule improves results in BOTH up and down sessions, with counts.

**Section 1 was written before any variant of this study was scored.** Seen beforehand: the published numbers of
RESCORE.md, timeofday, regime1009, trendguard (bdi-tg-*), the backlog. Section 1 changes only by dated amendments.

## 1. Pre-declaration

### 1.1 Data (open history only)
- Trades: `research/bdi/timeofday/data/trades.parquet` (already generated, nothing fitted here):
  - **Book P (primary, live today)** = the 14 lab/heat setups enabled in `config/default.yaml`, set `current`
    (exhaustion_short, MF1-MF5, NS1-NS5, RW6G1, heat_fade_short, heat_fade_long) + orb20_a and intraday_momentum
    (production-backtester trades `research/history2y/data/bt_trades.parquet`) = 16 setups.
  - **Book T (Testing account, full-day versions live from 10-12)** = the 32 `-FD` setups of
    `config/account_testing.yaml`: 29 from the timeofday set `full` (all its setups except RW8, which is not in the
    Testing config) + the 3 L3-*-FD modules, generated here from the lab frames with the FD module mask, window
    950-1500, prefilter gap <= -2.6573517 (min_adv 0), first qualifying bar per symbol-day; count check vs
    `research/bdi/fullday/verify.json` (n_full 5713 / 4156 / 4873).
- Entry price, daily ATR and 5-minute ATR% (`atrPct`) per trade: the lab frames via `research/history2y/lib.py`
  (locked months refused by the loader; `MCF_HIST_ALLOW_LOCKED` is never set).
- 1-minute paths: `data/cache_hist/1Min/<SYM>.parquet`; rows with a date in 2024-11-01..2025-02-28 are dropped
  right after reading, before any computation. Entry = close of the lab's 5-minute bar (tod = bar end), path = the
  1-minute bars starting at tod .. 15:54 (the 15:55 close is the flatten, as the lab).
- Market context per (session, bar): `research/bdi/regime1009/data/ctx.parquet` (S12 gap dispersion, S13 SPY ATR%,
  S14 SPY opening-range width in ATRs, S16 cross-sectional fromOpen dispersion; all known at the bar close). Regimes
  `lib.regimes()` (up / flat / down terciles, open history).

### 1.2 Book construction (fixed for every variant)
- One open position per symbol across setups (runner `already in symbol`): trades of a book sorted by entry time
  (ties: config order); a trade is taken only if that symbol has no position still open under the BASE exits. The
  resulting trade set is frozen and every variant is applied to the same set (exit variants change only the exits;
  sizing / process variants only weight or drop trades from it). Simplification: a trade dropped by a process rule
  does not free the symbol for a later trade of another setup.
- No account caps in the base (slots, per-setup sleeves, the -20R / -60R book stops). Max concurrent positions is
  reported. Book stops are tested as rules (P8/P9).
- orb20_a and intraday_momentum keep their own backtester exits in every exit variant (their exits are part of the
  rule: an opening-range break with a range stop; a 15:30 entry held to 15:55); they are in the sizing / process
  variants.

### 1.3 Simulation engine (1-minute)
- R = 0.25 x daily ATR (as the lab). Base exits per setup geometry (t1s1 / t05s1 / t1s05), flatten at 15:55.
- A 1-minute bar touching both target and stop counts as a stop (conservative, as the lab's 5-minute rule).
- Costs (production, `gates.prod_r` model): entry 1c + 1 bps; exit 1c + 1 bps except limit fills (target,
  scale-out); stop / trailing / breakeven stop fills +2c extra. Result in R of the initial risk.
- Reconciliation: 1-minute base vs the lab's 5-minute r per setup (mean and correlation) is reported. All variant
  deltas are against the 1-minute base, never against the 5-minute r.

### 1.4 Rules (configurations), each applied to the whole book at once
Exits (E, 11):
| id | rule |
|---|---|
| E1/E2/E3 | ATR trail: target removed; stop = the setup's stop, then trails k x ATR5 (5-min ATR = atrPct x close / 100 at entry) behind the best 1-minute high (long) / low (short) since entry, k = 1 / 1.5 / 2; checked on the next minute; flatten 15:55 |
| E4/E5/E6 | time stop: after 30 / 60 / 90 minutes, exit at that minute's close if the best excursion (MFE, highs/lows since entry) is still < +0.25R (runner `time_stop_min` / `time_stop_min_r` semantics); setup target/stop otherwise |
| E7/E8 | structural stop: stop just beyond the prior swing = lowest low (long) / highest high (short) of the 1-minute bars in the 30 / 60 minutes before entry (same session only) -/+ 1c; risk re-defined as that distance (clipped to 0.5R..3R of the ATR risk); size by that risk; target = the geometry's multiple of the new risk; result in units of the new risk (same $ at risk per trade) |
| E9 | scale-out: half at +1R (limit), stop on the rest to breakeven, rest held to 15:55 (setup target removed) |
| E10 | breakeven: stop to entry once MFE >= +0.75R; setup target kept |
| E11 | flatten at 15:30 instead of 15:55 |
Sizing / sit-out (Z, 8) - signals from ctx at the trade's entry bar; reference = the median (or 67th percentile) of the
same signal at the same tod over the previous 60 open sessions (min 20; no rule before that):
| id | rule |
|---|---|
| Z1 | weight = clip(ref_med / S13, 0.5, 2) (risk scaled by 1 / expected move, VIX proxy) |
| Z2 | weight = clip(ref_med / S14, 0.5, 2) (opening-range width in ATRs at the entry bar) |
| Z3 | skip the trade when S13 > its trailing 67th percentile (top tercile) |
| Z4 | skip the trade when S14 > its trailing 67th percentile (same tod) |
| Z5 | high-dispersion open (S16 at 09:50 > its trailing 67th pct): no entries before 10:00 |
| Z6 | as Z5, no entries before 10:30 |
| Z7 | high gap dispersion (S12 at 09:50 > its trailing 67th pct): no entries before 10:30 |
| Z8 | sanity / anti: weight = clip(S13 / ref_med, 0.5, 2) (bigger on volatile days) |
Process (P, 9) - realized P/L known at each entry from the base exits:
| id | rule |
|---|---|
| P1/P2 | per setup per day: no new entries after 2 / 3 losing closed trades |
| P3/P4 | per setup per day: no new entries once the setup's closed P/L <= -3R / -5R |
| P5/P6/P7 | max 5 / 10 / 20 entries per setup per day (first by time) |
| P8/P9 | book daily stop: no new entries once the book's closed P/L <= -10R / -20R |
Weighted variants report P/L as sum(weight x r); the mean weight is reported (Sharpe is scale-free).

### 1.5 Counting
- Book lineage: 28 rules x 2 books = **56** configurations; book bar t_req = sqrt(2 ln 56) = **2.84**.
- heat_fade_short lineage (prior N 19,648, bdi-tg-heat-fade-short): the 11 E + 8 Z + P1-P7 (7) = 26 rules on the
  setup alone, on `current` and `full` = 52, plus 3 scratch exits from backlog loop-1009-hfs-small-mfe-scratch
  (exit at market if MFE < +0.5R after 15 / 30 / 45 minutes) x 2 = **58**; t_req = sqrt(2 ln 19,706) = 4.45.
- Whole study: 56 + 58 = **114** configurations (+ the base reconciliation, not a configuration).

### 1.6 Metrics and verdicts
Per configuration: n trades, mean weight, exp R/trade, book daily P/L in R (mean, sd, annualised Sharpe x sqrt(252)),
max drawdown of cumulative daily R, worst day, up / flat / down mean daily P/L and exp, max concurrent positions,
and versus the base on the same sessions: daily delta (mean, day-level t), delta in up and down sessions, delta in H1 /
H2 (first / second 213 sessions), monthly delta positive share. Secondary: a "live notional" view weighting each trade
by atr_d / close (the runner's slot cap binds - shares = min(risk / stop distance, slot $ / price) - so live $ at risk
per trade is ~ slot x 0.25 x ATR%, not constant).
- **Book rule passes** (pre-declared) if: delta > 0 in up AND down sessions, delta t >= 2.84, delta > 0 in H1 and H2,
  monthly delta positive share >= 0.6, Sharpe and max drawdown not worse than base.
- **heat_fade_short robust** = the live-probation bar of RULES.md (n >= 150, exp > 0 in up AND down sessions with
  n >= 30, day-clustered t >= 2.0, walk-forward share >= 0.6, plateau (one-step neighbours: E1-E3 / E4-E6 /
  E7-E8 / Z1-Z2 / Z3-Z4 / Z5-Z6 / P1-P2 / P3-P4 / P5-P7 / scratch 15-45) mean > 0, ex-best-day > 0, busiest session
  <= 10% of trades); a pass is a probation candidate only (t_req 4.45 for "keep").
- Anything that passes goes to the backlog (prefix sw-w4-) and gets a runner spec; nothing is edited in mcf/.

### 1.7 Amendment (2026-10-10 ~00:30 UTC, after the 1-minute engine check on 3 symbols, before any variant was scored)
- Both books have negative expectancy at production cost (RESCORE / timeofday), so any rule that trades less or
  sizes down "improves" daily P/L mechanically. For sizing / sit-out / process rules (Z, P) the pass test therefore
  uses the **risk-matched** variant: its daily P/L scaled by (base total risk / variant total risk) over the whole
  sample, i.e. the rule run at the base's average risk budget. Delta vs base, up / down deltas, halves and monthly
  share are computed on the risk-matched series; raw daily P/L, Sharpe and drawdown are reported too. Exit rules (E)
  keep the same trades and the same $ risk per trade, so their raw delta is used (scale factor 1).
- Engine check: on AAPL / NVDA / TSLA (970 entries) the 1-minute base equals the lab's 5-minute production r to
  1e-5R (no same-bar ambiguity changed an outcome in that sample).
