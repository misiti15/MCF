"""RD3-vwapfade-band1-slope-inplay-long-FD - BDI Reddit study 2026-10-09 (research/bdi/reddit, NOTES.md R03 + amendment A).
Reddit 'VWAP rubber band / fade to VWAP' (long side): after a close more than 1 daily ATR below VWAP, the first close
back above VWAP - 1 ATR; 5-min SMA20 slope positive; |move from the open| >= 2% ('stock in play').
Side long, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). 5-minute bars, values known at the bar close.
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
2-year open history (426 sessions, locked block excluded, production costs): n 151 (0.35/day), win 0.543,
exp +0.003R, day-clustered t 0.03 (t_required 3.96); up -0.030 / flat -0.086 / down +0.091; walk-forward share 0.50
(4 folds); plateau mean -0.040; ex-best-day -0.017. FAILS the live-probation bar. Best-few module only (amendment A).
NOT scored on the rule-19 locked block. Educational only - not financial advice."""
import numpy as np

SIDE = "long"
GEOM = "t1s1"
LAYERS = ["close crosses back above VWAP - 1.0 daily ATR (after a close below it)", "5-min SMA20 slope > 0",
          "|move from the open| >= 2%", "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])"]


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    n = len(df)
    if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        new = np.r_[True, key[1:] != key[:-1]]
    else:
        new = np.r_[True, np.zeros(max(0, n - 1), bool)]

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        p[new] = np.nan
        return p

    c, atr = col("close"), col("atr_d")
    vw = c / (1 + col("vwapDistPct") / 100)
    z = (c - vw) / atr                                   # VWAP stretch in daily ATR
    with np.errstate(invalid="ignore"):
        return ((z > -1.0) & (prev(z) <= -1.0) & (col("sma20_slope_pct") > 0) & (np.abs(col("fromOpen")) >= 2.0)
                & (col("tod") >= 950))
