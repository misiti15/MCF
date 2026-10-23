"""pod-r3-williams-smash-day-pdh-reversal-long - Larry Williams Smash Day (buy): yesterday closed below the
day-before's low, today reclaims yesterday's high (LONG).

Source: Larry Williams Smash Day reversal (Oxford Strategies backtest rules; RoboForex summary: buy above the
smash-day high, stop below its low, best when it ends a correction in an uptrend).
URL: https://roboforex.com/blog/education/catch-your-smash-day-with-larry-williams/

VARIANT of cwt-a-a3-pdh-breakout-day2 and pod-cwt2-barrett-pdh-break-otf-confirm-long (opposite day context: D-1 is
a smash DOWN day, so the PDH break is a reversal). Also a sibling of pod-williams-smash-day-pdh-long (r2_5); stated
differences from it: the OR form of the smash definition below, a 10-session / 5m-SMA50 trend filter instead of the
daily SMA50 + 8-day-low gate, an SPY gate, a 10:00-13:30 window, a LOD/PDH-based stop and no target.
Rules (plain English, LONG):
  1. Smash setup (lib.daily(), completed days): D-1 close < D-2 low, OR (D-1 close in the bottom 25% of the D-1
     range AND D-1 close < D-2 close).
  2. Correction in an uptrend: the close 10 sessions back (D-10) < D-1 close, OR sma50_dist_pct > -0.5 on the first
     frame bar of the day (09:50; the frame has no 09:30 bar - declared harness limit).
  3. Trigger: the FIRST 5m close of the day above the PDH (previous bar closed at or below it; full-session 09:35+
     bars checked so an earlier close above PDH disqualifies the day), with volumeRatio >= 1.2.
  4. spy_fo > -0.3. Bar close 10:00-13:30. Entry at that bar's close.
  Stop (GEOM S): max(today's LOD, PDH - 0.75 x atr_d) - 0.05 x atr_d. Target: none (hold to 15:55).
  The t1s1 comparison the idea asks for is scored separately as pod-r3-williams-smash-day-pdh-reversal-long-t1s1
  (2 configurations for this idea). No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1330)
CONTEXT = ["spy_fo"]
LAYERS = ["smash D-1: c1 < l2 or (c1 bottom 25% of range and c1 < c2)", "c10 < c1 or sma50_dist_pct > -0.5 at open",
          "first close above PDH, volumeRatio >= 1.2", "spy_fo > -0.3", "stop max(LOD, PDH-0.75ATR)-0.05ATR, no target"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r25_util as R25  # noqa: E402
import _r29_util as U  # noqa: E402

_ST = {}


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[i])


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    _ST[id(df)] = stop
    if not n or "spy_fo" not in df:
        return z
    b = U.base(df)
    k = U.key(df)
    d = R25.map_daily(df, k, ["h1", "l1", "c1", "l2", "c2"])
    c10 = U.map_c10(df, k)
    atr, c, tod = b["atr"], b["c"], b["tod"]
    st = U.start(k)
    sma50_open = U.f(df, "sma50_dist_pct")[st][np.cumsum(st) - 1]
    first_tod = tod[st][np.cumsum(st) - 1]
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = d["h1"] - d["l1"]
        smash = (d["c1"] < d["l2"]) | ((rng > 0) & ((d["c1"] - d["l1"]) <= 0.25 * rng) & (d["c1"] < d["c2"]))
        trend = (c10 < d["c1"]) | ((first_tod == 950) & (sma50_open > -0.5))
        day_ok = smash & trend & np.isfinite(b["pdh"]) & (atr > 0)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].to_numpy()[st],
                      "pdh": b["pdh"][st], "ok": day_ok[st]})
    u = u[u["ok"]]
    if not len(u):
        return z
    fb = U.CB.full_bars(df, symbols=sorted(set(u["symbol"])))
    if fb is None:
        return z
    j = fb.merge(u[["symbol", "date", "pdh"]], on=["symbol", "date"], how="inner")
    j = j[(j["tod"] <= 1330) & (j["c"] > j["pdh"])]
    first = j.groupby(["symbol", "date"], sort=False)["tod"].min().rename("ftod").reset_index()
    kk = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    ftod = kk.merge(first, on=["symbol", "date"], how="left")["ftod"].to_numpy(float)
    dp = U.f(df, "dist_pdh_atr")
    with np.errstate(invalid="ignore"):
        m = day_ok & (tod == ftod) & (dp <= 0) & (U.lag(dp, k) > 0)
        m &= U.f(df, "volumeRatio") >= 1.2
        m &= U.f(df, "spy_fo") > -0.3
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop[:] = np.maximum(b["lod"], b["pdh"] - 0.75 * atr) - 0.05 * atr
        m &= stop < c
    return np.asarray(m, bool)
