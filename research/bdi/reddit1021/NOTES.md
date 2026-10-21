# reddit1021: "untouched levels + 5-minute fib retrace" (Reddit strategy, owner request 2026-10-21). Results

*Educational only - not financial advice. Everything here is a backtest on the open two-year history with costs in.
Nothing is paper or live. `PLAN.md` was written before any scoring; its one amendment (the stock control) was made
before any scoring and is marked there. The locked block 2024-11-01..2025-02-28 was never read: regular-hours bars
were loaded through pyarrow row filters that drop it, and the extended-hours fetch never requested it. No holdout was
scored.*

**Configurations: 183 in total** (`counts.json`).
- SPY+QQQ ("IDX"): 64 pre-declared + 11 stage-2 combinations + 3 post-hoc.
- Liquid stocks ("STK", 1,198 names, adv20 >= $95M on the day): 64 + 8 + 3.
- 30 module-version scores (10 modules x 3 forms).
- Study bar: max(1.5, sqrt(2 ln 183)) = **3.23** on the day-clustered t. Counting the earlier Reddit
  level-sweep study (reddit1012liq, 7,718 configurations) as the same lineage: **4.24**.
- At p = 0.05 about 9 false positives are expected by chance.

TRAIN = 2024-09-16..2024-10-31 and 2025-03-03..2025-12-31. VALID = 2026-01-02..2026-10-16. That is 444 sessions:
245 train and 199 valid.

## Failures first
- **No configuration reaches the study bar.** The best open-history t is 2.01: SPY/QQQ continuation through the
  prior-day high/low, 28 trades.
- **Stocks: all 75 stock configurations lose after costs** (-0.09 to -0.47R per trade over the open history, t -2.1 to
  -29.9).
  - **There is no edge even before costs.** Gross is -0.08..+0.06R per trade.
  - Against a random entry at the same minute with the same exit, every stock row is within -0.10..+0.06R.
  - In short, the stock version is random entries plus about 0.23R of costs per trade.
- **SPY+QQQ, exactly as posted** (continuation, 0.5 retrace, 2R, flat 15:55):
  - n 178, 39% winners, **-0.04R per trade** after costs (t -0.30).
  - Train -0.19R (n 103), valid +0.18R (n 75).
  - Before costs it is +0.16R. Costs are about 0.20R per trade on SPY/QQQ at these stop sizes.
  - **The reversal half is worse:** n 102, 30% winners, -0.30R (train -0.49 / valid -0.06).
- **The 0.618 retrace is worse than the 0.5 everywhere.**
  - IDX continuation: -0.17R vs -0.04R.
  - Stocks: -0.34R vs -0.26R.
  - It fills less often, and its fills are the deeper (worse) pullbacks.
- **Waiting for the retrace is the main problem.**
  - On SPY/QQQ, signal candles that did **not** pull back to the 0.5 within 10 minutes would have made, entered at
    the candle close: +0.25R train / +0.60R valid (n 106 / 66).
  - The ones that did pull back made -0.43 / -0.06R at a close entry, and -0.15 / +0.25R at the fib.
  - The limit order selects the losers (adverse selection). The same holds on stocks.
- **The 11:30 time stop and the target (1.5R / 2R / 3R) change almost nothing.**
  - IDX: the 11:30 time stop is -0.10R vs -0.04R.
  - Stocks: within ±0.01R.
- **Trend filters (VWAP / 5m EMA20), "first touch of the day only", and touch-fill vs trade-through do not help.**
  - Touch-fill equals trade-through on IDX (prices rarely print exactly at the fib) and is +0.01R on stocks.
- **Asia session: not available.** ETFs and stocks do not trade 18:00-03:00. The prior session's after-hours
  (16:00-20:00) was used as a proxy. It is one of the weakest level families.
- **London proxy: the 04:00-09:30 premarket range.** It is the worst family on IDX (-0.39R, n 33).
- **We test equities/ETFs, not ES/NQ futures.** Futures costs per unit of risk are lower, and futures have a real
  overnight session.
- **The one Testing-bar pass is fragile.**
  - The row: IDX reversal, any level, volume > 1.5x the previous candle. It is a stage-2 combination with train
    n 31 (t 0.28) and valid n 16.
  - Its lab-runnable module forms are weaker (see Finalists).
- **IDX regime split: the IDX continuation rows earn on down sessions and lose on up sessions** (primary:
  up -0.36 / down +0.23R). Most IDX trades are shorts (73%).
- **Sample.** IDX yields 0.4 trades per day (both tickers). That is too few for any single variant to reach the bar
  in two years.

## Results (avg R per trade after costs; n, day-clustered t, win %)
Full table: `results.csv` (183 rows; columns for train / valid / all, random control, excess, gross, trades per day,
up / flat / down sessions, walk-forward month share, ex-best-day). Level-family / side / ticker splits:
`breakdown_primary.csv`. Module versions: `module_versions.csv`.

