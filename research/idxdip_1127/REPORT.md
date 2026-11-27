# IDXDIP-1127 — index open-dip family on 10 years of minute data

**Educational only — not financial advice.** Research only: no change to config/, setups, exits, assignments.json,
decisions.json or the ledger. Pre-registered in `PREREG.md` (own commit def8919f4b, before any scoring). Engine label:
**E4 one-off simulator** (QQQOPEN-1127 `qo_sim` rules reused; check time / bounce / +2R target added as parameters).
Costs in everywhere: LIVE-L main, LR8 alongside. Locked block 2024-11-01..2025-02-28 dropped at load and asserted absent.
**Configurations tried: 40** (cumulative program N ~9,176 -> ~9,216). Per-config bar t >= sqrt(2 ln 40) = 2.72.

## In plain words

**There is no robust region. The family fails; one thin point survives.**

- Buying the 3x ETF after an index opening dip is **not a family edge**. Averaged over the 27-config lattice (SPY / QQQ /
  IWM x dip 0.75 / 1.0 / 1.5% x check 09:45 / 09:55 / 10:15), the family makes **+0.001 R per day (t 0.11)**: EARLY -0.003,
  T2 +0.002, CHECK -0.015. With +1 minute entry and +2 bp a side it makes -0.007 (t -0.92). Every H-FAM bar fails.
- **Neighbouring configs do not agree.** Positive and negative cells sit next to each other. IDX3 (SPY 0.75% 09:55) is
  positive (+0.42R, t 2.20), but the cells beside it are not: the same dip checked at 09:45 makes -0.07 and at 10:15
  makes +0.04 (CHECK -0.36). Under the stress test IDX3 keeps +0.23R but t drops to 1.24 (bar 1.65). **IDX3 = one lucky
  point, as wave 3 suspected.**
- **The one config that meets every point bar is IDX6 (QQQ >= 1.5% by 09:55, TQQQ, trail):** +1.15R, n 16, t 3.29,
  best day 23%, avg R without the best day +0.94, beats random 500/500, stress +0.73R (t 2.35), and all three neighbours
  positive. But 13 of its 16 trades are in 2016-2022 (9 in 2020). T2, FIT and CHECK hold **one trade each**, so "positive
  on every split" means three single trades. It also comes from the wave-3 grid, so this test is not independent of the
  pick. The +2R-target version (G3) has the same numbers (+1.09R, t 3.29, best day 11%). **It is a real-looking but very
  rare lead (about 1 trade a year since 2023). It is not a region.**
- **A second small cluster: IWM at 09:45** (0.75%: n 144, +0.24R, t 2.00; 1.0%: n 53, +0.36R, t 1.60). Both are positive on
  EARLY, T2 and CHECK, survive the stress test (+0.22 / +0.35, S12 t 1.73 / 1.66) and beat random 1.000 / 0.998. They are
  under the 2.72 bar and EARLY is weak (+0.09 / +0.19; 2022 negative). Their 09:55 and 10:15 neighbours are flat or
  negative. **Lead only.**
- **Shorts (open-pop fade) fail again:** all four negative or ~0 (QQQ 1.0%: -0.29R, t -2.0). DIA: 0 of 3 pass.
- **Book impact:** the whole lattice would add ~76 trades a year (2023 onward) at -0.08R. Keeping only the configs that are
  positive under stress gives ~23 a year at +0.20R. That set was picked in-sample, so treat it as optimistic. IDX3 alone
  adds ~3.5 a year; IDX6 ~0.9.
  **Correlation with Primary's daily R (bench base book, 861 days) is about zero:** 0.02 for the lattice, 0.05 for IDX3,
  0.01 for IDX6. IDX3 tends to fire on bad Primary days (Primary -4.8 R/day on IDX3 days vs -2.7 on other days, 12 days),
  so a working version would diversify the book. At about 1-4 trades a year it is too small to change Primary's numbers.

**Verdict: FAIL for the family question.** H-FAM is negative on CHECK and no robust region of 3 or more exists. Per
PREREG one robust point exists (IDX6), and it stays a lead on 3 trades since 2023. Recommendation: do not widen the
family or add size. Keep the existing backlog item `qqqopen-1127-idx6-qqq150-trail` as a forward-test lead (low-rep home).
Optional: a later pre-registered forward check of IWM 0.75% at 09:45. IDX3 stays as it is, with no size change; the
stress result confirms it is fragile.

