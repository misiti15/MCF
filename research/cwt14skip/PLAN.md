# CWT14SKIP — don't buy a failed break in a name already far below its open (Builder, pre-registered 2026-11-09 ~12:25 ET, before any score)

*Educational only — not financial advice.* Remedy candidate from Observer (observer-20261109-0943-2,
research/obs-wrongside): the CWT14 failed-break LONG family owns 21% of the wrong-way R on Move Hunt movers
(23 trades, -18.0R, 6 sessions). Lead queued it tonight (lead-20261109-1058-1). Research only, no config change.

## Rule (frozen)
Pool = every CWT14-failbrk-*-long lab setup with a 2-year trade list in research/history2y/data/bt_lab1104
(orl / pdl x p05 / p10 x plain / lowvol; the geom-S R2A variant has no list and is listed as not covered).
At the entry bar (lab `tod`, bar close), distance below the open in daily ATR: `dist = (open - close) / atr_d`, with
open = close / (1 + fromOpen/100) from the lab frame row of that bar (point-in-time). **Skip the entry if dist >= X.**
Configs: **X = 1.0 and X = 1.5** (2 configs).

## Try count
Same family, same kind of rule (a long-side guard on CWT14 failed-break longs): swing1104-L8 (IWM guard, 8 configs) +
these 2 = **N 10 → full bar 2.15, BAR90 1.93**. (Own-only N 2 → bar 1.50, shown, never used.)

## Scoring (Lead standard lead-20261109-0900-1: excess over a matched control, kept avg R shown)
- Per day: delta_d = -(sum of skipped R). Control = a same-day random block of equal size from the same pool
  (200 draws, seed 20261109); excess_d = delta_d - mean random delta_d. Days with no skip contribute 0.
- Day-clustered t of the daily excess (all pool days); TRAIN (<= 2025-09-30) and VALID excess separately; excess
  w/o its best day; split by SPY o-c up / down / quiet (+-0.25%).
- Kept avg R vs the pool's avg R; **retention: kept trades >= 80% and kept top-decile winners >= 90%** (top decile of
  the pool's R over the whole window) — the charter's filter-creep test.
- Per variant (8): excess, skipped n, better / worse count and by how much (Remedies rule).
- Caveat stated with the result: the lists are uncapped signal chains, so a skip does not create a re-entry here.

## Pass (lead worth pursuing)
Excess t >= 1.93, TRAIN and VALID excess > 0, excess w/o best day > 0, retention 80% / 90% met, and more variants
better than worse. Also written: per-trade `dist` and `fromOpen` at entry for the whole pool (`cwt14_dist.csv`),
the shared column Observer asked for (long-laggard split).
