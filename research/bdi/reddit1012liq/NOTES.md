# Reddit "trade liquidity" study (BDI, owner request 2026-10-12)

*Educational only - not financial advice. These are backtest results on the open two-year history only, with costs
included. Nothing here is a paper or live result. The locked block 2024-11-01..2025-02-28 was never loaded. The
plan in `PLAN.md` was written before anything was scored, and it was not amended.*

## Failures first

- **No configuration passes the research gates.** All 7,680 pre-declared intraday configurations were scored:
  - The try-count bar is t >= 4.23 (N = 7,718, including replicas, the daily grid and the robustness re-scores).
  - The best day-clustered t at n >= 150 is **1.07**, from a D5 long that the live frame cannot run.
  - Of the 6,668 configurations with n >= 150, only 61 have positive expectancy, and none has t >= 2.
  - At p = 0.05 about 380 false positives are expected by chance, so the positive tail is consistent with noise.
- **Strict Testing bar (a): 0 pass.** Bar (a) asks for positive expectancy with t >= 1.5, train and valid both
  positive, ex-best-day positive and a busiest session under 10%.
- **The novel management adds nothing.** Median expectancy by management: none -0.113R, break-even (BE) -0.116,
  time stop (TS) -0.103, BE+TS -0.104. By target: 2R -0.102, 2.5R -0.103, hold to 15:55 -0.106, VWAP ("NL") -0.163.
  The structural stop and the 0.25-ATR stop are the same (-0.110 vs -0.107). A second attempt changes nothing
  (-0.108 vs -0.108).
- **What does help a little is the slower trigger.** A 15-minute close beats a 5-minute one (median -0.102 vs -0.113),
  a deeper sweep beats a shallow one (0.15 vs 0.05 ATR), and the "impulse-bar open" trigger beats a close back
  through the level (-0.099 vs -0.116).
- **The best live-runnable cell is about zero after costs, and that is long beta, not a reversal edge.** The cell is
  the opening-range-low sweep with x 0.15 ATR and a 15-minute impulse-open trigger.
  - Result: n 13,335, exp -0.001R, t -0.01.
  - By regime: up sessions +0.59R, down sessions -0.49R. Walk-forward share 0.47. Ex-best-day -0.035R.
  - Survivorship (today's universe applied to the past) favours longs.
- **The two Testing 1 additions met only the pre-declared lowered bar (b)** (PLAN.md section 5). Neither is a
  validated edge (see "Incorporation").
  - The first configuration by the bar's own ordering was excluded by hand: a PD-high short with A stop and NL
    target. It has 54% of its trades on one session, and its ex-best-day is -0.66R. This is a tightening of the rule,
    stated here.
- **Daily-bar version (information only):** every short is negative in every split (-6 to -60 bps per trade). The
  longs' 3-5 day holds earn +3 to +54 bps, which is the market's drift over a bull decade. No excess-return control
  was run on them. Their S2R R-means at x = 0 are distorted by trades with a near-zero risk.

## 1. The strategy (paraphrased) and the translation

**What the poster does (FX, GBPUSD).**
1. Mark the obvious 4-hour swing highs and lows, where stops cluster.
2. Wait for price to run through one of them.
3. On the 1-hour chart, wait for price to chop at the level and for a candle to close out of that range in the
   reversal direction. In the example, the close is just beyond the open of the impulse candle that made the sweep.
4. Trade the reversal. The stop goes beyond the sweep extreme, the target is the next swing level, and only trades
   with reward:risk >= 2 are taken.
5. Close early if price turns against the trade within one to three 15-minute candles. Move the stop to break-even
   once the trade is comfortably in profit. Retry on a new breakdown.

**MCF translation (PLAN.md sections 1-3).**
- Universe and timing: US stocks with adv20 >= $95M, 5-minute bars, entries 09:50-15:00 at the signal bar's close,
  flat at 15:55.
- Costs: `gates` production costs with the time-of-day entry multiplier, a +2c stop fill, and x3 on the extended
  tier. A bar that opens through the stop fills at its open.
- Levels:
  - prior-day high/low;
  - 09:30-10:00 opening range;
  - "H60": a session extreme that has held for 60 minutes (the intraday higher-timeframe proxy);
  - 5-day and 20-day swing levels.
- Sweep: the bar trades x ATR beyond the level, after the previous close was inside it.
- Triggers, which must come within 60 minutes on 5- or 15-minute bars:
  - `lvl`: a close back through the level;
  - `open`: a close beyond the impulse bar's open (proxy: the prior bar's close; the live frame has no bar open);
  - `rng`: a close out of the post-sweep range.
