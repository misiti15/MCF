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

## 2. Results (appended 2026-10-10 ~03:30 UTC; section 1 unchanged apart from the dated amendment 1.7)

*Lab backtest on the open two-year history only (426 sessions: 142 up / 142 flat / 142 down), production costs.
Not live, not paper. Educational only - not financial advice.*

**Configurations scored: 114** (56 book rules = 28 rules x 2 books; 58 heat_fade_short configurations). Nothing was
fitted; every threshold was fixed in section 1. Locked block never loaded (`MCF_HIST_ALLOW_LOCKED` never set; 1-minute
rows of 2024-11-01..2025-02-28 dropped on read).

### 2.1 Failures first
- **No book rule passes (0 of 56).** No rule improves the book in both up and down sessions at the bar
  (delta t >= 2.84, both halves, monthly share >= 0.6, Sharpe and drawdown not worse).
- **Only 3 of 56 have a positive delta in BOTH up and down sessions, and none is significant:** T-Z1 (inverse
  SPY-ATR% sizing: up +3.21 / down +2.81 R/day, t 0.47, H2 negative), T-Z5 (no entries before 10:00 on
  high-dispersion opens: +0.15 / +0.42, t 0.16), T-P8 (book stop -10R: +0.26 / +11.75, t 0.20, H1 negative). Book P:
  0 of 28.
- **Almost every rule is a direction bet in disguise.** Both books are mostly shorts, so a rule that exits sooner or
  trades less "helps" in up sessions and hurts in down sessions, or the reverse. Example: E1 (1x ATR5 trail) on
  book T: +32.9 R/day in up sessions, -46.6 R/day in down sessions. Time stops E4-E6, trails E1-E2 and scratch exits
  all show this pattern. Scale-out (E9) shows the reverse.
- **Exits across all setups (E1-E11): 0 of 22 improve the book.** Of the 22, 19 lower mean daily P/L. The 3 with a
  higher mean are weak: T-E4/E5/E6 (+0.18 to +0.81 R/day, t <= 1.09, down sessions worse).
  Structural stops (E7/E8) are significantly worse on both books (t -3.3 to -9.2). The 2x ATR trail (E3) is worse on
  book T (t -3.15). Breakeven at +0.75R (E10) and the 15:30 flatten (E11) are slightly worse on both books.
  Per setup (n >= 100): out of 15 (P) / 27 (T) setups, an exit rule improves the setup's expectancy in both regimes
  for at most 4 setups (T-E11: 4; P-E6, T-E6, T-E8: 3) (`data/per_setup_exits_*.csv`).
- **Process rules (P1-P9): 0 of 18 pass.** Per-setup loss stops (P1-P4) and per-setup trade caps (P5-P7) trade
  less, but per unit of risk they are no better: the risk-matched delta has |t| <= 1.30, and the up and down signs
  are opposite in 13 of 14 cases (T-P2 is negative in both). The book daily stop -10R (P8) is the best of them (P: +1.19 R/day risk-matched, t 1.07; T: +0.69,
  t 0.20). It works through down sessions only (P up -0.87, T up +0.26), and one half is negative on book T.
- **Volatility sizing / sit-out (Z1-Z8): 0 of 16 pass.** The magnitude signals do separate down sessions, where the
  short-heavy books do better per unit of risk when they skip or shrink on wide-range days. They do not separate up
  sessions. The closest is **Z4** (skip a trade when SPY's opening-range width in ATRs at the entry bar is above its
  trailing 60-session 67th percentile for that time of day):
  - book P: risk-matched delta +2.63 R/day, t 2.03 (bar 2.84); up -0.83, down +6.42; H1 +2.05, H2 +3.21; months
    0.62; Sharpe -1.17 -> -0.03; max drawdown -2070 -> -1221 R.
  - book T: delta +4.53 R/day, t 1.36; up -1.35, down +15.48; months 0.52.
  - Z2 (inverse sizing on the same signal) is the same shape but weaker (P t 1.33, T t 1.57; up negative on both).
  - The anti-rule Z8 (bigger size on volatile days) is negative on both books, which is consistent with Z1/Z2.
