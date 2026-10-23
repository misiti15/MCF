"""pod-oneil-pocket-pivot-volume-pace-pm-long - Intraday pocket pivot: projected volume beats the 10-day max down-day
volume, near the 10-day MA (afternoon LONG).

Source: TraderLion / O'Neil school: Gil Morales & Chris Kacher 'Trade Like an O'Neil Disciple' pocket pivot (an up day
with volume above the highest down-day volume of the prior 10 sessions, near the 10 / 50-day MA, not extended); Chat
With Traders ep110 George (@RollyTrader) pocket pivot, end-of-day entry; the time-of-day RVOL concept (TradingView
'Relative Volume At Time').
URL: https://www.luxalgo.com/library/concept/pocket-pivot/

VARIANT of CWT ep110 pocket pivot (daily close or next-day entry). Stated change: the signal is taken intraday at
13:00-14:30 from a projected full-day volume, with an MOC-style exit the same day.

Rules (plain English, LONG), default universe (adv20 >= $20M). Volumes are regular-session (09:30-16:00) sums of the
1-minute vendor bars; daily closes / highs / lows from the daily table (completed days only).
  1. D-1 close within -2%..+4% of the daily SMA10; SMA50 rising (SMA50 at D-1 > SMA50 ten sessions earlier); the
     10-day (D-10..D-1) high-low range <= 15% of the D-1 close (a base, not extended).
  2. Projected volume = today's cumulative volume to bar i / the mean fraction of the full-day volume traded by that
     time of day over the prior 20 sessions; projected volume > the max volume of the down days (close < prior close)
     among D-10..D-1, and today's cumulative volume is already >= 0.6 x that max.
  3. Close > D-1 close and > session VWAP, fromOpen > 0.
  4. Gap at the open <= +3% (no gap chase).
  5. SPY fromOpen >= -0.3% (context spy_fo).
  Entry: the first bar meeting all conditions, bar close 13:00-14:30 ET. Stop (GEOM S): max(LOD, session VWAP - 0.25
  x atr_d); skip if the risk > 0.6 x atr_d. Exit: flat 15:55 (the source holds into the close; the optional 2R target
  is NOT used - pre-declared, no tweak).
Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r26_bars as RB  # noqa: E402
import _r24_bars as R24  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1300, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["D-1 within -2..+4% of SMA10, SMA50 rising, 10-day range <= 15%",
          "projected volume > max 10-day down-day volume, cum vol >= 0.6 x it", "close > PDC, > VWAP, fromOpen > 0",
          "gap <= +3%", "SPY fromOpen >= -0.3%", "stop max(LOD, VWAP - 0.25 ATR) (<= 0.6 ATR), flat 15:55"]
_ST = {}
_C = {}


def _daytab():
    if "d" in _C:
        return _C["d"]
    d = RB.day().copy()
    dt = pd.to_datetime(d["date"])
    run = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    pc = d["cls"].groupby(run).shift(1)
    dv = d["V"].where(d["cls"] < pc)                       # down-day volume (NaN otherwise)
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    out["maxdv"] = dv.groupby(run).transform(lambda x: x.shift(1).rolling(10, min_periods=1).max())
    out["nd10"] = d["V"].groupby(run).transform(lambda x: x.shift(1).rolling(10, min_periods=10).count())
    full = d["last_tod"] == 1600                             # half days excluded from the time-of-day curve
    for T in RB.CV_TODS:
        fr = (d[f"cv_{T}"] / d["V"].where(d["V"] > 0)).where(full)
        out[f"fr_{T}"] = fr.groupby(run).transform(lambda x: x.shift(1).rolling(20, min_periods=15).mean())
    dl = RB.daily()
    g = dl.groupby("run")
    s10 = g["close"].transform(lambda x: x.rolling(10, min_periods=10).mean())
    s50 = g["close"].transform(lambda x: x.rolling(50, min_periods=50).mean())
    t = pd.DataFrame({"symbol": dl["symbol"], "date": dl["date"]})
    t["c_1"] = g["close"].shift(1)
    t["s10_1"] = s10.groupby(dl["run"]).shift(1)
    t["s50_1"] = s50.groupby(dl["run"]).shift(1)
    t["s50_11"] = s50.groupby(dl["run"]).shift(11)
    t["hh10"] = g["high"].transform(lambda x: x.shift(1).rolling(10, min_periods=10).max())
    t["ll10"] = g["low"].transform(lambda x: x.shift(1).rolling(10, min_periods=10).min())
    out = out.merge(t, on=["symbol", "date"], how="left")
    _C["d"] = out
    return out


def _cumvol(df):
    syms = set(df["symbol"].astype(str))
    parts = []
    for mo in R24._months_of(df):
        p = R24._OUT / "bars" / f"month={mo}.parquet"
        if p.exists():
            b = pd.read_parquet(p, columns=["symbol", "dn", "tod", "v"])
            b["symbol"] = b["symbol"].astype(str)
            parts.append(b[b["symbol"].isin(syms)])
    if not parts:
        return None
    B = pd.concat(parts, ignore_index=True).sort_values(["symbol", "dn", "tod"], kind="mergesort")
    B["cv"] = B.groupby(["symbol", "dn"], sort=False)["v"].cumsum().astype(float)
    return B[["symbol", "dn", "tod", "cv"]]


def _compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    if not n or "spy_fo" not in df:
        return m, stop
    B = _cumvol(df)
    if B is None:
        return m, stop
    cols = ["maxdv", "nd10", "c_1", "s10_1", "s50_1", "s50_11", "hh10", "ll10"] + [f"fr_{T}" for T in RB.CV_TODS]
    D = RB.map_day(df, _daytab(), cols)
    cv = RB.map_bars(df, B, ["cv"])["cv"]
    tod = df["tod"].to_numpy(np.int64)
    fr = np.full(n, np.nan)
    for T in RB.CV_TODS:
        sel = tod == T
        fr[sel] = D[f"fr_{T}"][sel]
    c, atr = df["close"].to_numpy(float), df["atr_d"].to_numpy(float)
    lod = c - df["dist_lod_atr"].to_numpy(float) * atr
    vwap = c / (1 + df["vwapDistPct"].to_numpy(float) / 100)
    with np.errstate(invalid="ignore", divide="ignore"):
        dist10 = D["c_1"] / D["s10_1"] - 1
        m = (dist10 >= -0.02) & (dist10 <= 0.04) & (D["s50_1"] > D["s50_11"])
        m &= (D["hh10"] - D["ll10"]) <= 0.15 * D["c_1"]
        proj = cv / fr
        m &= (D["nd10"] >= 10) & np.isfinite(D["maxdv"]) & (proj > D["maxdv"]) & (cv >= 0.6 * D["maxdv"])
        m &= (c > D["c_1"]) & (c > vwap) & (df["fromOpen"].to_numpy(float) > 0)
        m &= df["gap"].to_numpy(float) <= 3.0
        m &= df["spy_fo"].to_numpy(float) >= -0.3
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        s = np.maximum(lod, vwap - 0.25 * atr)
        risk = c - s
        m &= (risk > 0) & (risk <= 0.6 * atr)
    stop = np.where(m, s, np.nan)
    return m, stop


def mask(df) -> np.ndarray:
    m, stop = _compute(df)
    _ST.clear()
    _ST[id(df)] = stop
    return np.asarray(m, bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
