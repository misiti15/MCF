"""pod-bbt-1to10-index-megacap-close-reversal-long - 1-to-10 into the close: index ETFs / mega-caps, a late higher low
after an all-day fade, tight stop, VWAP target (LONG).

Source: Bear Bull Traders - Peter Donnelly, 'Strategy 10: 1 to 10 Strategy' / TradeBook 'The 1-to-10 Strategy:
Structuring Trades for Maximum Risk-to-Reward at the Close' (webinar Apr 28, 2026).
URL: https://members.bearbulltraders.com/course/advanced-strategies/lesson/strategy-10-1-to-10-strategy/

VARIANT of pod-bbt-late-day-downtrend-squeeze-long. Stated changes: the universe is ONLY SPY, QQQ, IWM, DIA and the 8
largest caps (AAPL MSFT NVDA AMZN GOOGL META AVGO TSLA) - the source says 'only large caps with institutional
volume' - so the fade gate is fromOpen <= -0.5% (not -2%), there is no breadth gate, and the exit uses the 1-to-10
structure: a tight stop at the higher low with a reward/risk >= 4 gate to VWAP.

Rules (plain English), decision bar i (only bars up to i):
  1. >= 75% of today's frame bars up to i (09:50 on) closed below session VWAP; fromOpen_i <= -0.5%.
  2. The running LOD was set (last bar whose low equals it) on a frame bar j closing 13:30-14:40; i - j >= 2, and the
     lowest low of bars j+1..i (the higher low HL) >= LOD + 0.05 x daily ATR.
  3. Trigger: close_i > max(high_{i-2}, high_{i-1}) and close_i > EMA9_i (5-min EMA9 recovered from emaDiff).
  4. Stop = HL - 0.02 x daily ATR; cost guard: skip if entry - stop < 0.12% of price.
  5. (VWAP_i - close_i) >= 4 x (close_i - stop).
  Entry: close_i, bar close 14:15-15:00. Stop (GEOM S) as above; target: session VWAP at entry, else flat 15:55.
  Costs in (scorer; tight stops make costs per R large - see the cost note in the result). 1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

from _bbtr22_util import base

SIDE = "long"
GEOM = "S"
WINDOW = (1415, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "TSLA"]
CONTEXT = []
LAYERS = [">= 75% of bars below VWAP, fromOpen <= -0.5%", "LOD set 13:30-14:40, HL >= LOD + 0.05 ATR",
          "close > 2-bar high and > EMA9", "stop HL - 0.02 ATR, risk >= 0.12% of price", "VWAP >= 4R above",
          "target VWAP", "14:15-15:00 ET, index ETFs + 8 mega-caps"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, lod, vw, fo, e9, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        j = -1
        below = 0
        for i in range(i0, i1):
            if c[i] < vw[i]:
                below += 1
            if l[i] <= lod[i] + 1e-5 * c[i]:
                j = i
            if tod[i] < w0 or tod[i] > w1 or j < 0 or i - i0 < 2:
                continue
            a = atr[i]
            if not (a > 0 and fo[i] <= -0.5 and below >= 0.75 * (i - i0 + 1)):
                continue
            if tod[j] < 1330 or tod[j] > 1440 or i - j < 2:
                continue
            hl = 1e18
            for t in range(j + 1, i + 1):
                hl = min(hl, l[t])
            if hl < lod[i] + 0.05 * a:
                continue
            if not (c[i] > max(h[i - 2], h[i - 1]) and e9[i] == e9[i] and c[i] > e9[i]):
                continue
            sp = hl - 0.02 * a
            risk = c[i] - sp
            if not (risk >= 0.0012 * c[i]):
                continue
            if vw[i] - c[i] < 4.0 * risk:
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = vw[i]
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    if len(df) == 0:
        return np.zeros(0, bool)
    d = base(df)
    m, sp, tp = _kern(d["b"], d["e"], d["tod"], d["c"], d["h"], d["l"], d["lod"], d["vw"], d["fo"], d["e9"],
                      d["atr"], WINDOW[0], WINDOW[1])
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
