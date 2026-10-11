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
(none yet)
