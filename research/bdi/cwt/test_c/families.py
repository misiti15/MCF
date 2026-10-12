"""CWT package C, daily-bar families C1-C9 (TESTPLAN.md section 4 + amendment 2026-10-12; NOTES.md section 1).

Run: python research/bdi/cwt/test_c/families.py  -> raw_daily.csv (long format), data/trades_daily.parquet.
The two-year intraday pieces (C2 intraday entry, C5a 13:55 exit, C7 day 5) are in intraday.py; the S6 overlays in
s6_overlays.py; gates in evaluate.py. Educational only - not financial advice.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import common as cm
from common import (ATR14, C, Cn, Cx, ELIG, H, Hn, Hx, L, Ln, Lx, N, Ox, SPY, SPY_SMA10, SPY_SMA200, T, V, book,
                    col, dates, ema, locked, rsi, score, sma, spy_c)

SMA5, SMA10, SMA20, SMA50, SMA200 = sma(5), sma(10), sma(20), sma(50), sma(200)
EMA8, EMA20, EMA21 = ema(8), ema(20), ema(21)
RSI2, RSI3 = rsi(2), rsi(3)
ELIGB = ELIG.copy()
IDX = [col[s] for s in ("SPY", "QQQ", "IWM")]


def nz(a):
    return np.nan_to_num(a, nan=0.0).astype(bool) if a.dtype != bool else a


# ================================================================================================ overlay hooks (C9)
def ovl_rule(ovl, j, ei):
    if ovl == "sma20x2":
        return lambda d: d - 1 >= ei and Cx[d, j] < SMA20[d, j] and Cx[d - 1, j] < SMA20[d - 1, j]
    return None


def ovl_target(ovl, j):
    if ovl == "keltner":
        return lambda d: EMA20[d - 1, j] + 3 * ATR14[d - 1, j]
    return None


def combine_rules(*rules):
    rs = [r for r in rules if r is not None]
    if not rs:
        return None
    return lambda d: any(r(d) for r in rs)


def combine_targets(*tgs):
    ts = [x for x in tgs if x is not None]
    if not ts:
        return None
    return lambda d: np.nanmin([x(d) if callable(x) else x for x in ts])


def run_walk(j, ei, ep, side, mode, ek, base_rule, stop, target, max_xi, ovl, i):
    """Base walk plus an optional C9 exit overlay. Returns a row dict or None."""
    if ovl == "kidd":
        r1 = cm.walk(j, ei, ep, side, mode, stop, target, combine_rules(base_rule, lambda d: Cx[d, j] < EMA8[d, j]), max_xi)
        r2 = cm.walk(j, ei, ep, side, mode, stop, target, combine_rules(base_rule, lambda d: Cx[d, j] < EMA21[d, j]), max_xi)
        if r1 is None or r2 is None:
            return None
        return {"i": i, "j": j, "ei": ei, "ep": ep, "ek": ek, "xi": max(r1[0], r2[0]), "xp": r1[1], "xk": "C",
                "xi1": r1[0], "xp2": r2[1], "xi2": r2[0], "why": r1[3] + "/" + r2[3]}
    rule = combine_rules(base_rule, ovl_rule(ovl, j, ei))
    tg = combine_targets(target, ovl_target(ovl, j))
    r = cm.walk(j, ei, ep, side, mode, stop, tg, rule, max_xi)
    if r is None:
        return None
    return {"i": i, "j": j, "ei": ei, "ep": ep, "ek": ek, "xi": r[0], "xp": r[1], "xk": r[2], "why": r[3]}


def fix_kidd(t, side):
    """Two-leg trades: return = mean of the legs, each paying its own exit cost."""
    if not len(t) or "xp2" not in t:
        return t
    t = t.copy()
    g1 = side * (t.xp / t.ep - 1); g2 = side * (t.xp2 / t.ep - 1)
    t["gross"] = 0.5 * (g1 + g2)
    t["net"] = t.gross - cm.cost(t.ep) - 0.5 * (cm.cost(t.xp) + cm.cost(t.xp2))
    return t


def governor(t):
    """C9 Komar: size 0.5 when the book's cumulative net (trades closed before this entry) < its 20-trade mean."""
    if not len(t):
        return t
    t = t.copy()
    cl = t.sort_values("xi")
    xs = cl.xi.to_numpy()
    cum = np.cumsum(cl.net.to_numpy())
    ma = pd.Series(cum).rolling(20).mean().to_numpy()
    k = np.searchsorted(xs, t.ei.to_numpy(), side="left")
    w = np.ones(len(t))
    ok = k >= 20
    w[ok] = np.where(cum[k[ok] - 1] < ma[k[ok] - 1], 0.5, 1.0)
    t["w"] = w
    return t


