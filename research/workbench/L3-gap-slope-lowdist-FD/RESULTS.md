# Workbench RESULTS — Gap-Down Bounce-off-Low Fade (all day) `L3-gap-slope-lowdist-FD` (On Deck) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16, built 18:10-20:30 ET (after the close; research files only, no config change).

## Verdict
**`L3-gap-slope-lowdist-FD-WB4` PASSES and is recommended** = parent + three parts: bounce off the low > 0.82 ATR (P11, was 0.78) +
new entry layer rsi5 ≥ 50 + every lot closed 75 min after entry (P26, runner `time_stop_min 75` / `time_stop_min_r 99`).

| copy | change | replay avg R | 2-year avg R | w/o best day (replay / 2y) | worst day (replay / 2y) | trades (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|
| parent | — | +0.178 | −0.085 | −0.027 / −0.110 | −19.7 / −164.4 | 195 / 3,035 | — |
| `-WB1` | P11 dist from low > 0.82 ATR (was 0.78) | +0.193 | −0.074 | −0.001 / −0.101 | −14.5 / −147.0 | 169 / 2,733 | PASS (not deployed; in WB4) |
| `-WB2` | P26 max hold 75 min | +0.257 | −0.068 | +0.199 / −0.086 | −3.2 / −160.8 | 195 / 3,035 | PASS (not deployed; in WB4) |
| `-WB3` | new layer rsi5 ≥ 50 | +0.178 (meets) | −0.018 | −0.028 / −0.043 | −16.4 / −44.7 | 175 / 2,505 | PASS (not deployed; in WB4) |
| **`-WB4`** | **WB1 + WB2 + WB3** | **+0.271** | **+0.007** | **+0.196 / −0.012** | **−2.1 / −41.7** | **150 / 2,221** | **PASS — recommended (Testing F)** |

Pass rule (owner 2026-11-16 clarification): meets or exceeds the parent's avg R after costs in BOTH identical tests ("meets" = within
0.01R or ≥ 95%), and not worse on avg R w/o best day by > 0.02R or on worst day by > 10%. The parent's live record is not used in the
decision (DIAGNOSIS.md uses it for diagnosis only). **Configs counted: 54** (bar for the paired day-t max(1.5, √(2 ln 54)) = 2.82; L3
lineage incl. the fromopen-FD bench's 59 and L3LEASH/-2's 26: 139). WB4 paired-by-day t vs parent +0.16 (replay) / +1.46 (2y) — **not
significant**; it passes on meet-or-exceed.

## Method (identical for parent and every copy)
- **Replay of the live sessions (backtest, not live results):** every symbol-day the parent signalled live (Testing 1 / On Deck journal,
  `mcf-data-testing`) except the 170 not-shortable/ETB ones, 2026-10-12..11-13: 292 symbol-days, 22 sessions. 1-min SIP bars (read-only
  GET) → lab frame (`mcf.report.engine.lab_frame` + daily priors as live; `dist_lod_atr` recomputed after the daily ATR is set). Check:
  the backtest's first signal bar equals the live signal bar on 283 of 286 matched symbol-days (99%), the other 3 within 5-10 min.
  Copies that loosen a sensor cannot be replayed (none of the shortlist loosens).
- **2-year backtest:** research lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted), names
  shortable+ETB on ≥ 90% of the 26 universe snapshots (E90 proxy, as the L3 benches), 3,703 symbol-days with 1-min paths. Splits TRAIN ≤
  2025-12-31, VALID ..2026-10-05, FWD ..11-04.
- Same engine as `research/workbench/L3-gap-slope-fromopen-FD/code` (reused `sim.py`/`sim2.py` walk, costs, book; `code/sim_low.py`
  adds the lowdist sensors): signal on the 5-min bar close, first qualifying bar per symbol-day (refire off, as live), entry at the
  signal-bar close, price ≥ $5, exits walked on 1-min bars (stop first; target only when traded through by $0.01; flat 15:55), **LR8
  costs**, On Deck book: ≤ 150 open lots, ≤ 3 per symbol, no setup latch, **P17 cost filter** (skip when (2 × (1c + 1 bp) + 2c) / 1R >
  0.15, as the runner). SPY 1-min for the after-09:50 gate (cache to 11-04 + SIP 10-12..11-13).
