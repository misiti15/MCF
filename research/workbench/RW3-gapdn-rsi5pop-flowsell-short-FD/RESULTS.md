# Workbench RESULTS — Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` (Primary, TEAM-6) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16, built 13:10-14:45 ET (market hours: research files only, no config change, no deploy).

## Verdict
| copy | change | replay avg R (parent +0.168) | 2-year avg R (parent −0.030) | w/o best day (replay / 2y; parent +0.067 / −0.036) | worst day (replay / 2y; parent −10.0 / −19.9R) | trades (replay / 2y; parent 210 / 4,927) | verdict |
|---|---|---|---|---|---|---|---|
| `RW3-gapdn-rsi5pop-flowsell-short-FD-WB1` | P6/P7 window starts 10:30 (was 09:50) | **+0.221** | −0.030 (meets) | +0.121 / −0.036 | −9.9 / −20.6 | 210 / 4,701 | PASS (2-year only meets; VALID split worse) |
| `RW3-gapdn-rsi5pop-flowsell-short-FD-WB2` | new gate: skip while SPY > +0.20% since the 09:50 close | **+0.221** | **−0.016** | +0.096 / −0.025 | −9.9 / −19.9 | 163 / 3,732 | PASS |
| `RW3-gapdn-rsi5pop-flowsell-short-FD-WB3` | WB1 + WB2 + daily ATR ≥ 1.6% (1R ≥ 0.40% of price) | **+0.244** | **−0.007** | **+0.114 / −0.016** | **−8.7 / −19.5** | 137 / 3,174 | **PASS — recommended** |

Pass rule (owner 2026-11-16): meets or exceeds the parent's avg R after costs in BOTH identical tests (meets = within
0.01R or ≥ 95%), not worse on avg R w/o best day by > 0.02R or on worst day by > 10%. Parent and copies were scored by the
identical pipeline; the parent's live record is NOT used in the decision (DIAGNOSIS.md uses it for diagnosis only).

## Supervisor sign-off — WB3
- **What changed (3 parts):** (1) Timer: no entries before the 10:30 bar close; (2) new Gate: skip while SPY is up more
  than 0.20% since the 09:50 bar close (owner rule: market state measured after 09:50; module + `context: [spy_fo]`);
  (3) Intake: daily ATR ≥ 1.6% of price (1R ≥ 0.40% of price) so the fixed stop cost is not a large share of R.
  Sensors, stop, target, time exit, refire and sizing are the parent's.
- **Why:** the losses cluster on up-tape sessions (2-year up days −0.255R/trade vs down days +0.137R), in the first
  40 minutes (live 09:50-10:30 −0.57R on 9 trades; replay −0.47R/trade at 10:00-10:30) and on thin-R names (XLI 1R
  0.28% of price, PDBC 0.38-0.43%; 2-year 1R < 0.30% −0.24R/trade). WB3 drops 4 of the 5 worst live trades (XLI, PDBC,
  VG, MMM) and keeps all 5 best (11-05).
- **Overall before → after:** replay +0.168 → **+0.244R** (w/o best day +0.067 → +0.114; worst day −10.0 → −8.7R);
  2-year −0.030 → **−0.007R** (w/o best day −0.036 → −0.016; worst day −19.9 → −19.5R); better than the parent in every
  2-year split (TRAIN −0.074 → −0.057, VALID −0.002 → +0.016, FWD +0.136 → +0.194). Trades −35% (replay) / −36% (2-year).
- **Where it gives a little back:** replay TOTAL R is −1.9R lower (+33.4 vs +35.4R: fewer trades, higher avg); the ATR
  floor alone drops 15 replay trades that averaged +0.53R (it is the 2-year that pays for it: C6 without the floor is
  +0.274 replay / −0.015 2-year); up-tape days that still pass the gate are worse per trade (2-year up-day avg R
  −0.319 vs −0.255, on 594 instead of 1,569 trades) and flat days dip (−0.033 vs +0.014); down days unchanged (+0.137); still big-day dependent in the replay (best day 61% of R vs 65%).
- **Honest status:** the 2-year is still slightly negative after costs (−0.007R/trade); the copy is better than the
  parent, not yet a proven earner over 2 years. Day-paired t vs parent: replay −0.13 (total R about equal), 2-year +2.04
  (+124.7R); neither clears the counted bar 2.76 (45 configurations). The cleaner research copy R2 (WB3 + flat 15:00 instead
  of 15:55) reached **+0.264 replay / +0.003 2-year** (first positive 2-year result) but the live runner has no per-setup
  flatten time (`Signal.exit_by` is backtest-only), so it cannot ship as a config copy — backlog idea (runner hook).
- **In the destination book** (testing accounts: no −2R latch, 50 lots/setup, cost filter CF 0.15) everything scores
  lower (round 6): parent +0.111 / −0.026, WB3 **+0.173 / −0.022** — WB3 still meets or exceeds the parent there, but both
  lose the latch's protection (worst day −31.5R over 2 years for both).

## Rule-change context (owner 2026-11-02)
Live record window 10-12..11-16 holds 13 rule changes (blueprint list): TEAM moves (promotion to Primary 10-15, move-only
10-21), twin/−2R testing latch 10-20, ST-A 10-23, Primary size 10-28, Primary −2R latch 10-29, CF cost filter in Testing
10-30, LR1/LR3/LR5/LR7 and the LR8 cost model 11-12. The replay and the 2-year apply TODAY's Primary rules (−2R latch,
30 lots, LR8 costs) to every session for parent and copies alike, so none of these mix into the comparison.

## Side by side (ALL = whole test; 2-year splits; shape)

Configs: 45; counted bar max(1.5, sqrt(2 ln 45)) = 2.76