- Stops: `S` sits at the sweep extreme +/- 0.05 ATR (skipped if more than 1 ATR away); `A` is 0.25 ATR.
- Targets: 2R, 2.5R of the trade's own risk, VWAP when it is >= 2R away, or none.
- Management:
  - BE: the stop moves to the entry at +1R;
  - TS: exit at the next open if the trade is not +0.25R after 15 minutes;
  - BE+TS: both.
- Attempts: 1 or 2. The second attempt comes after a losing first trade.

## 2. Grid and counts

| part | configurations |
|---|---|
| intraday grid: 5 levels x 2 sides x 2 x x 3 triggers x 2 timeframes x 2 attempts x 2 stops x 4 targets x 4 management | 7,680 |
| CWT14/B3 replicas in this engine | 4 |
| daily-bar grid (`daily.py`) | 32 |
| robustness re-scores of the 2 picks (next-bar-open entry) | 2 |
| **N** | **7,718** -> t_required 4.23 (4.24 with the B3 96 + R15 128 lineage) |

**Engine check.** The B3 replicas reproduce the published package B trades:
- PDL p0.10 long t05s1: n 37,479, -0.085R here vs n 37,499, -0.086R in package B.
- PDL p0.05: n 66,859, -0.087R here vs n 66,875, -0.088R.

Random same-side bar baselines (stop A): -0.087 to -0.097R.

## 3. Finalists (PLAN 5: the top 10 by train t with n_train >= 150 and train exp > 0, plus the best per level; failures included)

Columns: n / exp R / t for train (to 2025-12-31), valid (2026) and the open history. "sR" = open expectancy in
structural R. "plat" = the worst one-step neighbour (x, k). Live = PD / OR / H60 level and attempt 1.

| config | train | valid | open | sR | up / down | WF | ex-best | busiest | plat | live |
|---|---|---|---|---|---|---|---|---|---|---|
| LIQ-D20-long-x0.15-open-k5-a1-S-2R-TS | 1061 / +0.108 / 0.98 | 1200 / -0.016 / -0.24 | 2261 / +0.042 / 0.63 | +0.006 | +0.43 / -0.41 | 0.35 | -0.002 | 0.09 | -0.058 | no |
| LIQ-D20-long-x0.15-open-k5-a2-S-2R-TS | 1104 / +0.092 / 0.92 | 1229 / -0.014 / -0.20 | 2333 / +0.036 / 0.58 | +0.005 | +0.41 / -0.41 | 0.35 | +0.002 | 0.10 | -0.064 | no |
| LIQ-OR-short-x0.15-lvl-k5-a2-A-NL-BE+TS | 159 / +0.133 / 0.90 | 112 / -0.138 / -0.87 | 271 / +0.021 / 0.18 | +0.021 | -0.01 / +0.10 | 0.44 | -0.042 | 0.10 | -0.169 | no |
| LIQ-OR-short-x0.15-lvl-k5-a2-A-NL-TS | 158 / +0.140 / 0.89 | 111 / -0.184 / -1.05 | 269 / +0.006 / 0.05 | +0.006 | -0.05 / +0.19 | 0.33 | -0.055 | 0.10 | -0.152 | no |
| LIQ-D20-long-x0.15-open-k5-a1-S-2.5R-TS | 1061 / +0.090 / 0.88 | 1200 / -0.017 / -0.22 | 2261 / +0.034 / 0.52 | +0.004 | +0.42 / -0.42 | 0.35 | +0.003 | 0.09 | -0.060 | no |
| LIQ-OR-short-x0.15-lvl-k5-a2-A-NL-BE | 159 / +0.133 / 0.86 | 112 / -0.138 / -0.87 | 271 / +0.021 / 0.18 | +0.021 | +0.01 / +0.09 | 0.44 | -0.051 | 0.10 | -0.146 | no |
| LIQ-OR-short-x0.15-lvl-k5-a2-A-NL-none | 158 / +0.141 / 0.86 | 111 / -0.171 / -0.97 | 269 / +0.012 / 0.10 | +0.012 | -0.03 / +0.20 | 0.33 | -0.058 | 0.10 | -0.110 | no |
| LIQ-D20-long-x0.15-open-k5-a1-S-2R-BE+TS | 1061 / +0.082 / 0.82 | 1200 / -0.011 / -0.16 | 2261 / +0.033 / 0.53 | -0.000 | +0.39 / -0.38 | 0.35 | -0.006 | 0.09 | -0.062 | no |
| LIQ-D20-long-x0.15-open-k5-a2-S-2.5R-TS | 1104 / +0.075 / 0.77 | 1229 / -0.014 / -0.18 | 2333 / +0.028 / 0.45 | +0.003 | +0.39 / -0.41 | 0.41 | +0.002 | 0.10 | -0.066 | no |
| LIQ-D20-long-x0.15-open-k5-a2-S-2R-BE+TS | 1113 / +0.064 / 0.73 | 1229 / -0.008 / -0.12 | 2342 / +0.026 / 0.47 | -0.002 | +0.37 / -0.38 | 0.29 | -0.002 | 0.10 | -0.070 | no |
| LIQ-PD-short-x0.15-lvl-k5-a1-A-NL-none | 451 / +0.011 / 0.01 | 65 / +0.135 / 0.66 | 516 / +0.026 / 0.03 | +0.026 | +0.03 / -0.18 | 0.25 | -0.672 | 0.54 | -0.741 | yes |
| LIQ-H60-long-x0.15-rng-k15-a2-S-EOD-none | 1700 / +0.079 / 0.44 | 1207 / -0.267 / -1.10 | 2907 / -0.065 / -0.42 | -0.028 | +0.84 / -0.69 | 0.41 | -0.150 | 0.05 | -0.291 | no |

