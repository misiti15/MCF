# pod1022 batch scorer - harness notes

*Educational only - not financial advice.*

`score_batch.py` scores candidate LAB setup modules (the `LabStrategy` format, `mcf/strategies/setups.py`) in one
pass over the open two-year history. The frames are loaded once per month, every module is scored on them, and then
the month is freed. Peak memory is about one month of frames (~1.5-2.5 GB). It never reads the rule-19 locked block
(2024-11-01..2025-02-28), never places orders and never touches secrets.

```
python research/bdi/pod1022/score_batch.py MOD.py [MOD.py ...] --out results.jsonl
    [--ref MOD.py ...]        # reference modules: used only for the duplicate check, not written to --out
    [--ref-config]            # add every `type: lab` setup in config/*.yaml (live, testing, GEN and graveyard)
    [--ref-cache DIR]         # reference trade cache (default .../scratchpad/pod/refcache; '' = off)
    [--ref-max-seconds 60]    # per reference module and month; slower refs are dropped (error 'timeout')
    [--max-seconds 0]         # the same for scored modules (0 = no limit)
    [--trades-dir DIR]        # each module's trades as parquet (date, symbol, tod, r, ctrl[, stop, target])
    [--months 2025-06,2026-02]  # subset of open months (smoke tests); the default is every open month
```
Progress goes to stderr. Writes one JSON line per module.

## Module contract
| name | required | meaning |
|---|---|---|
| `SIDE` | yes | `"long"` or `"short"` |
| `GEOM` | no (default `t1s1`) | `t1s1`, `t05s1`, `t1s05`, `t05s05` = target/stop in R; `hold` = stop 1R, no target; `holdtr` = stop 1R, then a 1R trail once the trade is +1R; `S` = structural (needs `stop_price`); `S+ts2` = `S` plus a 'breakout or bailout' time stop: exit at the close of bar i+`BAILOUT_BARS` (default 2) when no bar since entry made a high (long) / low (short) beyond the entry bar's, and with `BE_AT_R` > 0 the stop moves to entry once the trade is +`BE_AT_R` R (control: `hold`); optional `BAILOUT_REF_R` (added 2026-10-23) replaces the entry bar's high / low by entry + `BAILOUT_REF_R` x R, the form the live runner's `time_stop_min` / `time_stop_min_r` can carry; `S+bar1` = `S` plus a one-bar trailing exit: at the close of the first bar after entry whose low < the previous bar's low (long; mirror short), with the same optional `BE_AT_R` (control: `hold`; added 2026-10-23); `S+x` = `S` plus a module-defined exit: at the close of the frame row `exit_index(f, i, stop, target)` returns (same symbol-day, > i; -1 = none) or of the first path bar with close time >= `EXIT_TOD` (HHMM, 0 = none) or of path bar entry + `MAX_BARS` (0 = none), whichever comes first, after the stop / target checks (control: `hold`; added 2026-10-23, r3_3) |
| `WINDOW` | no (default (950, 1500)) | the entry bar's close time as HHMM, inclusive, clipped to 09:50-15:00 |
| `SYMBOLS` | no | allow-list; the mask then sees only these symbols' rows (and the random control uses them too) |
| `MIN_ADV` | no | adv20 floor in $; the default is 20e6 (the generator universe), or 0 when `SYMBOLS` is set |
| `CONTEXT` | no | informational. Every context column is always in the frame; live, the YAML `context:` must list them |
| `mask(df)` | yes | bool array of len(df): the bars where the setup qualifies |
| `stop_price(f, i)` | GEOM S | the stop price for row position `i` of `f` (the same frame `mask` saw) |
| `target_price(f, i, stop)` | optional, GEOM S | a limit target; without it, the trade holds to 15:55 |

**Trade model.** The scorer takes the first bar per symbol-day where the mask is true, inside WINDOW, with a finite
outcome (no refire). Entry is at that bar's close. R = 0.25 x daily ATR, or |entry - stop| for GEOM S. Every trade is
flat at 15:55. Costs follow RESEARCH_RULES rule 1: 1c + 1 bps per side; the entry side is scaled by the time-of-day
multiplier (x1.4 for entries before 10:30; entries start at 09:50); the exit side is free on a target fill and costs +2c on a stop
fill; all of it is x3 on the extended tier (|gap| >= 20% or price < $5).

