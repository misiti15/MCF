# pdl1030b (PDL-1b): beta-hedged PDL longs and an early-break (09:35-09:45) signal

*Educational only — not financial advice.* Backtest only (open two-year history); nothing here is paper or live.

**Result: 0 of 23 pre-declared configurations pass. 1 post-hoc sensitivity row (disclosed below) was also counted, so 24 configurations in total.
Nothing was verified, and no module was written.**
Lineage: CWT14 PDL (no new lineage claimed, which is the conservative choice). N = 121,611 + 24 = 121,635. BAR90 t >= 4.355.
TRAIN = 2024-10 and 2025-03..12. VALID = 2026-01..03 and 2026-07..09-15. There are 348 sessions.
The HOLD months and the locked block were never loaded; asserts in build.py, score.py and diag.py enforce this.
Parent parity is exact: A0 = p05 -0.0677 / -0.0675 with n 53,326. The p05 and p10 S3 rows match combo's cache trade for trade.

## Failures first: every row (avg R after costs; t is day-clustered over TRAIN+VALID)
| id | rule | TRAIN | VALID | t | /sess | WF% | up-day | down-day | w/o best day |
|---|---|---|---|---|---|---|---|---|---|
| A0 | p05 parent, no hedge (parity) | -0.0677 | -0.0675 | -9.51 | 153.2 | 6 | -0.009 | -0.124 | -0.069 |
| A1 | p05 + SPY beta1 | -0.1789 | -0.1377 | -31.0 | 153.2 | 0 | -0.163 | -0.164 | -0.165 |
| A2 | p05 + SPY beta20 | -0.1682 | -0.1270 | -28.5 | 153.2 | 0 | -0.145 | -0.160 | -0.154 |
| A3 | p05 S3 + cost5 (ref) | -0.0028 | -0.0084 | -1.21 | 54.3 | 41 | +0.030 | -0.039 | -0.006 |
| A4 | A3 + SPY beta1 | -0.0267 | -0.0197 | -8.54 | 54.3 | 0 | -0.018 | -0.029 | -0.024 |
| A5 | A3 + SPY beta20 | -0.0307 | -0.0199 | -9.52 | 54.3 | 0 | -0.027 | -0.025 | -0.026 |
| A6 | p05 S3 + SPY beta20 | -0.0492 | -0.0321 | -20.3 | 153.2 | 0 | -0.041 | -0.044 | -0.043 |
| A7 | p05 + cost5 + SPY beta20 | -0.1130 | -0.0795 | -14.9 | 54.3 | 0 | -0.095 | -0.100 | -0.099 |
| A8 | A3 + QQQ beta1 | -0.0298 | -0.0204 | -9.49 | 54.3 | 0 | -0.027 | -0.025 | -0.026 |
| A9 | A3 + QQQ beta20 | -0.0286 | -0.0173 | -8.83 | 54.3 | 0 | -0.022 | -0.025 | -0.024 |
| A10 | p10 S3 + cost5 + SPY beta20 | -0.0404 | -0.0342 | -8.37 | 29.4 | 0 | -0.038 | -0.037 | -0.038 |
| B1 | early reclaim long, p05 exits | -0.0907 | -0.0900 | -9.13 | 97.8 | 0 | -0.050 | -0.138 | -0.092 |
| B2 | B1 S3 + cost5 | -0.0029 | -0.0089 | -0.69 | 17.7 | 47 | +0.044 | -0.062 | -0.008 |
| B3 | B2 + SPY beta20 | -0.0209 | -0.0292 | -3.77 | 17.7 | 6 | -0.014 | -0.038 | -0.027 |
| B4 | B1 target 1R, no scale | -0.1288 | -0.1506 | -6.82 | 97.8 | 6 | -0.015 | -0.280 | -0.142 |
| B5 | early continuation short 0.05 (opened above PDL) | -0.1369 | -0.0601 | -9.01 | 69.6 | 6 | -0.153 | -0.058 | -0.109 |
| B6 | B5 at 0.10 ATR | -0.1393 | -0.0661 | -8.98 | 53.4 | 6 | -0.157 | -0.062 | -0.113 |
| B7 | B5 S3 + cost5 | -0.0061 | +0.0122 | +0.43 | 12.4 | 47 | -0.047 | +0.054 | +0.002 (best day 45% of R) |
| B8 | B7 + SPY beta20 (long SPY) | -0.0270 | -0.0148 | -3.26 | 12.4 | 12 | -0.039 | -0.002 | -0.022 |
| B9 | B5 target 1R, no scale | -0.1702 | -0.0946 | -6.63 | 69.6 | 6 | -0.269 | -0.007 | -0.144 |
| B10 | B5 any open (gap-under included) | -0.1217 | -0.0910 | -7.43 | 177.2 | 6 | -0.154 | -0.061 | -0.113 |
| B11 | early reclaim long p10 exits | -0.1233 | -0.1417 | -9.61 | 68.7 | 0 | -0.073 | -0.199 | -0.134 |
| B12 | B5 + SPY below VWAP | -0.1325 | -0.0134 | -5.47 | 40.9 | 12 | -0.161 | -0.029 | -0.091 |

The best-day share is shown only where total R > 0 (B7). The other rows lose in total.
Full columns are in results.csv and score_out.txt.

## Post-hoc sensitivity (disclosed and counted; not a candidate): diag.py -> diag_out.txt
This splits A4/A5's SPY leg on the A3 trades, per unit beta, in R of the stock's risk.
- Gross P/L at the exit-bar closes: -0.0017.
- Conservative-fill adjustment (the worse of two closes on intrabar exits): -0.0083.
- Costs: -0.0083.
- Even with the optimistic exit-bar-close fills, the beta-1 pair is -0.0153 with t -5.8.
- The pair's sd falls only from 0.255 to 0.232. Most of the trade's variance is idiosyncratic, not beta.

## What it means
- **A, beta hedge.** The hedge does what it should to the regime split: A5 is up-day -0.027 and down-day -0.025, which is flat.
  But it only exposes the fact that the long has no market-neutral edge, which matches why/NOTES (gross +0.014 at best).
  The hedge then adds ~0.008R of costs plus fill slippage. The losses become consistent and t goes strongly negative.
  The hedge removes the down-day disaster by turning every day into a small loss. Beta20 (median 1.0; 6% of trades fall back to 1.0)
  and QQQ make no difference.
- **B, early break.** The early window has 2.1x cost multipliers and the same beta problem as the parent.
  - The reclaim longs make money on up days and lose on down days.
  - The continuation shorts are the mirror: they lose on up days and make a little on down days.
  - The S3 + cost5 versions are about zero, and they trade only 12-18 per session, which fails the exposure floor of 25.
  - Neither version separates direction before the move. The Move Hunt observation (moves start early) holds,
    but a PDL break or reclaim in 09:35-09:45 does not say which way the move goes.
- No bar was loosened. Nothing reaches t > 0.5. The CWT14 PDL lineage now stands at N 121,635 with 0 passes.

## Files
- PLAN.md: the pre-declaration.
- build.py: entries, sim and hedge legs; cache in scratch `pdl1030b/cache`, 19 MB.
- score.py writes results.csv and score_out.txt.
- diag.py and diag_sum.py write diag_out.txt.
- Re-run: `python research/bdi/pdl1030b/build.py && python research/bdi/pdl1030b/score.py`.

*Educational only — not financial advice.*