# ================================================================================================ C8 gates
def ftd_state():
    """IBD-style follow-through state on SPY (NOTES 1.3). Returns bool array: True = 'on' at the close of row t."""
    c, lo, v = Cn[:, SPY], Ln[:, SPY], cm.Vn[:, SPY]
    on = np.zeros(T, bool)
    state = False
    low_since = np.inf; att_day = 0; att_low = np.nan
    dist = []
    for t in range(1, T):
        if not np.isfinite(c[t]):
            on[t] = state; continue
        dd = c[t] / c[t - 1] - 1 <= -0.002 and v[t] > v[t - 1]
        dist.append(t if dd else -1)
        n_dist = sum(1 for x in dist[-25:] if x >= 0)
        if state:
            if c[t] < att_low or n_dist >= 6:
                state = False; low_since = lo[t]; att_day = 0
        else:
            if lo[t] < low_since:
                low_since = lo[t]; att_day = 0          # undercut: attempt restarts
            elif att_day == 0 and c[t] > c[t - 1]:
                att_day = 1; att_low = low_since
            elif att_day >= 1:
                att_day += 1
                if att_day >= 4 and c[t] / c[t - 1] - 1 >= 0.0125 and v[t] > v[t - 1]:
                    state = True
                    dist.clear()                        # IBD: the distribution count restarts with a new uptrend
        on[t] = state
    return on


GATES = {"spy200": spy_c > SPY_SMA200, "spy10": spy_c > SPY_SMA10, "ftd": ftd_state()}


# ================================================================================================ C1 oversold limit dip
def c1_long(sig, R, Lp, ex, gate=None, ovl=None):
    s = ELIGB & (Cn > SMA200) & nz((RSI3 < 15) if sig == "rsi3_15" else (RSI2 < 5))
    if R == "spy200":
        s &= GATES["spy200"][:, None]
    if gate is not None:
        s &= GATES[gate][:, None]

    def make(i, j):
        ei = i + 1
        if locked[ei]:
            return None
        lim = Cn[i, j] * (1 - Lp)
        if not (Lx[ei, j] <= lim):
            return None
        ep = min(Ox[ei, j], lim)
        if ex == "open":
            xi = ei + 1
            if xi >= T or locked[xi] or not np.isfinite(Ox[xi, j]):
                return None
            return {"i": i, "j": j, "ei": ei, "ep": ep, "ek": "O", "xi": xi, "xp": Ox[xi, j], "xk": "O", "why": "open"}
        return run_walk(j, ei, ep, 1, "I", "O", lambda d: Cx[d, j] > SMA5[d, j], None, None, ei + 5, ovl, i)
    t = book(s, 1, make)
    return fix_kidd(t, 1)


