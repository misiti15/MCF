"""pod-cwt2-glick-beaten-down-base-vwap-break-long - Beaten-down multi-week base: intraday break of the base high
above VWAP (LONG).

Source: Chat With Traders ep 94, Kenny Glick; record ep094 'Beaten-down base breakout (exhaustion bottom range) with
VWAP confirmation'.
URL: https://chatwithtraders.com

VARIANT of cwt-c-c2 tight base breakout (daily, failed) and pod-traderlion-orh60-leader-long (LEADERS). Stated change:
the opposite universe (LAGGARDS: down >= 40% from the 1-year high, near 52-week lows, a base whose low was tested
repeatedly) and an INTRADAY entry gated by VWAP before 11:30. Not pod-bbt-fallen-angel (a gap-up that loses VWAP).

Rules (plain English). Daily values come only from COMPLETED days (research/history2y daily table, day D-1 and before):
  1. Daily: close(D-1) <= 0.6 x the 1-year high; the 20-day low is within 15% of the 1-year low; base = the last 20
     completed days with (max high - min low) <= 20% of the D-1 close; the base low was touched (a daily low within 2%
     of it) on >= 3 separate days.
     Data note (stated approximation): the daily table starts 2024-10-01 and the locked block (2024-11..2025-02) is
     absent, so the "1-year" high/low is the max/min over the completed days of the last 365 calendar days that are
     available, and at least 120 such days are required (so this setup only trades from about 2025-08 on).
  2. Today: close above the session VWAP (vwapDistPct > 0) and above the base midpoint at the entry bar.
  3. Trigger: the FIRST 5-minute close above the 20-day base high (the previous bar closed at or below it, no earlier
     frame close above it, and today's open was not above it), with volumeRatio >= 1.5.
  4. spy_fo >= -0.3.
  Entry: that close, bar close 09:50-11:30. Stop (GEOM S): max(base midpoint, today's LOD) - 0.05 x atr_d.
  Target: the most recent daily swing low (low below the 2 days either side, all completed) within the last 60
  completed days that is above the entry, if it is >= 1.5R away; otherwise 2R. Flat 15:55. Costs in (scorer).
  No tweak used (all thresholds as written in the idea).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1130)
CONTEXT = ["spy_fo"]
LAYERS = ["daily: close <= 0.6 x 1y high, 20d low within 15% of 1y low, 20d range <= 20% of close, base low touched >= 3 days",
          "close > VWAP and > base midpoint", "first 5m close above the 20d base high, volumeRatio >= 1.5",
          "spy_fo >= -0.3", "09:50-11:30 ET",
          "stop max(base mid, LOD) - 0.05 ATR; target prior daily swing low above if >= 1.5R else 2R"]

_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}
_CACHE = {}


def _lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    return lib


def _daily():
    if "d" in _CACHE:
        return _CACHE["d"]
    d = _lib().daily()[["symbol", "date", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    d["dt"] = pd.to_datetime(d["date"])
    out = []
    swings = {}
    for sym, g in d.groupby("symbol", sort=False):
        g = g.set_index("dt")
        hi = g["high"].rolling("365D").max()
        lo = g["low"].rolling("365D").min()
        cnt = g["close"].rolling("365D").count()
        h20 = g["high"].rolling(20).max()
        l20 = g["low"].rolling(20).min()
        dts = g.index.to_series()
        span20 = (dts - dts.shift(19)).dt.days
        lows = g["low"].to_numpy(float)
        l20a = l20.to_numpy(float)
        touch = np.full(len(g), np.nan)
        for k in range(19, len(g)):
            if np.isfinite(l20a[k]):
                touch[k] = np.sum(lows[k - 19:k + 1] <= l20a[k] * 1.02)
        nd = dts.shift(-1)
        o = pd.DataFrame({"symbol": sym, "date": nd.to_numpy(), "pc": g["close"].to_numpy(float),
                          "hi1y": hi.to_numpy(float), "lo1y": lo.to_numpy(float), "n1y": cnt.to_numpy(float),
                          "bh": h20.to_numpy(float), "bl": l20a, "span20": span20.to_numpy(float), "touch": touch,
                          "gapd": (nd - dts).dt.days.to_numpy(float)})
        o["k"] = np.arange(len(g))
        out.append(o)
        # daily swing lows: low_j below the lows of j-2, j-1, j+1, j+2 (confirmed only once j+2 is completed)
        sw = np.zeros(len(g), bool)
        for j in range(2, len(g) - 2):
            if lows[j] < lows[j - 1] and lows[j] < lows[j - 2] and lows[j] < lows[j + 1] and lows[j] < lows[j + 2]:
                sw[j] = True
        swings[sym] = (lows, sw)
    o = pd.concat(out, ignore_index=True)
    o = o[(o["gapd"] <= 5) & o["date"].notna()].copy()
    o["date"] = pd.to_datetime(o["date"]).dt.date
    with np.errstate(invalid="ignore"):
        gate = (o["n1y"] >= 120) & (o["pc"] <= 0.6 * o["hi1y"]) & (o["bl"] <= 1.15 * o["lo1y"]) \
            & ((o["bh"] - o["bl"]) <= 0.20 * o["pc"]) & (o["touch"] >= 3) & (o["span20"] <= 36)
    o = o[gate][["symbol", "date", "bh", "bl", "k"]].reset_index(drop=True)
    _CACHE["d"] = o
    _CACHE["sw"] = swings
    return o


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, fo, vd, vr, spy, lod, atr, bh, bl, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        H = bh[i0]
        L = bl[i0]
        if not (H == H and L == L):
            continue
        op = c[i0] / (1.0 + fo[i0] / 100.0)
        if op > H:
            continue
        mid = 0.5 * (H + L)
        if c[i0] > H:
            continue
        for i in range(i0 + 1, i1):
            if c[i] > H:
                if c[i - 1] <= H and tod[i] >= w0 and tod[i] <= w1 and vr[i] >= 1.5 and vd[i] > 0 \
                        and c[i] > mid and spy[i] >= -0.3:
                    sp = max(mid, lod[i]) - 0.05 * atr[i]
                    if sp < c[i]:
                        m[i] = True
                        stop[i] = sp
                break
    return m, stop


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    dg = key.merge(_daily(), on=["symbol", "date"], how="left")
    with np.errstate(invalid="ignore"):
        lod = c - f("dist_lod_atr") * atr
    b, e = _segments(df)
    m, stop = _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("fromOpen"), f("vwapDistPct"), f("volumeRatio"),
                      f("spy_fo"), lod, atr, dg["bh"].to_numpy(float), dg["bl"].to_numpy(float), WINDOW[0], WINDOW[1])
    tgt = np.full(n, np.nan)
    sw = _CACHE["sw"]
    sym = key["symbol"].to_numpy()
    kk = dg["k"].to_numpy(float)
    for i in np.flatnonzero(m):
        ent = c[i]
        R = ent - stop[i]
        lows, flag = sw[sym[i]]
        kd = int(kk[i])                    # index of day D-1 in the symbol's daily rows
        lvl = np.nan
        for j in range(kd - 2, max(-1, kd - 61), -1):     # swing at j is confirmed by j+2 <= D-1
            if flag[j] and lows[j] > ent:
                lvl = lows[j]
                break
        tgt[i] = lvl if (lvl == lvl and lvl - ent >= 1.5 * R) else ent + 2.0 * R
    return m, stop, tgt


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