- **heat_fade_short: 0 of 58 configurations make it robust.**
  - Up-session expectancy is negative in **all 58** (-0.08 to -0.27R). Down-session expectancy is positive in all 58.
  - Current window (09:50-10:30): base +0.018R (t 0.71, up -0.199, down +0.156). Best by exp is E3 (2x ATR trail),
    +0.040 (t 0.83, up -0.185). Best by t is Z5, +0.033 (t 1.22, up -0.184).
  - Exits that cut up-session losses also cut down-session gains by about as much: E1 up -0.076 / down +0.028;
    X15 scratch up -0.093 / down +0.046.
  - Full day (-FD, Testing): base -0.032R (t -2.20). Only P1 (stop after 2 losses per day) is positive: +0.008,
    t 0.27, n 11,445, up -0.215.
  - No variant reaches the probation bar (needs t >= 2.0 and up > 0), let alone t_req 4.45. The scratch idea of
    backlog loop-1009-hfs-small-mfe-scratch (X15/X30/X45) is tested here and fails.
  - **On this evidence, no exit or size change rescues heat_fade_short. Turning it off is the owner's decision; nothing
    here argues against it.**

### 2.2 Book facts (base, 1-minute exits; no account caps)
| | Book P (primary, 16 setups) | Book T (Testing, 32 -FD setups) |
|---|---|---|
| signals -> book trades (one position per symbol) | 64,400 -> 55,066 (129/day) | 305,384 -> 191,260 (449/day) |
| exp R/trade (up / down sessions) | -0.021 (-0.114 / +0.015) | -0.045 (-0.174 / +0.059) |
| mean daily P/L, Sharpe (ann.), max drawdown | -2.70 R/day, -1.17, -2,070 R | -20.3 R/day, -3.69, -9,129 R |
| max concurrent positions | 283 (config: 160 slots, 100 per setup) | 493 (config: 400 slots, 150 per setup) |
- **Slot caps bind:** both books exceed their slot caps on the busiest days, so live takes fewer trades than these
  books. Caps were left out on purpose (1.2).
- **Pre-emption by config order (live-relevant observation, not a rule test):** with one position per symbol and
  setups checked in config order, some setups almost never get the symbol.
  - Primary: RW6G1 keeps 12 of 424 lab trades, because NS2 (its parent, same window) fires first.
  - Testing: RW2-FD keeps 0 of 22,187 (exhaustion_short-FD fires first), RW4-FD 0 of 8,069 (NS3-FD), MF5-FD 2 of
    6,827, RW6-FD 9 of 3,614, RW6G1-FD 78 of 1,969.
  - So on these accounts the forward test of those setups is mostly empty. This assumes the runner checks
    strategies in config order (runner.step loops `self.strategies`).
- **Live sizing is not equal-R:** `RiskManager.size` = min(risk / stop distance, slot $ / price). With $100k x
  3.2 / 160 = $2,000 per slot, the slot cap binds (0.25% risk = $250 needs a stop distance >= 12.5% of price).
  Live $ at risk per trade is therefore about slot x 0.25 x ATR%, so high-ATR% names weigh more. The `notional_*`
  columns re-weight by that.
  - In that live-weighted view, Z4 improves both regimes on both books: P up +0.60 / down +5.34, t 2.22, months
    0.71; T up +0.97 / down +13.74, t 1.39.
  - This view is secondary and was looked at after the pre-declared test. It does not reach the 2.84 bar either.

### 2.3 Reconciliation
The 1-minute base reproduces the lab's 5-minute production r for every setup. Exp difference: <= 0.004R for 46 of
47 lists; ST5-FD differs by 0.030R (n 426). Per-trade correlation >= 0.95 (>= 0.994 for all but ST5-FD). Outcomes
change on <= 1.9% of trades, all of them 5-minute bars that touched both target and stop and that the 1-minute path
resolves (`data/reconcile.csv`). L3-*-FD counts equal verify.json (5,713 / 4,156 / 4,873).

