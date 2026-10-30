# pdl1030: BDI swarm on the Failed Prior-Day-Low Break Longs (owner 2026-10-30)

Educational only — not financial advice.

Owner ask: why do CWT14-failbrk-pdl-* fire so often, and find a variant that keeps that exposure with a higher avg R.
11 agents, 3 rounds, 9 families, **152 configurations scored**, all pre-declared (one disclosed post-hoc row in entry-confirm).
Lineage N 121,459 -> 121,611; BAR90 Testing bar t >= 4.355. TRAIN+VALID only; HOLD months and the locked block never loaded.
Parent parity exact in every family (p05 -0.0677 / -0.0675). **0 pass; nothing verified; no module written.**

## Why they are so common (why/NOTES.md)
- ~885 liquid names a session; the prior-day low sits close to the open (median 0.42 ATR above). 42.5% of symbol-days
  break it by 15:00 (60% of breaks by 09:45), and 41% of those reclaim within 3 bars -> ~153 signals a session.
- **No gross edge:** +0.020R before costs (p05), costs ~0.088R round trip. The R is mostly market beta (~0.9R per 1% SPY
  move during the trade); SPY down sessions carry 94-99% of the loss.
- Strongest gradient known at entry: cost per R (<= 5% of R: -0.018; > 12%: -0.210).

## Best per family (TRAIN / VALID avg R, day t, months positive, trades/session)
| family | best | TRAIN | VALID | t | WF | /session |
|---|---|---|---|---|---|---|
| tape-flip | breadth flip + cost <= 10% | +0.000 | -0.017 | -1.23 | 35% | 114 |
| entry-confirm | 2 bars hold + cost5 | -0.035 | -0.031 | -4.2 | 29% | 81 |
| structure-exit | stop LOD-0.25A on p10 | -0.030 | -0.032 | -5.4 | 12% | 86 |
| merge-size | merged, 3x stop, cost-weighted, half size SPY<VWAP | -0.015 | -0.015 | -4.1 | 12% | 159 |
| symbol-quality | 3x stop + cost5 + stock ahead of SPY +0.5% | +0.013 | +0.005 | 1.17 | 59% | 9 (fails exposure) |
| failed-reclaim-short | short new LOD, mirrored exits | -0.031 | -0.015 | -2.8 | 12% | 64 |
| combo | 3x stop + cost5 + SPY-VWAP flip | +0.006 | -0.000 | 1.18 | 59% | 54 |
| time-bucket | 09:35-10:30, 3x stop + cost5 | -0.004 | -0.006 | -0.75 | 59% | 34 |
| regime-day | 3x stop + cost5 + flip on SPY prior-day range | +0.003 | +0.007 | 1.14 | 76% | 54 |

Parents: p05 -0.068 (153/session), p10 -0.088. The best rows lift avg R by ~0.07R to about zero, but none is near t 4.355.

## Conclusion
The signal is a coin flip with a market-beta tilt; its frequency comes from the prior-day low sitting near the open, not
from an edge. Wider stop at the same $ + a cost floor remove the losses (to ~0R); nothing found adds a positive edge at
this exposure. Owner decision (inbox PDL-SWARM).

Files: one folder per agent (PLAN.md, NOTES.md, results.csv, scripts); swarm_result.json = full structured output.
