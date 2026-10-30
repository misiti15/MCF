# rdt1030 / F2 — 15-min Opening Range Break with Gap + "don't trade chop" gates (PLAN, written before any score)

*Educational only — not financial advice.*

Written 2026-10-30, before any outcome was computed. Source: `research/bdi/rdt1030/DESIGN.md` (section 0 harness, F1 and
F2 tables), copied unchanged. The F1 folder did not exist when this was written, so the F1-A entry is built here from
DESIGN.md 0.5 / F1 (`build.py`).

## Base entry (F1-A, as written) — "15-min Opening Range Break with Gap"
- OR15: ORH / ORL = max high / min low of the 0935, 0940, 0945 head rows (all three present, width >= 0.05 ATR_d).
- Fresh break: the first close above ORH (below ORL) today on a row with tod >= 0950.
- Bullish FVG completed at row i: rows i-2, i-1, i consecutive 5-min bars of the symbol-day, `low[i] - high[i-2] >=
  0.05 ATR_d` and >= $0.02 (bearish mirror `low[i-2] - high[i]`).
- Signal at row i if the FVG completes at i, the fresh break is at row i-1 or i, close[i] beyond the OR level, and
  tod(i) in 0955..1100. First signal per symbol-day per side. If none within the two-row allowance, the side is done.
- Entry close[i]; stop low[i-2] (long) / high[i-2] (short), no buffer; R = |entry - stop|; skip unless 0.03 <= R/ATR_d <= 1.0.
- Target 2R if R <= 0.085 ATR_d else 1R. Flat 15:55. No break-even.
- Universe adv20 >= $95M on the signal row, atr_d > 0.

## F2 rows (one gate on top of F1-A; gate known at the close of row i; applied to F1-A's trade, so each F2 row is a subset of F1-A)
| row | gate | sides |
|---|---|---|
| F2-G1 | OR15 width >= 0.30 ATR_d | L, S |
| F2-G2 | OR15 width <= 0.55 ATR_d | L, S |
| F2-G3 | stock ER >= 0.40 (ER over 5-min closes 0935..i-1, first term \|c0935 - open_d\|) | L, S |
| F2-G4 | `qqq_fo` >= +0.20% (L) / <= -0.20% (S) at row i | L, S |
| F2-G5 | SPY ER (same definition, SPY rows through i-1) >= 0.40 | L, S |
| F2-G6 | SPY prior-day range (H-L)/C >= trailing 20-day median of that range (known before the open) | L, S |
| F2-G7 | `volumeRatio` >= 1.0 at row i | L, S |
| F2-G8 | no close beyond the opposite OR side on any row 0950..i-1 | L, S |
| F2-G9 | G3 and G4 | L, S |

**18 configs** (9 gates x 2 sides). F1-A L/S are scored here only as the reference parent (they are F1's configs, not
counted again by F2). Harness check (not a config): CWT14 PDL p05 long with the unpatched `scan_1028.sim`, 0.25 ATR
risk, t0.5/s1 parent exits — must give -0.0677 (TRAIN) / -0.0675 (VALID) ± 0.002.

Implementation choices fixed now:
- Gating applies to the F1-A trade (first signal per symbol-day per side); a day whose first signal fails the gate is
  not re-tried on a later row (F1-A's "side is finished").
- G6 data: `lib.daily()` SPY rows, excluding HOLD months (2026-04..06, >= 2026-09-16) and the locked block. Prior day
  must be <= 5 calendar days before the session, the 20-day median needs >= 10 of its 20 trailing rows within 45
  calendar days; otherwise the gate value is missing and the trade is dropped from G6 (reported as coverage).
- Missing gate value (G4/G5) -> trade dropped from that row.

## Simulator, costs, statistics
Exactly DESIGN 0.2 / 0.3: `scan_1028.sim` copied and patched (per-trade R and up; costs 1c + 1 bp per side on every
exit incl. targets, entry x tod multiplier, +2c on stop exits, x3 extended tier; gap-through stop fill
min(stop, high[k]) / max(stop, low[k]); signal-close entry). TRAIN 2024-10, 2025-03..12; VALID 2026-01..03,
2026-07..2026-09-15. N = 2,108 (DESIGN), t_req = 0.9 x max(1.5, sqrt(2 ln N)) = 3.52 (recomputed if rework rows are added).
Pass = t_day >= t_req, gates.walk_forward share >= 54%, avg R > 0 TRAIN and VALID, >= 3 trades/session, up-day and
down-day R > 0, above the random control (K = 5 random universe symbols at the same signal bar, same side, risk in ATR
units, target multiple, seed 20261030). Opportunity retained vs F1-A: trades kept and top-decile (by R) winners kept
(>= 80% / >= 90% to be proposable as a filter).

Rework (rule 18) only after the 18 rows are scored, as new counted rows, declared in a dated amendment below before scoring.

## Amendment 2026-10-30 (after the 18 rows failed, before any rework row was scored) — rule 18 rework, 6 new counted rows
All 18 rows failed (results.csv). The parity check matched (-0.0677 / -0.0675). The failure pattern is the known regime
split (longs lose on SPY down days, shorts on up days) and every row stays negative after costs. Rework rows, chosen
from the gate family, not from new data looks; each is one condition added to the least-bad gate (G6, "active market
yesterday"), both sides:
| row | rule | sides |
|---|---|---|
| F2-RW1 | G6 + G8 (active market yesterday + clean one-way open) | L, S |
| F2-RW2 | G6 + G1 (active market yesterday + active open, OR15 >= 0.30 ATR) | L, S |
| F2-RW3 | G6 + cost floor: round-trip cost <= 5% of R | L, S |
N becomes 2,000 + 108 + 6 = 2,114 (t_req recomputed; 3.52). No further rework is declared by F2.
