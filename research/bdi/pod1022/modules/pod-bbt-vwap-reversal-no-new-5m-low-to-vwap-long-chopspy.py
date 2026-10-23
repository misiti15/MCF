"""pod-bbt-vwap-reversal-no-new-5m-low-to-vwap-long-chopspy - CHOPPY-INDEX ARM of the Aziz VWAP reversal (adds SPY |fromOpen| < 0.4% at entry).
Same rules as the full-day module below; only CHOP = True differs.

Source: Bear Bull Traders (Andrew Aziz) course slides 'VWAP Trading: VWAP Reversals / False Breakouts / MA Trends' and
the BBT page 'How to Trade Extreme Reversals and VWAP Reversals'.
URL: https://members.bearbulltraders.com/how-to-trade-extreme-reversals-and-vwap-reversals/

VARIANT of pod-bbt-extreme-rev-mtf-long and pod-bbt-bottom-reversal-level-hammer-long. Stated change: no stretch,
level or hammer; the trigger is a failure to make a new low, and the target is VWAP from below (never needs a VWAP
reclaim; not the VWAP false-breakdown or reclaim setups).

Rules (plain English), trigger bar i (5-minute bars):
  1. In play: rvol_day >= 2 at bar i (cumulative volume 09:30..bar / its 20-session same-time mean, r24 cache) and
     (|gap| >= 2% or |fromOpen| >= 2%).
  2. Weak: close < VWAP and fromOpen <= -1.5%; the session low was printed at or after 09:50 (a frame bar's low equals
     the low of day; the frame starts at 09:50).
  3. No new low: bars i-1 and i both have low > the session low.
  4. Trend turn: 5-minute EMA9 >= EMA21 (frame emaDiff >= 0; EMA21 stands in for EMA20). The source's alternative
     '1-minute EMA9 crossed above EMA20 in the last 5 bars' is NOT coded (no 1-minute frames for the universe) - a
     stated deviation that makes the rule stricter.
  5. Room: VWAP - close >= 0.4 x 5-minute ATR14 (atrPct x close).
  6. Trigger: bar i closes above bar i-1's high. Bar close 10:00-11:30 ET.
  Entry: bar i close (= next-bar open). Stop (GEOM S): session low - 0.05 x atr_d. Target: session VWAP at entry. The
  half scale-out at EMA20 is not tested. The source's 60-minute time stop is NOT supported by the scorer (holds to
  stop / target / 15:55) - a stated deviation.
Arms: this full-day arm; the choppy-index arm (SPY |fromOpen| < 0.4% at entry) is module ...-chopspy.
No tweak used. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r31_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1130)
CONTEXT = ["spy_fo"]
CHOP = True
LAYERS = ["rvol_day >= 2 and (|gap| or |fromOpen| >= 2%)", "close < VWAP, fromOpen <= -1.5, LOD set after 09:50",
          "bars i-1, i low > LOD", "emaDiff >= 0", "VWAP - close >= 0.4 ATR5", "close > prior high",
          "stop LOD - 0.05 ATR, target VWAP", "10:00-11:30 ET"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, h, l, lod, ok, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        runl = np.inf
        for i in range(i0, i1):
            runl = min(runl, l[i])
            if i == i0 or tod[i] < w0 or tod[i] > w1 or not ok[i]:
                continue
            if not (runl <= lod[i] + 1e-6 * c[i]):
                continue
            if l[i - 1] > lod[i] + 1e-9 and l[i] > lod[i] + 1e-9 and c[i] > h[i - 1]:
                m[i] = True
    return m


def compute(df):
    b = U.base(df)
    k = U.key(df)
    si = U.sess_ind(df)
    c, atr, vw = b["c"], b["atr"], b["vwap"]
    fo, gap = U.f(df, "fromOpen"), U.f(df, "gap")
    atr5 = U.f(df, "atrPct") / 100 * c
    with np.errstate(invalid="ignore"):
        ok = (si["rvc"] >= 2) & ((np.abs(gap) >= 2) | (np.abs(fo) >= 2))
        ok &= (c < vw) & (fo <= -1.5)
        ok &= U.f(df, "emaDiff") >= 0
        ok &= (vw - c) >= 0.4 * atr5
        if CHOP:
            ok &= np.abs(U.f(df, "spy_fo")) < 0.4
        ok &= atr > 0
    bb, ee = U.segments(k)
    m = _k(bb, ee, b["tod"], c, b["h"], b["l"], b["lod"], np.asarray(ok, np.bool_), WINDOW[0], WINDOW[1])
    stop = b["lod"] - 0.05 * atr
    return m, stop, vw


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return m


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