Every finalist fails valid, the regime split or both. The full table is in `results.csv` (all 7,680) and
`finalists.csv`.

## 4. Comparison with CWT14 / B3 and Testing 1 (lab R, open history, costs in)

| setup | n | exp R | t | note |
|---|---|---|---|---|
| CWT14 live (Testing 2), best: failbrk-pdl-p10-long t05s1 | 37,499 | -0.086 | -8.75 | the 14 live CWT14 rows run -0.086..-0.096 |
| B3 replica here: PDL p0.10 long t05s1 | 37,479 | -0.085 | -8.69 | engine check |
| B3 replica here: ORL p0.10 long t05s1 | 51,390 | -0.091 | -8.51 | |
| Liquidity, same level, plain (OR-long x0.05 lvl k5 S EOD) | 98,748 | -0.098 | -3.24 | the sweep alone = B3 |
| **Liquidity pick 1: OR-long x0.15 open k15, S stop, 2.5R** | 13,335 | -0.001 | -0.01 | up +0.59 / down -0.49 |
| **Liquidity pick 2: PD-long x0.05 open k15, A stop, VWAP target, BE+TS** | 160 | +0.088 | 0.58 | train -0.220 (t -1.79) / valid +0.549 (t 2.34) |
| Testing 1 -FD setups, median of 29 full-day backtests | | -0.046 | | range -0.079..+0.041 (config/account_testing.yaml notes) |
| Testing 1 best full-day: ST8-volspikedn-long-pm-t1s1-FD | ~1.24/day | +0.041 | | |
| Random same-side bar, stop A | 386,047 | -0.087..-0.097 | | |

**Does the liquidity version add anything over CWT14?**
- On the same level, the stop-at-sweep, 2R targets, break-even and early exit change almost nothing. Fading the
  first poke is about random minus costs, as in package B.
- The one real difference is the trigger. Waiting for a deeper sweep (0.15 ATR) and then for a 15-minute close
  beyond the impulse bar's open removes about 0.09R per trade versus B3, and it cuts the number of trades by about 7x.
- That moves the long OR-low version from -0.09R to ~0R. It does not make it positive. It is long-in-up-sessions
  beta, and it is no better than random in down sessions.

## 5. Incorporation (pre-declared PLAN 5, applied as written)