def c1_short(Lp, ex):
    up3 = (Cn > np.roll(Cn, 1, 0)) & (np.roll(Cn, 1, 0) > np.roll(Cn, 2, 0)) & (np.roll(Cn, 2, 0) > np.roll(Cn, 3, 0))
    up3[:3] = False
    s = ELIGB & nz(RSI3 > 90) & up3

    def make(i, j):
        ei = i + 1
        if locked[ei]:
            return None
        lim = Cn[i, j] * (1 + Lp)
        if not (Hx[ei, j] >= lim):
            return None
        ep = max(Ox[ei, j], lim)
        if ex == "open":
            xi = ei + 1
            if xi >= T or locked[xi] or not np.isfinite(Ox[xi, j]):
                return None
            return {"i": i, "j": j, "ei": ei, "ep": ep, "ek": "O", "xi": xi, "xp": Ox[xi, j], "xk": "O", "why": "open"}
        r = cm.walk(j, ei, ep, -1, "I", None, None, lambda d: Cx[d, j] < SMA5[d, j], ei + 5)
        if r is None:
            return None
        return {"i": i, "j": j, "ei": ei, "ep": ep, "ek": "O", "xi": r[0], "xp": r[1], "xk": r[2], "why": r[3]}
    return book(s, -1, make)


# ================================================================================================ C2 tight base breakout
MOM63 = (C / C.shift(63) - 1).to_numpy()
MAXH252 = H.rolling(252, min_periods=200).max().to_numpy()


def xs_top(X, elig, q):
    A = np.where(elig, X, np.nan)
    cut = np.nanquantile(A, 1 - q, axis=1)[:, None]
    with np.errstate(invalid="ignore"):
        return A >= cut


TREND2 = ELIGB & nz(Cn > SMA50) & nz(SMA50 > SMA200) & nz(Cn >= 0.75 * MAXH252)
BASE = {B: (H.shift(1).rolling(B).max().to_numpy(), L.shift(1).rolling(B).min().to_numpy()) for B in (10, 20)}
prevCn = np.vstack([np.full(N, np.nan), Cn[:-1]])


def c2_signals(M, B, w):
    bh, bl = BASE[B]
    with np.errstate(invalid="ignore"):
        s = TREND2 & xs_top(MOM63, TREND2 | ELIGB, M) & ((bh - bl) / prevCn < w) & (Cn > bh)
    return s, bh, bl


def c2(M, B, w, X, gate=None, ovl=None):
    s, bh, bl = c2_signals(M, B, w)
    if gate is not None:
        s &= GATES[gate][:, None]
    XS = SMA10 if X == "sma10" else SMA20

    def make(i, j):
        ei = i + 1
        if locked[ei] or not np.isfinite(Ox[ei, j]):
            return None
        ep = Ox[ei, j]
        stop = bl[i, j]
        if not stop < ep:
            return None
        return run_walk(j, ei, ep, 1, "O", "O", lambda d: Cx[d, j] < XS[d, j], stop, None, ei + 40, ovl, i)
    return fix_kidd(book(s, 1, make), 1)


# ================================================================================================ C3 uptrend pullback to MA
BELOW20 = np.cumsum(np.nan_to_num(Cx < SMA20).astype(np.int32), 0)
SMA50R = nz(SMA50 > np.vstack([np.full((20, N), np.nan), SMA50[:-20]]))


def c3(k, entry, ex, gate=None, ovl=None):
    MA = SMA20 if k == 20 else SMA50
    with np.errstate(invalid="ignore"):
        s = ELIGB & nz(Cn > SMA200) & SMA50R & (np.abs(Ln / MA - 1) <= 0.01) & (Cn > MA)
    if gate is not None:
        s &= GATES[gate][:, None]

    def make(i, j):
        stop = MA[i, j] - ATR14[i, j]
        if entry == "close":
            ei, ep, mode, ek = i, Cx[i, j], "C", "C"
        else:
            ei = i + 1
            if locked[ei]:
                return None
            trig = Hn[i, j] + 0.01
            if not (Hx[ei, j] >= trig):
                return None
            ep, mode, ek = max(Ox[ei, j], trig), "I", "O"
        if not (np.isfinite(ep) and stop < ep):
            return None
        if ex == "k10":
            return run_walk(j, ei, ep, 1, mode, ek, None, stop, None, ei + 10, ovl, i)
        s0 = ei + 1 if mode == "C" else ei                 # first close checked

        def rule(d):                                       # second close below SMA20 since entry (stateless)
            return BELOW20[d, j] - BELOW20[s0 - 1, j] >= 2
        return run_walk(j, ei, ep, 1, mode, ek, rule, stop, None, ei + 60, ovl, i)
    return fix_kidd(book(s, 1, make), 1)


