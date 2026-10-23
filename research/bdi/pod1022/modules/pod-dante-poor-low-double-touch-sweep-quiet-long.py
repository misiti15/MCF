"""pod-dante-poor-low-double-touch-sweep-quiet-long - A poor (flat, double-touched) session low is swept and reclaimed
on a quiet day (LONG). Structural stop under the sweep, target the session midpoint or 1R, whichever is nearer.

Source: Trader Dante 'Auction Market Theory & Market Profile Explained' (poor highs / lows = unfinished business, so
stops cluster there) + Bookmap 'Running the stops: how it happens and how to trade the aftermath'. Not re-fetched
this round.
URL: https://bookmap.com/blog/running-the-stops-how-it-happens-and-how-to-trade-the-aftermath

VARIANT of 'Liquidity sweep (turtle soup) of OR30 high/low or 1-hour HOD/LOD' and of CWT14-failbrk-orl. Stated
changes: the level must be a POOR low (>= 2 separate 5-min touches within 0.03 x ATR14d, >= 30 min apart, no long
lower wick on any touch), and the trade is allowed only on quiet days.

Rules (plain English, LONG, entry 11:00-14:45):
  1. P = the session low before the sweep bar (running low of day). The visible 5-min bars whose low is within
     0.03 x atr_d of P are the touches: >= 2 of them, the first and last >= 6 bars (30 min) apart, and no touch bar
     has a lower wick > 40% of its range.
  2. Quiet day (at the entry bar): the session range so far (HOD - LOD) <= 0.8 x this symbol's average session range
     at the same time of day over the prior 20 sessions (>= 10 needed; prior sessions only, the previous open month
     is read for the look-back, never the locked block), and |SPY from its open| <= 0.4%.
  3. Sweep bar: its low is 0.02-0.25 x ATR5m below P and it closes back above P; or it closes at/below P and the next
     bar closes above P without extending the sweep past 0.25 x ATR5m.
  4. Sweep-bar volumeRatio (volume / 20-bar average) >= 1.3.
  Entry: the reclaim close. Stop (GEOM S): sweep low - 0.05 x ATR5m. Target: the session midpoint (HOD + LOD) / 2, or
  1R if that is nearer. Flat 15:55 (the source's time stop).
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1445)
CONTEXT = ["spy_fo"]
LAYERS = [">= 2 tail-less touches of the session low within 0.03 ATR, >= 30 min apart",
          "range so far <= 0.8x the 20-session time-of-day norm, |spy_fo| <= 0.4", "sweep 0.02-0.25 ATR5m below and reclaim",
          "sweep volumeRatio >= 1.3", "stop sweep low - 0.05 ATR5m, target min(session mid, 1R)"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segs(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _base(df):
    """Point-in-time levels per row (all from the bar itself or earlier / completed prior days)."""
    c, atr = _f(df, "close"), _f(df, "atr_d")
    b = dict(c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr, tod=df["tod"].to_numpy(np.int64))
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") / 100 * c               # 5m ATR(14), $
    return b


def _prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
    return f"{y:04d}-{mo:02d}"


def _open_month(m):
    """True only for an OPEN month (never the rule-19 locked block)."""
    L = _lib()
    return m not in L.LOCKED_MONTHS and m in set(L.months())


def mask(df) -> np.ndarray:
    n = len(df)
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])


@numba.njit(cache=False)
def _roll_prior(g, x, nwin, nmin):
    """Mean of x over the previous nwin rows of the same group g (rows sorted by group, then date)."""
    n = len(x)
    out = np.full(n, np.nan)
    i = 0
    while i < n:
        j = i
        while j < n and g[j] == g[i]:
            j += 1
        for q in range(i, j):
            s = 0.0
            cnt = 0
            for p in range(max(i, q - nwin), q):
                if np.isfinite(x[p]):
                    s += x[p]
                    cnt += 1
            if cnt >= nmin:
                out[q] = s / cnt
        i = j
    return out


def _range_norm(df, b):
    """Per row: mean (HOD - LOD) at the same tod over the symbol's prior 20 sessions (prior open month included)."""
    n = len(df)
    sel = (b["tod"] >= 1100) & (b["tod"] <= 1445)
    cur = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[sel], "date": df["date"].astype(str).to_numpy()[sel],
                        "tod": b["tod"][sel], "rng": (b["hod"] - b["lod"])[sel], "row": np.flatnonzero(sel)})
    parts = []
    for mo in sorted(set(d[:7] for d in cur["date"].unique())):
        pm = _prev_month(mo)
        if not _open_month(pm):
            continue
        p = _lib().load_month(pm, columns=["symbol", "date", "tod", "close", "atr_d", "dist_hod_atr", "dist_lod_atr"])
        p = p[(p["tod"] >= 1100) & (p["tod"] <= 1445)]
        parts.append(pd.DataFrame({"symbol": p["symbol"].astype(str).to_numpy(), "date": p["date"].astype(str).to_numpy(),
                                   "tod": p["tod"].to_numpy(np.int64),
                                   "rng": ((p["dist_hod_atr"] + p["dist_lod_atr"]) * p["atr_d"]).to_numpy(float),
                                   "row": -1}))
    t = pd.concat(parts + [cur], ignore_index=True)
    t = t.drop_duplicates(["symbol", "date", "tod", "row"])
    t = t.sort_values(["symbol", "tod", "date"], kind="mergesort").reset_index(drop=True)
    g = pd.factorize(t["symbol"] + "|" + t["tod"].astype(str))[0]
    t["norm"] = _roll_prior(g.astype(np.int64), t["rng"].to_numpy(float), 20, 10)
    out = np.full(n, np.nan)
    r = t["row"].to_numpy()
    ok = r >= 0
    out[r[ok]] = t["norm"].to_numpy(float)[ok]
    return out


