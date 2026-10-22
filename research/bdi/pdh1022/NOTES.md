# pdh1022: rework of Failed Prior-Day-High Break Short (0.1 ATR) (CWT14-failbrk-pdh-p10-short), owner 2026-10-22

*Educational only - not financial advice.*

## Verdict (plain English)
**Nothing is viable. 0 of 47 reworks pass the Testing bar, and 0 meet your merit rule.** Every variant loses money
after costs in both train and valid. No new setup is proposed. The best rework is "only when fewer than half of
stocks are above VWAP, with a 1.5x wider stop at the same $ risk" (FBL+S150). It cuts the loss from -0.088R to
-0.038R per trade and keeps half the trades. It is still negative in train (-0.041R) and valid (-0.034R), and it is
no better than random same-minute shorts (excess -0.002 / -0.000R).

The setup is a bet on the market's direction, not an edge in the pattern:
- On Bear days it makes a little (+0.02R/trade).
- On Bull days it loses heavily (-0.23R/trade), and Quiet and Choppy days lose too.
- Random shorts entered at the same minute do as well as it does (-0.084R vs -0.088R).

No filter you can see at entry separates the good days from the bad ones well enough. **Recommendation: let its
Testing-1 forward test run out under rule 20, then move it to the Graveyard. Nothing here replaces it.**

- `PLAN.md` was written and pushed (0a3f2249) before anything was scored, and was not changed afterwards.
- **Configurations scored: 47.**
  - Stage 1: 35 one-knob rows.
  - Stage 2: 12 pairs, chosen on TRAIN only (`stage2.json`).
  - PLAN declared 36 + 12 = 48 by a miscount; stage 1 has 35 rows. The bar was kept at N 48 (conservative).
- **Bars:** study bar max(1.5, sqrt(2 ln 48)) = 2.78. CWT14 lineage N 121,444 -> 4.84.
- **Data:** open two-year history. The locked block 2024-11-01..2025-02-28 was never loaded.
  - TRAIN <= 2025-12.
  - VALID = 2026-01..03 + 07..09-15.
  - HOLD was **not scored**, because no variant qualified.
- Costs in: production + time-of-day.
- No config, setup or exit was changed (market hours). No module was built, because nothing passed.

## Failures first
| result | count |
|---|---|
| Testing bar (exp > 0 in TRAIN and VALID, VALID t >= 2.78, TRAIN+VALID t >= 4.84, beats random) | **0 / 47** |
| Owner merit rule (positive in TRAIN and VALID after costs, beats random in both, >= 30 / 20 trades, no day > 25% of total R) | **0 / 47** |
| Positive in both TRAIN and VALID | **0 / 47** |
| Positive in either TRAIN or VALID | **0 / 47** |
| Beats the parent (d > 0 in TRAIN and VALID, day-block t_improve >= 2.78) | 9 (all still negative) |

- **Lineage bar 4.84:** of the 9 that beat the parent, 5 also clear it on t_improve: S150 9.83, S125 9.20, SO35 6.87,
  FBL+S150 5.76, FBF+S150 5.48.
- **Wide-stop gains are generic, as in top5_1019 / 1021.** S150's excess over random is unchanged (-0.004 / +0.009R).
  A random entry gains about as much from the wider stop.
- **Owner-listed knobs that hurt or did nothing:**
  - Breakeven after +0.35R: -0.009R, t -3.2.
  - Target 0.75R / 1R: +0.000 / -0.001R. Bigger wins, but the win rate falls to 56% / 49%.
  - Target 1R with breakeven after +0.5R: -0.007R.
  - Time stops 30 / 60 min: -0.001R.
  - Deeper confirmation (close >= 0.1 ATR below PDH): -0.014R.
  - Fast failure (back below PDH within 1 bar): -0.005R.
  - Poke on high volume: -0.010R.
  - Window to 14:30: -0.010R.
  - From 10:30: -0.012R.
  - Skip gap-ups > 0.5 / 1 / 2%: -0.002 to -0.005R.
  - First failure of the day only: -0.002R.
  - Re-entry: +0.000R.
- **Train/valid sign flips (no knob is stable):**
  - Wait one bar: d -0.010 TRAIN, +0.021 VALID.
  - Lower-high: -0.008 / +0.018.
  - RS weak: -0.012 / +0.016.
  - Target 0.75R / 1R: -0.008 / +0.014.
  - These look good in valid only.

