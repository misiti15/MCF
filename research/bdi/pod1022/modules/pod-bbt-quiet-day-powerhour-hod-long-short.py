"""Quiet-tape late-day break of the whole-day range in a stock that held VWAP (SHORT side)
Source: Linda Raschke (CWT ep 048 guest; 'the last hour tells the truth', OptionsTradingIQ rules list); Bear Bull Traders webinar 'How to Trade Using the VWAP' (VWAP setups again around power hour).
URL: https://optionstradingiq.com/linda-raschke-rules-for-trading/

Rules (short): (1) SPY range since 09:30 <= 0.6 x SPY atr_d. (2) Stock day range <= 1.0 x atr_d, fromOpen <= -0.5%, >= 90% of closes since 11:00 below VWAP. (3) Trigger: close < prior low of day (made >= 6 bars earlier) by >= 0.02 atr_d with volumeRatio >= 1.3. (4) RSI(14) between 25 and 45 (mirror of 55-75). Window 14:00-15:00. Stop: min(VWAP, EMA9) + 0.05 atr_d (day midpoint fallback), capped at 0.5 atr_d. Exit 15:55.
No tweak made; the 'also above PDH' bonus config is not scored. EMA9 is seeded at the 09:50 bar (frames start there); it has converged by 14:00. SPY's own frame rows supply the SPY range (no SPY rows -> no trades). Costs per config/default.yaml (applied by the scorer).


Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1400, 1500)
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


def _gema(x, k, span):
    """EMA within each symbol-day, seeded on its first row (uses only bars up to each row)."""
    a = 2.0 / (span + 1)
    st = _start(k)
    gs = np.flatnonzero(st)[np.cumsum(st) - 1]
    pos = np.arange(len(x)) - gs
    e = np.asarray(x, float).copy()
    order = np.argsort(pos, kind="stable")
    ps = pos[order]
    cuts = np.flatnonzero(np.r_[True, ps[1:] != ps[:-1]])
    bounds = list(cuts) + [len(ps)]
    for j in range(1, len(cuts)):
        rows = order[bounds[j]:bounds[j + 1]]
        e[rows] = a * e[rows] + (1 - a) * e[rows - 1]
    return e


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    sym = df["symbol"].astype(str).to_numpy()
    if not (sym == "SPY").any():
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    rng_atr = _f(df, "dist_hod_atr") + _f(df, "dist_lod_atr")
    sp = pd.DataFrame({"date": df["date"].astype(str).to_numpy()[sym == "SPY"], "tod": tod[sym == "SPY"],
                       "spr": rng_atr[sym == "SPY"]}).drop_duplicates(["date", "tod"])
    spr = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": tod}).merge(sp, on=["date", "tod"],
                                                                                     how="left")["spr"].to_numpy(float)
    after11 = (tod >= 1100).astype(float)
    n11 = _gcum(after11, k)
    vr, rsi, fo = _f(df, "volumeRatio"), _f(df, "rsi"), _f(df, "fromOpen")
    idx = np.arange(len(df), dtype=float)
    st = _start(k)
    gs = np.flatnonzero(st)[np.cumsum(st) - 1]
    with np.errstate(invalid="ignore", divide="ignore"):
        if LONG:
            made = b["h"] >= b["hod"] - 1e-9
            lvl = _prev(b["hod"], k)
        else:
            made = b["l"] <= b["lod"] + 1e-9
            lvl = _prev(b["lod"], k)
        lm = np.maximum.accumulate(np.where(made, idx, -1.0))
        lmp = _prev(lm, k)                                   # last bar that made the extreme, up to bar i-1
        old = (lmp < gs) | (idx - lmp >= 6)                  # set before 09:50 or >= 6 bars ago
        m = (spr <= 0.6) & (rng_atr <= 1.0) & old & (vr >= 1.3) & (n11 > 0)
        if LONG:
            share = _gcum(after11 * (b["vd"] > 0), k) / n11
            m &= (fo >= 0.5) & (share >= 0.9) & (c > lvl + 0.02 * atr) & (rsi >= 55) & (rsi <= 75)
        else:
            share = _gcum(after11 * (b["vd"] < 0), k) / n11
            m &= (fo <= -0.5) & (share >= 0.9) & (c < lvl - 0.02 * atr) & (rsi >= 25) & (rsi <= 45)
        m &= (tod >= 1400) & (tod <= 1500)
        ema9 = _gema(c, k, 9)
        midd = (b["hod"] + b["lod"]) / 2
        if LONG:
            s = np.maximum(b["vwap"], ema9) - 0.05 * atr
            s = np.where(s < c, s, midd)
            stop = np.maximum(s, c - 0.5 * atr)
        else:
            s = np.minimum(b["vwap"], ema9) + 0.05 * atr
            s = np.where(s > c, s, midd)
            stop = np.minimum(s, c + 0.5 * atr)
    _ST.clear()
    _ST[id(df)] = (stop, None)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")
