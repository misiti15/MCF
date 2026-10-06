# obos_levels -- overbought/oversold meeting resistance/support

Educational only -- not financial advice.

## What was searched (train only, 40 sessions to 2026-08-25)
- OB/OS: rsi >65/70/75/80, rsi5 >80/85/90 (mirror for oversold).
- Level: |dist_pdh|, dist_hod, dist_round <= 0.1/0.2/0.3 ATR; failed break of PDH/PDL (bar traded through the level and closed back inside within x ATR); or no level.
- Third layer: none, wick >= .3/.5, flow3 sign / < -.3, flow flip (flow3 vs flow9prev), divergence, rsiSlope sign, |vwapDist| > 1%, vol_climax > 2.
- Time: all, <= 11:30, >= 11:00.  All three geometries.
- Run 1: fade direction (short at resistance / long at support). Run 2: same masks traded the other way (continuation).
- Total configurations: 31,212 (train) + 13 finalists checked on valid.

## Result
- **Fade direction: nothing.** Best was ~+0.04R with SE ~0.04 (noise level for 15.6k tries). No t05s1 (high-win-rate) fade cleared its ~69% breakeven win rate with PF >= 1.15. Example: long rsi5<10 at PDL (<=0.1 ATR) below VWAP after 11:00, t1s1: +0.037R, PF 1.11; same with t05s1: 58% win, -0.002R.
- **Continuation direction is where the train signal was:** an oversold bar that wicks under the prior-day low and closes back above (looks like a hammer / failed breakdown) before 11:30 is followed by MORE downside, not a bounce. Train +0.10..+0.15R in t1s1.
- **Valid (15 sessions) mostly killed it.** 13 finalists; only #1 stayed positive:
  - obos_levels_1 short t1s1 (rsi<25, failed PDL break <=0.2 ATR, lower_wick>=0.5, <=11:30):
    train n=532 win 52.4% exp +0.147R PF 1.39 halves +0.240/+0.040;
    valid n=214 win 47.2% exp +0.060R PF 1.146 (lab evaluate) vs baseline +0.020. Breakeven win ~51%.
    Misses PF 1.15 by a hair, SE 0.063 -> not distinguishable from zero. Not viable; kept as the only finalist for the lead's test.
  - Near miss: rsi<30 + failed PDL + rsiSlope>0, <=11:30, short t1s1: train +0.099R (n 1220), valid +0.054R, PF 1.13.
  - High-win-rate version (rsi<30 + failed PDL + bull_div, t05s1): train 71.6% win +0.075R -> valid 66.7% win -0.007R. Fails.
  - The PDL-proximity (not failed-break) and t1s05 versions flipped negative on valid (-0.06..-0.09R).

## Takeaways
- Classic "overbought into resistance -> fade" / "oversold at support -> bounce" does not carry an edge here after costs at R = 0.25 daily ATR, in any geometry.
- High win rates come almost entirely from the t05s1 geometry (coin flip ~65%); none of these layers lifted it above the ~69% breakeven.
- Only 40+15 sessions; train halves differ strongly by regime (short baseline +0.033 / -0.045), so every result here is fragile.
