# rdt1030 / F5 fvg-context: one indicator per row on two fixed base entries — RESULTS

*Educational only — not financial advice.* Backtest only (2-year open history, TRAIN + VALID). Nothing here is live or paper.

## Verdict: 0 of 23 counted configs pass. No finalist, so no mask module.
- **Configs scored by F5: 23.** That is 18 pre-declared in PLAN.md plus 5 rule-18 rework configs, declared in the PLAN
  amendment before they were scored. The base rows F1-A L/S and F4-01 L are shown as reference parents only; they are
  F1's and F4's configs.
- **Bar:** N = 2,000 + 137 (108 DESIGN + 24 F1-F4 rework + 5 F5 rework) = 2,137, so **t_req = 3.52**. A row must also have
  WF >= 54%, avg R > 0 on TRAIN and on VALID, >= 3 trades/session, up-day and down-day R > 0, and beat the random control.
- **Base check:** the trade cache reproduces the parents exactly. F1-A L: n 48,612, -0.0753R. F1-A S: n 48,807, -0.0741R
  (same as F1/F2). F4-01 L: n 6,498, -0.0306R (same as F4). Entry and sim code are imported from F2/build.py and
  F4/build.py, not re-written. The harness parity (CWT14 p05 -0.0677) was matched exactly by F2 and F4 on the same frames.
- **Sessions:** 348 (TRAIN 2024-10 and 2025-03..12; VALID 2026-01..03 and 2026-07..2026-09-15). The locked block and HOLD
  months were never loaded.

## Every row (all fail)
Avg R is net of costs. "Kept" means trades kept / top-decile base winners kept, relative to the base row. "w/o best day"
is avg R without the best session. The best-day share is undefined because total R < 0 on every row.