# ================================================================================================ C4 new-high breakout
MAXC = {n: C.shift(1).rolling(n, min_periods=n).max().to_numpy() for n in (50, 252)}
VOL50 = V.shift(1).rolling(50, min_periods=40).mean().to_numpy()
LL = {k: L.shift(1).rolling(k, min_periods=k).min().to_numpy() for k in (20, 50)}


def c4(Nh, vol, ex, gate=None, ovl=None):
    s = ELIGB & nz(Cn >= MAXC[Nh]) & GATES["spy200"][:, None]
    if vol == "v15":
        s &= nz(cm.Vn >= 1.5 * VOL50)
    if gate is not None:
        s &= GATES[gate][:, None]

    def make(i, j):
        ei = i + 1
        if locked[ei] or not np.isfinite(Ox[ei, j]):
            return None
        ep = Ox[ei, j]
        if ex == "bracket":
            return run_walk(j, ei, ep, 1, "O", "O", None, ep * 0.93, ep * 1.05, ei + 5, ovl, i)
        k = 20 if ex == "don20" else 50
        return run_walk(j, ei, ep, 1, "O", "O", None, lambda d: LL[k][d, j], None, ei + 250, ovl, i)
    return fix_kidd(book(s, 1, make), 1)


# ================================================================================================ C5 calendar
FOMC = """2016-01-27 2016-03-16 2016-04-27 2016-06-15 2016-07-27 2016-09-21 2016-11-02 2016-12-14
2017-02-01 2017-03-15 2017-05-03 2017-06-14 2017-07-26 2017-09-20 2017-11-01 2017-12-13
2018-01-31 2018-03-21 2018-05-02 2018-06-13 2018-08-01 2018-09-26 2018-11-08 2018-12-19
2019-01-30 2019-03-20 2019-05-01 2019-06-19 2019-07-31 2019-09-18 2019-10-30 2019-12-11
2020-01-29 2020-04-29 2020-06-10 2020-07-29 2020-09-16 2020-11-05 2020-12-16
2021-01-27 2021-03-17 2021-04-28 2021-06-16 2021-07-28 2021-09-22 2021-11-03 2021-12-15
2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21 2022-11-02 2022-12-14
2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18
2025-01-29 2025-03-19 2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10
2026-01-28 2026-03-18 2026-04-29 2026-06-17 2026-07-29 2026-09-16""".split()
FOMC_ROWS = [int(dates.get_loc(pd.Timestamp(x))) for x in FOMC if pd.Timestamp(x) in dates]


def c5a(cond):
    rows = []
    j = SPY
    for f in FOMC_ROWS:
        e = f - 1
        if locked[e] or locked[f]:
            continue
        if cond == "neg" and not (Cn[e, j] / Cn[e - 1, j] - 1 < 0):
            continue
        rows.append({"i": e, "j": j, "ei": e, "ep": Cx[e, j], "ek": "C", "xi": f, "xp": Cx[f, j], "xk": "C", "why": "fomc"})
    return cm.finish(rows, 1)


def first_on_after(y, m, d):
    k = int(np.searchsorted(dates.values, np.datetime64(f"{y}-{m:02d}-{d:02d}")))
    return k if k < T else None


