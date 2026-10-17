# swarm1017 / rework-misc — PLAN (pre-declared 2026-10-17, written before any configuration was scored)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits; candidates are lab modules.*

## Parents (family "heat / orb / momentum / LIQ")
| parent | rule (live) | live week 10-06..10-16 (paper, rule 7) | 2-yr history (research/history2y/rescore.csv) |
|---|---|---|---|
| heat_fade_short(-FD) | short score = -(rsiH+paH-momH-vwapH) - 8*8/atr_d >= 11.3, fromOpen<0, 09:50-10:30 (FD 09:50-15:00), t1s1, adv>=125M | p/t1 82 tr -0.42R; FD 240 tr -0.12R | n 14,433, +0.017R t 0.68; up -0.20 / down +0.15 (short beta) |
| heat_fade_long(-FD) | long score = rsiH+paH-momH-vwapH-5*clip(fo,±3) - 4*8/atr_d >= 57.5, gap>0, 11:05-13:30 (FD 09:50-15:00), t1s1 | p/t1 111 tr -0.27R; FD 91 tr -0.52R | n 14,460, -0.046R t -1.16 |
| orb20_a | 09:30-09:49 OR, direction of 09:49 close vs open, VWAP agrees, top-20 rvol>=1.5, stop-entry at OR extreme to 11:30, stop 0.5 OR / target 0.75 OR | 14 tr | n 2,827, -0.000R t 0.0 |
| intraday_momentum | SPY/QQQ/IWM/DIA, prev close->10:00 return >= 0.25% abs, enter 15:30 in that direction, hold to close | 5 tr | n 1,151, -0.067R t -2.7 |
| LIQ-orl-sweep-open15-s25-long | OR-low sweep x0.15 ATR, 15-min reclaim (open trigger), structural stop, 2.5R | 120 tr -0.04R | n 13,335 -0.001R (S geom) |
| LIQ-pdl-sweep-open15-vwap-long | PD-low sweep x0.05, 15-min reclaim, VWAP >= 2R above, 1R stop, VWAP target, BE + time stop | 1 tr | n 160 +0.088R t 0.58 |

## Data and split
- research/history2y/data/frames via `research/history2y/lib.py` (open months only; the locked block 2024-11..2025-02 is
  never loaded or scored). Bar close 09:50-15:00 (frames hold 09:50-15:00 rows; lab outcomes exit by 15:55).
- **train** = 2024-10 + 2025-03..2025-12; **valid** = 2026-01-01..2026-10-07 (end of frames).
- Costs: `mcf.research.gates.prod_r` with time-of-day entry costs (= `lab_trades`). Lab geometries only
  (t1s1 / t05s1 / t1s05; R = 0.25 x daily ATR). t05s05 does not exist in frames or LabStrategy.GEOMS - not tested.
- One trade per symbol-day (first qualifying bar inside the window) unless the refire dimension is on
  (LabStrategy `refire_select`, cooldown 1).
- Population: min_adv 125M for heat families (as live), 95M for ORB / IM / LIQ (as live).

## Filter library F (37; decision-time features only)
gap <0, >0, <-1, >1 | fromOpen <0, >0, <-1, >1 | vwapDistPct <0, >0 | volumeRatio >=1.5, <1 | atrPct low / high tercile
(cuts from train) | Mon..Fri, notMon, notFri | SPY fromOpen >0, <0, >0.5, <-0.5 **[live code needed]** | breadth (share of
min_adv names above their open, same bar) >0.5, <0.5 **[live code needed]** | sma20_slope_pct >0, <0 | dist_hod_atr <0.25, >0.5 |
dist_lod_atr <0.25, >0.5 | sma50_dist_pct >0, <0 | rsi <30, >70.

## Grids (every configuration counted, empty ones included)
Sides: parent side and the opposite side. Geoms: t1s1, t05s1, t1s05. W5 = {0950-1030, 1030-1130, 1130-1300, 1300-1500, 0950-1500}.
- **HS heat-short** (core T=11.3, gate fo-): A threshold T{5,11.3,15,20,25,30} x gate{fo-,none,gap-,gap+,fo+} x W5 x side2 x geom3 = 900;
  B core + 1 filter: 37 x W5 x 2 x 3 = 1,110; C core + filter pair: 666 x W{0950-1030, 0950-1500} x short x 3 = 3,996;
  D refire on B = 1,110. **7,116**
- **HL heat-long** (core T=57.5, gate gap+; W6 = W5 + parent 1105-1330): A T{30,40,50,57.5,65,75} x gate{gap+,none,gap-,fo+,fo-} x W6 x 2 x 3 = 1,080;
  B 37 x W6 x 2 x 3 = 1,332; C 666 x W{1105-1330, 0950-1500} x long x 3 = 3,996; D refire on B = 1,332. **7,740**
