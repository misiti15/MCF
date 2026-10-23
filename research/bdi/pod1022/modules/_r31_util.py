"""_r31_util - shared helpers for the pod r3_1 modules (CWT4 Jelinek / Raschke / Alintoff, BBT Aziz VWAP reversal and
MA trend, Zarattini-Barbon-Aziz stocks-in-play ORB). Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry (all causal):
  * unfilled multi-day down-gap edges per (symbol, D) from lib.daily() completed days D-20..D-1 plus D's opening
    print (known at 09:30). Series restart after a > 7-day gap, so nothing bridges the rule-19 locked block.
  * session EMA9 / EMA20 / SMA5 of 5-minute closes from 09:35 (the _r24_bars cache; locked block never read).
  * 30-minute bars built from the continuous full-session 5-minute bars (_cwt3_bars.full_bars, previous open month
    as warm-up) with box / stochastic features as of each 30-minute bar's close.
  * the 09:30-10:00 relative volume (rvol_30 = mean 5m volume 09:30-10:00 / the same over the 14 prior sessions) and
    a daily cross-sectional rank of it (Zarattini et al.), universe from completed days.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as C3  # noqa: E402
import _r24_bars as R24  # noqa: E402
import _r27_util as U  # noqa: E402

_MEM = {}
f, key, start, lag, base = U.f, U.key, U.start, U.lag, U.base


def segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def map_day(df, tab, cols):
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(),
                      "date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy()})
    m = k.merge(tab[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def spy_rows(df, cols, tod_cols=True):
    """SPY's own frame values per (date, tod) broadcast to every row (NaN when SPY has no row)."""
    s = df[df["symbol"].astype(str) == "SPY"]
    t = pd.DataFrame({"date": pd.Series(s["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": s["tod"].to_numpy(np.int64)})
    for c in cols:
        t[c] = s[c].to_numpy(float)
    t = t.drop_duplicates(["date", "tod"])
    k = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64)})
    m = k.merge(t, on=["date", "tod"], how="left")
    return {c: m[c].to_numpy(float) for c in cols}


# ---------------------------------------------------------------- unfilled multi-day down-gaps (Jelinek)
@numba.njit(cache=False)
def _gaps(run, o, h, l, atr1, lo_back, hi_back, thr):
    """For each row D: nearest (lowest) unfilled down-gap edge G above D's open, from gap days j in D-hi..D-lo.
    gap on day j: o_j < l_{j-1} - thr * atr1_j (atr1_j = ATR14 as of j-1); G = l_{j-1}; unfilled: max(h_j..h_{D-1}) < G.
    Also returns the nearest unfilled edge above the open with ANY distance (for the control)."""
    n = len(o)
    G = np.full(n, np.nan)
    for d in range(n):
        best = np.inf
        for back in range(lo_back, hi_back + 1):
            j = d - back
            if j - 1 < 0 or run[j - 1] != run[d]:
                break
            a = atr1[j]
            if not (a > 0):
                continue
            g = l[j - 1]
            if not (o[j] < g - thr * a):
                continue
            mh = -np.inf
            for q in range(j, d):
                if h[q] > mh:
                    mh = h[q]
            if mh < g and g > o[d] and g < best:
                best = g
        if best < np.inf:
            G[d] = best
    return G