| copy | config | test | trades | win % | avg R | avg R w/o best day | total R | worst day | t vs parent (day-paired) | dR vs parent | verdict / why |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | PARENT | replay | 210 | 58.1% | +0.168 | +0.067 | +35.4 | -10.0 | +0.00 | +0.0 | — |
| parent | PARENT | 2y | 4927 | 49.7% | -0.030 | -0.036 | -146.4 | -19.9 | +0.00 | +0.0 |  |
|  | V01 window end 15:00->13:00 (P6) | replay | 174 | 59.8% | +0.209 | +0.091 | +36.3 | -10.0 | +0.17 | +1.0 | PASS |
|  | V01 window end 15:00->13:00 (P6) | 2y | 3767 | 49.5% | -0.038 | -0.045 | -144.7 | -18.8 | +0.04 | +1.7 |  |
| WB1 | V02 window start 09:50->10:30 (P6/P7) | replay | 210 | 61.0% | +0.221 | +0.121 | +46.5 | -9.9 | +1.08 | +11.1 | PASS |
| WB1 | V02 window start 09:50->10:30 (P6/P7) | 2y | 4701 | 49.5% | -0.030 | -0.036 | -141.0 | -20.6 | +0.16 | +5.4 |  |
|  | V03 gap <0 -> <=-1.0% (P12) | replay | 126 | 63.5% | +0.276 | +0.144 | +34.7 | -5.3 | -0.06 | -0.6 | FAIL |
|  | V03 gap <0 -> <=-1.0% (P12) | 2y | 1654 | 48.5% | -0.043 | -0.059 | -71.0 | -18.6 | +0.92 | +75.3 | 2y avg R -0.043 < parent -0.030; 2y w/o best day -0.059 vs -0.036 |
|  | V04 gap <0 -> <=-0.5% (P12) | replay | 168 | 57.1% | +0.190 | +0.069 | +31.9 | -8.0 | -0.54 | -3.5 | FAIL |
|  | V04 gap <0 -> <=-0.5% (P12) | 2y | 2745 | 48.4% | -0.045 | -0.055 | -124.2 | -18.6 | +0.36 | +22.2 | 2y avg R -0.045 < parent -0.030 |
|  | V05 +price at/below VWAP (new sensor) | replay | 117 | 61.5% | +0.250 | +0.094 | +29.2 | -5.3 | -0.38 | -6.1 | FAIL |
|  | V05 +price at/below VWAP (new sensor) | 2y | 2330 | 48.3% | -0.048 | -0.058 | -110.7 | -18.0 | +0.47 | +35.7 | 2y avg R -0.048 < parent -0.030; 2y w/o best day -0.058 vs -0.036 |
| WB2 | V06 +skip SPY >+0.20% since 09:50 (new gate) | replay | 163 | 61.4% | +0.221 | +0.096 | +36.1 | -9.9 | +0.06 | +0.7 | PASS |
| WB2 | V06 +skip SPY >+0.20% since 09:50 (new gate) | 2y | 3732 | 50.2% | -0.016 | -0.025 | -60.7 | -19.9 | +1.68 | +85.7 |  |
|  | V07 max hold 90 min (P26) | replay | 207 | 58.5% | +0.157 | +0.066 | +32.5 | -5.5 | -0.24 | -2.8 | FAIL |
|  | V07 max hold 90 min (P26) | 2y | 5001 | 48.2% | -0.038 | -0.043 | -191.2 | -20.2 | -0.79 | -44.9 | replay avg R +0.157 < parent +0.168 |
|  | V08 max hold 120 min (P26) | replay | 210 | 59.1% | +0.167 | +0.070 | +35.1 | -6.6 | -0.04 | -0.3 | PASS |
|  | V08 max hold 120 min (P26) | 2y | 4952 | 49.3% | -0.028 | -0.033 | -135.9 | -20.4 | +0.24 | +10.4 |  |
|  | V09 BE stop after +0.5R (P23) | replay | 209 | 45.5% | +0.134 | +0.021 | +28.1 | -8.5 | -0.94 | -7.3 | FAIL |
|  | V09 BE stop after +0.5R (P23) | 2y | 5006 | 37.4% | -0.038 | -0.044 | -190.7 | -19.4 | -1.14 | -44.3 | replay avg R +0.134 < parent +0.168; replay w/o best day +0.021 vs +0.067 |
|  | V10 RSI(5) >80 -> >85 (P11) | replay | 157 | 61.8% | +0.241 | +0.159 | +37.9 | -6.3 | +0.17 | +2.5 | PASS |
|  | V10 RSI(5) >80 -> >85 (P11) | 2y | 3702 | 49.6% | -0.038 | -0.043 | -139.1 | -14.4 | +0.15 | +7.3 |  |
|  | V11 buyPressure <-0.35 -> <-0.40 (P10) | replay | 152 | 57.2% | +0.156 | +0.078 | +23.7 | -8.2 | -0.89 | -11.6 | FAIL |
|  | V11 buyPressure <-0.35 -> <-0.40 (P10) | 2y | 3458 | 49.6% | -0.040 | -0.048 | -139.8 | -16.8 | +0.12 | +6.6 | replay avg R +0.156 < parent +0.168; 2y avg R -0.040 < parent -0.030 |
|  | V12 heat <=-20 -> <=-25 (P9) | replay | 112 | 58.9% | +0.144 | +0.023 | +16.1 | -9.1 | -1.07 | -19.3 | FAIL |
|  | V12 heat <=-20 -> <=-25 (P9) | 2y | 2474 | 50.3% | -0.015 | -0.022 | -38.0 | -17.9 | +1.58 | +108.4 | replay avg R +0.144 < parent +0.168; replay w/o best day +0.023 vs +0.067 |
|  | V13 target 1.0 -> 0.8R (P24) | replay | 210 | 61.4% | +0.145 | +0.064 | +30.4 | -9.6 | -0.81 | -5.0 | FAIL |
|  | V13 target 1.0 -> 0.8R (P24) | 2y | 5121 | 53.4% | -0.031 | -0.036 | -157.0 | -19.3 | -0.34 | -10.6 | replay avg R +0.145 < parent +0.168 |
|  | V14 stop 1.0 -> 1.25R (P23) | replay | 228 | 61.0% | +0.189 | +0.101 | +43.2 | -14.0 | +0.61 | +7.8 | FAIL |
|  | V14 stop 1.0 -> 1.25R (P23) | 2y | 5130 | 51.9% | -0.031 | -0.038 | -158.9 | -24.6 | -0.33 | -12.5 | replay worst day -14.0R vs -10.0R (>10% worse); 2y worst day -24.6R vs -19.9R (>10% worse) |
|  | V15 ADV $95M -> $150M (P2) | replay | 129 | 60.5% | +0.205 | +0.051 | +26.4 | -7.0 | -0.98 | -9.0 | FAIL |
|  | V15 ADV $95M -> $150M (P2) | 2y | 3592 | 48.6% | -0.041 | -0.048 | -146.3 | -16.6 | +0.00 | +0.1 | 2y avg R -0.041 < parent -0.030 |
|  | V16 flat 15:55 -> 15:00 (P26) | replay | 210 | 61.4% | +0.190 | +0.089 | +39.9 | -7.6 | +0.58 | +4.6 | PASS |
|  | V16 flat 15:55 -> 15:00 (P26) | 2y | 4925 | 50.5% | -0.022 | -0.028 | -109.7 | -19.9 | +0.78 | +36.7 |  |
|  | V17 refire on, cooldown 6 bars (P8) | replay | 216 | 58.3% | +0.167 | +0.072 | +36.0 | -10.0 | +0.29 | +0.7 | PASS |
|  | V17 refire on, cooldown 6 bars (P8) | 2y | 5067 | 49.6% | -0.029 | -0.036 | -148.0 | -19.9 | -0.11 | -1.7 |  |
|  | V18 per-setup latch -2R -> off (P16) | replay | 233 | 57.9% | +0.162 | +0.071 | +37.8 | -15.3 | +0.25 | +2.4 | FAIL |
|  | V18 per-setup latch -2R -> off (P16) | 2y | 5689 | 49.5% | -0.032 | -0.038 | -182.6 | -38.7 | -0.95 | -36.2 | replay worst day -15.3R vs -10.0R (>10% worse); 2y worst day -38.7R vs -19.9R (>10% worse) |
|  | C1 SPY gate + flat 15:00 | replay | 163 | 63.2% | +0.237 | +0.111 | +38.7 | -7.6 | +0.25 | +3.3 | PASS |
|  | C1 SPY gate + flat 15:00 | 2y | 3730 | 51.4% | -0.009 | -0.016 | -32.5 | -19.9 | +1.78 | +113.9 |  |
|  | C2 C1 + start 10:30 | replay | 154 | 65.6% | +0.287 | +0.153 | +44.3 | -7.5 | +0.58 | +8.9 | PASS |
|  | C2 C1 + start 10:30 | 2y | 3473 | 51.0% | -0.009 | -0.016 | -29.9 | -20.6 | +1.68 | +116.5 |  |
|  | C3 C1 + RSI(5) > 85 | replay | 117 | 65.0% | +0.285 | +0.172 | +33.3 | -4.9 | -0.12 | -2.1 | PASS |
|  | C3 C1 + RSI(5) > 85 | 2y | 2762 | 50.5% | -0.024 | -0.030 | -66.0 | -14.4 | +1.05 | +80.4 |  |
|  | C4 SPY gate + max hold 120 | replay | 163 | 62.0% | +0.227 | +0.108 | +37.0 | -6.6 | +0.13 | +1.7 | PASS |
|  | C4 SPY gate + max hold 120 | 2y | 3772 | 49.9% | -0.019 | -0.026 | -72.1 | -20.4 | +1.17 | +74.3 |  |
|  | C5 C1 + max hold 120 | replay | 163 | 62.0% | +0.231 | +0.108 | +37.6 | -6.6 | +0.16 | +2.2 | PASS |
|  | C5 C1 + max hold 120 | 2y | 3772 | 50.7% | -0.013 | -0.019 | -47.5 | -20.4 | +1.39 | +98.9 |  |
|  | C6 SPY gate + start 10:30 | replay | 154 | 63.6% | +0.274 | +0.141 | +42.2 | -9.9 | +0.50 | +6.8 | PASS |
|  | C6 SPY gate + start 10:30 | 2y | 3478 | 50.0% | -0.015 | -0.023 | -51.9 | -20.6 | +1.63 | +94.5 |  |
|  | C7 C2 + RSI(5) > 85 | replay | 110 | 66.4% | +0.310 | +0.179 | +34.1 | -4.9 | -0.07 | -1.3 | PASS |
|  | C7 C2 + RSI(5) > 85 | 2y | 2545 | 50.4% | -0.021 | -0.029 | -53.9 | -16.3 | +1.16 | +92.5 |  |
|  | S1 SPY gate +0.10% | replay | 146 | 63.0% | +0.245 | +0.106 | +35.7 | -9.9 | +0.03 | +0.4 | PASS |
|  | S1 SPY gate +0.10% | 2y | 3193 | 50.0% | -0.021 | -0.028 | -66.0 | -19.9 | +1.24 | +80.4 |  |
|  | S2 SPY gate +0.30% | replay | 172 | 59.9% | +0.200 | +0.078 | +34.4 | -10.0 | -0.09 | -1.0 | PASS |
|  | S2 SPY gate +0.30% | 2y | 4054 | 49.8% | -0.026 | -0.034 | -105.1 | -19.9 | +0.95 | +41.3 |  |
|  | S3 flat 14:30 | replay | 208 | 58.2% | +0.199 | +0.101 | +41.3 | -9.2 | +0.67 | +6.0 | PASS |
|  | S3 flat 14:30 | 2y | 4928 | 47.7% | -0.032 | -0.038 | -159.5 | -20.6 | -0.25 | -13.1 |  |
|  | R1 C2 + 1R >= 0.30% of price | replay | 150 | 65.3% | +0.284 | +0.150 | +42.6 | -7.5 | +0.48 | +7.2 | PASS |
|  | R1 C2 + 1R >= 0.30% of price | 2y | 3405 | 51.3% | -0.004 | -0.011 | -13.1 | -20.6 | +1.92 | +133.2 |  |
|  | R2 C2 + 1R >= 0.40% of price | replay | 137 | 64.2% | +0.264 | +0.133 | +36.2 | -6.4 | +0.05 | +0.8 | PASS |
|  | R2 C2 + 1R >= 0.40% of price | 2y | 3174 | 51.6% | +0.003 | -0.004 | +9.6 | -19.8 | +2.19 | +156.0 |  |
|  | R3 C2 + heat <= -25 | replay | 81 | 60.5% | +0.242 | +0.086 | +19.6 | -7.2 | -0.74 | -15.8 | PASS |
|  | R3 C2 + heat <= -25 | 2y | 1691 | 51.0% | +0.001 | -0.010 | +1.5 | -18.7 | +1.75 | +147.8 |  |
|  | R4 C2 + max hold 120 | replay | 154 | 64.3% | +0.276 | +0.144 | +42.4 | -6.5 | +0.48 | +7.1 | PASS |
|  | R4 C2 + max hold 120 | 2y | 3511 | 50.8% | -0.013 | -0.020 | -44.1 | -20.6 | +1.38 | +102.3 |  |
|  | R5 C1 + 1R >= 0.30% (start 09:50) | replay | 160 | 63.1% | +0.237 | +0.114 | +37.9 | -7.6 | +0.19 | +2.6 | PASS |
|  | R5 C1 + 1R >= 0.30% (start 09:50) | 2y | 3659 | 51.6% | -0.004 | -0.010 | -12.8 | -19.9 | +2.06 | +133.6 |  |
| WB3 | D1 SPY gate + start 10:30 + 1R >= 0.40% | replay | 137 | 62.0% | +0.244 | +0.114 | +33.4 | -8.7 | -0.13 | -1.9 | PASS |
| WB3 | D1 SPY gate + start 10:30 + 1R >= 0.40% | 2y | 3174 | 50.2% | -0.007 | -0.016 | -21.7 | -19.5 | +2.04 | +124.7 |  |
|  | D2 D1 + max hold 120 | replay | 137 | 62.8% | +0.242 | +0.118 | +33.2 | -5.9 | -0.14 | -2.2 | PASS |
|  | D2 D1 + max hold 120 | 2y | 3201 | 50.2% | -0.012 | -0.020 | -37.6 | -20.4 | +1.55 | +108.8 |  |
|  | D3 D1 + max hold 150 | replay | 137 | 61.3% | +0.236 | +0.108 | +32.3 | -7.0 | -0.20 | -3.0 | PASS |
|  | D3 D1 + max hold 150 | 2y | 3182 | 50.3% | -0.009 | -0.018 | -30.1 | -19.5 | +1.76 | +116.3 |  |
|  | D4 D1 + window end 14:00 | replay | 128 | 63.3% | +0.268 | +0.132 | +34.3 | -8.7 | -0.07 | -1.0 | PASS |
|  | D4 D1 + window end 14:00 | 2y | 2812 | 50.6% | -0.006 | -0.015 | -15.7 | -19.5 | +2.03 | +130.7 |  |
|  | D5 D1 + end 14:00 + max hold 120 | replay | 128 | 64.1% | +0.267 | +0.137 | +34.1 | -5.9 | -0.08 | -1.2 | PASS |
|  | D5 D1 + end 14:00 + max hold 120 | 2y | 2823 | 50.7% | -0.011 | -0.018 | -29.6 | -20.4 | +1.57 | +116.8 |  |
|  | D6 D1 + max hold 90 | replay | 137 | 61.3% | +0.205 | +0.089 | +28.1 | -4.8 | -0.42 | -7.3 | PASS |
|  | D6 D1 + max hold 90 | 2y | 3205 | 49.7% | -0.021 | -0.027 | -66.7 | -20.2 | +1.04 | +79.7 |  |
|  | D7 SPY gate + 1R >= 0.40% (start 09:50) | replay | 141 | 59.6% | +0.184 | +0.057 | +26.0 | -8.7 | -0.64 | -9.3 | PASS |
|  | D7 SPY gate + 1R >= 0.40% (start 09:50) | 2y | 3375 | 50.3% | -0.007 | -0.017 | -24.4 | -18.8 | +2.16 | +121.9 |  |
|  | D8 1R >= 0.40% of price alone (P1/P20) | replay | 188 | 57.5% | +0.145 | +0.049 | +27.3 | -9.1 | -0.97 | -8.1 | FAIL |
|  | D8 1R >= 0.40% of price alone (P1/P20) | 2y | 4460 | 49.9% | -0.021 | -0.028 | -91.9 | -18.8 | +1.89 | +54.5 | replay avg R +0.145 < parent +0.168 |
|  | T0 parent, testing book | replay | 181 | 55.2% | +0.111 | +0.013 | +20.0 | -11.3 | -1.71 | -15.3 | info (destination book) |
|  | T0 parent, testing book | 2y | 4559 | 49.5% | -0.026 | -0.032 | -117.9 | -31.5 | +0.62 | +28.5 | parent re-scored in the testing-account book |
|  | T1 WB1 start 10:30, testing book | replay | 171 | 56.1% | +0.129 | +0.020 | +22.1 | -11.3 | -1.38 | -13.3 | PASS vs T0 |
|  | T1 WB1 start 10:30, testing book | 2y | 4257 | 49.1% | -0.030 | -0.036 | -129.0 | -31.5 | +0.34 | +17.4 |  |
|  | T2 WB2 SPY gate, testing book | replay | 136 | 57.4% | +0.162 | +0.036 | +22.0 | -10.3 | -0.98 | -13.4 | PASS vs T0 |
|  | T2 WB2 SPY gate, testing book | 2y | 3393 | 49.2% | -0.027 | -0.035 | -92.5 | -31.5 | +0.83 | +53.9 |  |
|  | T3 WB3 (D1), testing book | replay | 123 | 57.7% | +0.173 | +0.030 | +21.2 | -11.3 | -0.95 | -14.1 | PASS vs T0 |
|  | T3 WB3 (D1), testing book | 2y | 2974 | 49.1% | -0.021 | -0.030 | -64.1 | -31.5 | +1.18 | +82.3 |  |

| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |
|---|---|---|---|
| PARENT | -0.074 (2438) | -0.002 (2220) | +0.136 (269) |
| V01 window end 15:00->13:00 (P6) | -0.096 (1878) | -0.002 (1686) | +0.192 (203) |
| V02 window start 09:50->10:30 (P6/P7) | -0.066 (2331) | -0.012 (2120) | +0.152 (250) |
| V03 gap <0 -> <=-1.0% (P12) | -0.168 (648) | +0.004 (860) | +0.233 (146) |
| V04 gap <0 -> <=-0.5% (P12) | -0.103 (1205) | -0.026 (1357) | +0.194 (183) |
| V05 +price at/below VWAP (new sensor) | -0.102 (1015) | -0.026 (1156) | +0.138 (159) |
| V06 +skip SPY >+0.20% since 09:50 (new gate) | -0.072 (1803) | +0.020 (1718) | +0.165 (211) |
| V07 max hold 90 min (P26) | -0.057 (2471) | -0.028 (2270) | +0.045 (260) |
| V08 max hold 120 min (P26) | -0.052 (2451) | -0.014 (2233) | +0.083 (268) |
| V09 BE stop after +0.5R (P23) | -0.067 (2474) | -0.025 (2261) | +0.114 (271) |
| V10 RSI(5) >80 -> >85 (P11) | -0.059 (1839) | -0.035 (1655) | +0.135 (208) |
| V11 buyPressure <-0.35 -> <-0.40 (P10) | -0.065 (1775) | -0.023 (1527) | +0.064 (156) |
| V12 heat <=-20 -> <=-25 (P9) | -0.048 (1233) | -0.012 (1096) | +0.236 (145) |
| V13 target 1.0 -> 0.8R (P24) | -0.068 (2525) | -0.009 (2314) | +0.124 (282) |
| V14 stop 1.0 -> 1.25R (P23) | -0.057 (2525) | -0.022 (2324) | +0.135 (281) |
| V15 ADV $95M -> $150M (P2) | -0.083 (1715) | -0.023 (1685) | +0.179 (192) |
| V16 flat 15:55 -> 15:00 (P26) | -0.067 (2438) | +0.007 (2218) | +0.144 (269) |
| V17 refire on, cooldown 6 bars (P8) | -0.071 (2504) | -0.002 (2287) | +0.118 (276) |
| V18 per-setup latch -2R -> off (P16) | -0.057 (2810) | -0.027 (2567) | +0.150 (312) |
| C1 SPY gate + flat 15:00 | -0.062 (1803) | +0.023 (1716) | +0.187 (211) |
| C2 C1 + start 10:30 | -0.053 (1669) | +0.014 (1621) | +0.189 (183) |
| C3 C1 + RSI(5) > 85 | -0.059 (1348) | -0.011 (1258) | +0.174 (156) |
| C4 SPY gate + max hold 120 | -0.055 (1828) | +0.002 (1732) | +0.119 (212) |
| C5 C1 + max hold 120 | -0.051 (1828) | +0.010 (1732) | +0.134 (212) |
| C6 SPY gate + start 10:30 | -0.059 (1672) | +0.011 (1623) | +0.164 (183) |
| C7 C2 + RSI(5) > 85 | -0.046 (1224) | -0.017 (1188) | +0.177 (133) |
| S1 SPY gate +0.10% | -0.076 (1527) | +0.014 (1493) | +0.169 (173) |
| S2 SPY gate +0.30% | -0.080 (2003) | +0.013 (1828) | +0.137 (223) |
| S3 flat 14:30 | -0.064 (2444) | -0.017 (2215) | +0.128 (269) |
| R1 C2 + 1R >= 0.30% of price | -0.048 (1620) | +0.020 (1607) | +0.186 (178) |
| R2 C2 + 1R >= 0.40% of price | -0.042 (1454) | +0.019 (1533) | +0.221 (187) |
| R3 C2 + heat <= -25 | -0.053 (821) | +0.018 (769) | +0.310 (101) |
| R4 C2 + max hold 120 | -0.046 (1697) | +0.005 (1630) | +0.140 (184) |
| R5 C1 + 1R >= 0.30% (start 09:50) | -0.056 (1751) | +0.027 (1702) | +0.185 (206) |
| D1 SPY gate + start 10:30 + 1R >= 0.40% | -0.057 (1454) | +0.016 (1533) | +0.194 (187) |
| D2 D1 + max hold 120 | -0.046 (1470) | +0.002 (1544) | +0.147 (187) |
| D3 D1 + max hold 150 | -0.051 (1457) | +0.012 (1538) | +0.138 (187) |
| D4 D1 + window end 14:00 | -0.061 (1271) | +0.016 (1372) | +0.237 (169) |
| D5 D1 + end 14:00 + max hold 120 | -0.047 (1279) | -0.000 (1375) | +0.185 (169) |
| D6 D1 + max hold 90 | -0.063 (1467) | +0.002 (1552) | +0.127 (186) |
| D7 SPY gate + 1R >= 0.40% (start 09:50) | -0.064 (1552) | +0.022 (1625) | +0.195 (198) |
| D8 1R >= 0.40% of price alone (P1/P20) | -0.059 (2133) | -0.004 (2082) | +0.169 (245) |
| T0 parent, testing book | -0.058 (2205) | -0.012 (2108) | +0.144 (246) |
| T1 WB1 start 10:30, testing book | -0.061 (2037) | -0.021 (1989) | +0.158 (231) |
| T2 WB2 SPY gate, testing book | -0.080 (1602) | +0.009 (1597) | +0.110 (194) |
| T3 WB3 (D1), testing book | -0.069 (1355) | +0.002 (1447) | +0.157 (172) |