- **ORB** (lab version: OR = 09:30-09:50 high/low read from dist_hod/lod at the 09:50 bar; signal = first 5-min close beyond the
  OR extreme after 09:50; dir = sign(fromOpen at 09:50); parent core = breakout in dir, VWAP agrees at 09:50, volumeRatio(09:50) >= 1.5,
  window 0955-1130). W5o = {0955-1030, 0955-1130, 1130-1300, 1300-1500, 0955-1500}.
  A dir-rule{agree, any} x vwap{on,off} x rvol{none,>=1,>=1.5,>=2,>=3} x W5o x side{with, fade} x 3 = 600;
  B core + 37 x W5o x 2 x 3 = 1,110; C core + pair 666 x W{0955-1130, 0955-1500} x with x 3 = 3,996; D refire (every fresh cross) on B = 1,110. **6,816**
- **IM intraday momentum** (r30 = prev close -> 10:00 return, from gap and fromOpen at the 10:00 bar; entry bar E{1030,1100,1200,1300,1400,1500};
  15:30 entry / hold-to-close is NOT scorable from frames and NOT supported by LabStrategy - code needed).
  IM-ETF: own r30, thr{0.25,0.5,1.0} x side{with,against} x 3 x E6 = 108;
  IM-univ: SPY r30 thr{0.25,0.5,1.0} x stock rule{any, own r30 same sign, same sign & |own|>=1} x side{with,against} x 3 x E6 = 324;
  B IM-univ core (0.25, same sign) + 37 x E{1030,1300,1500} x 2 x 3 = 666. **1,098**
- **LIQ** sweep events (port of liq_live_lib, levels from decision-time features: OR low/high = LOD/HOD at the 10:00 bar, PD = prior-day
  low/high): level{OR,PD} x sweep{low->long, high->short} x x{0.05,0.10,0.15,0.25} x trig{open,lvl} x k{5,15} = 64 event sets.
  A 64 x side{reversal, continuation} x 3 x W4{0950-1100, 1100-1300, 1300-1500, 0950-1500} = 1,536; A-refire 1,536;
  B 2 parent cores (ORL x.15 open k15; PDL x.05 open k15, reversal long) x (37 + VWAP room >= 0.5 ATR) x W4 x 2 x 3 = 1,824;
  C 2 cores x pair 666 x W 0950-1500 x reversal x 3 = 3,996. **8,892**
- **Declared total N_study = 31,662.** (arithmetic corrected; the grids themselves are unchanged: HS A 900, HL A 1,080, ORB A 600.)

## Lineage and bars (t = day-clustered t on train+valid; bar = max(1.5, sqrt(2 ln N_lineage)))
- heat (HS + HL share the 2026-10-06 heat study): 19,200 + top5_1014/1015 34 + rescore 2 + this 14,856 = ~34,092 -> **4.57**
- ORB: setup screen 15 + 6,816 = 6,831 -> **4.20**
- IM: setup screen 15 + 1,098 = 1,113 -> **3.74**
- LIQ: reddit1012liq 7,716 + nightly1014 2 + 8,892 = 16,610 -> **4.41**

## Gates (fixed now)
Screen: n_train >= 150, n_valid >= 50, n_total >= 200, exp_train > 0 and exp_valid > 0 (production cost).
Quality candidate (all on train+valid):
1. regime gate (`gates.regime_split`, exp > 0 in up AND down sessions, n >= 30 each);
2. walk-forward share >= 0.6 (`gates.walk_forward`, locked months excluded);
3. beats random entries at the same minute: excess = R minus mean production R of all min_adv names at the same date+bar (same
   side/geom); mean excess > 0 on train AND valid, excess day-t >= 2 overall;
4. ex-best-day expectancy > 0;
5. plateau (Stage A threshold winners): >= 2/3 of one-step threshold neighbours positive on train and valid;
6. t >= family bar -> "passes"; below bar -> reported as near-miss only (never called edge).
De-dup: ranked by min(t_train, t_valid); dropped if >= 60% trade overlap with a higher-ranked candidate. Max 15 per family.
Exits: lab geometries only. Scale-out / trailing (live-supported) need 1-min paths - not scored. Hold-to-close / time exits need code.

## Amendment before scoring (2026-10-17)
- LabStrategy modules carry ONE side. ORB and IM configurations that trade both directions are scored as the union of two
  modules (a long module and a short module, each first-signal per symbol-day) - exactly what two live modules would do.
  A candidate from them ships as a module pair.
- ORB lab version uses the 5-minute CLOSE beyond the OR extreme (the parent uses an intrabar stop-entry at OR +-1c) and the
  09:50 bar's volumeRatio instead of the cross-sectional top-20 20-minute rvol rank (not in the lab frame).
