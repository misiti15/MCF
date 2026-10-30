# pdl1030c / ind4: one added indicator (Gap, 5-min SMA50) on the two demoted PDL longs

*Educational only — not financial advice.* Backtests on the open two-year history only; nothing here was traded on paper or live.

**Result: 0 of 14 pre-declared configurations pass.** No row was added after scoring; no module written.
- Lineage CWT14 PDL: N = 121,635 + 5 x 14 = 121,705 -> BAR90 t >= 4.355.
- TRAIN = 2024-10, 2025-03..12; VALID = 2026-01..03, 2026-07..09-15 (348 sessions). HOLD months and the locked block never loaded (asserts).
- Parity exact: p05 -0.0677 / -0.0675 (n 53,326, 153.2/session); p05-lowvol -0.0951 / -0.0948, TV -0.0950 (n 35,238, 101.3/session);
  p05 S3 -0.0210 / -0.0173. Base refs re-printed for context only (not counted): Q08 -0.0028 / -0.0084; ind1 B-lv -0.0072 / -0.0188.
- **No row is positive on both TRAIN and VALID; every row loses in total**, so best-day and top-5-day shares are undefined (blank).
  "w/o best day" and "w/o top-5 days" are still given: in every row removing the best day(s) makes the loss *worse*, i.e. the record is
  not one big day hiding a loss elsewhere — it is a broad, consistent loss lifted slightly by a few good up-days.

## Every row (avg R after costs; t day-clustered TRAIN+VALID; kept = % of the parent's trades)
| id | added indicator | TRAIN | VALID | t | /sess | kept | WF% | up-day | down-day | w/o best day | w/o top-5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G1-p05 | gap <= -2.657% | -0.0055 | -0.0348 | -0.93 | 7.0 | 4.6 | 29 | +0.041 | -0.117 | -0.031 | -0.047 |
| G2-p05 | gap > 0 | -0.0813 | -0.0725 | -8.50 | 57.1 | 37.2 | 6 | -0.016 | -0.126 | -0.080 | -0.085 |
| G3-p05 | gap_atr <= -0.41 | -0.0433 | -0.0443 | -3.24 | 20.9 | 13.6 | 18 | +0.013 | -0.124 | -0.048 | -0.060 |
| M1-p05 | close above SMA50 | -0.0644 | -0.0759 | -4.07 | 13.0 | 8.5 | 12 | -0.005 | -0.169 | -0.076 | -0.095 |
| M2-p05 | SMA50 cross up on signal bar | -0.0957 | -0.1078 | -5.20 | 5.8 | 3.8 | 6 | -0.031 | -0.195 | -0.107 | -0.122 |
| M3-p05 | close below SMA50 | -0.0680 | -0.0668 | -9.41 | 140.3 | 91.5 | 12 | -0.009 | -0.121 | -0.069 | -0.072 |
| S-p05 | S3 + cost5 + M3 (rule pick) | -0.0028 | -0.0084 | -1.18 | 49.3 | 32.2 | 41 | +0.032 | -0.039 | -0.006 | -0.009 |
| G1-lv | gap <= -2.657% | -0.0590 | -0.0637 | -1.93 | 4.4 | 4.4 | 24 | +0.043 | -0.240 | -0.071 | -0.105 |
| G2-lv | gap > 0 | -0.1143 | -0.0997 | -8.03 | 36.9 | 36.5 | 12 | -0.013 | -0.184 | -0.112 | -0.119 |
| G3-lv | gap_atr <= -0.41 | -0.0701 | -0.0884 | -3.53 | 14.3 | 14.1 | 12 | +0.017 | -0.216 | -0.085 | -0.113 |
| M1-lv | close above SMA50 | -0.0912 | -0.1045 | -3.89 | 8.8 | 8.7 | 6 | +0.002 | -0.246 | -0.106 | -0.132 |
| M2-lv | SMA50 cross up on signal bar | -0.1029 | -0.1204 | -3.93 | 4.2 | 4.1 | 6 | +0.005 | -0.262 | -0.119 | -0.141 |
| M3-lv | close below SMA50 | -0.0954 | -0.0940 | -8.45 | 92.5 | 91.3 | 12 | +0.001 | -0.184 | -0.097 | -0.104 |
| S-lv | S3 + cost5 + M3 (rule pick) | -0.0071 | -0.0177 | -1.64 | 32.1 | 31.7 | 29 | +0.048 | -0.069 | -0.014 | -0.019 |

## What it shows
- **Gap.** A deep gap down into the PDL (G1, the L3 cut) is the least-bad filter on TRAIN (p05 -0.006) but VALID is -0.035 and it keeps
  only 7/session (4.6% of trades) — far under the 25 floor. The ATR-scaled cut (G3) is in between (-0.044, 21/session).
  Opened above the prior close then swept the PDL (G2) is worse than the parent on both setups. Same picture as symbol-quality Q04/Q13:
  gap-down names lean a little better, but only at low volume, and the gain is all up-day beta (up-day +0.04, down-day -0.12).
- **SMA50.** Every SMA50 rule is worse than or equal to the parent. Reclaim bars above the SMA50 (M1) or crossing it (M2) lose more,
  especially on down sessions (-0.17..-0.26). 91% of reclaims are below the SMA50 (M3), so M3 is almost the parent itself.
- **S rows.** The pre-declared pick rule (highest TRAIN avg R at >= 25/session) chose M3 for both setups, so S-p05 / S-lv reproduce
  the S3 + cost5 bases (Q08 / B-lv) at ~32% of the parent's trades: about -0.005 / -0.012R, not positive, t far below 4.355.
- Conclusion matches pdl1030: the signal has ~0 gross edge plus market beta; neither the gap nor the SMA50 separates winners before
  entry at a volume that matters. Nothing to promote; both setups stay in the Graveyard.

## Files
PLAN.md (pre-declaration), build.py (ind1/build.py + gap, gap_atr, sma50 fields; cache in scratch pdl1030c/ind4/cache, ~3 MB),
score.py -> results.csv, score_out.txt. Re-run: `python research/bdi/pdl1030c/ind4/build.py && python research/bdi/pdl1030c/ind4/score.py`.

*Educational only — not financial advice.*
