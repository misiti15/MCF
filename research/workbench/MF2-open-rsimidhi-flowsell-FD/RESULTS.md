# Workbench RESULTS — Early Sellers, Mid-High RSI (all day) `MF2-open-rsimidhi-flowsell-FD` (On Deck) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16, built ~19:45-21:40 ET (after the close; research files only — no
config change, no deploy).

## Verdict — supervisor sign-off
> **Recommended: `MF2-open-rsimidhi-flowsell-FD-WB3`** — parent + four entry layers: do not short a stock whose 20-SMA (5-min)
> is rising (slope <= +0.05%/bar), do not short a gap-up > +2%, RSI(14) band 55-62 (was 55-65), heat between −40 and −30 (was
> <= −30), and ADV >= $150M (was $95M). Stop, target, refire, window unchanged. **PASS — better than the parent in both tests on
> avg R, avg R w/o best day and worst day, and positive after costs in both tests and in every 2-year split.**

| copy | change | replay avg R (parent −0.162) | 2-year avg R (parent −0.007) | w/o best day (replay / 2y; parent −0.233 / −0.027) | worst day (replay / 2y; parent −33.1 / −35.5R) | trades (replay / 2y; parent 177 / 2,956) | verdict |
|---|---|---|---|---|---|---|---|
| WB1 | NEW: skip rising 20-SMA (slope > +0.05%/bar) + skip gap-ups > +2% | **+0.088** | **+0.006** | −0.008 / −0.018 | −6.6 / −26.8 | 114 / 2,271 | PASS (contained in WB3) |
| WB2 | WB1 + RSI(14) <= 62 (P10) + ADV >= $150M (P2) | **+0.131** | **+0.078** | +0.061 / +0.052 | −6.6 / −21.5 | 96 / 1,410 | PASS (contained in WB3) |
| **WB3** | WB2 + heat >= −40 (P9 floor) | **+0.183** | **+0.087** | **+0.109 / +0.064** | **−4.5 / −18.3** | 76 / 1,276 | **PASS — recommended** |

Supervisor sign-off (what changed, why, before/after, where it gives back):
- **What / why.** The parent's losses come from shorting STRENGTH: a stock whose 5-min 20-SMA is still rising or that gapped up
  more than 2% (live: 34 such trades −0.82R, −28.0R; the other 105 +0.28R, +29.8R), plus the top of the RSI band and the most
  extreme heat (a trend day, not a fading pop — the same finding as RW5). The stop looked like the culprit (57% of exits, 32
  trades stopped within 10 minutes) but every wider stop is worse in both tests; the fix is WHAT gets shorted, not the exhaust.
- **Overall before → after (identical pipeline, LR8 costs, On Deck book incl. its 0.15R cost filter):** replay −0.162 →
  **+0.183R** (total −28.7R → +13.9R; w/o best day −0.233 → +0.109); 2-year −0.007 → **+0.087R** (total −22R → +111R; w/o best day
  −0.027 → +0.064); better in every 2-year split (TRAIN +0.042 → +0.056, VALID −0.054 → +0.078, FWD +0.107 → +0.356). Worst day
  replay −33.1R (11-06) → −4.5R (WB3 takes no trade on 11-06); 2-year −35.5R → −18.3R (both 2026-07-27). Up days (SPY open→close
  > +0.25%): 2-year −0.282R on 664 trades → −0.173R on 255 (−1.34R → −0.42R per up day) — the known up-day symptom is cut without
  any market gate. Paired-by-day vs parent: replay t +1.21 (dR +42.6R), 2-year t +1.55 (dR +132.5R).
- **Where it gives back:** (1) fewer trades — replay 177 → 76 (−57%), 2-year 2,956 → 1,276 (−57%; ~2.4 a day); (2) gap-up winners:
  TER 11-06 (+2.68R live, +9.7% gap) would not be taken; (3) up days are still negative (−0.173R), and down-day avg R in the 2-year
  stays about the same (+0.129 → +0.247R per trade but on fewer trades: +1.41 → +1.37R per down day).