### 2.4 Book tables (risk-matched deltas vs base; R per day; 142 up / 142 down sessions)
Book P
| rule | desc | n | exp_r | exp_up | exp_down | day_mean_raw | sharpe_raw | maxdd_raw | d_mean | d_t | d_up | d_down | d_h1 | d_h2 | d_month_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | base exits (setup geometry, flatten 15:55) | 55066 | -0.021 | -0.114 | +0.015 | -2.701 | -1.165 | -2069.800 | +0.000 | +nan | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| E1 | ATR5 trail 1.0x, no target | 55066 | -0.039 | -0.066 | -0.030 | -5.067 | -3.421 | -2256.500 | -2.366 | -1.660 | +6.069 | -5.981 | -0.094 | -4.638 | +0.333 |
| E2 | ATR5 trail 1.5x, no target | 55066 | -0.040 | -0.106 | -0.001 | -5.215 | -2.964 | -2536.500 | -2.514 | -1.540 | +0.923 | -2.175 | -0.386 | -4.641 | +0.286 |
| E3 | ATR5 trail 2.0x, no target | 55066 | -0.039 | -0.135 | +0.027 | -4.990 | -2.148 | -2907.200 | -2.290 | -1.100 | -2.732 | +1.554 | -0.307 | -4.272 | +0.333 |
| E4 | time stop 30 min if MFE < +0.25R | 55066 | -0.025 | -0.097 | -0.001 | -3.228 | -1.549 | -2021.900 | -0.527 | -1.320 | +2.112 | -2.146 | -0.229 | -0.826 | +0.381 |
| E5 | time stop 60 min if MFE < +0.25R | 55066 | -0.023 | -0.106 | +0.006 | -2.949 | -1.328 | -2086.500 | -0.248 | -1.000 | +1.013 | -1.206 | -0.135 | -0.361 | +0.381 |
| E6 | time stop 90 min if MFE < +0.25R | 55066 | -0.022 | -0.110 | +0.012 | -2.824 | -1.242 | -2091.000 | -0.123 | -0.690 | +0.415 | -0.402 | +0.006 | -0.253 | +0.429 |
| E7 | structural stop (30-min swing), risk = swing distance | 55066 | -0.052 | -0.126 | -0.024 | -6.686 | -3.218 | -3209.800 | -3.985 | -4.130 | -1.613 | -5.207 | -3.087 | -4.884 | +0.190 |
| E8 | structural stop (60-min swing), risk = swing distance | 55066 | -0.046 | -0.125 | -0.013 | -6.012 | -2.912 | -2960.600 | -3.312 | -3.310 | -1.488 | -3.817 | -2.554 | -4.069 | +0.238 |
| E9 | scale out 1/2 at +1R, rest BE to 15:55 | 55066 | -0.026 | -0.144 | +0.037 | -3.411 | -1.670 | -2307.300 | -0.710 | -0.830 | -3.870 | +2.855 | -0.623 | -0.798 | +0.286 |
| E10 | breakeven after +0.75R (target kept) | 55066 | -0.023 | -0.113 | +0.013 | -2.937 | -1.371 | -2090.500 | -0.236 | -0.710 | +0.147 | -0.291 | -0.191 | -0.282 | +0.286 |
| E11 | flatten 15:30 | 55066 | -0.023 | -0.109 | +0.005 | -3.028 | -1.306 | -2184.600 | -0.328 | -1.150 | +0.544 | -1.341 | -0.669 | +0.013 | +0.429 |
| Z1 | size x clip(med60/S13 SPY ATR%, 0.5, 2) | 55066 | -0.020 | -0.127 | +0.030 | -2.588 | -1.269 | -2148.900 | +0.110 | +0.170 | -0.983 | +1.915 | +0.098 | +0.121 | +0.429 |
| Z2 | size x clip(med60/S14 SPY OR width, 0.5, 2) | 55066 | -0.013 | -0.129 | +0.037 | -1.806 | -0.744 | -1696.500 | +0.978 | +1.330 | -1.080 | +2.971 | +0.734 | +1.221 | +0.524 |
| Z3 | skip if S13 > trailing p67 | 32836 | -0.020 | -0.152 | +0.052 | -1.545 | -1.056 | -1521.300 | +0.110 | +0.070 | -2.735 | +4.728 | +0.560 | -0.340 | +0.524 |
| Z4 | skip if S14 > trailing p67 (same tod) | 34599 | -0.001 | -0.135 | +0.064 | -0.044 | -0.028 | -766.900 | +2.631 | +2.030 | -0.830 | +6.418 | +2.051 | +3.211 | +0.619 |
| Z5 | S16 disp@09:50 > p67: no entries before 10:00 | 50764 | -0.020 | -0.107 | +0.011 | -2.360 | -1.054 | -1917.800 | +0.141 | +0.350 | +0.744 | -0.589 | -0.150 | +0.431 | +0.571 |
| Z6 | S16 disp@09:50 > p67: no entries before 10:30 | 46822 | -0.026 | -0.107 | -0.005 | -2.859 | -1.246 | -2099.200 | -0.661 | -0.980 | +0.744 | -2.649 | -1.778 | +0.456 | +0.476 |
| Z7 | S12 gap disp > p67: no entries before 10:30 | 45742 | -0.028 | -0.104 | -0.006 | -2.951 | -1.328 | -2118.800 | -0.852 | -1.040 | +1.077 | -2.886 | -1.835 | +0.132 | +0.476 |
| Z8 | anti: size x clip(S13/med60, 0.5, 2) | 55066 | -0.022 | -0.100 | -0.000 | -3.273 | -0.973 | -2244.000 | -0.178 | -0.220 | +0.939 | -2.048 | -0.257 | -0.098 | +0.524 |
| P1 | per setup/day: stop after 2 losses | 39384 | -0.019 | -0.135 | +0.048 | -1.749 | -1.099 | -1377.000 | +0.255 | +0.250 | -2.875 | +4.171 | -0.230 | +0.739 | +0.476 |
| P2 | per setup/day: stop after 3 losses | 42892 | -0.020 | -0.131 | +0.042 | -2.057 | -1.225 | -1593.200 | +0.060 | +0.060 | -2.462 | +3.401 | -0.483 | +0.603 | +0.476 |
| P3 | per setup/day: stop at -3R closed | 46590 | -0.024 | -0.138 | +0.037 | -2.660 | -1.495 | -1864.400 | -0.444 | -0.500 | -3.272 | +2.837 | -0.498 | -0.390 | +0.381 |
| P4 | per setup/day: stop at -5R closed | 49280 | -0.022 | -0.134 | +0.036 | -2.544 | -1.383 | -1804.600 | -0.142 | -0.170 | -2.882 | +2.648 | -0.094 | -0.191 | +0.429 |
| P5 | max 5 entries/setup/day | 19753 | -0.036 | -0.133 | +0.040 | -1.672 | -3.111 | -894.900 | -1.961 | -1.280 | -3.303 | +2.979 | -2.256 | -1.665 | +0.333 |
| P6 | max 10 entries/setup/day | 28782 | -0.026 | -0.123 | +0.047 | -1.790 | -2.397 | -1069.300 | -0.724 | -0.500 | -2.253 | +3.761 | -0.946 | -0.502 | +0.429 |
| P7 | max 20 entries/setup/day | 37231 | -0.026 | -0.127 | +0.048 | -2.296 | -2.262 | -1391.500 | -0.695 | -0.530 | -2.751 | +3.917 | -0.512 | -0.879 | +0.333 |
| P8 | book daily stop -10R closed | 42211 | -0.012 | -0.134 | +0.048 | -1.160 | -0.680 | -1277.300 | +1.188 | +1.070 | -0.872 | +4.630 | +2.067 | +0.309 | +0.667 |
| P9 | book daily stop -20R closed | 48751 | -0.019 | -0.132 | +0.032 | -2.198 | -1.113 | -1841.400 | +0.218 | +0.300 | -1.666 | +2.328 | +0.638 | -0.202 | +0.524 |
Book T
| rule | desc | n | exp_r | exp_up | exp_down | day_mean_raw | sharpe_raw | maxdd_raw | d_mean | d_t | d_up | d_down | d_h1 | d_h2 | d_month_pos |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | base exits (setup geometry, flatten 15:55) | 191260 | -0.045 | -0.174 | +0.059 | -20.273 | -3.688 | -9129.200 | +0.000 | +nan | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| E1 | ATR5 trail 1.0x, no target | 191260 | -0.062 | -0.099 | -0.038 | -27.893 | -13.201 | -11816.100 | -7.619 | -2.210 | +32.909 | -46.623 | -2.654 | -12.584 | +0.381 |
| E2 | ATR5 trail 1.5x, no target | 191260 | -0.065 | -0.135 | -0.008 | -29.049 | -8.697 | -12321.800 | -8.775 | -2.800 | +17.230 | -32.139 | -3.764 | -13.787 | +0.333 |
| E3 | ATR5 trail 2.0x, no target | 191260 | -0.068 | -0.171 | +0.020 | -30.410 | -6.351 | -12933.900 | -10.136 | -3.150 | +1.343 | -18.656 | -5.114 | -15.158 | +0.143 |
| E4 | time stop 30 min if MFE < +0.25R | 191260 | -0.043 | -0.140 | +0.032 | -19.461 | -4.517 | -8357.400 | +0.812 | +0.620 | +15.101 | -13.117 | +2.434 | -0.810 | +0.524 |
| E5 | time stop 60 min if MFE < +0.25R | 191260 | -0.043 | -0.157 | +0.046 | -19.479 | -3.924 | -8632.700 | +0.795 | +1.090 | +7.645 | -6.346 | +1.584 | +0.005 | +0.571 |
| E6 | time stop 90 min if MFE < +0.25R | 191260 | -0.045 | -0.166 | +0.053 | -20.098 | -3.834 | -8953.000 | +0.175 | +0.370 | +3.628 | -3.086 | +0.994 | -0.643 | +0.524 |
| E7 | structural stop (30-min swing), risk = swing distance | 191260 | -0.087 | -0.184 | -0.009 | -39.266 | -8.124 | -16736.700 | -18.992 | -9.190 | -4.189 | -32.499 | -17.815 | -20.170 | +0.048 |
| E8 | structural stop (60-min swing), risk = swing distance | 191260 | -0.084 | -0.184 | -0.003 | -37.822 | -7.736 | -16146.000 | -17.549 | -8.700 | -4.278 | -29.642 | -16.556 | -18.542 | +0.048 |
| E9 | scale out 1/2 at +1R, rest BE to 15:55 | 191260 | -0.052 | -0.201 | +0.075 | -23.216 | -3.934 | -10196.300 | -2.943 | -2.030 | -11.433 | +7.377 | -2.266 | -3.620 | +0.238 |
| E10 | breakeven after +0.75R (target kept) | 191260 | -0.048 | -0.168 | +0.049 | -21.545 | -4.177 | -9527.800 | -1.272 | -2.120 | +2.575 | -5.049 | -0.954 | -1.590 | +0.286 |
| E11 | flatten 15:30 | 191260 | -0.047 | -0.167 | +0.049 | -20.957 | -3.876 | -9093.100 | -0.684 | -0.740 | +3.253 | -4.789 | -0.438 | -0.930 | +0.333 |
| Z1 | size x clip(med60/S13 SPY ATR%, 0.5, 2) | 191260 | -0.044 | -0.174 | +0.066 | -19.910 | -3.802 | -9158.900 | +0.710 | +0.470 | +3.206 | +2.811 | +2.724 | -1.304 | +0.429 |
| Z2 | size x clip(med60/S14 SPY OR width, 0.5, 2) | 191260 | -0.039 | -0.188 | +0.076 | -18.407 | -3.118 | -8493.500 | +2.664 | +1.570 | -1.530 | +8.155 | +2.074 | +3.255 | +0.619 |
| Z3 | skip if S13 > trailing p67 | 117692 | -0.047 | -0.175 | +0.057 | -13.007 | -3.629 | -5919.000 | -0.864 | -0.230 | +8.716 | -1.611 | +3.449 | -5.178 | +0.238 |
| Z4 | skip if S14 > trailing p67 (same tod) | 118793 | -0.035 | -0.195 | +0.094 | -9.777 | -2.506 | -4498.600 | +4.533 | +1.360 | -1.354 | +15.477 | +4.145 | +4.920 | +0.524 |
| Z5 | S16 disp@09:50 > p67: no entries before 10:00 | 184103 | -0.045 | -0.174 | +0.060 | -19.428 | -3.568 | -8832.600 | +0.091 | +0.160 | +0.145 | +0.421 | -0.980 | +1.162 | +0.524 |
| Z6 | S16 disp@09:50 > p67: no entries before 10:30 | 175754 | -0.046 | -0.175 | +0.059 | -19.076 | -3.528 | -8670.600 | -0.485 | -0.500 | +0.215 | -0.003 | -2.268 | +1.297 | +0.381 |
| Z7 | S12 gap disp > p67: no entries before 10:30 | 175638 | -0.047 | -0.174 | +0.058 | -19.216 | -3.581 | -8658.100 | -0.652 | -0.610 | +0.424 | -0.459 | -1.882 | +0.578 | +0.429 |
| Z8 | anti: size x clip(S13/med60, 0.5, 2) | 191260 | -0.047 | -0.175 | +0.054 | -23.429 | -3.171 | -10374.400 | -0.769 | -0.440 | -4.921 | -1.835 | -3.838 | +2.300 | +0.667 |
| P1 | per setup/day: stop after 2 losses | 71886 | -0.041 | -0.175 | +0.049 | -6.902 | -3.200 | -3300.900 | +1.910 | +0.550 | +2.494 | -4.197 | -1.141 | +4.962 | +0.619 |
| P2 | per setup/day: stop after 3 losses | 85199 | -0.048 | -0.181 | +0.048 | -9.565 | -3.883 | -4410.000 | -1.199 | -0.400 | -0.249 | -5.051 | -5.541 | +3.142 | +0.476 |
| P3 | per setup/day: stop at -3R closed | 124164 | -0.052 | -0.194 | +0.059 | -15.078 | -4.143 | -6682.500 | -2.952 | -1.250 | -1.875 | +1.554 | -7.729 | +1.825 | +0.381 |
| P4 | per setup/day: stop at -5R closed | 142475 | -0.051 | -0.196 | +0.058 | -16.940 | -4.134 | -7516.900 | -2.467 | -1.300 | -3.330 | +0.550 | -6.482 | +1.547 | +0.429 |
| P5 | max 5 entries/setup/day | 35976 | -0.048 | -0.148 | +0.034 | -4.047 | -4.943 | -1790.800 | -1.242 | -0.370 | +10.029 | -12.999 | -0.068 | -2.415 | +0.429 |
| P6 | max 10 entries/setup/day | 56874 | -0.049 | -0.159 | +0.033 | -6.578 | -5.056 | -2881.400 | -1.846 | -0.640 | +5.665 | -13.171 | -0.815 | -2.878 | +0.333 |
| P7 | max 20 entries/setup/day | 83692 | -0.051 | -0.164 | +0.036 | -10.078 | -5.072 | -4404.800 | -2.758 | -1.070 | +3.424 | -11.628 | -3.301 | -2.215 | +0.333 |
| P8 | book daily stop -10R closed | 100024 | -0.044 | -0.212 | +0.078 | -10.241 | -3.146 | -4843.300 | +0.691 | +0.200 | +0.256 | +11.747 | -4.283 | +5.664 | +0.524 |
| P9 | book daily stop -20R closed | 133192 | -0.045 | -0.215 | +0.071 | -14.055 | -3.557 | -6288.700 | +0.090 | +0.040 | -2.769 | +8.558 | -2.729 | +2.910 | +0.476 |

