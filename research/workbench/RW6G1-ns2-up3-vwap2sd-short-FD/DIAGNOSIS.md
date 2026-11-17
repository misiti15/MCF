# Diagnosis — Big Gainer Fade, VWAP Band Guard (all day) `RW6G1-ns2-up3-vwap2sd-short-FD` (Graveyard)
Educational only — not financial advice. Mechanic, 2026-11-16 (built after the close: research files only, no config change, no deploy).

Engine: `RW6G1-ns2-up3-vwap2sd-short-FD_engine.png` (P1..P26, blueprint `RW6G1-ns2-up3-vwap2sd-short-FD.md`).
Live evidence: all 63 live trades (On Deck/Testing 1 30 trades −0.17R to 11-03; Graveyard 33 trades +0.15R from 11-04),
19 sessions 2026-10-13..11-13, avg −0.003R, win 49%, avg R w/o best day −0.093 (best day 11-09: 18 trades +4.0R), and
110 live signals. Leaderboard row at job start: rank 22, 63 trades / 19 sessions, −0.003R. Live R mixes the old cost
allowance (to 11-11) with LR8 (from 11-12) and two books: 7 rule changes sit inside the window (10-20 twin rule / Testing
−2R latch, 10-23 ST-A latch off in Testing, 10-30 CF stop-cost filter in Testing, 11-04 move to Graveyard (−2R latch, 25
then 75 lots), 11-12 Graveyard REPV-11/12 sizing, 11-12 LR1 / LR5). Live numbers DIAGNOSE only; the pass decision uses the
identical backtests in RESULTS.md (owner 2026-11-16). With 63 live trades the live split is thin, so the 2-year backtest
(1,744 parent trades) carries the weight — said plainly here.

What the setup does: short a stock that is up > 3% from the open when its 5-min close crosses back ABOVE the 5-min SMA50
with RSI(14) >= 60, unless an excursion above VWAP + 2 SD is unresolved; refire every qualifying bar (cooldown 1),
1R = 0.25 x daily ATR, target 1R / stop 1R, flat 15:55.

## The 5 worst and 5 best live trades
| Trade (chart) | What happened | Part that caused it | Catalogue part | What WB3 does to THIS trade |
|---|---|---|---|---|
| MDGL 10-20 −1.27R (`_worst1_MDGL_2026-10-20.png`) | Signal 14:50, short 14:51 @ 465.20; never went green (MFE −0.06R), late-day squeeze, P23 stop 15:42 | P9-P12 sensors: the reclaim bar sat only +0.34 SD over VWAP (a shallow reclaim in a trending name); ADV $121M | Sensors / Intake | **not taken** (z 0.34 < 0.5, ADV < $150M) |
| LUNR 10-15 −1.14R (`_worst2_LUNR_2026-10-15.png`) | Signal 10:55, short @ 11.02 (slip −41 bps), MFE +0.19R, stop 11:06 | P6/P7 morning entry: the 09:50-11:00 reclaim is often the trend resuming | Timer / window | **not taken** (before 11:00; ADV $115M) |
| DKNG 10-19 −1.08R (`_worst3_DKNG_2026-10-19.png`) | Signal 14:25, MFE 0.00R, stop 15:42 | shallow reclaim (z 0.38) | Sensors | **not taken** (z < 0.5) |
| TEM 11-09 −1.07R (`_worst4_TEM_2026-11-09.png`) | Signal 14:30, short 14:32 @ 84.23, MFE 0.00R, stop 15:31 @ 85.67 (stacked 11-09 afternoon) | P10 intake: gapped up +2.2% AND +3% from the open — a gap-and-go runner | Intake (gap) | **not taken** (gap > +2%) |
| NTSK 10-29 −1.06R (`_worst5_NTSK_2026-10-29.png`) | Signal 13:40, MFE +0.21R, stop 14:33 | shallow reclaim (z 0.22), thin name (ADV $120M) | Sensors / Intake | **not taken** |
| BMNR 11-09 +1.44R (`_best1_BMNR_2026-11-09.png`) | 14:40, target at 15:55 (fill slip −37 bps in our favour) | works as designed | — | kept |
| WWD 11-03 +1.16R (`_best2_WWD_2026-11-03.png`) | 14:05, target 15:50 | works; z 0.45 at the signal bar | Sensors | **dropped** (z 0.45 < 0.5) — a give-back |
| MDB 10-29 +1.06R (`_best3_MDB_2026-10-29.png`) | 12:50, target 13:51 | works; z 0.32 | Sensors | **dropped** (z 0.32) — a give-back |
| SMR 10-22 +1.01R (`_best4_SMR_2026-10-22.png`) | 12:25, target 14:01 | works as designed | — | kept |
| APH 11-12 +0.94R (`_best5_APH_2026-11-12.png`) | 11:00, MAE −0.77R, target 15:52 | works as designed | — | kept |