def gap_tab():
    if "gap" in _MEM:
        return _MEM["gap"]
    d = R24.lib().daily()[["symbol", "date", "open", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    h, l, c = d["high"], d["low"], d["close"]
    pcl = c.groupby(g).shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    atr1 = tr.groupby(g).transform(lambda x: x.rolling(14, min_periods=14).mean()).groupby(g).shift(1)
    G = _gaps(g.to_numpy(np.int64), d["open"].to_numpy(float), h.to_numpy(float), l.to_numpy(float),
              atr1.to_numpy(float), 2, 20, 0.3)
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"], "gapG": G})
    _MEM["gap"] = out
    return out


# ---------------------------------------------------------------- session EMAs / SMA5 from the r24 bars
@numba.njit(cache=False)
def _sess_ind(newday, c):
    n = len(c)
    e9 = np.full(n, np.nan)
    e20 = np.full(n, np.nan)
    s5 = np.full(n, np.nan)
    a9, a20 = 2.0 / 10.0, 2.0 / 21.0
    i0 = 0
    for i in range(n):
        if newday[i]:
            i0 = i
            e9[i] = c[i]
            e20[i] = c[i]
        else:
            e9[i] = a9 * c[i] + (1 - a9) * e9[i - 1]
            e20[i] = a20 * c[i] + (1 - a20) * e20[i - 1]
        if i - i0 >= 4:
            s5[i] = (c[i] + c[i - 1] + c[i - 2] + c[i - 3] + c[i - 4]) / 5.0
    return e9, e20, s5


def sess_ind(df):
    """Per df row: session EMA9 / EMA20 (seeded at the 09:35 close) and SMA5 of the r24 5m closes, the r24 close,
    and rvc (cumulative volume 09:30..bar / its 20-session same-time mean = rvol_day)."""
    B = U.vol_bars(df)
    n = len(df)
    if B is None:
        return {k: np.full(n, np.nan) for k in ("e9", "e20", "s5", "c24", "rvc")}
    ck = ("si", id(B))
    if ck not in _MEM:
        for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "si"]:
            del _MEM[kk]
        sym = B["symbol"].to_numpy()
        dn = B["dn"].to_numpy(np.int64)
        newday = np.r_[True, (sym[1:] != sym[:-1]) | (dn[1:] != dn[:-1])]
        e9, e20, s5 = _sess_ind(newday, B["c"].to_numpy(float))
        T = B[["symbol", "dn", "tod", "c"]].copy()
        T["e9"], T["e20"], T["s5"] = e9, e20, s5
        _MEM[ck] = T
    T = _MEM[ck]
    out = U.map_bars(df, T, ["e9", "e20", "s5", "c"])
    out["c24"] = out.pop("c")
    out["rvc"] = R24.bars_for(df, ["rvc"])["rvc"]
    return out


# ---------------------------------------------------------------- 30-minute boxes (Alintoff)
@numba.njit(cache=False)
def _box30(sym, H, L, C, nbox, need_div):
    """Per 30m bar (as of its close), over the last nbox bars of the same symbol: box hi / lo, ok flag.
    ok: range <= 0.6 x mean 30m range (20 bars) x nbox; lows flat or rising (min low of the second half >= min low of
    the first half - 0.1 x height); >= 2 tests of the box low (low <= lo + 0.1 x height) at least 2 bars apart;
    with need_div, Stochastic %K(14,3) at the last test >= %K at the first test + 10."""
    n = len(H)
    hi = np.full(n, np.nan)
    lo = np.full(n, np.nan)
    ok = np.zeros(n, np.bool_)
    raw = np.full(n, np.nan)
    K = np.full(n, np.nan)
    s0 = 0
    for i in range(n):
        if i > 0 and sym[i] != sym[i - 1]:
            s0 = i
        if i - s0 >= 13:
            hh, ll = -np.inf, np.inf
            for j in range(i - 13, i + 1):
                hh = max(hh, H[j])
                ll = min(ll, L[j])
            if hh > ll:
                raw[i] = 100.0 * (C[i] - ll) / (hh - ll)
        if i - s0 >= 15 and raw[i] == raw[i] and raw[i - 1] == raw[i - 1] and raw[i - 2] == raw[i - 2]:
            K[i] = (raw[i] + raw[i - 1] + raw[i - 2]) / 3.0
        if i - s0 < max(nbox, 20) - 1:
            continue
        sr = 0.0
        for j in range(i - 19, i + 1):
            sr += H[j] - L[j]
        avg = sr / 20.0
        b0 = i - nbox + 1
        bh, bl = -np.inf, np.inf
        for j in range(b0, i + 1):
            bh = max(bh, H[j])
            bl = min(bl, L[j])
        ht = bh - bl
        hi[i], lo[i] = bh, bl
        if not (ht > 0 and ht <= 0.6 * avg * nbox):
            continue
        half = nbox // 2
        l1, l2 = np.inf, np.inf
        for j in range(b0, b0 + half):
            l1 = min(l1, L[j])
        for j in range(b0 + half, i + 1):
            l2 = min(l2, L[j])
        if l2 < l1 - 0.1 * ht:
            continue
        first, last = -1, -1
        for j in range(b0, i + 1):
            if L[j] <= bl + 0.1 * ht:
                if first < 0:
                    first = j
                last = j
        if first < 0 or last - first < 2:
            continue
        if need_div:
            if not (K[first] == K[first] and K[last] == K[last] and K[last] >= K[first] + 10.0):
                continue
        ok[i] = True
    return hi, lo, ok


def box30(df, nbox=8, need_div=True):
    """Per df row: the box (hi, lo, ok) of the last COMPLETED 30-minute bar at the row's bar close."""
    n = len(df)
    ck = ("box", nbox, need_div, C3.month_of(df) if n else "")
    P = C3.full_bars(df)
    if P is None or not n:
        return {k: np.full(n, np.nan) for k in ("bhi", "blo", "bok")}
    if ck not in _MEM:
        for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "box"]:
            del _MEM[kk]
        mins = (P["tod"].to_numpy(np.int64) // 100) * 60 + P["tod"].to_numpy(np.int64) % 100
        P = P.assign(b=(mins - 571) // 30)
        A = P.groupby(["symbol", "date", "b"], sort=True).agg(H=("h", "max"), L=("l", "min"), C=("c", "last"),
                                                              nb=("c", "size")).reset_index()
        A = A[A["b"] >= 0]
        sc = pd.factorize(A["symbol"])[0].astype(np.int64)
        hi, lo, ok = _box30(sc, A["H"].to_numpy(float), A["L"].to_numpy(float), A["C"].to_numpy(float), nbox,
                            need_div)
        end = 570 + 30 * (A["b"].to_numpy(np.int64) + 1)
        dn = pd.to_datetime(A["date"].astype(str)).to_numpy("datetime64[D]").astype(np.int64)
        T = pd.DataFrame({"symbol": A["symbol"].astype(str).to_numpy(), "tkey": dn * 10000 + end,
                          "bhi": hi, "blo": lo, "bok": ok.astype(float)})
        _MEM[ck] = T.sort_values("tkey", kind="mergesort").reset_index(drop=True)
    T = _MEM[ck]
    tod = df["tod"].to_numpy(np.int64)
    dn = pd.to_datetime(pd.Series(df["date"].to_numpy()).astype(str)).to_numpy("datetime64[D]").astype(np.int64)
    q = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "tkey": dn * 10000 + (tod // 100) * 60 + tod % 100,
                      "pos": np.arange(n)})
    q = q.sort_values("tkey", kind="mergesort")
    m = pd.merge_asof(q, T, on="tkey", by="symbol", direction="backward", allow_exact_matches=True)
    m = m.sort_values("pos")
    return {c: m[c].to_numpy(float) for c in ("bhi", "blo", "bok")}


# ---------------------------------------------------------------- stocks in play rank (Zarattini et al.)
def sip_tab():
    if "sip" in _MEM:
        return _MEM["sip"]
    D = R24.day()[["symbol", "date", "o935", "dr_h", "dr_l", "dr_vavg", "c1000"]].copy()
    D["symbol"] = D["symbol"].astype(str)
    D = D.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(D["date"])
    g = ((D["symbol"] != D["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    base_v = D["dr_vavg"].groupby(g).transform(lambda x: x.shift(1).rolling(14, min_periods=14).mean())
    D["rvol30"] = D["dr_vavg"] / base_v.where(base_v > 0)
    d = R24.lib().daily()[["symbol", "date", "high", "low", "close", "volume"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt2 = pd.to_datetime(d["date"])
    g2 = ((d["symbol"] != d["symbol"].shift()) | ((dt2 - dt2.shift()).dt.days > 7)).cumsum()
    h, l, c, v = d["high"], d["low"], d["close"], d["volume"]
    pcl = c.groupby(g2).shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    d["atr1"] = tr.groupby(g2).transform(lambda x: x.rolling(14, min_periods=14).mean()).groupby(g2).shift(1)
    d["adv14v"] = v.groupby(g2).transform(lambda x: x.shift(1).rolling(14, min_periods=14).mean())
    d["c1"] = pcl
    D = D.merge(d[["symbol", "date", "atr1", "adv14v", "c1"]], on=["symbol", "date"], how="left")
    uni = (D["c1"] > 5) & (D["atr1"] > 0.5) & (D["adv14v"] >= 1e6) & D["rvol30"].notna()
    D["rk"] = np.nan
    D.loc[uni, "rk"] = D[uni].groupby("date")["rvol30"].rank(ascending=False, method="first")
    D["sip"] = ((D["rk"] <= 20) & (D["rvol30"] >= 1)).astype(float)
    # SPY opening-range width vs its trailing 60-session distribution (quiet = bottom tercile; prior days only)
    s = D[D["symbol"] == "SPY"][["date", "dr_h", "dr_l", "o935"]].sort_values("date").copy()
    s["w"] = (s["dr_h"] - s["dr_l"]) / s["o935"]
    q33 = s["w"].shift(1).rolling(60, min_periods=40).quantile(1 / 3)
    s["spy_quiet"] = np.where(q33.notna(), (s["w"] <= q33).astype(float), np.nan)
    D = D.merge(s[["date", "spy_quiet"]], on="date", how="left")
    _MEM["sip"] = D
    return D