| config | test | avg win | avg loss | median hold | stop share | target share | time share | up-day avg R | flat | down |
|---|---|---|---|---|---|---|---|---|---|---|
| PARENT | replay | +0.838 | -0.760 | 114 | 22% | 45% | 33% |  |  |  |
| PARENT | 2y | +0.808 | -0.857 | 100 | 34% | 36% | 31% | -0.255 | +0.014 | +0.137 |
| V01 window end 15:00->13:00 (P6) | replay | +0.885 | -0.796 | 118 | 23% | 50% | 27% |  |  |  |
| V01 window end 15:00->13:00 (P6) | 2y | +0.859 | -0.917 | 109 | 38% | 40% | 23% | -0.269 | +0.018 | +0.145 |
| V02 window start 09:50->10:30 (P6/P7) | replay | +0.824 | -0.719 | 120 | 19% | 46% | 35% |  |  |  |
| V02 window start 09:50->10:30 (P6/P7) | 2y | +0.794 | -0.839 | 106 | 33% | 35% | 33% | -0.262 | +0.015 | +0.140 |
| V03 gap <0 -> <=-1.0% (P12) | replay | +0.860 | -0.742 | 103 | 20% | 52% | 29% |  |  |  |
| V03 gap <0 -> <=-1.0% (P12) | 2y | +0.790 | -0.829 | 93 | 34% | 34% | 33% | -0.297 | +0.009 | +0.089 |
| V04 gap <0 -> <=-0.5% (P12) | replay | +0.876 | -0.725 | 110 | 22% | 46% | 32% |  |  |  |
| V04 gap <0 -> <=-0.5% (P12) | 2y | +0.789 | -0.829 | 100 | 33% | 33% | 33% | -0.299 | +0.005 | +0.112 |
| V05 +price at/below VWAP (new sensor) | replay | +0.855 | -0.718 | 86 | 21% | 49% | 30% |  |  |  |
| V05 +price at/below VWAP (new sensor) | 2y | +0.773 | -0.815 | 90 | 33% | 33% | 34% | -0.255 | -0.137 | +0.106 |
| V06 +skip SPY >+0.20% since 09:50 (new gate) | replay | +0.854 | -0.783 | 97 | 22% | 49% | 29% |  |  |  |
| V06 +skip SPY >+0.20% since 09:50 (new gate) | 2y | +0.820 | -0.859 | 97 | 33% | 37% | 29% | -0.318 | -0.013 | +0.124 |
| V07 max hold 90 min (P26) | replay | +0.643 | -0.527 | 90 | 11% | 27% | 63% |  |  |  |
| V07 max hold 90 min (P26) | 2y | +0.620 | -0.652 | 90 | 20% | 21% | 59% | -0.190 | -0.013 | +0.080 |
| V08 max hold 120 min (P26) | replay | +0.711 | -0.617 | 114 | 13% | 33% | 53% |  |  |  |
| V08 max hold 120 min (P26) | 2y | +0.677 | -0.713 | 100 | 24% | 25% | 50% | -0.208 | -0.000 | +0.112 |
| V09 BE stop after +0.5R (P23) | replay | +0.869 | -0.477 | 87 | 18% | 38% | 19% |  |  |  |
| V09 BE stop after +0.5R (P23) | 2y | +0.831 | -0.557 | 75 | 26% | 28% | 19% | -0.232 | +0.001 | +0.105 |
| V10 RSI(5) >80 -> >85 (P11) | replay | +0.841 | -0.728 | 111 | 19% | 48% | 33% |  |  |  |
| V10 RSI(5) >80 -> >85 (P11) | 2y | +0.798 | -0.859 | 104 | 34% | 35% | 31% | -0.242 | +0.016 | +0.106 |
| V11 buyPressure <-0.35 -> <-0.40 (P10) | replay | +0.842 | -0.762 | 122 | 22% | 45% | 34% |  |  |  |
| V11 buyPressure <-0.35 -> <-0.40 (P10) | 2y | +0.799 | -0.868 | 103 | 34% | 35% | 31% | -0.255 | +0.008 | +0.107 |
| V12 heat <=-20 -> <=-25 (P9) | replay | +0.798 | -0.795 | 120 | 23% | 44% | 33% |  |  |  |
| V12 heat <=-20 -> <=-25 (P9) | 2y | +0.807 | -0.847 | 103 | 33% | 36% | 31% | -0.224 | +0.044 | +0.132 |
| V13 target 1.0 -> 0.8R (P24) | replay | +0.714 | -0.762 | 88 | 21% | 54% | 25% |  |  |  |
| V13 target 1.0 -> 0.8R (P24) | 2y | +0.694 | -0.861 | 85 | 31% | 44% | 25% | -0.229 | +0.022 | +0.104 |
| V14 stop 1.0 -> 1.25R (P23) | replay | +0.825 | -0.803 | 126 | 15% | 46% | 39% |  |  |  |
| V14 stop 1.0 -> 1.25R (P23) | 2y | +0.801 | -0.931 | 120 | 26% | 37% | 37% | -0.279 | +0.023 | +0.149 |
| V15 ADV $95M -> $150M (P2) | replay | +0.858 | -0.795 | 111 | 24% | 49% | 27% |  |  |  |
| V15 ADV $95M -> $150M (P2) | 2y | +0.802 | -0.837 | 100 | 33% | 35% | 32% | -0.253 | -0.003 | +0.112 |
| V16 flat 15:55 -> 15:00 (P26) | replay | +0.722 | -0.657 | 94 | 16% | 39% | 46% |  |  |  |
| V16 flat 15:55 -> 15:00 (P26) | 2y | +0.710 | -0.769 | 84 | 28% | 29% | 43% | -0.235 | +0.022 | +0.132 |
| V17 refire on, cooldown 6 bars (P8) | replay | +0.829 | -0.761 | 114 | 22% | 44% | 33% |  |  |  |
| V17 refire on, cooldown 6 bars (P8) | 2y | +0.805 | -0.852 | 100 | 33% | 36% | 31% | -0.245 | +0.009 | +0.133 |
| V18 per-setup latch -2R -> off (P16) | replay | +0.829 | -0.756 | 113 | 22% | 44% | 34% |  |  |  |
| V18 per-setup latch -2R -> off (P16) | 2y | +0.798 | -0.848 | 100 | 33% | 35% | 32% | -0.238 | +0.013 | +0.122 |
| C1 SPY gate + flat 15:00 | replay | +0.774 | -0.683 | 82 | 16% | 44% | 40% |  |  |  |
| C1 SPY gate + flat 15:00 | 2y | +0.722 | -0.780 | 80 | 28% | 30% | 41% | -0.306 | +0.011 | +0.116 |
| C2 C1 + start 10:30 | replay | +0.766 | -0.625 | 90 | 12% | 45% | 43% |  |  |  |
| C2 C1 + start 10:30 | 2y | +0.705 | -0.752 | 85 | 27% | 29% | 44% | -0.315 | -0.004 | +0.119 |
| C3 C1 + RSI(5) > 85 | replay | +0.784 | -0.641 | 71 | 15% | 46% | 39% |  |  |  |
| C3 C1 + RSI(5) > 85 | 2y | +0.718 | -0.780 | 80 | 29% | 30% | 42% | -0.281 | -0.008 | +0.087 |
| C4 SPY gate + max hold 120 | replay | +0.766 | -0.650 | 97 | 14% | 39% | 47% |  |  |  |
| C4 SPY gate + max hold 120 | 2y | +0.691 | -0.726 | 96 | 25% | 27% | 49% | -0.269 | -0.018 | +0.098 |
| C5 C1 + max hold 120 | replay | +0.744 | -0.606 | 82 | 12% | 37% | 52% |  |  |  |
| C5 C1 + max hold 120 | 2y | +0.646 | -0.689 | 79 | 23% | 24% | 53% | -0.262 | -0.006 | +0.100 |
| C6 SPY gate + start 10:30 | replay | +0.851 | -0.736 | 101 | 19% | 51% | 31% |  |  |  |
| C6 SPY gate + start 10:30 | 2y | +0.806 | -0.836 | 102 | 32% | 36% | 32% | -0.330 | -0.027 | +0.129 |
| C7 C2 + RSI(5) > 85 | replay | +0.776 | -0.611 | 80 | 13% | 46% | 41% |  |  |  |
| C7 C2 + RSI(5) > 85 | 2y | +0.698 | -0.751 | 85 | 27% | 28% | 45% | -0.284 | -0.012 | +0.089 |
| S1 SPY gate +0.10% | replay | +0.845 | -0.778 | 100 | 21% | 50% | 29% |  |  |  |
| S1 SPY gate +0.10% | 2y | +0.812 | -0.853 | 95 | 33% | 36% | 30% | -0.299 | -0.061 | +0.108 |
| S2 SPY gate +0.30% | replay | +0.858 | -0.782 | 97 | 23% | 48% | 29% |  |  |  |
| S2 SPY gate +0.30% | 2y | +0.819 | -0.865 | 98 | 34% | 37% | 29% | -0.292 | -0.020 | +0.129 |
| S3 flat 14:30 | replay | +0.758 | -0.579 | 88 | 13% | 36% | 51% |  |  |  |
| S3 flat 14:30 | 2y | +0.686 | -0.688 | 74 | 26% | 27% | 48% | -0.230 | +0.009 | +0.110 |
| R1 C2 + 1R >= 0.30% of price | replay | +0.760 | -0.614 | 92 | 12% | 44% | 44% |  |  |  |
| R1 C2 + 1R >= 0.30% of price | 2y | +0.703 | -0.749 | 85 | 27% | 29% | 45% | -0.300 | -0.003 | +0.120 |
| R2 C2 + 1R >= 0.40% of price | replay | +0.747 | -0.603 | 96 | 12% | 42% | 46% |  |  |  |
| R2 C2 + 1R >= 0.40% of price | 2y | +0.701 | -0.742 | 85 | 26% | 29% | 45% | -0.308 | -0.000 | +0.130 |
| R3 C2 + heat <= -25 | replay | +0.786 | -0.591 | 95 | 11% | 44% | 44% |  |  |  |
| R3 C2 + heat <= -25 | 2y | +0.707 | -0.736 | 82 | 26% | 29% | 45% | -0.267 | +0.024 | +0.102 |
| R4 C2 + max hold 120 | replay | +0.734 | -0.550 | 90 | 8% | 37% | 55% |  |  |  |
| R4 C2 + max hold 120 | 2y | +0.623 | -0.669 | 83 | 22% | 22% | 56% | -0.277 | -0.020 | +0.107 |
| R5 C1 + 1R >= 0.30% (start 09:50) | replay | +0.770 | -0.675 | 84 | 16% | 44% | 41% |  |  |  |
| R5 C1 + 1R >= 0.30% (start 09:50) | 2y | +0.721 | -0.777 | 80 | 28% | 30% | 42% | -0.292 | +0.012 | +0.118 |
| D1 SPY gate + start 10:30 + 1R >= 0.40% | replay | +0.836 | -0.724 | 111 | 19% | 48% | 33% |  |  |  |
| D1 SPY gate + start 10:30 + 1R >= 0.40% | 2y | +0.807 | -0.826 | 101 | 32% | 36% | 32% | -0.319 | -0.033 | +0.137 |
| D2 D1 + max hold 120 | replay | +0.735 | -0.589 | 111 | 11% | 36% | 53% |  |  |  |
| D2 D1 + max hold 120 | 2y | +0.671 | -0.699 | 100 | 23% | 25% | 52% | -0.284 | -0.030 | +0.110 |
| D3 D1 + max hold 150 | replay | +0.779 | -0.624 | 111 | 13% | 41% | 46% |  |  |  |
| D3 D1 + max hold 150 | 2y | +0.712 | -0.741 | 100 | 26% | 29% | 45% | -0.306 | -0.043 | +0.134 |
| D4 D1 + window end 14:00 | replay | +0.849 | -0.733 | 122 | 19% | 50% | 31% |  |  |  |
| D4 D1 + window end 14:00 | 2y | +0.832 | -0.863 | 117 | 34% | 38% | 28% | -0.319 | -0.034 | +0.160 |
| D5 D1 + end 14:00 + max hold 120 | replay | +0.743 | -0.584 | 120 | 10% | 38% | 52% |  |  |  |
| D5 D1 + end 14:00 + max hold 120 | 2y | +0.679 | -0.719 | 117 | 24% | 26% | 50% | -0.283 | -0.032 | +0.131 |
| D6 D1 + max hold 90 | replay | +0.667 | -0.528 | 90 | 9% | 29% | 62% |  |  |  |
| D6 D1 + max hold 90 | 2y | +0.607 | -0.640 | 90 | 20% | 20% | 61% | -0.261 | -0.033 | +0.083 |
| D7 SPY gate + 1R >= 0.40% (start 09:50) | replay | +0.842 | -0.784 | 101 | 23% | 48% | 30% |  |  |  |
| D7 SPY gate + 1R >= 0.40% (start 09:50) | 2y | +0.821 | -0.846 | 98 | 33% | 37% | 30% | -0.306 | -0.012 | +0.129 |
| D8 1R >= 0.40% of price alone (P1/P20) | replay | +0.817 | -0.762 | 118 | 22% | 43% | 35% |  |  |  |
| D8 1R >= 0.40% of price alone (P1/P20) | 2y | +0.808 | -0.845 | 101 | 33% | 36% | 31% | -0.240 | +0.014 | +0.143 |
| T0 parent, testing book | replay | +0.815 | -0.759 | 115 | 24% | 40% | 36% |  |  |  |
| T0 parent, testing book | 2y | +0.800 | -0.836 | 100 | 33% | 35% | 32% | -0.225 | +0.026 | +0.103 |
| T1 WB1 start 10:30, testing book | replay | +0.808 | -0.740 | 120 | 22% | 40% | 37% |  |  |  |
| T1 WB1 start 10:30, testing book | 2y | +0.790 | -0.822 | 104 | 32% | 34% | 34% | -0.236 | +0.018 | +0.105 |
| T2 WB2 SPY gate, testing book | replay | +0.834 | -0.742 | 100 | 23% | 44% | 33% |  |  |  |
| T2 WB2 SPY gate, testing book | 2y | +0.809 | -0.838 | 97 | 33% | 36% | 31% | -0.319 | -0.015 | +0.093 |
| T3 WB3 (D1), testing book | replay | +0.820 | -0.712 | 108 | 21% | 43% | 36% |  |  |  |
| T3 WB3 (D1), testing book | 2y | +0.800 | -0.812 | 100 | 32% | 35% | 33% | -0.324 | -0.028 | +0.102 |