def c5b():
    rows = []
    iw, sp = col["IWM"], SPY
    for y in range(2016, 2026):
        a = first_on_after(y, 12, 15)
        b = first_on_after(y + 1, 1, 1)
        if a is None or b is None:
            continue
        b -= 1
        if locked[a] or locked[b]:
            continue
        g = (Cn[b, iw] / Cn[a, iw] - 1) - (Cn[b, sp] / Cn[a, sp] - 1)
        days = (dates[b] - dates[a]).days
        net = g - 0.5 * (cm.cost(Cn[a, iw]) + cm.cost(Cn[b, iw]) + cm.cost(Cn[a, sp]) + cm.cost(Cn[b, sp])) \
            - 0.5 * cm.BORROW * days / 365
        rows.append({"i": a, "j": iw, "ei": a, "xi": b, "ep": Cn[a, iw], "xp": Cn[b, iw], "ek": "C", "xk": "C",
                     "gross": g / 2, "net": net, "date": dates[a], "hold": b - a, "w": 1.0, "side": 0})
    return pd.DataFrame(rows)


def c5c(q):
    rows = []
    for y in range(2016, 2026):
        s15 = first_on_after(y, 12, 15)
        s20 = first_on_after(y, 12, 20)
        x15 = first_on_after(y + 1, 1, 15)
        y0 = first_on_after(y, 1, 1)
        if None in (s15, s20, x15, y0) or y0 == 0:
            continue
        ybase = y0 - 1                                      # last close of the prior year (input only)
        if locked[s20] or locked[x15] or locked[s15]:
            continue
        e = ELIGB[s15]
        ytd = np.where(e, Cn[s15] / Cn[ybase] - 1, np.nan)
        ok = np.isfinite(ytd)
        cut = np.nanquantile(ytd[ok], q)
        for j in np.flatnonzero(ok & (ytd <= cut)):
            if np.isfinite(Cx[s20, j]) and np.isfinite(Cx[x15, j]):
                rows.append({"i": s20, "j": j, "ei": s20, "ep": Cx[s20, j], "ek": "C", "xi": x15, "xp": Cx[x15, j],
                             "xk": "C", "why": "jan"})
    return cm.finish(rows, 1)


# ================================================================================================ C6 anchored VWAP
def earn_rows():
    e = pd.read_parquet(cm.ROOT / "research" / "bdi" / "earnings" / "data" / "earnings_yf.parquet",
                        columns=["symbol", "date", "session"])
    e = e[(e.date >= "2019-01-01") & (e.session != "unknown") & e.symbol.isin(col)]
    d = e.date.values.astype("datetime64[ns]")
    k = np.searchsorted(dates.values, d)                    # first session on/after the report date
    exact = (k < T) & (dates.values[np.minimum(k, T - 1)] == d)
    k = np.where(e.session.eq("amc").to_numpy() & exact, k + 1, k)
    out = {}
    for s, r in zip(e.symbol, k):
        if r < T:
            out.setdefault(col[s], []).append(int(r))
    return {j: np.array(sorted(set(v))) for j, v in out.items()}


TP = (Hn + Ln + Cn) / 3
PV = np.nan_to_num(TP * cm.Vn)
VV = np.nan_to_num(cm.Vn)
CPV = np.vstack([np.zeros(N), np.cumsum(PV, 0)])                  # CPV[t+1] = sum_{<=t}
CVV = np.vstack([np.zeros(N), np.cumsum(VV, 0)])


def avwap(j, a, t):
    v = CVV[t + 1, j] - CVV[a, j]
    return (CPV[t + 1, j] - CPV[a, j]) / v if v > 0 else np.nan


def anchors(kind):
    """A[t, j] = anchor row usable at t (<= t-5), -1 if none."""
    A = np.full((T, N), -1, np.int32)
    if kind == "earn":
        er = earn_rows()
        for j, rr in er.items():
            k = np.searchsorted(rr, np.arange(T) - 5, side="right") - 1
            A[:, j] = np.where(k >= 0, rr[np.maximum(k, 0)], -1)
    else:
        from numpy.lib.stride_tricks import sliding_window_view
        for j in range(N):
            h = np.where(np.isfinite(Hn[:, j]), Hn[:, j], -np.inf)
            if len(h) < 252:
                continue
            am = sliding_window_view(h, 252).argmax(1) + np.arange(T - 251)
            a = np.full(T, -1)
            a[251:] = am
            a[~np.isfinite(Hn[:, j])] = -1
            A[:, j] = np.where((a >= 0) & (a <= np.arange(T) - 5), a, -1)
    return A


