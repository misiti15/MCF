"""pod-cwt2-johansson-index-divergence-holder-long - Index divergence: buy the index that refuses to make a new low (LONG).

Source: Chat With Traders ep 262, Henrik Johansson & Patrick Petersson; record ep262 'Index divergence: short the
hesitant index'. URL: https://chatwithtraders.com

VARIANT (side flip, stated) of the guests' index-divergence short. Not ix-leadlag (failed: trades stocks after a
1/5-min index move), not bdi1013-splitgate (a short gate on QQQ-IWM from the open) and not longs1020 (STOCK longs with
relative strength against an index dip). Only index ETFs are traded, on an index-vs-index failure to confirm a low.

Rules (plain English). SYMBOLS = SPY, QQQ, IWM; every ordered pair (A, B), A != B, is checked (6 pairs, pooled; a
B symbol-day trades on the first pair that fires). Bars e..t are the 5-min bars from the event bar e to the trigger t.
  1. ETF A prints a new low of day in bar e = t - k (k = 0..3, e after 10:30): its low is below its prior low of day,
     and its new low of day is at least 0.3 x A's atr_d below A's 10:30 low of day.
  2. ETF B does NOT confirm: B's lowest low over bars e..t stays >= B's low of day before bar e + 0.10 x B's atr_d.
  3. A's new low fails: some A close in bars e..t is back above A's low of day before bar e.
  4. Trigger: B closes above its previous bar's high and B's flow3 > 0.
  Entry: long B at that close, bar close 11:00-15:00. Stop (GEOM S): B's low of day - 0.05 x B's atr_d.
  Target: B's session VWAP when it is >= 1R above the entry, else 1R; flat 15:55.
Configurations: 6 ordered pairs, pooled in this one file. Pre-declared choices: k counts from 0 (the new low and the
trigger may share a bar). No tweak used. No tuning on the valid period. Costs per config/default.yaml.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM"]
CONTEXT = []
LAYERS = ["ETF A new LOD >= 0.3 ATR below its 10:30 LOD (within 3 bars)",
          "ETF B low stays >= 0.10 ATR above its prior LOD", "A closes back above its prior LOD",
          "B closes above prior bar high, flow3 > 0", "stop B LOD - 0.05 ATR, target VWAP (>= 1R) else 1R",
          "11:00-15:00 ET"]

import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _sh(x, n):
    """Shift along the bar axis within each day (NaN-filled)."""
    p = np.full_like(x, np.nan)
    if n < x.shape[1]:
        p[:, n:] = x[:, :-n] if n > 0 else x
    return p


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n:
        return np.zeros(n, dtype=bool)
    sym = df["symbol"].astype(str).to_numpy()
    tod = df["tod"].to_numpy(np.int64)
    di, dates = pd.factorize(pd.Series(df["date"].astype(str).to_numpy()), sort=True)
    tods = np.unique(tod)
    ti = np.searchsorted(tods, tod)
    D, T = len(dates), len(tods)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - _f(df, "dist_lod_atr") * atr
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        W = {}
        for s in SYMBOLS:
            sel = sym == s
            W[s] = {}
            for nm, x in (("c", c), ("h", h), ("l", l), ("atr", atr), ("lod", lod), ("fl", _f(df, "flow3"))):
                a = np.full((D, T), np.nan)
                a[di[sel], ti[sel]] = x[sel]
                W[s][nm] = a
            # running low of day without float noise: the first frame row's LOD (covers 09:30-09:45), then the bar lows
            lw = W[s]["l"].copy()
            lw[:, 0] = np.fmin(W[s]["lod"][:, 0], lw[:, 0])
            W[s]["lod"] = np.fmin.accumulate(lw, axis=1)
        todm = np.broadcast_to(tods[None, :], (D, T))
        sigB = {s: np.zeros((D, T), bool) for s in SYMBOLS}
        for A in SYMBOLS:
            a = W[A]
            lod1030 = np.nanmax(np.where(todm == 1030, a["lod"], np.nan), axis=1)[:, None]
            plodA = _sh(a["lod"], 1)
            newlow = (a["l"] < plodA) & (a["lod"] <= lod1030 - 0.3 * a["atr"]) & (todm > 1030)
            for B in SYMBOLS:
                if B == A:
                    continue
                b = W[B]
                plodB = _sh(b["lod"], 1)
                trig = (b["c"] > _sh(b["h"], 1)) & (b["fl"] > 0)
                ok = np.zeros((D, T), bool)
                for kk in range(0, 4):
                    ev = _sh(newlow.astype(float), kk) == 1          # event at e = t - kk
                    pA = _sh(plodA, kk)                              # A's LOD before e
                    pB = _sh(plodB, kk) + 0.10 * b["atr"]            # B's LOD before e + 0.1 ATR
                    minlB = b["l"].copy()
                    maxcA = a["c"].copy()
                    for j in range(1, kk + 1):
                        minlB = np.fmin(minlB, _sh(b["l"], j))
                        maxcA = np.fmax(maxcA, _sh(a["c"], j))
                    ok |= ev & (minlB >= pB) & (maxcA > pA)
                sigB[B] |= ok & trig
        m = np.zeros(n, bool)
        for s in SYMBOLS:
            sel = np.flatnonzero(sym == s)
            m[sel] = sigB[s][di[sel], ti[sel]]
        lodr = np.full(n, np.nan)
        for s in SYMBOLS:
            sel = np.flatnonzero(sym == s)
            lodr[sel] = W[s]["lod"][di[sel], ti[sel]]
        stop = lodr - 0.05 * atr
        R = c - stop
        tgt = np.where(vwap - c >= R, vwap, c + R)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & np.isfinite(stop) & (R > 0)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)