## Method (identical for parent and every copy)
- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live
  (Primary + On Deck) and passed the shortable+ETB check, 2026-10-12..11-13 (233 symbol-days, 24 sessions; 11-16 still
  in progress, excluded). 1-min SIP bars (read-only GET) → lab frame (`mcf.report.engine.lab_frame` + daily priors as
  live). Parent replay vs live on the same symbol-days: 171 matched, replay +0.192R vs live +0.202R, correlation 0.95.
  Limit: names that never signalled live are not in it, so copies that LOOSEN a condition cannot be replayed (none does).
- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted),
  names shortable+ETB on ≥ 90% of 26 universe snapshots (E90 proxy), ADV ≥ $95M, daily ATR ≥ 1% (account universe),
  price ≥ $5. Splits TRAIN ≤ 2025-12-31, VALID 2026-01..10-05, FWD 10-06..11-04.
- **Engine (same for both; reused from the L3 Workbench bench, `code/sim_rw3.py`):** signal on the 5-min bar close
  (heat ≤ −20, buyPressure < −0.35, RSI(5) > 80, gap < 0), refire off (first qualifying bar per symbol-day), entry at the
  signal-bar close, 1R = 0.25 × daily ATR, exits on 1-min bars (stop first; target only when traded through by $0.01;
  flat 15:55), **LR8 costs** (entry 1 bp + SEC + TAF + CAT; stop max($0.02, 4 bps); time exit max($0.01, 1 bp)), Primary
  book (≤ 30 open lots, ≤ 3 per symbol, −2R net latch). SPY since 09:50 from SPY 1-min bars; the WB2/WB3 modules
  (`spy_fo` context) reproduce the research signal list exactly on the replay frames (176/176 and 148/148 symbol-days).