def c6(kind, ex):
    A = anchors(kind)
    start = int(np.searchsorted(dates.values, np.datetime64("2019-01-01"))) if kind == "earn" else 0
    sigs = []
    cand = ELIGB & nz(Cn > SMA50) & (A >= 0)
    cand[:max(start, 1)] = False
    for i, j in zip(*np.nonzero(cand)):
        a = A[i, j]
        av = avwap(j, a, i); av1 = avwap(j, a, i - 1)
        atr = ATR14[i, j]
        if not (np.isfinite(av) and np.isfinite(av1) and np.isfinite(atr)):
            continue
        if Cn[i - 1, j] > av1 and abs(Ln[i, j] - av) <= 0.5 * atr and Cn[i, j] > av:
            sigs.append((i, j))
    print("C6", kind, "signals", len(sigs), flush=True)

    def make(i, j):
        ei = i + 1
        if locked[ei] or not np.isfinite(Ox[ei, j]):
            return None
        ep = Ox[ei, j]
        a = A[i, j]
        stop = avwap(j, a, i) - ATR14[i, j]
        if not stop < ep:
            return None
        if ex == "k10":
            r = cm.walk(j, ei, ep, 1, "O", stop, None, None, ei + 10)
        else:
            r = cm.walk(j, ei, ep, 1, "O", stop, None, lambda d: Cx[d, j] < avwap(j, a, d), ei + 60)
        if r is None:
            return None
        return {"i": i, "j": j, "ei": ei, "ep": ep, "ek": "O", "xi": r[0], "xp": r[1], "xk": r[2], "why": r[3]}
    return book(sigs, 1, make)


# ================================================================================================ C7 index streaks / day 3
def c7_streak(Nd, ex):
    sigs = []
    for j in IDX:
        c = Cn[:, j]
        dn = np.r_[False, c[1:] < c[:-1]]
        st = np.zeros(T, int)
        for t in range(1, T):
            st[t] = st[t - 1] + 1 if dn[t] else 0
        sigs += [(i, j) for i in np.flatnonzero(st == Nd)]

    def make(i, j):
        if locked[i] or not np.isfinite(Cx[i, j]):
            return None
        ep = Cx[i, j]
        if ex == "k5":
            r = cm.walk(j, i, ep, 1, "C", None, None, None, i + 5)
        else:
            r = cm.walk(j, i, ep, 1, "C", None, None, lambda d: Cx[d, j] > Cx[d - 1, j], i + 20)
        if r is None:
            return None
        return {"i": i, "j": j, "ei": i, "ep": ep, "ek": "C", "xi": r[0], "xp": r[1], "xk": r[2], "why": r[3]}
    return book(sigs, 1, make)


def c7_day3(ex):
    HH20 = H.shift(1).rolling(20).max().to_numpy(); LL20 = L.shift(1).rolling(20).min().to_numpy()
    rng = Hn - Ln
    with np.errstate(invalid="ignore", divide="ignore"):
        clv = np.where(rng > 0, (Cn - Ln) / rng, np.nan)
        ok = (clv >= 0.75) & (Cn < HH20) & (Cn > LL20)
    sigs = []
    for j in IDX:
        o = ok[:, j]
        sigs += [(i, j) for i in np.flatnonzero(o & np.r_[False, o[:-1]])]

    def make(i, j):
        ei = i + 1
        if ei >= T or locked[ei] or not np.isfinite(Ox[ei, j]):
            return None
        ep = Ox[ei, j]
        if ex == "close":
            r = cm.walk(j, ei, ep, -1, "O", None, None, None, ei)
        else:
            r = cm.walk(j, ei, ep, -1, "O", None, None, lambda d: Cx[d, j] < Cx[d - 1, j], ei + 10)
        if r is None:
            return None
        return {"i": i, "j": j, "ei": ei, "ep": ep, "ek": "O", "xi": r[0], "xp": r[1], "xk": r[2], "why": r[3]}
    return book(sigs, -1, make)