- **Honest limits:** no copy clears the configs-counted bar max(1.5, sqrt(2 ln 48)) = 2.78 (WB3 2-year t +1.55; under the owner's
  2026-11-16 clarified rule the t is reported, not used to pass). The heat floor was added in Round 2 after the Round 1 one-part
  test (V09) showed only a small gain; neighbours agree (C8 bp floor +0.146 / +0.079, D1 heat+bp floor +0.210 / +0.093, D2 slope 0.02
  +0.131 / +0.081, D4 gap 1% +0.088 / +0.076 — a plateau, not a spike). The replay is the parent's live signal symbol-days, so the
  ADV part (P2) is scored by the 2-year test only. The replay is 76 trades on 22 sessions — the 2-year test (1,276 trades) carries the
  weight.

## Method (identical for parent and every copy) — reused harness (RW5 / L3 Workbench code, `code/`)
- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live in any
  account and was shortable+ETB, 2026-10-12..11-13 (222 symbol-days, 25 sessions). 1-min SIP bars (read-only GET) → lab frame
  (`mcf.report.engine.lab_frame` + daily priors). Parity: 139 of 141 live trades matched by symbol / day / entry minute; replay R vs
  live R correlation 0.95, same exit kind 86%.
- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted in
  cand2y.py / paths2y.py / load.py), ADV >= $95M (parent), names shortable+ETB on >= 90% of the universe snapshots (E90 proxy, same
  file as the L3 / RW5 jobs). Splits TRAIN <= 2025-12-31, VALID 2026-01..10-05, FWD 10-06..11-04.
- Same engine for both: MF2-FD sensors on 5-min bar close (heat <= −30, 55 <= RSI(14) <= 65, buyPressure < −0.25), window
  09:50-15:00, refire on with cooldown 1 (LabStrategy `refire_select`), entry at the signal-bar close, price >= $5, exits on 1-min
  bars (stop first; target only when traded through by $0.01; flat 15:55), **LR8 costs**, **On Deck book**: <= 150 lots per setup,
  <= 3 per symbol, no per-setup latch, account cost filter `max_stop_cost_r` 0.15 (applied after the refire chain, as the runner
  does). R = P&L / the parent's stop distance (0.125 ATR) for every copy, so a copy cannot gain by re-scaling R. The parent's live
  record is NOT used in the pass decision.
- Module parity (WB modules vs bench mask): WB1 229 / 4,948, WB2 173 / 2,648, WB3 138 / 2,337 bar hits (replay / 2-year), 100%
  agreement; each module loads in `LabStrategy` (t1s05, short).
- Rule changes inside the replay window (ledger): 10-20 promotion to Primary, 10-21 promotion = move, 10-23 ST-A, 10-28 Primary
  size / cap 30, 10-29 Primary −2R latch, 10-30 Testing cost filter 0.15R, 11-11 TEAM-6 move back to Testing 1, 11-12 LR1/LR3/LR5/LR7
  + LR8 costs + ONDECK. The replay applies today's On Deck rules to every session, so none of these mixes into the comparison.

## Every configuration tried (48), including failures
Round 1 (V01-V29, one part each, pre-declared in code/decl.py before any 2-year score), Round 2 (S1-S6 thresholds and combos
C1-C9, declared after Round 1), Round 3 (D1-D4, declared after Round 2; C4 re-run identically). Pass rule (owner 2026-11-16): meets
or exceeds the parent's avg R in BOTH tests (meets = within 0.01R or >= 95%), and not worse on avg R w/o best day by > 0.02R or on
worst day by > 10%. 30 pass, 18 fail.

