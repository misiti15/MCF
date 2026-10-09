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

## 2. Results
(appended after scoring)
