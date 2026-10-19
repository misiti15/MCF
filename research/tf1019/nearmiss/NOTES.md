# tf1019/nearmiss - results (Educational only - not financial advice)

Backtest on history only (not paper, not live). 108 configurations scored as pre-declared in PLAN.md: 12 Testing-2
swarm1017 near-miss setups x 5 decision-bar sizes as-is (60) + 4 time-equivalent (48). Core 80 symbols, each setup's
own window / geometry / min_adv, production costs with time-of-day entry costs, first qualifying bar per symbol-day.
Locked block 2024-11..2025-02 never loaded. Forward 10-08..10-16 reported in results.csv only, never used to choose.

## Failures first
- **0 of 108 pass all gates. No modules written.**
- Fail counts (one config can fail several): regime gate 86 (most because a regime has n < 30 on the core
  universe), walk-forward < 0.6 or too few folds 67, train exp <= 0 on 36, valid exp <= 0 on 24, excess vs random <= 0
  on 21. Every one of the 108 is below its lineage t bar (4.57-5.25). Best t is 3.66.
- **Low power, and this matters.** The near-misses were found on the full lab universe (1,226 symbols). The core
  80 holds only a slice of their signals, so the 5-min as-is rows do not reproduce the published numbers. RWN3 has
  41 trades here against 388 in its docstring; ETF has only 16 ETFs in core. Small-n rows (< ~100 trades) cannot
  pass the regime or walk-forward gates whatever their mean. Read them as "not shown", not "shown to fail".
- Structural zeros: AR-AM as-is on 10 and 15 min has n = 0 (ret12 = 120 / 180 min is NaN until after its 11:00
  window end). On 15-min TE, ret12 becomes 4 bars, but the first 15-min close is 10:00 and the window ends before
  11:00, so the trade count is 0 again. AMS-N1 as-is on 1-min has n = 0 (a 5-bar SMA20 slope <= -0.74% almost never
  happens over 5 minutes). RWR1 TE on 1-min has n = 0 (RSI(25) > 90 is very rare).

## Closest (all fail; t only)
- **NM-HL-T75-pm-long, 10-min bars, time-equivalent heat lookbacks** (RSI 7 bars = 70 min, price-position range 10
  bars, momentum shifts 2/5): n 545 on 204 sessions, train +0.090R (t 2.15), valid +0.106R (t 2.59), overall t 3.66 vs
  bar 4.57. Regime up +0.128 / flat +0.050 / down +0.126, walk-forward 0.69 (16 folds), excess over same-minute random
  +0.106R (t 3.88). Ex-best-day +0.096R, best day = 11% of P/L. Neighbours are positive in both halves: 3m as-is,
  3m TE, 5m as-is, 15m TE. 10m as-is is not (train -0.011). It would pass this family's own bar (N = 108 -> 3.06)
  but not the lineage bar, and the lineage bar is the rule. Forward: 18 trades on 3 sessions, +0.30R (too few to
  count).
- NM-ETF-late-dip-di-long, 5-min as-is (its native timeframe): t 3.12 vs 5.00. It fails on t only, with regime and
  WF passing. No other timeframe beats 5 min.

## Timeframe pattern (descriptive, not a selection)
- No timeframe wins consistently. The as-is 1-min version is usually the worst. Its lookbacks shrink 5x, and for the
  NS/RW reworks train exp is negative in 5 of 6 setups.
- Time-equivalent rescaling helps AR-AM and RWN4/RWN5 on 1 to 3 minutes, and HL-T75 on 10 minutes. It hurts RWR4 and RWN4
  on 10 minutes.
- None of this clears a bar. The forward data (7 sessions, 10-08..10-16) is too short to read either way.

## Method checks
- TE builder parity: unscaled at m = 1 / 5 / 15, it reproduces the frames_tf columns exactly (max diff 0.0, 11 columns).
- Arena modules: `arena.indicators.compute` assumes a 5-minute slot grid (STEP = 5, 63 slots). On 1/3/10/15-minute
  frames it would silently NaN off-grid rows, and "k bars ago" would turn into k x 5 minutes. run.py patches the grid
  per timeframe (one slot = one bar). The patched compute at m = 5 equals the original exactly for all 4 arena
  modules, and every row of the 1/3/10/15-min frames maps to a slot. **Anyone else running arena modules through
  mcf.research.timeframes on bars other than 5-min needs the same patch, or the results are wrong.**
- Not modelled: the RWR3 live refire (cooldown 1). Only the first bar per symbol-day is taken.
- One-bar cross tests stay one decision bar in TE.

Files: PLAN.md (pre-declared), te_build.py, run.py, results.csv (all 108 rows, every gate and the lookbacks in
minutes), grid.md (setup x timeframe), best.md (best timeframe per setup). Trades were in scratch, now deleted.
