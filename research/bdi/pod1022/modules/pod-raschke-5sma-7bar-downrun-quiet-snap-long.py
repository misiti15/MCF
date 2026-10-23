"""pod-raschke-5sma-7bar-downrun-quiet-snap-long - Quiet-day exhaustion: 7+ closes below the SMA5 that made a new
session low, first close back above it, target session VWAP (LONG).

Source: Linda Raschke 5-SMA extension rule (TradingView 'Linda Raschke 5 SMA Reversal [LuciTech]': runs of 7+ bars
on one side mean reversion is likely); Raschke Trade Sheet scanner ('extended-run exhaustion').
URL: https://kr.tradingview.com/script/8MVLfKu4-Raschke-Trade-Sheet-scanner/

VARIANT of pod-smb-rubberband-2bar-snap-long. What changes: the extension is a bar-count run below the SMA5 rather
than distance from VWAP, a quiet-SPY gate is required, and the target is VWAP. (Also related to
pod-cwt4-raschke-sma5-7bar-streak-first-cross-long, which used a drift-size band, an rvol gate and a 50%-retrace
target; here the gates are the idea's own.)

Rules (plain English), decision bar i. SMA5 = mean of the last 5 session 5m closes from 09:35 (_r24 cache).
  1. Quiet gate at bar i: |SPY from open| <= 0.3% (spy_fo) and SPY's range so far today (09:30..bar i) <= 0.6 x SPY
     daily ATR14 (as of D-1).
  2. The >= 7 bars just before i all closed below their SMA5, one of them set a new session low (its low = the
     running LOD), and at bar i the stock is >= 0.4 x daily ATR below session VWAP.
  3. Trigger: bar i is the first close above SMA5 after the run. Enter at that close, bar close 10:30-14:45.
  4. Stop: run low - 0.05 x ATR. Target: session VWAP at entry, capped at entry + 2R. Time stop 60 minutes (12 bars,
     GEOM S+x MAX_BARS). Flat 15:55.
  5. Skip names with |fromOpen| > 4% (not quiet).
No tweak made. 1 configuration. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r36_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
MAX_BARS = 12
WINDOW = (1030, 1445)
CONTEXT = ["spy_fo"]
RUN = 7
LAYERS = ["|spy_fo| <= 0.3, SPY range <= 0.6 SPY ATR", ">= 7 closes below SMA5 with a new LOD in the run",
          ">= 0.4 ATR below VWAP", "first close above SMA5, 10:30-14:45", "|fromOpen| <= 4",
          "stop run low - 0.05 ATR, target VWAP capped 2R, 60-min time stop"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, l, s5, lod, vw, atr, fo, gate, nrun, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 1, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0) or not gate[i] or not (c[i] > s5[i]) or not (abs(fo[i]) <= 4.0):
                continue
            if not (vw[i] - c[i] >= 0.4 * a):
                continue
            cnt = 0
            newlo = False
            lo = np.inf
            j = i - 1
            while j >= i0 and c[j] < s5[j]:
                cnt += 1
                if l[j] <= lod[j] + 1e-9:
                    newlo = True
                lo = min(lo, l[j])
                j -= 1
            if cnt < nrun or not newlo:
                continue
            sp = lo - 0.05 * a
            R = c[i] - sp
            if not (R > 0):
                continue
            t = min(vw[i], c[i] + 2.0 * R)
            if t > c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = t
    return m, stop, tgt


def compute(df):
    n = len(df)
    k = U.key(df)
    b = U.base(df)
    si = U.U31.sess_ind(df)
    sp = U.U27.map_spy(df, ["rng", "spy_atr"])
    with np.errstate(invalid="ignore"):
        gate = (np.abs(U.f(df, "spy_fo")) <= 0.3) & (sp["rng"] <= 0.6 * sp["spy_atr"])
    bb, ee = U.segments(k)
    return _k(bb, ee, b["tod"], b["c"], b["l"], si["s5"], b["lod"], b["vwap"], b["atr"], U.f(df, "fromOpen"),
              np.asarray(gate, np.bool_), RUN, WINDOW[0], WINDOW[1])


def mask(df):
    if "spy_fo" not in df:
        return np.zeros(len(df), dtype=bool)
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
