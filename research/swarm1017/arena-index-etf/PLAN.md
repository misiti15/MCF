# arena-index-etf (swarm 2026-10-17) - PLAN (written before any configuration is scored)

*Educational only - not financial advice. History backtests only; nothing here is paper or live.*

Goal: candidate lab setups that trade **US equity index / sector / leveraged-and-inverse equity ETFs only**, both
sides, all day (bar close 09:50-15:00), built as AND-combinations of 2-3 arena indicators (mcf/research/arena),
starting from single-indicator cells with the best TRAIN excess vs random. Emit only quality-passing combinations as
lab modules under modules/.

## Universe (pre-declared, fixed)
Rows of these symbols with adv20 >= $95M (the live lab floor), bar close 09:50..15:00:
- Broad index: SPY QQQ IWM DIA VOO IVV VTI RSP SPLG QQQM VUG VGT IWF IVW SPYG SCHG MGK VONG VOOG MTUM SPMO MDY IJH IJR
  SPMD SPSM VO VB IWR IWO IWN IWP VTWO SCHA VLUE AVUV
- Sector / industry: XLE XLF XLV XLI XLK XLU XLP XLY XLB XLC XLRE SMH SOXX SOXQ IGV XBI IBB KRE KBE KBWB XRT XOP OIH
  XME COPX XHB ITB IYR VNQ SCHH GDX GDXJ SILJ ARKK ARKG ITA CIBR IHI URA JETS ICLN TAN VDE VFH IYW MAGS
- Leveraged / inverse equity-index and sector: SPXL SPXS SPXU UPRO SSO SDS SH SPDN TQQQ SQQQ QLD QID PSQ TNA TZA RWM
  URTY SRTY UWM TWM UDOW SDOW DDM DXD DOG SOXL SOXS TECL TECS FAS FAZ LABU LABD NUGT DUST JNUG GDXU ERX ERY DPST
  FNGU BULZ
- Excluded on purpose: single-stock leveraged ETFs (TSLL, NVDL, MSTU, CONL, ...), crypto, commodities (GLD, SLV, USO,
  UNG), bonds (TLT, TMF), volatility (UVXY, VXX) and non-US country/region funds (EEM, EFA, FXI, EWZ, ...).

## Data, split, costs (fixed)
- research/history2y/data/frames via history2y lib.load_month (locked block 2024-11..2025-02 refused; never loaded).
- Outcomes: mcf.research.arena.data.outcomes (gates.prod_r with tod entry costs, x3 on the extended tier),
  geometries t05s1 / t1s1 / t1s05, R = 0.25 x daily ATR, timed exit 15:55. One trade per symbol-day: first qualifying
  bar in the window. Day-clustered t (gates.summary).
- Indicators: arena.indicators.compute(context=False) on the ETF rows only (every indicator is per symbol-day, so this
  equals the full-frame value). Context indicators are excluded (NaN in the live frame).
- Controls: c_* = arena random same-minute control (mean over the FULL adv20 >= $95M universe); e_* = same-minute
  mean over the ETF universe only (stricter, the relevant baseline for an ETF setup). "Beats random" = excess > 0 vs
  BOTH, on train AND valid.
- TRAIN = 2024-10 + 2025-03..2025-12. VALID = 2026-01-01 onward (arena split). Regimes: history2y lib.regimes().

## Search space (every scored configuration is counted)
- Windows W (4): (950,1100), (1100,1400), (1400,1500 incl. 15:00), (950,1500 all day). Geometries (3). Sides (2).
- Condition bins per live indicator from ETF-TRAIN quantiles of all-day rows: <= q05, <= q20, <= q50, >= q50, >= q80,
  >= q95 (binary: == 1 and == 0; categorical with <= 12 values: == each value).
- Stage 0 (singles, TRAIN): every condition x W x geometry x side.
- Triggers per side (30): (a) top 20 stage-0 conditions by TRAIN excess vs the ETF control (best window/geometry per
  condition, distinct indicators, n_train >= 300); (b) top 10 cells of the arena all-universe screen
  (research/swarm1017/arena/single_screen.parquet) for that side by train excess, live, n >= 2000, distinct indicators
  not already in (a), kept with their screen bin (op, lo, hi).
- Filters (64): 16 slow-state / regime indicators x 4 bins (<= q20, <= q50, >= q50, >= q80; ETF-train quantiles):
  gap_atr, from_pc_atr, prev_range_atr, day_vs_prev_range, atr_d_pct, rvol_day, vwap_atr, fromOpen_atr, emaDiff,
  di_diff7, adx7, day_pos, dist_pdh_atr, dist_pdl_atr, sma50_dist_pct, or_high_dist_atr. Same-indicator pairs skipped
  (not counted).
- Stage 1 (pairs, TRAIN): trigger x filter x W x geometry x side.
- Stage 2 (triples, TRAIN): per side the top 150 stage-1 pairs by TRAIN day-t (n_train >= 150) x each filter on a
  third indicator (same window / geometry).
- Stage 3 (VALID, held back): only configurations passing the TRAIN screen gate are scored on VALID (no new
  configurations), then combine-equivalent full gates on train+valid.

## Gates
- TRAIN screen gate: n_train >= 150, train sessions >= 60, exp_train > 0, excess_train > 0 vs both controls, train
  up-session exp > 0 and down-session exp > 0, both train halves (2024-10..2025-07 / 2025-08..2025-12) exp > 0.
- Candidate (quality): n_total >= 200, exp > 0 after costs on train AND valid, train day-t >= bar, regime gate (up AND
  down > 0, n >= 30 each, train+valid), walk-forward share >= 0.6 (gates.walk_forward, locked months excluded), excess
  > 0 vs both controls on train AND valid, live-computable. Preference: >= 1 trade/day across the universe.
- Bar = max(1.5, sqrt(2 ln N_lineage)), N_lineage = arena 20,282 + am-long 23,032 + am-short 22,932 + mid-long 30,752
  + mid-short 30,572 + pm-both 61,440 + ETF lineages bdi/idxdip1015 1,134 + bdi/indexlink 2,995 + every configuration
  here.
- Near-miss tier (reported, NOT candidates): passes everything except the t-bar.

## Outputs
results.csv (every scored configuration: train stats; valid stats where scored), counts.json, NOTES.md, scripts,
modules/ (quality-pass only). Scratch under /tmp/.../swarm1017/arena-index-etf/, deleted at the end.

## Amendment 1 (2026-10-17, after stage 3; dated, before these points were scored)
Stage 3 gave 1 quality pass (ret3 <= q05 & di_diff7 >= q50 & atr_d_pct >= q80, long t05s1 14:00-15:00) whose valid
result is weak (t 0.50). Pre-declared neighbour grid for it, 14:00-15:00 only, every point counted in N:
ret3 <= {q05, q20} x di_diff7 {>= q50, >= q80, none} x atr_d_pct {>= q50, >= q80, >= q95} x geometry (3) = 54.
Plus robust.py concentration diagnostics on the near-miss tier (no new configurations).

## Amendment 2 (2026-10-17, after running amendment 1)
Amendment 1 assumed the pass's ret3 threshold (-0.798%) was the ETF-train q05; it is the arena all-universe screen bin
(trigger source (b)); the ETF q05 is -0.452% and q20 lower in magnitude. The 54 points scored stand (counted). Added
grid at the actual threshold and one step further: ret3 <= {-0.798, -1.2} x the same di_diff7 x atr_d_pct x geometry
= 54 more (the pass itself is one of them; 53 new).
