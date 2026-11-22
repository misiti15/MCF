Educational only — not financial advice.

# Part D pre-registration: NM-ETF-late-dip-di-long protection study (rules-1122)

Written 2026-11-22 before any Part D configuration was scored (owner widened Part D the same day: "keep NM-ETF's normal
and good-burst R, cut the tail"). Research only; no config change.

## Engine and data
- E4-normal-way: the bench10 NM-ETF signals already on disk (`trades_t1.parquet` FIT + CHECK, `trades_t2.parquet` T2,
  from research/ultimate_1119/top10/bench10.py), re-walked minute by minute on 1-minute bars (data/cache_hist/1Min
  for T1 with the locked block filtered out and asserted absent; data/cache_fresh/1Min for T2) by one per-day simulator
  that reproduces bench10 `walk_trades` + `add_r` (LR8 costs) + `book` (Primary: cap 30, <= 3 lots per symbol, -2R latch
  on realized cost-R). The base must reproduce the booked bench10 numbers (FIT +57.78R / 226 lots, CHECK +10.71R / 262
  lots) within rounding before any rule is scored.
- FIT = 2024-10 + 2025-03..09 (development), T2 = 2023-01..2024-09 (second development period), CHECK =
  2025-10-01..2026-11-04 (scored once, same run, no change after). 2024-11-01..2025-02-28 never read.
- Rule exits happen at the close of the minute in which the rule triggers (market exit cost 1c + 1bp, x3 extended tier).
  A lot's own stop / target is checked first inside each minute (stop first).

## Definitions (causal)
- **Burst lot:** a booked NM-ETF lot entered when >= 4 NM-ETF lots (itself and same-minute peers included) were booked in
  the last 10 minutes. **Burst:** starts at the first burst lot; it holds every lot booked in the 10 minutes up to its
  start and every lot booked in the 10 minutes after; burst R = realized + open marks (minute close) of its lots.
- Open mark R of a lot = side x (close - entry) / risk x size (no exit cost in the mark).

## Configurations (19; <= 24 allowed)
| id | idea | rule |
|---|---|---|
| G2 / G3 | (1) shared group stop | once k = 2 / 3 lots of a burst have stopped out, flatten the burst's open lots |
| B2 / B3 / B4 | (2) burst loss budget | burst R <= -2 / -3 / -4 -> flatten the burst's open lots |
| T15 / T30 | (3) burst time stop | N = 15 / 30 min after the burst starts, if burst R < 0, flatten its open lots |
| S4 | (4) split a fixed per-bar risk | when >= 4 lots book in one decision minute, each is sized 4/n (bar budget 4R). **Conflicts with C3-BAR2 "per-setup risk stays flat"** |
| SH | (4b) half-size late burst lots | the 4th and later lots of a burst at 0.5 size (same conflict) |
| W3x1.5 / W3x2.5 / W4x1.5 / W4x2.5 | (5) in-runner burst sentinel | when >= k NM-ETF lots are open and their combined open mark <= -X R, flatten all open NM-ETF lots (entries continue under the normal latch) |
| O4 / O6 | (6) pre-trade open-risk budget | a new lot is taken only if realized R - (open lots x 1R) - 1R >= -L (L = 4 / 6): the worst case of the day, counting open lots at full stop, stays above -L |
| P1 | (7) staggered entries + latch | lots of one decision minute enter one per minute (j-th lot at the close of minute em + j, stop / target levels unchanged, R on the new stop distance, skipped if already through stop or target); the latch is checked before each |
| P1W | (7) + (5) | P1 plus sentinel W3x1.5 |
| Q50 | (8) tighter stop, burst lots | burst lots use half the stop distance (same shares, R in original risk units) |
| Q20 | (8) shorter time stop, burst lots | burst lots exit at the close 20 minutes after entry if still open |

Hedges are on the consultant's do-not-run list: mentioned, not tested.

## Metrics per configuration (FIT, T2, CHECK separately and FIT+T2+CHECK)
total R and dR vs base, lots, worst-day R (owner's main metric), days <= -4R (count and sum), days improved / worsened,
avg R without best day, day-clustered t of the per-day dR, effect on the April-2025 burst days (2025-04-03..04-11), on
losing-burst days (base burst R < 0), and on non-burst days. Ranking: worst-day R cut per R given up (all periods).

## Bars
- Try count: this study N = 19 -> max(1.5, sqrt(2 ln 19)) = 2.43; ETF-burst lineage (21 in final1121 + 2 group caps in
  giveback 1121 + 19) N = 42 -> 2.73. Applied to the day-clustered t of the per-day dR on FIT+T2.
- **Finalist** (fixed now): worst day better in FIT AND in T2, dR >= -5R in FIT AND in T2. Finalists are then judged on
  CHECK (worst day not worse, dR >= -5R) and the live 11-20 replay. A proposal needs a finalist that also clears the bar
  or, failing that, is offered only as Optional with its tail-for-R price stated.
- Live replay (10-19..11-20, NM-ETF + WB1 + WB4 + ULT-22 journals): no 1-minute bars after 2026-11-04 in this checkout,
  so open marks are interpolated linearly between each lot's journal entry and exit (E4 approximation, stated); every
  11-20 lot finally stopped, so the replay gives an upper estimate of the saving with a no-saving lower bound.

## Addendum (after the 19 were scored, 2026-11-22)
Q50 was the only finalist. Two plateau neighbours were added to check it (rule 18 plateau, not to pick a new winner):
**Q40** (burst-lot stop at 0.4 of the distance) and **Q65** (0.65). Count is now N = 21 (bar 2.47; lineage N = 44, bar
2.75). Q50 stays the candidate whatever the neighbours show; they only confirm or deny the plateau.