- Rule changes inside the replay window (ledger): 10-20 twin block + Testing latch, 10-23 latch off, 10-30 cost filter 0.15R, 11-11
  TEAM-6, 11-12 LR1/LR5/LR8 + account stop 300R + split-tape gate off. The replay applies today's rules to every session, so none of these
  mix into the parent-vs-copy comparison.

## WB4 in detail (parent → WB4)
- 2-year by split: TRAIN −0.075 → +0.037, VALID −0.084 → −0.036, FWD −0.193 → +0.124 (better in all three). Ex-April 2025 (the
  tariff-crash month, incl. the worst parent day 2025-04-07): −0.086 → −0.054.
- Day type (2y, SPY open→close): up −0.277 → −0.095, flat +0.083 → +0.042, down +0.181 → +0.179 — big gain on up days, gives a little
  back on flat days.
- Shape: avg win / loss +0.868 / −0.944 → +0.693 / −0.717 (2y); exit mix stop 44% → 25%, target 38% → 27%, time 17% → 49%; median hold
  65 → 70 min (2y), 110 → 75 (replay); R per day −0.59 → +0.03 (2y), +1.58 → +1.85 (replay).
- Day by day: replay WB4 better on 6 days (+41.0R), worse on 10 (−35.1R) — net +5.9R, mostly 10-15 (−19.7 → +10.3R) and 10-13; it gives
  back on the big winning day 11-12 (+38.5 → +19.7R). Replay best-day share 111% → 48%; replay avg w/o 11-12 −0.027 → +0.196. 2-year
  better on 132 days (+512R), worse on 133 (−240R) — net +272R.
- Book check (target accounts cap a setup at 30-50 open lots): at cap 30 parent +0.158 / −0.081, WB4 +0.277 / −0.010; at cap 50 parent
  +0.178 / −0.081, WB4 +0.271 / +0.007. WB4 still beats the parent on the identical book.
- Neighbours (plateau, not a knife edge): hold 60 / 90 instead of 75: +0.275 / −0.004, +0.248 / −0.001; dist > 0.85: +0.249 / +0.005;
  rsi5 ≥ 40: +0.283 / −0.005 (replay / 2y). Without the clock (Q1) +0.190 / −0.005; conditional clocks Q3/Q4 weaker.
- Live trades (diagnosis only): WB4's entry parts keep 50 of the 105 live trades (+0.291R journal vs +0.248 all; dropped 55 averaged
  +0.21R, incl. 36 dist ≤ 0.82 trades at +0.33R — live disagrees with the dist part); the clock leaves those 50 at about +0.287R. Of the
  5 worst live trades WB4 removes UGP, ITUB (rsi5 0 / 29) and NG (dist 0.807); of the 5 best it drops PENG 10-13 (dist 0.806) and NTSK
  11-05 (rsi5 12).

