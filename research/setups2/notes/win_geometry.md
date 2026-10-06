# win_geometry -- high-win-rate geometry search (t05s1 and t1s1)

Educational only -- not financial advice.

## Breakeven win rates (train, after costs; mean cost = 0.047R per round trip, median 0.027R)
| geometry | win pays | loss costs | breakeven win rate | win rate needed for +0.05R |
|---|---|---|---|---|
| t05s1 | +0.5R | -1R | ~0.70 | ~0.73 |
| t1s1  | +1R   | -1R | ~0.52 | ~0.55 |
| t1s05 | +1R   | -0.5R | ~0.36 | ~0.40 |
(Trades that end on the timed 15:55 exit fall in between. In t05s1 about 23% of all bars end that way.)

Baselines (first bar per symbol-day, so 09:50 entry): train long t05s1 wr .642 / -0.072R, short t05s1 .650 / -0.057R,
long t1s1 .442 / -0.086R, short t1s1 .479 / -0.006R. Valid: long t05s1 .630 / -0.100, short t05s1 .695 / -0.002,
short t1s1 .502 / +0.020.

## Search (train only, 40 sessions)
- Singles: 354 conditions (every input column at 2/5/10/20/30/70/80/90/95/98% quantiles; div/reclaim flags)
  x 5 time windows x 2 sides x 2 geometries = 7,080.
- Pairs: 364 conditions (+10 time-of-day cuts), 64,445 pairs x 4 side/geom = 257,780.
- Triples: top 70 pairs per side/geom (280 seeds) x 364 third layers = 96,336.
- Valid: 20 finalists scored once.  **Total configurations: ~361,200.**

## How win rate trades off against expectancy (train)
- Single conditions top out at wr ~0.72 in t05s1 (short, fromOpen < -3.4% before 10:30: wr .718, +0.061R, but
  half 2 = -0.004R). No single condition clears +0.05R with both halves positive under t05s1.
- Pairs/triples reach wr 0.74-0.82 under t05s1 with +0.15..+0.24R on train. Almost all are one family:
  **a sharp RSI thrust (rsiSlope > 23.7, or RSI > 65) in a stock deep below trend (macdPct < -1, emaDiff < -0.6..-1,
  sma50 < -2%)**, optionally back above VWAP. Example: emaDiff<-0.98 & rsiSlope>23.7 & vwapDist>0.29%:
  train n=368, wr .821, +0.241R, PF 2.64.
- Higher train win rate came with fewer trades and more day clustering; the most extreme (wr .82) was the worst
  decay on valid.

## Valid (20 finalists)
- **All 11 high-win t05s1 longs failed**: valid win rates .52-.68, all below the ~0.70 breakeven
  (best: macdPct<-1.06 & rsiSlope>23.7 & momentum>0.569: .746 -> .680, +0.166 -> +0.020R).
  The 3 short t05s1 finalists: .534-.638 win on valid, also below breakeven.
- Only short t1s1 "afternoon fade of an extended stock" survived:
  - win_geometry_1 (VIABLE on the written criteria): gap < -0.445% & sma50_dist > +2.19% & tod >= 13:00, short t1s1.
    Train n=875, 22.4/day, wr .417, +0.259R, PF 2.13. Valid n=166, 11.9/day, wr .361, +0.096R (SE 0.063), PF 1.30;
    baseline +0.020. Low win rate: most trades end on the timed exit.
  - win_geometry_2 (near miss, valid n=76 < 100): macdPct>0.399 & dist_pdh>0.95 ATR & flow3>0.376, short t1s1:
    valid +0.186R, PF 1.56.
  - dist_pdh>0.725 & sma50>2.19 & tod>=12:00 short t1s1: valid +0.132R but n=47.
- win_geometry_3 kept only as the best high-win-rate representative (not viable).

## Caveats
- Day clustering: for win_geometry_1, the top 5 of 39 train days give 91% of total R; on valid the top 5 days
  exceed the total. The real sample is ~40 days, not ~900 trades. Treat as a regime bet (afternoon selloffs).
- With ~361k configurations tried, train results of +0.2R are expected by chance alone; only valid results count.

## Bottom line
No setup kept a win rate >= 0.70 with margin out of sample. High win rate in t05s1 is mostly the geometry
(a coin flip already wins ~65%), and the layers that lifted it to .75-.82 on train did not carry over.
Positive expectancy that held came from low-win-rate t1s1 afternoon short fades, and that is fragile.