### Base grid, fib 0.5 (the 0.618 rows are worse in every cell)
| group | type | target / exit | train | valid | random same-minute | gross (all) |
|---|---|---|---|---|---|---|
| IDX | continuation | 2R / 15:55 (as posted) | -0.194 (103, t-1.13, 34%) | +0.175 (75, t0.94, 47%) | -0.223 | +0.156 |
| IDX | continuation | 1.5R / 15:55 | -0.210 (103, 40%) | +0.099 (75, 52%) | -0.178 | +0.109 |
| IDX | continuation | 3R / 15:55 | -0.217 (103, 27%) | +0.342 (75, t1.39, 41%) | -0.221 | +0.224 |
| IDX | continuation | 2R / 11:30 time stop | -0.326 (103, 32%) | +0.209 (75, 48%) | -0.199 | +0.103 |
| IDX | reversal | 2R / 15:55 (as posted) | -0.488 (57, t-2.61, 25%) | -0.062 (45, t-0.24, 38%) | -0.169 | -0.080 |
| IDX | reversal | 3R / 15:55 | -0.415 (57, 21%) | +0.195 (45, 36%) | -0.197 | +0.078 |
| STK | continuation | 2R / 15:55 (as posted) | -0.303 (26,128, t-12.4, 32%) | -0.217 (26,733, t-9.3, 34%) | -0.226 | -0.029 |
| STK | continuation | 1.5R / 3R | -0.295 / -0.309 | -0.221 / -0.219 | | |
| STK | reversal | 2R / 15:55 (as posted) | -0.299 (14,842, t-12.1, 33%) | -0.250 (15,190, t-10.1, 32%) | -0.229 | -0.039 |

Trades per session: IDX 0.40 (continuation) / 0.23 (reversal). STK 119 / 68 across the universe.

### Level family (as posted, fib 0.5, 2R) - train / valid avg R (n)
| family | IDX continuation | IDX reversal | STK continuation | STK reversal |
|---|---|---|---|---|
| opening range 09:30-09:45 | -0.42 (37) / +0.03 (27) | -0.46 (39) / +0.04 (33) | -0.32 / -0.22 (12.8k / 13.7k) | -0.32 / -0.26 |
| premarket 04:00-09:30 ("London") | -0.30 (13) / -0.92 (10) | n 3 / 3 | -0.26 / -0.23 | -0.26 / -0.22 |
| prior after-hours ("Asia" proxy) | -0.44 (4) / +0.80 (7) | n 2 / 2 | -0.32 / -0.30 | -0.37 / -0.23 |
| prior day H/L | +0.02 (13) / +0.90 (12) | n 1 / 1 | -0.30 / -0.22 | -0.26 / -0.32 |
| intraday swing | +0.03 (36) / +0.27 (19) | -0.46 (12) / -0.70 (6) | -0.27 / -0.19 | -0.25 / -0.23 |

### One-knob variants on IDX continuation (train / valid avg R, n)
| variant | train | valid | note |
|---|---|---|---|
| as posted | -0.194 (103) | +0.175 (75) | |
| **enter at the candle close (no retrace)** | **-0.074 (202)** | **+0.261 (135, t1.79)** | better on both splits; also the best stock row (-0.12 / -0.11) |
| candles 09:50-10:15 only | -0.508 (59) | +0.082 (49) | worst bucket in both groups |
| candles 10:20-10:45 / 10:50-11:30 | +0.135 (9) / +0.250 (35) | +0.473 (15) / +0.332 (12) | |
| *post-hoc: candles from 10:20 on* | *+0.226 (44)* | *+0.351 (26, t1.07)* | *post-hoc; stocks -0.24 / -0.18 (vs -0.30 / -0.22)* |
| candle >= 2x 5m ATR (vs 1.5x) | -0.005 (44) | -0.021 (31) | stocks better on both splits (-0.24 / -0.18) |
| candle >= 1x 5m ATR | -0.280 (249) | -0.178 (184) | worse everywhere |
| volume > 20-bar average | -0.090 (79) | +0.094 (57) | stocks better on both (-0.25 / -0.19) |
| volume filter off / > 1.5x | -0.153 / -0.199 | -0.005 / +0.192 | |
| trend: with VWAP / with EMA20 | -0.256 / -0.156 | +0.171 / +0.207 | |
| any level (touched or not) | -0.114 (136) | +0.088 (97) | |
| first signal of the day | -0.205 (89) | +0.217 (64) | |
| touch-fill | = as posted | = as posted | |
| lab-runnable (enter at the close of the 5m bar that reaches the fib) | -0.184 (94) | +0.153 (68) | |

The reversal variants and the stage-2 combinations are in `results.csv`. Every stock variant is negative on both
splits.