# ================================================================================================ run
def per_inst(cid, fam, side, desc, t, params):
    for s in ("SPY", "QQQ", "IWM"):
        score(f"{cid}__{s}", fam + "_inst", side, desc + f" ({s} only, reporting)", t[t.j == col[s]] if len(t) else t,
              params, stock=False)


def main():
    # ---- C1
    for sig in ("rsi3_15", "rsi2_5"):
        for R in ("none", "spy200"):
            for Lp in (0.02, 0.03, 0.05):
                for ex in ("sma5", "open"):
                    t = c1_long(sig, R, Lp, ex)
                    score(f"C1_L_{sig}_{R}_L{int(Lp*100)}_{ex}", "C1", 1,
                          f"long >SMA200 {sig} regime {R}, limit -{Lp:.0%}, exit {ex}", t,
                          {"sig": sig, "R": R, "L": Lp, "exit": ex}, keep=(sig, R, Lp, ex) == ("rsi3_15", "none", 0.02, "sma5"))
            print("C1", sig, R, flush=True)
    for Lp in (0.03, 0.05):
        for ex in ("sma5", "open"):
            t = c1_short(Lp, ex)
            score(f"C1_S_rsi3_90_up3_L{int(Lp*100)}_{ex}", "C1", -1, f"short RSI3>90 + 3 up closes, limit +{Lp:.0%}, exit {ex}",
                  t, {"sig": "short", "R": "none", "L": Lp, "exit": ex})
    print("C1 short", flush=True)
    # ---- C2
    for M in (0.10, 0.20):
        for B in (10, 20):
            for w in (0.08, 0.12):
                for X in ("sma10", "sma20"):
                    t = c2(M, B, w, X)
                    score(f"C2_M{int(M*100)}_B{B}_w{int(w*100)}_{X}", "C2", 1,
                          f"tight base: mom63 top {M:.0%}, base {B}d < {w:.0%}, close above base high -> MOO, stop base low, exit close<{X}",
                          t, {"M": M, "B": B, "w": w, "X": X}, keep=(M, B, w, X) == (0.10, 10, 0.08, "sma10"))
        print("C2", M, flush=True)
    # ---- C3
    for k in (20, 50):
        for entry in ("close", "stop"):
            for ex in ("2nd_sma20", "k10"):
                t = c3(k, entry, ex)
                score(f"C3_sma{k}_{entry}_{ex}", "C3", 1, f"pullback to SMA{k} in uptrend, entry {entry}, exit {ex}", t,
                      {"k": k, "entry": entry, "exit": ex}, keep=(k, entry, ex) == (20, "close", "2nd_sma20"))
    print("C3", flush=True)
    # ---- C4
    for Nh in (50, 252):
        for vol in ("none", "v15"):
            for ex in ("don20", "don50", "bracket"):
                t = c4(Nh, vol, ex)
                score(f"C4_N{Nh}_{vol}_{ex}", "C4", 1, f"close at {Nh}d high, SPY>SMA200, vol {vol}, MOO, exit {ex}", t,
                      {"N": Nh, "vol": vol, "exit": ex}, keep=(Nh, vol, ex) == (50, "none", "don20"))
    print("C4", flush=True)
    # ---- C5 (daily parts; the 13:55 exits are in intraday.py)
    for cond in ("all", "neg"):
        t = c5a(cond)
        score(f"C5a_fomc_{cond}_close", "C5", 1, f"SPY FOMC eve close -> FOMC-day close, {cond}", t,
              {"cond": cond, "exit": "close"}, stock=False, keep=True)
    t = c5b()
    score("C5b_toy_IWM_SPY", "C5", 0, "IWM long / SPY short Dec 15 -> Dec 31 (net per $ of gross; pair)", t, {},
          stock=False, keep=True)
    for q in (0.10, 0.20):
        t = c5c(q)
        score(f"C5c_janrebound_q{int(q*100)}", "C5", 1, f"bottom {q:.0%} YTD on Dec 15, buy Dec 20 close, sell Jan 15 close",
              t, {"q": q}, keep=True)
    print("C5", flush=True)
    # ---- C6
    for kind in ("earn", "h252"):
        for ex in ("avwap", "k10"):
            t = c6(kind, ex)
            score(f"C6_{kind}_{ex}", "C6", 1, f"AVWAP from {kind} anchor touch from above, MOO, exit {ex}", t,
                  {"anchor": kind, "exit": ex}, keep=True)
    print("C6", flush=True)
    # ---- C7
    for Nd in (3, 4, 5):
        for ex in ("upclose", "k5"):
            t = c7_streak(Nd, ex)
            cid = f"C7_streak{Nd}_{ex}"
            score(cid, "C7", 1, f"SPY/QQQ/IWM {Nd} down closes -> buy close, exit {ex}", t, {"Nd": Nd, "exit": ex},
                  stock=False, keep=True)
            per_inst(cid, "C7", 1, f"{Nd} down closes, exit {ex}", t, {"Nd": Nd, "exit": ex})
    for ex in ("close", "downclose"):
        t = c7_day3(ex)
        cid = f"C7_day3_{ex}"
        score(cid, "C7", -1, f"SPY/QQQ/IWM two strong closes inside 20d range -> short day-3 open, exit {ex}", t,
              {"exit": ex}, stock=False, keep=True)
        per_inst(cid, "C7", -1, f"day 3 short exit {ex}", t, {"exit": ex})
    print("C7", flush=True)
    # ---- C8 gates and C9 overlays on the base configurations of C1-C4
    bases = {"C1": lambda **kw: c1_long("rsi3_15", "none", 0.02, "sma5", **kw),
             "C2": lambda **kw: c2(0.10, 10, 0.08, "sma10", **kw),
             "C3": lambda **kw: c3(20, "close", "2nd_sma20", **kw),
             "C4": lambda **kw: c4(50, "none", "don20", **kw)}
    for b, fn in bases.items():
        for g in ("spy200", "spy10", "ftd"):
            score(f"C8_{g}_on_{b}", "C8", 1, f"{b} base, only when gate {g} is on", fn(gate=g), {"base": b, "gate": g},
                  keep=True)
        for o in ("sma20x2", "kidd", "keltner"):
            score(f"C9_{o}_on_{b}", "C9", 1, f"{b} base + exit overlay {o}", fn(ovl=o), {"base": b, "ovl": o}, keep=True)
        score(f"C9_governor_on_{b}", "C9", 1, f"{b} base, Komar equity-curve governor", governor(cm.TRADES[_base_id(b)]),
              {"base": b, "ovl": "governor"}, keep=True)
        print("C8/C9", b, flush=True)
    print("FTD on-share", round(float(GATES["ftd"][252:].mean()), 3), "spy200", round(float(GATES["spy200"][252:].mean()), 3),
          "spy10", round(float(GATES["spy10"][252:].mean()), 3))
    pd.DataFrame(cm.RESULTS).to_csv(cm.HERE / "raw_daily.csv", index=False)
    cm.save_trades(cm.DATA / "trades_daily.parquet")


def _base_id(b):
    return {"C1": "C1_L_rsi3_15_none_L2_sma5", "C2": "C2_M10_B10_w8_sma10", "C3": "C3_sma20_close_2nd_sma20",
            "C4": "C4_N50_none_don20"}[b]


if __name__ == "__main__":
    main()
