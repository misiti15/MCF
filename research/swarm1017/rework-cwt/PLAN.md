# swarm1017 / rework-cwt — PLAN (pre-declared 2026-10-17, written before any configuration was scored)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits; candidates are lab modules.*

## Parents (Testing 2, CWT batch 2026-10-12; modules research/bdi/cwt/live/, signal code cwt_live_lib.py)
| family | parent setups (live) | kernel | 2-yr open history (live/NOTES.md) | live week 10-12..10-16 (paper, rule 7) |
|---|---|---|---|---|
| B1 CWT04 backside short | lh-a25 / lh-a15 (trig 2, 10:30-15:00, t1s1); vwaptest-a25 (t1s1) / -a15 (t1s05) (trig 1, 09:50-15:00) | `b1(a, trig)`; run >= a ATR from open, drop >= 40% and close < VWAP arms; trig 1 = VWAP test, trig 2 = 38-62% retrace + close < prior low | +0.186 / +0.142 / -0.171 / -0.172 R (t 0.90 / 0.77 / -1.28 / -3.74) | 3 trades |
| B2 CWT13 VWAP stretch | z05/z075 long (t05s1 11:00-15:00 / t1s1 09:50-15:00), z05/z075 short (t1s1 11:00-15:00) | `b2(z, side)`; prior bar at session extreme >= z ATR from VWAP, this bar lower high / higher low | -0.080 / -0.046 / -0.069 / -0.077 | 72 trades, z05-short -0.345R (41) |
| B4 CWT12 coil / flag long | coil-k4 (t05s1), coil-k6 (t1s05), 09:50-11:30; flag-s1 (t05s1, 09:50-15:00) | `b4a(nco)` (>= 3 HOD touches, nco tight bars under HOD), `b4b(s)` (push >= s ATR, 30-50% pullback above VWAP, close > push high) | -0.075 / -0.070 / -0.074 | coil-k4 165 tr -0.081R |
| B5 CWT05 panic flush long | m05/m075 x v3/v5 (t05s1, 09:50-15:00) | `b5(m, v)`; >= m ATR drop in 6 bars to a new LOD with vol_climax >= v in the last 3 bars, then first close > prior high | -0.088..-0.154 | 23 trades |
| A7 CWT09 gap-down bounce short | g5/g10 x vwaploss (trig 1) / lowerhalf (trig 2), 10:30-15:00, structural stop (09:30-10:30 high) or t1s05, min_adv $1M | `a7(gap, trig)` | -0.031..+0.141 (t <= 0.78) | 76 trades, g5 pair -0.57 / -0.70R |

## Data and split
- research/history2y/data/frames via `research/history2y/lib.py` (open months only; the locked block 2024-11..2025-02 is
  never loaded, MCF_HIST_ALLOW_LOCKED never set), plus the 09:35-09:45 and 15:05-15:55 rows of
  research/bdi/cwt/test_b/data/headtail.parquet (the live-like frame of research/bdi/cwt/live/verify.py; tail rows are only
  used by the exit simulator). Decision bars 09:50-15:00.
- **train** = 2024-10 + 2025-03..2025-12; **valid** = 2026-01-01..2026-10-07 (end of frames).
- Population: adv20 >= $95M (B1, B2, B4, B5, as live); A7 adv20 >= $1M (as live; every frame symbol).
- Costs: `mcf.research.gates.prod_r` with time-of-day entry costs (= `lab_trades`) for t1s1 / t05s1 / t1s05; the same cost
  model inside a 5-minute path simulator (copy of research/swarm1017/rework-cwt14/sim.py, parity-checked against the frame
  geometries on one month) for the other exits. R = 0.25 x daily ATR, flat 15:55.
- Generalised numba kernels (`kern.py`) reproduce cwt_live_lib exactly at the parent parameters (parity check on 2 months
  against cwt_live_lib before scoring; any mismatch is reported).

## Exits (7; + S for A7)
| id | rule | live |
|---|---|---|
| t1s1, t05s1, t1s05 | lab geometries | yes (GEOM) |
| t05s05 | +0.5R / -0.5R | **no: LabStrategy.GEOMS lacks it (code needed)** |
| so1 | t1s1, bank half at +0.5R, rest stop to breakeven | yes: scale_out_r 0.5 + live_scale_out: true |
| so05 | t05s1, bank half at +0.25R, rest to breakeven | yes: scale_out_r 0.25 + live_scale_out: true |
| tr1 | t1s1, trail 0.5R behind best once +0.5R | yes: trail_r 0.5, trail_after_r 0.5 (Signal management) |
| S (A7 only) | structural stop = 09:30-10:30 high, no target, flat 15:55 | yes (GEOM "S" + stop_price) |

