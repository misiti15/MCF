"""pod-bbt-parabolic-ema9-capitulation-daily-level-long - Parabolic reversal (long side) at a daily level: three large
red bars stretched 2% below the 5-min EMA9, the first new 5-min high, target EMA9 (LONG).

Source: Bear Bull Traders - 'How to Trade Parabolic Reversals' (Strategy 3 deck 2023, Part 2 webinar).
URL: https://bearbulltraders.com/wp-content/uploads/2023/05/how-to-trade-parabolic-reversals-1.pdf

VARIANT of pod-bbt-parabolic-ema9-snapback-short (same source). Stated changes: the opposite SIDE (long after a
down-parabola), plus a required daily-level confluence (the deck lists 'reversal at a daily level' as a confirmation;
the short file has none) and a no-engulfing-into-entry rule. EMA9 recovered exactly from emaDiff as in the short file.

Rules (plain English), decision bar i (only bars up to i):
  1. Bars i-3, i-2, i-1 each close below the previous close ("red": the frame has no open), each with a range
     (high - low) >= 0.15 x daily ATR.
  2. low_{i-1} <= 0.98 x EMA9_{i-1} (>= 2% below the 5-min EMA9).
  3. volumeRatio of bar i-1 or i-2 >= 2.0 (climax).
  4. Daily level: the running LOD is within 0.15 x daily ATR of the prior-day low or the prior close.
  5. The 5-min SMA50 does not lie strictly between close_i and EMA9_i (no MA between entry and target).
  6. Not right after an engulfing bar: range_{i-1} <= 2.0 x range_{i-2}.
  7. Trigger: close_i > high_{i-1} (first new 5-min high).
  Entry: close_i, bar close 09:50-14:30. Stop (GEOM S): min low of bars i-3..i - 0.02 x daily ATR. Target: EMA9_i;
  skip if (EMA9 - entry) < 1.0 x (entry - stop). Flat 15:55. Costs in (scorer). 1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

from _bbtr22_util import base

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1430)
CONTEXT = []
LAYERS = ["3 falling closes with range >= 0.15 ATR each", "low_{i-1} <= 0.98 x EMA9", "volumeRatio >= 2 on i-1 or i-2",
          "LOD within 0.15 ATR of PDL or PDC", "5m SMA50 not between entry and EMA9", "range_{i-1} <= 2 x range_{i-2}",
          "close > prior bar high", "stop min low(i-3..i) - 0.02 ATR, target EMA9, skip < 1R", "09:50-14:30 ET"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, lod, pdc, pdl, e9, vr, sma, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 4, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0):
                continue
            ok = True
            for k in range(i - 3, i):
                if not (c[k] < c[k - 1] and h[k] - l[k] >= 0.15 * a):
                    ok = False
                    break
            if not ok:
                continue
            if not (e9[i - 1] == e9[i - 1] and l[i - 1] <= 0.98 * e9[i - 1]):
                continue
            if not (vr[i - 1] >= 2.0 or vr[i - 2] >= 2.0):
                continue
            if not (abs(lod[i] - pdl[i]) <= 0.15 * a or abs(lod[i] - pdc[i]) <= 0.15 * a):
                continue
            if not ((h[i - 1] - l[i - 1]) <= 2.0 * (h[i - 2] - l[i - 2])):
                continue
            if not (c[i] > h[i - 1]):
                continue
            t = e9[i]
            if not (t == t and t > c[i]):
                continue
            sm = sma[i]
            if sm == sm and sm > c[i] and sm < t:
                continue
            ll = min(min(l[i - 3], l[i - 2]), min(l[i - 1], l[i]))
            sp = ll - 0.02 * a
            if sp < c[i] and (t - c[i]) >= 1.0 * (c[i] - sp):
                m[i] = True
                stop[i] = sp
                tgt[i] = t
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    if len(df) == 0:
        return np.zeros(0, bool)
    d = base(df)
    m, sp, tp = _kern(d["b"], d["e"], d["tod"], d["c"], d["h"], d["l"], d["lod"], d["pdc"], d["pdl"], d["e9"],
                      d["vr"], d["sma50"], d["atr"], WINDOW[0], WINDOW[1])
    _ST[id(df)] = (sp, tp)
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
