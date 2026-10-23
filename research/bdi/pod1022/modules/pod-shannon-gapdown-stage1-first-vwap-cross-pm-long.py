"""pod-shannon-gapdown-stage1-first-vwap-cross-pm-long - Gap-down stock bases all morning under VWAP: buy its first
VWAP cross after noon (stage 1 to stage 2) (LONG).

Source: Brian Shannon / Alpha Trends - 'Technical Analysis Using Multiple Timeframes' (stage analysis applied
intraday: no buying below a declining VWAP; buy the first move above a flattening VWAP after a base) and 'Maximum
Trading Gains with Anchored VWAP' (2023). Not re-fetched in round 2.
URL: https://alphatrends.net

VARIANT of pod-unger-daydrop-vwap-reclaim-etf (ETFs only, 10:00-12:00, D-1 close-location filter) and
pod-bbt-fallen-angel (gap-UP names that base under VWAP). Stated change: single stocks that gap DOWN, a full-morning
base, and only the first VWAP cross after 12:00.

Rules (plain English), only bars up to and including the decision bar i of the same symbol-day:
  1. gap <= -1.0%.
  2. The day's low was set before 11:00: the running low of day on every bar closing 11:00 or later (up to i) equals
     the running low at the 10:55 bar; and dist_lod_atr >= 0.25 at entry.
  3. Stage-1 base: close below session VWAP (vwapDistPct < 0) on every bar closing 10:30..12:00.
  4. Trigger (bar close 12:05-14:30): the FIRST bar after 12:00 with vwapDistPct > 0 and the previous bar <= 0. It
     qualifies only if sma20_slope_pct >= 0 and volumeRatio >= 1.0; otherwise no trade that day (later crosses are
     not taken).
  5. |spy_fo| <= 0.6.
  Entry: trigger close. Stop (GEOM S): lowest low of the last 6 bars (i-5..i) - 0.05 x daily ATR; skip when the risk
  is > 0.5 x daily ATR. Target: the nearer of today's open and entry + 2R (skip when the open is not above entry).
  Flat 15:55. Costs in (scorer).
No tweak made.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1205, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["gap <= -1%", "LOD set before 11:00, dist_lod_atr >= 0.25", "below VWAP on every bar 10:30-12:00",
          "first VWAP cross after 12:00 with sma20_slope_pct >= 0, volumeRatio >= 1", "|spy_fo| <= 0.6",
          "stop 6-bar low - 0.05 ATR (<= 0.5 ATR), target min(open, 2R)", "12:05-14:30 ET"]


@numba.njit(cache=False)
def _kernel(b, e, tod, c, l, lod, dlod, vd, op, gap, slope, vr, spy, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if tod[i0] != 950 or i1 - i0 < 10:
            continue
        if not (gap[i0] <= -1.0):
            continue
        lod_ref = np.nan
        base_ok = True
        seen_base = False
        lod_ok = True
        for i in range(i0, i1):
            if tod[i] <= 1055:
                lod_ref = lod[i]
            else:
                if not (lod[i] >= lod_ref - 1e-3 * atr[i]):
                    lod_ok = False
            if 1030 <= tod[i] <= 1200:
                seen_base = True
                if not (vd[i] < 0):
                    base_ok = False
            if tod[i] <= 1200 or i == i0:
                continue
            if not (base_ok and seen_base and lod_ok):
                break
            if not (vd[i] > 0 and vd[i - 1] <= 0):
                continue
            # first VWAP cross after 12:00: decide here, then stop looking
            if tod[i] >= w0 and tod[i] <= w1 and slope[i] >= 0 and vr[i] >= 1.0 and abs(spy[i]) <= 0.6 \
                    and dlod[i] >= 0.25:
                a = atr[i]
                lo = 1e18
                for k in range(max(i0, i - 5), i + 1):
                    lo = min(lo, l[k])
                sp = lo - 0.05 * a
                R = c[i] - sp
                if R > 0 and R <= 0.5 * a and op[i] > c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = min(op[i], c[i] + 2.0 * R)
            break
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - f("dist_lod_atr") * atr
        op = c / (1 + f("fromOpen") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("low"), lod, f("dist_lod_atr"), f("vwapDistPct"), op,
                   f("gap"), f("sma20_slope_pct"), f("volumeRatio"), f("spy_fo"), atr, WINDOW[0], WINDOW[1])


_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


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
