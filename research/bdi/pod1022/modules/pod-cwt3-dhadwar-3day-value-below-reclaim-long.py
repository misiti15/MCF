"""pod-cwt3-dhadwar-3day-value-below-reclaim-long - Open below the 3-day composite value area, the early low holds,
buy the return to value (LONG).

Source: Chat With Traders EP041, Kam Dhadwar (trade back toward a multi-day value area) [~00:30:30-00:40:36].
URL: https://chatwithtraders.com/041

VARIANT. Parents: pod-dalton-quiet-poc-revert-long (prior-day POC) and the backlog 'Volume profile: 80% rule' (single
prior session). Stated change: the reference is a 3-SESSION composite value area, and the entry needs the opening range
to fail to extend lower.

Rules (plain English, LONG). Opening values and the composite profile come from the 1-minute cache
(research/bdi/pod1022/cwt3_openbars.py; the lab frames start at 09:50):
  Composite value area: 5-minute bar volume at the bar close price over sessions D-1, D-2, D-3 (completed; dropped if
  the three sessions span > 7 calendar days), price bins of 0.1% of the D-1 close (pre-declared bin size), POC = the
  highest-volume bin, value area = 70% of the volume grown out from the POC (VAL / VAH).
  Universe: SPY, QQQ, IWM and liquid large caps; pre-declared stand-in for 'liquid large caps': adv20 >= $500M.
  (a) the 09:30 open < composite VAL;
  (b) composite VA width (VAH - VAL) >= 0.5 x ATR14(daily) (the source's 1.0 x ATR x 0.5: a real bulge);
  (c) between 10:00 and 10:30 no new session low below the 09:30-10:00 low (checked on the bars seen so far);
  (d) not a trend-down day: SPY's 10:00 close vs its 09:30 open > -0.5%.
  Entry: the first 5-minute close above the 09:30-10:00 opening-range high (the first such close of the day), bar close
  10:00-13:00, while the close is still below the composite POC.
  Stop (GEOM S): session low - 0.05%. Target: composite POC. Skip if POC - entry < 1.5R or < 3 x an estimated
  round-trip cost (2 x (1c + 1 bps) x 1.4). Flat 15:55 (the time stop). The 50% scale at VAL is not modelled (the
  scorer takes one exit; the whole position targets the POC). Costs in (scorer).
No tweak used. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1300)
MIN_ADV = 500e6
CONTEXT = []
LAYERS = ["09:30 open < 3-day composite VAL", "VA width >= 0.5 x ATR14", "no new low below the 09:30-10:00 low 10:00-10:30",
          "SPY 10:00 vs open > -0.5%", "close crosses above the 30-min OR high, below the POC", "10:00-13:00",
          "stop session low - 0.05%, target POC, >= 1.5R and >= 3x cost"]

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
    if n == 0:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    ob = _ob()
    t = ob.table()
    j = ob.join(df, ["o930", "h30", "l30", "poc3", "val3", "vah3"])
    spy = t[t["symbol"] == "SPY"][["date", "o930", "c1000"]]
    spy = spy.assign(spy10=(spy["c1000"] / spy["o930"] - 1) * 100)[["date", "spy10"]]
    sp = pd.DataFrame({"date": df["date"].to_numpy()}).merge(spy, on="date", how="left")["spy10"].to_numpy(float)
    f = lambda k: df[k].to_numpy(float)
    c, l, atr = f("close"), f("low"), f("atr_d")
    tod = df["tod"].to_numpy(np.int64)
    o, h30, l30, poc, val, vah = (j[k].to_numpy(float) for k in ("o930", "h30", "l30", "poc3", "val3", "vah3"))
    k = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    with np.errstate(invalid="ignore", divide="ignore"):
        brk = ((tod > 1000) & (tod <= 1030) & (l < l30)).astype(int)
        broke = pd.Series(brk).groupby(k).cumsum().to_numpy() > 0       # a new low below the OR low 10:05..10:30, so far
        lod = np.fmin(c - f("dist_lod_atr") * atr, l30)
        stop = lod * (1 - 0.0005)
        risk = c - stop
        cost = 2 * (0.01 + 0.0001 * c) * 1.4
        m = (o < val) & ((vah - val) >= 0.5 * atr) & ~broke & (sp > -0.5)
        up = ((c > h30) & (tod > 1000)).astype(int)
        m &= (up == 1) & (pd.Series(up).groupby(k).cumsum().to_numpy() == 1)   # the first close above the OR high
        m &= c < poc
        m &= (risk > 0) & ((poc - c) >= 1.5 * risk) & ((poc - c) >= 3 * cost)
    return np.asarray(m, bool), stop, poc


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