| copy | config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | t vs parent (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
|  | PARENT | 177 | -0.162 | -0.233 | -33.1 | 2956 | -0.007 | -0.027 | -35.5 | +0.00 / +0.00 | — |
|  | V01 ADV >= $150M (P2) | 177 | -0.162 | -0.233 | -33.1 | 2423 | +0.027 | +0.006 | -32.2 | +0.00 / +2.44 | PASS |
|  | V02 price >= $10 (P3) | 177 | -0.162 | -0.233 | -33.1 | 2954 | -0.007 | -0.026 | -35.5 | +0.00 / +1.00 | PASS |
|  | V03 window start 09:50->10:15 (P6/P7) | 177 | -0.162 | -0.233 | -33.1 | 2948 | -0.010 | -0.029 | -37.5 | +0.00 / -1.20 | PASS |
|  | V04 window start 09:50->11:00 (P6/P7) | 117 | -0.059 | -0.146 | -7.6 | 2524 | -0.011 | -0.034 | -36.4 | +0.70 / -0.14 | PASS |
|  | V05 window end 15:00->14:00 (P6) | 164 | -0.142 | -0.218 | -33.2 | 2483 | -0.011 | -0.033 | -35.5 | +1.59 / -0.12 | PASS |
|  | V06 window end 15:00->13:00 (P6) | 150 | -0.113 | -0.197 | -33.2 | 1898 | -0.010 | -0.035 | -35.5 | +1.71 / +0.04 | PASS |
|  | V07 refire off (P8) | 139 | -0.088 | -0.155 | -18.5 | 2522 | -0.022 | -0.042 | -34.5 | +1.02 / -0.99 | FAIL — 2y avg R -0.022 < parent -0.007 |
|  | V08 refire cooldown 1->3 (P8) | 156 | -0.156 | -0.217 | -26.6 | 2689 | -0.022 | -0.043 | -34.5 | +0.50 / -1.49 | FAIL — 2y avg R -0.022 < parent -0.007 |
|  | V09 heat in [-40,-30] (P9 floor) | 145 | -0.123 | -0.193 | -23.5 | 2704 | -0.008 | -0.026 | -30.2 | +0.95 / -0.02 | PASS |
|  | V10 heat <= -35 (P9) | 78 | -0.259 | -0.318 | -23.4 | 1033 | +0.016 | -0.022 | -12.9 | +0.45 / +0.40 | FAIL — replay avg R -0.259 < parent -0.162; replay w/o best day -0.318 vs -0.233 |
|  | V11 RSI(14) 55-62 (P10 top) | 143 | -0.153 | -0.209 | -31.2 | 2186 | +0.029 | +0.007 | -29.1 | +0.98 / +1.78 | PASS |
|  | V12 RSI(14) 57-65 (P10 bottom) | 132 | -0.197 | -0.277 | -22.4 | 2394 | -0.019 | -0.039 | -29.0 | +0.19 / -0.56 | FAIL — replay avg R -0.197 < parent -0.162; replay w/o best day -0.277 vs -0.233; 2y avg R -0.019 < parent -0.007 |
|  | V13 buyPressure in [-0.5,-0.25) (P11 floor) | 151 | -0.106 | -0.187 | -19.2 | 2683 | -0.011 | -0.031 | -31.1 | +0.83 / -0.32 | PASS |
|  | V14 buyPressure < -0.30 (P11) | 129 | -0.180 | -0.285 | -30.9 | 2002 | -0.030 | -0.049 | -28.0 | +0.54 / -0.63 | FAIL — replay avg R -0.180 < parent -0.162; replay w/o best day -0.285 vs -0.233; 2y avg R -0.030 < parent -0.007; 2y w/o best day -0.049 vs -0.027 |
|  | V15 lots per symbol 3->1 (P14, tool) | 147 | -0.133 | -0.198 | -21.5 | 2609 | -0.020 | -0.040 | -34.5 | +0.70 / -0.97 | FAIL — 2y avg R -0.020 < parent -0.007 |
|  | V16 cost filter 0.15->0.10 (P17) | 148 | -0.120 | -0.213 | -26.5 | 2118 | +0.004 | -0.020 | -28.8 | +1.24 / +0.61 | PASS |
|  | V17 cost filter off (P17, account-level) | 275 | -0.122 | -0.282 | -37.7 | 4732 | -0.046 | -0.064 | -36.2 | -0.15 / -2.18 | FAIL — replay w/o best day -0.282 vs -0.233; replay worst day -37.7 vs -33.1R; 2y avg R -0.046 < parent -0.007; 2y w/o best day -0.064 vs -0.027 |
|  | V18 1R 0.25->0.30 ATR (P20) | 196 | -0.204 | -0.370 | -49.2 | 3314 | -0.007 | -0.029 | -42.6 | -0.44 / -0.02 | FAIL — replay avg R -0.204 < parent -0.162; replay w/o best day -0.370 vs -0.233; replay worst day -49.2 vs -33.1R; 2y worst day -42.6 vs -35.5R |
|  | V19 stop 0.5R->0.75R (P23) | 222 | -0.200 | -0.362 | -49.5 | 3667 | -0.027 | -0.049 | -50.8 | -0.53 / -0.88 | FAIL — replay avg R -0.200 < parent -0.162; replay w/o best day -0.362 vs -0.233; replay worst day -49.5 vs -33.1R; 2y avg R -0.027 < parent -0.007; 2y w/o best day -0.049 vs -0.027; 2y worst day -50.8 vs -35.5R |
|  | V20 geom t1s1: stop 0.5R->1R (P23) | 240 | -0.122 | -0.268 | -42.7 | 4070 | -0.014 | -0.038 | -71.2 | -0.01 / -0.25 | FAIL — replay w/o best day -0.268 vs -0.233; replay worst day -42.7 vs -33.1R; 2y worst day -71.2 vs -35.5R |
|  | V21 geom t05s05: target 1R->0.5R (P24) | 177 | -0.058 | -0.101 | -16.1 | 2958 | -0.052 | -0.065 | -30.2 | +0.89 / -1.88 | FAIL — 2y avg R -0.052 < parent -0.007; 2y w/o best day -0.065 vs -0.027 |
|  | V22 geom holdtr: stop 1R, no target, trail 1R after +1R (P23/P24) | 240 | -0.288 | -0.465 | -54.6 | 4069 | -0.019 | -0.049 | -72.4 | -1.07 / -0.31 | FAIL — replay avg R -0.288 < parent -0.162; replay w/o best day -0.465 vs -0.233; replay worst day -54.6 vs -33.1R; 2y avg R -0.019 < parent -0.007; 2y w/o best day -0.049 vs -0.027; 2y worst day -72.4 vs -35.5R |
|  | V23 trail 0.5R after +0.75R (P23 move) | 177 | -0.172 | -0.231 | -27.5 | 2956 | -0.021 | -0.038 | -33.5 | -0.22 / -1.21 | FAIL — replay avg R -0.172 < parent -0.162; 2y avg R -0.021 < parent -0.007 |
|  | V24 gate: skip SPY > +0.30% since 09:50 (new) | 170 | -0.193 | -0.268 | -33.1 | 2566 | -0.003 | -0.026 | -35.5 | -0.97 / +0.35 | FAIL — replay avg R -0.193 < parent -0.162; replay w/o best day -0.268 vs -0.233 |
|  | V25 gate: skip SPY above 09:30-09:50 high (new) | 164 | -0.198 | -0.276 | -33.1 | 2254 | -0.021 | -0.047 | -35.5 | -0.71 / -0.52 | FAIL — replay avg R -0.198 < parent -0.162; replay w/o best day -0.276 vs -0.233; 2y avg R -0.021 < parent -0.007; 2y w/o best day -0.047 vs -0.027 |
|  | V26 skip rising 20-SMA slope > +0.05%/bar (new) | 121 | +0.030 | -0.063 | -6.6 | 2605 | +0.004 | -0.018 | -34.3 | +1.11 / +1.22 | PASS |
|  | V27 skip gap-ups > +2% (new) | 123 | +0.061 | -0.029 | -7.6 | 2494 | -0.003 | -0.025 | -25.9 | +1.13 / +0.31 | PASS |
|  | V28 skip > 1% below VWAP (new) | 60 | +0.054 | -0.103 | -5.5 | 1508 | -0.021 | -0.033 | -11.5 | +1.02 / -0.10 | FAIL — 2y avg R -0.021 < parent -0.007 |
|  | V29 skip ATR% (5-min) > 0.8 (new) | 88 | -0.003 | -0.125 | -8.6 | 2181 | -0.030 | -0.051 | -20.1 | +0.83 / -0.84 | FAIL — 2y avg R -0.030 < parent -0.007; 2y w/o best day -0.051 vs -0.027 |
|  | S1 slope <= +0.10 | 125 | +0.028 | -0.063 | -6.6 | 2692 | -0.003 | -0.024 | -34.3 | +1.07 / +0.65 | PASS |
|  | S2 slope <= +0.02 | 120 | +0.041 | -0.053 | -6.6 | 2536 | +0.005 | -0.017 | -34.3 | +1.10 / +1.24 | PASS |
|  | S3 gap <= +1% | 113 | +0.028 | -0.074 | -7.6 | 2221 | -0.002 | -0.022 | -23.5 | +0.94 / +0.30 | PASS |
|  | S4 gap <= +3% | 127 | +0.024 | -0.066 | -8.7 | 2704 | -0.016 | -0.038 | -32.3 | +1.07 / -0.68 | PASS |
|  | S5 ADV >= $200M | 177 | -0.162 | -0.233 | -33.1 | 2005 | +0.024 | +0.001 | -27.8 | +0.00 / +1.26 | PASS |
|  | S6 RSI(14) 55-60 | 116 | -0.207 | -0.253 | -26.1 | 1643 | +0.030 | +0.005 | -21.6 | +0.32 / +1.01 | FAIL — replay avg R -0.207 < parent -0.162 |
| WB1 | C1 slope<=0.05 + gap<=2% | 114 | +0.088 | -0.008 | -6.6 | 2271 | +0.006 | -0.018 | -26.8 | +1.16 / +0.73 | PASS |
|  | C2 C1 + ADV>=$150M | 114 | +0.088 | -0.008 | -6.6 | 1874 | +0.043 | +0.018 | -25.7 | +1.16 / +1.73 | PASS |
|  | C3 C1 + RSI<=62 | 96 | +0.131 | +0.061 | -6.6 | 1698 | +0.048 | +0.022 | -21.5 | +1.21 / +1.50 | PASS |
| WB2 | C4 C1 + ADV150 + RSI<=62 | 96 | +0.131 | +0.061 | -6.6 | 1410 | +0.078 | +0.052 | -21.5 | +1.21 / +1.73 | PASS |
|  | C5 C4 + cost/R<=0.10 | 78 | +0.175 | +0.055 | -5.5 | 1068 | +0.075 | +0.045 | -18.2 | +1.24 / +1.17 | PASS |
|  | C6 C2 + cost/R<=0.10 | 92 | +0.152 | +0.027 | -5.5 | 1383 | +0.057 | +0.028 | -21.4 | +1.27 / +1.34 | PASS |
| WB3 | C7 C4 + heat>=-40 | 76 | +0.183 | +0.109 | -4.5 | 1276 | +0.087 | +0.064 | -18.3 | +1.21 / +1.55 | PASS |
|  | C8 C4 + bp>=-0.5 | 90 | +0.146 | +0.073 | -5.4 | 1307 | +0.079 | +0.052 | -20.3 | +1.21 / +1.56 | PASS |
|  | C9 C4 + end 13:00 | 80 | +0.241 | +0.149 | -6.6 | 951 | +0.081 | +0.045 | -21.5 | +1.41 / +0.98 | PASS |
|  | D1 C4 + heat>=-40 + bp>=-0.5 | 70 | +0.210 | +0.147 | -3.3 | 1183 | +0.093 | +0.068 | -17.2 | +1.23 / +1.47 | PASS |
|  | D2 C4 with slope<=0.02 | 96 | +0.131 | +0.061 | -6.6 | 1387 | +0.081 | +0.054 | -21.5 | +1.21 / +1.73 | PASS |
|  | D3 C4 + heat>=-40 + end 14:00 | 68 | +0.223 | +0.142 | -4.5 | 1094 | +0.070 | +0.043 | -18.3 | +1.25 / +1.05 | PASS |
|  | D4 C4 with gap<=1% | 89 | +0.088 | +0.011 | -6.6 | 1262 | +0.076 | +0.052 | -18.2 | +1.06 / +1.37 | PASS |

| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |
|---|---|---|---|
| PARENT | +0.042 (1145) | -0.054 (1639) | +0.107 (172) |
| V01 ADV >= $150M (P2) | +0.069 (939) | -0.016 (1334) | +0.150 (150) |
| V02 price >= $10 (P3) | +0.044 (1143) | -0.054 (1639) | +0.107 (172) |
| V03 window start 09:50->10:15 (P6/P7) | +0.038 (1141) | -0.055 (1635) | +0.107 (172) |
| V04 window start 09:50->11:00 (P6/P7) | +0.059 (996) | -0.071 (1374) | +0.077 (154) |
| V05 window end 15:00->14:00 (P6) | +0.023 (935) | -0.040 (1411) | +0.057 (137) |
| V06 window end 15:00->13:00 (P6) | -0.052 (683) | +0.003 (1101) | +0.119 (114) |
| V07 refire off (P8) | +0.031 (973) | -0.072 (1410) | +0.108 (139) |
| V08 refire cooldown 1->3 (P8) | +0.029 (1034) | -0.070 (1501) | +0.104 (154) |
| V09 heat in [-40,-30] (P9 floor) | +0.019 (1045) | -0.039 (1505) | +0.108 (154) |
| V10 heat <= -35 (P9) | +0.071 (403) | -0.037 (568) | +0.145 (62) |
| V11 RSI(14) 55-62 (P10 top) | +0.068 (844) | -0.005 (1219) | +0.104 (123) |
| V12 RSI(14) 57-65 (P10 bottom) | +0.055 (927) | -0.076 (1324) | +0.041 (143) |
| V13 buyPressure in [-0.5,-0.25) (P11 floor) | +0.029 (1045) | -0.053 (1481) | +0.114 (157) |
| V14 buyPressure < -0.30 (P11) | +0.005 (769) | -0.071 (1114) | +0.125 (119) |
| V15 lots per symbol 3->1 (P14, tool) | +0.031 (1013) | -0.066 (1450) | +0.095 (146) |
| V16 cost filter 0.15->0.10 (P17) | +0.055 (774) | -0.044 (1206) | +0.125 (138) |
| V17 cost filter off (P17, account-level) | -0.036 (1952) | -0.075 (2526) | +0.160 (254) |
| V18 1R 0.25->0.30 ATR (P20) | +0.039 (1309) | -0.061 (1821) | +0.199 (184) |
| V19 stop 0.5R->0.75R (P23) | +0.020 (1451) | -0.084 (2014) | +0.205 (202) |
| V20 geom t1s1: stop 0.5R->1R (P23) | +0.051 (1632) | -0.084 (2223) | +0.221 (215) |
| V21 geom t05s05: target 1R->0.5R (P24) | -0.041 (1147) | -0.066 (1639) | +0.011 (172) |
| V22 geom holdtr: stop 1R, no target, trail 1R after +1R (P23/P24) | +0.022 (1632) | -0.075 (2222) | +0.249 (215) |
| V23 trail 0.5R after +0.75R (P23 move) | +0.035 (1145) | -0.076 (1639) | +0.123 (172) |
| V24 gate: skip SPY > +0.30% since 09:50 (new) | +0.029 (1015) | -0.045 (1399) | +0.164 (152) |
| V25 gate: skip SPY above 09:30-09:50 high (new) | +0.005 (877) | -0.060 (1251) | +0.181 (126) |
| V26 skip rising 20-SMA slope > +0.05%/bar (new) | +0.046 (1033) | -0.039 (1427) | +0.128 (145) |
| V27 skip gap-ups > +2% (new) | +0.010 (938) | -0.029 (1401) | +0.147 (155) |
| V28 skip > 1% below VWAP (new) | -0.059 (591) | -0.012 (828) | +0.143 (89) |
| V29 skip ATR% (5-min) > 0.8 (new) | +0.039 (864) | -0.091 (1175) | +0.048 (142) |
| S1 slope <= +0.10 | +0.040 (1058) | -0.048 (1481) | +0.141 (153) |
| S2 slope <= +0.02 | +0.056 (1003) | -0.043 (1390) | +0.115 (143) |
| S3 gap <= +1% | +0.006 (837) | -0.029 (1241) | +0.177 (143) |
| S4 gap <= +3% | +0.013 (1021) | -0.050 (1515) | +0.116 (168) |
| S5 ADV >= $200M | +0.069 (799) | -0.015 (1086) | +0.083 (120) |
| S6 RSI(14) 55-60 | +0.088 (635) | -0.009 (916) | +0.019 (92) |
| C1 slope<=0.05 + gap<=2% | +0.014 (879) | -0.016 (1259) | +0.167 (133) |
| C2 C1 + ADV>=$150M | +0.037 (727) | +0.023 (1026) | +0.245 (121) |
| C3 C1 + RSI<=62 | +0.045 (652) | +0.029 (948) | +0.241 (98) |
| C4 C1 + ADV150 + RSI<=62 | +0.075 (541) | +0.054 (780) | +0.311 (89) |
| C5 C4 + cost/R<=0.10 | +0.071 (381) | +0.039 (612) | +0.393 (75) |
| C6 C2 + cost/R<=0.10 | +0.041 (499) | +0.035 (785) | +0.318 (99) |
| C7 C4 + heat>=-40 | +0.056 (484) | +0.078 (714) | +0.356 (78) |
| C8 C4 + bp>=-0.5 | +0.090 (504) | +0.049 (718) | +0.272 (85) |
| C9 C4 + end 13:00 | +0.014 (349) | +0.090 (540) | +0.379 (62) |
| D1 C4 + heat>=-40 + bp>=-0.5 | +0.072 (448) | +0.082 (661) | +0.314 (74) |
| D2 C4 with slope<=0.02 | +0.074 (530) | +0.059 (768) | +0.311 (89) |
| D3 C4 + heat>=-40 + end 14:00 | +0.019 (409) | +0.077 (622) | +0.336 (63) |
| D4 C4 with gap<=1% | +0.063 (482) | +0.059 (698) | +0.302 (82) |

Notes on the table: V01 / S5 (ADV) cannot be replayed (replay = names that passed $95M live), so their replay rows equal the
parent. V15 (1 lot per symbol) is a backtest-only tool part. V16 / C5 / C6 (cost/R <= 0.10) would need a module clause in a
testing account (the 0.15 filter is account-wide). V22 / V23 (holdtr / trail) are live-capable (`geom: holdtr`, `trail_r` /
`trail_after_r` in stop-distance units) but fail. Passing parts NOT shipped: V02 / V03 (no effect), V04 / V05 / V06 (2y no better or
VALID / TRAIN worse), V09 / V13 (small; folded only as the WB3 heat floor), V16 (2y +0.004 only; C5 / C6 not better than C4 / C7),
S1-S5 thresholds (neighbours of the shipped values — plateau), C8 / D1 (bp floor: higher avg, same total, one more layer), C9 / D3
(end 13:00 / 14:00: TRAIN worse), D2 / D4 (neighbours).
FAIL: V07 refire off, V08 cooldown 3, V10 heat <= −35, V12 RSI floor 57, V14 bp < −0.30, V15 1 lot per symbol, V17 cost filter off,
V18 1R 0.30 ATR, V19 stop 0.75R, V20 stop 1R (t1s1), V21 target 0.5R, V22 holdtr, V23 trail, V24 SPY > +0.30% since 09:50 gate,
V25 SPY above its 09:30-09:50 high gate, V28 skip > 1% below VWAP, V29 ATR% cap, S6 RSI 55-60.

## Shape (extras.csv; SPY day type open→close > +0.25% up / < −0.25% down)
| config | test | win % | avg win | avg loss | median hold (min) | stop share | target share | up-day avg R (n) | flat | down |
|---|---|---|---|---|---|---|---|---|---|---|
| PARENT | replay | 32.8% | +1.643 | −1.042 | 36 | 64% | 25% | −0.144 (28) | −0.545 (72) | +0.190 (77) |
| PARENT | 2y | 38.4% | +1.637 | −1.032 | 50 | 56% | 28% | −0.282 (664) | −0.026 (841) | +0.129 (1,451) |
| WB1 (C1) | 2y | 39.1% | +1.627 | −1.037 | 52 | 55% | 28% | −0.290 (484) | −0.055 (661) | +0.169 (1,126) |
| WB2 (C4) | 2y | 41.3% | +1.642 | −1.020 | 52.5 | 53% | 30% | −0.182 (291) | −0.043 (396) | +0.249 (723) |
| WB3 (C7) | replay | 46.1% | +1.627 | −1.050 | 50 | 51% | 34% | −0.016 (18) | +0.016 (12) | +0.304 (46) |
| WB3 (C7) | 2y | 41.7% | +1.630 | −1.017 | 54 | 52% | 30% | −0.173 (255) | −0.021 (363) | +0.247 (658) |

The copies work by raising the win rate (38% → 42% over 2 years, 33% → 46% in the replay) at the same bracket — avg win / loss do
not change; they remove losing entries, mostly on up and flat days.

## Pending config change — "ready to deploy after close" (NOT applied)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective the next session. One copy only: **WB3**
(it contains WB1 and WB2; running them side by side would be near-twins). The parent stays in On Deck, unchanged (Workbench rule 1).
Destination: **Testing 2** (`config/account_testing2.yaml`) — a testing account, not On Deck / Primary (rule 6 needs the owner for
those) and not the parent's account (twins rule). Testing 2 has no MF2 copy enabled (the MF2 base moved to Explore 1 on 11-04;
MF2-FD is `enabled: false` there), runs the same 0.15R cost filter, no per-setup latch, 50 lots per setup (WB3 takes ~2.4 trades a
day). If another Workbench job has already claimed the FIRST slot in Testing 2 tonight, put WB3 right after it (the main session
decides the order between Workbench copies).
1. Module: copy `research/workbench/MF2-open-rsimidhi-flowsell-FD/modules/MF2-open-rsimidhi-flowsell-FD-WB3.py` to
   `research/bdi/fullday/MF2-open-rsimidhi-flowsell-FD-WB3.py`.
