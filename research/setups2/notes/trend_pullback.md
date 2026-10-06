# trend_pullback: buy the dip / sell the rip inside an intraday trend

Educational only. Not financial advice.

## What was searched (train only: 40 sessions up to 2026-08-25)
- Stage 1 grid, one side at a time; shorts are the exact mirror. Pullback layer: rsi5 <20/30/40, rsi <35..50,
  below SMA20 (or within 0.3% under it), pricePosition <0.3, rsiSlope < -10, >0.3 ATR off the high of day.
  Trend layers: VWAP distance (above by 0/0.3/0.7%, near VWAP, below), SMA20 slope / above SMA50 / EMA9>21,
  fromOpen and gap. Time windows: all, <=11:30, >=11:00, >=13:00, 10:00-14:00. All 3 geometries.
- Stage 2: threshold refinement around the stage-1 winners, plus a trigger layer (flow3 sign, a volume flip,
  lower wick, rsiSlope>0, vol_climax <1 or >1.5, pricePosition) and finer time cutoffs (<=10:30 .. <=12:00).
- Configurations scored on train (mask x geometry, n>=300): 146,187 in stage 1 and 121,479 in stage 2, about 268k in total.
  20 finalists were checked on valid.
- **Key correction:** trades on the same day are strongly correlated. Trade-level t-stats of 6-8 dropped to about 2
  when computed from daily P&L (`td`). With 40 days and about 268k configurations, nothing on train is significant
  by daily t-stat. So valid was the real filter.

## Result: long "buy the dip in an uptrend" failed out of sample
- Train favourite: rsi5<30, more than 1.5% above VWAP, vol_climax<1, before 11:30, long t05s1.
  Train: n 439, win 79.0%, +0.203R, PF 2.19. Valid: n 78, win 50.0%, **-0.215R**, PF 0.52.
- All 11 long finalists lost money on valid, from -0.04R to -0.48R. That is worse than the long baseline
  (-0.10 to -0.13R) in most cases. These setups bunch up on strong-market days, so they act as market-regime bets.

## Only survivor: short "sell the rip in a stock down from the open" (trend_pullback_1/2/3, one mask)
Layers: fromOpen < -0.5%; close below VWAP; close below the 5-min SMA50; close back above the 5-min SMA20
(the bounce); bar close at or before 10:30 ET. Short entry on the first qualifying bar of the symbol-day.

| file | geom | split | n | /day | win | breakeven win | exp R | PF | halves | baseline |
|---|---|---|---|---|---|---|---|---|---|---|
| trend_pullback_1 | t05s1 | train | 662 | 17.0 | 74.3% | ~69% | +0.097 | 1.39 | +0.119/+0.062 | -0.057 |
| trend_pullback_1 | t05s1 | valid | 203 | 14.5 | 76.4% | ~70% | +0.115 | 1.49 | +0.030/+0.177 | -0.002 |
| trend_pullback_2 | t1s05 | train | 662 | 17.0 | 45.8% | ~36% | +0.168 | 1.59 | +0.200/+0.119 | -0.022 |
| trend_pullback_2 | t1s05 | valid | 203 | 14.5 | 44.3% | ~36% | +0.141 | 1.49 | +0.026/+0.226 | -0.012 |
| trend_pullback_3 | t1s1 | train | 662 | 17.0 | 56.0% | ~52% | +0.185 | 1.49 | +0.219/+0.134 | -0.006 |
| trend_pullback_3 | t1s1 | valid | 203 | 14.5 | 54.2% | ~52% | +0.127 | 1.32 | -0.013/+0.230 | +0.020 |

The breakeven win rate ignores timed exits; the average cost is about 0.04R per round trip.
About 30% of entries are on the first eligible bar (09:50).

### Caveats
- One idea with three exit geometries, not three independent setups. It is 1 survivor out of 20 valid looks,
  so selection bias applies.
- The daily-P&L t-stat is about 1.5 on train and 1.4-2.3 on valid. That is promising but not proven.
- The t05s1 margin over breakeven is only about 5-6 win-rate points (+0.10R). One extra cent of slippage per side
  costs about 0.04R. Prefer t1s05 or t1s1 if live fills are poor.
- Earlier near-misses that died on valid: the gap-up-fade short (rsi5>65, more than 1.5% below VWAP, gap > +0.5%,
  SMA20 falling, <=12:00, t05s1) went from +0.145R train to -0.058R valid. The early-afternoon long reversal
  (rsi5<20, below VWAP, SMA20 rising, after 13:00) was not taken to valid because its win rate was about 30%.
