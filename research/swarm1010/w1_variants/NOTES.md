# W1 (swarm 2026-10-10): indicator-variant sweep of every setup family on the open two-year history

*Educational only - not financial advice. Lab backtests on the open two-year history only; nothing here is a live or
paper result.*

Owner ask (2026-10-09 evening): "rerun all of our setups discussed with our new data set with different variants of
indicators again to find higher performing setups." Lead's brief: a disciplined variant sweep of every setup family,
one indicator parameter at a time around the original, then pairs only for the top neighbours (coordinate search),
every configuration counted, ranked by regime-robust performance (positive in up AND down sessions), and per family:
does ANY variant change the up/down asymmetry?

**Section 1 (pre-declaration) was written 2026-10-09 before any configuration of this workstream was scored.** The only
numbers seen beforehand are the published ones (history2y/RESCORE.md, timeofday, regime1009, stack1009, reddit NOTES).
The data build (`build_extras.py`) computes indicator columns and a reproduction check only (no P/L of any variant).
Section 1 may change only by dated amendments; results go in section 2.

## 1. Pre-declaration

### 1.1 Data (open history only)
- Rows: `research/bdi/stack1009/data/base.npz` (built through `research/history2y/lib.py`; the rule-19 locked block
  2024-11-01..2025-02-28 is not in it), adv20 >= 95M point in time, bar closes 09:50-15:00, 426 open sessions,
  24.2M rows; memory-mapped (`npzmap.py`), never loaded whole. `MCF_HIST_ALLOW_LOCKED` is never set.