## Shape table (parent and the four copies)
| copy | test | avg win | avg loss | median hold | stop / target / time share | up / flat / down (2y) | ex-11-12 (replay) / ex-Apr-25 (2y) |
|---|---|---|---|---|---|---|---|
| parent | replay | +0.876 | -0.916 | 110 | 32% / 49% / 18% |  | -0.027 |
| parent | 2y | +0.868 | -0.944 | 65 | 44% / 38% / 17% | -0.277 / +0.084 / +0.181 | -0.086 (n 2236) |
| WB1 | replay | +0.881 | -0.907 | 107 | 31% / 50% / 18% |  | -0.001 |
| WB1 | 2y | +0.877 | -0.943 | 63 | 44% / 39% / 17% | -0.257 / +0.097 / +0.180 | -0.069 (n 1998) |
| WB2 | replay | +0.633 | -0.588 | 75 | 14% / 30% / 56% |  | +0.199 |
| WB2 | 2y | +0.691 | -0.764 | 65 | 30% / 25% / 45% | -0.203 / +0.006 / +0.151 | -0.075 (n 2236) |
| WB3 | replay | +0.864 | -0.927 | 106 | 32% / 50% / 18% |  | -0.028 |
| WB3 | 2y | +0.867 | -0.927 | 70 | 41% / 41% / 19% | -0.193 / +0.099 / +0.230 | -0.076 (n 1970) |
| WB4 | replay | +0.674 | -0.586 | 75 | 14% / 33% / 53% |  | +0.196 |
| WB4 | 2y | +0.693 | -0.717 | 70 | 25% / 27% / 49% | -0.095 / +0.042 / +0.179 | -0.054 (n 1745) |