## 1. Live (paper, 8 sessions 10-12..10-21; `live_diag.py` -> `live_detail.txt`, `live_trades.csv`)
**Overall:** 209 trades, win 62.7% vs break-even 69.7%, avg -0.105R, -21.9R in total. (The brief's -0.139R is
probably on adjusted P/L. This uses `r_multiple`.)

**The asymmetry:** average win +0.45R vs average loss -1.04R.
- 73 stops average -1.09R. 16 losses were worse than -1.1R (3 worse than -1.5R).
- 30 of 78 losers never reached +0.2R (they went straight to the stop).

**By regime:**

| regime | trades | avg R |
|---|---|---|
| Bull (10-15) | 33 | -0.40 |
| Choppy (10-20, 10-21) | 52 | -0.29 |
| Bear | 63 | -0.04 |
| Quiet | 61 | +0.14 |

- 10-21 (Testing 1, Choppy) lost -14.2R: 65% of the total loss.
- 10-15 (Bull) lost -13.2R.

**By time of day:**

| entry window | trades | avg R | total |
|---|---|---|---|
| 09:50-09:59 | 86 | +0.06 | |
| 10:00-10:29 | 87 | -0.21 | -17.8R |
| after 10:30 | 36 | -0.25 | |

- In history, 10:00-10:29 is not worse (-0.074R vs -0.088R overall), and "from 10:00" / "until 11:00" do not help.
  This is live noise.

**Lot stacking:** none. Every symbol-day had exactly 1 lot (no refire configured).

## 2. History diagnosis of the parent (`hist_parent_detail.txt`; TRAIN+VALID n 24,154, 348 sessions)
**Overall:** win 65.3% vs break-even 71.0%, -0.088R/trade, -2,128R in total. Average win +0.45R, average loss -1.10R.

**Why it loses big:**
- 78% of losers lose more than -1.05R (avg -1.16R): the fill goes through the stop, plus the +2c stop cost on a
  0.25-ATR risk unit.
- 56% of losers never reached +0.2R.
- 25% of winners first went -0.5R against.

**By regime:**

| regime | TRAIN avg R | VALID avg R |
|---|---|---|
| Bull | -0.247 | -0.174 |
| Bear | +0.032 | +0.001 |
| Choppy | -0.086 | -0.033 |
| Quiet | -0.092 | -0.067 |

- Bull days alone are -1,150R. The 10 worst days are mostly Bull days (2025-04-02 -88R, 2025-11-25 -86R).

