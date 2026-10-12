# Reddit "trade liquidity" study: pre-declaration (BDI, 2026-10-12)

*Educational only - not financial advice. This file was written before any configuration of this study was scored.
Results go in NOTES.md; this file may only gain dated amendments, written before the affected configurations are
scored.*

## 0. Source (paraphrased; the post is not quoted)

An r/Daytrading post (FX, GBPUSD) describes trading "liquidity":
1. Liquidity sits at obvious higher-timeframe swing highs and lows (the poster marks them on 4-hour charts), where
   stops cluster.
2. Wait for price to come back to such a level and run through it (a stop sweep). Then drop to a lower timeframe
   (1 hour) and wait for a "breakdown": price chops in a small range at the level, and the entry is the first candle
   that closes out of that range in the reversal direction (in the example, an hourly close just below the open of
   the large impulse candle that made the sweep high). Trade the reversal: short after a high is swept, long after a
   low is swept.
3. Stop beyond the sweep extreme; target the next significant swing level; only trades with reward:risk >= 2
   (2.5R in the example).
4. Management: if price turns against the trade within the first one to three 15-minute candles, close early for a
   small loss; once price is comfortably in profit, move the stop to break-even; retry on a new breakdown signal
   (the poster needed two attempts).

This is the same family as CWT14 "failed breakout / stop-run reversal" (package B3, `research/bdi/cwt/test_b`,
live in Testing 2 as `CWT14-failbrk-*`) and the earlier Reddit R15 sweep (`bdi-rdt-r15-sweep`). B3 entered on a close
back inside within 3 bars and used the lab geometries (0.25 ATR stop) or the poke extreme with no target. What is new
here: the structural stop at the sweep extreme with a >= 2R target, the break-even move, the early exit, the
"breakdown" triggers (impulse-bar open, post-sweep range break), higher-timeframe levels and a second attempt.

## 1. Data, population, conventions

- Open two-year history: SIP 1-minute bars `data/cache_hist/1Min`, 2024-10-01..2026-10-07 minus the rule-19 locked
  block 2024-11-01..2025-02-28, which is filtered out at read (pyarrow filter) and never loaded. `MCF_HIST_ALLOW_LOCKED`
  is never set. 5-minute bars 09:30-15:55 rebuilt per symbol-day (`prep.py`): open, high, low, close, volume, session
  VWAP on hlc3 (as `mcf.research.heat.heat_frame`).
- Per-day constants from the lab frames (`research/history2y/lib.py`, first row of the day): `atr_d` (R = 0.25 x
  atr_d), `adv20`, `gap`, prior-day high/low (`close +/- dist_pd*_atr x atr_d`). Multi-day levels from
  `research/history2y/data/daily.parquet` (open rows only; a look-back window that spans the dropped locked block is NaN).
- Population: point-in-time `adv20 >= $95M` (the Testing -FD floor), `atr_d > 0`.
- Entries: decision bars closing 09:50-15:00, entry at the signal bar's close (lab convention); flat at the close of
  the 15:55 bar. Next-bar-open entry is re-scored for the finalists as a robustness line (counted).
- Costs (`mcf.research.gates`): 1c + 1 bps per side; the entry side x `gates.tod_cost_mult` (1.4x for entries
  09:50-10:25); the exit side free on target (limit) fills; +2c on every stop fill (including break-even stops); x3 on the
  extended tier (|gap| >= 20% or price < $5). Stops are filled at the stop price, or at the bar open when the bar
  opens through the stop (gap-through). Stop first inside a bar.
- Units: results in lab R = 0.25 x daily ATR (comparable with CWT14 and Testing 1); the structural-R expectancy
  (P/L / |entry - stop|, which is how live sizes positions) is reported next to it.
- Splits: train = open sessions to 2025-12-31; valid = 2026-01-01..2026-10-07; open = all open sessions.
  Day-clustered t (`gates.summary`), regime split, walk-forward (`gates.walk_forward`, locked months excluded),
  ex-best-day, busiest-session share.
