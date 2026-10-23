"""pod-smb-stuffed-triple-top-neckline - Stuffed at the high: three failed HOD tests, short the neckline break
(SHORT).

Source: SMB PlayBook (Mike Bellafiore, 'The PlayBook'): intraday levels, fade trades, reading the tape at a level.
URL: https://oreilly.com/library/view/the-playbook-an/9780132937672

VARIANT of the backlog M-top/W-bottom neckline idea (bdi-reddit-vwap-double-bottom, untested), exhaustion_short and
VT volume top. Stated change: the level is a triple-tested HOD and entry is the neckline break. Opposite trigger of
pod-wt-flat-top-roundnum-long.

Rules (plain English):
  1. HOD = the running high of day as of the previous bar. Test bars: bars among the last 24 (before this bar) whose
     high is within 0.06 x atr_d of HOD, taken in order with >= 2 bars between picks (a bar right after a pick is
     skipped). >= 3 tests, the first one >= 6 bars before this bar (the source's 6-24 bar pattern). 'None closing
     above HOD + 0.03 ATR' holds by construction: HOD is the running high, so no bar of the pattern broke it.
  2. >= 2 of the test bars have upper_wick >= 0.4.
  3. volumeRatio at the last test <= volumeRatio at the first test.
  4. Neckline N = the lowest low from the first through the last test. Trigger: this bar closes below N (the
     previous close was at or above N), while the close is above VWAP or at most 0.3 x atr_d below it.
  Entry: that close. Stop (GEOM S): HOD + 0.03 x atr_d. Target: N - (HOD - N), or VWAP when VWAP is below the entry
  and nearer. Flat 15:55. Bar close 10:30-14:45.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1445)
LAYERS = [">= 3 HOD tests within 0.06 ATR in the last 6-24 bars, >= 2 bars apart", ">= 2 tests with upper_wick >= 0.4",
          "volumeRatio last test <= first test", "close breaks the neckline, within 0.3 ATR of VWAP or above",
          "stop HOD + 0.03 ATR, target measured move or VWAP", "10:30-14:45"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

LONG = SIDE == "long"
_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _prev(x, k, n=1):
    """x shifted n bars back inside the same symbol-day (NaN where that bar is in another symbol-day)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        same = np.zeros(len(x), bool)
        same[n:] = k[n:] == k[:-n]
        p[~same] = np.nan
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
    Callers only use it on rows with tod > T (or == T), so nothing later than the decision bar is used."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


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


def _daily_feats():
    """Per (symbol, date D): daily values known at D's open, computed on completed days up to D-1 only.
    Series restart after a calendar gap > 7 days (the locked block is absent from lib.daily(), so the SMA50 / 20-day
    values are NaN until enough post-gap days exist)."""
    if "f" in _DC:
        return _DC["f"]
    try:
        try:
            import lib
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
            import lib
        d = lib.daily()[["symbol", "date", "high", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l = d["close"], d["high"], d["low"]
    gc = c.groupby(g)
    pc = gc.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1).where(pc.notna())
    rng = (h - l).replace(0, np.nan)
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c, "d_high": h, "d_low": l,
        "sma20": gc.transform(lambda x: x.rolling(20).mean()),
        "sma50": gc.transform(lambda x: x.rolling(50).mean()),
        "hi20": h.groupby(g).transform(lambda x: x.rolling(20).max()),
        "atr5": tr.groupby(g).transform(lambda x: x.rolling(5).mean()),
        "dchg": c - pc,
        "ibs": (c - l) / rng,
    })
    cols = [x for x in f.columns if x not in ("symbol", "date")]
    for col in cols:                       # the row for D carries the values as of D-1's close
        f[col] = f[col].groupby(g).shift(1)
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
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, vw, vr, uw, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 1, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            H = hod[i - 1]
            last = -10
            cnt = 0
            first = -1
            nw = 0
            for t in range(max(i0, i - 24), i):
                if h[t] >= H - 0.06 * a and t - last >= 2:
                    if first < 0:
                        first = t
                    last = t
                    cnt += 1
                    if uw[t] >= 0.4:
                        nw += 1
            if cnt < 3 or first > i - 6 or nw < 2:
                continue
            if not (vr[last] <= vr[first]):
                continue
            N = 1e18
            for t in range(first, last + 1):
                N = min(N, l[t])
            if not (c[i] < N and c[i - 1] >= N):
                continue
            if not (c[i] > vw[i] - 0.3 * a):
                continue
            meas = N - (H - N)
            tg = meas
            if vw[i] < c[i] and vw[i] > meas:
                tg = vw[i]
            m[i] = True
            stop[i] = H + 0.03 * a
            tgt[i] = tg
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    bb, ee = _segments(b["k"])
    m, stop, tgt = _kern(bb, ee, b["tod"], b["c"], b["h"], b["l"], b["hod"], b["vwap"], _f(df, "volumeRatio"),
                         _f(df, "upper_wick"), b["atr"], WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def target_price(f, i, stop):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[1][i]) if s is not None and s[1] is not None else float("nan")