| id | setup name | n/sess | win | W/L (R) | avg R | TRAIN | VALID | t_day | WF% | up / down-day R | w/o best day | ctrl R | kept / top10 kept | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1-A-L | 15-min Opening Range Break with Gap, Long (base, reference) | 139.7 | 0.501 | 0.82/0.97 | -0.075 | -0.079 | -0.068 | -3.61 | 10 | +0.057 / -0.271 | -0.084 | -0.094 |  | t -3.61<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F1-A-S | 15-min Opening Range Break with Gap, Short (base, reference) | 140.2 | 0.496 | 0.83/0.97 | -0.074 | -0.098 | -0.036 | -3.30 | 0 | -0.283 / +0.097 | -0.079 | -0.094 |  | t -3.3<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F4-01-L | Prior-Day-Low Sweep then 15-min Gap, Long (base, reference) | 18.7 | 0.492 | 0.51/0.55 | -0.031 | -0.042 | -0.014 | -1.18 | 50 | +0.099 / -0.183 | -0.038 | -0.031 |  | t -1.18<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I1-L | 15-min Opening Range Break with Gap + VWAP Side, Long | 139.7 | 0.501 | 0.82/0.97 | -0.075 | -0.079 | -0.068 | -3.61 | 10 | +0.057 / -0.271 | -0.084 | -0.094 | 100 / 100 | t -3.61<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I1-S | 15-min Opening Range Break with Gap + VWAP Side, Short | 140.2 | 0.496 | 0.83/0.97 | -0.074 | -0.098 | -0.036 | -3.30 | 0 | -0.283 / +0.097 | -0.079 | -0.094 | 100 / 100 | t -3.3<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-I2-L | 15-min Opening Range Break with Gap + RSI Momentum, Long | 103.0 | 0.497 | 0.81/0.97 | -0.083 | -0.083 | -0.082 | -4.32 | 10 | +0.033 / -0.251 | -0.087 | -0.102 | 74 / 70 | t -4.32<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I2-S | 15-min Opening Range Break with Gap + RSI Momentum, Short | 105.0 | 0.498 | 0.83/0.96 | -0.071 | -0.091 | -0.038 | -2.84 | 0 | -0.282 / +0.101 | -0.078 | -0.092 | 75 / 79 | t -2.84<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-I3-L | 15-min Opening Range Break with Gap + Not Overextended (RSI5), Long | 87.2 | 0.504 | 0.82/0.97 | -0.068 | -0.064 | -0.076 | -2.75 | 10 | +0.073 / -0.283 | -0.082 | -0.089 | 62 / 63 | t -2.75<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I3-S | 15-min Opening Range Break with Gap + Not Overextended (RSI5), Short | 87.7 | 0.501 | 0.83/0.96 | -0.066 | -0.086 | -0.033 | -2.91 | 20 | -0.281 / +0.110 | -0.073 | -0.090 | 62 / 59 | t -2.91<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-I4-L | 15-min Opening Range Break with Gap + Order Flow With You, Long | 56.6 | 0.495 | 0.82/0.96 | -0.081 | -0.090 | -0.066 | -3.94 | 20 | +0.036 / -0.245 | -0.086 | -0.100 | 40 / 41 | t -3.94<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I4-S | 15-min Opening Range Break with Gap + Order Flow With You, Short | 61.4 | 0.505 | 0.83/0.96 | -0.056 | -0.079 | -0.016 | -2.32 | 0 | -0.259 / +0.107 | -0.062 | -0.083 | 44 / 47 | t -2.32<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-I5-L | 15-min Opening Range Break with Gap + Strong Move From Open, Long | 74.9 | 0.501 | 0.81/0.94 | -0.062 | -0.059 | -0.067 | -2.52 | 10 | +0.077 / -0.264 | -0.074 | -0.080 | 54 / 63 | t -2.52<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I5-S | 15-min Opening Range Break with Gap + Strong Move From Open, Short | 75.0 | 0.497 | 0.83/0.94 | -0.059 | -0.078 | -0.029 | -2.32 | 20 | -0.256 / +0.101 | -0.065 | -0.087 | 54 / 63 | t -2.32<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-I6-L | 15-min Opening Range Break with Gap + Above/Below SMA50, Long | 114.4 | 0.498 | 0.81/0.97 | -0.081 | -0.086 | -0.071 | -4.28 | 10 | +0.036 / -0.255 | -0.085 | -0.101 | 82 / 78 | t -4.28<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I6-S | 15-min Opening Range Break with Gap + Above/Below SMA50, Short | 115.9 | 0.499 | 0.83/0.96 | -0.066 | -0.090 | -0.029 | -2.81 | 0 | -0.274 / +0.101 | -0.072 | -0.092 | 83 / 86 | t -2.81<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-I7-L | 15-min Opening Range Break with Gap + MarcoFlow Heat, Long | 26.3 | 0.495 | 0.80/0.90 | -0.060 | -0.076 | -0.037 | -2.40 | 30 | +0.052 / -0.230 | -0.070 | -0.079 | 19 / 34 | t -2.4<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I7-S | 15-min Opening Range Break with Gap + MarcoFlow Heat, Short | 13.1 | 0.481 | 0.83/0.95 | -0.090 | -0.180 | -0.005 | -2.13 | 30 | -0.325 / +0.127 | -0.103 | -0.127 | 9 / 17 | t -2.13<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-I8-L | 15-min Opening Range Break with Gap + Market Breadth, Long | 73.0 | 0.509 | 0.82/0.97 | -0.059 | -0.056 | -0.065 | -1.77 | 10 | +0.061 / -0.363 | -0.075 | -0.070 | 52 / 55 | t -1.77<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-I8-S | 15-min Opening Range Break with Gap + Market Breadth, Short | 69.8 | 0.498 | 0.84/0.97 | -0.070 | -0.076 | -0.057 | -1.86 | 20 | -0.457 / +0.112 | -0.080 | -0.081 | 50 / 52 | t -1.86<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-J1-L | Prior-Day-Low Sweep then 15-min Gap + Above VWAP, Long | 17.0 | 0.495 | 0.49/0.54 | -0.026 | -0.030 | -0.021 | -1.14 | 60 | +0.086 / -0.168 | -0.034 | -0.023 | 91 / 84 | t -1.14<3.52; TRAIN<=0; VALID<=0; down-day<=0; <=control |
| F5-J2-L | Prior-Day-Low Sweep then 15-min Gap + Buyers In Control, Long | 5.8 | 0.489 | 0.48/0.51 | -0.022 | -0.030 | -0.011 | -0.90 | 60 | +0.076 / -0.152 | -0.031 | -0.023 | 31 / 28 | t -0.9<3.52; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-RW1-L | 15-min Opening Range Break with Gap + Very Strong Move From Open (rework), Long | 34.0 | 0.499 | 0.81/0.91 | -0.053 | -0.045 | -0.066 | -1.83 | 20 | +0.087 / -0.253 | -0.067 | -0.066 | 24 / 34 | t -1.83<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-RW1-S | 15-min Opening Range Break with Gap + Very Strong Move From Open (rework), Short | 33.8 | 0.495 | 0.82/0.90 | -0.049 | -0.064 | -0.026 | -1.57 | 40 | -0.237 / +0.100 | -0.060 | -0.078 | 24 / 34 | t -1.57<3.52; WF<54; TRAIN<=0; VALID<=0; up-day<=0 |
| F5-RW2-L | 15-min Opening Range Break with Gap + Order Flow + Low Cost (rework), Long | 44.5 | 0.489 | 0.83/0.91 | -0.061 | -0.058 | -0.065 | -2.83 | 30 | +0.062 / -0.234 | -0.065 | -0.092 | 32 / 40 | t -2.83<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
| F5-RW2-S | 15-min Opening Range Break with Gap + Order Flow + Low Cost (rework), Short | 48.8 | 0.506 | 0.84/0.90 | -0.019 | -0.033 | +0.003 | -0.77 | 40 | -0.230 / +0.148 | -0.026 | -0.076 | 35 / 47 | t -0.77<3.52; WF<54; TRAIN<=0; up-day<=0 |
| F5-RW3-L | Prior-Day-Low Sweep then 15-min Gap + Above VWAP + Buyers In Control (rework), Long | 5.6 | 0.490 | 0.48/0.50 | -0.021 | -0.029 | -0.010 | -0.85 | 50 | +0.075 / -0.152 | -0.030 | -0.021 | 30 / 25 | t -0.85<3.52; WF<54; TRAIN<=0; VALID<=0; down-day<=0 |
Every row has >= 3 trades/session except F5-J2-L, F5-RW3-L and F5-I7-S (5.6-13/session, which still clears 3). Every row
beats its random control except F5-J1-L. All other gates fail on every row. Full columns are in results.csv: flat-day R,
±0.25% SPY-day split, busiest-session share, median cost/R, exit mix, share of 2R targets and indicator coverage (100%).

