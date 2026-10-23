"""pod-cwt4-jelinek-multiday-unfilled-gap-magnet-long - Old unfilled down-gap as a magnet: VWAP-reclaim long toward a
multi-day gap edge (LONG).

Source: Chat With Traders ep 26, Brad Jelinek ('Unfilled gap as intraday target': markets tend to come back to fill
gaps; use the gap mainly as a target). URL: https://chatwithtraders.com/26

VARIANT of pod-wt-gap-full-fill-pdc-hold-long and the small index-ETF gap-fill sleeve (today's gap to the prior close
only). Stated change: the target is an OLDER unfilled down-gap edge from 2-20 sessions back, and the entry is a VWAP
reclaim, not the open.

Rules (plain English):
  1. Gap: on some day j in D-20..D-2 the stock opened below the prior day's low by >= 0.3 x daily ATR14 (ATR as of
     j-1). Its upper edge G = low of day j-1. Unfilled: no daily high from day j through D-1 reached G. Use the nearest
     (lowest) such edge above today's open. Daily values come from completed days only (lib.daily, D-1 and earlier).
  2. In reach: today's open < G and 0.5 <= (G - open) / atr_d <= 1.5. Today's high so far is still below G.
  3. Trigger: a 5-minute close above session VWAP after the 3 previous closes were below VWAP, bar volumeRatio >= 1,
     bar close 10:00-13:30 ET (the frame starts at 09:50, so the first possible trigger is 10:05).
  4. SPY from-open (spy_fo) >= 0 at the trigger.
  Entry: the trigger close (= next-bar open). Stop (GEOM S): the tighter (higher) of the session low and
  entry - 0.6 x atr_d. Target: limit at G - 0.02 x atr_d. Flat 15:55. Costs per config/default.yaml (scorer).
Control (separate module ...-ctrl-nogap): the same trigger on days with NO unfilled edge within 1.5 ATR above the
open, target open + 1.0 x atr_d (the middle of the in-reach band), to show whether the magnet adds anything.
No tweak used. Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r31_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1330)
CONTEXT = ["spy_fo"]
CONTROL = False
LAYERS = ["unfilled down-gap edge G (gap >= 0.3 ATR) from D-20..D-2, nearest above open",
          "0.5 <= (G - open)/ATR <= 1.5, HOD < G", "close > VWAP after 3 closes below, volumeRatio >= 1",
          "spy_fo >= 0", "stop max(LOD, entry - 0.6 ATR), target G - 0.02 ATR", "10:00-13:30 ET"]
_ST = {}


def compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    G = U.map_day(df, U.gap_tab(), ["gapG"])["gapG"]
    c, atr, opn = b["c"], b["atr"], b["opn"]
    vd = U.f(df, "vwapDistPct")
    with np.errstate(invalid="ignore", divide="ignore"):
        dist = (G - opn) / atr
        if CONTROL:
            m = ~(dist <= 1.5)                     # no unfilled edge above the open within 1.5 ATR (NaN = none)
            tgt = opn + 1.0 * atr
        else:
            m = (dist >= 0.5) & (dist <= 1.5) & (b["hod"] < G)
            tgt = G - 0.02 * atr
        m &= (vd > 0) & (U.lag(vd, k, 1) < 0) & (U.lag(vd, k, 2) < 0) & (U.lag(vd, k, 3) < 0)
        m &= U.f(df, "volumeRatio") >= 1
        m &= U.f(df, "spy_fo") >= 0
        m &= (b["tod"] >= WINDOW[0]) & (b["tod"] <= WINDOW[1])
        stop = np.maximum(b["lod"], c - 0.6 * atr)
        m &= (stop < c) & (tgt > c) & (atr > 0)
    return np.asarray(m, bool), stop, tgt


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
