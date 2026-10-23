"""pod-williams-smash-day-pdh-long - Larry Williams smash-day reversal: buy the break of the smash day's high (LONG).

Source: Larry Williams smash-day patterns (Long-Term Secrets to Short-Term Trading), as summarised by RoboForex
'Catch your smash day with Larry Williams' and the RogueQuant 15-market backtest.
URL: https://roboforex.com/blog/education/catch-your-smash-day-with-larry-williams/

VARIANT of pod-traderlion-insideday-pdh-long (PDH break after an inside day). Stated change: the prior-day condition
is a Williams smash day instead of an inside day, with a daily-uptrend (SMA50) gate.

Rules (plain English, LONG). Universe: liquid stocks and index / sector ETFs with adv20 >= $50M.
  1. Smash day D-1 (lib.daily(), completed days): D-1 close < D-2 low AND D-1 low <= the lowest low of D-8..D-2.
     (Hidden-smash sub-config, scored separately as pod-williams-smash-day-pdh-long-hidden: D-1 close > D-2 close but
     D-1 close in the bottom 25% of the D-1 range, with the same D-1 low <= lowest low of D-8..D-2 condition.)
  2. D-1 close > daily SMA50 as of D-1 (a correction inside an uptrend).
  3. Today's open <= PDH (no gap over the trigger).
  4. The FIRST 5-minute close above PDH among bars closing 09:40-13:00 (full-session bars), and that bar has
     volumeRatio >= 1.2. Entry: that bar's close.
  Stop (GEOM S): max(D-1 low, entry - 0.6 x atr_d). Target: entry + 1.0 x (entry - stop); else flat 15:55.
Harness limit (declared): the frames start at the 09:50 bar (volumeRatio too), so a first close above PDH at 09:40 /
09:45 cannot be entered and the day is skipped. No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1300)
MIN_ADV = 50e6
HIDDEN = False
LAYERS = ["smash day D-1: close < D-2 low, low <= LL(D-8..D-2)", "D-1 close > SMA50", "open <= PDH",
          "first close > PDH 09:40-13:00 with volumeRatio >= 1.2", "stop max(D-1 low, entry - 0.6 ATR), target 1R"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r25_util as U  # noqa: E402

_ST = {}


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def target_price(f, i, stop):
    return _stash(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n:
        return z
    b = U.base(df)
    k = U.key(df)
    d = U.map_daily(df, k, ["h1", "l1", "c1", "l2", "c2", "ll2_8", "sma50_1"])
    atr = b["atr"]
    with np.errstate(invalid="ignore", divide="ignore"):
        if HIDDEN:
            rng = d["h1"] - d["l1"]
            day_ok = (d["c1"] > d["c2"]) & (rng > 0) & ((d["c1"] - d["l1"]) <= 0.25 * rng)
        else:
            day_ok = d["c1"] < d["l2"]
        day_ok &= d["l1"] <= d["ll2_8"]                                     # (1)
        day_ok &= d["c1"] > d["sma50_1"]                                    # (2)
        day_ok &= b["opn"] <= b["pdh"]                                      # (3)
        day_ok &= np.isfinite(b["pdh"]) & (atr > 0)
    st = U.start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].to_numpy()[st],
                      "pdh": b["pdh"][st], "ok": day_ok[st]})
    u = u[u["ok"]]
    if not len(u):
        return z
    fb = U.full_bars(df, symbols=sorted(set(u["symbol"])))
    if fb is None:
        return z
    j = fb.merge(u[["symbol", "date", "pdh"]], on=["symbol", "date"], how="inner")
    j = j[(j["tod"] >= 940) & (j["tod"] <= 1300) & (j["c"] > j["pdh"])]
    first = j.groupby(["symbol", "date"], sort=False)["tod"].min().rename("ftod").reset_index()
    kk = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    ftod = kk.merge(first, on=["symbol", "date"], how="left")["ftod"].to_numpy(float)
    tod = b["tod"]
    c = b["c"]
    with np.errstate(invalid="ignore"):
        m = day_ok & (tod == ftod) & (tod >= 950) & (tod <= 1300) & (c > b["pdh"])          # (4)
        m &= U.f(df, "volumeRatio") >= 1.2
        stop[:] = np.maximum(d["l1"], c - 0.6 * atr)
        tgt[:] = c + 1.0 * (c - stop)
        m &= stop < c
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
