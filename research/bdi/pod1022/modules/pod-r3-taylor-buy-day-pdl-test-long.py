"""pod-r3-taylor-buy-day-pdl-test-long - Taylor 'Buy Day': the morning low made first at the prior-day low after a
1-2 day sell-off (LONG).

Source: George D. Taylor, 'Taylor Trading Technique' (StoneX summary + Wyckoff thread on EliteTrader); the classic
day-cycle method.
URL: https://futures.stonex.com/blog/the-taylor-trading-technique

Parent check: related to CWT14-failbrk-pdl long, but NOT a copy - no break of the PDL is needed; the trigger is a
day-cycle gate plus a test of the PDL from either side.
Rules (plain English; open = close / (1 + fromOpen/100), prior close pc = open / (1 + gap/100), PDH / PDL from
dist_pdh_atr / dist_pdl_atr):
  1. The prior day closed in the bottom 35% of its range: (pc - PDL) / (PDH - PDL) <= 0.35.
  2. The prior day was a down day: pc < the close two sessions back (lib.daily(), completed days).
  3. Today's gap <= +0.3%.
  4. Trigger bar, 10:00-11:30: the low of day so far is within 0.25 x atr_d of the PDL (either side); the bar's
     lower_wick >= 0.4; rsi5 crosses up through 30 (previous bar < 30, this bar >= 30); close > LOD + 0.1 x atr_d;
     spy_fo > -0.5.
  Entry: trigger close. Stop (GEOM S): LOD - 0.05 x atr_d. Target: PDH or entry + 1.5R, whichever is closer;
  otherwise flat 15:55.
Harness notes (pre-declared): rule 2 uses the source's primary form (pc below the close two sessions back), not the
'close below its own open' alternative. The 'holdtr' second geometry the source mentions is not run (one module, the
stated geometry). No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r27_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1130)
CONTEXT = ["spy_fo"]
LAYERS = ["prior day close in bottom 35% of its range", "prior close < close two sessions back", "gap <= +0.3%",
          "LOD within 0.25 ATR of PDL", "lower wick >= 0.4, rsi5 crosses up 30, close > LOD + 0.1 ATR, spy_fo > -0.5",
          "10:00-11:30", "stop LOD - 0.05 ATR, target min(PDH, 1.5R)"]
_ST = {}


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool)
    k = U.key(df)
    b = U.base(df)
    D = U.map_daily(df, k, ["c2"])
    c, atr, lod, tod, pdh, pdl, pc = b["c"], b["atr"], b["lod"], b["tod"], b["pdh"], b["pdl"], b["pc"]
    r5 = U.f(df, "rsi5")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (pdh > pdl) & ((pc - pdl) / (pdh - pdl) <= 0.35)
        m &= pc < D["c2"]
        m &= U.f(df, "gap") <= 0.3
        m &= np.abs(lod - pdl) <= 0.25 * atr
        m &= U.f(df, "lower_wick") >= 0.4
        m &= (U.lag(r5, k) < 30) & (r5 >= 30)
        m &= c > lod + 0.1 * atr
        m &= U.f(df, "spy_fo") > -0.5
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = lod - 0.05 * atr
        risk = c - stop
        m &= risk > 0
        t15 = c + 1.5 * risk
        tgt = np.where((pdh > c) & (pdh < t15), pdh, t15)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), bool)
