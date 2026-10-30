# pdl1030 / symbol-quality — results

*Educational only — not financial advice.*

**Nothing passes.** I scored all 17 configurations declared in PLAN.md and added no extras. N = 121512 + 3 x 17 = 121563,
so the BAR90 bar is t >= 4.355. No row comes close: the best t is +1.17 (Q11). Every row that is positive on both TRAIN and VALID
runs at 9-14 trades/session, which is below the 25/session exposure floor. No module was written.

Parity is exact. p05: -0.0677 / -0.0675 (n 53,326, 153.2/session). p10: -0.0861 / -0.0912, TV -0.0880. p05 with the S3 stop:
-0.0210 / -0.0173, which equals swarm15. Data: TRAIN+VALID only, 348 sessions. HOLD months and the locked block were never loaded.

## When each condition is known
| condition | what it is | when it is known |
|---|---|---|
| vd | stock vwapDistPct | signal-bar close |
| rs | stock fromOpen minus SPY fromOpen | signal-bar close |
| volumeRatio | signal-bar volume / 20-bar average | signal-bar close |
| gap | open vs prior close | the open |
| cost5 | round-trip cost estimate <= 5% of the 0.25-ATR R | from price, tier, time and ATR |
| S3 | exit rule: stop x3 at the same $ risk | not an entry condition |

The SPY session direction is used only to split results into up and down days.

## Rows (TRAIN / VALID / t / trades per session / walk-forward % months positive)
- **Parent exits.**
  - Q01 vd >= 0.5: -0.024 / -0.029, 18.4/session.
  - Q02 rs >= 0.5: -0.046 / -0.047.
  - Q03 vr >= 1.5: -0.074 / -0.089. A high-volume reclaim is no better than the parent.
  - Q04 gap <= -1.5: -0.020 / -0.035.
- **S3 exits.**
  - Q05 vd: -0.006 / -0.005.
  - Q06 rs: -0.004 / -0.010.
  - Q07 vr: -0.024 / -0.021.
- **S3 + cost5 (the layered reference).**
  - Q08 (no quality filter): -0.0028 / -0.0084, t -1.21, 54.3/session, wf 41%. This is the best curve that keeps enough exposure.
  - Q09 vd >= 0.5: +0.0071 / +0.0026, t 0.69, 9.8/session, wf 59%.
  - Q11 rs >= 0.5: +0.0134 / +0.0049, t 1.17, 9.3/session, wf 59%, w/o best day +0.0065.
  - Q13 gap <= -1.5: +0.0148 / +0.0036, t 1.10, 10.4/session, wf 71%, w/o best day +0.0066.
  - Q14 vd or rs: +0.0062 / +0.0002, 14.1/session.
  - Q10 vd >= 0: +0.001 / -0.008. Q12 vr: negative.
  - Q15 vd and vr: 1.4/session, and the best day carries 138% of the total (a `1 day` record).
  - Q16 and Q17 (p10): negative on VALID.

## What it means
- Symbol quality is a small, real-looking lift of about 0.01-0.02R. Strong relative strength (vd / rs) and a gap down into PDL
  help a little. High relative volume on the reclaim bar hurts.
- The lift only turns avg R positive after S3 and cost5 have removed most of the cost drag. At that point exposure
  falls to about 10/session, and t stays near 1.
- Down-session R is negative in every row (-0.03..-0.13). The beta problem is still there, and quality filters do not fix it.
- Best curve with enough exposure: Q08 (S3 + cost5), -0.005R TV at 54/session.
  Best positive-on-both: Q11 / Q13 at about +0.009R TV, around 10/session, t about 1.1. Neither is a candidate.