@numba.njit(cache=False)
def _kernel(bs, be, tod, c, h, l, lod, hod, atr5, atr, lw, vr, spy, norm):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(bs)):
        i0, i1 = bs[s], be[s]
        for i in range(i0 + 7, i1):
            if tod[i] < 1055 or tod[i] > 1445:
                continue
            a5 = atr5[i]
            a = atr[i]
            if not (a5 > 0 and a > 0):
                continue
            P = lod[i - 1]
            if not (l[i] <= P - 0.02 * a5 and l[i] >= P - 0.25 * a5):                    # (3) sweep depth
                continue
            if not (vr[i] >= 1.3):                                                       # (4)
                continue
            first = -1
            last = -1
            cnt = 0
            okw = True
            for k in range(i0, i):
                if l[k] <= P + 0.03 * a:
                    cnt += 1
                    if first < 0:
                        first = k
                    last = k
                    if lw[k] > 0.4:
                        okw = False
            if not (cnt >= 2 and okw and last - first >= 6):                             # (1) poor low
                continue
            e = -1
            swl = l[i]
            if c[i] > P:
                e = i
            elif i + 1 < i1 and c[i + 1] > P and l[i + 1] >= P - 0.25 * a5:
                e = i + 1
                swl = min(l[i], l[i + 1])
            if e < 0 or tod[e] < 1100 or tod[e] > 1445:
                continue
            if not (np.isfinite(norm[e]) and hod[e] - lod[e] <= 0.8 * norm[e]):         # (2) quiet day
                continue
            if not (np.isfinite(spy[e]) and abs(spy[e]) <= 0.4):
                continue
            sp = swl - 0.05 * a5
            R = c[e] - sp
            if R <= 0:
                continue
            tp = min((hod[e] + lod[e]) / 2.0, c[e] + R)
            if tp > c[e] and not m[e]:
                m[e] = True
                stop[e] = sp
                tgt[e] = tp
    return m, stop, tgt


def _compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n or "spy_fo" not in df:
        return z
    b = _base(df)
    norm = _range_norm(df, b)
    bs, be = _segs(_key(df))
    return _kernel(bs, be, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["hod"], b["atr5"], b["atr"],
                   _f(df, "lower_wick"), _f(df, "volumeRatio"), _f(df, "spy_fo"), norm)