## Every configuration tried (54), including failures
Pre-declared in rounds in `code/decl_low.py`, each round declared before its scores (ROUND1 27 one-part tweaks incl. the sibling's
parts; ROUND2 12 combos; ROUND3 7 neighbours; ROUND4 4 softer exits; BOOK 4 cap checks). Verdict vs the PARENT on the pass rule.
| config | replay n | replay avg R | replay w/o best | replay worst day | 2y n | 2y avg R | 2y w/o best | 2y worst day | 2y TRAIN / VALID / FWD | t vs parent (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PARENT | 195 | +0.178 | -0.027 | -19.7 | 3035 | -0.085 | -0.110 | -164.4 | -0.075 / -0.084 / -0.193 |  | — |
| V01 window end 15:00->13:00 (P6) | 172 | +0.193 | -0.036 | -19.7 | 2305 | -0.130 | -0.164 | -195.1 | -0.137 / -0.125 / -0.110 | -0.37 / -0.55 | FAIL: 2y avg R -0.130 < parent -0.085; 2y w/o best day -0.164 vs -0.110; 2y worst day -195.1R vs -164.4R |
| V02 window end 15:00->14:00 (P6) | 186 | +0.161 | -0.059 | -19.7 | 2687 | -0.114 | -0.144 | -176.3 | -0.128 / -0.089 / -0.203 | -1.72 / -0.83 | FAIL: replay avg R +0.161 < parent +0.178; replay w/o best day -0.059 vs -0.027; 2y avg R -0.114 < parent -0.085; 2y w/o best day -0.144 vs -0.110 |
| V03 window start 09:50->10:05 (P6/P7) | 195 | +0.189 | -0.012 | -19.7 | 3020 | -0.086 | -0.112 | -163.3 | -0.079 / -0.084 / -0.179 | +1.00 / -0.44 | PASS |
| V04 gap <=-2.66->-3.2 (P4/P9) | 150 | +0.121 | -0.120 | -19.4 | 2264 | -0.076 | -0.111 | -137.9 | -0.074 / -0.060 / -0.267 | -1.60 / +1.42 | FAIL: replay avg R +0.121 < parent +0.178; replay w/o best day -0.120 vs -0.027 |
| V05 gap not deeper than -10% (P9 layer) | 184 | +0.213 | +0.012 | -19.7 | 2886 | -0.088 | -0.113 | -161.2 | -0.084 / -0.081 / -0.195 | +1.40 / +0.21 | PASS |
| V06 dist_lod hi 0.977->0.95 (P12) | 189 | +0.160 | -0.043 | -19.7 | 2913 | -0.093 | -0.120 | -147.0 | -0.084 / -0.091 / -0.201 | -1.66 / -0.44 | FAIL: replay avg R +0.160 < parent +0.178 |
| V07 dist_lod lo 0.782->0.82 (P11) | 169 | +0.193 | -0.001 | -14.5 | 2733 | -0.074 | -0.101 | -147.0 | -0.085 / -0.057 / -0.116 | -0.23 / +1.57 | PASS |
| V08 slope >0.372->>0.45 (P10) | 165 | +0.110 | -0.099 | -21.4 | 2563 | -0.080 | -0.112 | -136.1 | -0.065 / -0.084 / -0.223 | -1.79 / +1.31 | FAIL: replay avg R +0.110 < parent +0.178; replay w/o best day -0.099 vs -0.027 |
| V09 slope <= 1.0 (P10 layer) | 186 | +0.189 | -0.029 | -20.9 | 2921 | -0.081 | -0.108 | -147.9 | -0.065 / -0.084 / -0.226 | +0.11 / +0.86 | PASS |
| V10 fromOpen >= 0 (new layer) | 171 | +0.242 | +0.008 | -16.4 | 2510 | -0.131 | -0.145 | -165.2 | -0.162 / -0.096 / -0.196 | +1.29 / -1.56 | FAIL: 2y avg R -0.131 < parent -0.085; 2y w/o best day -0.145 vs -0.110 |
| V11 fromOpen >= 3 (new layer) | 122 | +0.332 | +0.023 | -12.3 | 1521 | -0.103 | -0.119 | -84.8 | -0.193 / -0.025 / -0.161 | +0.61 / +0.77 | FAIL: 2y avg R -0.103 < parent -0.085 |
| V12 rsi5 >= 50 (new layer) | 175 | +0.178 | -0.028 | -16.4 | 2505 | -0.018 | -0.043 | -44.7 | +0.051 / -0.067 / -0.185 | -0.60 / +1.30 | PASS |
| V13 1R >= 1.0% of price (P20 layer) | 170 | +0.210 | -0.025 | -17.2 | 2502 | -0.096 | -0.120 | -138.9 | -0.103 / -0.078 / -0.202 | +0.29 / +0.31 | FAIL: 2y avg R -0.096 < parent -0.085 |
| V14 max hold 75 min (P26) | 195 | +0.257 | +0.199 | -3.2 | 3035 | -0.068 | -0.086 | -160.8 | -0.080 / -0.071 / +0.089 | +0.41 / +0.73 | PASS |
| V15 max hold 90 min (P26) | 195 | +0.243 | +0.186 | -3.2 | 3035 | -0.073 | -0.096 | -162.0 | -0.080 / -0.077 / +0.029 | +0.35 / +0.61 | PASS |
| V16 max hold 120 min (P26) | 195 | +0.219 | +0.145 | -3.2 | 3035 | -0.074 | -0.099 | -163.5 | -0.080 / -0.071 / -0.034 | +0.28 / +0.82 | PASS |
| V17 target 1R->0.5R t05s1 (P24) | 195 | +0.198 | +0.140 | -3.2 | 3035 | -0.068 | -0.081 | -146.7 | -0.103 / -0.034 / -0.017 | +0.11 / +0.68 | PASS |
| V18 stop 1R->1.25R (P23; info, no geom) | 195 | +0.137 | -0.092 | -26.1 | 3035 | -0.079 | -0.112 | -173.8 | -0.079 / -0.065 / -0.215 | -1.16 / +0.47 | FAIL: replay avg R +0.137 < parent +0.178; replay w/o best day -0.092 vs -0.027; replay worst day -26.1R vs -19.7R |
| V19 BE stop after +0.5R (P23 hook) | 195 | +0.240 | +0.110 | -3.2 | 3035 | -0.093 | -0.107 | -168.3 | -0.121 / -0.068 / -0.048 | +0.51 / -0.47 | PASS |
| V20 refire on, cooldown 1 (P8) | 481 | +0.065 | -0.122 | -73.0 | 6965 | -0.056 | -0.077 | -168.3 | -0.040 / -0.055 / -0.215 | -0.05 / -0.66 | FAIL: replay avg R +0.065 < parent +0.178; replay w/o best day -0.122 vs -0.027; replay worst day -73.0R vs -19.7R |
| V21 open-lot cap 150->30 (P13) | 170 | +0.158 | -0.019 | -18.4 | 2484 | -0.081 | -0.102 | -56.0 | -0.071 / -0.079 / -0.181 | -0.84 / +0.44 | FAIL: replay avg R +0.158 < parent +0.178 |
| V22 cost filter 0.15->0.10R (P17) | 165 | +0.174 | -0.057 | -18.6 | 2535 | -0.105 | -0.128 | -147.4 | -0.105 / -0.092 / -0.223 | -1.00 / -0.25 | FAIL: replay w/o best day -0.057 vs -0.027; 2y avg R -0.105 < parent -0.085 |
| V23 price floor $5->$10 (P2) | 191 | +0.172 | -0.042 | -19.7 | 3024 | -0.085 | -0.110 | -163.8 | -0.076 / -0.084 / -0.187 | -0.77 / +0.38 | PASS |
| V24 skip SPY>+0.30% since 09:50 (gate) | 75 | +0.168 | +0.106 | -2.5 | 1529 | -0.006 | -0.052 | -42.9 | +0.091 / -0.137 / +0.085 | -0.51 / +1.34 | FAIL: replay avg R +0.168 < parent +0.178 |
| V25 VWAP dist >= 1% (new layer) | 176 | +0.189 | -0.045 | -18.5 | 2389 | -0.039 | -0.062 | -43.6 | +0.035 / -0.086 / -0.201 | -0.44 / +0.98 | PASS |
| V26 sibling WB4 parts: end 13:00 + gap -3.2 + hold 75 | 130 | +0.278 | +0.221 | -3.7 | 1745 | -0.082 | -0.114 | -159.1 | -0.121 / -0.064 / +0.180 | +0.04 / +1.05 | PASS |
| V27 sibling parts w/o gap: end 13:00 + hold 75 | 172 | +0.294 | +0.248 | -2.4 | 2305 | -0.101 | -0.130 | -193.4 | -0.138 / -0.092 / +0.183 | +0.42 / +0.22 | FAIL: 2y avg R -0.101 < parent -0.085; 2y w/o best day -0.130 vs -0.110; 2y worst day -193.4R vs -164.4R |
| R01 hold 75 + rsi5>=50 | 175 | +0.265 | +0.183 | -2.4 | 2505 | -0.007 | -0.028 | -46.8 | +0.044 / -0.066 / +0.076 | +0.34 / +1.31 | PASS |
| R02 hold 75 + VWAP>=1% | 176 | +0.266 | +0.177 | -3.1 | 2389 | -0.024 | -0.046 | -43.8 | +0.023 / -0.075 / +0.084 | +0.35 / +1.09 | PASS |
| R03 hold 75 + rsi5>=50 + VWAP>=1% | 166 | +0.283 | +0.181 | -3.1 | 2211 | -0.016 | -0.040 | -44.8 | +0.035 / -0.072 / +0.085 | +0.38 / +1.20 | PASS |
| R04 hold 75 + cap 30 | 170 | +0.243 | +0.168 | -3.2 | 2520 | -0.065 | -0.084 | -52.0 | -0.073 / -0.073 / +0.066 | +0.19 / +0.65 | PASS |
| R05 hold 75 + rsi5>=50 + cap 30 | 161 | +0.266 | +0.182 | -2.4 | 2240 | -0.028 | -0.048 | -46.8 | -0.005 / -0.062 / +0.078 | +0.23 / +1.02 | PASS |
| R06 hold 75 + rsi5>=50 + gap>=-10 | 165 | +0.314 | +0.254 | -1.4 | 2394 | -0.012 | -0.033 | -46.8 | +0.035 / -0.069 / +0.085 | +0.49 / +1.25 | PASS |
| R07 hold 75 + target 0.5R | 195 | +0.184 | +0.146 | -3.2 | 3035 | -0.069 | -0.084 | -146.3 | -0.106 / -0.040 / +0.054 | +0.03 / +0.52 | PASS |
| R08 hold 75 + rsi5>=50 + dist lo 0.82 | 150 | +0.271 | +0.196 | -2.1 | 2221 | +0.007 | -0.012 | -41.7 | +0.037 / -0.036 / +0.124 | +0.16 / +1.46 | PASS |
| R09 hold 75 + rsi5>=50 + skip SPY>+0.30 | 63 | +0.113 | +0.011 | -2.4 | 1248 | +0.024 | -0.017 | -38.3 | +0.118 / -0.102 / +0.128 | -0.61 / +1.52 | FAIL: replay avg R +0.113 < parent +0.178 |
| R10 hold 60 + rsi5>=50 | 175 | +0.267 | +0.177 | -2.3 | 2505 | -0.013 | -0.031 | -40.4 | +0.020 / -0.055 / +0.082 | +0.33 / +1.24 | PASS |
| R11 hold 90 + rsi5>=50 | 175 | +0.245 | +0.179 | -2.7 | 2505 | -0.010 | -0.032 | -51.6 | +0.047 / -0.070 / +0.020 | +0.23 / +1.31 | PASS |
| R12 hold 75 + rsi5>=50 + VWAP>=1% + cap 30 | 153 | +0.290 | +0.187 | -3.1 | 2012 | -0.028 | -0.051 | -44.8 | +0.000 / -0.067 / +0.085 | +0.28 / +1.05 | PASS |
| S1 R08 + window end 14:00 | 145 | +0.263 | +0.189 | -2.1 | 1932 | -0.004 | -0.026 | -34.5 | +0.013 / -0.033 / +0.125 | +0.09 / +1.33 | PASS |
| S2 R08 + window end 13:00 | 129 | +0.327 | +0.271 | -1.2 | 1588 | -0.008 | -0.034 | -29.4 | +0.038 / -0.077 / +0.207 | +0.20 / +1.32 | PASS |
| S3 R08 + gap>=-10 | 140 | +0.329 | +0.279 | -1.2 | 2119 | -0.001 | -0.020 | -41.7 | +0.025 / -0.040 / +0.124 | +0.30 / +1.38 | PASS |
| S4 R08 with hold 60 | 150 | +0.275 | +0.180 | -2.1 | 2221 | -0.004 | -0.022 | -36.2 | +0.014 / -0.035 / +0.110 | +0.17 / +1.33 | PASS |
| S5 R08 with hold 90 | 150 | +0.248 | +0.187 | -2.1 | 2221 | -0.001 | -0.021 | -37.6 | +0.032 / -0.040 / +0.060 | +0.06 / +1.40 | PASS |
| S6 R08 with dist lo 0.85 | 127 | +0.249 | +0.158 | -2.1 | 1974 | +0.005 | -0.014 | -39.0 | +0.027 / -0.027 / +0.086 | -0.09 / +1.36 | PASS |
| S7 R08 with rsi5>=40 | 156 | +0.283 | +0.212 | -2.1 | 2391 | -0.005 | -0.027 | -41.7 | +0.011 / -0.038 / +0.147 | +0.25 / +1.54 | PASS |
| Q1 rsi5>=50 + dist lo 0.82 (no clock) | 150 | +0.190 | -0.003 | -10.3 | 2221 | -0.004 | -0.030 | -34.7 | +0.038 / -0.035 / -0.120 | -0.41 / +1.48 | PASS |
| Q2 Q1 + hold 120 | 150 | +0.232 | +0.130 | -2.1 | 2221 | +0.000 | -0.024 | -43.2 | +0.039 / -0.038 / +0.003 | +0.00 / +1.49 | PASS |
| Q3 Q1 + 75 min only if best < 0.5R | 150 | +0.190 | +0.020 | -8.2 | 2221 | -0.007 | -0.029 | -40.3 | +0.039 / -0.051 / -0.028 | -0.33 / +1.42 | PASS |
| Q4 Q1 + 90 min only if best < 0.75R | 150 | +0.226 | +0.101 | -2.1 | 2221 | -0.003 | -0.027 | -37.9 | +0.036 / -0.042 / +0.010 | -0.03 / +1.44 | PASS |
| B1 parent at cap 30 | 170 | +0.158 | -0.019 | -18.4 | 2484 | -0.081 | -0.102 | -56.0 | -0.071 / -0.079 / -0.181 | -0.84 / +0.44 | FAIL: replay avg R +0.158 < parent +0.178 |
| B2 R08 at cap 30 | 148 | +0.277 | +0.200 | -2.1 | 2011 | -0.010 | -0.031 | -41.7 | -0.003 / -0.032 / +0.124 | +0.17 / +1.22 | PASS |
| B3 parent at cap 50 | 195 | +0.178 | -0.027 | -19.7 | 2715 | -0.081 | -0.103 | -87.8 | -0.072 / -0.077 / -0.193 | +0.00 / +0.40 | PASS |
| B4 R08 at cap 50 | 150 | +0.271 | +0.196 | -2.1 | 2147 | +0.007 | -0.012 | -41.7 | +0.020 / -0.018 / +0.124 | +0.16 / +1.42 | PASS |

Failures, in short: window end 13:00 / 14:00 (2y −0.130 / −0.114; worst day −195R), gap ≤ −3.2 (replay +0.121), dist hi 0.95 (replay
+0.160), slope > 0.45 (replay +0.110), fromOpen ≥ 0 / ≥ 3 (replay up, 2y −0.131 / −0.103), 1R ≥ 1% of price (2y −0.096), stop 1.25R
(replay +0.137), refire on (replay worst day −73R), cap 30 alone (replay +0.158), cost filter 0.10R (2y −0.105), SPY > +0.30% since
09:50 gate (replay +0.168 on 75 trades; with WB parts +0.113), sibling parts without the gap V27 (2y −0.101). Passed but not chosen:
start 10:05, gap ≥ −10%, slope ≤ 1.0, hold 90/120, target 0.5R, BE at +0.5R, price ≥ $10, VWAP ≥ 1%, sibling WB4 parts V26 (replay
+0.278 but 2y −0.082 on 1,745 trades), and the combos R01-R12 / S1-S7 (R06/S3 add gap ≥ −10%: replay +0.314/+0.329 but 2y below WB4).
Stop 1.25R copies are not deployable anyway (no `t1s125` geometry).

## Supervisor sign-off
WB4 = the parent with three changes: (1) the bounce must be more than 0.82 daily ATR off the low (was 0.78), (2) the 5-bar RSI on the
signal bar must be ≥ 50 — the bounce bar is still rising, not a bar that is already rolling over, (3) every lot is closed 75 minutes
after entry. Why: the setup's losses came from two places — mass-reversal days where every gap-down name keeps rising (2025-04-07,
308 trades, −164R; 10-15 in the replay) and slow drifts to the stop after being green; the RSI layer and the 0.82 floor remove the
weakest entries and the clock caps the drift. Overall before → after: replay +0.178 → +0.271R/trade, 2-year −0.085 → +0.007R/trade,
w/o best day −0.027 → +0.196 / −0.110 → −0.012, worst day −19.7 → −2.1R / −164.4 → −41.7R, better in every 2-year split and on the
target account's 30-lot book. Gives back: about a quarter fewer trades (195 → 150, 3,035 → 2,221), smaller wins (avg win 0.87 → 0.69R),
big trend days are cut (replay 11-12 +38.5 → +19.7R; 10 of 18 replay days slightly worse), flat 2-year days +0.083 → +0.042, and two of
the five best live trades (PENG 10-13, NTSK 11-05) would not be taken; the live journal disagrees with the 0.82 floor on 36 trades.
Not hidden: the improvement is not statistically significant (t +0.16 / +1.46 vs a counted bar of 2.82), the 2-year result is about
break-even after costs (+0.007R, w/o best day −0.012R), and part of the 2-year gain is April 2025. WB4 is the better car, not yet a
proven profitable one; live testing decides. Signed off for Testing F at the top of its priority order.

