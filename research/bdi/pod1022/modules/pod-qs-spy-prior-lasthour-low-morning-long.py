"""pod-qs-spy-prior-lasthour-low-morning-long - Prior day set its low in the last hour: next-morning bounce long
(index ETFs).

Source: Quantified Strategies, 'SPY sets low or high in the last hour' (enter at the next day's open, exit at 11:30,
day trade only; tested Jan 2010 - Aug 2012).
URL: https://quantifiedstrategies.substack.com/p/spy-sets-low-or-high-in-the-last

VARIANT of raschke-80-20 (prior close at the range extreme, then reversal through the prior low). Stated change: the
gate is the TIME the prior-day low was printed (inside the final hour), not where the close sat in the range; no new
low break is needed, and the source uses a morning time exit.

Rules (plain English, LONG). SYMBOLS SPY, QQQ, IWM, DIA.
  1. The prior session's low-of-day bar closed at 15:05 or later: argmin(low) over D-1's full-session 5m bars
     (09:35..15:55; when the daily low is below every 5m bar, the low printed in the 15:55-16:00 bar = 16:00).
     D-1 = the previous NYSE trading day; skipped when it is missing (e.g. right after the locked block).
  2. The prior close is within 0.25 x atr_d of that low (the low held into the bell).
  3. Today's gap is between -0.60% and +0.30%.
  4. Trigger: the first bar closing 09:50-10:30 above session VWAP (vwapReclaim == +1, or the 09:50 bar already above
     VWAP with fromOpen > 0). Entry: that bar's close (the frames start at 09:50, so the source's open entry cannot be
     taken; this is the stated intraday confirmation).
  Stop (GEOM S): today's low of day so far - 0.05 x atr_d. Target: prior close + 0.25 x atr_d; when that is not
  above the entry there is no target (held to the time exit). Main: flat 15:55.
Pre-declared configurations (3): this main (flat 15:55); -x1130 (the source's 11:30 time exit, GEOM S+x);
-high-short (the companion the source also tested: prior-day HIGH in the final hour, close within 0.25 ATR of it,
gap -0.30..+0.60%, first close below VWAP, stop HOD + 0.05 ATR, target prior close - 0.25 ATR; the source text could
not be fetched this run, so the short direction is the stated mirror, not verified). No tweak made.
Costs per config/default.yaml (scorer). Only bars up to the decision bar and completed prior days are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r38_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
EXIT_TOD = 0
WINDOW = (950, 1030)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = []
LAYERS = ["D-1 low-of-day bar at/after 15:05", "D-1 close within 0.25 ATR of that low", "gap -0.60..+0.30%",
          "first close above VWAP 09:50-10:30", "stop LOD - 0.05 ATR, target PC + 0.25 ATR, flat 15:55"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    p = U.map_prior(df, SYMBOLS)
    c, atr, tod = b["c"], b["atr"], b["tod"]
    vd, fo, gap = U.f(df, "vwapDistPct"), U.f(df, "fromOpen"), U.f(df, "gap")
    rc = U.f(df, "vwapReclaim")
    with np.errstate(invalid="ignore"):
        if SIDE == "long":
            m = (p["lo_tod_1"] >= 1505) & (np.abs(p["close_1"] - p["dlo_1"]) <= 0.25 * atr)
            m &= (gap >= -0.60) & (gap <= 0.30)
            m &= (rc == 1) | ((tod == 950) & (vd > 0) & (fo > 0))
            stop = b["lod"] - 0.05 * atr
            tgt = b["pc"] + 0.25 * atr
            tgt = np.where(tgt > c, tgt, c * 10.0)            # no target -> unreachable limit
        else:
            m = (p["hi_tod_1"] >= 1505) & (np.abs(p["dhi_1"] - p["close_1"]) <= 0.25 * atr)
            m &= (gap >= -0.30) & (gap <= 0.60)
            m &= (rc == -1) | ((tod == 950) & (vd < 0) & (fo < 0))
            stop = b["hod"] + 0.05 * atr
            tgt = b["pc"] - 0.25 * atr
            tgt = np.where(tgt < c, tgt, c * 0.0 + 1e-6)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0) & np.isfinite(stop)
    return np.asarray(m, bool), stop, tgt


def mask(df):
    m, s, t = _compute(df)
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
