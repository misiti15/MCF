"""pod-kell-daily-ema-crossback-first-touch-long - Kell EMA crossback: first daily 10/20 EMA touch after a wedge pop,
intraday open + VWAP reclaim trigger (LONG).

Source: TraderLion, 'How to Buy Stocks on Pullbacks with the EMA Crossback Strategy' and 'Oliver Kell's EMA Crossback
Uncovers Low-Risk Entries' (Oliver Kell, Cycle of Price Action).
URL: https://traderlion.com/technical-analysis/chart-patterns/ema-crossback/

VARIANT of pod-traderlion-kell-wedge-pop-long (intraday 5m EMA pop) and pod-traderlion-dryup-ema21-pullback-long
(5m EMA21 dry-up). Stated change: this is the NEXT stage of Kell's cycle on DAILY EMAs - a daily wedge pop in the last
3-15 sessions, then the first intraday touch of the daily EMA10 / EMA20, bought on the reclaim of the open and VWAP.
Rules (plain English):
  1. Wedge pop: some session p in D-15..D-3 closed above both its daily EMA10 and EMA20, after the 5 sessions just
     before it all closed below their EMA20 (the most recent such pop is used).
  2. Since the pop, the max high of p+1..D-1 is >= pop close + 1.5 x atr_d.
  3. First touch: no completed day p+1..D-1 had a low <= its EMA10; today's low of day (as of the previous bar) is
     <= EMA10 (as of D-1) + 0.1 x atr_d, and today's low of day stays >= EMA20 (D-1) - 0.3 x atr_d.
  4. Trigger: a 5-minute close above both today's open and the session VWAP (the previous bar was not above both),
     buyPressure > 0, after the touch.
  Entry: trigger close, 10:00-14:30 ET. Stop (GEOM S): LOD - 0.05 x atr_d; skip when risk > 0.7 x atr_d.
  Target: D-1 high when it is >= 1R above entry, else 2R; flat 15:55.
Harness notes (pre-declared): daily EMAs from lib.daily() closes (completed days, series restart after the locked
block; EMA10 needs 20 and EMA20 40 sessions of warm-up). The pop's '>= 5 sessions below EMA20' is read as the 5
sessions immediately before the pop. The frame starts at 09:50: a touch and reclaim that both finish before 09:50 is
not observable. No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r27_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = []
LAYERS = ["daily wedge pop in D-15..D-3 (close > EMA10/20 after 5 closes < EMA20)", "rally >= 1.5 ATR above pop close",
          "first touch of daily EMA10 (+0.1 ATR) holding EMA20 - 0.3 ATR", "5m close reclaims open and VWAP, buyPressure > 0",
          "10:00-14:30", "stop LOD - 0.05 ATR (risk <= 0.7 ATR), target PDH if >= 1R else 2R"]
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
    if not n:
        return np.zeros(0, bool)
    k = U.key(df)
    b = U.base(df)
    D = U.map_daily(df, k, ["e101", "e201", "h1", "kell_pc", "kell_mh", "kell_touch"])
    c, atr, lod, tod = b["c"], b["atr"], b["lod"], b["tod"]
    bp = U.f(df, "buyPressure")
    with np.errstate(invalid="ignore"):
        m = np.isfinite(D["kell_pc"]) & (D["kell_touch"] == 0)
        m &= D["kell_mh"] >= D["kell_pc"] + 1.5 * atr
        lodp = U.lag(lod, k)
        m &= lodp <= D["e101"] + 0.1 * atr
        m &= lod >= D["e201"] - 0.3 * atr
        above = (c > b["opn"]) & (c > b["vwap"])
        abovep = U.lag(above.astype(float), k)
        m &= above & (abovep == 0) & (bp > 0)
        stop = lod - 0.05 * atr
        risk = c - stop
        m &= (risk > 0) & (risk <= 0.7 * atr)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        tgt = np.where(D["h1"] - c >= risk, D["h1"], c + 2 * risk)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), bool)
