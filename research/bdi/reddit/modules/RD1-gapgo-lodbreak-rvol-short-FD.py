"""RD1-gapgo-lodbreak-rvol-short-FD - BDI Reddit study 2026-10-09 (research/bdi/reddit, NOTES.md R04 + amendment A).
Reddit 'gap and go' (short mirror, full-day proxy without premarket data): the stock gapped down >= 2% and the close
breaks below the prior low of day for the first time from 09:50; this bar's volume >= 1.5x its average ('volume
confirms'). Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). 5-minute bars, values known at the bar close.
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
2-year open history (426 sessions, locked block excluded, production costs): n 3,895 (9.1/day), win 0.520,
exp +0.010R, day-clustered t 0.23 (t_required 3.96 for N = 2,551); up -0.244 / flat -0.082 / down +0.213;
walk-forward share 0.53; ex-best-day -0.015. FAILS the live-probation bar (regime, t, walk-forward, ex-best-day):
a down-market beta trade, not an edge. Best-few module only (amendment A). NOT scored on the rule-19 locked block.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["gap down >= 2%", "close breaks below the prior low of day, first time from 09:50",
          "volume ratio >= 1.5", "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])"]


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

    c, atr, tod = col("close"), col("atr_d"), col("tod")
    lod = c - col("dist_lod_atr") * atr
    with np.errstate(invalid="ignore"):
        ev = (c < prev(lod)) & (col("gap") <= -2.0) & (tod >= 950)
    first = np.zeros(n, bool)                # first such bar of the symbol-day (counted from 09:50)
    if ev.any():
        idx = np.flatnonzero(ev)
        g = grp[idx]
        first[idx[np.r_[True, g[1:] != g[:-1]]]] = True
    with np.errstate(invalid="ignore"):
        return first & (col("volumeRatio") >= 1.5)
