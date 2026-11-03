"""PR2-decoupled-quiet-breakdown-short - ex30/peer peer / sympathy / dispersion setup (BDI 2026-11-03, research/bdi/ex30/peer).
Shorts a name that has DECOUPLED from the tape on a quiet index (SPY within +-0.25% of its open, intraday
correlation with SPY within +-0.15) and is breaking down on its own: >= 1 daily ATR below its open, under VWAP,
closing at a new low of the day (09:50 onward). Quiet-day design.
Needs lab context columns (YAML `context: ['spy_fo']`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate; see research/bdi/ex30/peer/NOTES.md. Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t1s1"
WINDOW = (1030, 1430)
CONTEXT = ['spy_fo']
LAYERS = ['abs(SPY from open) <= 0.25%', 'abs(intraday corr(stock, SPY)) <= 0.15 over >= 8 bars from 09:55', 'move from open <= -1.0 daily ATR', 'close < VWAP', 'close <= lowest earlier close since 09:50', 'bar close 10:30-14:30 ET']


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
        m = (F["n_spy"] >= 8) & (np.abs(F["spy"]) <= 0.25) & (np.abs(F["corr_spy"]) <= 0.15) & (F["move"] <= -1.0) & (F["vwd"] < 0) & (F["c"] <= F["low_before"])
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
