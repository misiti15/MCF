# BDI rework round 2026-10-08 (rule 18): strongest existing material

*Educational only - not financial advice. Backtest (lab) results only; nothing here was tested live.*

## 0. Pre-declared grid (written 2026-10-08 15:16 UTC, BEFORE any configuration was scored)

### Inputs reworked (lineages)
- `research/owner1008` scan (7,374 configs; NS1-NS5 probation; holdout look 1 used: NS1 weak +, all others -).
- `research/primitives/marcoflow` flow-sell family (MF1-MF5 probation; MF1 holdout look 1 weak +).
- `exhaustion_short` (`research/setups2/candidates/volume_flip_1.py`, live).
- Article near-misses (`research/bdi/articles/NOTES.md`): contrarian fades of upward breaks (covered by the side flips of
  the up-break triggers below). The Bollinger-squeeze near-miss needs BB columns that are NOT in the live lab frame
  (LabStrategy's `mask(df)` only sees the heat + extra_features columns), so it cannot be a LabStrategy module without a
  runner change; it is left to its own backlog entry (`bdi-art-squeeze-vol-rework`) and not scored here.
- Not reworked here (other agent): VWAP bands, anchored VWAP, volume profile, 9 EMA.
- MarcoFlow history (`data/marcoflow.sqlite`): descriptive only (section 1), used as rationale, not tuned on.

### Data and split
- `research/setups2/data/{train,valid}.parquet` only: train 2026-06-30..08-25 (40 sessions), valid 2026-08-26..09-15 (14).
- `data/cache/1Min` read with parquet filter `timestamp < 2026-09-16`, only to compute ADV (dollar volume) tiers.
- No locked holdout, no `data/cache_q2`, no `MCF_*_ALLOW_*`.

### Scoring (as research/owner1008/scan_fast.py)
- First qualifying bar per symbol-day, entry at that bar's close; outcome `r_{side}_{geom}`, geom in t1s1 / t05s1 / t1s05
  (R = 0.25 x daily ATR, exits by 15:55, lab 1c/side) minus production haircut (2 x 1 bps x price + 0.02) / R.
- Day-clustered t (se = sqrt(sum_d (S_d - n_d mu)^2) / N). Train halves split at the median train date.
- Valid ex-best-day expectancy. Trades/day = n / sessions in the split.
- Configs with train n < 60 are counted as tried, not scored.
- Only columns of the live lab frame are used, so every mask runs unchanged in `LabStrategy`.
  Previous-bar values are taken within the symbol-day (the lab frame's 09:50 row has no previous row; live it has the
  09:45 bar - a known, accepted small difference, same as NS1-NS5).

### Families
**F1 EVT - event on an extended mover** (rework of owner1008 scan):
- T trigger (10): rsi_x40dn (RSI14 crosses below 40), rsi_x60up, x_sma20_up, x_sma20_dn, x_sma50_up, x_sma50_dn,
  vwap_reclaim, vwap_loss, hod_break (high of day rises on this bar), lod_break.
- M move-from-open (17): none; up/down by pct {1,2,3,4}%; up/down in daily-ATR units (close-open)/atr_d {0.5,0.75,1.0,1.5}.
- S state (12): none, rsi>=60, rsi>=70, rsi<=30, rsi<=40, rsi5>=80, rsi5<=20, above_sma50, below_sma50,
  vol>=2x (volumeRatio), gap_up (gap >= +0.5%), gap_dn (gap <= -0.5%).
- W window (5, bar close ET): early 09:50-10:30, am 09:50-11:30, mid 10:30-13:00, pm 11:30-15:00, all 09:50-15:00.
- side 2 x geom 3.  Count: 10 x 17 x 12 x 5 x 6 = **61,200**.

**F2 MFX - MarcoFlow flow-sell family** (rework of MF1-MF5):
- H heat (4): none, heat <= -20, <= -30, <= -40.
- B buyPressure (3): < -0.15, < -0.25, < -0.35.
- E extension (8): none, vwapDistPct > 0.05, rsi5 > 70, rsi5 > 80, 55 <= rsi <= 65, rsi > 65, fromOpen > 1, fromOpen < -1.
- G gap (3): any, gap > 0, gap < 0.
- W (6): 09:50-10:30, 09:50-11:00, 09:50-11:30, 11:00-13:00, 13:00-15:00, 09:50-15:00.
- side 2 (flip = same mask traded long) x geom 3.  Count: 4 x 3 x 8 x 3 x 6 x 6 = **10,368**.

**F3 EXH - exhaustion neighbourhood** (rework of exhaustion_short / volume_flip_1, plus its mirror):
- bear version: rsi5 > {85,90,95} x sma20_dist_pct > {0.5,1.0,1.5} x bear_div {required, not} x upper_wick >= 0.5
  {required, not}; bull mirror: rsi5 < {15,10,5} x sma20_dist_pct < {-0.5,-1.0,-1.5} x bull_div x lower_wick.
- W (5): 09:50-11:30, 11:00-13:00, 12:00-15:00, 13:00-15:00, 09:50-15:00. side 2 x geom 3.
- Count: 2 x (3 x 3 x 2 x 2) x 5 x 6 = **2,160**.

**F4 CMB - two weak, uncorrelated components** (selected on TRAIN only):
- Components: the 20 best F1-F3 configs by train day-t among train n >= 60, train exp > 0, both train halves > 0,
  greedily de-duplicated (train symbol-day Jaccard < 0.5 with every higher-ranked pick).
- For every pair with the same side and geom: OR (first trigger of either) and SEQ A->B, SEQ B->A (B fires after A
  fired earlier the same day; entry at B). <= 190 x 3 = **<= 570**.

**F5 MGT - managed re-entry / stop-and-reverse** (top 10 de-duplicated train components, same selection):
- RE: second trade, same side and geom, at the first qualifying bar after the first trade's exit bar (stop checked
  first inside a bar, as the lab).