- Pre-declared rounds in `code/decl.py` (each round declared before its scores were read). Results `results.csv`,
  shapes `extras.csv`, `code/report.py` builds the tables below.

## Every configuration tried (45), including failures
Round 1 (18 one-part tweaks, every tunable part): PASS V01 end 13:00 (meets only), V02 start 10:30 (=WB1), V06 SPY gate
(=WB2), V08 max hold 120, V10 RSI(5) > 85, V16 flat 15:00, V17 refire cooldown 6. FAIL: V03 gap ≤ −1% (2-year −0.043),
V04 gap ≤ −0.5% (2-year −0.045), V05 price ≤ VWAP (2-year −0.048), V07 max hold 90 (replay +0.157), V09 BE after +0.5R
(replay +0.134), V11 buyPressure < −0.40 (both lower), V12 heat ≤ −25 (replay +0.144), V13 target 0.8R (replay +0.145),
V14 stop 1.25R (worst day −14.0 / −24.6R), V15 ADV $150M (2-year −0.041), V18 latch off (worst day −15.3 / −38.7R).
Round 2 (10 combos/sensitivity): all PASS — C1 gate + flat 15:00 (+0.237 / −0.009), C2 C1 + start 10:30 (+0.287 / −0.009),
C3/C7 + RSI 85 (2-year −0.024 / −0.021), C4/C5 + max hold 120 (−0.019 / −0.013), C6 gate + start 10:30 (+0.274 / −0.015),
S1/S2 gate at +0.10 / +0.30% (−0.021 / −0.026: 0.20 is the middle of a stable range), S3 flat 14:30 (2-year −0.032).
Round 3 (5 on C2): R1 1R ≥ 0.30% (+0.284 / −0.004), **R2 1R ≥ 0.40% (+0.264 / +0.003)**, R3 heat ≤ −25 (81 replay trades,
+0.242 / +0.001), R4 max hold 120 (+0.276 / −0.013), R5 C1 + 1R ≥ 0.30% (+0.237 / −0.004).
Round 4 (6, deployable stand-ins for flat 15:00): **D1 gate + start 10:30 + ATR floor (=WB3) +0.244 / −0.007**,
D2/D3/D6 + max hold 120/150/90 (−0.012 / −0.009 / −0.021 2-year: max hold does not stack), D4 + end 14:00 (+0.268 /
−0.006 on 11% fewer trades; not chosen, within noise of D1), D5 end 14:00 + hold 120 (−0.010).
Round 5 (2, attribution): D7 gate + ATR floor, start 09:50 (+0.185 / −0.007), D8 ATR floor alone (FAIL replay +0.145).
Round 6 (4, destination book: no latch, cap 50, CF 0.15): T0 parent +0.111 / −0.026; T1 WB1 +0.129 / −0.030;
T2 WB2 +0.162 / −0.027; T3 WB3 +0.173 / −0.022 (all PASS vs T0; all worst days −31.5R without the latch).
Not spawned though passing: V08/V10/V16/V17/V01 (one-test gains or not deployable: flat 15:00 needs a runner hook).

