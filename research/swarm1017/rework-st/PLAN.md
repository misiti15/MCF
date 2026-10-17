# swarm1017 / rework-st — PLAN (pre-declared 2026-10-17, written before any configuration was scored)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits; candidates are lab modules.*

## Parents (family "L3 + ST1-ST8", Testing 1; parent = source window, FD = 950-1500)
| parent | side | geom | core (5-min bars, decided at bar close) | source window | min_adv |
|---|---|---|---|---|---|
| L3a L3-gap-slope-fromopen | short | t1s1 | gap <= -2.657 & sma20_slope_pct > 0.3724 & fromOpen > 3.46 | 1300-1430 | 0 (prefilter gap_le) |
| L3b L3-gap-slope-lowdist | short | t1s1 | gap <= -2.657 & slope > 0.3724 & 0.7817 < dist_lod_atr <= 0.9765 | 1300-1430 | 0 |
| L3c L3-gap-slope-rsi5hi | short | t05s1 | gap <= -2.657 & slope > 0.5965 & rsi5 > 70 | 1300-1430 | 0 |
| ST1 ordn-long | long | t05s1 | close x below OR low & fo < -3 & volRatio >= 1.5 & inside prior-day range | 1335-1500 | 95M |
| ST2 slope20up-long | long | t05s1 | slope20 x up & fo < -3 & buyPressure > 0 & abs(VWAP z) < 0.5 ATR | 950-1130 | 95M |
| ST3 rsi5up-short | short | t1s1 | rsi5 x above 20 & fo < -3 (fo_with, short) & above VWAP (vwap_against) & gap > +1 (gap_against) | 1335-1500 | 95M |
| ST4 emadn-long | long | t1s05 | emaDiff x below 0 & fo < -3 & rsi > 50 & rsi5 <= 20 | 950-1130 | 95M |
| ST5 pdbrkup-short | short | t05s1 | close x above PDH & fo < -3 (fo_with, short) & above SMA50 (sma50_against) | 1135-1330 | 95M |
| ST6 volspikeup-short | short | t1s1 | volRatio x above 2 & above VWAP & fo < -3 (fo_with, short) & gap > +1 (gap_against) | 1135-1330 | 95M |
| ST7 rsi50dn-long | long | t1s1 | rsi x below 50 & rsi <= 30 (rsi_ext 70) & fo < -1 & buyPressure > 0 | 1335-1500 | 95M |
| ST8 volspikedn-long | long | t1s1 | volRatio x above 2 & below VWAP & fo < -3 & macdPct > 0 & flow3 > 0 | 1335-1500 | 95M |
(Table corrected before scoring: for a short, `fo_with p` means fromOpen < -p and `*_against` means the long-side
sign.) Semantics copied 1:1 from research/bdi/fullday/*-FD.py (filters keep the parent side's sign when the trade side is flipped).
Each re-implementation is checked bar-for-bar against the FD module's own mask on one open month before scanning.

## Data and split (same as the sibling rework folders)
- research/history2y/data/frames via `research/history2y/lib.py` (open months only; the 2024-11..2025-02 locked block is never
  loaded). Bar closes 09:50-15:00. **train** = 2024-10 + 2025-03..2025-12; **valid** = 2026-01-01..2026-10-07 (end of frames).
- Costs: `mcf.research.gates.prod_r` with time-of-day entry costs (= `lab_trades`). One trade per symbol-day (first qualifying
  bar in the window) unless refire (cooldown 1, live `refire_select` semantics: every other bar of a qualifying run).
- Offline caveat: frames start at the 09:50 bar, so crosses at 09:50 are not seen offline (prev bar missing).
- Live week 2026-10-12..16 is not in the frames; quoted from research/swarm1017/week (paper, rule 7) only.

## Grid (every configuration counted, including empty ones)
Common dims: side {parent, opposite} x geom {t1s1, t05s1, t1s05} (t05s05 is not in the frames nor LabStrategy.GEOMS) x
W6 = {0950-1030, 0950-1130, 1135-1330, 1300-1430, 1335-1500, 0950-1500} = 36 per point.
- **Stage A, threshold neighbourhood + drop-one** (x 36):
  - L3 shared: gap <= {-2.0, -2.657, -3.5} x slope > {0.2, 0.3724, 0.5965, 0.8}, with third layer:
    L3a fromOpen > {2.5, 3.46, 4.5}; L3b dist_lod_atr band {(0.6,0.8], (0.7817,0.9765], (0.95,1.2], (0.7817,inf)};
    L3c rsi5 > {60, 70, 80}; and "no third layer" (12) -> 132 points.
  - ST1 fo {1,2,3,4} x vol {off,1.5,2.0} x pd_inside {on,off} = 24; ST2 fo {1,2,3,4} x bp_with {on,off} x stretch
    {0.3,0.5,0.75,off} = 32; ST3 rsi5 level {10,20,30} x fo {1,2,3,4} x vwap_against {on,off} x gap_against {0.5,1,off} = 72;
    ST4 fo {1,2,3,4} x rsi50_with {on,off} x rsi5_ext {70,80,90,off} = 32; ST5 fo {1,2,3,4} x sma50_against {on,off} = 8;
    ST6 spike level {1.5,2,3} x fo {1,2,3,4} x gap_against {0.5,1,off} = 36; ST7 rsi_ext {60,70,80} x fo {0.5,1,2,3} x
    bp_with {on,off} = 24; ST8 fo {1,2,3,4} x macd_with {on,off} x flow3_with {on,off} = 16 -> 244 points.
  376 points x 36 = **13,536**.
- **Stage B, one extra context filter** on each parent core (parent thresholds); library F (40, same as rework-ns):
  gap <0, >0, <-1, >1, |gap|<1 | vwap side <0, >0 | rvol >=1.5, <1 | atrPct terciles (train cuts) | Mon..Fri, notMon,
  notFri | SPY fromOpen >0, <0, >0.5, <-0.5, |.|<0.25 [live code needed] | breadth >0.5, <0.5 [live code needed] |
  stock-minus-SPY fromOpen >0, <0 [live code needed] | slope >0, <0 | near/off HOD, near/off LOD | heat <=-30, >=30 |
  buyPressure <0, >0 | RSI5 >=70, <=30.  11 x 40 x 36 = **15,840**.
- **Stage C, filter pairs:** 11 x 780 x side x geom x W in {source window, 0950-1500} = **102,960**.
- **Stage D, refire (cd1) instead of first-signal:** every Stage B configuration = **15,840**.
- **Declared N_study = 148,176** (ST share 106,704; L3 share 41,472). Finalist neighbour checks are counted on top.
- Lineage: ST (stack1009) 120,542 incl. opp1014 + ~150 timeofday/refire/cutoff looks -> N_ST ~ 227,400 -> bar t >= 4.97.
  L3 (primitives/escalation/marcoflow/layering) 274,247 + ~50 -> N_L3 ~ 315,800 -> bar t >= 5.03.

## Same-minute random baseline
Mean production R (same side, same geom) of all names in the parent's universe at the same date+bar: adv20 >= 95M for ST,
all lab names (min_adv 0) for L3. Excess = trade R - baseline.

## Gates (fixed now)
Screen: n_train >= 150, n_valid >= 50, n_total >= 200, exp_train > 0 and exp_valid > 0 (production cost).
1. regime gate (`gates.regime_split` + `lib.regimes()`: exp > 0 in up AND down sessions, n >= 30 each);
2. walk-forward share >= 0.6 (`gates.walk_forward`, locked months excluded);
3. beats same-minute random: excess > 0 on train AND valid, and excess day-t >= 2 on train+valid;
4. plateau (Stage A): >= 2/3 of one-step threshold neighbours positive on train and valid;
5. ex-best-day expectancy > 0.
"Candidate" = screen + gates 1-3 + 5 (+4 for Stage A). Reported against the family bar (pass/fail stated). De-dup: rank by
min(train t, valid t); drop a candidate whose trades overlap >= 60% with a higher-ranked one; at most 15 modules; a module is
written only for finalists with day-t >= 2 on train+valid. If none pass, say so.

Exits: lab geometries only (frames hold no 1-min paths). Scale-out / trailing are live-supported but need path data - not
scored. Hold-to-close / time exits are not supported live (code needed).
