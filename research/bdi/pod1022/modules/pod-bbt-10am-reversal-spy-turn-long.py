"""pod-bbt-10am-reversal-spy-turn-long - 10 o'clock reversal: opening-hour selloff whose low holds after 10:00 while
SPY also turns (LONG).

Source: Bear Bull Traders YouTube / Andrew Aziz, discussion of the ~10:00 ET reversal of the opening move (the
opening amateur flow fades and the first-hour trend often reverses at 10:00-10:30). Not re-fetched this round.
URL: https://www.youtube.com/@BearBullTraders

VARIANT of pod-smb-backside-long-into-vwap and swarm1017-arena-am-long-gapdown-capitulation. Stated changes: the
setup is anchored to the clock (LOD set by 10:05 and never undercut afterwards), the index must make a confirming
turn at the same time, and entry is restricted to 10:10-10:45.

Rules (plain English):
  1. Weak open: fromOpen <= -1.0% at the 10:00 bar, OR gap <= -1% and the 10:00 close is below the open.
  2. The running LOD was set on a bar closing <= 10:05 (the LOD at this bar equals the LOD as of the 10:05 bar; a low
     from 09:30-09:45 counts), and no bar after 10:05 up to this bar has low < LOD + 0.02 x atr_d.
  3. SPY turn: spy_fo now > min(spy_fo over the 09:50-10:05 bars) + 0.15 pp, and spy_fo rose on this bar.
  4. This bar: close > max(high of the 2 prior bars); rsi5 >= 50 and rising, with rsi5 <= 30 on one of the 6 prior
     bars; flow3 > 0.
  5. Room: session VWAP - close >= 0.3 x atr_d.
  Entry: that close, bar close 10:10-10:45. Stop (GEOM S): LOD - 0.05 x atr_d. Target: session VWAP at entry, else
  flat 15:55.
Frame note: frames start at the 09:50 bar, so the SPY minimum is over 09:50-10:05 only (the 09:35-09:45 SPY bars are
not in the context). No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1010, 1045)
CONTEXT = ["spy_fo"]
LAYERS = ["fromOpen <= -1% at 10:00, or gap <= -1% and red at 10:00", "LOD set by 10:05, not retested within 0.02 ATR",
          "spy_fo > its 09:50-10:05 min + 0.15 and rising", "close > prior 2 highs, rsi5 >= 50 rising from <= 30, flow3 > 0",
          "VWAP >= 0.3 ATR above", "stop LOD - 0.05 ATR, target VWAP", "10:10-10:45"]

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
def _kern(b, e, tod, c, h, l, lod, vw, atr, fo, gap, spy, rsi5, fl3, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        fo10 = np.nan
        weak = False
        lod05 = np.nan
        smin = 1e18
        minlow_after = 1e18
        for i in range(i0, i1):
            if tod[i] == 1000:
                fo10 = fo[i]
                weak = (fo10 <= -1.0) or (gap[i] <= -1.0 and fo10 < 0)
            if tod[i] <= 1005:
                if spy[i] == spy[i]:
                    smin = min(smin, spy[i])
                if tod[i] == 1005:
                    lod05 = lod[i]
                continue
            minlow_after = min(minlow_after, l[i])
            if tod[i] < w0 or tod[i] > w1 or fo10 != fo10 or lod05 != lod05 or not weak:
                continue
            a = atr[i]
            L0 = lod05
            if lod[i] < L0 - 1e-9 * c[i] or minlow_after < L0 + 0.02 * a:
                continue
            if i - i0 < 6 or smin > 1e17:
                continue
            if not (spy[i] > smin + 0.15 and spy[i] > spy[i - 1]):
                continue
            if not (c[i] > max(h[i - 1], h[i - 2])):
                continue
            if not (rsi5[i] >= 50 and rsi5[i] > rsi5[i - 1]):
                continue
            lo = 1e18
            for t in range(i - 6, i):
                lo = min(lo, rsi5[t])
            if not (lo <= 30) or not (fl3[i] > 0):
                continue
            if vw[i] - c[i] < 0.3 * a:
                continue
            m[i] = True
            stop[i] = L0 - 0.05 * a
            tgt[i] = vw[i]
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    bb, ee = _segments(b["k"])
    m, stop, tgt = _kern(bb, ee, b["tod"], b["c"], b["h"], b["l"], b["lod"], b["vwap"], b["atr"], _f(df, "fromOpen"),
                         _f(df, "gap"), _f(df, "spy_fo"), _f(df, "rsi5"), _f(df, "flow3"), WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