`d_*` = variant minus base daily P/L (risk-matched for Z/P rules, amendment 1.7). The heat_fade_short table (58
rows, all gates) is in results.csv (`part = heat_fade_short`).

### 2.5 What the live system would need
- **Nothing is proposed for live.** No rule passed. No runner change is recommended; nothing in mcf/ or config/
  was edited.
- **Forward-test spec (Testing only, if the lead wants to track the closest candidate, Z4).** Backlog
  sw-w4-z4-orwidth-sitout. This is a spec; nothing is staged. Today it would be a risk overlay, not a setup:
  1. **Market-context feature** (computed once per bar for all setups, in the runner or a new
     `mcf/execution/context.py`):
     - `spy_orw(t) = (SPY session high - SPY session low, 09:30 .. bar close t) / SPY daily ATR(14)`. The ATR is the
       prior 14 sessions' true range, as `heat_frame.atr_d`.
     - It is evaluated at 5-minute bar closes, on the same grid as the setups' decision bars.
  2. **Reference:**
     - `p67(t)` = the 67th percentile of `spy_orw` at the same bar time over the previous 60 sessions (min 20;
       without that history the gate is off).
     - Persist it daily, e.g. `data/context/spy_orw_ref.parquet`, rebuilt pre-open from the 1-minute cache.
  3. **Gate:** in `Runner.step`, before `risk.check`, reject the signal with reason `"orw sit-out"` when
     `spy_orw(t) > p67(t)`, for setups whose YAML has `orw_sitout: true`.
     - Also log `spy_orw` and `p67` on every signal (taken or not), so forward data can score the rule without
       look-ahead.
  4. **Config:** `account.orw_sitout_default: false`; per setup `orw_sitout: true|false`. Testing account only;
     the rule-16 backlog and ledger process before any primary change.
  5. **Lab parity:** this is the same quantity as regime1009 S14 (`dist_hod_atr + dist_lod_atr` of SPY's lab
     frame).
