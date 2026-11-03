"""PR5-qqq-impulse-leadlag-long - ex30/peer peer / sympathy / dispersion setup (BDI 2026-11-03, research/bdi/ex30/peer).
Index lead-lag: QQQ rose >= 0.20% over the last two 5-minute bars, and a high-sympathy name (intraday corr with
QQQ >= 0.50, beta >= 0.80) has moved less than a quarter of what its beta implies over the same 10 minutes.
Buys the lagging follower.
Needs lab context columns (YAML `context: ['qqq_fo']`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate; see research/bdi/ex30/peer/NOTES.md. Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t05s1"
WINDOW = (1020, 1500)
CONTEXT = ['qqq_fo']
LAYERS = ['QQQ +0.20% or more over the last 2 bars', 'intraday corr(stock, QQQ) >= 0.50, beta >= 0.80 over >= 6 bars', "stock's 2-bar return <= 0.25 x beta x QQQ 2-bar return", 'bar close 10:20-15:00 ET']


def _features(df):
    """Per-bar peer features on a lab frame (one live symbol-day, or many offline symbol-days sorted by symbol, date, tod).
    Intraday sympathy stats use only returns of bars with tod >= 955 whose previous bar is >= 950 (history frames start
    at 09:50), so live (frame from 09:35) and history compute the same numbers."""
    def col(k):
        return df[k].to_numpy(dtype=float) if k in df else np.full(len(df), np.nan)

    if "symbol" in df and "date" in df:
        key = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    else:
        key = np.zeros(len(df), dtype=int)
    s = pd.DataFrame({"k": key, "c": col("close"), "spy": col("spy_fo"), "qqq": col("qqq_fo"), "tod": col("tod")})
    g = s.groupby("k", sort=False)
    pc, pt = g["c"].shift(1), g["tod"].shift(1)
    ok = (s["tod"] >= 955) & (pt >= 950)
    rs = (s["c"] / pc - 1) * 100
    out = {}
    for ix in ("spy", "qqq"):
        pi = g[ix].shift(1)
        ri = ((1 + s[ix] / 100) / (1 + pi / 100) - 1) * 100
        v = ok & np.isfinite(rs) & np.isfinite(ri)
        x, y = ri.where(v, 0.0), rs.where(v, 0.0)
        t = pd.DataFrame({"k": key, "n": v.astype(float), "x": x, "y": y, "xx": x * x, "yy": y * y, "xy": x * y})
        cs = t.groupby("k", sort=False)[["n", "x", "y", "xx", "yy", "xy"]].cumsum()
        n = cs["n"].to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            mx, my = cs["x"].to_numpy() / n, cs["y"].to_numpy() / n
            cov = cs["xy"].to_numpy() / n - mx * my
            vx = cs["xx"].to_numpy() / n - mx * mx
            vy = cs["yy"].to_numpy() / n - my * my
            out["n_" + ix] = n
            out["corr_" + ix] = cov / np.sqrt(vx * vy)
            out["beta_" + ix] = cov / vx
    c, atr, fo = col("close"), col("atr_d"), col("fromOpen")
    with np.errstate(invalid="ignore", divide="ignore"):
        atrp = atr / c * 100
        out["move"] = (c - c / (1 + fo / 100)) / atr
        out["res_spy"] = (fo - out["beta_spy"] * col("spy_fo")) / atrp
        out["res_qqq"] = (fo - out["beta_qqq"] * col("qqq_fo")) / atrp
        out["prev_res_qqq"] = pd.Series(out["res_qqq"]).groupby(key).shift(1).to_numpy()
        out["prev_c"] = pc.to_numpy()
        out["s2"] = (s["c"] / g["c"].shift(2) - 1).to_numpy() * 100
        out["q2"] = ((1 + s["qqq"] / 100) / (1 + g["qqq"].shift(2) / 100) - 1).to_numpy() * 100
        c950 = s["c"].where(s["tod"] >= 950)
        out["low_before"] = c950.groupby(key).cummin().groupby(key).shift(1).to_numpy()
    out.update(c=c, vwd=col("vwapDistPct"), spy=col("spy_fo"), qqq=col("qqq_fo"), bo=col("breadth_open"), tod=col("tod"))
    return out


def mask(df) -> np.ndarray:
    F = _features(df)
    tod = F["tod"]
    with np.errstate(invalid="ignore"):
        m = (F["n_qqq"] >= 6) & (F["corr_qqq"] >= 0.50) & (F["beta_qqq"] >= 0.80) & (F["q2"] >= 0.20) & (F["s2"] <= 0.25 * F["beta_qqq"] * F["q2"])
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
