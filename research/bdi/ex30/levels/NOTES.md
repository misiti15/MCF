Educational only — not financial advice

# ex30 / levels — price levels and magnets (results)

Pre-declared in `PLAN.md` (committed 864b265cb before anything was scored). Scripts: `score.py` (harness, independent
pandas re-implementation of every rule), `report.py` (tables); modules in `modules/` (+ shared `levels_lib.py`).
Outputs: `results.csv`, `parity.csv`. **Configurations scored: 15** (5 primaries + 10 pre-declared neighbours), nothing
else (the PLAN's calibration was signal counts only, on 2025-06, no outcome column). Locked block 2024-11-01..2025-02-28
never loaded (asserted). Costs in (production 1c + 1 bps per side, +2c on stops, time-of-day entry multiplier).
Backtest only (2-year lab frames, light gate); nothing here is a paper or live result.
Rule-change context: new setups scored on fixed historical frames; no ledger rule change (sizing, stops, filters,
timing, moves) applies to them.

**Not buildable live (dropped up front):** prior-week high/low, multi-day range edges, 52-week / all-time proximity and
prior-day VWAP. The live daily prior (`mcf.data.priors.Prior`) has only prev close / high / low, ATR, ADV, sma20, and the
mask sees no prior-day rows. Adding them needs a new prior field (mcf/ change), not done here.

## Failures first: 0 of 5 primaries (0 of 15 configs) pass the light lane gate

Sessions: TRAIN 234, VALID 114. Day type = SPY open-to-close, +-0.25%.

| setup (primary) | side/geom | TRAIN avg R (t) | VALID avg R (t) | trades/session | vs random TRAIN / VALID | up / down / quiet (TRAIN+VALID) | gate |
|---|---|---|---|---|---|---|---|
| LV1-round-firsttouch-reject-short | short t05s1 | -0.142 (-2.0) | -0.069 (-2.3) | 16.1 | -0.013 / +0.013 | -0.167 / -0.011 / -0.115 | fail (R) |
| LV2-round-secondtouch-break-long | long t1s1 | +0.007 (0.1) | -0.077 (-1.9) | 13.6 | +0.016 / -0.024 | +0.099 / -0.150 / -0.107 | fail (VALID R) |
| LV3-gapup-halffill-short | short t1s1 | +0.040 (0.3) | -0.157 (-3.2) | 8.1 | -0.047 / -0.064 | -0.302 / +0.172 / -0.182 | fail (VALID R); TRAIN carried by big days |
| LV4-gapdn-filled-retest-long | long t05s1 | -0.058 (-1.5) | -0.038 (-1.5) | 37.7 | -0.016 / +0.021 | +0.026 / -0.129 / -0.124 | fail (R, too busy) |
| LV5-flatopen-pclose-stretch-short | short t1s1 | -0.130 (-3.9) | -0.064 (-1.2) | 14.1 | +0.019 / +0.040 | -0.184 / +0.069 / -0.098 | fail (R) |

Parity (module vs harness, bar by bar, 2026-09 to 09-15, inside window + ADV): exact for all 5 (LV1 135, LV2 182,
LV3 201, LV4 4,714, LV5 528 bars).

One-big-day check: every VALID total is negative (no carry). TRAIN: LV3's TRAIN total is carried by single sessions
(best-day share 3.04 = the best session is 3x the whole TRAIN total; without it -0.104R); LV2's TRAIN share 6.75
(without best day -0.043R). Both small positive TRAIN numbers are therefore not records.

Neighbours (all in `results.csv`) sit on the primaries (plateau, no threshold accident): LV1 wick 0.30/0.50 -0.12/-0.17
TRAIN, -0.07 VALID; LV2 pull 0.30 -0.026/-0.068 (28.8/session), pull 0.50 +0.076/-0.126; LV3 gap 1.0%/2.5% +0.03/+0.10
TRAIN, -0.16/-0.11 VALID; LV4 gap -0.5%/-2.0% -0.08/-0.07 TRAIN, -0.06/-0.01 VALID; LV5 stretch 0.75/1.25 -0.11/-0.10
TRAIN, -0.05/-0.06 VALID.

## What the level family says

1. **No level by itself beats costs.** Vs-random excess is within +-0.06R everywhere; the level adds almost nothing to a
   random entry of the same side and window.
2. **Still direction bets, and still no quiet-day edge.** Every primary is negative on quiet days in both splits
   (except LV5's neighbours, ~0 on VALID quiet). Longs win only on up days (LV2 +0.099), shorts only on down days (LV3
   +0.172). The level shapes did not fix the live book's quiet-day hole.
3. **Least bad, if the owner wants exploratory exposure anyway:** LV5 (flat-open stretch short) beats random in both
   splits (+0.019 / +0.040, t 0.6 / 1.0; stretch 1.25 neighbour +0.053 / +0.070, t 1.1 / 1.5) and is positive on down
   days in both splits; LV4 gap -2.0% neighbour is the nearest to the gate (-0.072 / -0.013, 12.4/session). Neither
   clears -0.02 on TRAIN.
4. Gap-fill magnet (LV3) is the clearest regime bet: +0.27R TRAIN down days, -0.35R TRAIN up days.