## What was learned
1. **No single indicator rescues either entry.** On F1-A the eight indicators move avg R by -0.007 to +0.019R. Every
   F1-A-based row stays between -0.05 and -0.09R, with t between -1.6 and -4.3. On F4-01, VWAP side and buyPressure move
   it by +0.005 to +0.009R, to about -0.02R.
2. **The regime split survives every filter.** Long rows make +0.03 to +0.09R on SPY up days and lose 0.15-0.36R on down
   days. Short rows are the mirror. The index-context row (I8, breadth) makes the split *worse*: longs lose -0.36R on down
   days and shorts -0.46R on up days. The 10:00 breadth reading concentrates the bet on a close it does not predict. This
   is the same pattern F2-G4 showed with QQQ from open.
3. **VWAP side (I1) is a no-op on the ORB entry.** A close above the 15-min high with a fresh FVG is above VWAP on 99.99%
   of trades. The post's "trade with the structure" idea is already built into the break.
4. **Momentum confirmations hurt longs slightly.** RSI(14) >= 55, buyPressure >= +0.20 and SMA50 side all give -0.081 to
   -0.083R, against -0.075 for the base. "Not exhausted" (RSI5 <= 90) and a strong move from open help by about 0.007 and
   0.013R, but neither keeps >= 80% of trades with >= 90% of the top winners, so neither is proposable as a filter.
5. **Best near-miss: F5-RW2-S** (short ORB with gap + sellers in control + cost <= 10% of R). It makes -0.019R overall
   (TRAIN -0.033, VALID +0.003), t -0.77, and is +0.057R above its random control. It still loses -0.23R on SPY up days.
   It is the cost floor doing most of the work (F1-G/RW1 showed the same gradient), not an edge.
6. **Costs remain the binding constraint.** The ORB-with-gap entry is about 0.02R better than random liquid names at the
   same bar, against a median round-trip cost of about 0.05R per R. F4-01's stops are wide, so its cost is low (0.025R),
   but 80-85% of trades ride to the 15:55 flatten with about zero gross edge.

## Implementation notes
- `build.py` imports `F2/build.py` (`kernel`, patched `sim`, `_cut` monkeypatches) and `F4/build.py` (`seg_arrays`,
  `run_signal("PDL", DOL, formation)`, patched `sim`). Both modules are registered in `sys.modules` for numba caching,
  and the numba cache is redirected to scratch, so no file in the F2/F4 folders was written.
- Indicators are read at the signal row i (5-min bar close): `vwapDistPct`, `rsi`, `rsi5`, `buyPressure`,
  `sma50_dist_pct` and `heat` from the frame row, `breadth` from `lib.load_context` at (date, tod), and move from open =
  (close - close/(1 + fromOpen/100)) / ATR_d.
- Gates are applied to the base trade (the first signal per symbol-day per side). A failed gate does not re-try a later row.
- Random control: K = 5 random other universe symbols (adv20 >= $95M) at the same signal bar, with the same side, R in
  ATR units and target multiple, through the same patched sim. Seed [20261030, yyyymm].
- `score.py`: `stats`, `passes` and `fails` are copied verbatim from F2/score.py (day-clustered t, gates.walk_forward with
  10 usable folds). Set `RDT_N_SWARM` to rescore at a different N.
- The scratch trade cache (11 MB) was deleted after scoring.
