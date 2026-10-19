# tf1019/nearmiss - the 12 swarm1017 near-miss setups (Testing 2) on 1/3/5/10/15-minute decision bars (pre-declared)

Declared 2026-10-19 ~03:22 UTC (Sun 2026-10-18 23:22 ET), before any scoring. Educational only - not financial advice.

## Setups (config/account_testing2.yaml NM-*; module, window, geometry, min_adv unchanged)
"Week-2 Testing 2 additions" = these same 12 (commits e1e55395 = 5 swarm1017 near-misses, 94b6a183 = 7 made
runnable by Q8 features); nothing else was added to Testing 2 after the 2026-10-12 CWT batch.

| name | module | window | geom | min_adv | context |
|---|---|---|---|---|---|
| NM-RWN3-ns3-spyup-early-short | rework-ns/RWN3 | 950-1030 | t1s1 | 95M | spy_fo |
| NM-RWN4-ns2-spyup05-notfri-short | rework-ns/RWN4 | 950-1130 | t05s1 | 95M | spy_fo |
| NM-RWN5-ns3-mon-weakrs-short | rework-ns/RWN5 | 950-1130 | t1s1 | 95M | spy_fo |
| NM-RWR1-exh150-gapdn-spyup-pm-short | rework-rw/RWR1 | 1300-1500 | t05s1 | 150M | spy_fo |
| NM-RWR3-ns3-qqqup-early-short | rework-rw/RWR3 | 950-1030 | t1s1 | 150M | qqq_fo (live refire NOT modelled) |
| NM-RWR4-ns2-up3-qqqup-slopedn-short | rework-rw/RWR4 | 950-1100 | t05s1 | 95M | qqq_fo |
| NM-ETF-late-dip-di-long | arena-index-etf/AR-ETF | 1400-1500 | t05s1 | 95M | ETF list (16 ETFs in core) |
| NM-AR-AM-gapdown-capitulation-long | final/AR-AM | 950-1100 | t1s1 | 95M | - |
| NM-AMS-N1-quiet-morning-short | final/AMS-N1 | 1000-1100 | t05s1 | 95M | - |
| NM-PM-gapdn-above-pdh-rvol-short | final/NM-PM-S | 1400-1500 | t1s1 | 95M | - |
| NM1-cwt09-g10-vwaploss-short | final/NM1 | 1030-1500 | t1s1 | 1M | - |
| NM-HL-T75-pm-long | final/NM-HL-T75 | 1300-1500 | t05s1 | 125M | - |

## Harness and universe
`mcf.research.timeframes.run_module_tf`, symbols="core" (80 symbols, all five timeframes; like-for-like),
context=True for the spy_fo/qqq_fo setups (SPY and QQQ are in core, so spy_fo/qqq_fo are exact), split "open"
(train 2024-10 + 2025-03..12; valid 2026-01..10-07; forward 10-08..10-16 reported only, never used to choose).
Locked block 2024-11..2025-02 never loaded or scored.

**Arena modules (AR-ETF, AR-AM, AMS-N1, NM-PM) need a fix to run off 5-min bars:** `arena.indicators.compute` lays
rows on a fixed 5-minute slot grid (STEP=5, 63 slots from 09:50). On other bar sizes, rows off the grid become NaN
and "k bars ago" silently means k x 5 minutes. AS-IS on m-minute bars therefore patches the grid
(STEP=m, first slot = first bar close >= 09:50, N_SLOTS = bars to 15:00) so every row is a slot and one slot = one
bar. Parity: at m=5 the patched compute must equal the original exactly.

## Variants
(a) AS-IS: module unchanged; every lookback in BARS (e.g. RSI14 = 14 bars = 14 / 42 / 70 / 140 / 210 min; ret12 =
    12 bars; volumeRatio = 20-bar volume mean; SMA50 = 50 bars).
(b) TIME-EQUIVALENT (TE): every bar-count lookback n scaled to the 5-minute clock span:
    rolling windows / indicator lengths -> max(2, floor(n*5/m + 0.5)); pure shifts / returns -> max(1, floor(n*5/m+0.5)).
    Recomputed from the same 1-min SIP cache (resample -> same formulas as heat.heat_frame / setup_lab.extra_features),
    locked dates dropped at load: rsi(14), rsi5(5), sma50_dist_pct(50), sma20_dist_pct(20), sma20_slope_pct
    (SMA20 vs 5 bars ago), buyPressure(19), volumeRatio(20; feeds rvol_day), bear_div (20-bar high, RSI 20-bar max),
    rsiHeat / momentumHeat (shifts 4, 9) / priceActionHeat (20-bar range); vwapHeat is session-based (unchanged).
    In-frame (from frame OHLC): ret3 / ret12 -> ret over scaled bars; di_diff7 -> DI(scaled 7).
    Unchanged (clock/session based): fromOpen, vwapDistPct, gap, gap_atr, atr_d(_pct), dist_pdh_atr,
    day_vs_prev_range, spy_fo / qqq_fo, CWT09 a7 clock rules (above-VWAP by 10:30, close below VWAP from 10:30).
    One-bar "cross on this bar" tests (prev-bar VWAP/SMA50 cross) stay one decision bar (noted).
    m=5 TE == AS-IS (not counted twice). TE builder parity at m=5 vs frames_tf columns is checked.

## Configuration count (this task)
AS-IS 12 x 5 = 60; TE 12 x 4 = 48; total **108**. No window, threshold or geometry is changed.

## Bar: t_required = max(1.5, sqrt(2 ln N_lineage)), N_lineage = prior + 108 (all 108 added to every lineage)
- RWN3/RWN4/RWN5 (NS rework): 165,764 -> 165,872 (4.90)
- RWR1 (exhaustion): ~967,000 -> 967,108 (5.25)
- RWR3/RWR4 (NS/RW rework): ~114,000 -> 114,108 (4.83)
- AR-ETF: 266,882 -> 266,990 (5.00)
- AR-AM, AMS-N1: implied by their stated bar 4.62 -> exp(4.62^2/2) ~ 43,100 -> 43,208
- NM-PM: implied by bar 4.89 -> ~155,600 -> 155,708
- NM1 (A7): ~99,000 -> 99,108 (4.80)
- NM-HL-T75 (heat): ~34,000 -> 34,108 (4.57)
Informational: this task's family alone N=108 -> 3.06.

## Gates (a candidate must pass ALL on its timeframe)
day-clustered t >= t_required(N_lineage) and tf.summarize verdict gates (regime up AND down > 0 with n >= 30 each;
walk-forward share >= gates.WF_MIN_SHARE); exp_r > 0 on train AND on valid; excess vs the random same-minute
baseline > 0. Passing versions -> modules/ (parent copy + BAR_MINUTES = m). Forward never used to choose.
