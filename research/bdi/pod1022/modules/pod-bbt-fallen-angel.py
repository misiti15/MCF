"""pod-bbt-fallen-angel - Fallen Angel: gap-up stock loses VWAP, double-bottoms below it, then turns back up (LONG).
Config DB (double bottom + VWAP reclaim).

Source: Bear Bull Traders (Andrew Aziz) course deck 'Session 4' (2018), BBT TradeBook, forum thread 'Fallen Angel',
Aziz Oct 2025 newsletter. MERGED from pod-bbt-fallen-angel-db-vwap-long and pod-bbt-fallen-angel.
URL: https://bearbulltraders.com/wp-content/uploads/2018/01/Session-4.pdf

VARIANT of CWT08 good-news gap dip buy (cwt-a-a9, failed: buys at 25-40% of the gap), R02 VWAP reclaim (failed) and
bdi-reddit-vwap-double-bottom (idea: W at VWAP). Stated change: the gap-up stock must first LOSE VWAP and build a base /
double bottom BELOW VWAP without filling the gap.

Rules (plain English), every value from bars up to and including the decision bar i:
  1. gap >= +2.5% (pre-declared: the middle of the source's 2-3% range) and rvol by 10:00 >= 1.5. The frame has no
     raw volume, so rvol = mean volumeRatio of the 09:50, 09:55 and 10:00 bars (stated proxy).
  2. >= 3 closes below session VWAP on bars after 09:50 (09:55 on), and the low of day still above the prior close
     (the gap is not filled; prior close = open / (1 + gap), open = close / (1 + fromOpen)).
  3. Config DB: two swing lows 3-15 bars apart, both below VWAP, within 0.15 x daily ATR of each other, the second
     on a lower volumeRatio. A swing low (low <= the previous low and < the next low) is known only one bar after it.
     A later low below the double-bottom low cancels it.
     (Config B, separate file: the last 3 bars - pre-declared middle of 2-4 - sit in a range <= 0.15 x daily ATR,
     all highs below VWAP.)
  4. Trigger DB: the first close above VWAP (previous close at or below it) after the second low is confirmed, with
     volumeRatio >= 1.2. (B: a bar closing above the prior close with volumeRatio >= 2.5 and above the base high.)
  5. spy_fo > 0.
  Entry: trigger close, 10:00-12:30. Stop (GEOM S): double-bottom low - 0.03 x daily ATR (pre-declared middle of
  0.02-0.05). Target: the nearer of the high of day and entry + 2R; skip if the HOD is < 1R away. Flat 15:55.
  Costs in (scorer).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1230)
CONFIG = "DB"
CONTEXT = ["spy_fo"]
LAYERS = ["gap >= 2.5%, mean volumeRatio 09:50-10:00 >= 1.5", ">= 3 closes below VWAP, LOD above prior close",
          "config DB: double bottom below VWAP (3-15 bars, within 0.15 ATR, lower volume on the 2nd)",
          "trigger: VWAP reclaim close with volumeRatio >= 1.2", "spy_fo > 0",
          "stop base low - 0.03 ATR, target min(HOD, 2R), skip HOD < 1R", "10:00-12:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, hod, lod, vw, pc, gap, vr, spy, atr, cfg, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if tod[i0] != 950 or i1 - i0 < 4:
            continue
        if not (gap[i0] >= 2.5):
            continue
        rv = 0.0
        nr = 0
        for k in range(i0, i1):
            if tod[k] > 1000:
                break
            rv += vr[k]
            nr += 1
        if nr < 3 or rv / nr < 1.5:
            continue
        below = 0
        sw = np.full(64, -1, np.int64)   # confirmed swing-low bars (below VWAP)
        ns = 0
        dbl = np.nan                      # armed double-bottom low
        armed_at = -1
        for i in range(i0, i1):
            if i > i0 and c[i] < vw[i]:
                below += 1
            # confirm a swing low at i-1
            if cfg == 0 and i - 2 >= i0:
                j = i - 1
                if l[j] <= l[j - 1] and l[j] < l[i] and l[j] < vw[j]:
                    for q in range(ns):
                        k1 = sw[q]
                        if 3 <= j - k1 <= 15 and abs(l[j] - l[k1]) <= 0.15 * atr[i] and vr[j] < vr[k1]:
                            lo = min(l[j], l[k1])
                            dbl = lo
                            armed_at = i
                    if ns < 64:
                        sw[ns] = j
                        ns += 1
            if dbl == dbl and l[i] < dbl:
                dbl = np.nan
                armed_at = -1
            if tod[i] < w0 or tod[i] > w1 or i == i0:
                continue
            if below < 3 or not (lod[i] > pc[i]) or not (spy[i] > 0):
                continue
            a = atr[i]
            if cfg == 0:
                if not (dbl == dbl and armed_at >= 0 and i >= armed_at):
                    continue
                if not (c[i] > vw[i] and c[i - 1] <= vw[i - 1] and vr[i] >= 1.2):
                    continue
                base_lo = dbl
            else:
                nb = 3
                if i - nb < i0 + 1:
                    continue
                bh = -1e18
                bl = 1e18
                ok = True
                for k in range(i - nb, i):
                    bh = max(bh, h[k])
                    bl = min(bl, l[k])
                    if not (h[k] < vw[k]):
                        ok = False
                if not ok or bh - bl > 0.15 * a:
                    continue
                if not (c[i] > c[i - 1] and vr[i] >= 2.5 and c[i] > bh):
                    continue
                base_lo = bl
            sp = base_lo - 0.03 * a
            R = c[i] - sp
            if not (R > 0):
                continue
            H = hod[i]
            if H - c[i] < R:
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = min(H, c[i] + 2.0 * R)
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + f("dist_hod_atr") * atr
        lod = c - f("dist_lod_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
        op = c / (1 + f("fromOpen") / 100)
        pc = op / (1 + f("gap") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, hod, lod, vw, pc, f("gap"), f("volumeRatio"),
                   f("spy_fo"), atr, 0 if CONFIG == "DB" else 1, WINDOW[0], WINDOW[1])


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