- **Exit rules need no runner change to be tried, but they fail.** E4-E6 (time stop if MFE < x) and E10
  (breakeven) map onto the existing Signal fields `time_stop_min` / `time_stop_min_r` / `be_at_r`, and the trail
  onto `trail_r` / `trail_after_r`. An ATR5-based trail would need a new `trail_atr5_k`, but it failed here, so no
  spec is given for it.
- **Housekeeping for the lead (not a rule change):** the config-order pre-emption in 2.2 means RW2-FD / RW4-FD /
  MF5-FD / RW6-FD / RW6G1(-FD) get few or no forward trades. Whether that matters is the owner's call: the runner
  could let a different setup trade a symbol another setup already holds, or record the blocked signals as shadow
  trades.

### 2.6 Files
`NOTES.md` (this), `results.csv` (114 configurations + 2 book bases + 2 heat bases; book and heat parts),
`build_trades.py`, `sim.py` (1-minute engine), `analyze.py`. Git-ignored `data/`: trades_lab.parquet,
sim.parquet, reconcile.csv, per_setup_exits_{P,T}.csv, daily_{P,T}.parquet, report.json, tables.md, logs (45 MB).

Backlog (appended 2026-10-10): sw-w4-book-exits (failed, 22), sw-w4-book-volsize (failed, 16), sw-w4-z4-orwidth-sitout
(idea, forward tracking only), sw-w4-book-process (failed, 18), sw-w4-hfs-exit-size (failed, 58; lineage 19,706),
sw-w4-config-order-preemption (observation). `python -m pytest tests/test_backlog.py` passes.