## Ready to deploy after close — pending, NOT applied
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective session 2026-11-17 (or the next session if later).
Account: **Testing F** (`config/account_testingf.yaml`) — not the parent's account (On Deck = `account_testing`); no L3-family setup
there (the sister copies go to Testing A (fromopen-FD WB4) and Testing E (rsi5hi-FD WB4); keeping the three apart avoids the shared
3-lots-per-symbol limit on the same gap-down names); no other Workbench copy is pending for Testing F. Testing F = 30 open lots per
setup, cost filter 0.15R, no setup latch (all as tested in the BOOK check). Twin check: `twin_key` strips only `-FD`, so
`...-FD-WB4` is not the parent's twin key; different account anyway. Parent stays in On Deck unchanged.
1. `config/account_testingf.yaml`, under `strategies:` add
   ```yaml
   L3-gap-slope-lowdist-FD-WB4:
     # Workbench copy of L3-gap-slope-lowdist-FD (On Deck), Mechanic 2026-11-16: dist from low > 0.82 ATR + rsi5 >= 50
     # + every lot closed 75 min after entry; research/workbench/L3-gap-slope-lowdist-FD/RESULTS.md. Effective 2026-11-17.
     enabled: true
     type: lab
     module: research/workbench/L3-gap-slope-lowdist-FD/modules/L3-gap-slope-lowdist-FD-WB4.py
     min_adv: 0
     window: [950, 1500]
     prefilter: "gap_le:-2.6573517322540283"
     scale_out_r: null
     time_stop_min: 75
     time_stop_min_r: 99.0
     tags: [workbench, "parent:L3-gap-slope-lowdist-FD"]
   ```
   and put `L3-gap-slope-lowdist-FD-WB4` FIRST in its `live.setup_order` (ahead of the ROT1 rotated setups).
