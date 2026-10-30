# pdl1030 / time-bucket: results

*Educational only — not financial advice.*

**Nothing passes.** I scored 18 configurations, all pre-declared in PLAN.md, with none added afterwards. N = 121566 + 3 x 18 = 121620 (conservative), so the bar is t >= 4.355.
No row is positive on both TRAIN and VALID, and the best t is -0.39. No module was written.
Data: TRAIN+VALID only (348 sessions). HOLD months and the locked block were never loaded, which is asserted at build and at score.
Files: PLAN.md, build.py (cache/tr_*.parquet: every flagged bar 09:35-15:00, simulated with P and S3 exits), score.py, score_out.txt, results.csv.

## Parity (exact)
On the 09:50-15:00 window, first signal per symbol-day: p05 P -0.0677 / -0.0675 (n 53,326), p10 P TV -0.0880,
and p05 S3+cost5 (= symbol-quality Q08) -0.0028 / -0.0084 at 54.3/sess.

## What the time buckets show
1. **An earlier start (09:35) with parent exits makes things worse.** T01 09:35-15:00 runs 211/sess at -0.079. The 09:35-09:45 bucket alone (T02)
   is 98/sess at -0.090. Opening signals are plentiful (the gap and the auction break PDL), but entry costs are 2.1x and gross edge is still ~0.
   The Move Hunt point that big moves start before 09:50 does not carry over to this signal, which has no direction.
2. **Windows give small changes under parent exits.** The afternoon (T05, 13:00-15:00) is -0.064 vs the parent -0.068, at 37/sess.
   Skipping the 09:50 bar (T03) gives -0.072. Every bucket keeps the down-day loss (-0.12..-0.14).
3. **On top of S3 + cost5, time of day is flat:** every bucket lands at -0.002..-0.007 TV.
   - T09, 09:35-10:30: -0.0037 / -0.0060 at 33.5/sess. wf 58.8% is the only wf above 54%, but t is -0.75.
   - T07, 09:35-15:00: -0.0043 / -0.0064 at 58.3/sess. That is about 4/sess more than Q08 at the same avg R.
   - T12, lunch 11:30-13:30: +0.0026 TRAIN / -0.0089 VALID at 18.9/sess, under the exposure floor.
   Down-day R is negative in every row (-0.025..-0.085), so the market-beta loss stays.
4. A looser cost floor (c8) roughly doubles exposure to 86-116/sess and costs about 0.004R (T15 -0.009, T16 -0.010).
   p10 with S3+c5 is worse than p05 (-0.016..-0.022).

## Best curve
- **T09** (p05, signal bar 09:35-10:30, S3 stop x3 at the same $, round-trip cost <= 5% of R): -0.0037 TRAIN / -0.0060 VALID, t -0.75,
  33.5/sess, wf 58.8%, up days +0.041, down days -0.054.
- **T07** (09:35-15:00) is the best curve with high exposure: -0.0053 TV at 58.3/sess.

Neither is positive after costs. The time of day does not hold the missing edge. What is left is the S3 + cost-floor plateau at about -0.005R.

## Known-at-entry
- Window: the bar time.
- Signal: close of the reclaim bar (CWT14 b3_any, look-back only).
- Cost estimate: price, tier (gap at the open / price), bar-time multiplier and daily ATR, all known at the signal close.
- S3 is an exit rule. spy_day is EOD and is used only for the up/down split, never as a filter.
