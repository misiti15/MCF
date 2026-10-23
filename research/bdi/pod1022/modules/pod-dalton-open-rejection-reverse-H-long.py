"""pod-dalton-open-rejection-reverse-H-long - Open-rejection-reverse: a failed early drive closes back through the
opening price (LONG, stop config H).

Source: J. Dalton open types (LuxAlgo; MarketCalls 'Market Profile open type and confidence'); FTMO 'Market Profile:
Types of Opens'; Axia Futures Volume Profile course notes. Merged from pod-dalton-open-rejection-reverse-short and
pod-of-open-rejection-reverse.
URL: https://www.marketcalls.in/market-profile/market-profile-open-type-and-confidence.html

VARIANT of R06 red-to-green (level = prior close, failed) and wi-red-to-green (idea). Stated change: the level is
today's OPEN and a minimum failed opening drive is required first (auction rejection), morning only.
Files: pod-dalton-open-rejection-reverse-{M,H}-{short,long}; this file = STOPCFG and SIDE below. Two stop configs
are the source's own (pre-declared, both reported): M = midpoint of open and HOD, H = HOD + 0.05 x atr_d.

Values: open = close / (1 + fromOpen%); HOD / LOD so far from dist_hod_atr / dist_lod_atr (they include the
09:30-09:45 bars); VWAP from vwapDistPct; PDL = close - dist_pdl_atr x atr_d (prior completed day).
Rules (plain English; short shown, long = exact mirror: a down drive that fails back above the open and VWAP,
flow3 > 0 or volumeRatio >= 1.2, spy_fo >= -0.3%, target PDH / HOD + 0.25 ATR):
  1. |gap| <= 1.0%.
  2. Failed up-drive: HOD - open >= 0.4 x atr_d with no new HOD after the 10:30 bar (the HOD at this bar equals the
     HOD as of 10:30 once past 10:30), or fromOpen >= +0.4 x atr_d / close (in %) at the 09:50 bar.
  3. This bar is the first frame close with fromOpen < 0 today (09:50-11:30).
  4. close < VWAP, and flow3 < 0 or volumeRatio >= 1.2.
  5. spy_fo <= +0.3%.
  Entry: that close. Stop (GEOM S): M = (open + HOD) / 2, or H = HOD + 0.05 x atr_d. Target: the nearer of PDL (when
  below the entry) and LOD - 0.25 x atr_d. Flat 15:55. Costs per config/default.yaml (scorer).
Pre-declared choices (source ranges, set once, no tuning on valid): HOD cut-off 10:30 (range 10:05-10:30), spy_fo
cap 0.3% (range 0.2-0.3, the value the source gives for the long mirror). The 't1s1 fallback' is never needed (the
LOD - 0.25 ATR target always exists).
Educational only - not financial advice."""
SIDE = "long"
STOPCFG = "H"
GEOM = "S"
WINDOW = (950, 1130)
CONTEXT = ["spy_fo"]
LAYERS = ["|gap| <= 1%", "early drive >= 0.4 ATR beyond the open, extreme set by 10:30",
          "first close back through the open", "close vs VWAP, flow3 or volumeRatio >= 1.2", "spy_fo within 0.3%",
          "stop M (mid open-extreme) or H (extreme + 0.05 ATR), target PDL/PDH or LOD/HOD +- 0.25 ATR",
          "09:50-11:30 ET"]

import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _gcum(x, k):
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def mask(df) -> np.ndarray:
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return np.zeros(len(df), dtype=bool)
    k = _key(df)
    st = _start(k)
    g = np.cumsum(st) - 1
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        fo = _f(df, "fromOpen")
        op = (c / (1 + fo / 100))[st][g]
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        vd = _f(df, "vwapDistPct")
        first950 = np.where(tod == 950, fo, np.nan)[st][g]       # fromOpen at the 09:50 bar (NaN if missing)
        if SIDE == "short":
            ext, sg = hod, 1.0
        else:
            ext, sg = lod, -1.0
        cut = pd.Series(np.where(tod <= 1030, ext, np.nan)).groupby(g).ffill().to_numpy(float)
        drive = (sg * (ext - op) >= 0.4 * atr) & ((tod <= 1030) | (sg * (ext - cut) <= 1e-9))
        drive |= sg * first950 >= 0.4 * atr / c * 100
        x = sg * fo < 0
        m = x & ((_gcum(x, k) - x) == 0) & drive
        m &= np.abs(_f(df, "gap")) <= 1.0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        f3, vr, spy = _f(df, "flow3"), _f(df, "volumeRatio"), _f(df, "spy_fo")
        if SIDE == "short":
            m &= (vd < 0) & ((f3 < 0) | (vr >= 1.2)) & (spy <= 0.3)
            stop = (op + hod) / 2 if STOPCFG == "M" else hod + 0.05 * atr
            pdl = c - _f(df, "dist_pdl_atr") * atr
            tgt = np.maximum(np.where(pdl < c, pdl, -np.inf), lod - 0.25 * atr)
        else:
            m &= (vd > 0) & ((f3 > 0) | (vr >= 1.2)) & (spy >= -0.3)
            stop = (op + lod) / 2 if STOPCFG == "M" else lod - 0.05 * atr
            pdh = c + _f(df, "dist_pdh_atr") * atr
            tgt = np.minimum(np.where(pdh > c, pdh, np.inf), hod + 0.25 * atr)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)
