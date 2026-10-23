"""_r33_util - shared helpers for the pod r3_3 modules (Warrior pullback-count gate, SMB IPR first pullback, Spencer
index drop / Monday lower low, SMB capitulation BB fade, SMB opening-drive Trade2Hold). Not a setup (no SIDE / mask).

Point-in-time inputs (all causal):
  * frame segment helpers (symbol-day runs; the frame is sorted by symbol, date, tod).
  * a per-row pullback counter (Ross Cameron 'first or second pullback'): state as of the bar BEFORE the decision bar.
  * a numba port of the CWT12-coil-k4 parent trigger (research/bdi/cwt/live/cwt_live_lib.b4a, nco = 4).
  * the opening-range ratio IPR = (09:30-09:45 high - low) / mean of the same over the 20 prior sessions (min 10;
    the series restarts after a > 10-day gap so nothing bridges the rule-19 locked block), from the _r24_bars day
    cache, plus the 09:45 close and a close-weighted 09:35-09:45 VWAP from the _r24_bars 5m bars.
  * daily values as of D-1 (lib.daily(), completed days only): closes D-1..D-3, D-1 high / low, SMA20 / SMA50,
    SMA20 five sessions earlier, 10-day closing high, red-day count over the last 5 sessions, first-session-of-week.
  * continuous 5m closes (prior open month as warm-up, _cwt3_bars.full_bars) for Bollinger(20, 2).
The rule-19 locked block (2024-11-01..2025-02-28) is never read. Educational only - not financial advice."""
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

_LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
_MEM = {}


def f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def base(df):
    c, atr = f(df, "close"), f(df, "atr_d")
    b = dict(c=c, h=f(df, "high"), l=f(df, "low"), atr=atr, tod=df["tod"].to_numpy(np.int64))
    with np.errstate(invalid="ignore", divide="ignore"):
        b["hod"] = c + f(df, "dist_hod_atr") * atr       # running high of day incl. 09:30-09:45 and this bar
        b["lod"] = c - f(df, "dist_lod_atr") * atr
        b["pdh"] = c + f(df, "dist_pdh_atr") * atr
        b["pdl"] = c - f(df, "dist_pdl_atr") * atr
        b["opn"] = c / (1 + f(df, "fromOpen") / 100)
        b["vwap"] = c / (1 + f(df, "vwapDistPct") / 100)
        b["atr5"] = f(df, "atrPct") / 100 * c
    k = key(df)
    b["k"] = k
    b["b"], b["e"] = segments(k)
    return b


def seg_of(b, e, n):
    s = np.zeros(n, np.int64)
    for q in range(len(b)):
        s[b[q]:e[q]] = q
    return s


# ---------------------------------------------------------------- pullback counter (Warrior 'first two pullbacks')
@numba.njit(cache=False)
def _pullbacks(b, e, h, l, hod, atr5, min_depth):
    """Per row i, the state as of the close of bar i-1 (before the decision bar):
    ordinal = completed qualifying pullbacks + 1 if the current one already qualifies; dcur = depth of the current
    pullback (anchor HOD - lowest low since it); dprev = depth of the last completed qualifying pullback (NaN = none).
    A pullback = the bars after a new HOD up to the next new HOD; it qualifies when it holds >= 2 consecutive bars with
    lower highs and its depth >= min_depth x ATR14(5m) at the anchor bar. The anchor at 09:50 is the HOD so far."""
    n = len(h)
    ordn = np.full(n, np.nan)
    dcur = np.full(n, np.nan)
    dprev = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        H = hod[i0] if hod[i0] == hod[i0] else h[i0]
        a5 = atr5[i0]
        lo = np.inf
        run = 0
        lh = False
        cnt = 0
        pdp = np.nan
        newbar = h[i0] >= H - 1e-9
        if newbar:
            H = h[i0]
        else:
            lo = l[i0]
        for i in range(i0 + 1, i1):
            # state through bar i-1 -> row i
            dep = H - lo if lo < np.inf else 0.0
            q = lh and a5 > 0 and dep >= min_depth * a5
            ordn[i] = cnt + (1 if q else 0)
            dcur[i] = dep
            dprev[i] = pdp
            # process bar i
            if h[i] > H:
                if q:
                    cnt += 1
                    pdp = dep
                H = h[i]
                a5 = atr5[i]
                lo = np.inf
                run = 0
                lh = False
            else:
                lo = min(lo, l[i])
                if h[i] < h[i - 1]:
                    run += 1
                else:
                    run = 0
                if run >= 2:
                    lh = True
    return ordn, dcur, dprev