## Finalists for the testing accounts (pre-declared Testing bar; none reaches the research bar)
The Testing bar requires all of the following:
- train and valid avg R > 0;
- both above the random control;
- valid t ≥ 1.5;
- n_train ≥ 30 (IDX);
- ex-best-day > 0.

| row | status | train | valid | all t | why it falls short |
|---|---|---|---|---|---|
| IDX reversal, any level, volume > 1.5x prev (stage 2) | **Testing-bar pass** | +0.080 (31, t0.28) | +0.706 (16, t1.95) | 1.29 | 47 trades; train ~0; research bar 3.23 |
| IDX continuation, prior-day H/L only | near-miss | +0.273 (15) | +0.984 (13, t2.28) | 2.01 | n_train 15 < 30 |
| IDX continuation, candle-close entry | near-miss | -0.074 (202) | +0.261 (135, t1.79) | 0.65 | train < 0 |
| IDX continuation, candle-close entry, from 10:20 (post-hoc) | near-miss | -0.034 (88) | +0.417 (54, t1.85) | 0.97 | train < 0; post-hoc |
| IDX continuation, from 10:20 (post-hoc) | near-miss | +0.226 (44) | +0.351 (26, t1.07) | 1.23 | valid t; post-hoc |
| IDX continuation, 10:50-11:30 | near-miss | +0.250 (35) | +0.332 (12, t0.80) | 1.00 | valid t |
| IDX continuation, 2x ATR + any level (stage 2) | near-miss | +0.016 (56) | +0.222 (35, t0.80) | 0.52 | valid t |

**Modules** (`modules/`, LabStrategy contract: SIDE, GEOM "S" + `stop_price` / `target_price` (2R of the structural
risk), WINDOW (950, 1140), SYMBOLS [SPY, QQQ], `mask(df)`). LabStrategy takes one side per module, so each row has a
long and a short module, and the module fires on the first signal of the day (refire: false). Each module was scored
in its exact runnable form (`module_versions.csv`; train / valid avg R, n):

| module | scan form, this side | runnable now (OR/PD/SW levels) | with PM/AH context |
|---|---|---|---|
| RD1-idx-rev-anylevel-vol15-fib05-2R-long | -0.23 (13) / +0.86 (7) | -0.01 (10) / +0.46 (5) | -0.03 (13) / +0.69 (6) |
| RD1-...-short | +0.30 (18) / +0.59 (9) | +0.16 (14) / +0.70 (5) | -0.11 (17) / +0.27 (9) |
| RD2-idx-cont-closeentry-2R-long | -0.10 (67) / +0.03 (50) | -0.08 (60) / +0.02 (48) | -0.10 (67) / +0.05 (49) |
| RD2-...-short | -0.10 (140) / +0.34 (88) | -0.19 (128) / +0.31 (79) | -0.14 (131) / +0.29 (82) |
| RD3-idx-cont-pd-fib05-2R-long | -1.13 (4) / -0.07 (3) | -1.57 (4) / +0.37 (2) | same |
| RD3-...-short | +0.78 (11) / +1.30 (10) | +1.06 (11) / +1.02 (10), all t 3.29 | same |
| RD4-idx-cont-late-fib05-2R-long | n 4 / 1 | n 3 / 1 | same |
| RD4-...-short | +0.35 (31) / +0.47 (11) | +0.39 (32) / +0.23 (11) | +0.44 (33) / +0.36 (12) |
| RD5-idx-cont-k2-anylevel-fib05-2R-long | +0.14 (12) / +0.53 (12) | -0.41 (10) / +0.14 (10) | -0.05 (12) / +0.29 (12) |
| RD5-...-short | -0.02 (44) / +0.06 (23) | -0.24 (35) / +0.34 (20) | -0.15 (41) / +0.41 (21) |

- **Read with care.** The long/short split was made after seeing results. The short modules look better because
  the open history's IDX signals earned on down sessions.
- RD3-short has 21 trades in two years. It is an observation, not a setup.
- No module is a candidate.

**Parity** (`verify_modules.json`). Each module's mask on frames built the way LabStrategy builds them (heat_frame over
the 5-minute bars, volume, prior-day distances) reproduces the scan exactly:
- every module, both level sets;
- 0 module-only signals, 0 scan-only signals, 0 stop mismatches;
- 4-213 signals per module.

**Geometry / what live needs.**
- **No new GEOM is needed for the 2R target.** The structural geometry `S` with `target_price` (added for
  reddit1012liq) already sets the target at 2x the entry-to-stop risk.
- A `t2s1` geometry would not reproduce the posted rules: its R is 0.25 x daily ATR, not the candle's own stop
  distance.