WB3 drops all 5 worst live trades and keeps 3 of the 5 best. Across all 63 live trades: WB3 would have kept 22 (+0.188R
avg, +4.1R) and dropped 41 (−0.105R avg, −4.3R) — indicative only (ADV from today's universe snapshot; 3 trades had no
replay frame).

## Across all trades (which part is behind the losses)
- **Sensors — how stretched the reclaim is (P9/P12, new layer).** The reclaim bar's distance above VWAP in VWAP-SD units
  (z, same VWAP / SD the band guard uses): live z <= 0.5 31 trades −2.9R, z 0.5-1.5 22 trades +2.5R; replay z <= 0.5
  45 trades −4.1R, 0.5-1.5 30 trades +5.4R; 2-year z <= 0.5 960 trades −102R (−0.11R) vs > 1.0 303 trades −0.9R (−0.00R). A cross back over
  the SMA50 while barely above VWAP is a trend resuming, not an exhausted gainer. → require close >= VWAP + 0.5 SD (WB2).
- **Timer / window start (P6/P7).** 2-year entries 09:50-11:00 −0.122R (164 trades); the morning reclaim is usually the
  trend; and the parent's worst 2-year day (2025-04-07, −28.8R, 33 trades) is a crash-and-rebound morning. → start 11:00 (WB1).
- **Intake — liquidity (P2) and gap (new).** 2-year ADV $95-150M −0.171R (402 trades) vs > $300M −0.02/−0.07R; opening gap
  > +5% −0.31R (79), and in the refined copy gap > +2% −0.15/−0.50R — a name that gapped up AND runs 3% more from the open is
  a gap-and-go runner (TEM 11-09). → ADV >= $150M + gap <= +2% (in WB3).
- **Gates / day type.** 2-year by SPY open→close: up days −0.206R (613 trades), flat −0.060, down +0.045 — the short fades
  bleed on up days, as expected. The SPY-since-09:50 gate (owner rule: measured after 09:50) helps the 2-year (V24 −0.064,
  V25 −0.047) but the live sessions disagree (11-09, SPY +0.4..1.0% since 09:50, was the best live day: 18 trades +4.0R), so
  both gate copies fail the replay test. WB3 lifts up days from −0.206 to −0.078R without a gate.
- **Exhaust (P23/P24/P26).** 59% of live trades end at the 15:55 flatten (avg +0.04R, MFE +0.47R); median hold 82 min. But
  tighter exits do not help in the backtests: target 0.8R / 0.6R, BE after +0.5R, max hold 60 / 120, stop 1.25R are all
  flat-to-worse in the 2-year (RESULTS V18-V23). The losses are entry-quality losses, not exit losses (stopped trades had
  MFE +0.20R live / +0.27R 2-year — they were wrong from the start).
- **Refire / caps (P8, P14-P16).** Refire off or cooldown 6 change little (−0.082 / −0.081 vs −0.084 2-year). The −2R
  latch interacts with stacking: on 2025-04-07 the parent opened 33 shorts before realized losses hit −2R (−28.8R day);
  without the latch (V15 / the Testing book T0) that same day is +47.2R — the whole 2-year record of the testing-book parent
  rests on that one day. WB3 starts at 11:00 and makes 04-07 its best day (+19.7R on 43 trades in the Graveyard book, +16.8R on 40 in the Testing book).

