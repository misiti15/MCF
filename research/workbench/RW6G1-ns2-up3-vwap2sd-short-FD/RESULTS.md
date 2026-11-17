# Workbench RESULTS — Big Gainer Fade, VWAP Band Guard (all day) `RW6G1-ns2-up3-vwap2sd-short-FD` (Graveyard) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16, built ~19:45-23:00 ET (after the close; research files only:
no config change, no deploy).

## Verdict — supervisor sign-off
> **Recommended: `RW6G1-ns2-up3-vwap2sd-short-FD-WB3`** — parent + four layers: entries from the 11:00 bar, the reclaim
> bar must close at least +0.5 SD above VWAP (same VWAP / SD as the owner's band guard, which stays), 20-day ADV >= $150M,
> opening gap <= +2%. **PASS — better than the parent in both tests on avg R, avg R w/o best day and worst day, and
> positive after costs in both tests (replay +0.168R, 2-year +0.018R).**

| copy | change | replay avg R (parent −0.003) | 2-year avg R (parent −0.084) | w/o best day (replay / 2y; parent −0.067 / −0.097) | worst day (replay / 2y; parent −3.4 / −28.8R) | trades (replay / 2y; parent 84 / 1,744) | verdict |
|---|---|---|---|---|---|---|---|
| WB1 | P6/P7: window start 09:50 → 11:00 | +0.011 | −0.045 | −0.051 / −0.083 | −3.4 / −9.1 | 81 / 1,745 | PASS (contained in WB3) |
| WB2 | NEW sensor: close >= VWAP + 0.5 SD at the signal bar | +0.099 | −0.050 | +0.033 / −0.060 | −3.2 / −7.6 | 39 / 806 | PASS (contained in WB3) |
| **WB3** | start 11:00 + close >= VWAP + 0.5 SD + ADV >= $150M + gap <= +2% | **+0.168** | **+0.018** | **+0.072 / −0.022** | **−2.1 / −6.2** | 28 / 512 | **PASS — recommended** |

Supervisor sign-off (what changed, why, before/after, where it gives back):
- **What / why.** The parent's losers are entries where the gainer reclaims its SMA50 while barely above VWAP (a trend
  resuming, not an exhausted run), morning reclaims, thin names and gap-and-go runners. WB3 shorts only the stretched
  afternoon reclaim (>= +0.5 SD over VWAP, from 11:00) in liquid names that did not gap up more than 2%. It drops all 5
  worst live trades (MDGL, LUNR, DKNG, TEM, NTSK) and keeps 3 of the 5 best (BMNR, SMR, APH).
- **Overall before → after (identical pipeline, LR8 costs, Graveyard book):** replay −0.003 → **+0.168R** (w/o best day
  −0.067 → +0.072; total −0.3R → +4.7R); 2-year −0.084 → **+0.018R** (−147R → +9R; w/o best day −0.097 → −0.022; worst
  day −28.8 → −6.2R); better in every 2-year split (TRAIN −0.148 → −0.001, VALID −0.054 → +0.023, FWD −0.008 → +0.127);
  win 46% → 52% (2y). Paired-by-day t vs parent: 2-year +2.47 (dR +156.5R), replay +0.80 (dR +5.0R).
- **Up days (this is a short that fades big gainers):** 2-year up days (SPY open→close > +0.3%) −0.206 → −0.078R
  (613 → 218 trades); flat −0.060 → +0.059; down +0.045 → +0.132. Up days are still the losing condition — smaller,
  not gone. The SPY-since-09:50 gates that would cut them (V24, V25, C9, E1) all fail: the live sessions' best day
  (11-09, SPY +0.4..1.0% since 09:50) is an up-tape fade day, and the extreme-rally guard E1 also removes 2025-04-07.
- **Where it gives back:** (1) far fewer trades — replay 84 → 28, 2-year 1,744 → 512 (−71%), so it needs more sessions
  to build a record (about 1 trade per session); (2) two of the five best live trades (WWD 11-03, MDB 10-29: z 0.45 /
  0.32) are not taken; (3) **one-big-day check: the 2-year record leans on 2025-04-07 (+19.7R, 43 trades; 214% of the
  2-year total +9.2R) → `1 day` tag.** Without it WB3 is −0.022R/trade (parent without that day −0.069R), so the
  improvement holds without it but the copy is NOT positive without it. The replay's best day 11-09 (+3.3R) is 70% of
  the replay total (`1 day` tag on a 28-trade sample).
- **Destination book (info, not the pass test):** in the Testing A book (no −2R latch, 50 lots, stop cost <= 0.15R),
  parent T0 −0.029 / −0.024R vs WB3 (TB-D2) **+0.092 / −0.006R** (replay / 2y), w/o best day −0.094 / −0.057 vs
  **−0.029 / −0.046**, but 2-year worst day −10.3 → −11.4R (2025-04-09, tariff-pause rally; 10.7% worse — just over the
  10% line in that book only). The parent's Testing-book 2-year record itself rests on 04-07 (+47.2R of a −43.5R total).
- **Honest limits:** no copy clears the configs-counted bar max(1.5, sqrt(2 ln 52)) = 2.81 (WB3 2-year t 2.47; under the
  owner's 2026-11-16 clarified rule the t is reported, not used to pass). The gap cap (+2%) was picked between two
  pre-declared values (D1 +5% −0.000R, D2 +2% +0.018R) after Round 2 showed gap-up runners losing; both pass. The replay
  is the parent's live signal symbol-days (ETB), so the ADV part (P2) could not be replayed (replay names passed $95M live).
  The replay sample is small (84 parent trades, 20 sessions), so the 2-year backtest carries the weight.

## Method (identical for parent and every copy) — harness reused from research/workbench/RW5-.../code (L3 engine)
- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live in any
  account and was shortable+ETB, 2026-10-13..11-13 (71 symbol-days, 20 sessions). 1-min SIP bars (read-only GET) → lab
  frame (`mcf.report.engine.lab_frame` + daily priors as live); the VWAP band and z come from the module's own
  `vwap_band_block` / the same VWAP-SD on 5-min bars of the session (code/band.py). Parent replay 84 trades −0.003R vs
  live 63 trades −0.003R; bench signal bars match 81 of the 89 live signal bars that had frames (the rest are refire bars
  while a lot was held).
- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted in
  cand2y.py / paths2y.py / load.py), ADV >= $95M, names shortable+ETB on >= 90% of the universe snapshots (E90 proxy, same
  file as the earlier Workbench jobs). Band / z rebuilt from the 1-min history cache with volume (the frames carry no
  volume). Splits TRAIN <= 2025-12-31, VALID 2026-01..10-05, FWD 10-06..11-04.
