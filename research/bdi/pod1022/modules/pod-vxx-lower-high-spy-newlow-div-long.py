"""pod-vxx-lower-high-spy-newlow-div-long - SPY new session low while VXX makes a lower high (volatility divergence,
LONG on SPY / QQQ / IWM).

Source: Tim Ord, The Ord Oracle (StockCharts) - 'VIX lower high while SPY makes a lower low' bullish divergence,
applied there on daily bars; translated to 5-minute bars with the VXX ETN as the intraday VIX proxy.
URL: https://stockcharts.com/articles/tac/2015/09/tim-ord-the-ord-oracle-september-30-2015.html

VARIANT of pod-axia-spy-newlow-divergence-long and pod-raschke-blindfold-breadth-div. Stated change: the divergence
is measured on the volatility ETN (VXX), not on a stock's own low or on breadth.

Rules (plain English, LONG). SYMBOLS traded: SPY, QQQ, IWM (signal always from SPY + VXX).
  1. Bar t0 closes 10:30-14:30: SPY's t0 low is a new session low at least 0.10% below SPY's previous running low of
     day (the low of day as of the bar before t0; includes 09:30-09:45).
  2. On t0 VXX's high is below its session high so far (VXX lower high), and that VXX session high was set >= 4 bars
     before t0 (VXX's running high of day did not change over the 3 bars before t0).
  3. VXX at t0 is up less than 4% from its own open (no panic).
  4. Within the next 3 bars, the first 5-minute SPY close above SPY's t0 high. Entry: that bar's close, on the traded
     symbol (same bar).
  Stop (GEOM S): the traded symbol's t0 low - 0.05 x atr_d. Target: the session VWAP (as of the entry bar) if it is
  >= entry + 0.25 x atr_d, else entry + 1R; flat 15:55.
VXX rows are read from the open history frames of the same month (never the locked block); only bars up to the
decision bar are used. No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1035, 1445)
SYMBOLS = ["SPY", "QQQ", "IWM"]
LAYERS = ["t0 10:30-14:30: SPY new LOD >= 0.10% below prior LOD", "VXX t0 high < VXX HOD set >= 4 bars earlier",
          "VXX fromOpen < 4%", "within 3 bars SPY closes > SPY t0 high", "stop t0 low - 0.05 ATR",
          "target VWAP if >= 0.25 ATR away else 1R"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r25_util as U  # noqa: E402

_ST = {}


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def target_price(f, i, stop):
    return _stash(f, i, 1)


def _signals(df, b):
    """(date, t0 tod, entry tod) pairs from SPY + VXX, point in time."""
    sym = df["symbol"].astype(str).to_numpy()
    sp = sym == "SPY"
    if not sp.any():
        return None
    s = pd.DataFrame({"date": df["date"].astype(str).to_numpy()[sp], "tod": b["tod"][sp], "sh": b["h"][sp],
                      "sl": b["l"][sp], "sc": b["c"][sp], "slod": b["lod"][sp]})
    s = s.drop_duplicates(["date", "tod"]).sort_values(["date", "tod"]).reset_index(drop=True)
    s["slodp"] = s.groupby("date")["slod"].shift(1)
    v = U.vxx_rows(df)
    if v is None:
        return None
    v = v.copy()
    g = v.groupby("date")["vhod"]
    v["vhod1"], v["vhod4"] = g.shift(1), g.shift(4)
    s = s.merge(v[["date", "tod", "vh", "vfo", "vhod1", "vhod4"]], on=["date", "tod"], how="left")
    with np.errstate(invalid="ignore"):
        t0 = (s["tod"] >= 1030) & (s["tod"] <= 1430)
        t0 &= s["sl"] < s["slodp"] * (1 - 0.001)                                          # (1)
        t0 &= (s["vh"] < s["vhod1"] * (1 - 1e-5)) & ((s["vhod1"] - s["vhod4"]).abs() <= 1e-5 * s["vhod1"].abs())  # float tol: HOD is rebuilt from dist_hod_atr  # (2)
        t0 &= s["vfo"] < 4.0                                                              # (3)
    out = []
    dd, tt, hh, cc = s["date"].to_numpy(), s["tod"].to_numpy(), s["sh"].to_numpy(float), s["sc"].to_numpy(float)
    for i in np.flatnonzero(t0.to_numpy()):
        for j in range(i + 1, min(i + 4, len(s))):
            if dd[j] != dd[i]:
                break
            if cc[j] > hh[i]:                                                             # (4)
                out.append((dd[i], int(tt[i]), int(tt[j])))
                break
    return pd.DataFrame(out, columns=["date", "t0", "tod"]).drop_duplicates(["date", "tod"], keep="first")


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n:
        return z
    b = U.base(df)
    sig = _signals(df, b)
    if sig is None or not len(sig):
        return z
    rows = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].astype(str).to_numpy(),
                         "tod": b["tod"], "l": b["l"]})
    m0 = rows[["symbol", "date", "tod"]].merge(sig, on=["date", "tod"], how="left")
    assert len(m0) == n
    t0 = m0["t0"].to_numpy(float)
    lt0 = m0[["symbol", "date", "t0"]].rename(columns={"t0": "tod"}).merge(
        rows[["symbol", "date", "tod", "l"]], on=["symbol", "date", "tod"], how="left")["l"].to_numpy(float)
    c, atr, vwap = b["c"], b["atr"], b["vwap"]
    with np.errstate(invalid="ignore"):
        m = np.isfinite(t0) & np.isfinite(lt0)
        stop[:] = lt0 - 0.05 * atr
        one_r = c + (c - stop)
        tgt[:] = np.where(vwap >= c + 0.25 * atr, vwap, one_r)
        m &= (stop < c) & (tgt > c) & (b["tod"] <= 1445)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