def pullback_state(df, bb):
    return _pullbacks(bb["b"], bb["e"], bb["h"], bb["l"], bb["hod"], bb["atr5"], 0.3)


def gate(df, bb, arm):
    """arm 'a1': pullback ordinal <= 2; 'a2': a1 and current depth <= the previous pullback's depth (no expanding
    pullbacks; passes when there is no previous one); 'a3': a1 and HOD - open < 2.5 x daily ATR."""
    ordn, dcur, dprev = pullback_state(df, bb)
    with np.errstate(invalid="ignore"):
        g = ordn <= 2
        if arm == "a2":
            g &= ~(dcur > dprev)
        elif arm == "a3":
            g &= (bb["hod"] - bb["opn"]) < 2.5 * bb["atr"]
    return np.asarray(g, bool)


# ---------------------------------------------------------------- CWT12-coil-k4 parent (port of cwt_live_lib.b4a)
@numba.njit(cache=False)
def _b4a(b, e, h, l, c, atr_row, nco):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    for s in range(len(b)):
        s0, s1 = b[s], e[s]
        atr = atr_row[s0]                       # cwt_live_lib: atr = first value of the segment
        hod = -np.inf
        for i in range(s0, s1):
            hod = max(hod, h[i])                # frame-bar cummax (as in cwt_live_lib.arrays)
            if i - s0 + 1 < nco + 6:
                continue
            thr = hod - 0.1 * atr
            touches = 0
            for t in range(s0, i + 1):
                if h[t] >= thr:
                    touches += 1
            if touches < 3:
                continue
            a = i - nco + 1
            m0 = max(s0, a - 20)
            mr = 0.0
            for t in range(m0, a):
                mr += h[t] - l[t]
            mr /= (a - m0)
            ok = True
            lo = 1e18
            for k in range(a, i + 1):
                if not (h[k] - l[k] < 0.5 * mr and c[k] <= hod and hod - c[k] <= 0.25 * atr):
                    ok = False
                    break
                lo = min(lo, l[k])
            if ok and lo < c[i]:
                flag[i] = True
    return flag


def coil_k4(df, bb):
    return _b4a(bb["b"], bb["e"], bb["h"], bb["l"], bb["c"], bb["atr"], 4)


# ---------------------------------------------------------------- bull-flag parent (pod-wt / bdi-reddit trigger)
def flag_parent():
    if "flag" not in _MEM:
        import importlib.util
        p = _HERE / "pod-wt-bull-flag-breakout-or-bailout-long.py"
        spec = importlib.util.spec_from_file_location("_r33_flag_parent", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _MEM["flag"] = m
    return _MEM["flag"]


def flag_signal(df):
    """(mask, stop, target) of the bull-flag trigger shared by pod-wt-bull-flag-breakout-or-bailout-long and
    bdi-reddit-bull-flag-pole (pole / flag / break, stop flag low - 0.02 ATR, target flag high + pole)."""
    P = flag_parent()
    b = P._base(df)
    bb, ee = P._segments(b["k"])
    return P._kern(bb, ee, b["tod"], b["c"], b["h"], b["l"], b["hod"], b["vwap"], b["atr"],
                   P._f(df, "volumeRatio"), P.WINDOW[0], P.WINDOW[1])


# ---------------------------------------------------------------- IPR (SMB Radar opening-range ratio)
def ipr_tab():
    if "ipr" in _MEM:
        return _MEM["ipr"]
    d = R24.day()[["symbol", "date", "or_h", "or_l", "o935"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d[~d["date"].str[:7].isin(_LOCKED_MONTHS)]
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 10)).cumsum()
    w = (d["or_h"] - d["or_l"]).where(d["or_h"] > d["or_l"])
    base = w.groupby(g).transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
    d["orw"] = w
    d["ipr"] = w / base
    _MEM["ipr"] = d
    return d


def c945_tab(df):
    """Per (symbol, date str): the 09:45 close and the close-weighted VWAP of the 09:35-09:45 bars (r24 cache)."""
    ms = sorted(set(pd.Series(pd.unique(pd.Series(df["date"].to_numpy()).astype(str))).str[:7]) - _LOCKED_MONTHS)
    ck = ("c945", tuple(ms))
    if ck in _MEM:
        return _MEM[ck]
    for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "c945"]:
        del _MEM[kk]
    parts = []
    for m in ms:
        p = R24._OUT / "bars" / f"month={m}.parquet"
        if p.exists():
            x = pd.read_parquet(p, columns=["symbol", "dn", "tod", "c", "v"], filters=[("tod", "<=", 945)])
            parts.append(x)
    if not parts:
        _MEM[ck] = None
        return None
    B = pd.concat(parts, ignore_index=True)
    B["symbol"] = B["symbol"].astype(str)
    B["cv"] = B["c"].astype(float) * B["v"].astype(float)
    g = B.groupby(["symbol", "dn"])
    T = pd.DataFrame({"pv": g["cv"].sum(), "v": g["v"].sum().astype(float)})
    T["c945"] = B[B["tod"] == 945].set_index(["symbol", "dn"])["c"].astype(float)
    T = T.reset_index()
    T["vw945"] = T["pv"] / T["v"].where(T["v"] > 0)
    T["date"] = pd.to_datetime(T["dn"].astype(np.int64), unit="D").dt.strftime("%Y-%m-%d")
    T = T[["symbol", "date", "c945", "vw945"]]
    _MEM[ck] = T
    return T


