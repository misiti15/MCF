"""pod-r3-slowday-stoch-range-low-small-target-long - Slow-day playbook: low first-hour activity, stochastic turn at
the day's range low, small target (LONG).

Source: Finance Magnates 'Day Trading 101: Different Types of Trading Days' (slow / choppy days: small profits,
stochastics for entries, low volume in the first 30 min flags a choppy day); BearBull 'trade the extremes of the
range' webinar.
URL: https://financemagnates.com/executives/insights/day-trading-101-different-types-of-trading-days-require-different-game-plans

VARIANT of pod-brooks-range-day-edge-fade-BR-long and pod-smb-quiet-tape-level-fade. Stated changes: the slow-day
gate is the stock's own low early participation plus a compressed first hour (not an index range label); the trigger
is a stochastic %K / %D cross up from < 20 at the range low; a small fixed target (t05s1). To be dropped if the
harness overlap check is >= 0.60 against either parent.
Rules (plain English, LONG), bar close 10:45-14:30:
  1. Slow day: the stock's 09:50-10:30 high-low range (bars closing 09:55..10:30) <= 0.45 x atr_d, and the mean
     volumeRatio of those bars <= 0.9.
  2. Quiet market: |spy_fo| <= 0.35 and 0.4 <= breadth <= 0.6.
  3. At the range low: dist_lod_atr <= 0.08 and the LOD is within 0.1 x atr_d of the first-hour (09:30-10:30) low
     (running LOD on the 10:30 bar), i.e. the range is holding, not trending.
  4. Slow stochastic %K(14,3) crosses above %D(3) on this bar with both < 20. The stochastic is computed on the
     symbol's continuous 5m chart over the bars the frame carries (09:50-15:00, spanning prior sessions), because one
     session has too few bars by 10:45.
  Entry at close. GEOM t05s1 (R = 0.25 x atr_d: target 0.5R, stop 1R, flat 15:55).
The alternative S geometry in the idea is not scored (one configuration). No tweak made. Costs per
config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "t05s1"
WINDOW = (1045, 1430)
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["09:50-10:30 range <= 0.45 ATR and mean volumeRatio <= 0.9", "|spy_fo| <= 0.35, breadth 0.4-0.6",
          "dist_lod_atr <= 0.08, LOD within 0.1 ATR of the first-hour low", "stoch %K(14,3) crosses %D below 20",
          "t05s1"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r29_util as U  # noqa: E402


def _stoch(df, b):
    sk = U.symkey(df)
    hh = pd.Series(b["h"]).groupby(sk).transform(lambda s: s.rolling(14, min_periods=14).max()).to_numpy()
    ll = pd.Series(b["l"]).groupby(sk).transform(lambda s: s.rolling(14, min_periods=14).min()).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        raw = np.where(hh > ll, 100 * (b["c"] - ll) / (hh - ll), 50.0)
    raw[~np.isfinite(hh)] = np.nan
    K = pd.Series(raw).groupby(sk).transform(lambda s: s.rolling(3, min_periods=3).mean()).to_numpy()
    D = pd.Series(K).groupby(sk).transform(lambda s: s.rolling(3, min_periods=3).mean()).to_numpy()
    return sk, K, D


def mask(df) -> np.ndarray:
    n = len(df)
    if not n or "spy_fo" not in df or "breadth" not in df:
        return np.zeros(n, bool)
    b = U.base(df)
    k = U.key(df)
    tod, atr = b["tod"], b["atr"]
    early = (tod >= 955) & (tod <= 1030)
    t = pd.DataFrame({"k": k[early], "h": b["h"][early], "l": b["l"][early],
                      "vr": U.f(df, "volumeRatio")[early]})
    ng = int(k.max()) + 1
    eh, el, ev, en = (np.full(ng, np.nan) for _ in range(4))
    if len(t):
        a = t.groupby("k").agg(h=("h", "max"), l=("l", "min"), vr=("vr", "mean"), n=("h", "size"))
        idx = a.index.to_numpy()
        eh[idx], el[idx], ev[idx], en[idx] = a["h"], a["l"], a["vr"], a["n"]
    fhl = U.at_tod(b["lod"], k, tod, 1030)
    sk, K, D = _stoch(df, b)
    Kp, Dp = U.lag(K, sk), U.lag(D, sk)
    with np.errstate(invalid="ignore"):
        m = (en[k] >= 5) & ((eh[k] - el[k]) <= 0.45 * atr) & (ev[k] <= 0.9)
        m &= (np.abs(U.f(df, "spy_fo")) <= 0.35)
        br = U.f(df, "breadth")
        m &= (br >= 0.4) & (br <= 0.6)
        m &= (U.f(df, "dist_lod_atr") <= 0.08) & (b["lod"] >= fhl - 0.1 * atr)
        m &= (K > D) & (Kp <= Dp) & (K < 20) & (D < 20)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
