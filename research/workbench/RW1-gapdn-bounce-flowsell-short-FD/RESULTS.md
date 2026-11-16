# Workbench RESULTS — Gap-Down Bounce Short, Heavy Selling (all day) `RW1-gapdn-bounce-flowsell-short-FD` (On Deck) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16, built ~14:45-16:30 ET (research files only; no config change, no deploy).

## Verdict — supervisor sign-off
> **Recommended: `RW1-gapdn-bounce-flowsell-short-FD-WB3`** — parent + four layers: RSI(14) band 55-60 (was 55-65), 1R (0.25 x daily ATR) >= 0.40% of
> price, entries only to the 13:00 bar close (was 15:00), and skip while SPY is up more than +0.20% since the 09:50 bar close
> (sibling RW3 / RW5 gate, measured after 09:50 per the owner rule). **PASS — better than the parent in both tests on avg R,
> avg R w/o best day and worst day, positive after costs in both, and better in every 2-year split.**

| copy | change | replay avg R (parent +0.013) | 2-year avg R (parent −0.018) | w/o best day (replay / 2y; parent −0.057 / −0.022) | worst day (replay / 2y; parent −8.2 / −25.7R) | trades (replay / 2y; parent 177 / 5,905) | verdict |
|---|---|---|---|---|---|---|---|
| WB1 | P6 window end 15:00 -> 13:00 | +0.088 | −0.013 | +0.009 / −0.017 | −8.2 / −25.7 | 140 / 4,433 | PASS (contained in WB3; TRAIN split worse −0.056 vs −0.044) |
| WB2 | P11 RSI(14) band 55-65 -> 55-60 | +0.082 | −0.012 | +0.005 / −0.019 | −6.6 / −16.6 | 115 / 3,362 | PASS (contained in WB3) |
| **WB3** | RSI 55-60 + 1R >= 0.40% of price + end 13:00 + skip SPY > +0.20% since 09:50 | **+0.185** | **+0.026** | **+0.081 / +0.018** | **−6.6 / −14.3** | 76 / 1,855 | **PASS — recommended** |

Pass rule (owner 2026-11-16): meets or exceeds the parent's avg R after costs in BOTH identical tests (meets = within 0.01R or
>= 95%), not worse on avg R w/o best day by > 0.02R or on worst day by > 10%. Parent and copies scored by the identical pipeline;
the parent's live record is NOT used in the decision (DIAGNOSIS.md uses it for diagnosis only).

Supervisor sign-off (what changed, why, before/after, where it gives back):
- **What / why.** The parent's losses come from three leaks, all confirmed in live, replay and the 2-year test: (1) the upper half
  of the RSI(14) band (60-65) — a gap-down name that has already reclaimed, not one bouncing into supply (live 54 trades −6.9R);
  (2) afternoon entries (replay 13:00-15:00 −0.27R/trade); (3) thin-R names (2-year 1R < 0.40% of price −0.23R/trade). With those
  closed, the sibling SPY-since-09:50 gate adds a further step on both tests (C5 -> WB3: replay +0.160 -> +0.185, 2-year +0.008 ->
  +0.026). WB3 drops 4 of the 5 worst live trades (EMR, XLI, FDS, BNO) and keeps 2 of the 5 best (APH, BAI).
- **Overall before -> after (identical pipeline, LR8 costs, On Deck book):** replay +0.013 -> **+0.185R** (total +2.2 -> +14.0R; w/o
  best day −0.057 -> +0.081; worst day −8.2 -> −6.6R); 2-year −0.018 -> **+0.026R** (total −105.5 -> +47.7R; w/o best day −0.022 ->
  +0.018; worst day −25.7 -> −14.3R); better in every 2-year split (TRAIN −0.044 -> −0.016, VALID −0.002 -> +0.048, FWD +0.070 ->
  +0.152). Day-paired t vs parent: replay +1.12 (dR +11.8R), 2-year +1.66 (dR +153.2R).