**Universe.** adv20 >= $20M, with the live earnings blackout removed (4 trading days either side of a report).

**Frame shape.** `df` holds many symbol-days sorted by symbol, date, tod. Live, the frame is one symbol-day. Any
look-back must be keyed by symbol + date; see `_prev` in `examples/EX1-*.py`. Frames start at the **09:50** bar
(tod 950), so there are no 09:35-09:45 rows: an opening-range module cannot be scored here. A module that needs a
column that is missing should return all False; it then scores 0 trades rather than an error. Do **not** use
outcome columns. The `r_*` / `win_*` columns are removed before `mask` runs.

## Columns available to mask(df)
One row = one completed 5-minute bar of one symbol. "5m" = computed on 5-minute bars (`mcf/research/heat.py`
`heat_frame`, `mcf/research/setup_lab.py` `extra_features`). Typical 1%..99% ranges (June 2025) are in brackets.

**Identity / time**
- `symbol` (str), `date` (datetime.date), `ts` (bar START timestamp, America/New_York)
- `tod` int HHMM of the bar **close** (950 = the 09:45-09:50 bar) [950..1500]

**Price / volatility**
- `close`, `high`, `low` - 5m bar, $ (there is no `open` or raw `volume` column in the history frames)
- `atr_d` - daily ATR(14) as of the prior close, $ (R = 0.25 x atr_d)
- `atrPct` - 5m ATR(14) / close, % [0.05..1.2]
- `gap` - today's open vs the prior close, % [-3.4..4.1]
- `fromOpen` - close vs today's open, % [-4.3..5.0]
- `adv20` - 20-day average dollar volume, $

**Momentum / oscillators (5m)**
- `rsi` RSI(14) [12..89]; `rsi5` RSI(5) [0..100]; `rsiSlope` = rsi - rsi 3 bars ago [-28..27]
- `momentum` = 0.6 x 4-bar % change + 0.4 x 9-bar % change [-1.4..1.6]
- `emaDiff` = (EMA9 - EMA21) / EMA21, % [-0.8..1.0]; `macdPct` = (EMA12 - EMA26) / close, % [-0.84..1.0]

**VWAP / trend**
- `vwapDistPct` - close vs the session VWAP (5m typical price x volume), % [-2.0..2.0]
- `vwapReclaim` - +1 when close is above VWAP and was at or below it 3 bars ago; -1 for the reverse; else 0
- `sma20_dist_pct`, `sma50_dist_pct` - close vs the 5m SMA20 / SMA50, % (these span previous days)
- `sma20_slope_pct` - SMA20 vs SMA20 five bars ago, % [-0.79..0.97]
- `pricePosition` - (close - 20-bar low) / (20-bar high - 20-bar low), 0..1

**Volume / flow (5m)**
- `volumeRatio` - bar volume / its 20-bar average [0.09..3.5]; `vol_climax` is the same quantity
- `volumeSurge` - 5-bar average volume / the previous 15-bar average [0.18..3.6]
- `buyPressure` - signed volume (sign of close - open) over 19 bars / volume, -1..1
- `flow3` - the same over the last 3 bars, -1..1; `flow9prev` - the same over the 9 bars before those, -1..1

**Levels (in daily ATRs)**
- `dist_pdh_atr` = (prior-day high - close) / atr_d (> 0 = below the PDH); `dist_pdl_atr` = (close - PDL) / atr_d (> 0 = above)
- `dist_hod_atr` = (high of day so far - close) / atr_d >= 0; `dist_lod_atr` = (close - low of day) / atr_d >= 0
- `dist_round_atr` - distance to the nearest round number ($5 step >= $100, $1 >= $20, else $0.5) / atr_d

**Candle / divergence**
- `upper_wick`, `lower_wick` - wick / bar range, 0..1
- `bear_div` 1 when the high is a 20-bar high and RSI < its 20-bar max - 5; `bull_div` is the mirror. Both 0/1