- Same engine for both: sensors on 5-min bar close (close crosses above the SMA50 on this bar, fromOpen > 3, RSI(14) >= 60,
  no unresolved close above VWAP + 2 SD), refire chain with cooldown 1 (LabStrategy `refire_select`), entry at the
  signal-bar close, price >= $5, exits on 1-min bars (stop first; target only when traded through by $0.01; flat 15:55),
  **LR8 costs**, the parent's Graveyard book (<= 75 lots, <= 3 per symbol, −2R latch). Testing book (T0 / TB-*): no latch,
  <= 50 lots, stop-exit cost <= 0.15R (Testing A). SPY-since-09:50 from SPY 1-min closes (09:50 bar close reference).
  The parent's live record is NOT used in the pass decision.
- Module parity (WB modules' own `mask` vs the bench mask on the replay frames, volume from the SIP bars): parent 89/89,
  WB1 86/86, WB2 39/39, WB3 28/28 signal bars (code/parity.py).
- Rule changes inside the replay window (ledger): 10-20 twin rule / Testing −2R latch, 10-23 ST-A (latch off in Testing),
  10-30 Testing CF stop-cost filter, 11-04 move to Graveyard, 11-12 Graveyard REPV-11/12 sizing, 11-12 LR1 / LR5 / LR8
  costs. The replay applies today's rules to every session, so none of these mixes into the comparison.

## Every configuration tried (52), including failures
Round 1 (T0 + V01-V27, one part each, pre-declared in code/decl6.py before any 2-year score), Round 2 (S1-S3 and combos
C1-C11, declared after Round 1 + the 2-year component analysis), Round 3 (D1-D4 + Testing-book TB-*, declared after Round 2),
Round 4 (E1 / TB-E1 extreme-rally guard, declared after Round 3). Pass rule (owner 2026-11-16): meets or exceeds the
parent's avg R in BOTH tests (meets = within 0.01R or >= 95%), and not worse on avg R w/o best day by > 0.02R or on worst
day by > 10%. TB-* rows are judged against T0 (the parent in the same Testing book). Day types: SPY 09:30 open → 16:00
close > +0.3% up, < −0.3% down, else flat.

Configs: 52; counted bar max(1.5, sqrt(2 ln 52)) = 2.81

| copy | config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | t vs parent (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | PARENT | 84 | -0.003 | -0.067 | -3.4 | 1744 | -0.084 | -0.097 | -28.8 | +0.00 / +0.00 | — |
|  | T0 parent, testing book | 81 | -0.029 | -0.094 | -4.2 | 1789 | -0.024 | -0.057 | -10.3 | -0.83 / +1.32 | info (destination book) — parent re-scored in the Testing book (no latch, cap 50, stop cost <= 0.15R) |
|  | V01 ADV >= $150M (P2) | 84 | -0.003 | -0.067 | -3.4 | 1366 | -0.051 | -0.062 | -24.4 | +0.00 / +3.57 | PASS |
|  | V02 price >= $10 (P3) | 80 | -0.038 | -0.107 | -3.4 | 1687 | -0.087 | -0.100 | -27.7 | -1.94 / +0.05 | FAIL — replay avg R -0.038 < -0.003; replay w/o best day -0.107 vs -0.067 |
|  | V03 window end 15:00->14:00 (P6) | 38 | -0.118 | -0.211 | -3.2 | 851 | -0.120 | -0.135 | -28.8 | -0.69 / +1.57 | FAIL — replay avg R -0.118 < -0.003; replay w/o best day -0.211 vs -0.067; 2y avg R -0.120 < -0.084; 2y w/o best day -0.135 vs -0.097 |
| WB1 | V04 window start 09:50->11:00 (P6/P7) | 81 | +0.011 | -0.051 | -3.4 | 1745 | -0.045 | -0.083 | -9.1 | +0.90 / +0.81 | PASS |
|  | V05 refire off (P8) | 70 | +0.017 | -0.055 | -3.2 | 1487 | -0.082 | -0.091 | -28.8 | +0.46 / +1.55 | PASS |
|  | V06 refire cooldown 1->6 (P8) | 72 | +0.005 | -0.068 | -3.2 | 1565 | -0.081 | -0.093 | -28.8 | +0.31 / +1.62 | PASS |
|  | V07 fromOpen > 3 -> > 4 (P10) | 35 | +0.126 | +0.082 | -1.3 | 834 | -0.107 | -0.119 | -23.4 | +0.79 / +1.73 | FAIL — 2y avg R -0.107 < -0.084; 2y w/o best day -0.119 vs -0.097 |
|  | V08 fromOpen > 3 -> > 2.5 (P10) | 85 | -0.002 | -0.064 | -3.4 | 2564 | -0.108 | -0.115 | -29.9 | +1.00 / -3.34 | FAIL — 2y avg R -0.108 < -0.084 |
|  | V09 fromOpen <= 8 cap (P10) | 81 | +0.020 | -0.055 | -3.4 | 1691 | -0.081 | -0.094 | -23.5 | +1.28 / +1.05 | PASS |
|  | V10 RSI(14) >= 65 (P11) | 52 | -0.056 | -0.130 | -3.4 | 991 | -0.065 | -0.079 | -6.7 | -0.62 / +2.09 | FAIL — replay avg R -0.056 < -0.003; replay w/o best day -0.130 vs -0.067 |
|  | V11 RSI(14) >= 55 (P11) | 99 | -0.032 | -0.105 | -3.4 | 2662 | -0.072 | -0.081 | -54.0 | -1.05 / -0.88 | FAIL — replay avg R -0.032 < -0.003; replay w/o best day -0.105 vs -0.067; 2y worst day -54.0R vs -28.8R (>10% worse) |
|  | V12 band 2 SD -> 2.5 SD (P12) | 85 | +0.009 | -0.050 | -3.4 | 1991 | -0.068 | -0.075 | -33.1 | +1.00 / +0.47 | FAIL — 2y worst day -33.1R vs -28.8R (>10% worse) |
|  | V13 band 2 SD -> 1.5 SD (P12) | 72 | +0.006 | -0.061 | -3.4 | 1567 | -0.099 | -0.113 | -28.8 | +0.16 / -0.42 | FAIL — 2y avg R -0.099 < -0.084 |
|  | V14 band guard off (P12) | 86 | +0.020 | -0.035 | -3.4 | 2761 | -0.055 | -0.064 | -16.4 | +0.99 / -0.06 | PASS |
|  | V15 latch -2R off (P16, tool) | 89 | -0.018 | -0.081 | -4.6 | 2110 | -0.023 | -0.066 | -10.3 | -1.00 / +0.97 | FAIL — replay avg R -0.018 < -0.003; replay worst day -4.6R vs -3.4R (>10% worse) |
|  | V16 1R 0.25 -> 0.30 ATR (P20) | 89 | +0.011 | -0.036 | -4.1 | 1771 | -0.069 | -0.079 | -32.4 | +0.44 / +1.59 | FAIL — replay worst day -4.1R vs -3.4R (>10% worse); 2y worst day -32.4R vs -28.8R (>10% worse) |
|  | V17 cost/R <= 0.15 (P20/intake) | 77 | -0.018 | -0.083 | -4.2 | 1525 | -0.070 | -0.082 | -23.3 | -0.47 / +2.31 | FAIL — replay avg R -0.018 < -0.003; replay worst day -4.2R vs -3.4R (>10% worse) |
|  | V18 stop 1.0 -> 1.25R (P23) | 89 | +0.009 | -0.054 | -4.8 | 1790 | -0.084 | -0.097 | -36.1 | +0.36 / -0.20 | FAIL — replay worst day -4.8R vs -3.4R (>10% worse); 2y worst day -36.1R vs -28.8R (>10% worse) |
|  | V19 target 1.0 -> 0.8R (P24) | 84 | -0.035 | -0.101 | -3.4 | 1757 | -0.080 | -0.091 | -27.6 | -3.41 / +0.50 | FAIL — replay avg R -0.035 < -0.003; replay w/o best day -0.101 vs -0.067 |
|  | V20 target 1.0 -> 0.6R (P24) | 84 | -0.004 | -0.050 | -3.6 | 1799 | -0.073 | -0.084 | -20.2 | -0.03 / +0.73 | PASS |
|  | V21 BE stop after +0.5R (P23 move) | 84 | -0.000 | -0.047 | -3.2 | 1758 | -0.086 | -0.097 | -19.3 | +0.10 / -0.17 | PASS |
|  | V22 max hold 60 min (P26) | 89 | -0.030 | -0.051 | -2.6 | 1748 | -0.078 | -0.083 | -28.8 | -0.41 / +0.31 | FAIL — replay avg R -0.030 < -0.003 |
|  | V23 max hold 120 min (P26) | 84 | +0.013 | -0.045 | -3.4 | 1753 | -0.088 | -0.098 | -28.8 | +0.60 / -0.56 | PASS |
|  | V24 gate: skip SPY > +0.30% since 09:50 (new) | 43 | -0.041 | -0.092 | -3.2 | 1226 | -0.064 | -0.080 | -9.5 | -0.22 / +1.84 | FAIL — replay avg R -0.041 < -0.003; replay w/o best day -0.092 vs -0.067 |
|  | V25 gate: skip SPY above 09:30-09:50 high (new) | 40 | -0.092 | -0.141 | -3.2 | 954 | -0.047 | -0.068 | -9.5 | -0.48 / +2.41 | FAIL — replay avg R -0.092 < -0.003; replay w/o best day -0.141 vs -0.067 |
|  | V26 price >= VWAP at signal (new sensor) | 74 | +0.009 | -0.062 | -4.2 | 1511 | -0.079 | -0.091 | -27.6 | +0.51 / +1.87 | FAIL — replay worst day -4.2R vs -3.4R (>10% worse) |
| WB2 | V27 close >= VWAP + 0.5 SD at signal (new sensor) | 39 | +0.099 | +0.033 | -3.2 | 806 | -0.050 | -0.060 | -7.6 | +0.68 / +2.59 | PASS |
|  | S1 close within 0.5 ATR of HOD (new sensor) | 72 | -0.011 | -0.092 | -4.2 | 1468 | -0.026 | -0.041 | -7.7 | -0.14 / +2.03 | FAIL — replay w/o best day -0.092 vs -0.067; replay worst day -4.2R vs -3.4R (>10% worse) |
|  | S2 gap >= -2% (intake) | 50 | +0.052 | +0.004 | -2.5 | 1195 | -0.051 | -0.066 | -7.2 | +0.49 / +2.17 | PASS |
|  | S3 volumeRatio >= 0.8 (new sensor) | 60 | +0.013 | -0.082 | -3.2 | 1180 | -0.060 | -0.070 | -7.5 | +0.24 / +2.26 | PASS |
|  | C1 start 11:00 + z5 >= 0.5 | 37 | +0.123 | +0.072 | -2.1 | 758 | -0.020 | -0.061 | -6.2 | +0.77 / +1.96 | PASS |
|  | C2 C1 + ADV >= $150M | 37 | +0.123 | +0.072 | -2.1 | 593 | -0.015 | -0.052 | -6.2 | +0.77 / +2.21 | PASS |
|  | C3 C2 + HOD <= 0.5 ATR | 37 | +0.123 | +0.072 | -2.1 | 527 | -0.037 | -0.044 | -6.2 | +0.77 / +2.52 | PASS |
|  | C4 C3 + target 0.6R | 37 | +0.091 | +0.049 | -2.1 | 530 | -0.085 | -0.093 | -6.2 | +0.56 / +2.00 | PASS |
|  | C5 C2 + refire off | 34 | +0.114 | +0.051 | -2.1 | 554 | -0.034 | -0.079 | -6.2 | +0.65 / +2.00 | PASS |
|  | C6 C3 + band guard off | 38 | +0.146 | +0.073 | -2.1 | 1279 | -0.035 | -0.052 | -16.7 | +0.93 / +1.50 | PASS |
|  | C7 C1 + HOD <= 0.5 ATR | 37 | +0.123 | +0.072 | -2.1 | 666 | -0.039 | -0.045 | -6.2 | +0.77 / +2.48 | PASS |
|  | C8 C3 + gap >= -2% | 21 | +0.220 | +0.492 | +0.2 | 291 | -0.026 | -0.036 | -5.2 | +0.61 / +2.62 | PASS |
|  | C9 C3 + skip SPY > +0.30% since 09:50 | 10 | -0.002 | -0.112 | -1.0 | 351 | -0.014 | -0.025 | -6.2 | +0.03 / +2.79 | FAIL — replay w/o best day -0.112 vs -0.067 |
|  | C10 C3 + volumeRatio >= 0.8 | 28 | +0.103 | -0.022 | -1.0 | 367 | -0.036 | -0.048 | -5.2 | +0.42 / +2.57 | PASS |
|  | C11 start 11:00 + ADV >= $150M + HOD <= 0.5 ATR (no z5) | 69 | +0.005 | -0.075 | -4.2 | 1057 | -0.037 | -0.052 | -8.1 | +0.16 / +2.47 | FAIL — replay worst day -4.2R vs -3.4R (>10% worse) |
|  | D1 C2 + gap <= +5% | 36 | +0.124 | +0.072 | -2.1 | 575 | -0.000 | -0.037 | -6.2 | +0.75 / +2.36 | PASS |
| WB3 | D2 C2 + gap <= +2% | 28 | +0.168 | +0.072 | -2.1 | 512 | +0.018 | -0.022 | -6.2 | +0.80 / +2.47 | PASS |
|  | D3 C2 + max hold 120 min | 37 | +0.164 | +0.147 | -1.5 | 597 | -0.031 | -0.069 | -6.2 | +0.96 / +2.03 | PASS |
|  | D4 C2 + latch off (tool) | 37 | +0.123 | +0.072 | -2.1 | 614 | -0.026 | -0.063 | -10.4 | +0.77 / +2.10 | PASS |
|  | TB-C1 C1 in testing book | 33 | +0.062 | -0.029 | -2.1 | 679 | -0.029 | -0.072 | -13.5 | +0.36 / +1.88 | FAIL vs T0 — 2y worst day -13.5R vs -10.3R (>10% worse) |
|  | TB-C2 C2 in testing book | 33 | +0.062 | -0.029 | -2.1 | 534 | -0.032 | -0.068 | -11.4 | +0.36 / +2.11 | FAIL vs T0 — 2y worst day -11.4R vs -10.3R (>10% worse) |
|  | TB-D1 D1 in testing book | 32 | +0.061 | -0.029 | -2.1 | 521 | -0.022 | -0.059 | -11.4 | +0.34 / +2.20 | FAIL vs T0 — 2y worst day -11.4R vs -10.3R (>10% worse) |
|  | TB-D2 D2 in testing book | 24 | +0.092 | -0.029 | -2.1 | 466 | -0.006 | -0.046 | -11.4 | +0.38 / +2.32 | FAIL vs T0 — 2y worst day -11.4R vs -10.3R (>10% worse) |
|  | E1 D2 + skip SPY > +1.5% since 09:50 | 28 | +0.168 | +0.072 | -2.1 | 468 | -0.024 | -0.032 | -6.2 | +0.80 / +2.72 | PASS |
|  | TB-E1 E1 in testing book | 24 | +0.092 | -0.029 | -2.1 | 422 | -0.041 | -0.051 | -8.3 | +0.38 / +2.54 | FAIL vs T0 — 2y avg R -0.041 < -0.024 |

| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |
|---|---|---|---|
| PARENT | -0.148 (618) | -0.053 (1034) | -0.008 (92) |
| T0 parent, testing book | +0.020 (721) | -0.056 (984) | -0.036 (84) |
| V01 ADV >= $150M (P2) | -0.115 (488) | -0.028 (808) | +0.130 (70) |
| V02 price >= $10 (P3) | -0.148 (583) | -0.057 (1020) | -0.027 (84) |
| V03 window end 15:00->14:00 (P6) | -0.186 (326) | -0.079 (482) | -0.081 (43) |
| V04 window start 09:50->11:00 (P6/P7) | -0.013 (676) | -0.075 (974) | +0.039 (95) |
| V05 refire off (P8) | -0.137 (544) | -0.056 (867) | +0.013 (76) |
| V06 refire cooldown 1->6 (P8) | -0.140 (567) | -0.053 (917) | +0.015 (81) |
| V07 fromOpen > 3 -> > 4 (P10) | -0.226 (301) | -0.056 (492) | +0.157 (41) |
| V08 fromOpen > 3 -> > 2.5 (P10) | -0.165 (941) | -0.077 (1494) | -0.048 (129) |
| V09 fromOpen <= 8 cap (P10) | -0.144 (591) | -0.050 (1010) | -0.021 (90) |
| V10 RSI(14) >= 65 (P11) | -0.138 (342) | -0.024 (599) | -0.052 (50) |
| V11 RSI(14) >= 55 (P11) | -0.127 (990) | -0.038 (1532) | -0.052 (140) |
| V12 band 2 SD -> 2.5 SD (P12) | -0.121 (740) | -0.044 (1136) | +0.040 (115) |
| V13 band 2 SD -> 1.5 SD (P12) | -0.165 (526) | -0.073 (955) | +0.020 (86) |
| V14 band guard off (P12) | -0.088 (999) | -0.031 (1615) | -0.092 (147) |
| V15 latch -2R off (P16, tool) | +0.008 (895) | -0.052 (1116) | +0.012 (99) |
| V16 1R 0.25 -> 0.30 ATR (P20) | -0.150 (617) | -0.029 (1064) | +0.018 (90) |
| V17 cost/R <= 0.15 (P20/intake) | -0.107 (512) | -0.052 (929) | -0.036 (84) |
| V18 stop 1.0 -> 1.25R (P23) | -0.167 (624) | -0.041 (1073) | -0.026 (93) |
| V19 target 1.0 -> 0.8R (P24) | -0.130 (621) | -0.053 (1042) | -0.047 (94) |
| V20 target 1.0 -> 0.6R (P24) | -0.130 (633) | -0.052 (1071) | +0.070 (95) |
| V21 BE stop after +0.5R (P23 move) | -0.120 (625) | -0.079 (1038) | +0.068 (95) |
| V22 max hold 60 min (P26) | -0.124 (625) | -0.059 (1029) | +0.019 (94) |
| V23 max hold 120 min (P26) | -0.152 (621) | -0.059 (1040) | +0.016 (92) |
| V24 gate: skip SPY > +0.30% since 09:50 (new) | -0.155 (391) | -0.029 (768) | +0.066 (67) |
| V25 gate: skip SPY above 09:30-09:50 high (new) | -0.143 (281) | -0.007 (619) | -0.017 (54) |
| V26 price >= VWAP at signal (new sensor) | -0.159 (543) | -0.038 (889) | +0.013 (79) |
| V27 close >= VWAP + 0.5 SD at signal (new sensor) | -0.106 (322) | -0.020 (441) | +0.048 (43) |
| S1 close within 0.5 ATR of HOD (new sensor) | -0.061 (509) | -0.016 (892) | +0.090 (67) |
| S2 gap >= -2% (intake) | -0.106 (366) | -0.037 (771) | +0.123 (58) |
| S3 volumeRatio >= 0.8 (new sensor) | -0.110 (402) | -0.042 (716) | +0.058 (62) |
| C1 start 11:00 + z5 >= 0.5 | -0.016 (320) | -0.039 (394) | +0.122 (44) |
| C2 C1 + ADV >= $150M | -0.037 (252) | -0.012 (308) | +0.120 (33) |
| C3 C2 + HOD <= 0.5 ATR | -0.112 (200) | -0.012 (298) | +0.234 (29) |
| C4 C3 + target 0.6R | -0.158 (200) | -0.066 (301) | +0.223 (29) |
| C5 C2 + refire off | -0.039 (235) | -0.038 (289) | +0.052 (30) |
| C6 C3 + band guard off | -0.054 (482) | -0.043 (715) | +0.148 (82) |
| C7 C1 + HOD <= 0.5 ATR | -0.090 (251) | -0.033 (376) | +0.236 (39) |
| C8 C3 + gap >= -2% | -0.169 (98) | +0.013 (180) | +0.516 (13) |
| C9 C3 + skip SPY > +0.30% since 09:50 | -0.200 (125) | +0.053 (206) | +0.446 (20) |
| C10 C3 + volumeRatio >= 0.8 | -0.131 (140) | -0.001 (209) | +0.304 (18) |
| C11 start 11:00 + ADV >= $150M + HOD <= 0.5 ATR (no z5) | -0.102 (346) | -0.024 (661) | +0.251 (50) |
| D1 C2 + gap <= +5% | -0.023 (247) | -0.002 (297) | +0.199 (31) |
| D2 C2 + gap <= +2% | -0.001 (223) | +0.023 (263) | +0.127 (26) |
| D3 C2 + max hold 120 min | -0.044 (252) | -0.045 (312) | +0.194 (33) |
| D4 C2 + latch off (tool) | -0.056 (261) | -0.017 (320) | +0.120 (33) |
| TB-C1 C1 in testing book | -0.028 (284) | -0.039 (358) | +0.058 (37) |
| TB-C2 C2 in testing book | -0.064 (228) | -0.013 (279) | +0.045 (27) |
| TB-D1 D1 in testing book | -0.050 (223) | -0.014 (273) | +0.136 (25) |
| TB-D2 D2 in testing book | -0.032 (202) | +0.009 (243) | +0.073 (21) |
| E1 D2 + skip SPY > +1.5% since 09:50 | -0.115 (179) | +0.023 (263) | +0.127 (26) |
| TB-E1 E1 in testing book | -0.132 (158) | +0.009 (243) | +0.073 (21) |

| config | test | win % | avg win | avg loss | median hold (min) | stop / target / time share | up-day avg R (n) | flat (n) | down (n) |
|---|---|---|---|---|---|---|---|---|---|
| PARENT | replay | 56% | +0.497 | -0.639 | 82 | 18% / 17% / 65% | +0.027 (39) | -0.125 (35) | +0.304 (10) |
| PARENT | 2y | 46% | +0.680 | -0.748 | 75 | 30% / 24% / 47% | -0.206 (613) | -0.060 (681) | +0.045 (450) |
| T0 parent, testing book | replay | 53% | +0.466 | -0.589 | 80 | 16% / 15% / 69% | -0.005 (35) | -0.114 (37) | +0.227 (9) |
| T0 parent, testing book | 2y | 50% | +0.714 | -0.749 | 70 | 29% / 28% / 43% | -0.059 (761) | -0.028 (629) | +0.048 (399) |
| V01 ADV >= $150M (P2) | replay | 56% | +0.497 | -0.639 | 82 | 18% / 17% / 65% | +0.027 (39) | -0.125 (35) | +0.304 (10) |
| V01 ADV >= $150M (P2) | 2y | 48% | +0.690 | -0.733 | 75 | 28% / 25% / 47% | -0.209 (505) | +0.011 (522) | +0.090 (339) |
| V02 price >= $10 (P3) | replay | 54% | +0.479 | -0.639 | 82 | 19% / 15% / 66% | -0.013 (37) | -0.135 (34) | +0.227 (9) |
| V02 price >= $10 (P3) | 2y | 46% | +0.677 | -0.741 | 75 | 30% / 23% / 47% | -0.211 (596) | -0.060 (670) | +0.045 (421) |
| V03 window end 15:00->14:00 (P6) | replay | 47% | +0.551 | -0.720 | 120 | 24% / 18% / 58% | +0.011 (13) | -0.363 (20) | +0.530 (5) |
| V03 window end 15:00->14:00 (P6) | 2y | 46% | +0.776 | -0.872 | 96 | 40% / 30% / 30% | -0.263 (324) | -0.059 (332) | +0.012 (195) |
| V04 window start 09:50->11:00 (P6/P7) | replay | 57% | +0.500 | -0.632 | 80 | 17% / 17% / 65% | +0.057 (38) | -0.140 (34) | +0.384 (9) |
| V04 window start 09:50->11:00 (P6/P7) | 2y | 48% | +0.693 | -0.736 | 70 | 28% / 26% / 47% | -0.071 (664) | -0.075 (639) | +0.038 (442) |
| V05 refire off (P8) | replay | 57% | +0.501 | -0.629 | 82 | 17% / 17% / 66% | +0.113 (33) | -0.163 (30) | +0.335 (7) |
| V05 refire off (P8) | 2y | 47% | +0.691 | -0.761 | 72 | 30% / 24% / 45% | -0.206 (540) | -0.044 (574) | +0.040 (373) |
| V06 refire cooldown 1->6 (P8) | replay | 57% | +0.513 | -0.665 | 82 | 19% / 18% / 62% | +0.076 (34) | -0.146 (30) | +0.274 (8) |
| V06 refire cooldown 1->6 (P8) | 2y | 47% | +0.688 | -0.755 | 73 | 30% / 24% / 46% | -0.206 (561) | -0.044 (599) | +0.039 (405) |
| V07 fromOpen > 3 -> > 4 (P10) | replay | 60% | +0.540 | -0.496 | 75 | 9% / 17% / 74% | +0.237 (16) | -0.046 (14) | +0.252 (5) |
| V07 fromOpen > 3 -> > 4 (P10) | 2y | 45% | +0.702 | -0.757 | 68 | 32% / 25% / 44% | -0.194 (309) | -0.070 (308) | -0.035 (217) |
| V08 fromOpen > 3 -> > 2.5 (P10) | replay | 56% | +0.489 | -0.639 | 84 | 18% / 16% / 66% | +0.029 (40) | -0.125 (35) | +0.304 (10) |
| V08 fromOpen > 3 -> > 2.5 (P10) | 2y | 45% | +0.680 | -0.761 | 75 | 31% / 23% / 46% | -0.196 (923) | -0.071 (1063) | -0.035 (578) |
| V09 fromOpen <= 8 cap (P10) | replay | 57% | +0.504 | -0.617 | 84 | 16% / 17% / 67% | +0.055 (38) | -0.107 (33) | +0.304 (10) |
| V09 fromOpen <= 8 cap (P10) | 2y | 47% | +0.673 | -0.741 | 75 | 29% / 23% / 48% | -0.193 (590) | -0.059 (662) | +0.035 (439) |
| V10 RSI(14) >= 65 (P11) | replay | 52% | +0.450 | -0.602 | 84 | 17% / 12% / 71% | -0.070 (25) | -0.085 (21) | +0.103 (6) |
| V10 RSI(14) >= 65 (P11) | 2y | 47% | +0.682 | -0.734 | 71 | 28% / 24% / 48% | -0.148 (333) | -0.065 (392) | +0.039 (266) |
| V11 RSI(14) >= 55 (P11) | replay | 53% | +0.518 | -0.641 | 80 | 19% / 17% / 64% | +0.051 (40) | -0.154 (48) | +0.196 (11) |
| V11 RSI(14) >= 55 (P11) | 2y | 47% | +0.705 | -0.764 | 75 | 30% / 26% / 44% | -0.200 (982) | -0.031 (1072) | +0.061 (608) |
| V12 band 2 SD -> 2.5 SD (P12) | replay | 56% | +0.508 | -0.639 | 80 | 18% / 18% / 65% | +0.052 (40) | -0.125 (35) | +0.304 (10) |
| V12 band 2 SD -> 2.5 SD (P12) | 2y | 48% | +0.718 | -0.786 | 70 | 31% / 27% / 41% | -0.209 (768) | -0.007 (777) | +0.070 (446) |
| V13 band 2 SD -> 1.5 SD (P12) | replay | 56% | +0.478 | -0.584 | 84 | 15% / 15% / 69% | +0.058 (32) | -0.112 (31) | +0.227 (9) |
| V13 band 2 SD -> 1.5 SD (P12) | 2y | 46% | +0.656 | -0.729 | 75 | 29% / 21% / 50% | -0.215 (535) | -0.084 (620) | +0.031 (412) |
| V14 band guard off (P12) | replay | 57% | +0.517 | -0.639 | 84 | 17% / 19% / 64% | +0.074 (41) | -0.125 (35) | +0.302 (10) |
| V14 band guard off (P12) | 2y | 48% | +0.773 | -0.816 | 71 | 33% / 31% / 35% | -0.249 (1029) | +0.013 (1072) | +0.137 (660) |
| V15 latch -2R off (P16, tool) | replay | 53% | +0.497 | -0.594 | 80 | 17% / 16% / 67% | +0.027 (39) | -0.142 (40) | +0.304 (10) |
| V15 latch -2R off (P16, tool) | 2y | 50% | +0.728 | -0.764 | 65 | 29% / 29% / 42% | -0.032 (909) | -0.050 (713) | +0.030 (488) |
| V16 1R 0.25 -> 0.30 ATR (P20) | replay | 54% | +0.430 | -0.479 | 85 | 8% / 11% / 81% | +0.046 (39) | -0.066 (40) | +0.185 (10) |
| V16 1R 0.25 -> 0.30 ATR (P20) | 2y | 47% | +0.591 | -0.651 | 81 | 23% / 18% / 59% | -0.196 (625) | -0.037 (686) | +0.056 (460) |
| V17 cost/R <= 0.15 (P20/intake) | replay | 56% | +0.466 | -0.629 | 84 | 17% / 16% / 68% | -0.005 (35) | -0.098 (33) | +0.227 (9) |
| V17 cost/R <= 0.15 (P20/intake) | 2y | 47% | +0.670 | -0.730 | 75 | 29% / 23% / 48% | -0.208 (539) | -0.036 (599) | +0.069 (387) |
| V18 stop 1.0 -> 1.25R (P23) | replay | 54% | +0.508 | -0.575 | 84 | 6% / 17% / 78% | +0.052 (39) | -0.106 (40) | +0.304 (10) |
| V18 stop 1.0 -> 1.25R (P23) | 2y | 48% | +0.673 | -0.793 | 80 | 21% / 24% / 55% | -0.223 (632) | -0.041 (686) | +0.039 (472) |
| V19 target 1.0 -> 0.8R (P24) | replay | 56% | +0.440 | -0.639 | 80 | 18% / 20% / 62% | -0.002 (39) | -0.146 (35) | +0.224 (10) |
| V19 target 1.0 -> 0.8R (P24) | 2y | 49% | +0.621 | -0.756 | 65 | 29% / 32% / 39% | -0.181 (618) | -0.057 (684) | +0.022 (455) |
| V20 target 1.0 -> 0.6R (P24) | replay | 61% | +0.404 | -0.634 | 75 | 17% / 32% / 51% | -0.031 (39) | -0.058 (35) | +0.291 (10) |
| V20 target 1.0 -> 0.6R (P24) | 2y | 54% | +0.517 | -0.764 | 55 | 26% / 44% / 30% | -0.176 (635) | -0.031 (702) | +0.004 (462) |
| V21 BE stop after +0.5R (P23 move) | replay | 51% | +0.480 | -0.504 | 78 | 27% / 15% / 57% | -0.016 (39) | -0.093 (35) | +0.385 (10) |
| V21 BE stop after +0.5R (P23 move) | 2y | 37% | +0.695 | -0.547 | 63 | 45% / 20% / 35% | -0.188 (627) | -0.067 (676) | +0.028 (455) |
| V22 max hold 60 min (P26) | replay | 43% | +0.442 | -0.381 | 60 | 6% / 6% / 89% | -0.063 (39) | -0.041 (40) | +0.145 (10) |
| V22 max hold 60 min (P26) | 2y | 47% | +0.518 | -0.611 | 60 | 19% / 14% / 67% | -0.132 (636) | -0.048 (689) | -0.047 (423) |
| V23 max hold 120 min (P26) | replay | 54% | +0.492 | -0.540 | 82 | 15% / 15% / 69% | +0.023 (39) | -0.073 (35) | +0.277 (10) |
| V23 max hold 120 min (P26) | 2y | 46% | +0.628 | -0.702 | 75 | 27% / 20% / 53% | -0.189 (618) | -0.072 (685) | +0.024 (450) |
| V24 gate: skip SPY > +0.30% since 09:50 (new) | replay | 47% | +0.624 | -0.619 | 95 | 19% / 21% / 60% |  (0) | -0.145 (33) | +0.304 (10) |
| V24 gate: skip SPY > +0.30% since 09:50 (new) | 2y | 47% | +0.686 | -0.742 | 76 | 29% / 24% / 47% | -0.239 (192) | -0.088 (585) | +0.043 (449) |
| V25 gate: skip SPY above 09:30-09:50 high (new) | replay | 42% | +0.622 | -0.619 | 95 | 20% / 20% / 60% |  (0) | -0.224 (30) | +0.304 (10) |
| V25 gate: skip SPY above 09:30-09:50 high (new) | 2y | 48% | +0.693 | -0.742 | 75 | 28% / 25% / 47% | -0.321 (73) | -0.088 (451) | +0.042 (430) |
| V26 price >= VWAP at signal (new sensor) | replay | 55% | +0.532 | -0.642 | 75 | 19% / 19% / 62% | +0.007 (38) | -0.096 (27) | +0.327 (9) |
| V26 price >= VWAP at signal (new sensor) | 2y | 47% | +0.678 | -0.744 | 75 | 29% / 24% / 47% | -0.207 (539) | -0.045 (592) | +0.053 (380) |
| V27 close >= VWAP + 0.5 SD at signal (new sensor) | replay | 69% | +0.455 | -0.703 | 75 | 18% / 18% / 64% | +0.121 (27) | -0.038 (11) | +0.992 (1) |
| V27 close >= VWAP + 0.5 SD at signal (new sensor) | 2y | 48% | +0.736 | -0.788 | 66 | 32% / 29% / 39% | -0.186 (324) | -0.000 (292) | +0.103 (190) |
| S1 close within 0.5 ATR of HOD (new sensor) | replay | 56% | +0.490 | -0.636 | 78 | 19% / 17% / 64% | +0.007 (38) | -0.081 (26) | +0.133 (8) |
| S1 close within 0.5 ATR of HOD (new sensor) | 2y | 50% | +0.657 | -0.699 | 77 | 25% / 24% / 52% | -0.093 (535) | -0.035 (572) | +0.086 (361) |
| S2 gap >= -2% (intake) | replay | 62% | +0.449 | -0.595 | 78 | 16% / 14% / 70% | +0.010 (25) | +0.075 (21) | +0.196 (4) |
| S2 gap >= -2% (intake) | 2y | 48% | +0.645 | -0.692 | 73 | 25% / 22% / 53% | -0.119 (412) | -0.070 (469) | +0.068 (314) |
| S3 volumeRatio >= 0.8 (new sensor) | replay | 53% | +0.514 | -0.561 | 80 | 15% / 17% / 68% | +0.047 (28) | -0.119 (27) | +0.534 (5) |
| S3 volumeRatio >= 0.8 (new sensor) | 2y | 48% | +0.665 | -0.722 | 70 | 27% / 23% / 50% | -0.202 (404) | -0.051 (447) | +0.102 (329) |
| C1 start 11:00 + z5 >= 0.5 | replay | 70% | +0.458 | -0.667 | 75 | 16% / 19% / 65% | +0.168 (26) | -0.081 (10) | +0.992 (1) |
| C1 start 11:00 + z5 >= 0.5 | 2y | 50% | +0.736 | -0.773 | 65 | 30% / 30% / 40% | -0.096 (320) | -0.013 (260) | +0.104 (178) |
| C2 C1 + ADV >= $150M | replay | 70% | +0.458 | -0.667 | 75 | 16% / 19% / 65% | +0.168 (26) | -0.081 (10) | +0.992 (1) |
| C2 C1 + ADV >= $150M | 2y | 50% | +0.736 | -0.759 | 65 | 30% / 30% / 40% | -0.112 (256) | +0.007 (197) | +0.131 (140) |
| C3 C2 + HOD <= 0.5 ATR | replay | 70% | +0.458 | -0.667 | 75 | 16% / 19% / 65% | +0.168 (26) | -0.081 (10) | +0.992 (1) |
| C3 C2 + HOD <= 0.5 ATR | 2y | 49% | +0.700 | -0.738 | 73 | 29% / 27% / 45% | -0.220 (205) | +0.038 (188) | +0.139 (134) |
| C4 C3 + target 0.6R | replay | 76% | +0.356 | -0.732 | 75 | 16% / 30% / 54% | +0.095 (26) | +0.033 (10) | +0.592 (1) |
| C4 C3 + target 0.6R | 2y | 54% | +0.507 | -0.768 | 56 | 27% / 42% / 30% | -0.264 (205) | +0.013 (191) | +0.050 (134) |
| C5 C2 + refire off | replay | 68% | +0.488 | -0.667 | 75 | 18% / 21% / 62% | +0.173 (24) | -0.142 (9) | +0.992 (1) |
| C5 C2 + refire off | 2y | 49% | +0.731 | -0.771 | 67 | 31% / 29% / 40% | -0.116 (243) | -0.015 (184) | +0.098 (127) |
| C6 C3 + band guard off | replay | 71% | +0.477 | -0.667 | 75 | 16% / 21% / 63% | +0.199 (27) | -0.081 (10) | +0.992 (1) |
| C6 C3 + band guard off | 2y | 49% | +0.775 | -0.799 | 79 | 33% / 32% / 36% | -0.216 (607) | +0.091 (414) | +0.189 (258) |
| C7 C1 + HOD <= 0.5 ATR | replay | 70% | +0.458 | -0.667 | 75 | 16% / 19% / 65% | +0.168 (26) | -0.081 (10) | +0.992 (1) |
| C7 C1 + HOD <= 0.5 ATR | 2y | 49% | +0.696 | -0.747 | 70 | 29% / 26% / 45% | -0.210 (254) | +0.018 (246) | +0.139 (166) |
| C8 C3 + gap >= -2% | replay | 76% | +0.380 | -0.291 | 75 | 5% / 14% / 81% | +0.115 (16) | +0.554 (5) |  (0) |
| C8 C3 + gap >= -2% | 2y | 47% | +0.654 | -0.630 | 70 | 22% / 22% / 56% | -0.210 (124) | +0.007 (101) | +0.271 (66) |
| C9 C3 + skip SPY > +0.30% since 09:50 | replay | 50% | +0.763 | -0.766 | 68 | 30% / 30% / 40% |  (0) | -0.112 (9) | +0.992 (1) |
| C9 C3 + skip SPY > +0.30% since 09:50 | 2y | 51% | +0.720 | -0.778 | 70 | 30% / 29% / 41% | -0.474 (57) | +0.021 (160) | +0.139 (134) |
| C10 C3 + volumeRatio >= 0.8 | replay | 68% | +0.428 | -0.583 | 75 | 14% / 14% / 71% | +0.112 (19) | -0.031 (8) | +0.992 (1) |
| C10 C3 + volumeRatio >= 0.8 | 2y | 48% | +0.669 | -0.700 | 75 | 26% / 24% / 49% | -0.271 (151) | +0.066 (126) | +0.216 (90) |
| C11 start 11:00 + ADV >= $150M + HOD <= 0.5 ATR (no z5) | replay | 57% | +0.492 | -0.628 | 77 | 19% / 17% / 64% | +0.037 (37) | -0.100 (25) | +0.211 (7) |
| C11 start 11:00 + ADV >= $150M + HOD <= 0.5 ATR (no z5) | 2y | 49% | +0.625 | -0.668 | 80 | 23% / 21% / 56% | -0.150 (381) | -0.022 (394) | +0.096 (282) |
| D1 C2 + gap <= +5% | replay | 69% | +0.472 | -0.667 | 75 | 17% / 19% / 64% | +0.171 (25) | -0.081 (10) | +0.992 (1) |
| D1 C2 + gap <= +5% | 2y | 51% | +0.737 | -0.755 | 68 | 29% / 31% / 41% | -0.107 (251) | +0.032 (190) | +0.155 (134) |
| D2 C2 + gap <= +2% | replay | 68% | +0.568 | -0.676 | 75 | 18% / 25% / 57% | +0.266 (17) | -0.081 (10) | +0.992 (1) |
| D2 C2 + gap <= +2% | 2y | 52% | +0.757 | -0.775 | 69 | 29% / 33% / 38% | -0.077 (218) | +0.059 (173) | +0.132 (121) |
| D3 C2 + max hold 120 min | replay | 70% | +0.450 | -0.511 | 75 | 11% / 16% / 73% | +0.154 (26) | +0.106 (10) | +0.992 (1) |
| D3 C2 + max hold 120 min | 2y | 49% | +0.674 | -0.697 | 66 | 27% / 24% / 49% | -0.096 (259) | -0.037 (198) | +0.097 (140) |
| D4 C2 + latch off (tool) | replay | 70% | +0.458 | -0.667 | 75 | 16% / 19% / 65% | +0.168 (26) | -0.081 (10) | +0.992 (1) |
| D4 C2 + latch off (tool) | 2y | 49% | +0.733 | -0.761 | 66 | 30% / 29% / 40% | -0.138 (272) | +0.021 (201) | +0.123 (141) |
| TB-C1 C1 in testing book | replay | 70% | +0.406 | -0.729 | 75 | 18% / 15% / 67% | +0.117 (24) | -0.084 (9) |  (0) |
| TB-C1 C1 in testing book | 2y | 49% | +0.723 | -0.757 | 66 | 30% / 28% / 42% | -0.125 (301) | +0.014 (222) | +0.093 (156) |
| TB-C2 C2 in testing book | replay | 70% | +0.406 | -0.729 | 75 | 18% / 15% / 67% | +0.117 (24) | -0.084 (9) |  (0) |
| TB-C2 C2 in testing book | 2y | 49% | +0.722 | -0.747 | 70 | 30% / 28% / 42% | -0.170 (244) | +0.051 (168) | +0.130 (122) |
| TB-D1 D1 in testing book | replay | 69% | +0.420 | -0.729 | 75 | 19% / 16% / 66% | +0.117 (23) | -0.084 (9) |  (0) |
| TB-D1 D1 in testing book | 2y | 49% | +0.720 | -0.745 | 70 | 30% / 28% / 42% | -0.166 (239) | +0.058 (166) | +0.157 (116) |
| TB-D2 D2 in testing book | replay | 67% | +0.515 | -0.754 | 75 | 21% / 21% / 58% | +0.197 (15) | -0.084 (9) |  (0) |
| TB-D2 D2 in testing book | 2y | 50% | +0.742 | -0.767 | 70 | 30% / 30% / 39% | -0.141 (208) | +0.079 (153) | +0.137 (105) |
| E1 D2 + skip SPY > +1.5% since 09:50 | replay | 68% | +0.568 | -0.676 | 75 | 18% / 25% / 57% | +0.266 (17) | -0.081 (10) | +0.992 (1) |
| E1 D2 + skip SPY > +1.5% since 09:50 | 2y | 50% | +0.726 | -0.761 | 74 | 30% / 29% / 41% | -0.214 (174) | +0.059 (173) | +0.132 (121) |
| TB-E1 E1 in testing book | replay | 67% | +0.515 | -0.754 | 75 | 21% / 21% / 58% | +0.197 (15) | -0.084 (9) |  (0) |
| TB-E1 E1 in testing book | 2y | 49% | +0.708 | -0.748 | 76 | 30% / 27% / 43% | -0.266 (164) | +0.079 (153) | +0.137 (105) |

## Ready to deploy after close (NOT applied — the main session applies it after hours under RULES.md 5)
Deploy **WB3 only** (it contains WB1 and WB2; running them side by side would be near-twins). The parent stays in the
Graveyard, unchanged (Workbench rule 1). Destination: **Testing A** (`config/account_testing2.yaml`) — a testing account
(not Graveyard, not On Deck); its book (no −2R latch, 50 lots per setup, `max_stop_cost_r: 0.15`) is the one scored as
TB-D2 above; it holds no NS2 / RW6 relative (Testing E runs the windowed twin `RW6G1-ns2-up3-vwap2sd-short`, Testing F runs
`NM-RWN4-ns2-spyup05-notfri-short`, Testing D already has two Workbench copies). If another Workbench job claimed the FIRST
slot in Testing A tonight (orb20_a WB3), put this one right after it (the main session decides the order between copies).
1. Module: copy `research/workbench/RW6G1-ns2-up3-vwap2sd-short-FD/modules/RW6G1-ns2-up3-vwap2sd-short-FD-WB3.py`
   to `research/bdi/fullday/RW6G1-ns2-up3-vwap2sd-short-FD-WB3.py`.
2. `config/account_testing2.yaml`, under `strategies:` add
   ```yaml
   RW6G1-ns2-up3-vwap2sd-short-FD-WB3:
     # Workbench copy of RW6G1-ns2-up3-vwap2sd-short-FD (Graveyard), Mechanic 2026-11-16: entries from 11:00 + close >= VWAP
     # + 0.5 SD + ADV >= $150M + gap <= +2%; research/workbench/RW6G1-ns2-up3-vwap2sd-short-FD/RESULTS.md. From session 2026-11-17.
     enabled: true
     refire: true
     refire_cooldown: 1
     type: lab
     module: research/bdi/fullday/RW6G1-ns2-up3-vwap2sd-short-FD-WB3.py
     min_adv: 150000000
     window: [1100, 1500]
     scale_out_r: null
     tags: [workbench, "parent:RW6G1-ns2-up3-vwap2sd-short-FD"]
   ```
   and put `RW6G1-ns2-up3-vwap2sd-short-FD-WB3` FIRST in `live.setup_order` (rule 5).
3. `config/setup_names.yaml`: `RW6G1-ns2-up3-vwap2sd-short-FD-WB3: {name: "Big Gainer Fade, VWAP Band Guard (all day) — WB3: from 11:00, stretched reclaim, liquid, no gap-up runners", side: short, what: "11:00-15:00: a stock up over 3% from the open (opening gap no more than +2%, ADV >= $150M) closes back above its 5-min SMA50 with RSI(14) >= 60 while at least +0.5 SD above VWAP; short it unless a close above the +2 SD VWAP band is unresolved; target / stop 1R (0.25 ATR), flat 15:55."}`
4. `research/ledger.jsonl`: id `2026-11-16-wb-rw6g1-wb3`, effective 2026-11-17, title "Workbench copy
   RW6G1-ns2-up3-vwap2sd-short-FD-WB3 added to Testing A, first in setup_order (Mechanic pass)", patch
   `{"strategies.RW6G1-ns2-up3-vwap2sd-short-FD-WB3 (testing2)": [null, "added, enabled"], "live.setup_order (testing2)": ["...", "WB3 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5"; then `python -m mcf.research.ledger check`.
5. Smoke test (the module needs a `volume` column; without it the band guard and z fail safe: no signal), `python -m
   mcf.report.assignments` (docs/live/assignments.json in the same commit), `pytest -q`, commit, push after 16:05 ET (setup-freeze).
Note: expect about one trade per session (2-year 512 trades over 446 sessions); the record will take weeks to mean much,
and its 2-year number leans on one crash-rebound day (2025-04-07) — review it with the one-big-day column.

Files: DIAGNOSIS.md, variants.jsonl, modules/, *.yaml stubs (no account loads them), code/ (sim3.py bench, band.py,
load.py, go.py, decl6.py, report.py, extras.py, parity.py, cand2y.py, paths2y.py, fetch_replay.py, live.py, liveana.py,
ana2y.py, mkwb.py; run from a scratch dir holding the data files), results_all.csv, extras.csv, component_analysis.txt,
PNGs (engine, worst1-5, best1-5). Educational only — not financial advice.