- **The posted entry (a resting limit at the fib, cancelled after 10 minutes) is not supported.** LabStrategy enters
  at the close of the qualifying 5-minute bar. Supporting it would take:
  - a new entry type: the Signal carries a limit price and an expiry;
  - in the runner: place a limit order and cancel it after 10 minutes;
  - in the backtester: fill only on a trade-through within the expiry.
- The modules therefore use the lab-runnable proxy: enter at the close of the bar that reaches the fib. It scores a
  little worse than the limit form on IDX continuation (-0.18 / +0.15 vs -0.19 / +0.18) and clearly worse on reversal.
- **Context.**
  - OR, prior-day and swing levels come from the frame itself: the 09:35-09:45 rows, `dist_pdh_atr` x `atr_d`, and
    today's pivots.
  - Premarket and after-hours levels need a new lab context field (pm_high / pm_low / ah_high / ah_low from
    extended-hours bars). The modules use those levels only if the columns are present.
- Live caveat (all lab setups): a signal is evaluated only on complete 5-minute bars.

```yaml
# ONLY if the owner wants forward observation in a testing account. Near-misses; research bar NOT met. Example:
  RD2-idx-cont-closeentry-2R-short:
    enabled: true
    type: lab
    module: research/bdi/reddit1021/modules/RD2-idx-cont-closeentry-2R-short.py
    symbols: module
    window: [950, 1140]
    refire: false
    tags: [near-miss, reddit1021, forward-observation]
```

## Method notes
- **Data.**
  - Regular hours: `data/cache_hist/1Min` (row-filtered).
  - Extended hours (04:00-20:00): a read-only Alpaca SIP fetch, `scripts/fetch_ext.py`. It uses a market-data GET
    only, with keys from the environment, never written.
  - 1-minute bars for SPY/QQQ; 30-minute bars for 1,198 stocks, enough for the exact premarket and after-hours H/L.
  - The prior-day and after-hours levels are skipped on 2025-03-03, whose prior session is in the locked block.
- **Fills.**
  - The limit entry fills only when a later 1-minute bar trades strictly through the fib (touch-fill reported).
  - The stop is checked first in every bar, including the fill bar.
  - A bar that opens through the stop fills at its open.
  - The target is a limit, with no exit cost.
  - Costs: production costs (1c + 1 bps per side; entry side x the time-of-day multiplier; +2c on stops), x3 on the
    extended tier.
- **Random control.** A market entry at the close of the same fill minute on other sessions of the same split (IDX: 60
  sessions, STK: 20 sessions of the same symbol), with the same side, R/price, target and exit.
- **Bug fixed before the final run.** Lab-entry trades whose close sat exactly on the stop carried R ≈ 1e-15
  (floating point) instead of being skipped. R ≤ 1e-6 x price is now "no trade". Both groups were re-run in full.
- **Disk.** The stock prep arrays (~2 GB) live in /dev/shm; scratch is in the session scratchpad. Nothing large is in
  the repo.
- **Scripts:** `scripts/` holds common, fetch_ext, prep, engine (numba), run, posthoc, report, modules, and
  module_template.

## Reddit reply (draft, plain words)
> Ran your rules on ~2 years of 1-minute data (Sep 2024–Oct 2026, minus 4 months we keep locked; 444 days), on SPY and
> QQQ as stand-ins for ES/NQ, plus ~1,200 liquid stocks. "Result per trade" below = profit or loss in units of the
> risk you took (stop distance), after commissions/slippage.
>
> SPY+QQQ:
> ```
> version                              trades  win%  result/trade
> your rules, continuation              178    39%    -0.04
> your rules, reversal                  102    30%    -0.30
> enter at breakout-candle close        337    41%    +0.06
> only candles 10:20-11:30               70    50%    +0.27
> use 0.618 instead of 0.5              133    37%    -0.17
> prior-day high/low breaks only         28    61%    +0.60
> premarket high/low breaks only         33    27%    -0.39
> ```
> What looked good: the continuation side is roughly break-even after costs and positive before them (+0.16), and
> prior-day high/low breaks were the best levels (tiny sample though).
> Tweaks worth looking at:
> 1. Don't wait for the 50% pullback: enter on the close of the breakout candle, stop still past the candle. Candles
>    that never pulled back within 10 minutes were the big winners. Waiting for the pullback filters them out.
> 2. Skip the first half hour after the opening range; the 9:45–10:15 breakout candles were the worst on both
>    SPY/QQQ and stocks.
> 3. Stick with 0.5 over 0.618, and need a bigger candle (about 2x the average 5-min range).
> 4. The reversal setup was the weak half. 1.5:1 vs 2:1 vs 3:1 targets barely mattered.
>
> Limits: ETFs/stocks, not futures (your costs per trade are lower); no Asia session (we used after-hours/premarket as
> stand-ins). On individual stocks none of it worked after costs. Nothing cleared our statistical bar. These are
> ideas to test, not advice.

Educational only - not financial advice.
