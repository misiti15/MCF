"""pod-cwt4-raschke-post-expansion-range-low-test-long - Post-expansion consolidation: buy intraday tests of the
multi-week range low, never the middle (LONG).

Source: Chat With Traders ep 48, Linda Raschke ('Post-expansion range: trade only tests of the range edges').
VARIANT of pod-of3-dalton-rf-balance-lowerhalf-long and pod-brooks-range-day-edge-fade. The change: a regime gate
(a multi-week 2.5-sigma move just finished), a multi-week box as the reference, and a 3/10 oscillator trigger.
URL: https://chatwithtraders.com/48

Rules (plain English). Universe: the scorer's liquid stocks and ETFs (adv20 >= $20M).
Daily gate (data through D-1's close only; daily series restart after a > 7-day gap):
  1. Expansion: z = 20-day return / (std of daily returns over the prior 100 sessions x sqrt(20)); a day E with
     |z| >= 2.5 (up or down) lies 5-30 sessions before D, and no such day lies in the last 4 sessions (it ended).
  2. Range: high / low = max high / min low of the sessions after E through D-1; width 1.5-4.0 x ATR(14) (D-1);
     >= 2 sessions whose low was within 0.25 ATR of the range low.
  3. D-1's close inside the range (strictly between low and high).
Intraday trigger, decision bar 09:50-15:00 ET:
  4. Today's session low so far came within 0.3 ATR of the range low and never more than 0.5 ATR below it.
  5. The 5-min 3/10 oscillator (fast = SMA3 - SMA10 of 5-min closes, slow = SMA16 of fast; continuous bars incl.
     prior days) crosses above its slow line on this bar, and the bar closes above the range low.
  6. Skip a volume surge: volumeSurge (5-bar vs prior 15-bar average volume, the frame's RVOL proxy) < 2.5.
  Entry: decision bar's close (scorer; the source's next-bar open). Stop (GEOM S): range low - 0.5 ATR.
  Target: range midpoint; else flat 15:55. The multi-day 'hold to range high' option is not modelled (intraday
  scorer). One trade per symbol per day.
No tweak made. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt4_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1500)
LAYERS = ["|z20| >= 2.5 expansion ended 5-30 sessions ago", "post-expansion box 1.5-4 ATR, >= 2 low tests",
          "session low within 0.3 ATR of box low, not > 0.5 below", "5m 3/10 fast crosses above slow, close > box low",
          "volumeSurge < 2.5", "stop box low - 0.5 ATR, target box mid"]
_ST = {}
_C = {}


def _gate():
    if "g" in _C:
        return _C["g"]
    d = U.raw_daily()
    d = d.assign(seg=U._seg(d))
    out = []
    for _, x in d.groupby("seg", sort=False):
        if len(x) < 60:
            continue
        h, l, c = (x[k].to_numpy(float) for k in ("high", "low", "close"))
        pc = np.r_[np.nan, c[:-1]]
        r = c / pc - 1
        sig = pd.Series(r).shift(20).rolling(100, min_periods=60).std().to_numpy()
        ret20 = c / np.r_[np.full(20, np.nan), c[:-20]] - 1
        z = ret20 / (sig * np.sqrt(20))
        ex = np.abs(z) >= 2.5
        tr = np.maximum.reduce([h - l, np.abs(h - pc), np.abs(l - pc)])
        atr = pd.Series(tr).rolling(14, min_periods=14).mean().to_numpy()
        dates = x["date"].dt.strftime("%Y-%m-%d").to_numpy()
        sym = x["symbol"].iloc[0]
        exi = np.flatnonzero(ex)
        for t in range(35, len(x)):
            if ex[t - 4:t].any():
                continue
            cand = exi[(exi >= t - 30) & (exi <= t - 5)]
            if not len(cand):
                continue
            E = cand[-1]
            a = atr[t - 1]
            if not np.isfinite(a) or a <= 0:
                continue
            hh, ll = h[E + 1:t], l[E + 1:t]
            rh, rl = hh.max(), ll.min()
            w = (rh - rl) / a
            if not (1.5 <= w <= 4.0):
                continue
            if int((ll <= rl + 0.25 * a).sum()) < 2:
                continue
            if not (rl < c[t - 1] < rh):
                continue
            out.append((sym, dates[t], rh, rl))
    _C["g"] = pd.DataFrame(out, columns=["symbol", "date", "rh", "rl"])
    return _C["g"]


def _osc(df, syms):
    fb = U.full_bars(df, symbols=syms)
    if fb is None or not len(fb):
        return None
    fb = fb.copy()
    dt = pd.to_datetime(fb["date"])
    g = ((fb["symbol"] != fb["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    cg = fb["c"].groupby(g)
    fast = cg.transform(lambda x: x.rolling(3, min_periods=3).mean()) - cg.transform(
        lambda x: x.rolling(10, min_periods=10).mean())
    slow = fast.groupby(g).transform(lambda x: x.rolling(16, min_periods=16).mean())
    fb["fast"], fb["slow"] = fast, slow
    fb["fast_p"], fb["slow_p"] = fast.groupby(g).shift(1), slow.groupby(g).shift(1)
    return fb


def mask(df) -> np.ndarray:
    n = len(df)
    z = np.zeros(n, bool)
    if n == 0:
        return z
    k = U.key(df)
    gt = _gate()
    s = U.map_day(df, k, gt, ["rh", "rl"])
    rh, rl = s["rh"], s["rl"]
    gated = np.isfinite(rl)
    if not gated.any():
        return z
    syms = sorted(set(df["symbol"].astype(str).to_numpy()[gated]))
    fb = _osc(df, syms)
    if fb is None:
        return z
    o = U.map_rows(df, fb, ["fast", "slow", "fast_p", "slow_p"])
    b = U.base(df)
    c, lod, atr = b["c"], b["lod"], b["atr"]
    with np.errstate(invalid="ignore", divide="ignore"):
        m = gated & (lod <= rl + 0.3 * atr) & (lod >= rl - 0.5 * atr) & (c > rl)
        m &= (o["fast"] > o["slow"]) & (o["fast_p"] <= o["slow_p"])
        m &= U.f(df, "volumeSurge") < 2.5
        stop = rl - 0.5 * atr
        tgt = 0.5 * (rh + rl)
        m &= tgt > c
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def stop_price(f, i):
    return U.stash_get(_ST, f, mask, i, 0)


def target_price(f, i, stop):
    return U.stash_get(_ST, f, mask, i, 1)