## H-FAM (pre-specified family test, G1 lattice, mean of 27 configs' day R)

| | days | mean R/day | t |
|---|---|---|---|
| ALL | 600 | +0.001 | 0.11 |
| EARLY | 408 | -0.003 | -0.25 |
| T2 | 99 | +0.002 | 0.23 |
| FIT | 32 | +0.072 | 0.97 |
| CHECK | 61 | -0.015 | -0.99 |
| ALL, S12 (+1 min, +2 bp) | 600 | -0.007 | -0.92 |

Bars: positive on EARLY/T2/CHECK — no; t >= 2.0 — no; S12 > 0 with t >= 1.65 — no; concentration — no (best-day share
4.26). **H-FAM fails.**

## Lattice (G1, LIVE-L R/trade; S12 = +1 min entry and +2 bp a side)

| config | n | EARLY | T2 | FIT | CHECK | ALL | t | S1 | S12 | S12 t | ctrl pct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SPY 0.75 09:45 | 29 | +0.05 | -1.30 | -0.33 | – | -0.07 | -0.29 | -0.14 | -0.26 | -0.84 | 0.62 |
| **SPY 0.75 09:55 (IDX3)** | 57 | +0.41 | +0.51 | +0.55 | +0.13 | **+0.42** | 2.20 | +0.27 | +0.23 | 1.24 | 1.00 |
| SPY 0.75 10:15 | 112 | +0.14 | -0.16 | -0.46 | -0.36 | +0.04 | 0.31 | +0.04 | +0.00 | 0.03 | 0.89 |
| SPY 1.0 09:45 | 11 | -0.24 | – | -1.09 | – | -0.32 | -0.74 | +0.02 | -0.02 | -0.04 | 0.24 |
| SPY 1.0 09:55 | 23 | +0.32 | +1.09 | +4.27 | +0.24 | +0.52 | 1.71 | +0.15 | +0.12 | 0.49 | 1.00 |
| SPY 1.0 10:15 | 50 | +0.16 | -0.59 | -0.03 | -0.80 | +0.07 | 0.37 | +0.09 | +0.07 | 0.35 | 0.92 |
| SPY 1.5 09:45 | 7 | -0.01 | – | +3.92 | – | +0.55 | 0.66 | +1.03 | +1.00 | 0.98 | 0.94 |
| SPY 1.5 09:55 | 9 | +0.50 | – | +4.27 | – | +0.92 | 1.51 | +0.31 | +0.28 | 0.56 | 1.00 |
| SPY 1.5 10:15 | 11 | +0.35 | – | +1.09 | – | +0.41 | 1.36 | +0.21 | +0.20 | 0.69 | 0.99 |
| QQQ 0.75 09:45 | 100 | -0.13 | -0.06 | -0.47 | -0.06 | -0.15 | -1.17 | -0.11 | -0.15 | -1.22 | 0.28 |
| QQQ 0.75 09:55 | 184 | -0.13 | +0.12 | -0.00 | +0.10 | -0.08 | -0.87 | -0.11 | -0.15 | -1.72 | 0.43 |
| QQQ 0.75 10:15 | 314 | -0.17 | -0.19 | -0.26 | -0.25 | -0.19 | -3.11 | -0.17 | -0.20 | -3.27 | 0.03 |
| QQQ 1.0 09:45 | 35 | -0.09 | +0.16 | -0.36 | – | -0.09 | -0.40 | -0.17 | -0.20 | -1.08 | 0.46 |
| QQQ 1.0 09:55 | 67 | +0.08 | +0.53 | +0.18 | -0.33 | +0.09 | 0.56 | +0.06 | +0.03 | 0.21 | 0.90 |
| QQQ 1.0 10:15 | 151 | -0.12 | +0.51 | -0.13 | -0.03 | -0.07 | -0.75 | +0.01 | -0.02 | -0.21 | 0.54 |
| QQQ 1.5 09:45 | 7 | +1.00 | – | +4.89 | – | +1.56 | 1.64 | +1.37 | +1.35 | 1.38 | 1.00 |
| **QQQ 1.5 09:55 (IDX6)** | 16 | +0.99 | +1.20 (n1) | +4.29 (n1) | +0.02 (n1) | **+1.15** | **3.29** | +0.75 | +0.73 | 2.35 | 1.00 |
| QQQ 1.5 10:15 | 34 | +0.10 | +1.02 | +0.77 | +0.31 | +0.22 | 1.00 | +0.26 | +0.24 | 0.98 | 0.98 |
| **IWM 0.75 09:45** | 144 | +0.09 | +0.53 | +1.15 | +0.26 | +0.24 | 2.00 | +0.26 | +0.22 | 1.73 | 1.00 |
| IWM 0.75 09:55 | 264 | -0.03 | +0.21 | +0.47 | -0.26 | +0.02 | 0.26 | -0.01 | -0.05 | -0.62 | 0.95 |
| IWM 0.75 10:15 | 431 | -0.11 | -0.19 | +0.40 | -0.29 | -0.12 | -2.09 | -0.12 | -0.15 | -2.75 | 0.34 |
| **IWM 1.0 09:45** | 53 | +0.19 | +0.53 | +1.67 | +0.31 | +0.36 | 1.60 | +0.38 | +0.35 | 1.66 | 1.00 |
| IWM 1.0 09:55 | 97 | -0.05 | -0.14 | +1.17 | +0.45 | +0.05 | 0.41 | +0.00 | -0.02 | -0.18 | 0.90 |
| IWM 1.0 10:15 | 198 | -0.03 | -0.18 | +0.65 | -0.13 | -0.00 | -0.05 | -0.05 | -0.08 | -0.91 | 0.89 |
| IWM 1.5 09:45 | 10 | +0.78 | – | +0.29 | – | +0.73 | 1.41 | +0.41 | +0.39 | 0.94 | 1.00 |
| IWM 1.5 09:55 | 22 | +0.12 | +0.25 | -0.04 | – | +0.12 | 0.46 | -0.15 | -0.17 | -0.84 | 0.85 |
| IWM 1.5 10:15 | 48 | -0.05 | -0.20 | -0.18 | +0.04 | -0.07 | -0.40 | -0.11 | -0.12 | -0.72 | 0.52 |

