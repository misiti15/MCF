"""pod-dalton-half-gap-hold-long - Gap-up 'half-gap' hold: the first-hour pullback holds above the 50% gap level,
then continuation (LONG). Structural stop, target the morning high. The GEOM holdtr check is
pod-dalton-half-gap-hold-long-holdtr.py (same mask).

Source: Axia Futures / J. Dalton 'Mind Over Markets' gap rules (half-gap / gap-fill as the line between a gap that
holds and a gap that fails); Trader Dante gap commentary. Not re-fetched this round.
URL: https://nexusfi.com/articles/trading/Opening-Types

VARIANT of gap_continuation_in_play (research/setups_research.json). Stated change: the gap counts as valid only if
price retests and holds the HALF-GAP level, and entry is the reclaim after that test, not the break of the opening
range.

Rules (plain English, LONG, 5-min bars):
  1. Gap = open - prior close between +0.4 and +1.5 x ATR14d (atr_d), and the open is above the PDH or within
     0.2 x atr_d of it.
  2. Half-gap H = prior close + 0.5 x gap. The session low (running low of day, includes 09:30-09:45; frozen after the
     10:30 bar - no new low after 10:30) comes within 0.15 x atr_d of H, and no visible 5-min bar closes below H from
     09:50 up to the entry bar.
  3. Entry 10:00-11:30: the first 5-min close above session VWAP and above the high of the lowest visible pullback
     bar (lowest low among the 09:50..10:30 bars before the entry bar).
  4. Pullback volume: mean volumeRatio of the visible bars 09:50 .. the lowest pullback bar <= 1.0.
  Stop (GEOM S): min(session low, H) - 0.05 x ATR5m. Target: the morning high (HOD so far at entry); skip the trade
  if the HOD is less than 1R above the entry. Flat 15:55. holdtr alternative in the -holdtr file.
Harness approximations (declared, no tuning): the frame starts at the 09:50 bar and has no raw volume - the
09:35-09:45 closes cannot be checked (only the running low covers them), and rule 4's 'pullback volume <= 0.8x the
09:30-09:45 average' is proxied by the pullback bars' mean volumeRatio (bar volume / its 20-bar average, which spans
the opening bars) <= 1.0. 'Within 0.15 x atr_d of H' is read as |LOD - H| <= 0.15 x atr_d.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1130)
LAYERS = ["gap +0.4..+1.5 ATR14d, open >= PDH - 0.2 ATR", "LOD within 0.15 ATR of the half-gap H, no close below H",
          "first close above VWAP and the pullback-low bar's high, 10:00-11:30", "pullback mean volumeRatio <= 1.0",
          "stop min(LOD, H) - 0.05 ATR5m, target morning high (>= 1R)"]

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
def _kernel(bs, be, tod, c, h, l, lod, hod, vwap, atr5, atr, opn, pc, pdh, vr):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(bs)):
        i0, i1 = bs[s], be[s]
        a = atr[i0]
        if not (a > 0):
            continue
        g = opn[i0] - pc[i0]
        if not (g >= 0.4 * a and g <= 1.5 * a and opn[i0] >= pdh[i0] - 0.2 * a):          # (1)
            continue
        H = pc[i0] + 0.5 * g
        below = False
        kmin = -1
        lod1030 = np.nan
        for i in range(i0, i1):
            if c[i] < H:
                below = True
            if below:
                break
            if tod[i] == 1030 or (tod[i] > 1030 and not np.isfinite(lod1030)):
                lod1030 = lod[i - 1] if tod[i] > 1030 and i > i0 else lod[i]
            if tod[i] >= 1000 and tod[i] <= 1130 and kmin >= 0:
                ok = True
                L = lod[i]
                if tod[i] > 1030 and abs(L - lod1030) > 1e-6 * c[i]:
                    ok = False                                                          # new low after 10:30
                if ok and abs(L - H) > 0.15 * a:                                         # (2)
                    ok = False
                if ok:
                    mv = 0.0
                    for q in range(i0, kmin + 1):
                        mv += vr[q]
                    if mv / (kmin - i0 + 1) > 1.0:                                       # (4)
                        ok = False
                if ok and c[i] > vwap[i] and c[i] > h[kmin]:                             # (3)
                    sp = min(L, H) - 0.05 * atr5[i]
                    R = c[i] - sp
                    if R > 0 and hod[i] - c[i] >= R:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = hod[i]
                        break
            if tod[i] <= 1030 and (kmin < 0 or l[i] < l[kmin]):
                kmin = i
    return m, stop, tgt


def _compute(df):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    b = _base(df)
    bs, be = _segs(_key(df))
    return _kernel(bs, be, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["hod"], b["vwap"], b["atr5"], b["atr"],
                   b["opn"], b["pc"], b["pdh"], _f(df, "volumeRatio"))
