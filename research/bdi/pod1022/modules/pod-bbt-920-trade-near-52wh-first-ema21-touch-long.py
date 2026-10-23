"""pod-bbt-920-trade-near-52wh-first-ema21-touch-long - Aziz 9/20 trade: a strong-open stock near its 52-week high, the
first touch of the 5-min EMA20/21, target the high of day (LONG).

Source: Bear Bull Traders - Andrew Aziz, 'Strategy: 9-20 Trade' deck (Feb 2023).
URL: https://members.bearbulltraders.com/wp-content/uploads/2023/02/Strategy-9-20-Trade.pdf

VARIANT of Reddit R09 'first pullback to the 20 MA in a trend' (full day, failed). Stated changes: only stocks within
3% of their 52-week high (source: 'near all-time highs'), only the FIRST touch of the EMA after a strong open, a hard
10:00-11:00 window, and the HOD as target. The frame has EMA9 / EMA21 (emaDiff), so EMA21 stands in for the deck's
EMA20.

52-week high (stated data note): max daily high over the 365 calendar days through the prior session, from
research/history2y/data/daily.parquet with the locked block (2024-11-01..2025-02-28) filtered out on read; it needs
>= 100 non-locked sessions in the window (the daily file starts 2024-09-16), so the earliest open months score no
trades. Known before the open; nothing from today is used.

Rules (plain English), decision bar i (only bars up to i):
  1. Prior close >= 0.97 x the 52-week high; ADV >= $20M (scorer default).
  2. Strong open: the running HOD at i >= today's open + 0.6 x daily ATR, and it was set (the last bar whose high
     equals the running HOD) on a frame bar closing after 09:50 that lies in i-8..i-2.
  3. First touch: every bar from the HOD bar to i-1 had low > EMA21; bar i has low_i <= EMA21_i x 1.001,
     close_i > EMA21_i and close_i > session VWAP.
  4. EMA9_i > EMA21_i (emaDiff > 0).
  Entry: close_i, bar close 10:00-11:00. Stop (GEOM S): EMA21_i - 0.15 x daily ATR ('meaningful break of the 20').
  Target: the running HOD at entry; skip if (HOD - entry) < 1.0 x (entry - stop). Flat 15:55. Costs in (scorer).
  1 config, no tweak.
Educational only - not financial advice."""
import numba
import numpy as np

from _bbtr22_util import base, prior_52w

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1100)
MIN_ADV = 20e6
CONTEXT = []
LAYERS = ["prior close >= 0.97 x 52-week high", "HOD >= open + 0.6 ATR set after 09:50 within i-8..i-2",
          "first touch of EMA21 since the HOD, close above EMA21 and VWAP", "emaDiff > 0",
          "stop EMA21 - 0.15 ATR, target HOD, skip < 1R", "10:00-11:00 ET"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, hod, vw, op, ok52, ed, e21, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not ok52[i0]:
            continue
        j = -1
        for i in range(i0, i1):
            if h[i] >= hod[i] - 1e-5 * c[i]:
                j = i
            if tod[i] < w0 or tod[i] > w1 or j < 0:
                continue
            a = atr[i]
            if not (a > 0 and tod[j] > 950 and i - j >= 2 and i - j <= 8):
                continue
            if not (hod[i] >= op[i] + 0.6 * a):
                continue
            first = True
            for k in range(j, i):
                if not (e21[k] == e21[k] and l[k] > e21[k]):
                    first = False
                    break
            if not first:
                continue
            x = e21[i]
            if not (x == x and l[i] <= x * 1.001 and c[i] > x and c[i] > vw[i] and ed[i] > 0):
                continue
            sp = x - 0.15 * a
            t = hod[i]
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
    _, hi52 = prior_52w(df)
    with np.errstate(invalid="ignore"):
        ok52 = np.isfinite(hi52) & (d["pdc"] >= 0.97 * hi52)
    m, sp, tp = _kern(d["b"], d["e"], d["tod"], d["c"], d["h"], d["l"], d["hod"], d["vw"], d["op"], ok52, d["ed"],
                      d["e21"], d["atr"], WINDOW[0], WINDOW[1])
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
