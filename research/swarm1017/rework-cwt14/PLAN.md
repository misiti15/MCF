# swarm1017 / rework-cwt14 — PLAN (pre-declared 2026-10-17, written before any configuration was scored)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits; candidates are lab modules.*

## Parents (family "CWT14 failed-break", Testing 2; all 95M adv floor, 09:50-15:00 unless noted, GEOM t05s1)
Kernel = `research/bdi/cwt/live/cwt_live_lib.b3`: a bar trades >= p x daily ATR beyond the level, then a bar closes back
inside within 3 bars (k <= 3); lowvol = the poke bar's volumeRatio < 1. Levels: PD = prior-day high/low; OR = the
09:30-10:00 high/low, live from the 10:05 bar.

| parent | level | p | vol | side | window | open-history (verify.json) | live 10-12..16 (paper, T2) |
|---|---|---|---|---|---|---|---|
| pdl-p10-long | PDL | 0.10 | any | long | 950-1500 | 37,499, -0.086 | 153, -0.124 |
| pdl-p05-long | PDL | 0.05 | any | long (scale_out 0.25 live) | 950-1500 | 66,875, -0.088 | 192, -0.124 |
| pdl-p10-lowvol-long | PDL | 0.10 | <1 | long | 950-1500 | 20,080, -0.095 | 77, +0.043 |
| pdl-p05-lowvol-long | PDL | 0.05 | <1 | long | 950-1500 | 44,026, -0.096 | 145, -0.088 |
| pdh-p10-short | PDH | 0.10 | any | short | 950-1200 | 30,261, -0.096 | 154, -0.054 |
| pdh-p10-lowvol-short | PDH | 0.10 | <1 | short | 950-1500 | 19,479, -0.089 | 87, -0.154 |
| pdh-p05-lowvol-short | PDH | 0.05 | <1 | short | 950-1500 | 43,876, -0.095 | 169, -0.076 |
| orl-p10-long | ORL | 0.10 | any | long | 950-1200 | 39,989, -0.091 | 165, -0.155 |
| orl-p05-long | ORL | 0.05 | any | long | 950-1500 | 105,023, -0.093 | 301, -0.147 |
| orl-p10-lowvol-long | ORL | 0.10 | <1 | long | 950-1500 | 31,676, -0.089 | 157, -0.137 |
| orl-p05-lowvol-long | ORL | 0.05 | <1 | long | 950-1500 | 74,014, -0.090 | 294, -0.249 |

Live week total (research/swarm1017/week/rework_trades.csv, paper, rule 7): 1,894 trades, -0.133R actual. Known from
the lineage: longs +0.02..+0.05R in up sessions and about -0.20R in down sessions (bdi1012, top5_1015); index
confirmation barely moved it (bdi1012, 240 configs); scale-out X06 improved it by +0.017R but stayed negative.
ORH (failed opening-range-high break, short) was never live; it is in the grid as the fourth level.

## Data and split
- research/history2y/data/frames via `research/history2y/lib.py` (open months only; the 2024-11..2025-02 locked block is
  never loaded; MCF_HIST_ALLOW_LOCKED is never set), plus the 09:35-09:45 and 15:05-15:55 5-min rows of
  research/bdi/cwt/test_b/data/headtail.parquet (read per open month), exactly as research/bdi/cwt/live/verify.py.
