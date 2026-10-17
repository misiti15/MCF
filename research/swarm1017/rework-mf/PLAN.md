# swarm1017 / rework-mf — PLAN (pre-declared, written 2026-10-16 before any configuration was scored)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits; candidates are lab modules.*

## Parents (family "MF1-MF5 (+FD)")
Core masks (all short, all `heat <= -30 & buyPressure < -0.25` plus):

| parent | extra core layer | geom | parent window | FD window |
|---|---|---|---|---|
| MF1-945-flowsell-vwapup | vwapDistPct > 0.05 | t1s05 | 950-1030 | 950-1500 |
| MF2-open-rsimidhi-flowsell | 55 <= RSI14 <= 65 | t1s05 | 950-1100 | 950-1500 |
| MF3-open-flowsell-rsi5hi | RSI5 > 70 | t1s1 | 950-1100 | 950-1500 |
| MF4-h40-open-flowsell | heat <= -40 | t05s1 | 950-1100 | 950-1500 |
| MF5-flowsell-vwapup-rsi5hi | vwapDistPct > 0.05 & RSI5 > 70 | t1s1 | 950-1500 | 950-1500 |

The -FD version of each parent is the same core mask with window 950-1500, so parent and FD are two windows of one grid.

## Data and split
- research/history2y/data/frames (open months only; loader `research/history2y/lib.py`; the locked block 2024-11..2025-02
  is never loaded). min_adv 95,000,000 (adv20), bar close 09:50-15:00 as live.
- **train** = 2024-10-01..2025-12-31 (2024-10 + 2025-03..2025-12); **valid** = 2026-01-01..2026-10-07 (end of frames).
- Costs: `mcf.research.gates.prod_r` with time-of-day entry costs (= `lab_trades` convention). One trade per symbol-day
  (first qualifying bar) unless the refire dimension says otherwise (cooldown 1, as `refire_select`).
- Live week 2026-10-12..16 is not in the frames; it is reported from research/swarm1017/week (paper, rule 7) only.

## Grid (every configuration counted, including empty ones)
- Sides: short (parent) and long (opposite side, same signal). Geoms: t1s1, t05s1, t1s05. (t05s05 does not exist in
  the frames or in LabStrategy.GEOMS — not tested; would need new outcome columns + live code.)
- Windows W (bar close): 950-1030, 950-1100, 1100-1300, 1300-1500, 950-1500.
- **Stage A, threshold neighbourhood:** heat cut {-20,-30,-40,-50} (MF4: {-30,-40,-50,-60}) x bp cut {-0.15,-0.25,-0.35,-0.50}
  x parent param (MF1 vwap > {0, 0.05, 0.25}; MF2 RSI band {50-60, 55-65, 60-70}; MF3/MF5 RSI5 > {60, 70, 80}; MF4 none)
  x side x geom x W. = 4 x (16x3x2x3x5) + 16x2x3x5 = **6,240**.
- **Stage B, one extra filter** on each parent core (original thresholds), filter library F (33):
  gap <0, >0, <-1, >1 | fromOpen <0, >0, <-1, >1 | vwapDistPct <0, >0 | volumeRatio >=1.5, <1 |
  atrPct low / high tercile (cut points from the train superset) | day-of-week Mon..Fri, not-Mon, not-Fri |
  SPY fromOpen >0, <0 [live code needed] | breadth (share of universe above its open) >0.5, <0.5 [live code needed] |
  stock fromOpen minus SPY fromOpen >0, <0 [live code needed] | sma20_slope_pct >0, <0 | dist_hod_atr <0.25, >0.5 |
  sma50_dist_pct >0, <0.
  x side x geom x W = 5 x 33 x 2 x 3 x 5 = **4,950**.
- **Stage C, filter pairs:** 5 parents x C(33,2)=528 x side x geom x W in {parent window, 950-1500} = **31,680**.
- **Stage D, refire (cooldown 1) instead of first-signal:** every Stage B configuration re-scored with refire = **4,950**.
- **Declared total N_study = 47,820.**
- Lineage before this study (MF family): 82,068 (marcoflow 8,012 + rework1008 74,056, per rework1008 NOTES) + trendguard
  1,120 + regime1009 1,052 + swarm1013 402 + indexlink 912 + bdi1014 480 + timeofday/refire/cutoff ~50 = **~86,084**.
  N_lineage ~ 133,904 -> **bar t >= sqrt(2 ln N) = 4.86** (day-clustered t on train+valid).

## Gates (fixed now)
Screen: n_train >= 150, n_valid >= 50, n_total >= 200, exp_train > 0 and exp_valid > 0 (production cost).
Candidate ("quality") gates on train+valid (open history):
1. regime gate (`regime_split`: exp > 0 in up AND down sessions, n >= 30 each);
2. walk-forward share >= 0.6 (`walk_forward`, locked months excluded);
3. beats random entries at the same minute: mean excess (trade R minus the mean production R of all min_adv names at the
   same date+bar, same side/geom) > 0 on train AND valid, and excess day-t >= 2 on train+valid;
4. plateau (Stage A only): >= 2/3 of the threshold neighbours (one step in heat or bp) have exp > 0 on train and valid;
5. ex-best-day expectancy > 0.
Reported for every candidate: day-clustered t vs the 4.86 bar (pass/fail stated; nothing is called "edge" below the bar).
De-duplication: candidates ranked by min(train t, valid t); a candidate is dropped if its trades overlap >= 60% with a
higher-ranked one. At most 15 reported as modules. If none pass, say so.

Exits: only lab geometries are scored (frames hold no 1-minute paths). Scale-out / trailing are live-supported but need
path data - not scored here. Hold-to-close / time exits are not supported live (code needed).
