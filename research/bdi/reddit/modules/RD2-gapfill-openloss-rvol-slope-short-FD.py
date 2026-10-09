"""RD2-gapfill-openloss-rvol-slope-short-FD - BDI Reddit study 2026-10-09 (research/bdi/reddit, NOTES.md R05 + amendment A).
Reddit 'gap fill / gap fade' (short side): the stock gapped up >= 2% and the close crosses below the day's open for the
first time from 09:50; this bar's volume >= 1.5x its average; 5-min SMA20 slope negative ('with the trend').
Side short, exit t05s1 (R = 0.25 x daily ATR, exit by 15:55). 5-minute bars, values known at the bar close.
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
2-year open history (426 sessions, locked block excluded, production costs): n 380 (0.89/day), win 0.653,
exp +0.006R, day-clustered t 0.20 (t_required 3.96); up -0.035 / flat +0.012 / down +0.027; walk-forward share
0.43; plateau mean -0.041; ex-best-day -0.001. FAILS the live-probation bar. Best-few module only (amendment A).
NOT scored on the rule-19 locked block. Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = ["gap up >= 2%", "close crosses below the day's open, first time from 09:50", "volume ratio >= 1.5",
          "5-min SMA20 slope < 0", "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])"]


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    n = len(df)
    if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        new = np.r_[True, key[1:] != key[:-1]]
    else:
        new = np.r_[True, np.zeros(max(0, n - 1), bool)]
    grp = np.cumsum(new)

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        p[new] = np.nan
        return p

    fo, tod = col("fromOpen"), col("tod")
    with np.errstate(invalid="ignore"):
        ev = (fo < 0) & (prev(fo) >= 0) & (col("gap") >= 2.0) & (tod >= 950)
    first = np.zeros(n, bool)
    if ev.any():
        idx = np.flatnonzero(ev)
        g = grp[idx]
        first[idx[np.r_[True, g[1:] != g[:-1]]]] = True
    with np.errstate(invalid="ignore"):
        return first & (col("volumeRatio") >= 1.5) & (col("sma20_slope_pct") < 0)