## Pending config change — "ready to deploy after close" (NOT applied; built during market hours)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective session 2026-11-17. One copy only:
**WB3** (it contains WB1 and WB2; running them side by side would be near-twins). The parent stays in Primary, unchanged.
Account: **Testing D** (`config/account_testingd.yaml`) — a testing account, not the parent's (Primary) and not On Deck;
no RW/MF/L3 gap-down sister there (Testing A/B/C/E/F hold MF4/MF5, MF2, RW6, RW6G1, RW7-FD/MF1 — same gap-down names would
compete for the per-symbol lot cap); today's CWT14-WB5 plan also targets Testing D but is a LONG setup appended last (an
opposite-side hold can block a lot either way, rare). If another Mechanic job claims Testing D first, Testing B is the
next choice. Twin check: `twin_key` strips only `-FD`, so `...-FD-WB3` is not the parent's twin key; different accounts.
Note the destination book differs from Primary (no −2R latch, 50 lots, CF 0.15 → round 6 numbers, not the main table).
1. `config/account_testingd.yaml`, under `strategies:` add
   ```yaml
   RW3-gapdn-rsi5pop-flowsell-short-FD-WB3:
     # Workbench copy of RW3-gapdn-rsi5pop-flowsell-short-FD (Primary), Mechanic 2026-11-16: start 10:30 + skip while SPY
     # > +0.20% since 09:50 + daily ATR >= 1.6%; research/workbench/RW3-gapdn-rsi5pop-flowsell-short-FD/RESULTS.md. Effective 2026-11-17.
     enabled: true
     type: lab
     module: research/workbench/RW3-gapdn-rsi5pop-flowsell-short-FD/modules/RW3-gapdn-rsi5pop-flowsell-short-FD-WB3.py
     min_adv: 95000000
     window: [1030, 1500]
     context: [spy_fo]
     scale_out_r: null
     tags: [workbench, "parent:RW3-gapdn-rsi5pop-flowsell-short-FD"]
   ```
   and put `RW3-gapdn-rsi5pop-flowsell-short-FD-WB3` FIRST in `live.setup_order` (ahead of the ROT1 spotlight
   CWT04-backside-vwaptest-a25-short; RULES 5).