- Universe: adv20 >= 95M (the parents' floor), atr_d > 0. Decision bars 09:50-15:00, entry at the signal bar close.
- **train** = 2024-10 + 2025-03..2025-12; **valid** = 2026-01-01..2026-10-07 (end of frames). Same as sibling folders.
- Costs: `gates.prod_r` with tod entry costs (= `gates.lab_trades`) for the three frame geometries; the 5-min path
  simulator (`sim.py`) charges the identical cost model (1c + 1 bps per side x tod multiplier on entry, exit free on
  target fills, +2c on stop / breakeven fills). Parity of the simulator with the frame `r_*` columns is checked first.

## Exits (E, 11; live support stated)
| id | exit | live |
|---|---|---|
| t1s1, t05s1, t1s05 | frame geometries | yes (GEOM) |
| t05s05 | 0.5R target / 0.5R stop (sim) | **no** — LabStrategy.GEOMS lacks it (one-line code) |
| t05s1so | t05s1 + bank half at +0.25R, rest stop to breakeven | yes (scale_out_r 0.25 + live_scale_out: true) |
| t1s1so | t1s1 + bank half at +0.5R, rest to breakeven | yes (scale_out_r 0.5 + live_scale_out) |
| t1s1be | t1s1 + breakeven at +0.5R | yes (be_at_r 0.5) |
| t1s1tr | t1s1 + trail 0.5R once +0.5R | yes (trail_r 0.5, trail_after_r 0.5) |
| t1s1ts | t1s1 + time stop 30 min if best < +0.25R | yes (time_stop_min 30, time_stop_min_r 0.25) |
| hold | 1R stop, no target, flat 15:55 | **no** — needs a no-target GEOM (code) |
| holdtr | 1R stop, no target, trail 1R once +1R, flat 15:55 | **no** — needs a no-target GEOM (code) |
Management is simulated on 5-min bars from the bar after entry (stop first inside a bar); live manages on 1-min bars.

## Grid (every configuration counted, including empty ones)
Core = level {PDL, PDH, ORL, ORH} x p {0.03, 0.05, 0.10, 0.15, 0.20, 0.30} x reclaim within k {1, 2, 3, 5} bars x poke
volume {any, v0<1, v0<0.7, v0>=1, v0>=1.5} = 480 cores (the 11 parents are among them).
Windows W6 = {0950-1030, 0950-1130, 1030-1300, 1130-1500, 1300-1500, 0950-1500}.
- **Stage A** (thresholds, side, exit, window, refire): 480 cores x side {natural, opposite} x 11 exits x W6 x
  {first-signal, refire cd1} = **126,720**.
- **Stage B** (one context filter): 24 cores (4 levels x p {0.05, 0.10, 0.20} x vol {any, v0<1}, k 3) x 52 filters x
  2 sides x 11 exits x 3 windows {0950-1500, 0950-1130, 1130-1500}, first-signal = **82,368**.
- **Stage C** (filter pairs): the 11 parent cores x C(52,2)=1,326 pairs x natural side x 3 exits {t05s1, t1s1, t05s1so}
  x 0950-1500 = **43,758**.
- **Declared N_study = 252,846.** Neighbour / robustness checks on finalists counted on top.
- Filter library (52, all known at the decision bar): gap <-1, <0, >0, >1, |gap|<1, |gap|>=2 | VWAP side >0, <0 |
  signal-bar rvol >=1.5, <1 | atrPct terciles (train cuts) lo/mid/hi | Mon..Fri, notMon, notFri | SPY fromOpen >0, <0,
  >0.5, <-0.5, |.|<0.25 [live code] | breadth (share of 95M names above open) >0.5, <0.5, >0.6, <0.4 [live code] |
  stock-minus-SPY fromOpen >0, <0 [live code] | stock fromOpen >0, <0, >1, <-1 | rsi <40, >60 | rsi5 >=70, <=30 |
  heat >=30, <=-30 | sma20 slope >0, <0 | emaDiff >0, <0 | poke depth >=0.3 ATR, <0.15 ATR | first excursion of the day (ord1) |
  adv20 >= 250M | price >= 20 | below/above the other level (PD level for OR cores, OR level for PD cores).
  "Day-class decided at signal time" = the SPY / breadth filters.
- Lineage: CWT14 cwt-b-b3 lineage 121,181 (top5_1015 PLAN) + bdi1016 day-class (84) + refire1014 (44) -> 121,309 prior;
  N_lineage = 121,309 + 252,846 = 374,155 -> **bar t >= max(1.5, sqrt(2 ln N)) = 5.07**.

## Same-minute random baseline
Mean production R (same side, same exit) over every adv20 >= 95M name at the same date + bar. Excess = R - baseline.

## Gates (fixed now)
Screen: n_train >= 150, n_valid >= 50, n_total >= 200, exp_train > 0 and exp_valid > 0 (costs in).
1. regime gate (`gates.regime_split` + `lib.regimes()`: exp > 0 in up AND down sessions, n >= 30 each);
2. walk-forward share >= 0.6 (`gates.walk_forward`, locked months excluded);
3. beats same-minute random: excess > 0 on train AND valid, and excess day-clustered t >= 2 on train+valid;
4. ex-best-day expectancy > 0; busiest session <= 10% of trades;
5. plateau: >= 2/3 of one-step neighbours (p, k, window) positive on train and valid (Stage A grid).
"Candidate" = screen + gates 1-5. The lineage bar (t >= 5.07) is reported per candidate, pass/fail stated; a candidate
below the bar is labelled "Testing-grade" not "research-grade". De-dup: rank by min(t_train, t_valid); drop a candidate
whose trades overlap >= 60% with a higher-ranked one; at most 15 modules. If none pass, say so.
