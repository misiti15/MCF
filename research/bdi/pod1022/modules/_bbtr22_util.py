"""Shared helpers for the pod1022 round r2_2 Bear Bull Traders modules (segments, EMA9 recovery, derived levels,
point-in-time 52-week high). Not a setup. Educational only - not financial advice."""
from pathlib import Path

import numba
import numpy as np
import pandas as pd

LOCKED = ("2024-11-01", "2025-02-28")          # rule-19 locked block: never read
DAILY = Path(__file__).resolve().parents[4] / "research" / "history2y" / "data" / "daily.parquet"


def segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def ema9(b, e, c, ed):
    """Continuous 5-min EMA9 recovered from emaDiff (as in pod-bbt-parabolic-ema9-snapback-short); NaN on each
    day's first frame row."""
    out = np.full(len(c), np.nan)
    a9, a21 = 0.2, 2.0 / 22.0
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if i1 - i0 < 2:
            continue
        d0, d1 = ed[i0] / 100.0, ed[i0 + 1] / 100.0
        den = (1 - a9) * (1 + d0) - (1 - a21) * (1 + d1)
        if den == 0.0 or d0 != d0 or d1 != d1:
            continue
        E = (a21 * c[i0 + 1] * (1 + d1) - a9 * c[i0 + 1]) / den
        e9 = (1 + d0) * E
        for i in range(i0 + 1, i1):
            e9 = a9 * c[i] + (1 - a9) * e9
            out[i] = e9
    return out


def base(df):
    """Common derived arrays (only values known at each bar's close)."""
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    d = {"c": c, "h": h, "l": l, "atr": atr, "vr": f("volumeRatio"), "fo": f("fromOpen"), "gap": f("gap"),
         "ed": f("emaDiff"), "tod": df["tod"].to_numpy(np.int64)}
    with np.errstate(invalid="ignore", divide="ignore"):
        d["vw"] = c / (1 + f("vwapDistPct") / 100)
        d["op"] = c / (1 + d["fo"] / 100)                 # today's open (proxy)
        d["pdc"] = d["op"] / (1 + d["gap"] / 100)         # prior close
        d["pdl"] = c - f("dist_pdl_atr") * atr
        d["hod"] = c + f("dist_hod_atr") * atr
        d["lod"] = c - f("dist_lod_atr") * atr
        d["sma50"] = c / (1 + f("sma50_dist_pct") / 100)
    b, e = segments(df)
    d["b"], d["e"] = b, e
    d["e9"] = ema9(b, e, c, d["ed"])
    with np.errstate(invalid="ignore", divide="ignore"):
        d["e21"] = d["e9"] / (1 + d["ed"] / 100)
    return d


_HI = {}


def prior_52w(df, min_sessions=100):
    """Per row: (prior-day close, max daily high over the 365 calendar days through the prior day). Point in time:
    only completed days before the row's date. Locked-block days are filtered out on read, so the window simply has
    no rows there; it needs >= min_sessions non-locked sessions, else NaN (stated: the daily file starts 2024-09-16)."""
    if "t" not in _HI:
        d = pd.read_parquet(DAILY, columns=["symbol", "date", "high", "close"])
        ds = d["date"].astype(str)
        d = d[(ds < LOCKED[0]) | (ds > LOCKED[1])].copy()
        d["date"] = pd.to_datetime(d["date"].astype(str))
        d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
        g = d.groupby("symbol", sort=False)
        hi = g.rolling("365D", on="date", min_periods=min_sessions)["high"].max().reset_index(level=0, drop=True)
        d["hi52"] = hi.to_numpy()
        # value usable on the NEXT session: shift by one row per symbol
        d["hi52_prior"] = g["hi52"].shift(1)
        d["pdc_d"] = g["close"].shift(1)
        d["dkey"] = d["date"].dt.strftime("%Y-%m-%d")
        _HI["t"] = d[["symbol", "dkey", "hi52_prior", "pdc_d"]]
    t = _HI["t"]
    q = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "dkey": df["date"].astype(str).to_numpy()})
    q = q.merge(t, on=["symbol", "dkey"], how="left")
    return q["pdc_d"].to_numpy(float), q["hi52_prior"].to_numpy(float)
