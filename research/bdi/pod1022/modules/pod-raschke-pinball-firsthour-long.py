"""Momentum Pinball: daily RSI(3) of the 1-day ROC picks the side, then a break of the first-hour range (LONG side)
Source: Linda Raschke (Chat With Traders ep 048; Better System Trader guest); Raschke & Connors 'Street Smarts' Momentum Pinball (WH SelfInvest, MQL5 and TradingView write-ups); 'the first hour dictates the day'.
URL: https://www.whselfinvest.de/en-de/trading-platform/free-trading-strategies/tradingsystem/48-momentum-pinball-trading-indicator-raschke-linda-connors-larry

Rules (long): (0) LBR/RSI = Wilder RSI(3) of the daily 1-day % change, on completed daily closes up to D-1, is < 30. (1) First-hour high FH / low FL = high / low of day as of the 10:30 bar. (2) 0.25 <= (FH-FL)/atr_d <= 0.8. (3) Trigger: the FIRST 5-min close above FH from 10:35 to 13:30 (no earlier close above FH since 10:35), and that close is above session VWAP. (4) spy_fo > -0.3%. Entry at the trigger close. Stop: FL, or the FH/FL midpoint when FL is more than 1.5 x 0.25 ATR (0.375 atr_d) below the entry. No target: hold to 15:55 (the book's overnight hold is dropped). One trade per symbol-day.
No tweak made. The optional SMA50 gate and the 2-day ROC variant are not used. Costs per config/default.yaml (applied by the scorer).


Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1035, 1330)
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
    dd = _map_daily(df, k, ["lbr"])
    if dd is None:
        return z
    lbr = dd["lbr"]
    fh, fl = _at(b["hod"], k, tod, 1030), _at(b["lod"], k, tod, 1030)
    rng = fh - fl
    spy = _f(df, "spy_fo")
    inwin = (tod >= 1035) & (tod <= 1330)
    with np.errstate(invalid="ignore"):
        if LONG:
            trig = _first(inwin & (c > fh), k)
            m = trig & (lbr < 30) & (b["vd"] > 0) & (spy > -0.3)
            stop = np.where(c - fl > 0.375 * atr, (fh + fl) / 2, fl)
        else:
            trig = _first(inwin & (c < fl), k)
            m = trig & (lbr > 70) & (b["vd"] < 0) & (spy < 0.3)
            stop = np.where(fh - c > 0.375 * atr, (fh + fl) / 2, fh)
        m &= (rng >= 0.25 * atr) & (rng <= 0.8 * atr)
    _ST.clear()
    _ST[id(df)] = (stop, None)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")