- Extra columns (`build_extras.py`, git-ignored `data/ext/`), row-aligned with base.npz:
  - from the lab frames (lib.load_month, locked months refused): `heat`, `rest3` = priceActionHeat - momentumHeat -
    vwapHeat (heat_fade's score without its RSI component);
  - from `data/cache_hist/1Min` with the locked-block rows **dropped at load, before any computation** (so warm-up
    across the gap differs from the frames for the first bars of 2025-03; checked against the frames' rsi / emaDiff):
    RSI 9 / 21 (MarcoFlow simple RSI as `heat_frame`; RSI 5 / 14 are the frame's `rsi5` / `rsi`), EMA pair
    differences 8/21, 13/21, 9/20, 8/20, 13/20 (9/21 = the frame's `emaDiff`), SMA100 distance (live parity: NaN
    until 60 prior + today's bars >= 100, i.e. today's 40th bar, ~12:50), VWAP SD z = (close - VWAP) / volume-weighted
    SD of the typical price over today's 5-min bars (as RW6G1's guard), and two extra exits computed with the lab's
    outcome rules on 5-min bars: t15s1 (target 1.5R / stop 1R) and t1s075 (target 1R / stop 0.75R); R = 0.25 x daily
    ATR, stop first on a shared bar, timed exit at the 15:55 bar close, production cost formula of `gates.prod_r`.
    Their t1s1 twin is computed the same way and compared with base.npz `p_*_t1s1` (build_check.json).
  - RSI divergence flags and bar high/low (ATR distances): `research/bdi/reddit/data/extra.npz` (row-aligned).
- L3 lineage (min_adv 0, gap prefilter): its population is not in base.npz (adv < 95M), so the L3 family is run on
  a separate month-by-month pass over the frames (rows with gap <= -1%, all adv), thresholds and the three frame
  exits only (no extra indicator columns for those rows).
- Regimes: `lib.regimes()` (terciles of the universe median open-to-close; up / flat / down, 142 each).
- Costs: production (`gates.prod_r`: 1c + 1 bps per side, exit side free on target fills, +2c on stops).
- Entry: first qualifying bar per symbol-day at its close, **full day 09:50-15:00** for every variant (owner
  preference); time of day is reported for the finalists (buckets B1-B5 of the timeofday study), not searched.
- Survivorship: today's 1,226 names applied to the past (as RESCORE.md).

### 1.2 Families (bases reproduce the full-day versions)
- **33 lab/heat families**: the 32 full-day modules of `research/bdi/fullday/` (heat_fade_short/long, exhaustion_short,
  MF1-MF5, NS1-NS5, RW1-RW7, RW6G1, ST1-ST8, L3 x3) + RW8 (`research/bdi/rework1008/modules`, already full day).
  Each base = the module's mask with its own side, exit and min_adv, full day. Reproduction target: the full-day
  trade lists of `research/bdi/timeofday/data/trades.parquet` (n and exp per setup).
  RW6G1's VWAP band guard is rebuilt from base rows only (09:50 on): an excursion above +2 SD set on the 09:35-09:45
  bars is not seen (small, reported by the reproduction check).
- **40 Reddit lists**: the 20 rules of `research/bdi/reddit/strategies.py` x long / short, no filter, t1s1, default p
  (as regime1009's base lists), triggers computed by the Reddit builders themselves.
- **72 stack1009 trigger lists**: the 18 trigger families of the ST modules' `trig()` (vwap, ema, macd, rsi14, rsi5,
  or, sma50, sma20, pdbrk, pdfail, band05, band10, hodlod, rsi50, volspike, fo3, slope20, flow3) x up / dn event x
  long / short, no filter, t1s1 (stack1009 stage-1 shape, full day).
Total **145 base lists**.

### 1.3 Variant axes (one at a time around the base; values ordered for plateau neighbours)
Family-specific axes (only where the family uses that indicator; the original value is always in the list):
- RSI length: 5 / 9 / 14 / 21 (swaps the RSI column in that layer, level kept).
- RSI levels: low side {20, 25, 30} and high side {70, 75, 80}, plus the original (e.g. NS2 60, RW1 band 55-65 ->
  bands 50-60 / 60-70 / 65-75; rsi5 > 90 -> {70, 75, 80, 85, 90}; cross levels 40 -> {30, 35, 40, 45}).
- EMA pair (emaDiff layers / ema triggers): fast 8 / 9 / 13 x slow 20 / 21 (base 9/21).
- SMA length (sma20 / sma50 layers and crosses): 20 / 50 / 100.
- Threshold axes on the family's own layers: fromOpen {1, 2, 3, 4}% (sign as in the rule), gap {0, 0.5, 1, 2, 3}%
  as fits the rule (L3: {-1, -2, -2.66, -3, -4}), volumeRatio {1.25, 1.5, 2, 3}, heat {-20, -30, -40} (MF4: -30 /
  -40 / -50), buyPressure {-0.15, -0.25, -0.35} (RW1/RW3: -0.25 / -0.35 / -0.45), heat_fade threshold base +-3 / +-6,
  heat_fade cost k {x0.5, x1, x1.5}, heat_fade gate {orig, none}, ST filter thresholds on the stack1009 grids,
  VWAP band guard k (RW6G1) {1, 1.5, 2, 2.5}, Reddit p on its plateau grid.
Common axes (every family; replaced by the family's own axis where it already has that indicator):
- exit: t1s1, t05s1, t1s05, t15s1, t1s075 (the base's exit is the original).
- volume ratio layer: volumeRatio >= {1.25, 1.5, 2, 3}.
- VWAP SD band layer: "stretched against the trade" s*zsd <= -k (short: close above VWAP + k SD; long: below
  VWAP - k SD), or "inside" |zsd| < k; k in {1, 1.5, 2, 2.5} (8 variants).
- in-play layer: |fromOpen| >= {1, 2, 3, 4}% (families without their own fromOpen threshold).
- SMA trend layer: with (s * sma_dist_n > 0) or against, n in {20, 50, 100} (6 variants; families without an MA layer).
The 1.5R target / 0.75R stop exits were cheap (computed in the build), so they are included as two exit values.

### 1.4 Search (coordinate search; every evaluated configuration counted)
- Stage 1 (OFAT): every single-axis variant of every base (the base itself counted once).
- Ranking score ("regime-robust"): robust = min(day-clustered t in up sessions, in down sessions), requiring
  n_up >= 30 and n_down >= 30 (else not ranked). Raw t is reported, not ranked on.
- Stage 2 (pairs): per base, the 3 best stage-1 variants by robust (n >= 150, distinct axes) -> the 3 pairwise
  combinations.
- Plateau neighbours of any configuration that meets every other probation condition are evaluated and counted.
- Try-count bar per lineage: t_required(N_prior + N_this) with N_prior from rescore.csv (heat 19,200; exhaustion
  855,600; MF 8,012; NS 7,374; RW 81,430-934,522; L3 274,247 (backlog configs_tried); ST 120,500; Reddit 2,551 + 400 + 400 (regime1009 gates);
  stack triggers 120,500) and N_this = this workstream's configurations of that base. Whole-study count reported.

### 1.5 Live-probation bar (all must hold; RULES.md)
n >= 150; exp > 0 in up AND down sessions (n >= 30 each); day-clustered t >= 2.0; walk-forward positive share >= 0.6
(`gates.walk_forward` folds, locked months excluded); plateau mean (one-step neighbours on every ordered axis of the
configuration) > 0; ex-best-day exp > 0; busiest session <= 10% of trades. Passers are probation candidates, not
"keep" unless t >= t_required. For passers: a lab module (SIDE, GEOM, LAYERS, mask(df)) on live-frame columns only,
verified to reproduce the scan, and a staged Testing YAML snippet. Variants that need columns the live frame lacks
(RSI 9/21, EMA 8/13/20, SMA100, exits t15s1/t1s075) are reported with the live change they would need.

### 1.6 Asymmetry question (per family, declared now)
For each base: up-session exp, down-session exp and spread = up - down (for shorts the spread is usually negative).
Across its variants: the number with exp > 0 in both regimes (n >= 30 each), the smallest |spread|, whether any
variant flips the sign of the spread, and the best both-positive variant. Pre-declared reading: a variant "changes
the asymmetry" only if both regimes are positive with min(t_up, t_down) >= 1.0 and it is not a lone point (its
plateau neighbours are both-positive on average); otherwise the asymmetry is unchanged. With ~40 variants per base,
a handful of both-positive variants are expected by chance (reported against that count).

## 2. Results (appended 2026-10-10; section 1 unchanged except the dated amendment 2.0)

*Lab backtests on the open two-year history only (not live, not paper). Production costs. Educational only - not
financial advice.*

### 2.0 Amendments and deviations (dated 2026-10-10)
- **Amendment A (after the first read of the passers, before any module was written):** all 7 probation passers use
  the SMA100 layer, which is NaN until today's 40th bar (~12:50 ET) under live parity, so the layer is also an
  afternoon filter. Two controls per passer were added and counted (14 configurations, `controls.py`,
  `controls.csv`): C1 = the same rule on the same SMA100-available bars without the SMA100 side, C2 = the SMA100 side
  flipped. They are diagnostics only; nothing was selected on them.
- Container restart mid-run: `run.py --resume` kept the 50 completed lists and ran the other 92 (no configuration
  run twice, none lost; the per-list search is independent).
- Reproduction (base rows vs `research/bdi/timeofday` full-day lists): 28 of 30 lab bases identical (n and exp);
  heat_fade_short / long differ by 5 / 7 trades (float32 RSI-heat rounding; exp equal to 0.0001); ST1 1,628 vs
  1,621 (opening-range float precision); **RW6G1 2,224 vs 1,969** - the guard rebuilt from 09:50 rows cannot see
  +2 SD excursions on the 09:35-09:45 bars (declared in 1.2), so RW6G1's guard results are approximate (no RW6G1
  variant passed). Reddit R01 long 197,074 / -0.080R = regime1009 exactly. Extra columns: RSI14 / RSI5 recomputed
  from 1-min within 0.1 on 99.96% / 99.99% of rows, EMA 9/21 within 0.005 on 99.8% (differences = warm-up after the
  dropped locked block and float16 storage), t1s1 outcome within 0.01R on 99.998% (`build_check.json`).
- L3 lineage: population outside base.npz, run separately (`l3.py`, gap <= -1% rows, all adv, three frame exits).

### 2.1 Counts
| part | lists | configurations |
|---|---|---|
| lab / heat families (32 full-day modules + RW8, excl. L3) | 30 | 1,078 |
| L3 (3 modules) | 3 | 64 |
| Reddit 20 rules x long / short | 40 | 1,302 |
| stack1009 trigger families 18 x up / dn x long / short | 72 | 2,219 |
| **total coordinate search** | **145** | **4,663** (base 145, one-axis 4,051, pairs 435, plateau / asymmetry neighbours 32) |
| amendment A controls | - | 14 |
| **study total** | | **4,677** |
Per-list t bars (t_required(N_prior + N_this)): heat 4.44, exhaustion 5.23 / 5.24, MF 4.24, NS 4.22, RW 4.76,
ST and triggers 4.84, Reddit 4.03, L3 5.0. The probation bar uses t >= 2.0; no configuration reaches its t bar.

### 2.2 Failures first
- **Big lineages: nothing.** heat_fade_short / long, exhaustion_short / RW2, MF1-MF5, RW1/RW3/RW5/RW7, NS1, NS2,
  NS4, NS5, RW6, RW6G1, RW8, ST2, ST3, ST4, ST5, ST7, L3 x3, all 40 Reddit lists and all 72 trigger lists have **no
  configuration meeting the probation bar**. Their bases lose -0.01 to -0.20R full day after costs (Reddit mean
  -0.082R, triggers -0.081R).
- **The asymmetry does not move.** Base lists: longs win in up sessions and lose in down sessions, shorts the reverse
  (Reddit longs up +0.109 / down -0.282, shorts -0.281 / +0.096; triggers longs +0.118 / -0.273, shorts -0.280 /
  +0.110; lab shorts typically -0.16..-0.29 / +0.02..+0.16). Of 3,993 variants with n >= 150, **54 (1.4%)** are
  positive in both regimes (lab 40 / 909, Reddit 3 / 1,094, triggers 11 / 1,990); only **4** meet the pre-declared
  "asymmetry changed" reading (both regimes > 0, min(t_up, t_down) >= 1, neighbours both-positive on average):
  ST1 + SMA100, ST6 + SMA100 (x2), and R14-ict-fvg-short p 0.2 + VWAP +1 SD - which is one cluster (2025Q2: 456 of
  915 trades at +0.71R; H1 +0.49R, H2 -0.06R; walk-forward 0.375) and is not a regime fix.
- **Per indicator axis (one-axis variants, n >= 150; change vs the list's base):**

| axis | variants | mean change in exp (R) | share better | mean change of abs(up - down) | both-regime positive |
|---|---|---|---|---|---|
| VWAP SD band layer (stretched / inside, k 1-2.5) | 942 | -0.004 | 46% | +0.000 | 2 |
| SMA trend layer (with / against 20/50/100) | 681 | -0.004 | 48% | -0.022 | 5 (4 are "against SMA100") |
| exit (t1s1 / t05s1 / t1s05 / t15s1 / t1s075) | 574 | -0.004 | 28% | -0.062 (t05s1 -0.15: smaller payoffs, mechanical) | 2 |
| volume ratio 1.25 / 1.5 / 2 / 3 | 490 | -0.007 | 33% | -0.057 | 1 |
| in-play abs(fromOpen) >= 1 / 2 / 3 / 4% | 471 | **+0.021** | 85% | -0.104 | **0** |
| RSI length 5 / 9 / 14 / 21 | 95 | -0.012 | 34% | +0.002 | 1 |
| RSI levels / bands | 56 | -0.005 | 34% | +0.007 | 0 |
| EMA pair (8/9/13 x 20/21) | 45 | +0.000 | 58% | +0.002 | 0 |
| SMA length 20 / 50 / 100 (swapped in the rule) | 42 | -0.006 | 45% | -0.013 | 0 |
| own thresholds (fromOpen, gap, heat, buyPressure, Reddit p, trigger p, ST filters) | ~300 | -0.03..+0.02 | - | - | 2 |
  RSI length, RSI levels, EMA pairs and SMA lengths do essentially nothing to the regime split. The in-play layer is
  the only consistently helpful layer (+0.02R, narrower spread) but never makes both regimes positive.
- The 1.5R-target and 0.75R-stop exits were included (built cheaply with the lab outcome rules); neither helps
  (t15s1 -0.004R mean, wider spread; t1s075 -0.005R).

### 2.3 Live-probation passers (7 configurations, 5 lists; all use the SMA100 layer)
| list | variant | n (/day) | exp R | t (t_req) | up / flat / down (n up, down) | WF | plateau | ex-best-day | busiest day |
|---|---|---|---|---|---|---|---|---|---|
| ST6-volspikeup-short | ma=a100 (close above SMA100) | 237 (0.56) | +0.171 | 3.23 (4.84) | +0.150 / +0.182 / +0.175 (64, 91) | 0.75 | +0.118 | +0.150 | 7.6% |
| ST6-volspikeup-short | ma=a100; gap filter 2% | 205 (0.48) | +0.164 | 2.77 (4.84) | +0.152 / +0.192 / +0.145 | 0.857 | +0.139 | +0.139 | 7.8% |
| NS3-failed-vwap-reclaim-short | sma=100 (for 50); vol >= 2 | 212 (0.50) | +0.139 | 2.53 (4.22) | +0.133 / +0.109 / +0.174 | 0.857 | +0.065 | +0.125 | 3.8% |
| NS3-failed-vwap-reclaim-short | sma=100; fromOpen < -4% | 240 (0.56) | +0.125 | 2.29 (4.22) | +0.078 / +0.160 / +0.118 | 0.80 | +0.057 | +0.119 | 7.9% |
| RW4-ns3-adv150-short | sma=100; fromOpen < -4% | 196 (0.46) | +0.134 | 2.17 (4.76) | +0.106 / +0.149 / +0.134 | 0.833 | +0.056 | +0.121 | 8.7% |
| ST1-ordn-long | ma=a100 (close below SMA100) | 567 (1.33) | +0.075 | 2.29 (4.84) | +0.111 / +0.011 / +0.094 (128, 280) | 0.688 | +0.028 | +0.070 | 4.4% |
| ST8-volspikedn-long | exit t05s1; ma=a100 | 353 (0.83) | +0.078 | 2.06 (4.84) | +0.056 / +0.168 / +0.004 (65, 149) | 0.923 | +0.043 | +0.060 | 5.4% |

Amendment A controls (same bars where SMA100 exists, i.e. after ~12:50):
| passer | C1: no SMA100 side | C2: SMA100 side flipped |
|---|---|---|
| ST6 a100 | 493 trades +0.003R (up -0.064 / down +0.057) | 276, -0.135R |
| NS3 sma100 vol2 | 1,399, -0.023R | 1,188, -0.052R (t -2.0) |
| NS3 sma100 F4 / RW4 sma100 F4 | -0.017R / -0.014R | -0.031R / -0.029R |
| ST1 a100 | 621, **+0.061R t 1.55** (up +0.123 / down +0.059) | 58, -0.125R |
| ST8 t05s1 a100 | 454, +0.057R t 1.59 | 105, -0.014R |
Reading: for ST6 and NS3 the SMA100 side carries the result (fade a name that is down on the day but still above its
~8-hour average); for ST1 and ST8 most of it is the afternoon restriction (both ST windows were "pm" originally).

Time of day (timeofday buckets; SMA100 makes B1/B2 impossible): ST6 B3 +0.06 (13) / B4 +0.25 (87) / B5 +0.13 (137);
NS3 vol2 B3 +0.12 / B4 +0.15 / B5 +0.14; ST1 B3 +0.07 / B4 +0.01 / B5 +0.13; ST8 B4 +0.04 / B5 +0.09. Halves (median
session): ST6 +0.099 / +0.203, NS3 vol2 +0.163 / +0.128, ST1 +0.071 / +0.079, ST8 +0.056 / +0.086. Per quarter:
`finalists.json` (every candidate has one or two negative quarters, e.g. ST6 2025Q3 -0.25R n 25).

**Candidates staged (one per list, best t; RW4 is NS3 at adv150 and is not staged separately; ST6 overlaps NS3 on 25%
of symbol-days):** modules in `modules/`, staged snippet `account_testing_w1.yaml`, verification `verify.json`:
| module | offline = scan | live-shaped sample (prior 60 bars + today, no symbol/date) |
|---|---|---|
| W1-NS3-vwapreclaim-sma100-vol2-short | 212 / 212 rows, same R | 133 symbol-days, 100% same first bar |
| W1-ST6-volspikeup-sma100above-short | 237 / 237, same R | 151, 100% |
| W1-ST1-ordn-sma100below-long | 567 scan / 561 module (frame-column OR; module list +0.073R t 2.20, still passes) | 140, 100% |
| W1-ST8-volspikedn-sma100below-long-t05s1 | 353 / 353, same R | 188, 100% |
**What live needs:** one column `sma100_dist_pct` = (close / SMA100 - 1) x 100 on 5-min closes over PRIOR5_BARS (60)
prior + today's bars (`mcf.research.setup_lab.extra_features`); NaN until today's 40th bar is part of the tested rule.
Without it the modules return nothing (fail-safe). Exits are t1s1 / t05s1 (already supported). These are
**probation candidates only**: t 2.1-3.2 against try-count bars of 4.2-4.8, from 4,677 configurations, never scored
on the locked block (the lead scores once). Expect shrinkage.

### 2.4 Top variant per family (by robust = min(t_up, t_down), n >= 150), lab / heat lists
| list | configs | base n | base exp | base up / down | both-pos / variants | spread flips | best variant | n | exp | t | up / down | robust | passers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| heat_fade_short | 34 | 75141 | -0.032 | -0.235 / +0.131 | 0/31 | 0 | fo=3.0 | 6896 | -0.065 | -1.98 | -0.152 / +0.047 | -2.87 | 0 |
| heat_fade_long | 38 | 23513 | -0.030 | +0.117 / -0.140 | 0/37 | 2 | vband=ext2.5;vol=3.0 | 453 | +0.149 | 1.94 | -0.003 / +0.147 | -0.02 | 0 |
| exhaustion_short | 36 | 28458 | -0.059 | -0.172 / +0.116 | 0/32 | 0 | vol=3.0 | 1012 | -0.009 | -0.22 | -0.065 / +0.071 | -0.95 | 0 |
| RW2-exhaustion-noon-adv150-short | 36 | 22187 | -0.056 | -0.166 / +0.121 | 0/32 | 0 | vol=3.0 | 728 | +0.008 | 0.16 | -0.035 / +0.095 | -0.41 | 0 |
| MF1-945-flowsell-vwapup | 37 | 10540 | -0.074 | -0.212 / +0.069 | 0/28 | 0 | io=3.0 | 176 | -0.075 | -1.37 | -0.154 / +0.064 | -2.03 | 0 |
| MF2-open-rsimidhi-flowsell | 40 | 4517 | -0.046 | -0.126 / +0.050 | 0/29 | 1 | heat=-40;io=4.0 | 296 | -0.012 | -0.16 | -0.064 / +0.070 | -0.75 | 0 |
| MF3-open-flowsell-rsi5hi | 39 | 10564 | -0.071 | -0.279 / +0.098 | 0/32 | 0 | io=4.0;ma=w20 | 489 | -0.026 | -0.48 | -0.171 / +0.110 | -1.90 | 0 |
| MF4-h40-open-flowsell | 34 | 7273 | -0.079 | -0.226 / +0.017 | 0/27 | 0 | heat=-50;ma=w20 | 362 | +0.008 | 0.11 | -0.160 / +0.077 | -0.85 | 0 |
| MF5-flowsell-vwapup-rsi5hi | 42 | 6827 | -0.052 | -0.278 / +0.163 | 0/31 | 0 | ma=w100 | 395 | -0.101 | -2.04 | -0.232 / +0.023 | -2.79 | 0 |
| RW1-gapdn-bounce-flowsell-short | 43 | 7474 | -0.046 | -0.259 / +0.129 | 1/36 | 0 | gap=2.0;io=4.0 | 234 | +0.047 | 0.57 | +0.055 / +0.172 | 0.46 | 0 |
| RW3-gapdn-rsi5pop-flowsell-short | 43 | 5995 | -0.068 | -0.254 / +0.083 | 0/35 | 0 | gap=2.0;io=4.0 | 237 | -0.064 | -0.76 | -0.143 / +0.003 | -1.24 | 0 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short | 43 | 5598 | -0.058 | -0.287 / +0.131 | 0/34 | 0 | ma=w20 | 223 | +0.078 | 1.08 | -0.255 / +0.255 | -1.59 | 0 |
| RW7-gapdn-bounce-early-short | 43 | 26164 | -0.058 | -0.275 / +0.121 | 0/36 | 0 | gap=2.0;io=4.0 | 1025 | -0.084 | -1.41 | -0.083 / +0.033 | -1.21 | 0 |
| NS1-rsidip-rsi5pop-long | 38 | 2438 | -0.068 | +0.040 / -0.194 | 0/26 | 0 | L=30;ma=a50 | 152 | -0.016 | -0.27 | +0.092 / -0.027 | -0.26 | 0 |
| NS2-sma50break-overbought-short | 32 | 8151 | -0.054 | -0.156 / +0.103 | 2/31 | 1 | F=4.0;vband=ext1 | 925 | +0.053 | 0.57 | +0.037 / +0.053 | 0.23 | 0 |
| RW6-ns2-up3-short | 32 | 3614 | -0.021 | -0.079 / +0.088 | 3/31 | 0 | L=65;geom=t15s1 | 2257 | +0.058 | 0.56 | +0.051 / +0.107 | 0.26 | 0 |
| RW6G1-ns2-up3-vwap2sd-short | 35 | 2224 | -0.012 | -0.024 / +0.037 | 6/30 | 6 | L=65;vband=ext1 | 431 | +0.189 | 1.08 | +0.216 / +0.132 | 0.80 | 0 |
| RW8-sma50up-spikefade-short | 31 | 459 | -0.090 | -0.235 / -0.015 | 0/17 | 1 | L=25 | 151 | -0.130 | -1.35 | -0.194 / -0.118 | -1.23 | 0 |
| NS5-sma50-flush-oversold-long | 31 | 3139 | -0.043 | +0.049 / -0.139 | 0/28 | 4 | vol=2.0 | 360 | +0.005 | 0.07 | -0.017 / +0.012 | -0.16 | 0 |
| NS3-failed-vwap-reclaim-short | 32 | 10201 | -0.028 | -0.170 / +0.085 | 3/25 | 0 | sma=100;vol=2.0 | 212 | +0.139 | 2.53 | +0.133 / +0.174 | 0.97 | 2 |
| RW4-ns3-adv150-short | 27 | 8069 | -0.028 | -0.162 / +0.086 | 2/22 | 0 | F=4.0;sma=100 | 196 | +0.134 | 2.17 | +0.105 / +0.134 | 0.84 | 1 |
| NS4-pm-vwap-reclaim-oversold-short | 35 | 1692 | -0.054 | -0.162 / +0.113 | 0/23 | 0 | vol=1.5 | 190 | -0.048 | -0.96 | -0.147 / +0.299 | -2.09 | 0 |
| ST1-ordn-long-pm-t05s1 | 31 | 1628 | -0.050 | +0.019 / -0.070 | 5/26 | 5 | ma=a100 | 567 | +0.075 | 2.29 | +0.111 / +0.095 | 1.78 | 1 |
| ST2-slope20up-long-am-t05s1 | 32 | 10956 | -0.015 | +0.035 / -0.072 | 0/26 | 1 | f0=4.0;ma=w100 | 211 | -0.174 | -2.50 | -0.107 / -0.107 | -0.96 | 0 |
| ST3-rsi5up-short-pm-t1s1 | 37 | 657 | +0.017 | -0.089 / +0.029 | 4/25 | 2 | geom=t1s05;ma=a100 | 208 | +0.127 | 2.79 | +0.150 / +0.082 | 0.83 | 0 |
| ST4-emadn-long-am-t1s05 | 42 | 1300 | +0.018 | +0.144 / -0.044 | 0/28 | 3 | geom=t1s1;vband=in1 | 983 | +0.023 | 0.48 | +0.115 / -0.036 | -0.55 | 0 |
| ST5-pdbrkup-short-mid-t05s1 | 25 | 426 | -0.035 | -0.055 / +0.014 | 2/16 | 4 | geom=t1s1;vband=in1 | 323 | +0.100 | 1.33 | +0.119 / +0.131 | 0.86 | 0 |
| ST6-volspikeup-short-mid-t1s1 | 41 | 607 | +0.024 | -0.075 / +0.100 | 10/30 | 2 | ma=a100 | 237 | +0.171 | 3.23 | +0.150 / +0.175 | 1.18 | 2 |
| ST7-rsi50dn-long-pm-t1s1 | 36 | 1035 | +0.033 | +0.231 / -0.069 | 1/22 | 0 | ma=a100 | 225 | +0.122 | 1.79 | +0.335 / +0.022 | 0.17 | 0 |
| ST8-volspikedn-long-pm-t1s1 | 33 | 528 | +0.041 | +0.071 / -0.045 | 1/22 | 0 | geom=t05s1;ma=a100 | 353 | +0.079 | 2.06 | +0.056 / +0.004 | 0.08 | 1 |
| L3-gap-slope-fromopen | 21 | 4873 | -0.040 | -0.111 / +0.099 | 0/20 | 0 | fo=4.0;vol=1.5 | 2681 | +0.002 | 0.03 | -0.010 / +0.013 | -0.08 | 0 |
| L3-gap-slope-lowdist | 21 | 4156 | -0.103 | -0.243 / +0.117 | 0/20 | 0 | lod=(1.0, 1.25);vol=3.0 | 198 | -0.040 | -0.41 | -0.108 / +0.127 | -0.74 | 0 |
| L3-gap-slope-rsi5hi | 22 | 5713 | -0.037 | -0.081 / +0.026 | 0/21 | 0 | gap=-4.0;geom=t1s1 | 3174 | +0.013 | 0.23 | -0.045 / +0.110 | -0.41 | 0 |

Reddit and trigger lists: every list's best variant is in `summary.csv`. Lists with any both-regime-positive variant
(n >= 150): R14-ict-fvg-short (2 of 30; the 2025Q2 cluster above), R19-orb-fib-long (1; io 4 + with SMA100, n 216,
+0.167R, down +0.040), T-macd-dn-long (1), T-rsi5-dn-long (1), T-sma20-dn-long (3; io 4 + VWAP -2.5 SD, n 175,
+0.160R t 1.69), T-pdfail-dn-long (1), T-band05-up-short (1, exp < 0), T-band10-up-short (1, exp < 0),
T-band10-dn-long (3; against SMA20, n 558, +0.208R, t 1.10, WF < 0.6). None meets the bar.

### 2.5 Answer to the key question
No indicator setting changes the up/down asymmetry of these setups. Across 145 lists, RSI length / levels, EMA pairs,
SMA lengths, VWAP SD bands, volume, in-play, gap, threshold and exit variants leave longs positive only in up
sessions and shorts only in down sessions; both-regime-positive variants are 1.4% of those with n >= 150 and almost all are
small-n, single-point results. The exception is one layer - **"against the SMA100" on afternoon conditional stacks**
(ST6, NS3 / RW4, ST1, ST8) - which is plausibly a "stretched intraday vs the multi-session average" reversion, and for
ST1 / ST8 mostly an afternoon effect. That is what is staged for Testing; everything else stays failed.

Files: `NOTES.md`, `results.csv` (4,663 configurations, every stat), `summary.csv` (per list), `controls.csv`,
`finalists.json`, `verify.json`, `build_check.json`, `modules/`, `account_testing_w1.yaml`; code `build_extras.py`,
`eng.py`, `families.py`, `run.py`, `l3.py`, `report.py`, `finalists.py`, `controls.py`, `verify.py`, `add_backlog.py`,
`npzmap.py`. Git-ignored `data/` keeps the raw config tables; the 785 MB extra columns (`data/ext`) were deleted after the run (shared disk) - `python build_extras.py` rebuilds them (~35 min) before re-running run.py / verify.py. Backlog: `sw-w1-*` (4 testing candidates, 4 failures,
1 finding, 1 live-column idea).

## 3. Locked block (rule 19, look 1) - scored once, 2026-10-10, authorised by the lead

*Lab backtest on the rule-19 locked block 2024-11-01..2025-02-28 (80 sessions: 29 up / 20 flat / 31 down; regime
cut points from the open history, as lib.regimes). Production costs. Educational only - not financial advice.*

- Script `score_locked.py` (run once with `MCF_HIST_ALLOW_LOCKED=1` set for that script only), output `locked.json`.
  The 4 modules were run exactly as staged (no edits after the scan or after these numbers). Frames from
  `research/history2y/data/locked`; `sma100_dist_pct` rebuilt from `data/cache_hist/1Min` with the same live-parity
  rule (SMA100 on 5-min closes, valid when today's bar count + 60 >= 100; prior-day bars for 2024-11-01 from open
  October 2024 data). SMA100 missing on 1.5-2.1% of rows after 12:50 (thin / new names). YAML window 09:50-15:00,
  adv20 >= 95M, first qualifying bar per symbol-day.
- Bar (look 1): exp > 0 and day-clustered t >= 1.0.

| module | n | /day | win | exp R | t | ex-best-day | up exp (n) | flat exp (n) | down exp (n) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| W1-NS3-vwapreclaim-sma100-vol2-short | 20 | 0.25 | 0.450 | -0.266 | -1.49 | -0.359 | -0.500 (12) | +0.305 (5) | -0.280 (3) | **failed_locked** |
| W1-ST6-volspikeup-sma100above-short | 26 | 0.33 | 0.462 | -0.051 | -0.31 | -0.092 | -0.179 (17) | -0.100 (4) | +0.424 (5) | **failed_locked** |
| W1-ST1-ordn-sma100below-long | 92 | 1.15 | 0.609 | -0.001 | -0.01 | -0.030 | -0.091 (22) | +0.216 (29) | -0.105 (41) | **failed_locked** |
| W1-ST8-volspikedn-sma100below-long-t05s1 | 33 | 0.41 | 0.545 | -0.031 | -0.27 | -0.082 | +0.142 (12) | -0.057 (9) | -0.184 (12) | **failed_locked** |

**All four fail.** Samples are small (20-92 trades over 80 sessions, about half the open-history rate per day), so the
test has little power, but none is even positive: the open-history numbers (t 2.1-3.2 against try-count bars of
4.2-4.8, out of 4,677 configurations) look like selection, as the try-count bar warned. For the shorts the up-session
losses are back (NS3 -0.50R, ST6 -0.18R in up sessions), i.e. the SMA100 layer did not remove the regime dependence
out of sample. Recommendation: do not apply `account_testing_w1.yaml`; the live `sma100_dist_pct` column is not needed
for these. The lineages have used look 1; any rework would face look 2 (t >= 1.5).
