# swarm1017 / rework-rw — PLAN (pre-declared 2026-10-17, written before any configuration was scored)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits; candidates are lab modules.*

## Parents (family "RW1-RW7 FD + exhaustion"; all short, t1s1, R = 0.25 x daily ATR, exit by 15:55)
| parent | core mask | min_adv | live FD window | lineage |
|---|---|---|---|---|
| RW1 | heat<=-20 & bp<-0.35 & 55<=RSI14<=65 & gap<0 | 95M | 950-1500 | MF2 (MF) |
| RW7 | heat<=-20 & bp<-0.15 & 55<=RSI14<=65 & gap<0 | 95M | 950-1500 | MF2 (MF) |
| RW3 | heat<=-20 & bp<-0.35 & RSI5>80 & gap<0 | 95M | 950-1500 (also Primary) | MF3 (MF) |
| RW5 | heat<=-30 & bp<-0.15 & RSI5>80 & gap<0 | 95M | 950-1500 (also Primary, refire cd 6) | MF3/MF5 (MF) |
| RW2 | RSI5>90 & sma20_dist>1 & bear_div | 150M | 950-1500 | exhaustion |
| EXH | RSI5>90 & sma20_dist>1 & bear_div, prefilter new_high_100m | 95M | 950-1500 (live: >= 11:10 because of the prefilter) | exhaustion |
| RW4 | VWAP cross up this bar & fromOpen<-2 & sma50_dist>0 | 150M | 950-1500 (refire cd 1) | NS3 (NS) |
| RW6 | SMA50 cross up this bar & fromOpen>3 & RSI14>=60 | 95M | 950-1500 (refire cd 1) | NS2 (NS) |
(RW6G1 is out of scope: its VWAP-band guard needs 5-min volume, which the 2-year frames do not carry.)

## Data and split
- Open 2-year frames research/history2y/data/frames via research/history2y/lib.py (locked 2024-11..2025-02 never loaded).
- **train** = 2024-10-01..2025-12-31 (2024-10 + 2025-03..2025-12); **valid** = 2026-01-01..2026-10-07 (end of frames).
- Bars: decision bar close 09:50-15:00, adv20 >= min_adv (point in time). Costs: `mcf.research.gates.prod_r` with
  time-of-day entry costs (the `lab_trades` convention). One trade per symbol-day (first qualifying bar) unless refire.
- Same-minute random baseline: mean production R of every adv20>=95M name at the same date+bar, same side/geom.
- Live week (paper, rule 7): research/swarm1017/week (setups_live.csv, rework_trades.csv) — descriptive only.

## Grid (every configuration counted, including empty ones)
Sides: short (parent) and long (opposite side). Geoms: t1s1, t05s1, t1s05 (t05s05 has no outcome columns in the frames
and is not in LabStrategy.GEOMS — not tested; would need new frames + live code). = 6 side-geoms (SG).
Windows W (bar close): 0950-1030, 0950-1100, 1100-1300, 1300-1500, 0950-1500 (5). Exhaustion lineage (RW2/EXH) Stage A
also gets 1110-1500 (the live new_high_100m prefilter cut-off) = 6.

**Stage A — threshold neighbourhood and each condition removed in turn (rule 18):**
- G-MF2 (RW1, RW7 share it): heat {-10,-20,-30,-40} x bp {-0.15,-0.25,-0.35,-0.50} x RSI14 band {50-60, 55-65, 60-70,
  removed} x gap {<0, <-1, removed} = 192 cores x 6 SG x 5 W = **5,760**.
- G-MF3 (RW3, RW5 share it): heat {-10,-20,-30,-40} x bp {-0.15,-0.25,-0.35,-0.50} x RSI5 {>70, >80, >90, removed} x
  gap {<0, <-1, removed} = 192 x 30 = **5,760**.
- G-EXH (RW2, EXH): RSI5 {>80,>85,>90,>95} x sma20_dist {>0.5,>1,>1.5,>2} x bear_div {required, removed} x min_adv
  {95M,150M,300M} = 96 x 6 SG x 6 W = **3,456**.