Robust-point check (all 6 criteria): only **QQQ 1.5 09:55**. Region members (positive EARLY/T2/CHECK, S12 ok, t >= 2.0):
QQQ 1.5 09:55 and IWM 0.75 09:45, which are not connected. Largest region = 1 config, below the 3 required. **No robust
region.** Pattern: deeper dips at 09:45-09:55 tend to be positive, but they are rare (7-23 trades in 10 years). Shallow
dips and the 10:15 check are flat-to-negative on QQQ and IWM, and the 10:15 check is weak on SPY.

## G2-G4 (judged on criteria 1-5)

| config | n | EARLY | T2 | FIT | CHECK | ALL | t | S12 | S12 t | ctrl | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DIA 0.75 09:55 | 48 | -0.01 | +0.96 | +0.74 | +0.20 | +0.13 | 0.76 | +0.09 | 0.50 | 0.91 | no |
| DIA 1.0 09:55 | 21 | -0.09 | – | +2.96 | – | +0.20 | 0.61 | +0.26 | 0.71 | 0.90 | no |
| DIA 1.5 09:55 | 7 | +0.52 | – | – | – | +0.52 | 0.70 | +0.33 | 0.61 | 0.98 | no |
| SPY 0.75 B0.35 TRAIL | 48 | +0.30 | +1.13 | +1.44 | +0.32 | +0.44 | 2.33 | +0.16 | 0.83 | 1.00 | no (t, S12) |
| SPY 0.75 HOLD | 57 | +0.29 | +2.94 | -0.41 | +0.69 | +0.36 | 1.08 | +0.21 | 0.67 | 1.00 | no |
| SPY 0.75 TGT2 | 57 | +0.49 | +1.89 | -0.04 | +0.37 | +0.49 | 2.48 | +0.23 | 1.14 | 1.00 | no (t, S12) |
| QQQ 1.5 B0.35 TRAIL | 14 | +0.52 | +0.29 | +4.29 | – | +0.77 | 2.04 | +0.36 | 1.20 | 1.00 | no |
| QQQ 1.5 HOLD | 16 | -0.13 | +2.30 | +2.17 | +0.73 | +0.22 | 0.52 | +0.03 | 0.09 | 0.86 | no |
| **QQQ 1.5 TGT2** | 16 | +0.99 | +1.91 (n1) | +1.94 (n1) | +0.73 (n1) | **+1.09** | **3.29** | +0.87 | 2.46 | 1.00 | **yes (1-5)** |
| SHORT SPY 0.75 | 52 | -0.10 | -1.11 | -0.17 | – | -0.15 | -0.89 | -0.19 | -1.16 | 0.40 | no |
| SHORT SPY 1.0 | 25 | +0.08 | -1.12 | +0.10 | – | +0.03 | 0.13 | -0.11 | -0.41 | 0.81 | no |
| SHORT QQQ 1.0 | 60 | -0.16 | -1.12 | -0.81 | -0.77 | -0.29 | -2.02 | -0.36 | -2.34 | 0.09 | no |
| SHORT QQQ 1.5 | 15 | +0.17 | – | -1.07 | -1.09 | +0.00 | 0.00 | -0.05 | -0.15 | 0.68 | no |

