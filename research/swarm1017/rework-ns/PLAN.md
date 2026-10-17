# swarm1017 / rework-ns — PLAN (pre-declared 2026-10-17, written before any configuration was scored)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits; candidates are lab modules.*

## Parents (family "NS1-NS5 + RW6G1 (+FD)")
| parent | side | geom | core (5-min bars, decision at bar close) | parent window | FD window |
|---|---|---|---|---|---|
| NS1-rsidip-rsi5pop-long | long | t05s1 | RSI14 crosses below 40 (prev > 40) & RSI5 >= 80 & fromOpen > 2 | 950-1130 | 950-1500 (refire cd3) |
| NS2-sma50break-overbought-short | short | t1s1 | close crosses above SMA50 & RSI14 >= 60 & fromOpen > 2 | 950-1130 | 950-1500 |
| NS3-failed-vwap-reclaim-short | short | t1s1 | close crosses above VWAP & above SMA50 & fromOpen < -2 | 950-1130 | 950-1500 (refire cd1) |
| NS4-pm-vwap-reclaim-oversold-short | short | t1s05 | close crosses above VWAP & RSI14 <= 30 & fromOpen > 2 | 1130-1500 | 950-1500 |
| NS5-sma50-flush-oversold-long | long | t1s1 | close crosses below SMA50 & RSI14 <= 30 & fromOpen < -2 | 950-1130 | 950-1500 |
| RW6G1-ns2-up3-vwap2sd-short | short | t1s1 | NS2 core with fromOpen > 3 & no unresolved close above VWAP+2SD | 950-1130 (refire cd1) | 950-1500 (refire cd1) |

Parent and FD are two windows of one grid. All min_adv 95M (adv20).

## Data and split
- research/history2y/data/frames (open months only via `research/history2y/lib.py`; locked block 2024-11..2025-02 never loaded),
  bar close 09:50-15:00. **train** = 2024-10 + 2025-03..2025-12; **valid** = 2026-01-01..2026-10-07 (end of frames).
- The RW6G1 VWAP-SD guard needs volume, which the frames lack: it is computed from the 1-min SIP cache
  (data/cache_hist/1Min) for the symbol-days carrying an NS2-type row, as research/bdi/trendguard did (locked rows dropped at load).
- Costs: `mcf.research.gates.prod_r` with time-of-day entry costs (= `lab_trades` convention). One trade per symbol-day
  (first qualifying bar) unless refire (cooldown 1, every other bar of a qualifying run, as live `refire_select`).
- Offline caveat (all parents): frames start at the 09:50 bar, so a crossing whose previous bar is 09:45 is not visible
  offline (live would see it). Same caveat as the parents' own history results.
- Live week 2026-10-12..16 is not in the frames; it is quoted from research/swarm1017/week (paper, rule 7) only.

## Grid (every configuration counted, including empty ones)
Common dims: side {parent, opposite} x geom {t1s1, t05s1, t1s05} (t05s05 does not exist in the frames or in
LabStrategy.GEOMS: not tested) x window W.
- W6 = {950-1030, 950-1130, 1130-1300, 1130-1500, 1300-1500, 950-1500}.
- **Stage A, threshold neighbourhood** (x side x geom x W6 = 36 per point):
  - NS1: RSI14 cross level {35,40,45} x RSI5 min {70,80,90} x fromOpen min {1,2,3} = 27
  - NS2: RSI14 min {50,55,60,65,70} x fromOpen min {1,2,3,4} = 20
  - NS3: SMA50 layer {required, dropped} x fromOpen max {-1,-2,-3,-4} = 8
  - NS4: RSI14 max {30,35,40} x fromOpen min {1,2,3} = 9
  - NS5: RSI14 max {25,30,35} x fromOpen max {-1,-2,-3} = 9
  - RW6G1: fromOpen min {2,3,4} x RSI14 min {55,60,65} x guard {none, k1.5, k2, k2.5} = 36
  total points 109 -> **3,924**.
- **Stage B, one extra filter** on each parent core (parent thresholds), filter library F (40):
  gap <0, >0, <-1, >1, |gap|<1 | vwapDistPct <0, >0 | volumeRatio >=1.5, <1 | atrPct low/mid/high tercile (train cuts) |
  Mon..Fri, not-Mon, not-Fri | SPY fromOpen >0, <0, >0.5, <-0.5, |.|<0.25 [live code needed] | breadth (share of min_adv
  universe above its open, same bar) >0.5, <0.5 [live code needed] | stock fromOpen minus SPY fromOpen >0, <0 [live code
  needed] | sma20_slope_pct >0, <0 | dist_hod_atr <0.25, >0.5 | dist_lod_atr <0.25, >0.5 | heat <=-30, >=30 |
  buyPressure <0, >0 | RSI5 >=70, <=30.
  6 parents x 40 x 36 = **8,640**.
- **Stage C, filter pairs:** 6 x C(40,2)=780 x side x geom x W in {parent window, 950-1500} = **56,160**.
- **Stage D, refire (cooldown 1) instead of first-signal:** every Stage B configuration re-scored with refire = **8,640**.
- **Declared total N_study = 77,364.**
- Lineage before this study: NS lineage N 82,102 at research/bdi/trendguard (owner1008 scan 7,374 + rework1008 + earlier)
  + trendguard study 5,158 + regime1009 1,052 + timeofday/refire1014/cutoff/demote ~100 = **~88,400**.
  N_lineage ~ 165,800 -> **bar: day-clustered t >= sqrt(2 ln N) = 4.90** on train+valid.

## Gates (fixed now)
Screen: n_train >= 150, n_valid >= 50, n_total >= 200, exp_train > 0 and exp_valid > 0 (production cost).
Quality gates on train+valid (open history):
1. regime gate (`gates.regime_split` with `lib.regimes()`: exp > 0 in up AND down sessions, n >= 30 each);
2. walk-forward share >= 0.6 (`gates.walk_forward`, locked months excluded);
3. beats random entries at the same minute: excess R (trade R minus the mean production R of all min_adv names at the same
   date+bar, same side/geom) > 0 on train AND valid, and excess day-t >= 2 on train+valid;
4. plateau (Stage A only): >= 2/3 of one-step threshold neighbours have exp > 0 on train and valid;
5. ex-best-day expectancy > 0.
"Candidate" = screen + gates 1-3 + 5 (+4 for Stage A). Reported against the 4.90 bar (pass/fail stated; nothing below the
bar is called an edge). De-duplication: rank by min(train t, valid t); drop a candidate whose trades overlap >= 60% with a
higher-ranked one. At most 15 modules. If none pass, say so.

Exits: only lab geometries are scored (frames hold no 1-minute paths). Scale-out (live_scale_out) / trailing are live-
supported but need path data - not scored here. Hold-to-close / time exits are not supported live (code needed).