## Context filters F (40; decision-time only)
SPY fromOpen >0, <0, >0.3, <-0.3 | breadth (share of $95M names above their open, same bar) >0.5, <0.5, >0.6, <0.4 |
SPY gap >0, <0 | volumeRatio >=1.5, >=2, <1 | vwapDistPct >0, <0 | gap >0, <0, |gap|<1, >2, <-2 | atrPct low / mid / high
tercile (cuts from train rows) | Mon..Fri | stock fromOpen >0, <0, >1, <-1 | sma20_slope_pct >0, <0 | rsi <30, >70 |
sma50_dist_pct >0, <0 | SPY and stock fromOpen same sign / opposite sign.
SPY / breadth filters (12) need live code (the LabStrategy frame has no index or universe context) — marked `code_needed`.

## Windows
W6 = {0950-1030, 1030-1130, 1130-1300, 1300-1500, 0950-1500, parent window} (deduplicated per family; A7 windows start
at 1030 because its condition is defined up to 10:30: {1030-1130, 1130-1300, 1300-1500, 1030-1500}).

## Signal variants (kernel grids; parents in bold)
- B1: a {1.0, **1.5**, 2.0, **2.5**, 3.0} x drop {0.3, **0.4**, 0.5} x trig {**1**, **2**} = 30
- B2: stretch side {above, below} x z {0.25, **0.5**, **0.75**, 1.0, 1.25, 1.5} = 12 (parent sides: above->short, below->long)
- B4a coil: nco {2, 3, **4**, **6**, 8} x touches {2, **3**, 4} = 15
- B4b flag: s {0.5, **1.0**, 1.5, 2.0} x pullback band {**0.3-0.5**, 0.2-0.6, 0.2-0.4, 0.4-0.6} = 16
- B5: m {**0.5**, **0.75**, 1.0, 1.25} x v {2, **3**, **5**, 8} = 16
- A7: gap {3, **5**, 7, **10**, 15} x trig {**1**, **2**} = 10

## Grids (every configuration counted, empty ones included)
- **A (variants)**: every variant x side {parent, opposite} x 7 exits (8 for A7) x W x pick {first, refire cooldown 1}.
- **B (one filter)**: every variant x 40 filters x side {parent, opposite} x exits {t1s1, t05s1, t1s05, so1, so05, tr1}
  (+S for A7) x W {parent window, full window} x first.
- **C (filter pairs)**: parent variants only x 780 pairs x parent side x exits {parent exit, t1s1, t05s1} x parent window x first.
- Counts are computed by the scan and written to NOTES.md / results.csv (N per family).

## Lineage and bars (bar = max(1.5, sqrt(2 ln N_lineage)), N_lineage = prior + this study)
- B1: test_b N_lineage 356,381 (+ refire1014 extras)
- B2: test_b 192 + bdi1012 80 = 272
- B4 (coil + flag one lineage): test_b 160 + bdi1012 160 + top5_1015 22 + top5_1016 12 = 354
- B5: 30,970 (longs1013 lineage incl. CWT05) + bdi1012 320 = 31,290
- A7: test_a lineage bar 4.76 -> N ~ 83,300

## Gates (fixed now; a candidate needs ALL)
1. n_all >= 200 (train+valid), exp > 0 after costs on train AND on valid.
2. Day-clustered t on train+valid >= the family bar.
3. Regime gate (gates.regime_split with lib.regimes(), open-history terciles): exp > 0 in up AND down sessions, n >= 30 each.
4. Walk-forward share (gates.walk_forward, 3-month train / 1-month test, locked months excluded) >= 0.6.
5. Beats random entries at the same minute: mean(r - same-minute universe mean for the same side/exit) > 0 on train AND valid.
6. Plateau: at least one neighbouring kernel variant (one parameter one step away) with the same side/exit/window/filters
   is also exp > 0 on train and valid.
7. Exit must be live-supported, or is flagged code_needed.
Screening order: train is used to search; valid is used to choose; the locked block is the lead's (never touched here).
Near-misses (pass 1, 3, 5 but not 2) are reported as such, not as candidates.
