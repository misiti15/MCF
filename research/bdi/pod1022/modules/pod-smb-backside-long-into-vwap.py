"""pod-smb-backside-long-into-vwap - Backside scalp: higher-low base under VWAP after a morning flush, target VWAP
(LONG).

Source: SMB Capital Scalp Radar 'Back$ide' scalp; TradingView 'Backside Bubble Scalping' port.
URL: https://pl.tradingview.com/script/oxCB0k3f-Backside-Bubble-Scalping

VARIANT of CWT05 flush V (failed), R03 VWAP fade (failed) and the 'VWAP reclaim after 15-30 min below' backlog idea.
Stated change: it trades the move INTO VWAP from a higher-low base below it; the reclaim ideas trade beyond VWAP.

Rules (plain English):
  1. The low of day was set 4-20 bars before this bar (the last frame bar whose low equals the running LOD), and at
     that bar the LOD was >= 0.75 x atr_d below that bar's session VWAP.
  2. Higher low: the lowest low from the LOD bar + 2 through this bar is >= LOD + 0.15 x atr_d.
  3. Base: the K bars before this bar (K = the longest of 6, 5, 4, 3 with high-low range <= 0.30 x atr_d, all after
     the LOD bar; pre-declared rule for picking K inside the source's 3-6 range) have every close >= EMA9 - 0.05 x
     atr_d and below VWAP (each bar's own EMA9 / VWAP; EMA9 on the day's 5-minute closes).
  4. Trigger: this bar closes above the base high, and VWAP - close >= 1.5 x (close - stop).
  Entry: that close. Stop (GEOM S): the higher low - 0.03 x atr_d. Target: VWAP at entry. Flat 15:55.
  Bar close 10:15-14:30.
Frame note: the LOD must have been made on a frame bar (09:50 or later); a low from 09:30-09:45 cannot be dated, so
those days do not qualify. EMA9 is seeded at the 09:50 close. The regime hint (avoid spy_fo < -0.75%) is not a rule.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1430)
LAYERS = ["LOD set 4-20 bars ago, >= 0.75 ATR below VWAP", "higher low >= LOD + 0.15 ATR",
          "3-6 bar base range <= 0.30 ATR, closes >= EMA9 - 0.05 ATR, below VWAP", "close > base high",
          "VWAP >= 1.5R away", "stop HL - 0.03 ATR, target VWAP", "10:15-14:30"]

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
def _kern(b, e, tod, c, h, l, lod, vw, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    ema = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        j = -1
        ev = c[i0]
        for i in range(i0, i1):
            ev = ev + (2.0 / 10.0) * (c[i] - ev)
            ema[i] = ev
            if l[i] <= lod[i] + 1e-6 * c[i]:
                j = i
            if tod[i] < w0 or tod[i] > w1 or j < 0:
                continue
            a = atr[i]
            if i - j < 4 or i - j > 20:
                continue
            L0 = lod[i]
            if vw[j] - L0 < 0.75 * a:
                continue
            hl = 1e18
            for t in range(j + 2, i + 1):
                hl = min(hl, l[t])
            if hl < L0 + 0.15 * a:
                continue
            for K in range(6, 2, -1):
                if i - K <= j:
                    continue
                bh = -1e18
                bl = 1e18
                for t in range(i - K, i):
                    bh = max(bh, h[t])
                    bl = min(bl, l[t])
                if bh - bl <= 0.30 * a:
                    ok = True
                    for t in range(i - K, i):
                        if not (c[t] >= ema[t] - 0.05 * a and c[t] < vw[t]):
                            ok = False
                    st = hl - 0.03 * a
                    if ok and c[i] > bh and (vw[i] - c[i]) >= 1.5 * (c[i] - st):
                        m[i] = True
                        stop[i] = st
                        tgt[i] = vw[i]
                    break
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    bb, ee = _segments(b["k"])
    m, stop, tgt = _kern(bb, ee, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["vwap"], b["atr"], WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def target_price(f, i, stop):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[1][i]) if s is not None and s[1] is not None else float("nan")