- G-RW4: fromOpen {<-1,<-2,<-3} x sma50_dist {>0, removed, <0} x min_adv {95M,150M} = 18 x 30 = **540**.
- G-RW6: fromOpen {>2,>3,>4} x RSI14 {>=50, >=60, >=70, removed} x min_adv {95M,150M} = 24 x 30 = **720**.
- Stage A total **16,236**.

**Filter library F (45, all known at the decision bar):**
gap <0, >0, <-1, >1, <-2, >-1 | fromOpen <0, >0, <-1, >1 | vwapDistPct <0, >0 | volumeRatio >=1.5, <1 |
atrPct low / high tercile (cuts from train) | Mon..Fri, notMon, notFri |
SPY fromOpen >0, <0, <-0.5, >0.5 [live code] | QQQ fromOpen >0, <0 [live code] |
breadth (share of the adv>=95M universe above its open at this bar) >0.5, <0.5, <0.35, >0.65 [live code] |
SPY gap >0, <0 [live code] | stock fromOpen - SPY fromOpen >0, <0 [live code] | sma20_slope_pct >0, <0 |
dist_hod_atr <0.25, >0.5 | dist_lod_atr <0.25, >0.5 | sma50_dist_pct >0, <0.
(The SPY / QQQ / breadth items are the "day-class gates decided at signal time".)

- **Stage B — one extra filter** on each of the 8 parent cores: 8 x 45 x 6 SG x 5 W = **10,800**.
- **Stage C — filter pairs**: 8 x C(45,2)=990 x 6 SG x 2 W = **95,040**; W = {0950-1500, 0950-1100} for RW1/RW7/RW3/
  RW5/RW4/RW6, {0950-1500, 1300-1500} for RW2/EXH.
- **Stage D — refire (cooldown 1, LabStrategy.refire_select)** instead of first-signal: every Stage B config = **10,800**.
- Parents reproduced (8, at their live refire setting) = 8.
- **Declared total N_study = 132,884.**

## Lineage and bar (try-count t on train+valid, day-clustered)
- MF lineage (RW1/RW3/RW5/RW7): prior ~133,904 (rework-mf NOTES, incl. its 47,820) + this study's MF-lineage share.
- NS lineage (RW4/RW6): prior ~84,000 (owner1008 7,374 + rework1008 74,056 + trendguard/indexlink/time-of-day ~2,500).
- Exhaustion lineage (RW2/EXH): prior ~934,500 (rework1008 NOTES).
- Bar = max(1.5, sqrt(2 ln N_lineage)) computed in gate.py; expected ~4.9 (MF), ~4.8 (NS), ~5.25 (exhaustion).

## Gates (fixed now; same as the sibling rework-mf so results are comparable)
Screen: n_train >= 150, n_valid >= 50, n_total >= 200, exp_train > 0 and exp_valid > 0 (production cost).
Quality gates (train+valid): (1) regime gate (`regime_split`, up AND down > 0, n >= 30 each); (2) walk-forward share >= 0.6;
(3) beats same-minute random: mean excess > 0 on train AND valid and excess day-t >= 2; (4) Stage A plateau >= 2/3 of
one-step neighbours (first two parameters) positive on train and valid; (5) ex-best-day exp > 0.
**A candidate is "quality / bar-passing" only if it passes every gate AND t_all >= its lineage bar.** Gate-passers below
the bar are reported as near-misses (Testing-only at most, never live funds). De-dup: rank by min(t_tr, t_va); drop if
>= 60% symbol-day overlap with a higher-ranked one; at most 15 modules.

## Exits
Only lab geometries are scored (frames hold no 1-minute paths). Scale-out (live_scale_out + scale_out_r) and trailing are
live-supported but cannot be scored on the frames; the live week's exit replays (week/rework_trades.csv) are reported
descriptively for this family. Hold-to-close / time exits are NOT supported live (code needed).
