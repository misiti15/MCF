"""pod-hill-iwm-leads-reversal-long - Small caps lead the intraday reversal: the IWM/SPY ratio turns up first, then
SPY breaks its prior 30-min high (LONG SPY).

Source: Arthur Hill, StockCharts Art's Charts, 'Small-caps Lead Intraday Reversal' (Oct 2014).
URL: https://articles.stockcharts.com/article/articles-arthurhill-2014-10-small-caps-lead-intraday-reversal-/

NEW (cross-ETF leadership trigger; the earlier RS-hold setups compare a stock to the index, not small caps to large
caps).
Rules (plain English, LONG). Traded symbol: SPY (the companion file -iwm- trades IWM on the same signal, as the source
idea asks 'also test IWM').
  1. Arming bar: a 5-min close between 11:00 and 13:30 ET where SPY is down >= 0.5% from its open (fromOpen).
  2. On that bar the IWM/SPY 5-min close ratio is >= 0.30% above its session low so far (ratio from full-session
     bars, 09:35 on), and IWM closes above its own session VWAP.
  3. On that bar SPY is still below its session VWAP (the laggard).
  4. SPY's daily close yesterday > its daily SMA50 (lib.daily(), completed days).
  Entry: the first 5-min close of the traded ETF above the highest high of its previous 6 bars (prior 30 min), at or
  after the first arming bar, bar close 11:30-14:30. One trade per day.
  Stop (GEOM S): traded ETF's session low - 0.05 x atr_d. Target: its prior close, or entry + 2R if that is nearer
  (2R when the prior close is not above the entry). Flat 15:55.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1130, 1430)
TRADE = "SPY"
SYMBOLS = ["SPY", "IWM"]
LAYERS = ["armed 11:00-13:30: SPY fromOpen <= -0.5%", "IWM/SPY ratio >= 0.30% above its session low, IWM > VWAP",
          "SPY < VWAP", "SPY D-1 close > SMA50", "first close > prior 6-bar high, 11:30-14:30",
          "stop LOD - 0.05 ATR, target min(prior close, 2R)"]

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


def _arm(df, b, k):
    """Dates -> first arming tod (SPY + IWM, point in time)."""
    sym = df["symbol"].astype(str).to_numpy()
    d = U.map_daily(df, k, ["c1", "sma50_1"])
    cols = {}
    for s in ("SPY", "IWM"):
        sel = sym == s
        if not sel.any():
            return None
        cols[s] = pd.DataFrame({"date": df["date"].astype(str).to_numpy()[sel], "tod": b["tod"][sel],
                                "c": b["c"][sel], "fo": U.f(df, "fromOpen")[sel], "vd": U.f(df, "vwapDistPct")[sel],
                                "trend": (d["c1"] > d["sma50_1"])[sel]}).drop_duplicates(["date", "tod"])
    fb = U.full_bars(df, symbols=["SPY", "IWM"])
    if fb is None:
        return None
    fb = fb.copy()
    fb["date"] = fb["date"].astype(str)
    p = fb.pivot_table(index=["date", "tod"], columns="symbol", values="c").reset_index()
    if "SPY" not in p or "IWM" not in p:
        return None
    p = p.sort_values(["date", "tod"])
    p["ratio"] = p["IWM"] / p["SPY"]
    p["rlow"] = p.groupby("date")["ratio"].cummin()
    a = cols["SPY"].merge(cols["IWM"][["date", "tod", "vd"]].rename(columns={"vd": "ivd"}), on=["date", "tod"])
    a = a.merge(p[["date", "tod", "ratio", "rlow"]], on=["date", "tod"], how="left")
    with np.errstate(invalid="ignore"):
        ok = (a["tod"] >= 1100) & (a["tod"] <= 1330) & (a["fo"] <= -0.5)           # (1)
        ok &= (a["ratio"] >= a["rlow"] * 1.003) & (a["ivd"] > 0)                     # (2)
        ok &= a["vd"] < 0                                                           # (3)
        ok &= a["trend"].astype(bool)                                               # (4)
    a = a[ok.to_numpy()]
    return a.groupby("date")["tod"].min().rename("atod").reset_index()


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
    arm = _arm(df, b, k)
    if arm is None or not len(arm):
        return z
    atod = pd.DataFrame({"date": df["date"].astype(str).to_numpy()}).merge(arm, on="date", how="left")["atod"]
    atod = atod.to_numpy(float)
    tod, c, h, atr = b["tod"], b["c"], b["h"], b["atr"]
    hh = np.vstack([U.lag(h, k, j) for j in range(1, 7)])
    with np.errstate(invalid="ignore"):
        hi6 = np.max(hh, axis=0)                                     # NaN if any missing
        m = (df["symbol"].astype(str).to_numpy() == TRADE) & np.isfinite(atod) & (tod >= atod)
        m &= c > hi6
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop[:] = b["lod"] - 0.05 * atr
        r = c - stop
        pc = b["pc"]
        tgt[:] = np.where(pc > c, np.minimum(pc, c + 2 * r), c + 2 * r)
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
