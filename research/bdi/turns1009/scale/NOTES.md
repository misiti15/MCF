# T2 scale-up: label every intraday turn, then diagnose which factors were present (owner idea 2026-10-11)

*Educational only - not financial advice. Lab backtests on the open two-year history only; nothing here is a live or
paper result.*

Owner (2026-10-11): "look at the finished house and see what blocks built it" - start from the actual swings (big
intraday turns where a long or short entry would have been great), diagnose which factors were present at those
moments, and turn recurring combinations into setups. Another worker studies the owner's five 2026-10-09 cases; this
study does it systematically: label EVERY turn automatically across the open two-year history and measure which
factor combinations, known at that bar's close, separate real turns from look-alike moments that did not turn - and,
what matters, whether entering on them makes money after production costs and after removing the market.

**Section 1 (pre-declaration) was written on 2026-10-11 before any label, feature or trade of this study was
computed.** Seen beforehand: published numbers of earlier studies only (RESCORE.md, swarm1010 W2 NOTES). Section 1 may
change only by dated amendments in section 1.9.

## 1. Pre-declaration

### 1.1 Data (open history only)
- 1-minute SIP cache `data/cache_hist/1Min` (RTH 09:30-15:59), resampled to 5-minute bars with `mcf.data.bars.resample`
  (the history2y pipeline), bar-close tod 09:35..15:55 (77 bars). Locked-block rows (2024-11-01..2025-02-28) are
  dropped right after each symbol's load, before any computation; only the 426 open sessions of `lib.daily()` are kept.
  `MCF_HIST_ALLOW_LOCKED` is never set. 1-minute bars are not used beyond building the 5-minute bars (scope).
- Per symbol-day daily ATR (`atr_d`), prior close, prior-day high/low and point-in-time `adv20` are read from the open
  lab frames (`lib.load_month`, first row per symbol-day: prior close = day open / (1 + gap/100),
  pdh = close + dist_pdh_atr x atr_d, pdl = close - dist_pdl_atr x atr_d), so nothing is derived from locked data
  (the frames were built by the lead). R = 0.25 x atr_d, as in the lab.
- Indicators run on each symbol's continuous RTH 5-minute series (sessions concatenated, as the lab frames do). Missing
  5-minute bars: close forward-filled, O/H/L = close, volume 0, and the bar is not eligible as an entry.
  The first sessions of 2025-03 warm up on 2024-10 bars (open data, a known approximation).
- Betas: `beta_spy` [session, symbol] from prior 60 open sessions' open-to-close returns, clipped [0, 3], copied from
  the W2 study (`research/swarm1010/w2_neutral/data/betas.npz`, NOTES 1.2 there). Undefined for the first ~30 open
  sessions; those trades are dropped from the hedged line only (the raw line keeps them; both n are reported).
