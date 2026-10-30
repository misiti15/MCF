# rdt1030 / F1 orb15-fvg-break: results

*Educational only — not financial advice.*

**Verdict: no row passes. 24 configs were scored: the 18 pre-declared plus 6 rework configs from a dated amendment.**

This is the Reddit post's "15-min ORB + FVG" model. The entry is the close of the candle that breaks the 09:30-09:45 range
and completes a 3-candle fair value gap. The stop is the gap's first candle, and the target is 1R, or 2R when the stop is
small.

On our stocks the setup has **roughly zero gross edge** (about +0.00R before costs on every row) and loses about 0.03 to
0.08R after costs. Its result is entirely market direction:
- longs make +0.05 to +0.14R on SPY up days and lose 0.25 to 0.34R on down days
- shorts are the mirror image

That is the same failure as R14/R18 and every earlier ORB test.

## Harness (DESIGN 0.2)
- **Frames:** `scan_1019.build_paths` (5-min frames, 0935-0945 head rows, tail rows to 15:55). The `_cut` patches and
  asserts are copied from pdl1030/combo. Nothing from the locked block or the HOLD months was loaded.
  - TRAIN: 2024-10 and 2025-03..12
  - VALID: 2026-01..03 and 2026-07..09-15
  - 348 sessions in total
