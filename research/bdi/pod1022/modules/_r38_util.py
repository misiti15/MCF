"""_r38_util - shared helpers for the pod1022 round-3 batch 8 lab modules (not a setup; no SIDE / mask).

Point-in-time inputs the scorer frame does not carry, all built from _cwt3_bars (full-session 5m bars, the frame's
month plus the previous OPEN month as warm-up; the rule-19 locked block is never read) and lib.daily():
  * prior_day_extremes: per (symbol, date D) the bar-close time of D-1's low / high of day (argmin / argmax over
    D-1's 09:35..15:55 bars; when lib.daily()'s D-1 low / high is beyond every 5m bar, the extreme printed in the
    missing 15:55-16:00 bar and the time is set to 1600), D-1's low / high and close. Completed days only.
  * stc / ema on continuous 5m closes per symbol (across days), and the same STC on 15m closes (the 5m bar that
    completes each 15m bar, 09:45, 10:00, ...).
  * chandelier exit (22, 3) direction / lines and ZLSMA(32) on continuous 5m bars.
Every rolling value ends at the bar it is stored on (no lookahead). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt3_bars as C  # noqa: E402

_CACHE = {}


def f(df, c):
    return C.f(df, c)


def key(df):
    return C.key(df)


def lag(x, k, n=1):
    return C.lag(x, k, n)


def base(df):
    return C.base(df)


def rows_at(df, sym, cols):
    """Values of symbol `sym`'s row at the same (date, tod), broadcast to every row (NaN where missing)."""
    s = df["symbol"].astype(str).to_numpy()
    d = df["date"].astype(str).to_numpy()
    t = df["tod"].to_numpy(np.int64)
    sel = s == sym
    tab = pd.DataFrame({"date": d[sel], "tod": t[sel]})
    for c in cols:
        tab[c] = f(df, c)[sel]
    tab = tab.drop_duplicates(["date", "tod"])
    m = pd.DataFrame({"date": d, "tod": t}).merge(tab, on=["date", "tod"], how="left")
    return {c: m[c].to_numpy(float) for c in cols}


# ---------------------------------------------------------------- prior-day extremes (time of the LOD / HOD)
def prior_day_extremes(df, symbols):
    fb = C.full_bars(df, symbols=symbols)
    if fb is None or not len(fb):
        return None
    fb = fb.copy()
    fb["date"] = fb["date"].astype(str)
    i_lo = fb.groupby(["symbol", "date"])["l"].idxmin()
    i_hi = fb.groupby(["symbol", "date"])["h"].idxmax()
    t = pd.DataFrame({"symbol": fb.loc[i_lo, "symbol"].to_numpy(), "date": fb.loc[i_lo, "date"].to_numpy(),
                      "lo5": fb.loc[i_lo, "l"].to_numpy(float), "lo_tod": fb.loc[i_lo, "tod"].to_numpy(float)})
    h = pd.DataFrame({"symbol": fb.loc[i_hi, "symbol"].to_numpy(), "date": fb.loc[i_hi, "date"].to_numpy(),
                      "hi5": fb.loc[i_hi, "h"].to_numpy(float), "hi_tod": fb.loc[i_hi, "tod"].to_numpy(float)})
    t = t.merge(h, on=["symbol", "date"])
    d = C.lib().daily()[["symbol", "date", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    t = t.merge(d[d["symbol"].isin(symbols)], on=["symbol", "date"], how="inner")   # completed days with a daily row
    eps = 1e-6 * t["close"]
    t.loc[t["low"] < t["lo5"] - eps, "lo_tod"] = 1600.0      # low printed in the missing 15:55-16:00 bar
    t.loc[t["high"] > t["hi5"] + eps, "hi_tod"] = 1600.0
    t["dlo"] = np.minimum(t["low"], t["lo5"])
    t["dhi"] = np.maximum(t["high"], t["hi5"])
    return t[["symbol", "date", "lo_tod", "hi_tod", "dlo", "dhi", "close"]]


def prev_trading_day():
    """{date str: previous NYSE trading day str} (hard-coded calendar)."""
    if "ptd" in _CACHE:
        return _CACHE["ptd"]
    hol = set(pd.to_datetime(HOLIDAYS).date)
    days = [str(x) for x in pd.bdate_range("2024-01-01", "2027-01-31").date if x not in hol]
    out = {days[i]: days[i - 1] for i in range(1, len(days))}
    _CACHE["ptd"] = out
    return out


def map_prior(df, symbols):
    """{lo_tod_1, hi_tod_1, dlo_1, dhi_1, close_1} per df row: the values of D-1 = the previous NYSE trading day
    (NaN when D-1 is missing, e.g. after the locked block or past the end of the daily table)."""
    cols = ["lo_tod_1", "hi_tod_1", "dlo_1", "dhi_1", "close_1"]
    t = prior_day_extremes(df, symbols)
    if t is None:
        return {c: np.full(len(df), np.nan) for c in cols}
    ptd = prev_trading_day()
    t = t.rename(columns={"date": "pdate", "lo_tod": "lo_tod_1", "hi_tod": "hi_tod_1", "dlo": "dlo_1",
                          "dhi": "dhi_1", "close": "close_1"})
    d = df["date"].astype(str).to_numpy()
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "pdate": [ptd.get(x, "") for x in d]})
    m = k.merge(t, on=["symbol", "pdate"], how="left")
    return {c: m[c].to_numpy(float) for c in cols}


