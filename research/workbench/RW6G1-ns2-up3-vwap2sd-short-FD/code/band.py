"""VWAP band table per 5-min bar (tod = bar close) from 1-min RTH bars, using the parent module's own vwap_band_block
(exact live logic) for k = 1.5 / 2.0 / 2.5 / 3.0, plus VWAP and SD for distance layers."""
import importlib.util, numpy as np, pandas as pd
_sp = importlib.util.spec_from_file_location("rw6g1", "/home/user/MCF/research/bdi/fullday/RW6G1-ns2-up3-vwap2sd-short-FD.py")
M = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(M)
KS = (1.5, 2.0, 2.5, 3.0)
def table(m1, symbol, date):
    """m1: 1-min bars of ONE session (tz NY index, open/high/low/close/volume)."""
    d5 = m1.resample("5min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["open"])
    end = d5.index + pd.Timedelta(minutes=5)
    out = pd.DataFrame({"symbol": symbol, "date": date, "tod": (end.hour * 100 + end.minute).astype(int)})
    h, l, c, v = (d5[x].to_numpy(float) for x in ("high", "low", "close", "volume"))
    tp = (h + l + c) / 3; cv = np.cumsum(v); cv[cv == 0] = np.nan
    vw = np.cumsum(tp * v) / cv; sd = np.sqrt(np.clip(np.cumsum(tp * tp * v) / cv - vw * vw, 0, None))
    out["vw5"] = vw; out["sd5"] = sd; out["c5"] = c
    for k in KS:
        out[f"blk{int(k*10)}"] = M.vwap_band_block(d5, k)
    # highest close / VWAP SD multiple reached so far today (how stretched the run was)
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (c - vw) / sd
    out["zmax"] = pd.Series(z).cummax().values; out["z5"] = z
    return out
