"""pod-bbt-booty-reversal-pm-15m-consolidation-long - Booty Reversal: afternoon 15-min consolidation after a down-trend,
EMA9 over SMA50, box break (LONG).

Source: Bear Bull Traders - 'Strategy 14: Booty Reversal' TradeBook (2023) + Andrew Aziz 'Reversals' webinar deck
(June 22, 2023).
URL: https://members.bearbulltraders.com/wp-content/uploads/2023/06/How-to-Trade-the-Booty-Reversal-Tradebook.pdf

VARIANT of pod-bbt-extreme-rev-mtf-long (EMA9-over-EMA20 cross that ends a stretched decline). Stated changes: no
VWAP-stretch / RSI-oversold gate; a higher-timeframe CONSOLIDATION (the 'boot', three 15-min bars = nine 5-min bars)
must form at the lows; the cross is the 5-min EMA9 over the 5-min SMA50; entry is a break of the consolidation box;
afternoon only.

Rules (plain English), decision bar i (only bars up to i):
  1. Down-trend: on the 12:00 bar, fromOpen <= -1.0% and the close is below session VWAP.
  2. Boot: bars i-9..i-1 span (max high - min low) <= 0.35 x daily ATR, make no new running low of day (the running
     LOD at i-1 equals the one at i-10), and the range of bars i-3..i-1 is smaller than the range of bars i-9..i-7
     (narrowing / wedge).
  3. The 5-min EMA9 (recovered exactly from emaDiff) is above the 5-min SMA50 (from sma50_dist_pct) at i and was
     below it on at least one bar in i-6..i-1.
  4. Trigger: close_i > max high of bars i-9..i-1 (box break) and volumeRatio_i >= 1.2.
  Entry: close_i, bar close 12:30-14:45. Stop (GEOM S): low_{i-1} - 0.02 x daily ATR (source: the extreme of the
  previous 5-min candle). Target: entry + 2R (source minimum 2:1). Flat 15:55. Costs in (scorer). 1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

from _bbtr22_util import base

SIDE = "long"
GEOM = "S"
WINDOW = (1230, 1445)
CONTEXT = []
LAYERS = ["12:00 fromOpen <= -1% and below VWAP", "9-bar box <= 0.35 ATR, no new LOD, narrowing",
          "EMA9 crossed above SMA50 within 6 bars", "close > box high, volumeRatio >= 1.2",
          "stop low_{i-1} - 0.02 ATR, target 2R", "12:30-14:45 ET"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, lod, vw, fo, vr, e9, sma, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        down = False
        seen = False
        for i in range(i0, i1):
            if tod[i] == 1200:
                seen = True
                down = fo[i] <= -1.0 and c[i] < vw[i]
            if not (seen and down) or tod[i] < w0 or tod[i] > w1 or i - 10 < i0:
                continue
            a = atr[i]
            if not (a > 0):
                continue
            hh = -1e18
            ll = 1e18
            for k in range(i - 9, i):
                hh = max(hh, h[k])
                ll = min(ll, l[k])
            if hh - ll > 0.35 * a:
                continue
            if lod[i - 1] < lod[i - 10] - 1e-5 * c[i]:
                continue
            r_late = max(max(h[i - 3], h[i - 2]), h[i - 1]) - min(min(l[i - 3], l[i - 2]), l[i - 1])
            r_early = max(max(h[i - 9], h[i - 8]), h[i - 7]) - min(min(l[i - 9], l[i - 8]), l[i - 7])
            if not (r_late < r_early):
                continue
            if not (e9[i] == e9[i] and sma[i] == sma[i] and e9[i] > sma[i]):
                continue
            was = False
            for k in range(i - 6, i):
                if e9[k] == e9[k] and sma[k] == sma[k] and e9[k] < sma[k]:
                    was = True
            if not was:
                continue
            if not (c[i] > hh and vr[i] >= 1.2):
                continue
            sp = l[i - 1] - 0.02 * a
            if sp < c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = c[i] + 2.0 * (c[i] - sp)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    if len(df) == 0:
        return np.zeros(0, bool)
    d = base(df)
    m, sp, tp = _kern(d["b"], d["e"], d["tod"], d["c"], d["h"], d["l"], d["lod"], d["vw"], d["fo"], d["vr"],
                      d["e9"], d["sma50"], d["atr"], WINDOW[0], WINDOW[1])
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