- Survivorship caveat as RESCORE.md (today's universe applied to the past).

## 2. Signal definitions (short side; the long side is the mirror at lows)

All on k-minute bars (k = 5, or k = 15 built from three 5-minute bars aligned to 09:30). ATR = daily ATR.

**Levels L** (known before the sweep bar):
- `PD`  prior-day high.
- `OR`  09:30-10:00 high; usable from the first k-bar that ends after 10:00.
- `H60` established intraday swing: the session high through the k-bar 60 minutes or more before bar i, with no
  k-bar in the last 60 minutes trading above it (a high that has held for an hour).
- `D5` / `D20` the highest daily high of the prior 5 / 20 sessions (not available in the live frame; research only).

**Arming:** the previous k-bar close (the day open for the first bar) is below L.

**Sweep:** an armed bar s with high >= L + x*ATR, x in {0.05, 0.15}. Impulse bar = bar s; its open proxy
O_s = the previous k-bar close (the day open for the first bar) - the live frame carries no bar open, so the proxy is
used in research and live alike. Sweep extreme E = the highest high from s to the trigger bar.

**Trigger** (bar j, within 60 minutes of s: j - s < 60/k; otherwise the break is "accepted" and the level must re-arm):
- `lvl`  close back below L (j >= s).
- `open` close below O_s (j > s) - the poster's example ("close below the open of the impulse candle").
- `rng`  breakdown of the post-sweep range: j >= s + 2, close below the lowest low of bars s+1..j-1 and below L.

A trigger before the 09:50 decision bar ends the sweep without a trade. One trade per symbol-day per level and side
(attempt 1 = the first trigger of the day in the window).

**Attempts** `a1` one; `a2` a second trade on the same level after attempt 1 has exited with gross R <= 0, on a new
sweep (re-armed) and trigger, entry by 15:00.

## 3. Exits and management

- Stop `S`: E + 0.05 ATR (structural); trades whose structural risk exceeds 1.0 ATR are skipped. Stop `A`: entry +
  0.25 ATR (the lab R).
- Target (in units of the trade's own risk |entry - stop|): `2R`, `2.5R`; `NL` next level = session VWAP at the signal
  bar, only if it is >= 2R away in the trade direction (otherwise no trade: the poster's >= 1:2 filter); `EOD` none
  (hold to 15:55).
- Management (as `mcf.backtest.engine.simulate` and the live runner's `manage`: updates apply from the next bar):
  `none`; `BE` stop to the entry once the best excursion reaches +1.0 risk; `TS` after 3 bars (15 minutes) in the trade,
  exit at the next bar open if the best excursion is still below +0.25 risk (the poster's early exit; live:
  `time_stop_min: 15`, `time_stop_min_r: 0.25`); `BE+TS` both.

## 4. Grid (counted in full)

| dimension | values | n |
|---|---|---|
| level | PD, OR, H60, D5, D20 | 5 |
| side | short at highs, long at lows | 2 |
| sweep depth x | 0.05, 0.15 ATR | 2 |
| trigger | lvl, open, rng | 3 |
| trigger timeframe k | 5, 15 min | 2 |
| attempts | a1, a2 | 2 |
| stop | S, A | 2 |
| target | 2R, 2.5R, NL, EOD | 4 |
| management | none, BE, TS, BE+TS | 4 |

Intraday grid: 5 x 2 x 2 x 3 x 2 x 2 x 2 x 4 x 4 = **7,680** configurations.
Plus 4 CWT14/B3 replica configurations in this engine (PD high p0.10 short, PD low p0.10 long, PD low p0.05 long,
OR low p0.10 long; close back inside within 3 bars; t05s1, full window), used as an engine check against the
published package B numbers and as the direct comparison. Plus the daily-bar grid (section 6, 32), plus every
finalist robustness re-score. **N for the try-count bar = all of these**; with ~7.7k, t_required = sqrt(2 ln N)
= ~4.23. The related lineages (B3 96, `bdi-rdt-r15-sweep` 128) are reported alongside.

## 5. Selection, bars, incorporation (fixed now)

- Finalists: among configurations with n_train >= 150, the 10 with the highest train day-clustered t and train exp > 0
  (if fewer, all of them), plus the best by train t of each level. All finalists are reported on valid and open,
  failures included. Plateau = the one-step neighbours in x and in k.
- Controls: a random same-side bar per symbol-day in 09:50-15:00 with stop A and target 2R / EOD, and with the BE+TS
  management; the B3 replicas.
- **Research gates** (`gates.verdict`): exp > 0, t >= t_required(N), regime gate, walk-forward >= 0.6.
- **Testing-1 incorporation bar** (the lowered Testing bar of ledger `2026-10-09-owner-testing-batch`, as the lead
  phrased it), only for configurations the live engine can run (level PD / OR / H60, attempts a1, management via the
  YAML keys `be_at_r` / `time_stop_min` / `time_stop_min_r`, the stop via GEOM `S`; a fixed R target needs a small
  opt-in `target_price` hook in LabStrategy that changes no other setup):
  - (a) n_open >= 150, open exp > 0 after costs, day-clustered t_open >= 1.5, train exp > 0 and valid exp > 0,
    ex-best-day > 0, busiest session <= 10% of trades; or, if nothing passes (a),
  - (b) n_open >= 150, open exp >= the median full-day backtest expectancy of Testing 1's -FD setups (-0.046R, the 29
    `exp` notes in config/account_testing.yaml), valid exp > 0, exp > the best live CWT14 configuration (-0.086R),
    and positive in at least one regime (up or down, n >= 30).
  - At most 2 configurations of this family are added, best open t first, distinct level/side.
- Nothing is scored on the locked block; that is the lead's single look.

## 6. Daily-bar version (information only; not eligible for Testing)

10-year daily bars `research/swarm1010/w3_daily/data/daily_2016.parquet`, W3 splits (train 2016-2022, valid1
2023-01..2024-10, valid2 2025-03..2026-10; any trade touching the locked block dropped). Eligible: close >= $5, 20-day
mean dollar volume >= $20M. Sweep day: high >= the prior n-day high (n in {10, 20}) + x*ATR14 (x in {0, 0.1}) and the
close back below that level (long mirror at lows). Entry next open. Exits: hold 1 / 3 / 5 days to the close, or `S2R`
(stop = sweep extreme + 0.05 ATR, target 2R, stop first, gap-through at the open, max 10 days). Costs 1c + 1 bps per
side, shorts 3%/yr borrow. One open position per symbol per configuration. 2 sides x 2 n x 2 x x 4 exits = 32.
Unit: net bps per trade (and R for S2R). Clustered by entry date blocks of 2 x hold days.