# ---------------------------------------------------------------- indicator kernels (per symbol segment)
@numba.njit(cache=False)
def _ema(x, b, e, n):
    out = np.full(len(x), np.nan)
    a = 2.0 / (n + 1.0)
    for s in range(len(b)):
        v = np.nan
        cnt = 0
        for i in range(b[s], e[s]):
            if not (x[i] == x[i]):
                continue
            v = x[i] if not (v == v) else v + a * (x[i] - v)
            cnt += 1
            if cnt >= n:
                out[i] = v
    return out


@numba.njit(cache=False)
def _stc(x, b, e, fast, slow, cyc, fac):
    """Schaff Trend Cycle (TradingView standard): MACD(fast, slow) -> stochastic(cyc) smoothed by fac -> again."""
    out = np.full(len(x), np.nan)
    af = 2.0 / (fast + 1.0)
    asl = 2.0 / (slow + 1.0)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        m = i1 - i0
        if m <= 0:
            continue
        macd = np.full(m, np.nan)
        ef = np.nan
        es = np.nan
        for j in range(m):
            v = x[i0 + j]
            ef = v if not (ef == ef) else ef + af * (v - ef)
            es = v if not (es == es) else es + asl * (v - es)
            macd[j] = ef - es
        ff = 0.0
        pf = np.nan
        pfa = np.full(m, np.nan)
        ff2 = 0.0
        st = np.nan
        for j in range(m):
            if j >= cyc - 1:
                lo = macd[j]
                hi = macd[j]
                for q in range(j - cyc + 1, j + 1):
                    lo = min(lo, macd[q])
                    hi = max(hi, macd[q])
                if hi - lo > 0:
                    ff = (macd[j] - lo) / (hi - lo) * 100.0
                pf = ff if not (pf == pf) else pf + fac * (ff - pf)
                pfa[j] = pf
            if j >= 2 * cyc - 2:
                lo = pfa[j]
                hi = pfa[j]
                for q in range(j - cyc + 1, j + 1):
                    lo = min(lo, pfa[q])
                    hi = max(hi, pfa[q])
                if hi - lo > 0:
                    ff2 = (pfa[j] - lo) / (hi - lo) * 100.0
                st = ff2 if not (st == st) else st + fac * (ff2 - st)
                if j >= slow + 2 * cyc:          # warm-up: MACD slow EMA + two stochastic windows
                    out[i0 + j] = st
    return out