2. `config/account_testing2.yaml`, under `strategies:` add
   ```yaml
   MF2-open-rsimidhi-flowsell-FD-WB3:
     # Workbench copy of MF2-open-rsimidhi-flowsell-FD (On Deck), Mechanic 2026-11-16: + skip rising 20-SMA / gap-ups > 2%
     # + RSI(14) 55-62 + heat -40..-30 + ADV $150M; research/workbench/MF2-open-rsimidhi-flowsell-FD/RESULTS.md.
     refire: true
     refire_cooldown: 1
     enabled: true
     type: lab
     module: research/bdi/fullday/MF2-open-rsimidhi-flowsell-FD-WB3.py
     min_adv: 150000000
     window: [950, 1500]
     scale_out_r: null
     tags: [workbench, "parent:MF2-open-rsimidhi-flowsell-FD"]
   ```
   and put `MF2-open-rsimidhi-flowsell-FD-WB3` FIRST in `live.setup_order` (rule 5).
3. `config/setup_names.yaml`: `MF2-open-rsimidhi-flowsell-FD-WB3: {name: "Early Sellers, Mid-High RSI (all day) — WB3: skip rising 20-SMA / gap-ups > 2% + RSI 55-62 + heat -40..-30 + ADV $150M", side: short, what: "09:50-15:00: bearish heat between -40 and -30, net selling, RSI(14) 55-62, on a stock whose 20-SMA is not rising and that did not gap up more than 2%; short; target 1R / stop 0.5R (1R = 0.25 ATR), flat 15:55."}`
4. `research/ledger.jsonl`: id `2026-11-16-wb-mf2-wb3`, title "Workbench copy MF2-open-rsimidhi-flowsell-FD-WB3 added to Testing 2,
   first in setup_order (Mechanic pass)", patch `{"strategies.MF2-open-rsimidhi-flowsell-FD-WB3 (testing2)": [null, "added, enabled"],
   "live.setup_order (testing2)": ["...", "WB3 first"]}`, evidence this file, approved_by "owner rule research/workbench/RULES.md 5";
   then `python -m mcf.research.ledger check`.
5. Smoke test (the module reads `sma20_slope_pct` and `gap` from the live lab frame; NaN -> no signal, fail safe), `python -m
   mcf.report.assignments` (docs/live/assignments.json in the same commit), `pytest -q`, commit, push after 16:05 ET (setup-freeze).
Note: live fills (spread / quote checks, 24% of live signals) and the account's shared book will not match these tables one for one.