- **Where it gives back:** (1) far fewer trades — replay 177 -> 76 (−57%), 2-year 5,905 -> 1,855 (−69%), about 4 a day; (2) up-tape
  days are still the weak spot and are worse per trade (2-year up days −0.249 -> −0.324R on 415 instead of 1,860 trades; the gate
  cuts exposure, it does not fix them) and flat days are flat (+0.008 -> +0.005); (3) **replay is carried by one day**: 10-22 =
  66% of WB3's replay R (`1 day` tag) — w/o that day still +0.081R/trade vs the parent's −0.057; in the 2-year test the best day is
  31% of R; (4) afternoon winners such as PURR 10-16 14:30 / LEVI 10-28 13:30 are not taken (both would also fail today's CF
  cost filter).
- **Honest limits:** no RW1 copy clears the configs-counted bar max(1.5, sqrt(2 ln 48)) = 2.78 except V03 alone (1R >= 0.40%,
  2-year t +3.29, replay unchanged); under the owner's clarified rule the t is reported, not used to pass. The SPY gate fails on
  its own here (V24: replay −0.008, w/o best day −0.103) — it is in WB3 only because it adds inside the combo in both tests, a
  combination chosen in round 3 after seeing round 2 (selection risk). The window end is sensitive (end 13:30, D3: 2-year −0.011).
  The replay is the live signal symbol-days (228, incl. ones the live book skipped), so the ADV part (P2) cannot be replayed.

## Sibling parts (RW3 / RW5) — do they transfer?
| part | RW3 / RW5 result | RW1 alone | RW1 inside the combo |
|---|---|---|---|
| SPY-since-09:50 gate 0.20% | core of both siblings' WB3 | **no** — V24 FAIL (replay −0.008 vs +0.013, w/o best day −0.103); V25 0.30 FAIL (w/o best day) | **yes** — C5 -> D8 better in both tests and all 2-year splits |
| cost / ATR intake | RW5 cost/R <= 0.15 (already the parent's CF here); RW3 1R >= 0.40% of price | RW5 form tightened to 0.10R: V04 FAIL (replay +0.002); RW3 form: V03 PASS (2-year −0.009, t +3.29) | 1R >= 0.40% kept (D6 without it: 2-year −0.003) |
| later start | RW3 10:30, RW5 10:15 | V07 10:30 / V08 11:00 meet only (~0) | **no** — C8 / C9 worse than C1 / C7; this setup's problem is the END of the window (13:00), not the start |

## Method (identical for parent and every copy) — harness reused from research/workbench/RW3-gapdn-rsi5pop-flowsell-short-FD/code
- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live in any account
  and was shortable+ETB, 2026-10-12..11-13 (228 symbol-days, 24 sessions). 1-min SIP bars (read-only GET) -> lab frame (`mcf.report.engine.lab_frame`
  + daily priors as live). Parent replay 177 trades +0.013R vs live 140 trades +0.004R (117 symbol-days in both).
- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted in cand2y.py /
  paths2y.py / load.py), ADV >= $95M, names shortable+ETB on >= 90% of the universe snapshots (E90 proxy). Splits TRAIN <= 2025-12-31,
  VALID 2026-01..10-05, FWD 10-06..11-04.
- Same engine for both: RW1 sensors on the 5-min bar close (heat <= −20, buyPressure < −0.35, 55 <= RSI(14) <= 65, gap < 0), account
  universe daily ATR >= 1%, price >= $5, refire off (first qualifying bar per symbol-day), entry at the signal-bar close, exits on
  1-min bars (stop first; target only when traded through by $0.01; flat 15:55), **LR8 costs**, the On Deck book the parent runs in
  today (no per-setup latch, <= 150 lots, <= 3 per symbol, CF: skip if stop-exit cost > 0.15R). SPY since 09:50 from SPY 1-min closes.