## Every part, P1..P26
| Part | Setting | Inspected | Result |
|---|---|---|---|
| P1 account universe | ADV >= $5M, ATR >= 1% | 2y intake is ADV >= $95M; universe not binding | no change |
| P2 setup ADV floor | $95M | V01 $150M | PASS alone (2y −0.084 → −0.051); kept in WB3 |
| P3 price floor | $5 | V02 $10 | FAIL (replay −0.038) |
| P4 earnings blackout | 4 days | not testable in the frames (universe-level) | no change |
| P5 short borrow | shortable + ETB | 22% of live signals blocked; 2y uses names ETB on >= 90% of snapshots | no change |
| P6 window | 09:50-15:00 | V03 end 14:00 (FAIL), V04 start 11:00 (PASS) | start 11:00 kept in WB3 |
| P7 no entries before | 09:50 | same as V04 | — |
| P8 refire | cooldown 1 | V05 off, V06 cooldown 6 | both PASS small; not kept (no gain in combos, C5) |
| P9 SMA50 cross | cross above on this bar | the cross itself is the setup; quality judged by z (WB2) and HOD distance (S1, mixed) | z layer added |
| P10 fromOpen > 3 | 3% | V07 > 4 (FAIL 2y), V08 > 2.5 (FAIL 2y), V09 <= 8 cap (PASS, small) | no change |
| P11 RSI(14) >= 60 | 60 | V10 >= 65 (FAIL replay), V11 >= 55 (FAIL) | no change |
| P12 VWAP +2 SD guard | k = 2 | V12 2.5 (FAIL worst day), V13 1.5 (FAIL), V14 off (PASS alone, C6 combo no better) | owner's guard kept |
| P13 full-day note | — | covered by P6 | — |
| P14 open lots per setup | 75 (Graveyard) | max concurrent rarely binding; Testing book cap 50 scored (T0) | — |
| P15 lots per symbol | 3 | backtest-only part; not needed (refire tests) | — |
| P16 per-setup −2R latch | Graveyard | V15 off (FAIL replay); D4 copy + latch off (2y −0.026 vs −0.015) | kept (account-level anyway) |
| P17 account stop | −120R | not binding | — |
| P18 quote / spread checks | <= 30 bps | live-only (4% of signals); not modelled | — |
| P19 entry | market at signal-bar close | as modelled | — |
| P20 1R | 0.25 x ATR | V16 0.30 (FAIL worst day), V17 cost/R <= 0.15 (FAIL replay) | no change |
| P21 / P22 sizing / max position | — | do not change R | — |
| P23 stop | 1R | V18 1.25R (FAIL), V21 BE after +0.5R (PASS, flat) | no change |
| P24 target | 1R | V19 0.8R (FAIL), V20 0.6R (PASS alone; C4 combo worse 2y −0.085) | no change |
| P25 scale-out | none | — | — |
| P26 time exit | 15:55 | V22 60 min (FAIL), V23 120 min (PASS small), D3 combo (2y worse) | no change |
| NEW sensor | — | V26 close >= VWAP (FAIL worst day), V27 z >= 0.5 (PASS), S1 HOD <= 0.5 ATR (FAIL replay), S3 volumeRatio >= 0.8 (PASS) | z >= 0.5 kept (WB2, WB3) |
| NEW intake | — | S2 gap >= −2% (PASS), D1 gap <= +5% (PASS), D2 gap <= +2% (PASS, best) | gap <= +2% kept (WB3) |
| NEW gate | — | V24 / V25 / C9 / E1 SPY after-09:50 gates | FAIL replay or lose the 04-07 day |

Candidate tweaks chosen: WB1 start 11:00 (P6), WB2 close >= VWAP + 0.5 SD (new sensor), WB3 = both + ADV >= $150M + gap
<= +2% (combo). Full numbers: RESULTS.md.