**MarcoFlow heat components** (piecewise scores, `mcf/research/heat.py`)
- `volumeHeat` [-10..20], `rsiHeat` [-25..25], `momentumHeat` [-20..20], `priceActionHeat` [-15..15],
  `trendHeat` [-15..15], `macdHeat` [-10..10], `vwapHeat` [-12..12], `heat` = sum + bonuses [-100..100]

**Market context** (point-in-time per (date, tod), `mcf/strategies/lab_context.py`; live these need YAML `context:`)
- `spy_fo`, `qqq_fo` - SPY / QQQ close vs their first 5m open today, %
- `breadth` - share of the universe with close above its own VWAP, 0..1; `breadth_open` - share above its own open
- `qqq_vwap` - QQQ close vs its session VWAP, %. When the stored context has no qqq_vwap, it is filled from the QQQ
  frame's `vwapDistPct`

Indicators that are not in the frame can be computed inside `mask` with `mcf.research.arena.indicators.compute(df,
names=[...])`, as the generator modules do (e.g. `atr_d_pct`, `from_pc_atr`, ADX, ORB flags). It is slower:
40-100 s per module over the full history.

## Output (one JSON line per module)
- `n_`, `avg_r_`, `t_` (day-clustered), `per_day_`, `win_rate_`, `total_r_`, `ctrl_avg_r_`, `excess_`, `active_days_`
  for `train` (<= 2025-12-31), `valid` (2026-01+) and `pooled`
- `ctrl_avg_r_*` is the same-date same-minute mean outcome of the same side x geometry over the module's population.
  This is the random-entry control. GEOM S modules are compared with `hold`. `excess_*` = mean(r - control)
- `best_day`, `best_day_r`, `best_day_share` (best day's R / total R; null when the total <= 0), `avg_r_ex_best_day`
- `by_regime` - Bull / Bear / Choppy / Quiet (regime1022: SPY o2c >= +0.5% / <= -0.5% / within it with a range at or
  above, or below, the 20-day median), each with n, avg_r, day t, and train / valid n and avg_r. These are hindsight labels
- **Duplicate check** (owner: variants are fine, copies of setups already put through the process are not).
  `overlap_max`, `overlap_with`, `overlap_top` (up to 5 of [name, overlap, shared symbol-days]), `dup_flag`.
  overlap = |A and B| / min(|A|, |B|) over the same-side (symbol, date) trades, against the other batch modules and
  the `--ref` / `--ref-config` modules. `dup_flag` is set at >= 0.60 (the generator's OVERLAP_MAX)
- `error` - a load or mask error. The batch goes on without that module
- `mask_seconds` - this module's own time; shared frame loads and path builds are excluded
- `n_days`, `months`, `note`

## Runtime (2026-10-22, shared machine)
- Frames: ~9 s per month to load and build (21 open months, about 3 min). Outcome paths for t05s05 / hold / holdtr / S
  are built once per month the first time a module needs them.
- Module masks: simple column masks take 1-7 s over the full history. Masks that call `arena.indicators.compute` take
  40-100 s.
- `--ref-config` (137 config lab setups) takes ~6 min per month, about 2 h for the full history. The cache makes this
  a one-time cost per history version. One graveyard module (LIQ-orl-sweep, a per-day Python loop) took 848 s on one
  month; the 60 s budget drops it and logs it. Reference keys are cached per (module file, overrides, months), so later
  batches reuse them.

## Checks done (2026-10-22)
- Parity with the Setup Generator quick screen (same universe, costs and control), over the full open history:
  `GEN-261019-01` (t05s05, path sim) scored 469 / 517 trades, +0.1006 / +0.0612R, t 1.63 / 1.16, an exact match.
  `GEN-261019-05` (t1s1) scored 760 / 904 trades at +0.0687R train, t 0.50; the docstring says 760 / 908.
  `GEN-261022-08` (holdtr) scored 470 / 570 at +0.0638R; the docstring says 471 / 570 at +0.0615R. The generator
  stores R as float16, which explains the small differences.
- Duplicate check: on 2026-03, `--ref-config` flagged GEN-261019-01 as a 1.00 copy of its own config entry, and the
  per-reference time budget and the cache were exercised.
- Both `examples/` modules score without error. They are format demos, not candidates; both lose after costs.
