"""pod-bbt-market-vwap-test-rs-hold-long - Relative-strength leader bought when QQQ pulls back to its VWAP on an up
day (LONG).

Source: Bear Bull Traders / Andrew Aziz, 'trade with the market' and relative-strength stock selection (how to day
trade with SPY context; BBT YouTube). Not re-fetched this round.
URL: https://www.youtube.com/@BearBullTraders

VARIANT of pod-smb-market-flush-holder-long. Stated changes: the market event is an orderly pullback to QQQ's VWAP on
an UP day (not a flush to a new session low with breadth <= 0.35); the stock must stay above its own VWAP and keep
EMA9 > EMA21 through the dip; long only on up days.

Rules (plain English):
  1. Up day: spy_fo >= +0.2% and breadth >= 0.5 on this bar.
  2. Market VWAP test: on one of the last 3 bars (this bar and the 2 before) qqq_vwap <= +0.05%, and before that
     touch qqq_vwap was >= +0.25% on some earlier bar today (a touch from above); on this bar qqq_vwap is above the
     prior bar's and > -0.10%.
  3. Stock relative strength: fromOpen - spy_fo >= +1.0 pp; close above session VWAP on every one of the last 12 bars
     (this bar included); emaDiff > 0.
  4. This bar: close > prior close, and its low held above the stock's session VWAP.
  Entry: that close, bar close 10:30-14:30; only the top 3 symbols per (date, bar) by rule-3 relative strength.
  Exits, both declared before scoring: GEOM t1s1 (R = 0.25 x atr_d) in this file; the '-S' file uses the same mask
  with stop = session VWAP - 0.05 x atr_d and target = HOD (needs HOD above the entry), flat 15:55.
Frame note: 'earlier today' starts at the 09:50 bar; the top-3 ranking is cross-sectional (a scanner-level rank live).
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "t1s1"
WINDOW = (1030, 1430)
CONTEXT = ["spy_fo", "breadth", "qqq_vwap"]
TOPN = 3
LAYERS = ["spy_fo >= 0.2, breadth >= 0.5", "qqq_vwap touched <= 0.05 in last 3 bars after >= 0.25, now rising > -0.10",
          "fromOpen - spy_fo >= 1.0, above VWAP 12 bars, emaDiff > 0", "close up, bar low above VWAP",
          "top 3 per bar by RS", "10:30-14:30"]

import numba
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _base(df):
    k = _key(df)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=df["tod"].to_numpy(np.int64), c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    return b


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


@numba.njit(cache=False)
def _kern(b, e, tod, c, l, vw, q, spy, brd, fo, ed, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0, i1):
            if tod[i] < w0 or tod[i] > w1 or i - i0 < 12:
                continue
            if not (spy[i] >= 0.2 and brd[i] >= 0.5):
                continue
            if not (q[i] > q[i - 1] and q[i] > -0.10):
                continue
            touch = -1
            for t in range(i - 2, i + 1):
                if q[t] <= 0.05:
                    touch = t
                    break
            if touch < 0:
                continue
            hi = -1e18
            for t in range(i0, touch):
                if q[t] == q[t]:
                    hi = max(hi, q[t])
            if not (hi >= 0.25):
                continue
            if not (fo[i] - spy[i] >= 1.0 and ed[i] > 0):
                continue
            ok = True
            for t in range(i - 11, i + 1):
                if not (c[t] > vw[t]):
                    ok = False
                    break
            if not ok or not (c[i] > c[i - 1] and l[i] > vw[i]):
                continue
            m[i] = True
    return m


def _mask_core(df):
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "qqq_vwap" not in df or "spy_fo" not in df or "breadth" not in df:
        return z, None
    b = _base(df)
    bb, ee = _segments(b["k"])
    fo = _f(df, "fromOpen")
    spy = _f(df, "spy_fo")
    m = _kern(bb, ee, b["tod"], b["c"], b["l"], b["vwap"], _f(df, "qqq_vwap"), spy, _f(df, "breadth"), fo,
              _f(df, "emaDiff"), WINDOW[0], WINDOW[1])
    if m.any():
        idx = np.flatnonzero(m)
        t = pd.DataFrame({"d": df["date"].astype(str).to_numpy()[idx], "tod": b["tod"][idx], "rs": (fo - spy)[idx]})
        rk = t.groupby(["d", "tod"])["rs"].rank(ascending=False, method="first").to_numpy()
        m[idx[rk > TOPN]] = False
    return np.asarray(m, dtype=bool), b


def mask(df) -> np.ndarray:
    return _mask_core(df)[0]