@numba.njit(cache=False)
def _ce(h, l, c, b, e, n, mult):
    """Chandelier Exit (everget TradingView logic, high / low extremums, Wilder ATR): returns dir, longStop,
    shortStop per bar. dir flips to +1 when close > the prior bar's shortStop, to -1 when close < the prior longStop."""
    N = len(c)
    d = np.zeros(N, np.int64)
    ls = np.full(N, np.nan)
    ss = np.full(N, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        atr = np.nan
        trs = 0.0
        lsp = np.nan
        ssp = np.nan
        dirp = 1
        for i in range(i0, i1):
            j = i - i0
            tr = h[i] - l[i] if j == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
            if j < n:
                trs += tr
                if j == n - 1:
                    atr = trs / n
            else:
                atr = (atr * (n - 1) + tr) / n
            if j < n - 1:
                d[i] = 0
                continue
            hh = h[i]
            ll = l[i]
            for q in range(i - n + 1, i + 1):
                hh = max(hh, h[q])
                ll = min(ll, l[q])
            lst = hh - mult * atr
            sst = ll + mult * atr
            if lsp == lsp and c[i - 1] > lsp:
                lst = max(lst, lsp)
            if ssp == ssp and c[i - 1] < ssp:
                sst = min(sst, ssp)
            dr = dirp
            if ssp == ssp and c[i] > ssp:
                dr = 1
            elif lsp == lsp and c[i] < lsp:
                dr = -1
            ls[i] = lst
            ss[i] = sst
            d[i] = dr if j >= 2 * n else 0          # warm-up: no direction before 2n bars
            lsp = lst
            ssp = sst
            dirp = dr
    return d, ls, ss


@numba.njit(cache=False)
def _linreg(x, b, e, n):
    """Linear-regression end-point value over the last n values (TradingView linreg(x, n, 0))."""
    out = np.full(len(x), np.nan)
    xm = (n - 1) / 2.0
    vx = 0.0
    for q in range(n):
        vx += (q - xm) ** 2
    for s in range(len(b)):
        for i in range(b[s] + n - 1, e[s]):
            sy = 0.0
            sxy = 0.0
            ok = True
            for q in range(n):
                v = x[i - n + 1 + q]
                if not (v == v):
                    ok = False
                    break
                sy += v
                sxy += (q - xm) * v
            if ok:
                out[i] = sy / n + sxy / vx * (n - 1 - xm)
    return out


def segments(sym):
    s = np.asarray(sym)
    st = np.flatnonzero(np.r_[True, s[1:] != s[:-1]]) if len(s) else np.zeros(0, np.int64)
    en = np.r_[st[1:], len(s)] if len(s) else np.zeros(0, np.int64)
    return st.astype(np.int64), en.astype(np.int64)


def _fb(df, symbols=None):
    fb = C.full_bars(df, symbols=symbols)
    return fb


def stc_ema_rows(df, fast=23, slow=50, cyc=10, fac=0.5, ema_n=200):
    """Per df row: stc5, stc5_prev (prior continuous 5m bar), ema200, ema200 12 bars ago, stc15, stc15_prev
    (on the rows whose tod completes a 15m bar; NaN elsewhere), min low of this + previous 5 bars."""
    ck = ("stc", C.month_of(df), len(df), fast, slow, cyc, fac, ema_n)
    if ck in _CACHE:
        return _CACHE[ck]
    _CACHE.clear()
    fb = _fb(df)
    cols = ["stc", "stcp", "ema", "ema12", "stc15", "stc15p", "lo6"]
    if fb is None:
        return {c: np.full(len(df), np.nan) for c in cols}
    sym = fb["symbol"].to_numpy(object)
    b, e = segments(sym)
    c = fb["c"].to_numpy(float)
    lo = fb["l"].to_numpy(float)
    stc = _stc(c, b, e, fast, slow, cyc, fac)
    ema = _ema(c, b, e, ema_n)
    k = pd.factorize(pd.Series(sym))[0]
    t = pd.DataFrame({"symbol": sym, "date": fb["date"].to_numpy(), "tod": fb["tod"].to_numpy(np.int64)})
    t["stc"] = stc
    t["stcp"] = C.lag(stc, k, 1)
    t["ema"] = ema
    t["ema12"] = C.lag(ema, k, 12)
    t["lo6"] = np.nanmin(np.vstack([lo] + [C.lag(lo, k, j) for j in range(1, 6)]), axis=0)
    tod = t["tod"].to_numpy(np.int64)
    mins = (tod // 100) * 60 + tod % 100 - 570
    q = (mins % 15 == 0) & (mins > 0)
    s15 = sym[q]
    b15, e15 = segments(s15)
    st15 = _stc(c[q], b15, e15, fast, slow, cyc, fac)
    k15 = pd.factorize(pd.Series(s15))[0]
    t["stc15"] = np.nan
    t["stc15p"] = np.nan
    t.loc[q, "stc15"] = st15
    t.loc[q, "stc15p"] = C.lag(st15, k15, 1)
    out = C.map_rows(df, t, cols)
    _CACHE[ck] = out
    return out


def ce_zlsma_rows(df, n=22, mult=3.0, zn=32):
    """Per df row: CE dir, prior-bar dir, CE long line, ZLSMA(zn), ZLSMA 3 bars ago."""
    ck = ("ce", C.month_of(df), len(df), n, mult, zn)
    if ck in _CACHE:
        return _CACHE[ck]
    _CACHE.clear()
    fb = _fb(df)
    cols = ["dir", "dirp", "cel", "zl", "zl3"]
    if fb is None:
        return {c: np.full(len(df), np.nan) for c in cols}
    sym = fb["symbol"].to_numpy(object)
    b, e = segments(sym)
    h, l, c = (fb[x].to_numpy(float) for x in ("h", "l", "c"))
    d, ls, _ss = _ce(h, l, c, b, e, n, mult)
    lr = _linreg(c, b, e, zn)
    lr2 = _linreg(lr, b, e, zn)
    zl = lr + (lr - lr2)
    k = pd.factorize(pd.Series(sym))[0]
    d = d.astype(float)
    d[d == 0] = np.nan
    t = pd.DataFrame({"symbol": sym, "date": fb["date"].to_numpy(), "tod": fb["tod"].to_numpy(np.int64)})
    t["dir"] = d
    t["dirp"] = C.lag(d, k, 1)
    t["cel"] = ls
    t["zl"] = zl
    t["zl3"] = C.lag(zl, k, 3)
    out = C.map_rows(df, t, cols)
    _CACHE[ck] = out
    return out


# ---------------------------------------------------------------- NYSE calendar (hard-coded, as pod-cal-monthend)
HOLIDAYS = ["2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27", "2024-06-19", "2024-07-04",
            "2024-09-02", "2024-11-28", "2024-12-25",
            "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26", "2025-06-19",
            "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
            "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25", "2027-01-01"]


def tdom():
    """{date str: (trading day of month from the start, from the end)}; 1-based."""
    if "tdom" in _CACHE:
        return _CACHE["tdom"]
    hol = set(pd.to_datetime(HOLIDAYS).date)
    days = pd.Series([x for x in pd.bdate_range("2024-01-01", "2027-01-31").date if x not in hol])
    ym = days.map(lambda x: (x.year, x.month))
    fwd = days.groupby(ym).cumcount() + 1
    bwd = days.groupby(ym).cumcount(ascending=False) + 1
    out = {str(d): (int(a), int(z)) for d, a, z in zip(days, fwd, bwd)}
    _CACHE["tdom"] = out
    return out


def daily_sma(df, symbol, n):
    """Per row: (D-1 close, D-1 SMA_n of daily closes) of `symbol` from lib.daily() completed days."""
    ck = ("dsma", symbol, n)
    if ck not in _CACHE:
        d = C.lib().daily()
        d = d[d["symbol"].astype(str) == symbol][["date", "close"]].copy()
        d["date"] = pd.to_datetime(d["date"])
        d = d.sort_values("date").reset_index(drop=True)
        g = ((d["date"] - d["date"].shift()).dt.days > 7).cumsum()       # never bridge the locked block
        sma = d["close"].groupby(g).transform(lambda x: x.rolling(n, min_periods=n).mean())
        tab = pd.DataFrame({"d": d["date"], "c1": d["close"], "s1": sma})
        _CACHE[ck] = tab
    tab = _CACHE[ck]
    dd = pd.to_datetime(pd.Series(df["date"].astype(str).to_numpy()))
    # latest completed daily row strictly before D, within 5 calendar days
    idx = np.searchsorted(tab["d"].to_numpy(), dd.to_numpy(), side="left") - 1
    ok = idx >= 0
    idx2 = np.where(ok, idx, 0)
    gap = (dd.to_numpy() - tab["d"].to_numpy()[idx2]) / np.timedelta64(1, "D")
    ok &= gap <= 5
    c1 = np.where(ok, tab["c1"].to_numpy()[idx2], np.nan)
    s1 = np.where(ok, tab["s1"].to_numpy()[idx2], np.nan)
    return c1, s1
