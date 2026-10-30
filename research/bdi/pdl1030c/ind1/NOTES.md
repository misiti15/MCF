# pdl1030c / ind1: one added indicator (Move from open, VWAP position/cross) on the two demoted PDL longs

*Educational only — not financial advice.* These are backtests on the open two-year history. Nothing here was traded on paper or live.

**Result: 0 of 13 pre-declared configurations pass.** No row was added after scoring, and no module was written.
- Lineage CWT14 PDL: N = 121,635 + 5 x 13 = 121,700. The BAR90 bar is t >= 4.355.
- Data: TRAIN = 2024-10 and 2025-03..12. VALID = 2026-01..03 and 2026-07..09-15. That is 348 sessions.
  The HOLD months and the locked block were never loaded (asserts in build.py and score.py).
- **No row is positive on both TRAIN and VALID. No row reaches t > 0. Every row loses in total.** That is why the best-day and
  top-5-day shares are blank: they are undefined when total R is negative.
- Parity is exact.
  - p05: -0.0677 / -0.0675, n 53,326, 153.2/session.
  - p05-lowvol: -0.0951 / -0.0948, TV -0.0950, n 35,238, 101.3/session.
  - p05 S3: -0.0210 / -0.0173 (matches swarm15).

## Overlap skipped (already scored in earlier swarms)
- rs vs SPY >= +0.5% (Q02/Q06/Q11/Q14).
- Stock vd >= 0 and >= +0.5% (Q01/Q05/Q09/Q10/Q14/Q15/Q16).
- SPY vs VWAP (tape-flip, combo).

## Every row (avg R after costs; t is day-clustered over TRAIN+VALID)
| id | added indicator (exits) | TRAIN | VALID | t | /sess | % parent kept | WF% | up-day | down-day | w/o best day | w/o top-5 days |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F1-p05 | fromOpen > 0 (parent) | -0.0574 | -0.0608 | -5.23 | 43.9 | 28.6 | 6 | -0.006 | -0.131 | -0.063 | -0.074 |
| F2-p05 | fromOpen > +2% (parent) | -0.0238 | -0.0239 | -1.09 | 3.7 | 2.4 | 35 | +0.024 | -0.132 | -0.034 | -0.058 |
| F3-p05 | fromOpen < -2% (parent) | -0.0602 | -0.0517 | -4.62 | 14.5 | 9.5 | 0 | +0.013 | -0.097 | -0.058 | -0.063 |
| V1-p05 | VWAP reclaim on signal bar (parent) | -0.0492 | -0.0717 | -4.64 | 28.2 | 18.4 | 12 | -0.008 | -0.116 | -0.062 | -0.070 |
| V2-p05 | below VWAP, room >= 0.5 ATR (parent) | -0.1147 | -0.0685 | -2.31 | 3.4 | 2.2 | 24 | -0.067 | -0.112 | -0.108 | -0.126 |
| S-p05 | V1 on S3 + cost5 | +0.0014 | -0.0057 | -0.24 | 9.5 | 6.2 | 53 | +0.032 | -0.044 | -0.004 | -0.009 |
| F1-lv | fromOpen > 0 (parent) | -0.0925 | -0.0973 | -5.26 | 29.3 | 28.9 | 6 | -0.004 | -0.219 | -0.101 | -0.118 |
| F2-lv | fromOpen > +2% (parent) | -0.0507 | -0.0058 | -1.13 | 2.3 | 2.3 | 41 | +0.012 | -0.150 | -0.046 | -0.076 |
| F3-lv | fromOpen < -2% (parent) | -0.0697 | -0.0739 | -3.80 | 8.3 | 8.2 | 18 | +0.028 | -0.131 | -0.075 | -0.087 |
| V1-lv | VWAP reclaim on signal bar (parent) | -0.1139 | -0.1246 | -6.87 | 16.5 | 16.3 | 6 | -0.022 | -0.230 | -0.121 | -0.131 |
| V2-lv | below VWAP, room >= 0.5 ATR (parent) | -0.1341 | -0.2045 | -4.53 | 1.5 | 1.5 | 12 | -0.112 | -0.170 | -0.161 | -0.179 |
| B-lv | S3 + cost5, no indicator (reference) | -0.0072 | -0.0188 | -1.77 | 35.5 | 35.1 | 29 | +0.045 | -0.069 | -0.014 | -0.019 |
| S-lv | F1 on S3 + cost5 | -0.0037 | -0.0193 | -0.95 | 10.9 | 10.8 | 29 | +0.043 | -0.092 | -0.014 | -0.024 |

Parents for comparison: p05 is -0.068 at 153/session; p05-lowvol is -0.095 at 101/session.
The p05 S3 + cost5 base is symbol-quality Q08: -0.0028 / -0.0084, 54.3/session. It was not re-counted here.

The S rows were picked by the rule fixed in PLAN.md: among the parent-exit rows with >= 25/session, the highest TRAIN avg R.
- For p05 that was V1. F1 was the other row with at least 25/session.
- For p05-lowvol it was F1, the only row with at least 25/session.

## What it means
- **Neither indicator adds an edge.** On the parent exits the best rows that keep volume are F1-p05 at 44/session and V1-p05 at 28/session.
  They lift avg R by only ~0.01R and stay at about -0.05..-0.06.
- **Strong up-from-open (F2, > +2%) is the only real lift**, to about -0.024. But it keeps only 2-4 trades/session, and it is still negative.
- **Washout-then-reclaim (F3) and LIQ-style room to VWAP (V2) are no better, or worse.**
- **On the lowvol parent, the VWAP reclaim hurts** (-0.118). A low-volume reclaim through VWAP is the weakest version.
- **The problem is the same one the earlier swarms found.** Every row makes a little on SPY up days and loses on SPY down days
  (-0.09..-0.23R). Neither stock-level indicator, known at entry, removes that market beta.
- **On S3 + cost5 the indicator adds almost nothing.**
  - S-p05 is -0.002 TV at 9.5/session, against the base's -0.005 at 54/session.
  - S-lv is -0.011 at 11/session, against B-lv's -0.013 at 36/session.
  - Volume is cut by 70-80% for a gain within noise.
- **One-big-day / top-5 check:** every row loses in total, so no record here is being carried by its best day or best 5 days.
  Removing the top 5 sessions makes each row 0.005-0.03R worse, which is the expected small amount. The losses are broad.

## Files
- PLAN.md: the pre-declaration.
- build.py: the symbol-quality build plus p05lv and the fo / vd_prev / vwap_room_atr fields.
  Cache: scratchpad pdl1030c/ind1/cache, about 5 MB.
- score.py writes results.csv and score_out.txt.
- Re-run: `python research/bdi/pdl1030c/ind1/build.py && python research/bdi/pdl1030c/ind1/score.py`.

*Educational only — not financial advice.*
