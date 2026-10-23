"""First-hour (60-min) range break inside the prior-day range with a midpoint stop and an ATR-room target - config B (BBT) (SHORT side)
Source: Andrea Unger (CWT guest; Better System Trader ep 016/045), Unger Academy 'DAX First Hour Strategy'; Bear Bull Traders webinar 'Opening Range Breakouts beyond the 1-5 minute chart' and BBT TradeBook.
URL: https://ungeracademy.com/blog/dax-first-hour-strategy-last-year-performance

Rules (short): Config B. (1) First-hour range <= 0.45 x atr_d, FH < PDH and FL > PDL. (2) Trigger: the FIRST 5-min close below FL between 10:35 and 12:00, volumeRatio >= 1.3, close below VWAP, |close - open| <= 0.5 x atr_d. Stop: first-hour midpoint. Target: open - 0.9 x atr_d, else 15:55.
Second pre-declared config of pod-unger-first-hour-2nd-hour-break. No tweak. Costs per config/default.yaml (applied by the scorer).


Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1035, 1200)
CONTEXT = ["spy_fo", "breadth_open"]
CONFIG = "B"

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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    fh, fl = _at(b["hod"], k, tod, 1030), _at(b["lod"], k, tod, 1030)
    rng = fh - fl
    vr = _f(df, "volumeRatio")
    inwin = (tod >= 1035) & (tod <= 1200)
    with np.errstate(invalid="ignore"):
        if LONG:
            m = _first(inwin & (c > fh), k) & (b["vd"] > 0)
        else:
            m = _first(inwin & (c < fl), k) & (b["vd"] < 0)
        m &= vr >= 1.3
        if CONFIG == "U":
            dd = _map_daily(df, k, ["dchg"])
            if dd is None:
                return z
            m &= np.abs(dd["dchg"]) < 1.5 * atr
            m &= (b["pdh"] - b["pdl"]) < 1.8 * atr
            m &= (rng >= 0.25 * atr) & (rng <= 0.7 * atr)
            tgt = None
        else:
            m &= (rng <= 0.45 * atr) & (fh < b["pdh"]) & (fl > b["pdl"])
            m &= np.abs(c - b["opn"]) <= 0.5 * atr
            tgt = b["opn"] + SG * 0.9 * atr
    stop = (fh + fl) / 2
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


def target_price(f, i, stop):
    s = _ST.get(id(f))
    return float(s[1][i]) if s is not None else float("nan")
