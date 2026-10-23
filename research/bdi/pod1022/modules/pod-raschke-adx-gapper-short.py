"""ADX Gapper: open beyond the prior-day extreme against a strong daily trend, buy/sell the reclaim (SHORT side)
Source: Linda Raschke (CWT ep 048 guest); Raschke & Connors 'Street Smarts' ADX Gapper (Traders.com article; CryptoDataDownload write-up; TradingView ADX Gapper script).
URL: https://technical.traders.com/tradersonline/display.asp?art=2794

Rules (short): (1) Daily ADX(14) > 30 and -DI > +DI as of D-1. (2) Open above PDH by >= 0.1 x atr_d. (3) The 09:50 bar still closes above PDH. (4) Trigger 09:55-11:30: the FIRST 5-min close back below PDH with volumeRatio >= 1.2 and close <= VWAP + 0.2 x atr_d. (5) spy_fo < +0.5%. Stop: high of day + 0.05 atr_d, capped at 0.75 atr_d. Target: the nearer of the prior close (when below the entry) and 1.5R; else flat 15:55.
No tweak made. Costs per config/default.yaml (applied by the scorer).


Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (955, 1130)
CONTEXT = ["spy_fo", "breadth_open"]

import numpy as np
import pandas as pd

LONG = SIDE == "long"
SG = 1.0 if LONG else -1.0
_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _prev(x, k):
    p = np.r_[np.nan, np.asarray(x, float)[:-1]]
    p[_start(k)] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _first(cond, k):
    """True only on the first True row of each symbol-day (no earlier row qualified)."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to the whole symbol-day (NaN when that bar is missing).
    Callers only use it on rows with tod > T, so nothing later than the decision bar is used."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vd"] = _f(df, "vwapDistPct")
    b["vwap"] = c / (1 + b["vd"] / 100)
    return b

_DC = {}


def _daily_feats():
    """Per (symbol, date D) daily values known at D's open: computed on completed days up to D-1 only.
    Series restart after a calendar gap > 7 days (the locked block is absent from lib.daily())."""
    if "f" in _DC:
        return _DC["f"]
    try:
        try:
            import lib
        except ImportError:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
            import lib
        d = lib.daily()[["symbol", "date", "high", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    newseg = (d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)
    g = newseg.cumsum()
    c, h, l = d["close"], d["high"], d["low"]
    pc = c.groupby(g).shift(1)
    roc = (c / pc - 1) * 100
    dr = roc.groupby(g).diff()
    up, dn = dr.clip(lower=0), (-dr).clip(lower=0)
    ew = lambda s, n, mp: s.groupby(g).transform(lambda x: x.ewm(alpha=1 / n, adjust=False, min_periods=mp).mean())
    au, ad = ew(up, 3, 3), ew(dn, 3, 3)
    lbr = 100 - 100 / (1 + au / ad.replace(0, np.nan))
    lbr = lbr.where(ad > 0, 100.0).where(au.notna())
    ph, pl = h.groupby(g).shift(1), l.groupby(g).shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1).where(pc.notna())
    upm, dnm = h - ph, pl - l
    pdm = upm.where((upm > dnm) & (upm > 0), 0.0).where(pc.notna())
    mdm = dnm.where((dnm > upm) & (dnm > 0), 0.0).where(pc.notna())
    atr = ew(tr, 14, 14)
    pdi, mdi = 100 * ew(pdm, 14, 14) / atr, 100 * ew(mdm, 14, 14) / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    adx = ew(dx, 14, 14)
    f = pd.DataFrame({"symbol": d["symbol"], "date": d["date"], "lbr": lbr, "adx": adx, "pdi": pdi, "mdi": mdi,
                      "dchg": c - pc})
    # shift by one day inside each segment: the row for D carries the values as of D-1's close
    for col in ["lbr", "adx", "pdi", "mdi", "dchg"]:
        f[col] = f[col].groupby(g).shift(1)
    f["date"] = f["date"].astype(str)
    _DC["f"] = f
    return f


def _map_daily(df, k, cols):
    """Daily features for every frame row (via its symbol-day), NaN when missing."""
    f = _daily_feats()
    if f is None:
        return None
    st = _start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(f, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[k] for c in cols}


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    dd = _map_daily(df, k, ["adx", "pdi", "mdi"])
    if dd is None:
        return z
    c950 = _at(c, k, tod, 950)
    vr, spy = _f(df, "volumeRatio"), _f(df, "spy_fo")
    inwin = (tod >= 955) & (tod <= 1130)
    with np.errstate(invalid="ignore"):
        m = dd["adx"] > 30
        if LONG:
            m &= dd["pdi"] > dd["mdi"]
            m &= (b["pdl"] - b["opn"]) >= 0.1 * atr
            m &= c950 < b["pdl"]
            m &= _first(inwin & (c > b["pdl"]), k)
            m &= (vr >= 1.2) & (c >= b["vwap"] - 0.2 * atr) & (spy > -0.5)
            stop = np.maximum(b["lod"] - 0.05 * atr, c - 0.75 * atr)
            r = c - stop
            tgt = np.where(b["pc"] > c, np.minimum(b["pc"], c + 1.5 * r), c + 1.5 * r)
        else:
            m &= dd["mdi"] > dd["pdi"]
            m &= (b["opn"] - b["pdh"]) >= 0.1 * atr
            m &= c950 > b["pdh"]
            m &= _first(inwin & (c < b["pdh"]), k)
            m &= (vr >= 1.2) & (c <= b["vwap"] + 0.2 * atr) & (spy < 0.5)
            stop = np.minimum(b["hod"] + 0.05 * atr, c + 0.75 * atr)
            r = stop - c
            tgt = np.where(b["pc"] < c, np.maximum(b["pc"], c - 1.5 * r), c - 1.5 * r)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


def target_price(f, i, stop):
    s = _ST.get(id(f))
    return float(s[1][i]) if s is not None else float("nan")
