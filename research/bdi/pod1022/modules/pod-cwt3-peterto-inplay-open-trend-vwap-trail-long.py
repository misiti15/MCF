"""pod-cwt3-peterto-inplay-open-trend-vwap-trail-long - In-play open-to-close trend, VWAP-trail exit (LONG).

Source: Chat With Traders EP098, Peter To (open-to-close trend capture with a VWAP trail) [~00:57:14].
URL: https://chatwithtraders.com/098

VARIANT, parents pod-edgeful-green-first15-open-hold-long and pod-oa-wide-first-hour-continuation. Stated changes:
in-play universe only (gap and relative volume), a 30-minute direction test that must also stay above VWAP the whole
time, and a different exit (VWAP trail with a partial at OR high + 2 x OR range).

Rules (plain English, LONG). The 09:30 print, the 09:30-10:00 range, the first-30-minute volume and the 09:35-09:45
closes vs VWAP come from the 1-minute cache (research/bdi/pod1022/cwt3_openbars.py; the frames start at 09:50).
  Universe: |gap| >= 3%, first-30-minute relative volume >= 2.0 (09:30-10:00 volume / its mean over the prior 20
  completed sessions), price >= $5, adv20 >= $20M.
  At the 10:00 bar: (a) 10:00 close > 09:30 open; (b) no 5-minute close below session VWAP from 09:35 to 10:00;
  (c) 10:00 close in the top 30% of the 09:30-10:00 range; (d) SPY fromOpen (spy_fo) > -0.3%.
  Entry: the 10:00 bar close.
  Stop (GEOM S): the higher of the 30-minute opening-range low and VWAP - 0.25 x ATR14(5m) (atrPct x close).
  Exit deviation (scorer limit): the VWAP trail (first 5-minute close below VWAP) cannot be modelled by the pod1022
  scorer; the module uses the source's partial level, OR high + 2 x OR range, as the single limit target, the fixed
  initial stop, and otherwise holds to 15:55. Costs in (scorer).
No tweak used. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1000)
CONTEXT = ["spy_fo"]
LAYERS = ["|gap| >= 3%, 30-min rvol >= 2, price >= $5", "10:00 close > 09:30 open",
          "no 5m close below VWAP 09:35-10:00", "10:00 close in the top 30% of the 30-min range", "spy_fo > -0.3",
          "entry 10:00 close", "stop max(OR low, VWAP - 0.25 ATR5m), target OR high + 2 x OR range, else 15:55"]

_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}


def _ob():
    p = str(_ROOT / "research" / "bdi" / "pod1022")
    if p not in sys.path:
        sys.path.insert(0, p)
    import cwt3_openbars  # noqa: E402
    return cwt3_openbars


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    j = _ob().join(df, ["o930", "h30", "l30", "rvol30", "below_vwap_pre950"])
    f = lambda k: df[k].to_numpy(float)
    c, vd, gap = f("close"), f("vwapDistPct"), f("gap")
    tod = df["tod"].to_numpy(np.int64)
    o, h30, l30, rv, pre = (j[k].to_numpy(float) for k in ("o930", "h30", "l30", "rvol30", "below_vwap_pre950"))
    k = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    with np.errstate(invalid="ignore", divide="ignore"):
        bel = ((tod <= 1000) & (vd < 0)).astype(int)
        anybel = pd.Series(bel).groupby(k).cumsum().to_numpy() > 0         # 09:50 / 09:55 / 10:00 frame closes
        vw = c / (1 + vd / 100)
        atr5 = f("atrPct") / 100 * c
        stop = np.fmax(l30, vw - 0.25 * atr5)
        tgt = h30 + 2 * (h30 - l30)
        m = (tod == 1000) & (np.abs(gap) >= 3) & (rv >= 2.0) & (c >= 5)
        m &= (c > o) & (pre == 0) & ~anybel
        m &= c >= l30 + 0.7 * (h30 - l30)
        m &= f("spy_fo") > -0.3
        m &= (stop < c) & (tgt > c)
    return np.asarray(m, bool), stop, tgt


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
