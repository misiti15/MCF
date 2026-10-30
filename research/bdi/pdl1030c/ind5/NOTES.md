# pdl1030c / ind5: heat and relative volume added to the two demoted PDL longs (results)

*Educational only — not financial advice.* Research only. Nothing committed; no config/, mcf/, ledger or backlog writes.

Indicators: **MarcoFlow heat** (composite) and **Relative volume** (volumeRatio cross, 3-bar volume climax, rvol_day).
Pre-declared in PLAN.md; **14 configs scored**, all reported (results.csv, score_out.txt). N = 121,705, BAR90 t >= 4.355.
Parity exact: p05 -0.0677 / -0.0675 (153.2/session), p05lv TV -0.0950 (101.3/session); S3 refs -0.0196 / -0.0272.
Overlap skipped: volumeRatio >= 1.5 on the signal bar (symbol-quality Q03/Q07/Q12/Q15/Q17); vr < 1 on the poke = p05lv itself.
TRAIN+VALID only; HOLD months and the locked block never loaded (asserts).

## Result: 0 of 14 pass. No row has avg R > 0 on both splits.
| id | rule | TRAIN | VALID | t | /session | kept | WF |
|---|---|---|---|---|---|---|---|
| H1-p05 | heat >= +20 | -0.072 | -0.106 | -5.87 | 15.3 | 10% | 12% |
| H2-p05 | heat > -20 | -0.069 | -0.070 | -9.68 | 140.9 | 92% | 6% |
| H3-p05 | heat <= -30 | -0.065 | -0.063 | -2.77 | 2.9 | 2% | 24% |
| R1-p05 | vr crosses 2.0 | -0.063 | -0.080 | -3.39 | 7.3 | 5% | 29% |
| R2-p05 | vol climax >= 3 (3 bars) | -0.047 | -0.117 | -4.17 | 8.2 | 5% | 24% |
| R3-p05 | rvol_day >= 0.84 | -0.075 | -0.079 | -8.72 | 54.1 | 35% | 0% |
| S-p05 | S3 + cost5 + heat > -20 | -0.003 | -0.007 | -1.19 | 47.6 | 31% | 41% |
| H1-lv | heat >= +20 | -0.064 | -0.188 | -4.38 | 4.4 | 4% | 6% |
| H2-lv | heat > -20 | -0.096 | -0.100 | -8.66 | 91.0 | 90% | 6% |
| H3-lv | heat <= -30 | -0.056 | -0.066 | -1.91 | 2.5 | 2% | 29% |
| R1-lv | vr crosses 2.0 | -0.076 | -0.088 | -2.37 | 2.0 | 2% | 24% |
| R2-lv | vol climax >= 3 (3 bars) | -0.070 | -0.146 | -2.73 | 1.6 | 2% | 18% |
| R3-lv | rvol_day >= 0.84 | -0.121 | -0.117 | -8.55 | 24.2 | 24% | 0% |
| S-lv | S3 + cost5 + heat > -20 | -0.010 | -0.019 | -1.95 | 30.0 | 30% | 29% |

Base refs (not counted, already scored): p05 S3+cost5 (Q08) -0.0028 / -0.0084, 54.3/session; p05lv S3+cost5 (ind1 B-lv)
-0.0072 / -0.0188, 35.5/session. The S rows add nothing over those bases (S-p05 TRAIN slightly worse, VALID slightly better; S-lv about equal).

## Read
- Heat: the "not bearish" gate keeps ~90% of trades and changes nothing; bullish heat >= +20 is *worse* (chasing strength into a PDL
  reclaim); the washed-out heat <= -30 side is the least bad but only ~3/session and still negative.
- Relative volume: high day activity (rvol_day >= 0.84) is clearly worse (0% months positive). Volume spikes (vr cross 2, climax >= 3)
  shrink to 2-8/session with no gain.
- Every row loses on SPY-down days and is flat-to-small-positive on up days: the same market-beta picture as pdl1030/why.
- Best-day check: every row's total R is negative, so "share of total R" is undefined; avg R without the best day and without the
  top-5 days is always more negative than the full avg (e.g. S-p05 -0.0049 -> -0.0057 w/o best day -> -0.0081 w/o top 5; top-5 days
  = +46.6R against a -81.9R total). No record here is carried by one day, because there is no positive record.