**Nothing else separates winners from losers:**
- **Time of day:** every bucket is between -0.07 and -0.14R.
- **Poke extension above PDH:** -0.08 to -0.09R in every bucket up to 0.5 ATR. Deeper than 0.5 ATR is -0.14R.
- **Bars to failure:** 0 bars -0.108R; 1-3 bars -0.078 to -0.090R.
- **Volume:**
  - Poke-bar volume ratio: flat.
  - Volume fade (failure-bar volume ratio < poke bar's): -0.080R vs -0.096R without the fade.
- **Gap:** flat. Gap-ups of 1-4% are slightly *less* bad.
- **RS vs SPY:** flat.
- **Index and breadth at entry:**

| condition at entry | avg R |
|---|---|
| SPY below VWAP | -0.078 |
| SPY above VWAP | -0.099 |
| QQQ below open | -0.082 |
| QQQ above open | -0.094 |
| breadth falling | -0.074 |
| breadth rising | -0.105 |
| breadth <= 0.3 | -0.032 (best bucket) |

- **Random same-minute shorts:** -0.084R, so the parent's excess is -0.005R. The entry pattern adds nothing.

## 3. Best variants (TRAIN+VALID; all 47 rows in `results.csv`, stage 1 also in `results_stage1.csv`)
| variant | TRAIN avg R (n) | VALID avg R (n) (t) | kept | total R | worst day | excess vs random TRAIN / VALID | Bull / Bear / Choppy / Quiet | d vs parent (t) |
|---|---|---|---|---|---|---|---|---|
| parent (P) | -0.101 (15,329) | -0.066 (8,825) (-4.43) | 100% | -2,128 | -88.4 | -0.005 / -0.004 | -0.225 / +0.022 / -0.059 / -0.083 | - |
| FBL+S150: breadth < 0.5 + stop x1.5 | -0.041 (7,901) | -0.034 (4,738) (-2.13) | 52% | -485 | -45.9 | -0.002 / -0.000 | -0.244 / +0.059 / -0.021 / -0.060 | +0.050 (5.76) |
| FBL+FBF: breadth < 0.5 + falling | -0.047 (4,837) | -0.043 (2,707) (-1.72) | 31% | -342 | -40.3 | +0.025 / +0.012 | -0.251 / +0.069 / -0.014 / -0.090 | +0.043 (3.28) |
| FBF+S150: breadth falling + stop x1.5 | -0.059 (8,330) | -0.024 (4,644) (-1.45) | 54% | -598 | -65.4 | -0.001 / +0.011 | -0.201 / +0.082 / -0.001 / -0.052 | +0.042 (5.48) |
| FSO+S150: SPY below open + stop x1.5 | -0.055 (7,985) | -0.035 (4,337) (-2.15) | 51% | -592 | -69.9 | -0.004 / +0.006 | -0.343 / +0.051 / -0.035 / -0.089 | +0.040 (4.15) |
| S150: stop x1.5, same $ | -0.065 (15,329) | -0.032 (8,825) (-2.54) | 100% | -1,275 | -82.9 | -0.004 / +0.009 | -0.189 / +0.059 / -0.017 / -0.051 | +0.035 (9.83) |
| FBL+SO35: breadth < 0.5 + scale-out 0.35R | -0.057 | -0.047 (-2.63) | 52% | -670 | -45.5 | +0.001 / -0.015 | -0.208 / +0.027 / -0.048 / -0.071 | +0.035 (3.97) |
| SO35: scale-out half at +0.35R | -0.080 | -0.047 (-3.64) | 100% | -1,637 | -77.0 | -0.003 / -0.001 | -0.163 / +0.020 / -0.058 / -0.065 | +0.020 (6.87) |
| FBL: breadth < 0.5 | -0.070 | -0.071 (-3.58) | 52% | -886 | -49.5 | +0.007 / -0.007 | -0.270 / +0.029 / -0.048 / -0.096 | +0.018 (1.97) |
| FBF: breadth falling (3 bars) | -0.086 | -0.056 (-2.70) | 54% | -977 | -72.2 | +0.008 / +0.009 | -0.250 / +0.068 / -0.019 / -0.082 | +0.013 (1.50) |

- **Closest to "slightly more viable": FBL+FBF** (breadth below half *and* falling). It is the only row that beats
  random in both periods (+0.025 / +0.012R), but it still loses -0.047 / -0.043R/trade. Its excess is a
  thinning-of-bad-tape effect, not a positive edge. It is not proposed.
- Every row's Bull-day result stays between -0.18 and -0.47R.

## Live support (if the owner wants the "least bad" form anyway)
These are not proposals:
- **FBL / FBF:** module only, via LabStrategy `context: [breadth]`.
  - Breadth falling needs the breadth 3 bars back. The live context gives the current bar only, so a module must keep
    its own history.
  - Caveat: the lab context has no 09:35-09:45 breadth, so FBF never fires at 09:50 in the backtest.
- **S150:** a GEOM "S" module at the same $ (see top5_1019).
- **SO35:** config `scale_out_r` + `live_scale_out`.

## Files
- `live_diag.py` -> `live_detail.txt`, `live_trades.csv` (paper).
- `pdh_scan.py`: harness. PLAN calls it `scan.py`; it was renamed to avoid a clash with refire1014's `scan` module on
  sys.path. Code unchanged otherwise.
  - Reuses top5_1019 `build_paths` / `sim` / `next_after` and top5_1015's random-control pool.
  - New kernel `_b3s`. **Parity on 2025-06:**
    - `_b3s` flags == `cwt_live_lib.b3` at p 0.05 / 0.10 / 0.20 (5,511 flags at p 0.10).
    - Parent == `gates.lab_trades` trade for trade: 1,376 / 1,376 matched, mean |d| 3.5e-5R, 100% within 0.01R
      (`parity_parent.json`).
  - Scratch trades in `$SCR/pdh1022` (not committed).
- `report.py` -> `results_stage1.csv`, `hist_parent_detail.txt`, `stage2.json`, `results.csv`, `summary.json`.
- `backlog_proposals.jsonl`: 2 lines (failed study + the best rework as `rework`). Not appended to
  research/backlog.jsonl.

Educational only — not financial advice.