- Population (entries and turn statistics): non-ETF symbols (W2's ETF list) with point-in-time adv20 >= 95M (the
  Testing account's min_adv), atr_d > 0. Market context uses SPY and QQQ; breadth uses every non-ETF symbol with a bar.
- Splits: **train** = open sessions <= 2025-12-31 (2024-10, 2025-03..2025-12); **valid** = 2026-01-02..2026-10-07.
  Regimes: `lib.regimes()` (universe median open-to-close terciles). Walk-forward: `gates.walk_forward`, locked months
  excluded.

### 1.2 Turn labels (hindsight; used only as outcomes)
For one symbol-session with 5-minute H/L and R:
- **Long turn (swing low) at bar i, size k, approach m, tolerance a:**
  (1) approach: let p = the last bar before i in the session with low < low_i (none -> session start); the highest
  high of bars p+1..i-1 is >= low_i + m R (a move of >= m R into the extreme, of which bar i is the lowest low);
  (2) follow-through: the first later bar j (<= 15:55) whose high >= low_i + k R comes strictly before the first later
  bar whose low < low_i - a R (a bar that does both counts as adverse first).
- **Short turn (swing high)**: the mirror image.
- Grid: k in {2, 3, 4}; m = 2; a = 1 (the owner's "before any adverse move of 1 R": the label used for diagnosis).
  a = 0 (strict: bar i stays the extreme until +k R) is used only to count distinct turns.
- **Turn size** (strict labels): the largest favourable excursion from the extreme before the first bar beyond the
  extreme (or 15:55), in R.
- **Close-based labels** for the market-neutral control (k in {2, 3}, m = 2, a = 1, same rules on closes instead of
  H/L): raw x_t = ln C_t, and residual x_t = ln C_t - beta_spy x ln SPY_t (the stock's own move), R in log units =
  R / prior close.
- **SPY swings**: SPY strict turns with SPY's own R (0.25 x SPY atr_d), same k. A stock turn "coincides" with the
  market when an SPY turn of the same side has its extreme within +-2 bars (+-10 minutes). Chance reference: the
  share expected if SPY turn bars were placed independently (SPY turn-bar density x 5).
- **Diagnosis target** at entry bar t (09:50..15:00 bar close): Y_t(k) = a long (short) turn bar at t, t+1 or t+2.
  Base rate = mean Y over eligible bars. A condition's **lift** = P(Y | condition) / base rate; **coverage** = share
  of all Y = 1 bars it catches; **false-alarm rate** = 1 - P(Y(2) | condition).

### 1.3 Factor panel (known at the bar's close; long reading / short mirror)
RSI is MarcoFlow's simple RSI (as frames `rsi`, `rsi5`). R = 0.25 x atr_d; Rs / Rq = 0.25 x SPY / QQQ atr_d.
LOD/HOD include the current bar. "both" = the same condition for both sides.

| id | long condition | short mirror |
|---|---|---|
| O1 rsi2_5 | RSI2 <= 5 | >= 95 |
| O2 rsi2_10 | RSI2 <= 10 | >= 90 |
| O3 rsi5_20 | RSI5 <= 20 | >= 80 |
| O4 rsi14_30 | RSI14 <= 30 | >= 70 |
| O5 stoch14 | Stoch %K(14) <= 10 | >= 90 |
| O6 wr5 | Williams %R(5) <= -95 | >= -5 |
| O7 cci20 | CCI(20) <= -150 | >= 150 |
| O8 mfi14 | MFI(14) <= 20 | >= 80 |
| O9 macdh_turn | MACD(12,26,9) hist < 0 and rising vs prior bar | > 0 and falling |
| O10 macd_div | low <= min(low of prior 12 bars), hist < 0 and hist > min(prior 12 hist) | mirror |
| O11 rsi_div | low <= min(prior 20 lows) and RSI14 > min(prior 20 RSI14) + 5 | mirror |
| B1 bb_out | Bollinger %B(20,2) <= 0 | >= 1 |
| B2 bb_wide | bandwidth >= 1.5 x median of prior 50 bars (both) | both |
| B3 kelt2 | close <= EMA20 - 2 x ATR14(5-min) | >= EMA20 + 2 x ATR14 |
| B4 vwap2sd | close <= session VWAP - 2 sd (volume-weighted) | >= + 2 sd |
| B5 vwap1sd | close <= VWAP - 1 sd | >= + 1 sd |
| T1 ema_dn | EMA9 < EMA21 | > |
| T2 ema9_reclaim | close > EMA9 and prior close <= prior EMA9 | mirror |
| T3 sma50 | close < SMA50 (5-min) | > |
| T4 sma200 | close < SMA200 (5-min) | > |
| T5 adx_trend | ADX14 >= 25 and -DI > +DI | +DI > -DI |
| T6 adx_range | ADX14 <= 20 (both) | both |
| V1 atr_exp | mean TR(5) / mean TR(50) >= 1.5 (both) | both |
| V2 rvol2 | volume / mean volume of the same bar over the prior 20 sessions (min 10) >= 2 (both) | both |
| V3 rvol3 | same >= 3 (both) | both |
| V4 climax | volume >= 3 x mean of prior 20 bars and a down bar (close < open) | up bar |
| V5 obv_div | low <= min(prior 12 lows) and OBV > min(prior 12 OBV) | mirror |
| V6 cmf | CMF(20) > 0.1 | < -0.1 |
| K1 wick | lower wick >= 0.5 of range, range >= 0.5 R | upper wick |
| K2 engulf | bullish engulfing (up bar, prior down, close >= prior open, open <= prior close) | bearish |
| K3 hammer | lower wick >= 2 x body, upper wick <= body, range >= 0.4 R | shooting star |
| K4 rev3 | up bar after 3 lower closes | down bar after 3 higher closes |
| K5 consec4 | 4 lower closes in a row (incl. this bar) | higher |
| K6 consec6 | 6 lower closes in a row | higher |
| K7 close_top | close in top third of the bar, range >= 0.5 R | bottom third |
| K8 brk_prev | close > prior bar high | close < prior bar low |
| K9 bigbar | range >= 1 R (both) | both |
| L1 speed2 | close - close 3 bars ago <= -2 R | >= +2 R |
| L2 speed3 | <= -3 R | >= +3 R |
| L3 at_lod | (close - LOD) <= 0.05 atr | (HOD - close) <= 0.05 atr |
| L4 new_lod | this bar's low is a new session low | new high |
| L5 near_pdl | abs(close - prior-day low) <= 0.1 atr | prior-day high |
| L6 below_pdl | close < prior-day low | > prior-day high |
| L7 open05 | close - day open <= -0.5 atr | >= +0.5 atr |
| L8 open1 | <= -1 atr | >= +1 atr |
| L9 pclose1 | close - prior close <= -1 atr | >= +1 atr |
| L10 gap05 | day open - prior close <= -0.5 atr | >= +0.5 atr |
| L11 off_hod1 | HOD - close >= 1 atr | close - LOD >= 1 atr |
| L12 range1 | HOD - LOD >= 1 atr (both) | both |
| M1 spy_fall | SPY close - SPY close 3 bars ago <= -1 Rs | >= +1 Rs |
| M2 spy_nofall | SPY 3-bar move >= 0 | <= 0 |
| M3 spy_rsi2 | SPY RSI2 <= 10 | >= 90 |
| M4 spy_lod | SPY within 0.05 SPY atr of its LOD | of its HOD |
| M5 qqq_fall | QQQ 3-bar move <= -1 Rq | >= +1 Rq |
| M6 rs_flush | (stock 6-bar return - beta x SPY 6-bar return) x close / R <= -1.5 | >= +1.5 |
| M7 rs_strong | same >= +1 | <= -1 |
| M8 breadth_lo | share of non-ETF symbols above session VWAP <= 30% | >= 70% |
| M9 breadth_turn | breadth - breadth 2 bars ago >= +5 points | <= -5 |
| M10 spy_dayup | SPY close >= SPY day open | <= |
| D1..D4 tod | bar close in [09:50,10:30), [10:30,12:00), [12:00,14:00), [14:00,15:00] (both) | both |

63 conditions per side (M6/M7 need beta; undefined beta -> condition false).

### 1.4 Configurations (counted)
- **Stage A**: every single (63) and every pair (63 x 62 / 2 = 1,953) per side = 2,016 x 2 sides = **4,032 conditions**.
- **Stage B (triples)**: per side, the 12 singles with the highest train lift for Y(3) (min 5,000 train fires) -> all
  220 triples of them = **440 conditions**. Chosen on train only.
- Each condition is traded with 4 exits {t1s1, t05s1, t1s05, hold-to-15:55-close} x {raw, SPY-hedged} =
  8 trade lines. **N = (4,032 + 440) x 8 = 35,776** -> t bar = max(2.0, sqrt(2 ln N)) = **4.58** (live-probation floor
  2.0). The diagnosis statistics (lift, coverage, false alarms) are reported for every condition and are not counted
  as extra trade configurations.

### 1.5 Trades
- Entry at the close of the first qualifying bar per symbol-day (bar close 09:50..15:00, eligible population).
  R = 0.25 x atr_d. Fixed geometries simulated on the 5-minute bars exactly as `mcf.research.setup_lab._outcomes_asym`
  (later bars only, target vs stop first touch, stop first when both in one bar, timed exit at the 15:55 close), then
  production cost via `gates.prod_r(..., tod=entry tod)` (1c + 1 bps per side with time-of-day entry multipliers,
  exit side free on target, +2c on stops). Parity check (declared): the simulated lab R equals the frame's
  `r_{side}_{geom}` for >= 99% of a sample of (symbol, date, tod) rows.
- Hold-to-close: exit at the 15:55 close; cost = entry side (1c + 1 bps) x tod multiplier + exit side (1c + 1 bps).
- **SPY-hedged** line (market-neutral control): hedged R = stock production R - side x beta x close x
  (SPY_exit / SPY_entry - 1) / R - hedge cost, SPY priced at the 5-minute closes of the entry bar and the stock's exit
  bar; hedge cost = beta x close x (0.01 / SPY_entry + 1e-4) per side, both sides, / R (as W2 1.3).
- Baseline (rule 6): every eligible bar as an entry ("random bar", same side, same window), and the
  first-eligible-bar (09:50) entry per symbol-day.

### 1.6 Statistics and gates
- Per line: n, sessions, exp R, day-clustered t (`gates.summary` formula), win rate, ex-best-day, busiest session
  share, train / valid exp, up / flat / down exp (n), walk-forward positive share.
- **Live-probation bar** (swarm1010 RULES.md) plus this study's try-count bar: n >= 150; exp > 0 in up AND down
  sessions (n >= 30 each); day-clustered t >= 4.58; walk-forward positive share >= 0.6; plateau neighbours' mean exp
  > 0; ex-best-day > 0; busiest session <= 10% of trades; exp > 0 in train AND valid. A raw (single-leg) line passing
  everything -> lab module + verification. A hedged-only pass -> two-leg spec, no module.
- **Plateau neighbours** of a condition: the same side and exit with one condition dropped (pairs, triples), or one
  condition swapped for its declared threshold sibling (O1<->O2, O3<->O4, V2<->V3, K5<->K6, L1<->L2, L7<->L8,
  B4<->B5, M6<->M7 not a sibling).
- **Market-neutral diagnosis**: for each condition, lift for the raw close-based label vs the residual close-based
  label (k = 3). A signature "predicts the stock's own turn" only if its residual lift is >= its raw lift x 0.8 and
  > 1.2; reported for every condition, not a gate.

### 1.7 Reports (section 2)
Failures first; config counts; turn base rates per k and side; distinct turns per stock-day (all bars and the
09:50-15:00 window) and sizes; SPY-coincidence share vs chance; the top conditions by lift (diagnosis) and by
trade expectancy, each with its after-cost, hedged and residual-lift numbers; any line passing the bar.

### 1.8 Machine limits
One process, float32 per-symbol arrays, aggregates per (condition, session) only; data/ < 1 GB; intermediates
deleted at the end.

### 1.9 Amendments
**A1 (2026-10-11, lead's request after T1 `CASES.md`; written while stage A was still running, before any
configuration of this study was scored).** Adds stage C, the T1 confluence signatures S1-S5, on 1-minute bars.
- Data: the 1-minute cache `data/cache_hist/1Min` already covers the whole open history (2024-09..2026-10, locked
  rows dropped on load), so the 1-minute variants run on all 426 open sessions and do not need the shorter
  `data/cache/1Min` window. Same population and R (0.25 x atr_d) as 1.1. Entries are taken at the close of a
  1-minute bar, bar close 09:50..15:00. Premarket levels are not available (RTH cache) and are left out.
- Own-stock percentiles: the quantile over the same stock's previous 20 open sessions (all RTH bars; at least 10
  sessions), nothing from the current session.
- **1-minute trigger trig1** (long / short mirror): the 1-minute MACD(12,26,9) histogram crossed from <= 0 to > 0
  within the last 3 bars (incl. this one), OR bullish engulfing on this bar (up bar, prior down, close >= prior open,
  open <= prior close), OR hammer (lower wick >= 2 x body, upper wick <= body, range > 0).
- **S1 stretched + roll** (C3b): last completed 5-minute bar's VWAP z ((close - VWAP) / volume-weighted sd) <= own p10
  AND its 5-minute RSI14 (simple) <= own p10 (short: both >= p90), AND trig1.
- **S2 1-minute flush** (C6): ROC10 in ATR ((close - close 10 bars ago) / atr_d) <= own p10 (short >= p90) on this bar
  AND trig1; longs also need 1-minute RSI2 (simple) <= 10 and close < 1-minute EMA9 on at least one of the last 3 bars.
- **S3 flush into a level**: S2 AND this bar's low (short: high) within 0.10 x atr_d of at least one of: the session
  low as of 30 minutes earlier (short: high), the day open, the prior close, the prior-day low (short: high), the
  nearest multiple of $5. Read against S2 alone: does the level add anything?
- **S4 market-confirmed**: S2 AND a causally confirmed swing low (short: high) of SPY or the stock's sector ETF (W2
  sector map; SPY when none) in the last 6 minutes: at minute u the ETF's bar u-1 low is the lowest low of bars
  u-30..u-1, bar u has a higher low and closes above the highest high of bars u-3..u-1 (mirror for highs).
- **S5 confluence count**: the number of this study's 59 non-time 5-minute flags (1.3 minus D1-D4) lit for the side on
  the last completed 5-minute bar >= own p97 AND trig1. (T1 counted ~99 flags; this panel is the one available here.)
- Exits: **fixed 1R** (t1s1 on 1-minute bars, stop first inside a bar, timed exit at the 15:55 close, `gates.prod_r`
  with tod costs) and **trail after 1R** (initial stop -1R; once a bar's high reaches +1R the stop ratchets to the
  highest high since entry - 1R, applied from the next bar; stop first; timed exit 15:55; cost: entry side x tod
  multiplier + exit side 1c + 1 bps, +2c on stop exits).
- Taking signals: **all** = every onset with a 15-minute refractory per symbol-side, only when no trade of that
  symbol-side is open; **first** = first signal per symbol-day.
- Raw and SPY-hedged (1.5, SPY 1-minute closes).
- Configurations: 5 signatures x 2 sides x 2 exits x 2 taking rules x {raw, hedged} = **80**. **N = 35,776 + 80 =
  35,856**; the t bar stays 4.58 (sqrt(2 ln 35,856) = 4.579). Same gates as 1.6; plateau for S-lines = the other
  taking rule and the other exit of the same signature and side must have mean exp > 0.
- Per the lead, no configurations are spent on bare level retests, single oscillators, breadth level or heat as a
  timer beyond what stage A already pre-declared (stage A was fixed before T1 reported and is kept unchanged).

**A2 (2026-10-11, owner clarification relayed by the lead; written after stage A (singles + pairs) had been scored
and stage C computed, before stage B was scored and before anything below was computed).** Stage A's R-unit labels
are kept as the secondary view; they are not re-labelled in place. Instead a new **stage D** applies the owner's
definitions:
- **Percent turn labels** (on log prices, otherwise as 1.2): a long turn at bar i is preceded by a move of >= 0.5%
  into the extreme (m = 0.5%), and from the extreme the high reaches +0.5% before the low goes below the extreme by
  X, with **X in {0.25%, 0.35%}**; strict version (X = 0) for counting distinct turns and sizes (in %). Short mirror.
  Diagnosis target Y_t = a turn bar at t, t+1 or t+2 as before. Turn statistics count only turns whose extreme bar
  closes >= 09:50 (and <= 15:55), with a time-of-day histogram (30-minute buckets).
- **Entry window** unchanged: bar close 09:50..15:00 (already excludes 09:30-09:50).
- **Context panel extended by 7 conditions** (prior day and earlier session; long reading / short mirror), appended
  after D4 (indices 63-69):
  P1 pd_down: prior-day open-to-close <= -0.5 atr / >= +0.5 atr;
  P2 pd_range: prior-day range >= 1.2 atr (both);
  P3 pd_weak_close: prior-day close in the bottom 25% of its range / top 25%;
  P4 retest_low: this bar's low within 0.05 atr of the session low as of 30 minutes earlier (6 bars) and close above
     it / high within 0.05 atr of the session high as of 30 minutes earlier and close below it;
  P5 session_pct: close <= day open x (1 - 1%) / >= x (1 + 1%);
  P6 move3h: close - close 36 bars (3 hours, spans the prior session) earlier <= -1 atr / >= +1 atr;
  P7 near_pd_extreme_retest: bar low within 0.05 atr of the prior-day low and close above it / high within 0.05 atr of
     the prior-day high and close below it.
  Prior-day open comes from the 5-minute bars of the previous open session, NaN when the previous open session is
  not the previous trading day (the locked gap). Premarket high/low and premarket move are NOT available: the
  two-year cache is RTH only (stated as a gap; T1 had premarket only for 4 stocks x 20 sessions).
- **Configurations of stage D**: singles (70) and all pairs (70 x 69 / 2 = 2,415) per side = 4,970 conditions,
  each traded with 6 lines: percent geometry target +0.5% / stop -0.35% and target +0.5% / stop -0.25% (5-minute
  bars, stop first, timed exit 15:55; cost in bps: entry side (1c + 1 bps) x tod multiplier, exit side free on target,
  else 1c + 1 bps, +2c on stops), plus t1s1, each raw and SPY-hedged. Scored in bps of entry price for the percent
  lines and in R for t1s1. New lines (the 8,064 stage-A t1s1 lines of the 4,032 old conditions are not counted twice):
  4,970 x 6 - 8,064 = **21,756**. **N = 35,856 + 21,756 = 57,612**; **t bar = sqrt(2 ln 57,612) = 4.68**, applied to
  every line of every stage from now on.
- Gates as 1.6. Plateau neighbours as 1.6 (P-conditions have no threshold sibling).

## 2. Results (written after scoring; section 1 changed only by the dated amendments A1 and A2)

**Configurations: 57,612 trade lines scored** (stage A 32,256 + stage B 3,520 + stage C 80 + stage D 21,756 new lines;
stage D's 8,064 repeats of stage-A t1s1 lines are not counted twice). t bar = sqrt(2 ln 57,612) = **4.68**.
**0 of 57,612 lines pass the live-probation bar. No lab module or Testing YAML is staged.** The locked block was never
loaded and `MCF_HIST_ALLOW_LOCKED` was never set. 426 open sessions, 1,116 non-ETF symbols scanned, 352,365
population stock-days (adv20 >= 95M), 22.1M eligible entry bars per side.

### 2.0 Failures and caveats first
- **Gate tally** (lines with n >= 150; `gate_tally.csv`):

  | Stage | Lines | n >= 150 | exp > 0 | t >= 2 | t >= 4.68 | up and down > 0 | WF share >= 0.6 | train and valid > 0 | pass |
  |---|---|---|---|---|---|---|---|---|---|
  | A singles + pairs, R labels, 4 exits x raw/hedged | 32,256 | 31,752 | 265 | 9 | 1 * | 36 | 105 | 58 | 0 |
  | B triples (top-12 train-lift singles) | 3,520 | 3,520 | 183 | 3 | 0 | 53 | 123 | 38 | 0 |
  | C T1 signatures S1-S5, 1-minute | 80 | 80 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
  | D % labels, 70-condition panel, pct and t1s1 exits | 29,820 | 29,418 | 45 | 3 | 2 * | 5 | 17 | 6 | 0 |

  \* `M2 spy_nofall & M5 qqq_fall` (long): QQQ down >= 1 R in 15 minutes while SPY is not down - it fired on a single
  session (busiest = 100%), so its t is degenerate. No other line reaches 4.68.
- **Nothing beats the random-bar baseline after costs, and the hedged line is worse everywhere.** Baselines (every
  eligible bar as an entry, 22.1M per side; `report.py`):

  | Side | Line | exp | up | down | train | valid |
  |---|---|---|---|---|---|---|
  | long | t1s1 (R) | -0.085 | +0.095 | -0.266 | -0.080 | -0.091 |
  | short | t1s1 (R) | -0.074 | -0.254 | +0.106 | -0.094 | -0.055 |
  | long | t1s1 hedged | -0.114 | -0.078 | -0.149 | -0.119 | -0.111 |
  | short | t1s1 hedged | -0.100 | -0.136 | -0.065 | -0.118 | -0.084 |
  | long | +0.5% / -0.35% (bps) | -7.0 | -1.6 | -12.7 | -6.7 | -7.3 |
  | short | +0.5% / -0.35% (bps) | -6.5 | -12.0 | -0.7 | -6.9 | -6.0 |

  Single conditions sit at -0.06..-0.13 R (t1s1) and -6..-10 bps (percent lines), i.e. at the baseline: gross
  expectancy is about zero and the result is the cost.
- **Lift is real and does not pay - the "diagnose then trade" gap.** The factors that are present at turns (big
  speed, big bars, relative flush, new session low, wick) are 5-50x enriched for turn bars, because a turn measured in
  R or % needs volatility and these flag volatility. The same moments are just as likely to continue: entering at the
  bar close, with the turn's extreme still 0-2 bars ahead, gives baseline expectancy. Examples (t1s1, raw):

  | Condition (long) | Fires | P(turn in t..t+2), 2R | Lift 3R | Lift % (X 0.35%) | Coverage 3R | t1s1 exp | hedged |
  |---|---|---|---|---|---|---|---|
  | L2 speed3 (close - close 3 bars ago <= -3 R) | 8,667 | 0.69 | 49.6 | 3.2 | 1.9% | -0.021 | -0.069 |
  | L1 speed2 | 42,130 | 0.54 | 32.7 | 3.0 | 6.2% | -0.085 | -0.115 |
  | K9 big bar (range >= 1 R) | 352,534 | 0.24 | 13.6 | 2.3 | 21.8% | -0.085 | -0.128 |
  | M6 rs_flush (stock - beta x SPY <= -1.5 R in 30 min) | 377,613 | 0.26 | 12.1 | 2.3 | 20.7% | -0.087 | -0.125 |
  | L4 new session low | 1,416,552 | 0.18 | 7.0 | 2.5 | 44.7% | -0.095 | -0.123 |
  | O1 RSI2 <= 5 | 5,848,520 | 0.05 | 2.0 | - | 52.8% | -0.093 | -0.123 |

  False alarms: even the best signature (L2) fires without a 2 R turn within 3 bars 31% of the time, and the common
  ones 75-95%. Full per-condition table for both sides: `singles_diagnosis.csv` (lift for k = 2 / 3 R, coverage,
  false-alarm rate, raw vs residual lift, all 8 trade lines).
- **Market-neutral control.** Residual-label lift / raw-label lift (k = 3 R, close-based) is ~0.9-1.4 for the
  stock-specific signatures (speed, big bar, relative flush 1.26-1.38, consecutive closes), so they do mark the
  stock's OWN turns as well as the market's; but the market conditions (M1 SPY falling 0.37, M5 QQQ falling 0.36,
  M8 breadth low 0.55, M4 SPY at LOD 0.63, M3 SPY RSI2 0.72) mark market turns only. Hedging removes the regime split
  (as W2 found) and leaves every single condition negative (-0.07..-0.21 R hedged, t1s1). The trade P/L of the
  stock-specific part is negative, confirming W2.
- **Best near-misses (not candidates):**
  - `L2 speed3 & M1 spy_fall & M5 qqq_fall` long t1s1 (stage B): n 1,542, +0.209 R, t 2.31 (bar 4.68); train +0.274,
    valid +0.005; up +0.381 / down +0.098; WF 0.64; **busiest session 36% of trades** (a market-crash bounce on a few
    days); hedged +0.135 (t 1.23), WF 0.43. Its pair parent `L2 speed3 & M5 qqq_fall` is +0.183 (t 2.05, valid +0.003,
    busiest 33%). This is "buy the stock that crashed with the index" - market beta concentrated on crash days, not a
    stock turn.
  - `O9 macdh_turn & L2 speed3` hold-to-close (long hedged +0.895 R, n 178, t 2.50; short raw +0.531, t 1.32): tiny
    samples, hold-to-close tails, below the bar.
  - Stage D: best non-degenerate percent line `O6 wr5 & K8 brk_prev` short +0.5%/-0.35%: +2.4 bps, t 1.76, up -3.2 /
    down +8.1 bps - regime.
- **Stage C (T1's S1-S5 on 1-minute bars, all open sessions): all 80 lines negative**, -0.08..-0.17 R, t -4..-26
  (`results_stageC.csv`). Fixed-1R "1R-first" rates are 36-43% (T1 in-sample: 23-28% hit within 60 minutes vs a 12-13%
  base, a different definition). Every long line is positive in up sessions (+0.10..+0.23) and negative in down
  sessions; shorts the mirror; hedged all negative. **The level (S3) adds nothing over S2** (long S2 all/fixed -0.105,
  S3 -0.101; short -0.099 vs -0.089, within noise). **The market-confirmed version (S4)** is the least bad long
  (-0.081, ~80 signals/session) and is still negative after hedging (-0.123). **Trail after 1R is worse than the fixed
  1R target on every signature** (by 0.01-0.035 R). Signal counts: S2 fires ~1,000-1,200 per session (all, 15-minute
  refractory), S1/S5 ~500, S4 80-120.
- **Approximations:** labels and entries on 5-minute bars (stage C on 1-minute); premarket levels are missing (RTH
  cache), so "prior premarket high" retests (TSLA, SPCX) could not be tested; CCI uses the exact mean deviation; the
  first 2025-03 sessions warm up on 2024-10 bars; survivorship as RESCORE.md (today's list applied backwards); betas
  from W2 (undefined for ~30 sessions, which are dropped from the hedged line only).
- **Checks:** simulated lab R equals the frame's `r_{side}_{geom}` on 1,810,812 population rows of 22 symbols
  (99.998%; non-population days are NaN by design); the 1-minute exits use the same rules.

### 2.1 Turn base rates, counts, sizes and market coincidence
**R units** (strict labels: distinct turns; extreme bar 09:50-15:00; `turnstats.npz`):

| k | Long per stock-day | Short per stock-day | Both, per session (population ~830 names) | Median size (R) | p90 size | SPY same-side within +-10 min (long / short) | Chance |
|---|---|---|---|---|---|---|---|
| 2 R | 0.345 | 0.338 | ~565 | 2.9 | 4.9 | 20.6% / 14.9% | 5.4% / 5.0% |
| 3 R | 0.150 | 0.146 | ~245 | 3.9 | 6.1-6.4 | 19.8% / 14.0% | 4.2% / 3.9% |
| 4 R | 0.065 | 0.067 | ~109 | 4.9 | 7.6 | 19.6% / 15.3% | 3.9% / 3.4% |

Diagnosis base rate Y(k) (a 1-R-tolerance turn bar in t..t+2): 2.6% / 1.0% / 0.4% of eligible bars (k = 2 / 3 / 4).

**Percent units (owner's definition, A2; extreme bar >= 09:50; `turnstatsD.npz`):**
- Strict 0.5% turns: **4.95 long + 4.96 short per stock-day**, about **8,000 per session** across the population (median
  8,006; p10 4,603; p90 11,807). With the adverse tolerance: 9.0 / 9.2 per stock-day (X = 0.35%), 8.2 / 8.5 (X = 0.25%).
- Size (move from the extreme before it is broken): median 1.08%, p75 1.8%, p90 3.0%; 54% of turns reach >= 1%. The
  owner's five moves (0.71-2.18%) are typical turns of this kind.
- Time of day (share of turns by extreme-bar close): 09:50-10:00 6% (two bars), 10:00-10:30 15%, 10:30-11:00 12%,
  11:00-11:30 10%, 11:30-12:00 8%, then 6-7% per half hour to 15:30, 15:30-15:55 4-5%.
- Diagnosis base rate Y_t (0.5% turn in t..t+2): 26-28% of all eligible bars - a 0.5% swing is an ordinary event in this
  universe.
- Market coincidence: 11.2% (long) / 10.3% (short) of stock turns have a same-side SPY 0.5% turn within +-10 minutes
  (chance 6.9%); 6.0% / 4.8% with SPY's 2 R turns (chance 3.5% / 3.1%).

**So:** the owner's 80-200 good trades a day exist in hindsight many times over (~110 distinct 4 R turns, ~245 3 R
turns, ~8,000 0.5% turns per session), and 80-85% of them are NOT market turns (only 1.5-4x chance coincidence with
SPY). The problem is not supply. No combination of the factors known at the bar (63-70 conditions, all pairs, the top
triples, T1's five 1-minute signatures) picks them out with positive expectancy after costs: the factors present at
turns are present just as often at continuations, and at the bar close the extreme is not yet known.

### 2.2 Files
- `NOTES.md` (this), `singles_diagnosis.csv`, `results_top.csv` (top 25 lines by t per stage, failures included),
  `gate_tally.csv`, `results_stageC.csv`.
- Code: `common.py` (loaders, panel, labels, exits), `aux.py`, `context.py`, `scan.py` (A/B), `select_triples.py`,
  `scan1m.py` (C), `scanD.py` (D), `score.py`, `score1m.py`, `scoreD.py`, `report.py`.
- `data/` (git-ignored) keeps only `scores_{A,B,D}.parquet` and `turnstats*.npz`; the per-session aggregates and the
  1-minute trade list were deleted after scoring (re-run `scan*.py` to rebuild, ~30 min each).

*Educational only - not financial advice.*