- Module parity (WB modules vs bench masks): WB1 6,449 / 6,449 and WB2 4,435 / 4,435 bar hits on the 2-year candidate rows; WB3
  96 / 96 on the full replay frames (WB3 needs each session's 09:50 bar and the `spy_fo` context column; without them it fails safe).
- Rule changes inside the replay window (ledger): 10-20 twin rule / −2R latch Testing 1/2, 10-23 latch off, 10-30 CF cost filter,
  11-12 LR1/LR5 + LR8 costs + On Deck build (this setup moved Testing A -> On Deck), 11-16 RW7 to Testing F. The replay applies
  today's On Deck rules to every session, so none of these mixes into the comparison.

## Every configuration tried (48), including failures
Round 1 (V01-V26, one part each, declared in code/decl.py before any score), Round 2 (C1-C11, S1-S3, declared after Round 1),
Round 3 (D1-D8, declared after Round 2). Verdict column = the owner's pass rule.

Configurations: 48 (parent excluded); configs-counted bar max(1.5, sqrt(2 ln 48)) = 2.78

| copy | config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | t vs parent (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | PARENT | 177 | +0.013 | -0.057 | -8.2 | 5905 | -0.018 | -0.022 | -25.7 | +0.00 / +0.00 | — |
|  | V01 ADV $95M -> $150M (P2) | 148 | -0.057 | -0.129 | -7.1 | 4277 | -0.009 | -0.015 | -21.8 | -1.72 / +1.48 | FAIL — replay avg R -0.057 < parent +0.013; replay w/o best day -0.129 vs -0.057 |
|  | V02 price >= $10 (P3) | 177 | +0.013 | -0.057 | -8.2 | 5903 | -0.018 | -0.022 | -25.7 | +0.00 / -1.41 | PASS |
|  | V03 1R >= 0.40% of price (P1/P21 intake, RW3) | 173 | +0.013 | -0.057 | -8.2 | 5681 | -0.009 | -0.014 | -23.7 | +0.06 / +3.29 | PASS |
|  | V04 cost filter 0.15 -> 0.10R (P18, RW5 intake) | 157 | +0.002 | -0.065 | -6.1 | 4806 | -0.011 | -0.016 | -19.8 | -0.41 / +1.38 | FAIL — replay avg R +0.002 < parent +0.013 |
| WB1 | V05 window end 15:00->13:00 (P6) | 140 | +0.088 | +0.009 | -8.2 | 4433 | -0.013 | -0.017 | -25.7 | +1.61 / +1.00 | PASS |
|  | V06 window end 15:00->14:00 (P6) | 160 | +0.037 | -0.036 | -8.2 | 5231 | -0.023 | -0.027 | -25.7 | +1.56 / -0.56 | PASS |
|  | V07 start 09:50->10:30 (P7, RW3) | 176 | +0.007 | -0.064 | -8.2 | 5667 | -0.017 | -0.022 | -25.7 | -1.00 / +0.41 | PASS |
|  | V08 start 09:50->11:00 (P7) | 142 | +0.039 | -0.047 | -8.3 | 4333 | -0.022 | -0.027 | -23.7 | +0.60 / +0.14 | PASS |
|  | V09 refire on, cooldown 6 (P8) | 181 | +0.003 | -0.067 | -9.9 | 6166 | -0.016 | -0.020 | -25.1 | -0.78 / +0.35 | FAIL — replay worst day -9.9 vs -8.2R |
|  | V10 heat <= -25 (P9) | 85 | +0.062 | -0.049 | -4.5 | 2331 | -0.015 | -0.022 | -18.1 | +0.28 / +0.85 | PASS |
|  | V11 heat <= -15 (P9 looser) | 178 | +0.034 | -0.044 | -8.5 | 11869 | -0.026 | -0.030 | -45.1 | +1.37 / -1.51 | FAIL — 2y worst day -45.1 vs -25.7R |
|  | V12 buyPressure < -0.40 (P10) | 112 | +0.103 | +0.021 | -3.8 | 3976 | -0.029 | -0.034 | -19.1 | +1.14 / -0.23 | FAIL — 2y avg R -0.029 < parent -0.018 |
| WB2 | V13 RSI(14) 55-60 (P11 hi) | 115 | +0.082 | +0.005 | -6.6 | 3362 | -0.012 | -0.019 | -16.6 | +1.07 / +0.98 | PASS |
|  | V14 RSI(14) 58-65 (P11 lo) | 112 | +0.037 | -0.008 | -5.8 | 4548 | -0.031 | -0.035 | -21.7 | +0.19 / -0.76 | FAIL — 2y avg R -0.031 < parent -0.018 |
|  | V15 gap <= -0.5% (P12) | 142 | +0.003 | -0.089 | -7.1 | 3446 | -0.004 | -0.010 | -23.5 | -0.33 / +1.52 | FAIL — replay w/o best day -0.089 vs -0.057 |
|  | V16 gap <= -1.0% (P12) | 107 | +0.074 | -0.026 | -6.0 | 2144 | -0.003 | -0.010 | -19.5 | +0.66 / +1.20 | PASS |
|  | V17 lots per symbol 3 -> 1 (P15) | 177 | +0.013 | -0.057 | -8.2 | 5905 | -0.018 | -0.022 | -25.7 | +0.00 / +0.00 | PASS |
|  | V18 per-setup latch -2R (P16) | 160 | -0.008 | -0.046 | -7.9 | 5181 | -0.018 | -0.023 | -19.1 | -0.49 / +0.29 | FAIL — replay avg R -0.008 < parent +0.013 |
|  | V19 stop 1.0 -> 1.25R (P24) | 177 | +0.017 | -0.063 | -8.9 | 5905 | -0.008 | -0.013 | -29.5 | +0.20 / +1.73 | FAIL — 2y worst day -29.5 vs -25.7R |
|  | V20 target 1.0 -> 0.8R (P25) | 177 | +0.004 | -0.051 | -7.2 | 5905 | -0.018 | -0.022 | -26.3 | -0.27 / -0.08 | PASS |
|  | V21 BE stop after +0.5R (P24 move) | 177 | +0.001 | -0.067 | -8.1 | 5905 | -0.030 | -0.034 | -24.4 | -0.54 / -1.70 | FAIL — replay avg R +0.001 < parent +0.013; 2y avg R -0.030 < parent -0.018 |
|  | V22 max hold 120 min (P27) | 177 | -0.033 | -0.114 | -6.1 | 5905 | -0.027 | -0.030 | -25.3 | -1.25 / -1.03 | FAIL — replay avg R -0.033 < parent +0.013; replay w/o best day -0.114 vs -0.057 |
|  | V23 flat 15:55 -> 15:00 (P27, no live knob) | 177 | +0.009 | -0.073 | -8.6 | 5905 | -0.014 | -0.017 | -24.8 | -0.08 / +0.44 | PASS |
|  | V24 gate: skip SPY > +0.20% since 09:50 (new, RW3/RW5) | 141 | -0.008 | -0.103 | -8.2 | 4484 | -0.007 | -0.012 | -25.7 | -0.39 / +1.42 | FAIL — replay avg R -0.008 < parent +0.013; replay w/o best day -0.103 vs -0.057 |
|  | V25 gate: skip SPY > +0.30% since 09:50 (new) | 148 | +0.008 | -0.079 | -8.2 | 4918 | -0.014 | -0.019 | -25.7 | -0.12 / +0.81 | FAIL — replay w/o best day -0.079 vs -0.057 |
|  | V26 price at/below VWAP (new sensor) | 128 | +0.039 | -0.046 | -7.7 | 3527 | -0.024 | -0.030 | -22.4 | +0.40 / +0.30 | PASS |
|  | C1 RSI 55-60 + 1R>=0.40% | 113 | +0.086 | +0.007 | -6.6 | 3257 | -0.006 | -0.012 | -14.3 | +1.07 / +1.27 | PASS |
|  | C2 RSI 55-60 + gap<=-1% | 79 | +0.125 | +0.013 | -6.0 | 1417 | +0.018 | +0.009 | -13.7 | +0.72 / +1.36 | PASS |
|  | C3 C1 + gap<=-1% | 79 | +0.125 | +0.013 | -6.0 | 1408 | +0.015 | +0.006 | -13.7 | +0.72 / +1.31 | PASS |
|  | C4 RSI 55-60 + heat<=-25 | 59 | +0.066 | -0.055 | -3.3 | 1301 | +0.014 | +0.004 | -8.8 | +0.13 / +1.23 | PASS |
|  | C5 C1 + end 13:00 | 91 | +0.160 | +0.072 | -6.6 | 2382 | +0.008 | +0.002 | -14.3 | +1.52 / +1.47 | PASS |
|  | C6 C3 + end 13:00 | 65 | +0.178 | +0.044 | -6.0 | 1049 | +0.042 | +0.033 | -12.7 | +0.81 / +1.43 | PASS |
|  | C7 C1 + SPY gate 0.20 (sibling) | 94 | +0.085 | -0.013 | -6.6 | 2551 | +0.005 | -0.003 | -14.3 | +0.58 / +1.50 | PASS |
|  | C8 C1 + start 10:30 (sibling) | 112 | +0.077 | -0.003 | -6.6 | 3107 | -0.005 | -0.012 | -14.3 | +0.92 / +1.29 | PASS |
|  | C9 C1 + SPY gate 0.20 + start 10:30 (sibling pack) | 93 | +0.075 | -0.027 | -6.6 | 2424 | +0.004 | -0.004 | -14.3 | +0.46 / +1.45 | PASS |
|  | C10 C3 + heat<=-25 | 48 | +0.089 | -0.061 | -3.3 | 717 | +0.055 | +0.043 | -8.8 | +0.14 / +1.31 | PASS |
|  | C11 C1 + end 14:00 | 105 | +0.101 | +0.020 | -6.6 | 2842 | -0.013 | -0.020 | -14.3 | +1.16 / +0.91 | PASS |
|  | S1 RSI 55-58 + 1R>=0.40% | 82 | +0.053 | -0.041 | -4.7 | 2027 | +0.023 | +0.016 | -9.6 | +0.20 / +1.67 | PASS |
|  | S2 RSI 55-61 + 1R>=0.40% | 124 | +0.055 | -0.021 | -6.6 | 3764 | -0.003 | -0.008 | -15.6 | +0.74 / +1.66 | PASS |
|  | S3 C1 + gap<=-0.75% | 88 | +0.091 | -0.015 | -5.8 | 1697 | +0.022 | +0.015 | -13.7 | +0.65 / +1.59 | PASS |
|  | D1 C5 + gap<=-0.5% | 80 | +0.113 | -0.005 | -5.8 | 1534 | +0.026 | +0.019 | -13.8 | +0.72 / +1.51 | PASS |
|  | D2 C5 + gap<=-0.75% | 72 | +0.130 | +0.000 | -5.8 | 1255 | +0.046 | +0.038 | -12.7 | +0.72 / +1.62 | PASS |
|  | D3 C5 with end 13:30 | 99 | +0.132 | +0.047 | -6.6 | 2625 | -0.011 | -0.017 | -14.3 | +1.45 / +0.97 | PASS |
|  | D4 C5 with RSI 55-61 | 98 | +0.135 | +0.048 | -6.6 | 2764 | +0.010 | +0.005 | -14.3 | +1.40 / +1.74 | PASS |
|  | D5 C5 with 1R>=0.35% | 91 | +0.160 | +0.072 | -6.6 | 2430 | +0.006 | -0.001 | -15.5 | +1.52 / +1.43 | PASS |
|  | D6 C5 without 1R floor (RSI 55-60 + end 13:00) | 93 | +0.155 | +0.067 | -6.6 | 2463 | -0.003 | -0.009 | -16.6 | +1.51 / +1.19 | PASS |
|  | D7 C5 without RSI band (1R>=0.40% + end 13:00) | 136 | +0.092 | +0.011 | -8.2 | 4260 | -0.001 | -0.005 | -23.4 | +1.56 / +1.99 | PASS |
| WB3 | D8 C5 + SPY gate 0.20 (sibling) | 76 | +0.185 | +0.081 | -6.6 | 1855 | +0.026 | +0.018 | -14.3 | +1.12 / +1.66 | PASS |

| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |
|---|---|---|---|
| PARENT | -0.044 (2705) | -0.002 (2907) | +0.070 (293) |
| V01 ADV $95M -> $150M (P2) | -0.040 (1927) | +0.008 (2139) | +0.099 (211) |
| V02 price >= $10 (P3) | -0.044 (2705) | -0.002 (2905) | +0.070 (293) |
| V03 1R >= 0.40% of price (P1/P21 intake, RW3) | -0.033 (2541) | +0.001 (2859) | +0.094 (281) |
| V04 cost filter 0.15 -> 0.10R (P18, RW5 intake) | -0.039 (2172) | +0.001 (2391) | +0.109 (243) |
| V05 window end 15:00->13:00 (P6) | -0.056 (2042) | +0.017 (2180) | +0.098 (211) |
| V06 window end 15:00->14:00 (P6) | -0.056 (2385) | -0.002 (2605) | +0.078 (241) |
| V07 start 09:50->10:30 (P7, RW3) | -0.040 (2576) | -0.005 (2808) | +0.067 (283) |
| V08 start 09:50->11:00 (P7) | -0.036 (1957) | -0.023 (2133) | +0.087 (243) |
| V09 refire on, cooldown 6 (P8) | -0.040 (2845) | -0.002 (3026) | +0.067 (295) |
| V10 heat <= -25 (P9) | -0.023 (976) | -0.027 (1227) | +0.159 (128) |
| V11 heat <= -15 (P9 looser) | -0.073 (5591) | +0.010 (5718) | +0.078 (560) |
| V12 buyPressure < -0.40 (P10) | -0.047 (1838) | -0.016 (1945) | +0.008 (193) |
| V13 RSI(14) 55-60 (P11 hi) | -0.041 (1482) | +0.004 (1701) | +0.072 (179) |
| V14 RSI(14) 58-65 (P11 lo) | -0.052 (2166) | -0.020 (2172) | +0.077 (210) |
| V15 gap <= -0.5% (P12) | -0.050 (1352) | +0.014 (1883) | +0.116 (211) |
| V16 gap <= -1.0% (P12) | -0.033 (776) | -0.002 (1202) | +0.135 (166) |
| V17 lots per symbol 3 -> 1 (P15) | -0.044 (2705) | -0.002 (2907) | +0.070 (293) |
| V18 per-setup latch -2R (P16) | -0.048 (2385) | +0.007 (2566) | +0.010 (230) |
| V19 stop 1.0 -> 1.25R (P24) | -0.027 (2705) | +0.002 (2907) | +0.067 (293) |
| V20 target 1.0 -> 0.8R (P25) | -0.041 (2705) | -0.007 (2907) | +0.078 (293) |
| V21 BE stop after +0.5R (P24 move) | -0.057 (2705) | -0.018 (2907) | +0.091 (293) |
| V22 max hold 120 min (P27) | -0.047 (2705) | -0.020 (2907) | +0.093 (293) |
| V23 flat 15:55 -> 15:00 (P27, no live knob) | -0.046 (2705) | +0.002 (2907) | +0.131 (293) |
| V24 gate: skip SPY > +0.20% since 09:50 (new, RW3/RW5) | -0.038 (2031) | +0.014 (2222) | +0.070 (231) |
| V25 gate: skip SPY > +0.30% since 09:50 (new) | -0.047 (2237) | +0.006 (2422) | +0.085 (259) |
| V26 price at/below VWAP (new sensor) | -0.051 (1435) | -0.016 (1895) | +0.094 (197) |
| C1 RSI 55-60 + 1R>=0.40% | -0.033 (1405) | +0.007 (1678) | +0.086 (174) |
| C2 RSI 55-60 + gap<=-1% | -0.045 (523) | +0.043 (779) | +0.134 (115) |
| C3 C1 + gap<=-1% | -0.051 (518) | +0.042 (775) | +0.134 (115) |
| C4 RSI 55-60 + heat<=-25 | -0.028 (512) | +0.024 (717) | +0.220 (72) |
| C5 C1 + end 13:00 | -0.037 (1034) | +0.033 (1228) | +0.140 (120) |
| C6 C3 + end 13:00 | -0.070 (404) | +0.101 (570) | +0.203 (75) |
| C7 C1 + SPY gate 0.20 (sibling) | -0.029 (1102) | +0.025 (1306) | +0.085 (143) |
| C8 C1 + start 10:30 (sibling) | -0.034 (1322) | +0.010 (1616) | +0.071 (169) |
| C9 C1 + SPY gate 0.20 + start 10:30 (sibling pack) | -0.032 (1032) | +0.027 (1254) | +0.067 (138) |
| C10 C3 + heat<=-25 | -0.019 (253) | +0.071 (406) | +0.261 (58) |
| C11 C1 + end 14:00 | -0.044 (1218) | +0.000 (1484) | +0.105 (140) |
| S1 RSI 55-58 + 1R>=0.40% | +0.013 (819) | +0.028 (1088) | +0.043 (120) |
| S2 RSI 55-61 + 1R>=0.40% | -0.028 (1642) | +0.009 (1928) | +0.092 (194) |
| S3 C1 + gap<=-0.75% | -0.042 (644) | +0.050 (934) | +0.158 (119) |
| D1 C5 + gap<=-0.5% | -0.072 (599) | +0.077 (843) | +0.196 (92) |
| D2 C5 + gap<=-0.75% | -0.054 (491) | +0.096 (685) | +0.235 (79) |
| D3 C5 with end 13:30 | -0.046 (1139) | +0.007 (1356) | +0.117 (130) |
| D4 C5 with RSI 55-61 | -0.034 (1211) | +0.035 (1421) | +0.145 (132) |
| D5 C5 with 1R>=0.35% | -0.037 (1070) | +0.029 (1239) | +0.143 (121) |
| D6 C5 without 1R floor (RSI 55-60 + end 13:00) | -0.052 (1092) | +0.029 (1246) | +0.118 (125) |
| D7 C5 without RSI band (1R>=0.40% + end 13:00) | -0.040 (1918) | +0.021 (2142) | +0.134 (200) |
| D8 C5 + SPY gate 0.20 (sibling) | -0.016 (808) | +0.048 (948) | +0.152 (99) |

| config | test | avg win | avg loss | median hold (min) | stop | target | time | up-day avg R (n) | flat (n) | down (n) |
|---|---|---|---|---|---|---|---|---|---|---|
| PARENT | replay | +0.798 | -0.764 | 121 | 29% | 35% | 36% | -0.031 (53) | -0.044 (53) | +0.087 (71) |
| PARENT | 2y | +0.790 | -0.842 | 100 | 33% | 35% | 32% | -0.249 (1860) | +0.008 (1855) | +0.157 (2190) |
| V05 window end 15:00->13:00 (P6) | replay | +0.843 | -0.833 | 154 | 31% | 41% | 28% | +0.050 (39) | -0.012 (46) | +0.200 (55) |
| V05 window end 15:00->13:00 (P6) | 2y | +0.839 | -0.911 | 113 | 37% | 39% | 24% | -0.259 (1512) | +0.028 (1353) | +0.190 (1568) |
| V13 RSI(14) 55-60 (P11 hi) | replay | +0.823 | -0.785 | 121 | 27% | 40% | 33% | +0.059 (35) | +0.087 (27) | +0.095 (53) |
| V13 RSI(14) 55-60 (P11 hi) | 2y | +0.794 | -0.834 | 96 | 33% | 35% | 32% | -0.267 (956) | -0.012 (1042) | +0.166 (1364) |
| D8 C5 + SPY gate 0.20 (sibling) | replay | +0.872 | -0.813 | 126 | 26% | 49% | 25% | +0.103 (16) | +0.303 (18) | +0.165 (42) |
| D8 C5 + SPY gate 0.20 (sibling) | 2y | +0.849 | -0.893 | 107 | 36% | 41% | 23% | -0.324 (415) | +0.005 (572) | +0.206 (868) |
| C5 C1 + end 13:00 | replay | +0.855 | -0.854 | 136 | 29% | 46% | 25% | +0.117 (27) | +0.205 (22) | +0.165 (42) |
| C5 C1 + end 13:00 | 2y | +0.842 | -0.903 | 107 | 36% | 40% | 23% | -0.265 (741) | +0.017 (707) | +0.217 (934) |

Passing parts NOT shipped: V02 / V17 (no effect), V06 / V07 / V08 / V20 / V26 (meet only), V10 / V16 (TRAIN or w/o-best-day weaker in
combos), V23 / flat 15:00 (no per-setup live knob), C6 / D1 / D2 (gap depth: higher avg but TRAIN worse than the parent, thin),
C4 / C10 (heat <= −25: 48-59 replay trades, replay w/o best day below the parent's), S1 (RSI 55-58: replay +0.053 only),
D7 (no RSI band: 2-year worst day −23.4R). FAIL: V01 ADV $150M, V04 cost 0.10R, V09 refire, V11 heat <= −15, V12 bp < −0.40,
V14 RSI 58-65, V15 gap <= −0.5% alone, V18 −2R latch, V19 stop 1.25R, V21 breakeven at +0.5R, V22 max hold 120, V24 / V25 SPY gate alone.

## Pending config change — "ready to deploy after close" (NOT applied; built during market hours)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective session 2026-11-17. One copy only: **WB3**
(it contains WB1 and WB2). The parent stays in On Deck, unchanged (Workbench rule 1).
Destination: **Testing E** (`config/account_testinge.yaml`) — a testing account, not the parent's (On Deck). Not Testing A (tonight's
MF2-open-rsimidhi-flowsell-FD-WB3 is RW1's own lineage source), not Testing B (runs MF2-open-rsimidhi-flowsell), not Testing C (RW3-FD-WB3:
same heat / buyPressure / gap sensors), not Testing F (RW7, the near-twin of RW1). Testing E's book matches the bench (no per-setup latch,
CF 0.15; cap 50 lots per setup — WB3 averages ~4 trades a day, never near it). If the main session puts several Workbench copies in
Testing E tonight (CWT09-WB4, L3-rsi5hi-FD-WB4), it decides their order; fallback account: Testing D.
1. Module: copy `research/workbench/{S}/modules/{S}-WB3.py` to `research/bdi/fullday/{S}-WB3.py`.
2. `config/account_testinge.yaml`, under `strategies:` add
   ```yaml
   {S}-WB3:
     # Workbench copy of {S} (On Deck), Mechanic 2026-11-16: RSI(14) 55-60 + 1R >= 0.40% of price + entries to 13:00
     # + skip when SPY is up > +0.20% since 09:50; research/workbench/{S}/RESULTS.md. From session 2026-11-17.
     enabled: true
     type: lab
     module: research/bdi/fullday/{S}-WB3.py
     min_adv: 95000000
     window: [950, 1300]
     context: [spy_fo]
     scale_out_r: null
     tags: [workbench, "parent:{S}"]
   ```
   (refire stays off, as the parent) and put `{S}-WB3` FIRST in `live.setup_order` (rule 5).
3. `config/setup_names.yaml`: `{S}-WB3: {{name: "Gap-Down Bounce Short, Heavy Selling — WB3: RSI 55-60 + 1R >= 0.40% + to 13:00 + SPY-since-09:50 gate", side: short, what: "09:50-13:00: stock gapped down, bearish heat <= -20, heavy net selling, RSI(14) bounces to 55-60 and 1R (0.25 x daily ATR) is at least 0.40% of price; short the bounce unless SPY is up more than 0.20% since 09:50; target / stop 1R, flat 15:55."}}`
4. `research/ledger.jsonl`: id `2026-11-16-wb-rw1-wb3`, effective 2026-11-17, title "Workbench copy {S}-WB3 added to Testing E,
   first in setup_order (Mechanic pass)", patch `{{"strategies.{S}-WB3 (testinge)": [null, "added, enabled"], "live.setup_order (testinge)": ["...", "WB3 first"]}}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5"; then `python -m mcf.research.ledger check`.
5. Smoke test (module needs the `spy_fo` context column and the 09:50 bar; without them the mask fires nothing — fail safe),
   `python -m mcf.report.assignments` (docs/live/assignments.json in the same commit), `pytest -q`, commit, push after 16:05 ET (setup-freeze).

Files: DIAGNOSIS.md, variants.jsonl, modules/, *.yaml stubs (no account loads them), code/ (decl.py, sim_rw1.py, load.py, go.py,
report.py, live_ana.py, cand2y.py, paths2y.py, fetch_replay.py, etb.py), results.csv, extras.csv, component_analysis.txt, PNGs
(engine, worst1-5, best1-5), BLUEPRINT_worst5.md / BLUEPRINT_best5.md.

Educational only — not financial advice.