Bar (a) passes 0. Bar (b) passes 24 configurations, all OR-long or PD-long/short cells. The rule takes the best open
t first, with distinct level and side, at most 2:

1. `LIQ-PD-short-x0.15-lvl-k5-a1-A-NL-*` is **excluded**: 54% of its 516 trades fall on one session, and its
   ex-best-day is -0.66R (RESEARCH_RULES rule 5).
2. **`LIQ-pdl-sweep-open15-vwap-long`** = LIQ-PD-long-x0.05-open-k15-a1-A-NL-BE+TS.
   - Open history: n 160, +0.088R, t 0.58, 0.38 trades/day.
   - With a next-bar-open entry it drops to +0.030R.
   - Train and valid disagree in sign; walk-forward share 0.33.
3. **`LIQ-orl-sweep-open15-s25-long`** = LIQ-OR-long-x0.15-open-k15-a1-S-2.5R-none.
   - Open history: n 13,335, -0.001R, t -0.01, 31.3/day; next-bar-open entry -0.000R.
   - Neighbours run -0.076..-0.001R.

Live mechanics:
- The engine supports the structural stop (GEOM `S`), break-even (`be_at_r`) and the time stop (`time_stop_min`,
  `time_stop_min_r`). The live runner applies the last two from 1-minute bars, so the break-even move can come a few
  minutes earlier than in the 5-minute backtest.
- A fixed target with a structural stop needed one small opt-in hook in `mcf/strategies/setups.py` LabStrategy: a
  module may define `target_price(f, i, stop)`. Modules without it are unchanged (target None).
- **The second attempt is not supported live**: LabStrategy takes one signal per symbol per setup per day. That is
  why only attempt-1 configurations were eligible.
- `scale_out_r: null` is set, so the default 1R scale-out does not apply to these two setups.

**Parity** (`live/verify.json`):
- Exact trade for trade: 13,335 / 13,335 and 160 / 160, with 0 missing and 0 extra. The stop and target equal the
  scored levels on every sampled row (882 and 160 checks, max diff 0.0).
- Live path (`live/spot_live.json`, real 1-minute bars through `LabStrategy.generate`): 42 of 44 checks agree. The
  2 misses (MOH 2025-06-26, HUBS 2025-06-25) are the same 5-minute bar with the same stop and target; a missing
  1-minute print moves the end-minute index by 1-2 minutes.

**Testing 1 overlay:**
- `config/account_testing.yaml`: both setups enabled at window [950, 1500] and min_adv $95M; setup_order is by
  trades per day.
- Display names: `config/setup_names.yaml` and `docs/live/setup_names.json`.
- Test: `tests/test_testing_liquidity.py`.
- Backlog entry: `bdi-reddit1012-liquidity-sweep`, status failed (gates), 7,716 configurations.
- No ledger entry was written: the lead approves and records the change at merge.

## 6. Daily-bar version (information only; `daily.py`, `data/daily_results.csv`)

Setup: a sweep of the prior 10/20-day high or low by x ATR, a close back inside, entry at the next open. Exits: hold
1/3/5 days, or S2R. Splits: train 2016-2022 / valid1 2023-01..2024-10 / valid2 2025-03..2026-10.

- Shorts: every configuration is negative in every split, e.g. n20 x0 h3: -20 / -36 / -34 bps.
- Longs: h1 is negative. h3/h5 are positive, e.g. n20 x0.1 h5: +27 / +54 / +37 bps, t 1.0-2.1. That is consistent
  with the long drift W3 found for any long basket. S2R longs are positive in train and valid1 and negative in valid2.
- Not eligible for Testing (multi-day holds), and not proposed.

## Files

- `PLAN.md`: the pre-declaration.
- Pipeline: `prep.py` (5-minute bars from the 1-minute cache, day levels), `score.py` (grid, kernels, exits, costs,
  replicas, baselines), `report.py` (gates -> `results.csv`, `finalists.csv`, `summary.json`), `daily.py`.
- `live/`: `liq_live_lib.py`, the two modules, `verify.py` / `verify.json`, `spot_live.py` / `spot_live.json`.
- `data/` (git-ignored): the bars, `daystats.npz`, the controls.