2. `config/setup_names.yaml`: `L3-gap-slope-lowdist-FD-WB4: {name: "Gap-Down Bounce-off-Low Fade (all day) — WB4: bounce > 0.82 ATR, RSI5 ≥ 50, 75-min hold", side: short, what: "09:50-15:00: a stock that gapped down 2.7%+ with its 20-bar average turning up has bounced 0.82-0.98 daily ATR off its low on a still-rising bar (5-bar RSI 50+); short the bounce; out at target, stop or 75 minutes."}`
3. `research/ledger.jsonl`: id `2026-11-16-wb-l3-lowdist-wb4`, effective 2026-11-17, title "Workbench copy L3-gap-slope-lowdist-FD-WB4
   added to Testing F, first in setup_order (Mechanic pass)", patch `{"strategies.L3-gap-slope-lowdist-FD-WB4 (testingf)": [null,
   "added, enabled"], "live.setup_order (testingf)": ["...", "WB4 first"]}`, evidence this file, approved_by "owner rule
   research/workbench/RULES.md 5"; then `python -m mcf.research.ledger check`.
4. `python -m mcf.report.assignments`, `pytest -q`, commit, push after 16:05 ET (setup-freeze).
Note: the runner's time stop acts on its poll (≈ 1 min); the backtest exits at the next 1-min open after 75 min. The rsi5 layer lives
in the copy's own module (no runner change).

## Files
`code/` (sim_low.py, load_low.py, go_low.py, decl_low.py, report_low.py, cand_low.py, paths_inc.py, rep_check.py, rep_only.py; they
import `sim.py`/`sim2.py` and reuse `fetch_replay.py` from `../L3-gap-slope-fromopen-FD/code`; run from a scratch dir holding their
inputs), `results_all.csv` (every config × test × split), `shape.csv`, `variants.jsonl`, `DIAGNOSIS.md`, `BLUEPRINT_worst5.md` /
`BLUEPRINT_best5.md` (teardown text), engine + 10 trade PNGs.