Exits at the anchors: on IDX3 a +2R target beats the trail slightly (+0.49 vs +0.42) and HOLD is worse (t 1.08). On IDX6
the target and the trail are close (+1.09 vs +1.15) and HOLD is poor (+0.22). A stricter 35% bounce does not help.

## Finalists (every config that met criteria 1-5)
1. **G1 QQQ 1.5 09:55 TRAIL (IDX6)**: n 16, +1.147R (LR8 +1.159, gross +1.235), t 3.29, best day 23.4%, w/o best +0.937,
   control 1.000 (p95 +0.32), S1 +0.747, S2 +1.130, S12 +0.730 (t 2.35); above/below QQQ 50-day SMA: +0.96 (n 5) /
   +1.23 (n 11). Years: 2020 9 trades +0.76, 2021 2, 2022 2, 2023 1, 2025 1 (+4.29), 2026 1 (+0.02). It is a robust point
   by the PREREG definition, but the evidence is concentrated in time: 13 of 16 trades are EARLY, and it was selected from
   the wave-3 grid.
2. **G3 QQQ 1.5 09:55 TGT2**: the same 16 days. +1.088R, t 3.29, best day 11.1%, w/o best +1.03, S12 +0.873 (t 2.46).
Not finalists, nearest misses: IDX3 (t 2.20, S12 t 1.24), SPY 0.75 TGT2 (t 2.48, S12 t 1.14), SPY 0.75 B0.35 (t 2.33),
IWM 0.75 09:45 (t 2.00, S12 t 1.73).

## Book impact and diversification (Primary 4 base book, bench, regsteer_1126 base.parquet, 2023-01..2026-11-04)

| set | trades | per year (all 10.5 y) | per year (2023+) | mean R | corr with Primary day R (all days) | corr on IDX days | Primary R/day on IDX days vs other |
|---|---|---|---|---|---|---|---|
| G1 lattice union (1/index/day) | 898 | 85.5 | 76.4 | -0.078 | +0.022 | +0.036 | -3.29 vs -2.58 |
| G1 configs positive ALL and S12 (in-sample pick) | 337 | 32.1 | 23.4 | +0.198 | +0.017 | +0.090 | -3.80 vs -2.66 |
| IDX3 | 57 | 5.4 | 3.5 | +0.424 | +0.048 | +0.399 (12 d) | -4.83 vs -2.71 |
| IDX6 | 16 | 1.5 | 0.9 | +1.147 | +0.013 | (3 d) | +1.71 vs -2.75 |

The bench Primary base book is the RAW replay (mean -2.73 R/day on bench). It is used only for the correlation, not as a
target. Daily-Sharpe change from adding each set is within ±0.07, because a few trades a year cannot move a book that trades
every day. Opening dips cluster in volatile years (2020: 168 lattice trades; 2022: 202), so this family is a crisis-year
add-on, not a steady contributor.

## Rule changes
No live trades are used. All numbers are history / bench replays of fixed rules, so no ledger effective date falls inside
the windows. (Live IDX trades and the 11-17..11-25 rule changes are covered in research/wave3_1127/SUMMARY.md.)

## Files
`PREREG.md` (+sha256), `idx_sim.py` (E4 simulation, trades to scratch), `idx_score.py` (costs, stress, controls, H-FAM,
lattice, impact), `results.json` (every config, every split, controls, regions, impact by year), `score_out.txt`.
Reproduce: `python research/idxdip_1127/idx_sim.py OUT RAW_2016_2022_DIRS` then
`python research/idxdip_1127/idx_score.py OUT RAW_DIRS PRIMARY_BASE_PARQUET` (2016-2022 bars GET-only from Alpaca SIP).