- SAR x 3 geoms: after the first trade is stopped, the opposite side at the close of the stop bar.
- BOTH: first trade + RE scored together.  10 x 5 = **50**.
- These are separate LabStrategy modules (the mask recomputes the parent trade from the day's bars), so the runner is
  unchanged.

**F6 ADV tiers**: the 50 best configs that pass every gate except plateau/baseline (or the 50 best by min(train t,
valid t) if fewer pass) x min ADV {150M, 300M} (applied via YAML `min_adv`; ADV = mean daily $ volume of the prior 20
sessions, min 5, from data/cache/1Min). **100**.

**Declared total: <= 74,448 configurations.** At p = 0.05 roughly 3,700 false positives are expected; configs overlap
heavily, so the effective number is smaller but still large.

### Gates (fixed in advance)
1. train exp > 0 and valid exp > 0 after the haircut; 2. valid n >= 30; 3. valid day-clustered t >= 1.5;
4. both train halves > 0; 5. beats the same-side / same-window / same-geom random baseline (mean over every bar in the
window, after haircut) on train AND valid; 6. plateau: neighbours' mean train and mean valid exp > 0 and >= 2/3 of
neighbours positive on valid (neighbours with train n < 60 are skipped; < 2 scored neighbours = fail);
7. report valid ex-best-day (must be reported, not gated). Also reported: same-time control (each trade vs the mean of
all bars at the same tod).

Neighbours (one step in one ordered dimension): F1 M threshold +-1 step within the same unit and sign; S rsi>=60<->70,
rsi<=30<->40; W early<->am, am<->mid, am<->all, mid<->pm, pm<->all. F2 H, B one step; E rsi5>70<->80; W list
adjacency. F3 rsi5 and sma20 one step; W list adjacency. F4/F5/F6: plateau = the parent(s) and their F1-F3 plateau.

### Finalists (max 8)
Pass gates 1-6; de-duplicate (valid symbol-day Jaccard > 0.5 -> keep the higher min(train t, valid t)); rank by
min(train t, valid t), then show trades/day and daily-P&L correlation + trade overlap with the live lab-reproducible
setups (exhaustion_short, heat_fade_short, heat_fade_long, MF1-MF5, NS1-NS5).

<!-- results below are written after scoring -->

## 1. MarcoFlow history: what separated winners from losers (descriptive, not tuned on)
`data/marcoflow.sqlite`: 2,709 closed paper trades and 166,584 resolved 5-minute signal observations.
- **Paper trades lost on both sides.** Shorts averaged -0.23% (win rate 37%, n 2,369) and longs -0.19% (n 340).
- **Exits drove the losses.** Stop-loss exits averaged -1.64% (n 719) against +1.34% for take-profit exits (n 444).
- **Signals: shorting strength beat shorting weakness.** Short signals with RSI(14) > 50 averaged +0.026 to +0.037%, with 56-57% wins. Short signals with RSI < 40 averaged -0.03%. Every long RSI bucket was negative.
- **Regime:** bear-regime signals were the worst (-0.13%).

All of this points the same way as the lab result below: **fade strength / selling into a bounce**, not chasing weakness, and no long edge.

## 2. Counts
| family | declared | tried | scored (train n >= 60) |
|---|---|---|---|
| F1 EVT | 61,200 | 61,200 | 35,850 |
| F2 MFX | 10,368 | 10,368 | 9,054 |
| F3 EXH | 2,160 | 2,160 | 2,148 |
| F4 CMB | <= 570 | 174 (only same side + geom pairs exist among the 20 components) | 66 |
| F5 MGT | 50 | 50 | 14 |
| F6 ADV | 100 | 100 | 56 |
| post-declared diagnostics (re-entry on RW1/RW3, NOT finalist-eligible) | - | 4 | 4 |
| **total** | <= 74,448 | **74,056** | 47,192 |

- **Multiple testing.** Of the 42,743 scored configs with valid n >= 30, only 389 (0.9%) reach valid t >= 1.5, while 27,233 reach t <= -1.5.
  - Reason: the same-side random baselines are deeply negative after costs (table below).
  - So a positive config is rare. But with 74k tries, roughly 3,700 false positives at p = 0.05 are still the right yardstick for "a few dozen pass".
- **Lineage totals (rule 18):**
  - MF lineage: 8,012 + 74,056 = 82,068.
  - NS (owner1008) lineage: 7,374 + 74,056 = 81,430.
  - exhaustion lineage: about 934,500 (swarm 855,600 + earlier reworks 4,866 + 74,056).

Random baseline (every bar in the window, after the haircut), train / valid, R per trade:
| window | long t1s1 | short t1s1 | short t05s1 | short t1s05 |
|---|---|---|---|---|
| 09:50-10:30 | -0.173 / -0.172 | -0.063 / -0.108 | -0.094 / -0.130 | -0.075 / -0.113 |
| 09:50-11:00 | -0.155 / -0.166 | -0.080 / -0.115 | -0.104 / -0.135 | -0.086 / -0.118 |
| 09:50-11:30 | -0.146 / -0.158 | -0.090 / -0.122 | -0.111 / -0.145 | -0.092 / -0.128 |
| 11:30-15:00 | -0.128 / -0.207 | -0.107 / -0.073 | -0.114 / -0.096 | -0.105 / -0.099 |

## 3. Results: failures first
**Gate funnel** (configs passing each gate on its own / all gates):
| family | both splits > 0 | valid t >= 1.5 | halves > 0 | beats baseline | ALL gates |
|---|---|---|---|---|---|
| F1 | 480 | 415 | 1,065 | 13,054 | 2 |
| F2 | 170 | 207 | 125 | 2,957 | 6 |
| F3 bear | 36 | 8 | 24 | 582 | 2 |
| F3 bull | 6 | 1 | 8 | 519 | **0** |
| F4 | 7 | 2 | 65 | 45 | 1 |
| F5 | 2 | 1 | 10 | 5 | **0** |
| F6 | 50 | 27 | 37 | 54 | 8 |

### Failures
- **Long side: nothing passes.**
  - F1 has 272 long configs positive on both splits; none survives halves + t + plateau.
  - The F3 bullish-exhaustion mirror: 0 pass.
  - F2 masks traded long: 8 are positive on both splits, but none passes. RW1 flipped long is -0.37R on train and -0.39R on valid (t -5).
  - The best long near-miss is the SMA50 flush long (section 4).
- **F1 new trigger/filter angles add nothing.**
  - HOD/LOD-break triggers, ATR-normalised move filters, and the gap_up/gap_dn states: none of these produced a passer.
  - The two F1 passers are NS2-family shorts (% move filters).
- **F4 two weak components:**
  - The 20 components were picked on train only, and 16 of them are negative on valid. The train top-t list is mostly noise.
  - 174 pairs give 1 passer (an OR of RW1 with a PM VWAP-reclaim short). It only dilutes RW1: valid +0.125R vs +0.171R.
- **F5 re-entry / stop-and-reverse:**
  - Re-entries rarely fire, because parents seldom re-qualify after their exit (1 RE config scorable: valid -0.270R).
  - SAR was scorable for 1 parent: negative on all 3 geometries on both splits (train -0.19 to -0.28R).
  - The RW1/RW3 re-entry diagnostic found 2-3 extra trades in 54 sessions.
  - **Re-entry is not a volume lever for these setups.**
- **Exit geometry:** every passer is t1s1. On RW1, t05s1 (+0.087 / +0.046R) and t1s05 (+0.034 / +0.105R) are weaker. The 1R target is what pays.
- **Bollinger-squeeze near-miss:** not scorable as a LabStrategy module (it needs BB columns that are not in the live frame). Left in `bdi-art-squeeze-vol-rework`.
- **Regime caveat (important):** the valid window (08-26..09-15) favoured shorts.
  - All 13 live lab-reproducible setups are positive on valid (`data/live_ref.csv`): MF3 +0.187R, NS5 +0.477R, and so on.
  - Yet 4 of them are negative on train, and their locked holdouts were mostly negative.
  - A strong valid t on a short is therefore weaker evidence than it looks. Train strength and both train halves matter more.

### Passers (19 configs in 10 lineages; lineage = valid+train symbol-day overlap coefficient > 0.5)
- **The grouping rule was tightened after scoring.** The declared Jaccard rule does not catch subsets: an ADV tier is a subset of its parent rule.
- So passers were additionally grouped into lineages by overlap coefficient. This tightening can only remove finalists, never add them.
- Of the 9 lineage representatives, the lowest-ranked one was cut by the 8-finalist cap: ADV>=150M bp<-0.35 & RSI>65 & gap<0. It is listed as a near-miss.

### Finalists (max 8; modules in `modules/`, verified against the scan in `verify.json`)
In the table, `tpd` is trades per day. "Same-time edge" is each trade measured against the mean of all bars at the same time of day. "corr live" is the daily-P&L correlation with the sum of all live lab-reproducible setups; "max" is the most-correlated single setup. "overlap" is the share of symbol-days also traded by a live setup.

| id | rule (short, t1s1) | train exp / t / n / tpd | train halves | valid exp / t / n / tpd | valid ex-best | same-time edge tr / va | corr live (max) | overlap |
|---|---|---|---|---|---|---|---|---|
| RW1-gapdn-bounce-flowsell | heat<=-20, bp<-0.35, 55<=RSI<=65, gap<0, 09:50-11:00 | +0.186 / 2.47 / 323 / 8.1 | +0.235 / +0.146 | +0.171 / 2.45 / 132 / 9.4 | +0.127 | +0.29 / +0.29 | 0.20 (MF2 0.51) | 10% |
| RW2-exhaustion-noon-adv150 | rsi5>90, >1% above SMA20, bear_div, 12:00-15:00, ADV>=150M | +0.137 / 1.73 / 939 / 23.5 | +0.150 / +0.121 | +0.128 / 1.89 / 145 / 10.4 | +0.074 | +0.24 / +0.20 | 0.31 (exhaustion_short **0.92**) | 64% |
| RW3-gapdn-rsi5pop-flowsell | heat<=-20, bp<-0.35, rsi5>80, gap<0, 09:50-11:00 | +0.124 / 1.59 / 211 / 5.3 | +0.233 / +0.046 | +0.163 / 1.56 / 92 / 6.6 | +0.110 | +0.22 / +0.29 | 0.05 (NS3 -0.17) | 25% |
| RW4-ns3-adv150 | NS3 (VWAP reclaim, down>2%, above SMA50, AM), ADV>=150M | +0.139 / 1.51 / 176 / 4.4 | +0.089 / +0.170 | +0.357 / 1.72 / 35 / 2.5 | +0.231 | +0.23 / +0.49 | 0.28 (NS3 **0.97**) | 100% |
| RW5-heat30-flowsell-rsi5pop-gapdn | heat<=-30, bp<-0.15, rsi5>80, gap<0, 09:50-11:00 | +0.102 / 1.06 / 147 / 3.7 | +0.028 / +0.162 | +0.273 / 2.13 / 52 / 3.7 | +0.204 | +0.20 / +0.39 | 0.34 (MF5 0.40) | 53% |
| RW6-ns2-up3 | NS2 with up>3% (was 2%), AM | +0.098 / 0.78 / 217 / 5.4 | +0.083 / +0.113 | +0.203 / 2.34 / 45 / 3.2 | +0.145 | +0.20 / +0.33 | 0.08 (NS2 **0.89**) | 78% |
| RW7-gapdn-bounce-early | heat<=-20, bp<-0.15, 55<=RSI<=65, gap<0, 09:50-10:30 | +0.059 / 0.67 / 175 / 4.4 | +0.089 / +0.038 | +0.153 / 1.84 / 69 / 4.9 | +0.091 | +0.12 / +0.27 | -0.08 (NS2 0.41) | 7% |
| RW8-sma50up-spikefade | SMA50 up-cross, up>3%, RSI14<=30, 09:50-15:00 | +0.026 / 0.25 / 86 / 2.2 | +0.033 / +0.016 | +0.295 / 3.18 / 38 / 2.7 | +0.221 | +0.13 / +0.37 | 0.09 (MF5 0.29) | 27% |

Gates passed by every finalist:
- train and valid > 0, valid n >= 30, valid t >= 1.5, both train halves > 0;
- beats the random baseline on both splits;
- plateau positive.

Also true of every finalist:
- ex-best-day stays positive;
- the same-time control edge is positive on both splits.

**RW1 detail** (the only finalist with train t > 2 and valid t > 2):
- 7 of 9 train weeks and 4 of 4 valid weeks positive.
- Its heat <= -20 neighbours at t1s1 are positive on valid in every window.
- Train is positive only up to 11:00/11:30, so the effect is a morning one.
- Heat matters: the same rule without a heat filter is -0.04 to +0.02R on train.
- ADV tiers make it stronger: ADV >= 150M is +0.293 / +0.239R, and ADV >= 300M is +0.393 / +0.383R with fewer trades.
- Mechanism (the MarcoFlow lesson): a name that gapped down bounces to a mid-high RSI while the 19-bar signed volume stays heavily negative. Sellers are distributing into the bounce.

## 4. Near-misses (status `rework` in the backlog)
- **High-volume variant:** buyPressure < -0.35 & RSI > 65 & gap < 0, 09:50-11:00 short.
  - It passes every gate, but train is about flat after costs: +0.005R, t 0.10, n 1,032.
  - Valid is +0.131R, t 2.70, n 499, **35.6 trades/day**.
  - At ADV >= 150M: train +0.012R, valid +0.129R, 17/day.
  - It was cut by the 8-finalist cap. Testing account only, if the owner wants volume.
- **NS1 itself** (rsi_x40dn + up>2% + rsi5>=80, AM, long t05s1) fails the plateau gate.
  - Train +0.090R, t 1.30, n 68; valid +0.319R, t 3.90, n 31.
  - Its neighbours average 0.000 on valid. It is a lone spike.
- **SMA50 flush long, 10:30-13:00** (x_sma50_dn & down > 1% & RSI <= 30) fails only the halves gate.
  - Train +0.047R, t 1.07, n 675; half 1 is -0.087.
  - Valid +0.130R, t 1.81, n 206, 14.7/day.
  - This is the best long candidate in the round.
- **NS2, 09:50-10:30 only** fails only halves.
  - Train +0.255R, t 2.02, n 131 (halves +0.476 / -0.117).
  - Valid +0.304R, t 2.25, n 40.
- **Exhaustion rsi5 > 95, 13:00-15:00, ADV >= 150M** fails only the t gate.
  - Train +0.289R, t 2.27; valid +0.195R, t 1.41, n 47.
- **Fail only on plateau:**
  - x_sma20_up & up>1% & RSI>=60, early short: valid +0.362R, t 2.61 (fewer than 2 scorable neighbours).
  - The F4 OR pair: train t 3.40, valid t 2.16 (it has no plateau definition, and it is RW1-diluted).

## 5. Recommendation (the lead decides; the holdouts are not scored by BDI)
- **Primary account candidate: RW1 only.**
  - It is the only result strong on both splits independently, additive to the live book (10% trade overlap, 0.20 portfolio correlation), and at about 8-9 trades/day.
  - Its lineage (MF2) already used holdout look 1, so this is **look 2: t >= 1.5 is needed on both locked holdouts**.
  - If it passes, it goes to paper as probation (holdout re-look), per rule 18.
  - If it clears only look-1 strength, it goes to the Testing account.
- **Testing account:**
  - RW3 and RW7: additive, low correlation, weaker train.
  - RW5: 53% overlap with MF3/MF5.
  - RW8: train t 0.25.
  - The high-volume flow-sell variant (near-miss) for volume.
- **Changes to existing live setups (not new setups):**
  - RW2 = exhaustion_short with a 12:00 start and min_adv 150M. It gives about 1.4-1.5x the trades/day of the live rule at similar expectancy, but it is a look 3 for that lineage: **t >= 2.0** is needed.
  - RW4 = NS3 with min_adv 150M, and RW6 = NS2 with a 3% floor. Both are look 2 (t >= 1.5).
  - Correlation with their parents is 0.89-0.97, so they replace their parents; they do not add to them.
- **Not recommended:** anything long, re-entry, or stop-and-reverse.

## 6. Disclosed deviations and limits
- **Lineage grouping:** the overlap-coefficient grouping (section 3) was added after scoring. It only tightens.
- **Re-entry diagnostics:** the 4 re-entry diagnostic configs were not pre-declared. They are counted, and are not finalist-eligible.
- **F4 count:** 174 F4 configs, not 570. Only pairs with the same side and geometry exist among the train-chosen components.
- **ADV:** ADV is computed from data/cache/1Min (prior 20 sessions of RTH $ volume, min 5). Live `avg_dollar_volume` may be computed differently, and early-train ADV rests on only 5-10 sessions.
- **Heat fades:** heat_fade_short/long were emulated with t1s1 for the correlation only.
- **Previous-bar values at 09:50:** the lab frame's 09:50 row has no previous bar, while live it has 09:45. This affects the cross triggers (RW4, RW6, RW8), as in NS1-NS5.
- **Sample size:** train is 40 sessions and valid 14. Nothing here is significant after multiple-testing correction.

## Files
| file | what |
|---|---|
| grid.py | declared grid + expressions (the same strings are written into the modules) |
| lib.py | split loader, stats (day-clustered t, halves, ex-best-day), baselines, exit-bar walk |
| scan.py | F1-F3 scoring -> data/grid.parquet |
| gates.py | gates + plateau -> data/gated.parquet |
| adv.py | ADV table from data/cache/1Min (< 2026-09-16) |
| combos.py | F4 / F5 / F6 -> data/extra.parquet |
| finalists.py, lineage.py | passers, same-time control, live correlation/overlap, lineage grouping |
| diag.py | RW1 neighbourhood, week split, re-entry diagnostic |
| gen_modules.py | writes + verifies modules/RW*.py (verify.json) |
| results.csv | every scored config (gates column: P both>0, N valid n, T valid t, H halves, B baseline, L plateau) |
