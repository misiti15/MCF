# pdl1030 / combo: NOTES

*Educational only — not financial advice.*

**Result: nothing passes.** 10 configurations scored (6 combos + 4 parity re-scores), all pre-declared in PLAN.md, nothing added.
N = 121566 + 3 x 10 = 121596 -> BAR90 t >= 4.355. TRAIN+VALID only (348 sessions); HOLD months and the locked block never loaded.

Parity (diff <= 0.0000 vs swarm15 / symbol-quality / tape-flip): p05 -0.0677/-0.0675, p10 -0.0861/-0.0912 (TV -0.0880),
p05 S3 -0.0210/-0.0173, TC-F (short-leg check) -0.0392/-0.0498.

| id | rule | TRAIN | VALID | t | /sess | wf% | up | down | w/o best day | best-day share |
|---|---|---|---|---|---|---|---|---|---|---|
| K3 | S3 + cost5 + SPY-VWAP flip | +0.0062 | -0.0003 | 1.18 | 54.3 | 58.8 | -0.000 | +0.007 | +0.0027 | 18.7% |
| K2 | S3 + cost5 + breadth flip | +0.0052 | -0.0023 | 0.63 | 54.3 | 58.8 | -0.000 | +0.004 | +0.0012 | 33.5% |
| K5 | S3 + cost10 + breadth flip | +0.0002 | -0.0045 | -0.69 | 114.4 | 41.2 | -0.005 | +0.001 | -0.0022 | - |
| K6 | S3 + cost5 + (SPY>VWAP or SPY gap<=-0.5%) | +0.0036 | -0.0123 | -0.68 | 30.8 | 35.3 | +0.026 | -0.063 | -0.0053 | - |
| K4 | S3 + cost5, tape-score sizing | +0.0012 | -0.0117 | -0.96 | 54.3 (29.3 risk units) | 29.4 | +0.028 | -0.051 | -0.0059 | - |
| K1 | S3 + cost5 + SPY>VWAP | +0.0027 | -0.0139 | -0.98 | 26.0 | 29.4 | +0.022 | -0.068 | -0.0060 | - |

What it shows:
- Stacking the three real levers (S3 wide stop at the same $, cost floor, tape flip) takes the p05 signal from -0.068R to about 0,
  with the down-session loss gone (flip rows: down-day R about +0.005), while keeping 54/session (>= 25 floor) or 114/session (K5).
- Even the best curve (K3) is only +0.003R TV, t 1.18, and VALID is flat (-0.0003). It is far from the bar (t 4.355) and fails VALID > 0.
  The gross edge of this signal is about +0.01-0.02R, so no combination of these pieces lifts it to a tradeable edge after costs.
- Long-only tape gates (K1, K6, K4) stay positive on TRAIN only. On VALID they lose on down sessions (-0.05..-0.07).

Known at entry: S3/cost floor (price, tier, time, ATR), SPY vwapDistPct and breadth at the signal-bar close, SPY gap at the open.
spy_day (EOD) is used only for the descriptive up/down split.

No module was written, because nothing passed. Files: PLAN.md, build.py, score.py, score_out.txt, results.csv, cache/ (3.9 MB).
