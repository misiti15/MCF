"""pod-rule201-ssr-intraday-trigger-reclaim-long - Rule 201 short-sale-restriction trigger bounce: intraday -10%
crossing, then a reclaim of the trigger bar's high (LONG).

Source: Barardehi, Bird, Karolyi & Ruchti, 'Are Short-Selling Restrictions Effective?' (Management Science 2025, OFR
WP 23-08); counter-side of Chat With Traders ep171 Stan Gluzman 'SSR-day short' (research/bdi/cwt CATALOG).
URL: https://ideas.repec.org/a/inm/ormnsc/v71y2025i5p3829-3851.html

VARIANT (opposite side and different logic) of CWT ep171 Gluzman SSR-day short; not a gap-down VWAP-reclaim copy,
because the trigger is the intraday crossing of the -10% Rule 201 threshold, not the gap. Evidence (paper): stocks that
just cross -10% intraday earn ~35 bp higher same-day return than stocks just above the threshold; short volume -8%;
the effect does not reverse.

Rules (plain English), universe adv20 >= $50M (MIN_ADV), price >= $10:
  from_pc = (1 + gap/100) x (1 + fromOpen/100) - 1 (bar close vs the prior close).
  1. gap > -7% (the threshold is crossed intraday, not at the open). Trigger bar = the first 5m bar (bar close
     09:50-13:30) whose close has from_pc <= -10%, and no trade before it was at or below -10% (the running low of day
     before the trigger bar, 09:30-09:45 included via the 1-minute cache, is above prior close x 0.90), so the SSR
     starts on that bar.
  2. Within the next 6 bars, a 5m close above the trigger bar's high, and on that bar:
  3. flow3 > 0 and vwapDistPct <= -0.5 (still below VWAP, room to the magnet);
  4. spy_fo > -1.0 (not a market-wide crash).
  Entry: that bar's close, bar close 09:55-14:00, one per symbol-day. Stop (GEOM S): low of day - 0.05 x atr_d.
  Target: session VWAP or the -8% from-prior-close level, whichever is closer (only levels above the entry); else
  flat 15:55.
Reading (pre-declared): the 'first crossing' check uses the running low, because Rule 201 triggers on any trade price.
Tweak: none. 1 configuration. Expect few trades (rare event). Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import numba
import numpy as np

import _r24_bars as R24
import _r33_util as U

SIDE = "long"
GEOM = "S"
WINDOW = (955, 1400)
MIN_ADV = 50e6
CONTEXT = ["spy_fo"]
LAYERS = ["gap > -7%, first close <= -10% vs prior close 09:50-13:30, no earlier trade <= -10%",
          "within 6 bars a close above the trigger bar high", "flow3 > 0, vwapDistPct <= -0.5", "spy_fo > -1.0",
          "price >= 10, adv20 >= 50M", "stop LOD - 0.05 ATR, target nearer of VWAP / -8% level"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, lod, pc, gap, orl, fl3, vd, spy, vw, atr):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        P = pc[i0]
        if not (P > 0) or not (gap[i0] > -7.0) or not (c[i0] >= 10.0):
            continue
        thr = 0.9 * P
        trig = -1
        for i in range(i0, i1):
            prev_low = orl[i0] if i == i0 else lod[i - 1]
            if not (prev_low == prev_low) or prev_low <= thr:
                break                                   # SSR already active before this bar (or unknown)
            if c[i] <= thr:
                if tod[i] >= 950 and tod[i] <= 1330:
                    trig = i
                break
        if trig < 0:
            continue
        for i in range(trig + 1, min(i1, trig + 7)):
            if tod[i] > 1400:
                break
            if c[i] > h[trig] and fl3[i] > 0 and vd[i] <= -0.5 and spy[i] > -1.0:
                sp = lod[i] - 0.05 * atr[i]
                t8 = 0.92 * P
                tp = np.inf
                if vw[i] > c[i]:
                    tp = vw[i]
                if t8 > c[i] and t8 < tp:
                    tp = t8
                if tp < np.inf and sp < c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = tp
                elif sp < c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = c[i] + 100.0 * atr[i]     # no level above: effectively no target, flat 15:55
                break
    return m, stop, tgt


def mask(df):
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    if not n or "spy_fo" not in df:
        return z
    bb = U.base(df)
    with np.errstate(invalid="ignore", divide="ignore"):
        pc = bb["opn"] / (1 + U.f(df, "gap") / 100)
    D = R24.daymap(df, ["or_l"])
    m, stop, tgt = _kern(bb["b"], bb["e"], bb["tod"], bb["c"], bb["h"], bb["l"], bb["lod"], pc, U.f(df, "gap"),
                         D["or_l"], U.f(df, "flow3"), U.f(df, "vwapDistPct"), U.f(df, "spy_fo"), bb["vwap"],
                         bb["atr"])
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
