"""Index-ETF gap beyond the prior range that holds: follow it to the close (SHORT side)
Source: Linda Raschke (CWT ep 048: 'the larger the gap, the greater the odds of continuation'); Scott Andrews, Better System Trader ep 018 (fade vs follow); Ernie Chan opening-gap momentum (QuantRocket summary).
URL: https://www.quantrocket.com/blog/buy-or-sell-down-gaps/

Rules (short): (1) Open < prior-day low and (prior close - open) >= 0.5 x atr_d. (2) At 09:50 the gap is less than half filled and the 09:30-09:50 high stayed below PDL. (3) Close < VWAP and breadth_open <= 0.45. (4) Entry at the 09:50 close. Stop: midpoint of the 09:30-09:50 range (or the prior close if lower). Exit 15:55.
Config 2 (pre-declared in the source idea): index ETFs plus the sector SPDRs. Otherwise identical to pod-bst018-andrews-etf-follow-beyond. Costs per config/default.yaml (applied by the scorer).


Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (950, 950)
CONTEXT = ["spy_fo", "breadth_open"]
SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA', 'XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLY', 'XLP', 'XLU', 'XLB', 'XLRE', 'XLC']

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
    if not len(df) or "breadth_open" not in df:
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    bo = _f(df, "breadth_open")
    mid = (b["hod"] + b["lod"]) / 2          # 09:30-09:50 range midpoint (only the 09:50 bar is used)
    with np.errstate(invalid="ignore"):
        m = tod == 950
        if LONG:
            m &= b["opn"] > b["pdh"]
            m &= (b["opn"] - b["pc"]) >= 0.5 * atr
            m &= (c - b["pc"]) > 0.5 * (b["opn"] - b["pc"])      # gap less than half filled
            m &= b["lod"] > b["pdh"]                               # 09:30-09:50 low held above PDH
            m &= (b["vd"] > 0) & (bo >= 0.55)
            stop = np.maximum(mid, b["pc"])
        else:
            m &= b["opn"] < b["pdl"]
            m &= (b["pc"] - b["opn"]) >= 0.5 * atr
            m &= (b["pc"] - c) > 0.5 * (b["pc"] - b["opn"])
            m &= b["hod"] < b["pdl"]
            m &= (b["vd"] < 0) & (bo <= 0.45)
            stop = np.minimum(mid, b["pc"])
    _ST.clear()
    _ST[id(df)] = (stop, None)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")
