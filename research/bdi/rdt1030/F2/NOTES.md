# rdt1030 / F2 — 15-min Opening Range Break with Gap + "don't trade chop" gates: RESULTS

*Educational only — not financial advice.* Backtest only (2-year open history, TRAIN + VALID); nothing here is live or paper.

## Verdict first: 0 of 24 counted configs pass. No finalist, no mask module.
- Configs scored by F2: **24** (18 pre-declared in PLAN.md + 6 rule-18 rework rows declared in the PLAN amendment
  before they were scored). F1-A L/S are scored as the reference parent only (F1's configs, not counted here).
- Bar: N = 2,000 + 108 (DESIGN) + 6 = 2,114, **t_req = 3.52**; WF >= 54%; avg R > 0 on TRAIN and VALID; >= 3 trades/session;
  up-day and down-day R > 0; above the random control.
- **Harness parity passed:** CWT14 PDL p05 parent with the unpatched sim = -0.0677 TRAIN / -0.0675 VALID (target -0.0677 / -0.0675).
- 348 sessions (TRAIN 2024-10, 2025-03..12; VALID 2026-01..03, 2026-07..2026-09-15). Locked block and HOLD months never loaded.

## The base trade (F1-A, as the post writes it) has zero gross edge
- Long: n 48,612 (139.7/session), win 50.1%, avg win 0.82R / avg loss 0.97R, **-0.075R net, t -3.61**; approx gross +0.001R.
- Short: n 48,807 (140.3/session), win 49.6%, 0.83R / 0.97R, **-0.074R net, t -3.30**; approx gross 0.000R.
- Random control (5 random liquid names at the same bar, same risk/target): -0.094R. So the break-plus-gap entry is
  ~0.02R better than random, which is far less than the ~0.05R median round-trip cost (median cost 0.053-0.056R per R here;
  DESIGN's 0.11 calibration figure was higher than measured).
- The post's 1R/2R switch almost never fires on stocks: the stop at the FVG's first candle is a median 0.29-0.33 ATR,
  so only 0.1% of trades get 2R. Exit mix: 41% target, 39% stop, 19% flat at 15:55.
- **Regime split is the whole story again:** long +0.057R on SPY up days / -0.271R on down days; short -0.283 / +0.097.
  WF share 0-10%.

## Every row (failures — all of them)
Avg R is net of costs. "Kept" = trades / top-decile winners kept vs F1-A. Best-day share is blank when total R < 0.

| id | setup name | n/sess | win | W/L (R) | avg R | TRAIN | VALID | t_day | WF% | up / down-day R | w/o best day | kept / top10 kept | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F2-G1-L | 15-min ORB with Gap + Active Open, Long | 100.9 | .502 | 0.82/0.95 | -0.064 | -0.069 | -0.056 | -2.85 | 10 | +0.062 / -0.249 | -0.076 | 72 / 82 | all but rate/ctrl |
| F2-G1-S | 15-min ORB with Gap + Active Open, Short | 100.1 | .496 | 0.83/0.94 | -0.064 | -0.083 | -0.036 | -2.84 | 10 | -0.259 / +0.100 | -0.069 | 71 / 79 | |
| F2-G2-L | ... + Unspent Range (OR15 <= 0.55 ATR), Long | 109.6 | .500 | 0.81/0.98 | -0.084 | -0.089 | -0.074 | -3.98 | 10 | +0.053 / -0.289 | -0.090 | 79 / 69 | |
| F2-G2-S | ... + Unspent Range, Short | 110.6 | .497 | 0.83/0.98 | -0.079 | -0.107 | -0.032 | -3.31 | 0 | -0.304 / +0.102 | -0.086 | 79 / 71 | |
| F2-G3-L | ... + Trending Stock (ER >= 0.40), Long | 70.1 | .499 | 0.82/0.97 | -0.076 | -0.078 | -0.072 | -3.24 | 10 | +0.060 / -0.278 | -0.082 | 50 / 51 | |
| F2-G3-S | ... + Trending Stock, Short | 68.3 | .504 | 0.83/0.97 | -0.059 | -0.086 | -0.016 | -2.27 | 10 | -0.254 / +0.094 | -0.066 | 49 / 51 | |
| F2-G4-L | ... + Nasdaq With You (QQQ >= +0.20% from open), Long | 57.9 | .510 | 0.81/0.96 | -0.060 | -0.040 | -0.094 | -1.66 | 10 | +0.036 / **-0.439** | -0.081 | 42 / 48 | |
| F2-G4-S | ... + Nasdaq With You (QQQ <= -0.20%), Short | 58.0 | .510 | 0.84/0.96 | -0.041 | -0.078 | +0.012 | -1.06 | 30 | **-0.414** / +0.098 | -0.053 | 41 / 52 | |
| F2-G5-L | ... + Trending Market (SPY ER >= 0.40), Long | 63.2 | .496 | 0.80/0.97 | -0.090 | -0.117 | -0.041 | -3.52 | 20 | +0.011 / -0.270 | -0.097 | 45 / 43 | |
| F2-G5-S | ... + Trending Market, Short | 63.6 | .495 | 0.83/0.95 | -0.072 | -0.110 | -0.009 | -2.36 | 20 | -0.250 / +0.059 | -0.083 | 45 / 46 | |
| F2-G6-L | ... + Active Market Yesterday (SPY prior range >= 20d median), Long | 63.4 | .522 | 0.82/0.96 | -0.030 | -0.073 | +0.038 | -0.86 | 40 | +0.109 / -0.247 | -0.049 | 45 / 56 | |
| F2-G6-S | ... + Active Market Yesterday, Short | 60.3 | .479 | 0.84/0.97 | -0.102 | -0.124 | -0.074 | -2.68 | 20 | -0.324 / +0.093 | -0.111 | 43 / 46 | |
| F2-G7-L | ... + High Relative Volume (volumeRatio >= 1), Long | 39.4 | .503 | 0.80/0.93 | -0.060 | -0.067 | -0.047 | -2.49 | 20 | +0.068 / -0.243 | -0.071 | 28 / 40 | |
| F2-G7-S | ... + High Relative Volume, Short | 40.1 | .505 | 0.82/0.93 | -0.043 | -0.062 | -0.013 | -1.44 | 40 | -0.266 / +0.122 | -0.048 | 29 / 42 | |
| F2-G8-L | ... + Clean One-Way Open (no earlier close beyond ORL), Long | 128.1 | .501 | 0.82/0.97 | -0.073 | -0.076 | -0.068 | -3.38 | 20 | +0.057 / -0.269 | -0.083 | 92 / 93 | |
| F2-G8-S | ... + Clean One-Way Open, Short | 126.7 | .497 | 0.83/0.97 | -0.072 | -0.095 | -0.036 | -3.15 | 0 | -0.279 / +0.095 | -0.078 | 90 / 90 | |
| F2-G9-L | ... + Trending Stock + Nasdaq With You, Long | 28.1 | .508 | 0.81/0.96 | -0.060 | -0.017 | -0.124 | -1.47 | 10 | +0.039 / **-0.472** | -0.074 | 20 / 24 | |
| F2-G9-S | ... + Trending Stock + Nasdaq With You, Short | 28.9 | .517 | 0.85/0.96 | -0.028 | -0.070 | +0.031 | -0.60 | 30 | **-0.391** / +0.101 | -0.042 | 21 / 28 | |
| F2-RW1-L | ... + Active Market Yesterday + Clean One-Way Open, Long (rework) | 58.3 | .520 | 0.82/0.96 | -0.032 | -0.077 | +0.042 | -0.88 | 40 | +0.101 / -0.242 | -0.052 | 42 / 52 | |
| F2-RW1-S | same, Short (rework) | 54.7 | .483 | 0.84/0.97 | -0.093 | -0.114 | -0.067 | -2.39 | 20 | -0.312 / +0.097 | -0.103 | 39 / 43 | |
| F2-RW2-L | ... + Active Market Yesterday + Active Open, Long (rework) | 48.0 | .521 | 0.83/0.94 | -0.022 | -0.061 | +0.035 | -0.58 | 40 | +0.107 / -0.230 | -0.046 | 34 / 47 | |
| F2-RW2-S | same, Short (rework) | 45.5 | .479 | 0.84/0.95 | -0.094 | -0.116 | -0.067 | -2.40 | 20 | -0.312 / +0.103 | -0.105 | 33 / 38 | |
| F2-RW3-L | ... + Active Market Yesterday + cost <= 5% of R, Long (rework) | 29.6 | .532 | 0.82/0.85 | **+0.039** | +0.023 | +0.060 | 0.86 | 50 | +0.187 / -0.217 | **+0.005 (best day 2025-04-07 = 89% of total R — "1 day")** | 21 / 56 | t, WF, down-day |
| F2-RW3-S | same, Short (rework) | 30.2 | .471 | 0.84/0.87 | -0.068 | -0.098 | -0.037 | -1.54 | 50 | -0.326 / +0.162 | -0.078 | 22 / 46 | |

All rows meet >= 3 trades/session and beat the random control; every row fails t_day, WF and the up/down-day gate,
and all but G4-S, G6-L, G9-S, RW1-L, RW2-L, RW3-L also fail TRAIN and VALID > 0. Full columns (flat-day R, ±0.25%
SPY-day split, busiest-session share, median cost/R, exit mix, control R, gate coverage) are in results.csv.

## What was learned
1. The post's model as written has no gross edge on liquid US stocks (gross ~0.000R), and its costs (~0.05R) make it a
   steady -0.075R. The FVG-at-the-break entry is only ~0.02R better than random entries.
2. None of the "don't trade chop" gates removes the regime dependence. The intraday context gates (QQQ from open,
   SPY trend efficiency) make it worse: QQQ-with-you longs lose -0.44R on days SPY closes down (the index trend at
   10:00 does not predict the close, and it concentrates the bet on it).
3. The only gate that helps a little is "SPY's prior day was active" (G6) for longs. With a low-cost filter (RW3-L) the
   row turns +0.039R on both TRAIN and VALID, but t is only 0.86, WF 50%, down days -0.22R, and **one session
   (2025-04-07, the tariff-crash rebound) is 89% of its total R**; without it the row is +0.005R. That is not an edge.
4. G8 "no double break" is a near-no-op (keeps 90%+ of trades): the post's chop symptom is rare at 10:00 on our names.
5. The 1R/2R-by-stop-size switch does not translate: on stocks the FVG-candle stop is almost never "small", so the
   setup is effectively a 1R scalp with a stop at the gap's first candle.

## Implementation notes (DESIGN 0.2 patches as applied)
- Entry code built here (`build.py`, the F1 folder did not exist): OR15 from the 0935-0945 head rows; fresh break at
  tod >= 0950; FVG completing at the break row or the next row; signal 0955-1100; first per symbol-day per side.
- Sim = scan_1028.sim copied and patched: per-trade R and up; exit costs 1c + 1 bp on every exit including targets;
  +2c on stop exits; entry x tod multiplier; x3 extended tier; gap-through stop fill min(stop, high) / max(stop, low).
- Gates applied to F1-A's trade (a failed gate does not re-try a later row). G6 uses lib.daily SPY with HOLD/locked
  rows excluded (coverage 91%); gaps > 5 days in the prior-day series leave it missing.
- gates.walk_forward has 10 usable folds (3-month train windows need consecutive open months).
- Scratch trade parquet was deleted after scoring. Scripts: build.py, score.py; results.csv; parity.json.