- **Simulator:** a numba copy of `scan_1028.sim` (`build.py:sim`), stop-first.
  - **Sim check:** with the patches switched off it matches `scan_1028.sim` exactly (max |diff| 0.0 on 20,000 trades,
    2025-06). Run it with `python build.py check`.
  - **Patches:** per-trade R (entry to the FVG's first candle) and target multiple; 1c + 1 bp entry × ToD multiplier; 1c + 1 bp
    on **every** exit including targets, +2c on stops; ×3 on the extended tier; gap-through stops fill at min(stop, high) for
    a long and max(stop, low) for a short.
- **Random control:** 5 random other universe symbols at the same signal row (seed 20261030), using the same side, the same
  R in ATR units, the same target multiple and the same sim and costs.
- **Base-row sanity check** (2025-06, run before any R was read):
  - F1-A long gave 2,603 trades, 0.16 per liquid symbol-day. DESIGN 0.4 had 0.27 per symbol-day *before* the fresh-break
    requirement, so the count is consistent.
  - The median R/ATR was 0.294, against 0.29 in DESIGN 0.4.
  - The median signal time was 10:10, against 10:10 in DESIGN 0.4.
  - The median round-trip cost/R was 0.069, below DESIGN's 0.11. The cost estimate here leaves out the +2c stop slip; the
    sim charges it.
  - Across the full period it is 140 trades per session for each side.
- **Literal 2R switch:** "30 NQ points" maps to 0.085 ATR, which gives 2R to only 0.1% of trades. F1-A and F1-E (always 1R)
  are therefore almost the same row.

## Bar
- N = 2,000 + 108 (the swarm's declared total) + 6 (F1 rework) = 2,114, so t_req = 3.52.
- A pass needs all of the following: t_day >= 3.52, WF >= 54%, avg R > 0 on TRAIN and on VALID, >= 3 trades per session,
  R > 0 on up days and on down days, and R above the control.

## Results (full table with every column: results.csv)
| id | name | n | tr/sess | TRAIN | VALID | all | t_day | WF% | win% | W/L | up-day | down-day | w/o best day | control | gross≈ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1-A-L | 15-min Opening Range Break with Gap (as posted), Long | 48,612 | 139.7 | -0.079 | -0.068 | -0.075 | -3.61 | 10 | 50.1 | 0.84 | +0.057 | -0.271 | -0.084 | -0.089 | +0.001 |
| F1-A-S | 15-min Opening Range Break with Gap (as posted), Short | 48,807 | 140.3 | -0.098 | -0.036 | -0.074 | -3.30 | 0 | 49.6 | 0.86 | -0.283 | +0.097 | -0.079 | -0.094 | +0.000 |
| F1-B-L | ... small gap allowed (0.02 ATR), Long | 68,767 | 197.6 | -0.087 | -0.071 | -0.081 | -4.22 | 10 | 50.2 | 0.83 | +0.049 | -0.279 | -0.088 | -0.104 | +0.002 |
| F1-B-S | ... small gap allowed, Short | 67,603 | 194.3 | -0.108 | -0.043 | -0.084 | -3.91 | 0 | 49.6 | 0.85 | -0.291 | +0.086 | -0.088 | -0.105 | -0.005 |
| F1-C-L | ... big gap required (0.10 ATR), Long | 23,086 | 66.3 | -0.062 | -0.074 | -0.067 | -2.52 | 10 | 49.3 | 0.88 | +0.081 | -0.277 | -0.081 | -0.067 | -0.003 |
| F1-C-S | ... big gap required, Short | 24,204 | 69.6 | -0.081 | -0.028 | -0.060 | -2.40 | 20 | 49.2 | 0.90 | -0.267 | +0.106 | -0.066 | -0.079 | +0.003 |
| F1-D-L | ... 2R on tight stops (<= 0.20 ATR), Long | 48,612 | 139.7 | -0.081 | -0.067 | -0.076 | -3.47 | 20 | 48.4 | 0.91 | +0.066 | -0.286 | -0.085 | -0.090 | +0.001 |
| F1-D-S | ... 2R on tight stops, Short | 48,807 | 140.3 | -0.094 | -0.037 | -0.072 | -3.10 | 0 | 48.1 | 0.92 | -0.291 | +0.107 | -0.078 | -0.094 | +0.002 |
| F1-E-L | ... fixed 1R target, Long | 48,612 | 139.7 | -0.079 | -0.068 | -0.075 | -3.61 | 10 | 50.1 | 0.84 | +0.057 | -0.271 | -0.084 | -0.090 | +0.001 |
| F1-E-S | ... fixed 1R target, Short | 48,807 | 140.3 | -0.098 | -0.036 | -0.074 | -3.30 | 0 | 49.6 | 0.86 | -0.283 | +0.097 | -0.079 | -0.090 | +0.000 |
| F1-F-L | ... fixed 2R target, Long | 48,612 | 139.7 | -0.075 | -0.070 | -0.073 | -2.69 | 20 | 42.4 | 1.18 | +0.108 | -0.340 | -0.083 | -0.087 | +0.004 |
| F1-F-S | ... fixed 2R target, Short | 48,807 | 140.3 | -0.095 | -0.037 | -0.073 | -2.44 | 20 | 41.1 | 1.24 | -0.369 | +0.170 | -0.081 | -0.097 | +0.002 |
| F1-G-L | ... skip if costs > 10% of risk, Long | 37,876 | 108.8 | -0.045 | -0.056 | -0.049 | -2.16 | 20 | 49.8 | 0.90 | +0.089 | -0.253 | -0.060 | -0.082 | -0.000 |
| F1-G-S | ... skip if costs > 10% of risk, Short | 38,607 | 110.9 | -0.057 | -0.011 | -0.038 | -1.64 | 30 | 49.7 | 0.93 | -0.254 | +0.137 | -0.044 | -0.084 | +0.009 |
| F1-H-L | ... late gap allowed (3 bars), Long | 54,708 | 157.2 | -0.083 | -0.068 | -0.078 | -3.77 | 0 | 50.1 | 0.84 | +0.052 | -0.274 | -0.086 | -0.094 | +0.000 |
| F1-H-S | ... late gap allowed, Short | 54,616 | 156.9 | -0.096 | -0.040 | -0.074 | -3.28 | 0 | 49.7 | 0.86 | -0.290 | +0.098 | -0.079 | -0.091 | +0.001 |
| F1-I-L | ... all-day window (to 15:00), Long | 61,270 | 176.1 | -0.087 | -0.076 | -0.083 | -4.57 | 0 | 49.8 | 0.84 | +0.045 | -0.278 | -0.090 | -0.096 | -0.003 |
| F1-I-S | ... all-day window, Short | 62,863 | 180.6 | -0.106 | -0.046 | -0.084 | -4.23 | 0 | 49.3 | 0.85 | -0.284 | +0.067 | -0.089 | -0.097 | -0.006 |
| F1-RW1-L | (rework) ... skip if costs > 5% of risk, Long | 21,391 | 61.5 | -0.017 | -0.045 | -0.029 | -1.05 | 40 | 49.7 | 0.94 | +0.118 | -0.250 | -0.046 | -0.069 | +0.003 |
| F1-RW1-S | (rework) ... skip if costs > 5% of risk, Short | 22,869 | 65.7 | -0.051 | -0.004 | -0.030 | -1.15 | 40 | 49.0 | 0.97 | -0.260 | +0.154 | -0.035 | -0.075 | +0.001 |
| F1-RW2-L | (rework) Big Gap (0.10 ATR), low-cost only, Long | 19,635 | 56.4 | -0.039 | -0.064 | -0.048 | -1.71 | 20 | 49.2 | 0.92 | +0.103 | -0.265 | -0.065 | -0.060 | -0.003 |
| F1-RW2-S | (rework) Big Gap, low-cost only, Short | 20,606 | 59.2 | -0.048 | -0.006 | -0.031 | -1.20 | 30 | 49.5 | 0.95 | -0.241 | +0.137 | -0.037 | -0.070 | +0.013 |
| F1-RW3-L | (rework) low-cost, fixed 2R target, Long | 37,876 | 108.8 | -0.041 | -0.055 | -0.046 | -1.64 | 30 | 43.0 | 1.21 | +0.135 | -0.316 | -0.059 | -0.081 | +0.002 |
| F1-RW3-S | (rework) low-cost, fixed 2R target, Short | 38,607 | 110.9 | -0.056 | -0.016 | -0.040 | -1.31 | 20 | 41.9 | 1.24 | -0.340 | +0.284 | -0.049 | -0.085 | +0.007 |

Notes on the table:
- "gross≈" is avg R plus the mean pre-trade cost estimate. It leaves out the stop slip, so it is a rough number.
- **Best-day share** is undefined for every row because total R is negative. The best day is 2025-04-07 for the longs and
  2026-03-20 for the shorts. No record is carried by one day; each row is a broad, steady loss.
- **Busiest session:** at most 1.9% of a row's trades.

## What we learned
1. **The trade is market beta at the open, with no stock-level edge.**
   - Win rate is 49-50% at 1R. W/L is 0.84-0.97 at 1R because costs and stop slip shrink wins and grow losses.
   - The rows beat their own random control by only +0.01 to +0.05R. The ORB+FVG break picks entries only slightly better
     than a random liquid name taken at the same bar, side, risk and target.
   - The post's 52% win rate and 1.56 W/L do not carry over to US single stocks at 5-min resolution.
2. **The regime split is the whole story, as in R14/R18 and ORB30.**
   - Longs: +0.05..+0.25R on up days, -0.25..-0.37R on down days.
   - Shorts: the mirror image.
   - Any edge would have to come from knowing the day's direction early, which is what F2-G4/G9 (QQQ from open) and F5-I8
     (breadth) test. F1 says the entry by itself has none.
3. **Costs are the only lever that moved the numbers, and only toward zero.**
   - Cost caps raise net avg R (from -0.075 to -0.049 at 10% and -0.029 at 5%) because they drop high-cost trades.
   - Gross R stays at about 0, so the 5% cap does not create an edge.
   - The NQ trader's costs are about 1-2% of R. Ours are a median 5-6% plus 2c stop slip, about 7-11% all-in.
4. **Bigger gaps, wider windows, late gaps and 2R targets change nothing material.**
   - A bigger FVG (0.10) is slightly less bad, mainly through lower cost/R.
   - The all-day window and the small-gap version are worst.
   - 2R lowers the win rate to 41-43% and raises W/L to 1.2. Its expectancy is the same as 1R.
5. **The literal "2R if stop < 30 NQ points" maps to 0.1% of trades** (0.085 ATR), so on stocks the post's model is a 1R
   model.

## Not done / handover
- **No finalist, so no mask module.**
- **Entry code for F5:** the F1-A entry is `build.py:signals()` plus the universe and risk-guard lines in `month_job`. F5
  can import it, using `SIG["A"]`, `CFG["F1-A"]` and side ±1.
- **Scratch:** the per-month trade parquet was deleted after this report. To rebuild, run `python build.py` and then
  `python build.py rework` (about 12 minutes on one core), then `python score.py`.
- **Config count to add to the swarm total:** 24 (18 declared + 6 rework).