def map_day(df, tab, cols):
    k = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(),
                      "date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy()})
    m = k.merge(tab[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


# ---------------------------------------------------------------- daily values as of D-1
def daily_tab():
    if "d" in _MEM:
        return _MEM["d"]
    d = C3.lib().daily()[["symbol", "date", "open", "high", "low", "close", "volume"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c = d["close"]
    gb = lambda s: s.groupby(g)
    sma20 = gb(c).transform(lambda x: x.rolling(20, min_periods=20).mean())
    sma50 = gb(c).transform(lambda x: x.rolling(50, min_periods=50).mean())
    hi10c = gb(c).transform(lambda x: x.rolling(10, min_periods=10).max())
    red = (c < gb(c).shift(1)).astype(float).where(gb(c).shift(1).notna())
    red5 = red.groupby(g).transform(lambda x: x.rolling(5, min_periods=5).sum())
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    out["c1"] = gb(c).shift(1)
    out["c2"] = gb(c).shift(2)
    out["c3"] = gb(c).shift(3)
    out["h1"] = gb(d["high"]).shift(1)
    out["l1"] = gb(d["low"]).shift(1)
    out["sma20_1"] = sma20.groupby(g).shift(1)
    out["sma20_6"] = sma20.groupby(g).shift(6)
    out["sma50_1"] = sma50.groupby(g).shift(1)
    out["hi10c_1"] = hi10c.groupby(g).shift(1)        # max close D-10..D-1
    out["red5_1"] = red5.groupby(g).shift(1)          # red closes among D-5..D-1
    # first session of its ISO week (calendar fact, known in advance): previous listed session in an earlier week
    prev_dt = dt.groupby(d["symbol"]).shift(1)
    wk = dt.dt.isocalendar()
    pwk = prev_dt.dt.isocalendar()
    out["wk_first"] = ((wk["year"] != pwk["year"]) | (wk["week"] != pwk["week"])).astype(float).where(
        prev_dt.notna() & ((dt - prev_dt).dt.days <= 7))
    _MEM["d"] = out
    return out


# ---------------------------------------------------------------- continuous Bollinger(20, 2) on 5m closes
def boll(df):
    """Per df row: Bollinger middle / lower band (20, 2) of continuous 5m closes (09:35..15:55 bars, previous open
    month as warm-up), and the session's 09:35+ bars for swing logic are not needed here."""
    P = C3.full_bars(df)
    n = len(df)
    if P is None:
        return np.full(n, np.nan), np.full(n, np.nan)
    c = pd.Series(P["c"].to_numpy(float))
    sym = P["symbol"].to_numpy()
    g = pd.factorize(sym)[0]
    mid = c.groupby(g).transform(lambda x: x.rolling(20, min_periods=20).mean())
    sd = c.groupby(g).transform(lambda x: x.rolling(20, min_periods=20).std(ddof=0))
    T = pd.DataFrame({"symbol": P["symbol"].to_numpy(object), "date": P["date"].to_numpy(),
                      "tod": P["tod"].to_numpy(np.int64), "bbm": mid.to_numpy(), "bbl": (mid - 2 * sd).to_numpy()})
    m = C3.map_rows(df, T, ["bbm", "bbl"])
    return m["bbm"], m["bbl"]
