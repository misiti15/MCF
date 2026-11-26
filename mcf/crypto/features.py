"""Bar-level features for crypto research. Every feature at bar i uses data up to bar i's CLOSE only
(signals act at the next bar's open). Prior-window levels (ranges, opening ranges) are shifted so the current bar
is not part of its own reference level.

Educational only — not financial advice.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data as D

RET_MIN = (30, 60, 240, 720)
RANGE_H = (4, 12, 24)


def wilder(x: pd.Series, n: int) -> pd.Series:
    return x.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def rsi(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    up, dn = wilder(d.clip(lower=0), n), wilder((-d).clip(lower=0), n)
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def bars_for(base: str, tf: int, start=None, end=None, cache=None) -> pd.DataFrame:
    """tf-minute bars on a full grid (empty buckets carry the last close, `filled`=True, v=0)."""
    raw = D.load_bars(base, start, end, cache)
    if raw.empty:
        return raw
    return D.resample(raw, f"{tf}min", ffill=True)


def build(b: pd.DataFrame, tf: int, btc: pd.DataFrame | None = None) -> pd.DataFrame:
    """Feature frame (float32) for one pair's tf-minute bars. `btc`: BTC bars on the same tf for the lead features."""
    o, h, l, c, v = b["o"], b["h"], b["l"], b["c"], b["v"]
    per_h = 60 // tf if tf <= 60 else 1
    day = max(1, 1440 // tf)
    f = pd.DataFrame(index=b.index)
    f["o"], f["h"], f["l"], f["c"] = o, h, l, c
    f["filled"] = b["filled"].astype(bool)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    f["atr"] = wilder(tr, 14)
    f["atr_pct"] = f["atr"] / c
    f["ema20"] = c.ewm(span=20, adjust=False).mean()
    f["ema200"] = c.ewm(span=200, adjust=False).mean()
    f["stretch"] = (c - f["ema20"]) / f["atr"]
    for m in RET_MIN:
        k = max(1, m // tf)
        f[f"ret{m}"] = (c / c.shift(k) - 1) / f["atr_pct"]            # move in ATR units
    r1 = np.log(c).diff()
    f["z1"] = r1 / r1.rolling(day, min_periods=day // 2).std()       # 1-bar return in sigma
    pv = (b["vw"] * v)
    f["vwap24"] = pv.rolling(day, min_periods=day // 2).sum() / v.rolling(day, min_periods=day // 2).sum()
    dkey = b.index.floor("D")
    f["vwap_sess"] = pv.groupby(dkey).cumsum() / v.groupby(dkey).cumsum().replace(0, np.nan)
    f["d_vwap24"] = (c - f["vwap24"]) / f["atr"]
    f["d_vwap_sess"] = (c - f["vwap_sess"]) / f["atr"]
    f["vol_ratio"] = v / v.rolling(day, min_periods=day // 2).mean().shift()
    f["rsi"] = rsi(c, 14)
    for H in RANGE_H:
        k = H * per_h if tf <= 60 else max(1, H * 60 // tf)
        f[f"hi{H}"] = h.rolling(k).max().shift()
        f[f"lo{H}"] = l.rolling(k).min().shift()
        f[f"rng{H}"] = (f[f"hi{H}"] - f[f"lo{H}"]) / f["atr"]
    rng = (h - l).replace(0, np.nan)
    f["lwick"] = (np.minimum(o, c) - l) / rng
    f["day_open"] = o.groupby(dkey).transform("first")
    f["day_ret"] = (c / f["day_open"] - 1) / f["atr_pct"]
    mins = b.index.hour * 60 + b.index.minute
    f["mod"] = mins                                                   # minute of day (UTC), bar open time
    f["dow"] = b.index.dayofweek
    # opening ranges (known only once the window has closed): US 13:30-14:00, Asia 00:00-04:00 UTC
    for name, a, z in (("us", 810, 840), ("asia", 0, 240)):
        inwin = (mins >= a) & (mins + tf <= z)
        hi = h.where(inwin).groupby(dkey).transform("max")
        lo = l.where(inwin).groupby(dkey).transform("min")
        known = mins >= z
        f[f"{name}_hi"] = hi.where(known)
        f[f"{name}_lo"] = lo.where(known)
        f[f"{name}_rng"] = (hi - lo).where(known) / f["atr"]
    mag = 10 ** np.floor(np.log10(c.clip(lower=1e-12)))
    nearest = np.round(c / mag) * mag
    f["round_dist"] = (nearest - c) / f["atr"]                         # >0: round level just above
    if btc is not None and len(btc):
        bc = btc["c"].reindex(b.index).ffill()
        batr = (btc["atr"] if "atr" in btc else None)
        bpct = (batr.reindex(b.index).ffill() / bc) if batr is not None else f["atr_pct"]
        for m in (30, 60, 240):
            k = max(1, m // tf)
            f[f"btc{m}"] = (bc / bc.shift(k) - 1) / bpct
            f[f"lag{m}"] = f[f"btc{m}"] - f[f"ret{m}"]
    num = [k for k in f.columns if k not in ("filled", "mod", "dow")]
    f[num] = f[num].replace([np.inf, -np.inf], np.nan)
    out = f.astype({k: "float32" for k in f.columns if k not in ("filled", "mod", "dow")})
    return out
