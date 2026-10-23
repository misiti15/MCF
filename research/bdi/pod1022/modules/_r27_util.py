"""_r27_util - shared helpers for the pod r2_7 modules (Kell daily-EMA crossback, Raschke first pullback, Taylor buy
day, Shannon session/2-day VWAP pinch, time-of-day RVOL ignition). Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry:
  * daily values as of D-1's close (lib.daily(), completed days only; the rule-19 locked block is not in lib.daily();
    every series restarts after a > 7-day gap so nothing is bridged across the block): open / high / low / close of
    D-1, close of D-2 / D-3, daily EMA10 / EMA20 / SMA20 / SMA50 / ATR14, the 20-day high (D-20..D-1), the
    typical-price x volume sums used for the multi-day VWAPs, and the Kell wedge-pop look-back (pop in D-15..D-3).
  * 5-minute volume per bar 09:35..15:00 (the _r24_bars cache, built from the 1-minute vendor bars, locked block
    dropped) and the RVOL-at-time = bar volume / mean volume of the same 5-minute slot over the 20 PRIOR sessions
    (min 10). The previous open month is loaded only as warm-up; a locked previous month is skipped.
  * SPY 5-minute bars 09:35..15:00 (the _smbv5_bars cache, every open SPY day) and SPY's daily ATR14 as of D-1.
Callers use a bar's values only on that bar or later. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r24_bars as R24  # noqa: E402

_LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
_MEM = {}


def f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def lag(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def base(df):
    c, atr = f(df, "close"), f(df, "atr_d")
    b = dict(c=c, h=f(df, "high"), l=f(df, "low"), atr=atr, tod=df["tod"].to_numpy(np.int64))
    with np.errstate(invalid="ignore", divide="ignore"):
        b["hod"] = c + f(df, "dist_hod_atr") * atr
        b["lod"] = c - f(df, "dist_lod_atr") * atr
        b["pdh"] = c + f(df, "dist_pdh_atr") * atr
        b["pdl"] = c - f(df, "dist_pdl_atr") * atr
        b["opn"] = c / (1 + f(df, "fromOpen") / 100)
        b["pc"] = b["opn"] / (1 + f(df, "gap") / 100)
        b["vwap"] = c / (1 + f(df, "vwapDistPct") / 100)
    return b


@numba.njit(cache=False)
def _kell(run, c, h, l, e10, e20, valid):
    """Per daily row D: the most recent wedge pop p in D-15..D-3 (close > EMA10 and EMA20 after 5 closes below EMA20),
    its close, the max high of p+1..D-1 and whether any day p+1..D-1 had low <= its EMA10. All from days < D."""
    n = len(c)
    pc = np.full(n, np.nan)
    mh = np.full(n, np.nan)
    touched = np.full(n, np.nan)
    pop = np.zeros(n, np.bool_)
    for t in range(n):
        if t < 5 or not valid[t]:
            continue
        if run[t - 5] != run[t]:
            continue
        ok = c[t] > e10[t] and c[t] > e20[t]
        for j in range(t - 5, t):
            if not (valid[j] and c[j] < e20[j]):
                ok = False
        pop[t] = ok
    for d in range(n):
        for k in range(3, 16):
            p = d - k
            if p < 0 or run[p] != run[d]:
                break
            if pop[p]:
                pc[d] = c[p]
                m = -1e300
                tch = 0.0
                for j in range(p + 1, d):
                    if h[j] > m:
                        m = h[j]
                    if l[j] <= e10[j]:
                        tch = 1.0
                mh[d] = m
                touched[d] = tch
                break
    return pc, mh, touched


def daily_tab():
    """Per (symbol, date str D): values known at D's open (completed days D-1 and earlier)."""
    if "d" in _MEM:
        return _MEM["d"]
    d = R24.lib().daily()[["symbol", "date", "open", "high", "low", "close", "volume"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    o, h, l, c, v = d["open"], d["high"], d["low"], d["close"], d["volume"]
    gb = lambda s: s.groupby(g)
    pos = gb(c).cumcount()
    e10 = gb(c).transform(lambda x: x.ewm(span=10, adjust=False).mean()).where(pos >= 19)
    e20 = gb(c).transform(lambda x: x.ewm(span=20, adjust=False).mean()).where(pos >= 39)
    sma20 = gb(c).transform(lambda x: x.rolling(20, min_periods=20).mean())
    sma50 = gb(c).transform(lambda x: x.rolling(50, min_periods=50).mean())
    pcl = gb(c).shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    atr14 = tr.groupby(g).transform(lambda x: x.rolling(14, min_periods=14).mean())
    hi20 = gb(h).transform(lambda x: x.rolling(20, min_periods=20).max())
    tpv = (h + l + c) / 3.0 * v
    s4, v4 = gb(tpv).transform(lambda x: x.rolling(4, min_periods=4).sum()), gb(v).transform(
        lambda x: x.rolling(4, min_periods=4).sum())
    s5, v5 = gb(tpv).transform(lambda x: x.rolling(5, min_periods=5).sum()), gb(v).transform(
        lambda x: x.rolling(5, min_periods=5).sum())
    run = g.to_numpy(np.int64)
    valid = (e20.notna() & e10.notna()).to_numpy()
    kpc, kmh, ktch = _kell(run, c.to_numpy(float), h.to_numpy(float), l.to_numpy(float),
                           e10.to_numpy(float), e20.to_numpy(float), valid)
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    cur = {"o": o, "h": h, "l": l, "c": c, "v": v, "tpv": tpv, "e10": e10, "e20": e20, "sma20": sma20,
           "sma50": sma50, "atr14": atr14, "hi20": hi20, "s4": s4, "v4": v4, "s5": s5, "v5": v5}
    for nm, s in cur.items():
        out[nm + "1"] = s.groupby(g).shift(1)              # as of D-1 (row D)
    out["c2"] = c.groupby(g).shift(2)
    out["c3"] = c.groupby(g).shift(3)
    out["kell_pc"] = kpc                                   # computed from rows < D only (see _kell)
    out["kell_mh"] = kmh
    out["kell_touch"] = ktch
    _MEM["d"] = out
    return out


def map_daily(df, k, cols):
    t = daily_tab()
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st],
                      "date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy()[st]})
    m = u.merge(t[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    idx = np.cumsum(st) - 1
    return {c: m[c].to_numpy(float)[idx] for c in cols}


def _months(df):
    ds = pd.Series(pd.unique(pd.Series(df["date"].to_numpy()).astype(str)))
    return sorted(set(ds.str[:7]) - _LOCKED_MONTHS)


def _prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
    return f"{y:04d}-{mo:02d}"


def vol_bars(df):
    """r24 5m bars (symbol, dn, tod, c, v, cv = cumulative volume 09:30..bar, rvt = RVOL at time over the 20 prior
    sessions of the same slot, min 10) for the frame's months, previous open month as warm-up."""
    ms = _months(df)
    ck = ("vb", tuple(ms))
    if ck in _MEM:
        return _MEM[ck]
    for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "vb"]:
        del _MEM[kk]
    load = []
    if ms and _prev_month(ms[0]) not in _LOCKED_MONTHS:
        load.append(_prev_month(ms[0]))
    load += ms
    parts = []
    for m in load:
        assert m not in _LOCKED_MONTHS
        p = R24._OUT / "bars" / f"month={m}.parquet"
        if p.exists():
            parts.append(pd.read_parquet(p, columns=["symbol", "dn", "tod", "c", "v"]))
    if not parts:
        _MEM[ck] = None
        return None
    B = pd.concat(parts, ignore_index=True)
    B["symbol"] = B["symbol"].astype(str)
    B["dn"] = B["dn"].astype(np.int64)
    B["tod"] = B["tod"].astype(np.int64)
    B = B.sort_values(["symbol", "tod", "dn"], kind="mergesort").reset_index(drop=True)
    v = B["v"].to_numpy(float)
    sc = pd.factorize(B["symbol"])[0].astype(np.int64)
    gid = sc * 10000 + B["tod"].to_numpy(np.int64)
    dn = B["dn"].to_numpy(np.int64)
    newg = np.r_[True, (gid[1:] != gid[:-1]) | (dn[1:] - dn[:-1] > 10)]
    B["rvt"] = _rvt(newg, v)
    B = B.sort_values(["symbol", "dn", "tod"], kind="mergesort").reset_index(drop=True)
    B["cv"] = B.groupby(["symbol", "dn"])["v"].cumsum()
    _MEM[ck] = B
    return B


@numba.njit(cache=False)
def _rvt(newg, v):
    n = len(v)
    out = np.full(n, np.nan)
    g0 = 0
    for i in range(n):
        if newg[i]:
            g0 = i
        j0 = max(g0, i - 20)
        cnt = i - j0
        if cnt >= 10:
            s = 0.0
            for j in range(j0, i):
                s += v[j]
            if s > 0:
                out[i] = v[i] / (s / cnt)
    return out


def map_bars(df, B, cols):
    dn = pd.to_datetime(pd.Series(df["date"].to_numpy()).astype(str)).to_numpy("datetime64[D]").astype(np.int64)
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "dn": dn, "tod": df["tod"].to_numpy(np.int64)})
    m = k.merge(B[["symbol", "dn", "tod"] + list(cols)], on=["symbol", "dn", "tod"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def spy_tab():
    """SPY per (date str, tod): running range since 09:30 (rng), the bar high / low, and SPY ATR14 as of D-1."""
    if "spy" in _MEM:
        return _MEM["spy"]
    S = R24.spy_bars().copy()
    S["date"] = S["date"].astype(str)
    S["rng"] = S["run_h"] - S["run_l"]
    t = daily_tab()
    a = t[t["symbol"] == "SPY"][["date", "atr141"]].rename(columns={"atr141": "spy_atr"})
    S = S.merge(a, on="date", how="left")
    _MEM["spy"] = S
    return S


def map_spy(df, cols):
    S = spy_tab()
    k = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64)})
    T = S[["date", "tod"] + list(cols)].copy()
    T["tod"] = T["tod"].astype(np.int64)
    m = k.merge(T, on=["date", "tod"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}