2. `config/setup_names.yaml`: `RW3-gapdn-rsi5pop-flowsell-short-FD-WB3: {name: "Gap-Down Pop Fade, Heavy Selling (all day) — WB3: from 10:30, SPY gate, ATR 1.6%+", side: short, what: "10:30-15:00: stock gapped down, bearish heat <= -20, heavy net selling, RSI(5) pops above 80, daily ATR >= 1.6% of price, and SPY not up more than 0.20% since 09:50; short the pop."}`
3. `research/ledger.jsonl`: id `2026-11-16-wb-rw3-fd-wb3`, effective 2026-11-17, title "Workbench copy
   RW3-gapdn-rsi5pop-flowsell-short-FD-WB3 added to Testing D, first in setup_order (Mechanic pass)", patch
   `{"strategies.RW3-gapdn-rsi5pop-flowsell-short-FD-WB3 (testingd)": [null, "added, enabled"], "live.setup_order (testingd)": ["...", "WB3 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5 (passes go to a testing account at once)";
   then `python -m mcf.research.ledger check`.
4. Smoke test: load the account config and run the setup over one cached session (the module needs the `spy_fo` context
   column; without it the mask fires nothing — fail safe), `python -m mcf.report.assignments` (regenerates
   docs/live/assignments.json in the same commit), `pytest -q`, commit, push after 16:05 ET (setup-freeze).
Low-rep note: WB3 is a new setup (< 20 live trades) — first in Testing D's order for exposure per RULES 5.

## Files
`DIAGNOSIS.md`, blueprint `RW3-gapdn-rsi5pop-flowsell-short-FD.md` + `_engine.png`, trade charts `_worst1..5_*.png` /
`_best1..5_*.png`, `variants.jsonl`, `modules/` + `*-WB1..3.yaml` (stubs, not account configs), `results.csv`, `extras.csv`,
`code/` (sim_rw3.py, load.py, go.py, decl.py, report.py, cand2y.py, paths2y.py, etb.py, fetch_replay.py; run from a scratch dir
holding their inputs; go.py takes `decl ROUND<n>`).
