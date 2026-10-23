"""pod-cwt3-cady-balance-ma-converge-break-long - Balance-to-vertical: flat converged 30-min MAs, then a break of the
2-day range (LONG).

Source: Chat With Traders EP235, Chris Cady (A Lifetime Student of Markets; balance to vertical) [~00:57:11].
URL: https://chatwithtraders.com/235

New in MCF: the trigger is a moving-average CONVERGENCE state on 30-min bars, not a bar-range coil (CWT12) or an NR7
day (both already tested).

Rules (plain English, LONG). Universe: the scorer universe with adv20 >= $100M (index / sector ETFs and liquid large
caps; pre-declared liquidity floor).
  30-min bars (09:30-10:00 ... 15:30-16:00) are built from continuous full-session 5m closes (frames + head/tail
  table, previous open month as warm-up); SMA33 and SMA65 of the 30-min closes, rolling across days. At a 5m decision
  bar only the latest COMPLETED 30-min bar is used.
  (1) Balance: |SMA33 - SMA65| / close <= 0.15% for the ETFs (_cwt3_bars.ETFS), 0.30% for everything else;
  (2) flat: |SMA33(k) - SMA33(k-5)| / 5 and |SMA65(k) - SMA65(k-5)| / 5 are each <= 0.05% of the close per 30-min bar;
  (3) trigger: the 5m bar closes above the 2-day balance high max(high D-1, high D-2) (completed days) while the
      previous 5m bar closed at or below it (a fresh break), bar close 10:00-14:30 ET;
  (4) 5m volume >= 1.5 x its 20-bar average (volumeRatio).
  Entry: the trigger bar's close. Stop (GEOM S+ts2): the 2-day high - 0.25 x ATR14(5m) (the source's 'back inside the
  range' close rule, applied as a price stop). Exit when it stops extending, proxied by the scorer's bailout: flat at
  the close of bar i+3 if no bar since entry made a high above the entry bar's high (BAILOUT_BARS = 3, pre-declared
  from the source's 3 non-extending bars); else flat 15:55. No target.
  The pyramiding add (second unit on a new session high within 30 minutes) cannot be modelled by the one-unit
  scorer: this is the WITHOUT-add result only.
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar and completed
daily bars are used.
Educational only - not financial advice."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S+ts2"
BAILOUT_BARS = 3
BE_AT_R = 0.0
WINDOW = (1000, 1430)
MIN_ADV = 100e6
CONTEXT = []
LAYERS = ["30m SMA33 vs SMA65 within 0.15% (ETF) / 0.30%", "both 30m SMAs flat (<= 0.05%/bar over 5 bars)",
          "fresh 5m close above the 2-day high, 10:00-14:30", "volumeRatio >= 1.5",
          "stop 2-day high - 0.25 ATR5, bailout after 3 non-extending bars"]

_ST = {}


def _u():
    n = "_cwt3_bars"
    if n not in sys.modules:
        sp = importlib.util.spec_from_file_location(n, Path(__file__).resolve().parent / "_cwt3_bars.py")
        m = importlib.util.module_from_spec(sp)
        sys.modules[n] = m
        sp.loader.exec_module(m)
    return sys.modules[n]


def _mins(t):
    t = np.asarray(t, np.int64)
    return (t // 100) * 60 + t % 100


def _compute(df):
    U = _u()
    n = len(df)
    z0 = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n:
        return z0
    p = U.full_bars(df)
    if p is None or not len(p):
        return z0
    p = p[["symbol", "date", "tod", "c"]].copy()
    p["bk"] = -(-_mins(p["tod"].to_numpy()) // 30) * 30                    # 30-min bucket END, minutes
    g = p.groupby(["symbol", "date", "bk"], sort=True)["c"].last().reset_index()
    gs = g.groupby("symbol", sort=False)["c"]
    g["s33"] = gs.transform(lambda x: x.rolling(33, min_periods=33).mean())
    g["s65"] = gs.transform(lambda x: x.rolling(65, min_periods=65).mean())
    g["s33p"] = g.groupby("symbol", sort=False)["s33"].shift(5)
    g["s65p"] = g.groupby("symbol", sort=False)["s65"].shift(5)
    g = g.rename(columns={"c": "c30"})
    tod = df["tod"].to_numpy(np.int64)
    kk = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(object), "date": df["date"].to_numpy(),
                       "bk": (_mins(tod) // 30) * 30})                     # latest COMPLETED bucket
    mm = kk.merge(g, on=["symbol", "date", "bk"], how="left")
    assert len(mm) == n
    s33, s65, s33p, s65p, c30 = (mm[x].to_numpy(float) for x in ("s33", "s65", "s33p", "s65p", "c30"))
    b = U.base(df)
    k = U.key(df)
    c, a5 = b["c"], b["atr5"]
    d = U.map_daily(df, k, ["d_high_1", "d_high_2"])
    etf = np.isin(df["symbol"].astype(str).to_numpy(), U.ETFS)
    with np.errstate(invalid="ignore", divide="ignore"):
        conv = np.abs(s33 - s65) / c30 * 100 <= np.where(etf, 0.15, 0.30)             # (1)
        flat = (np.abs(s33 - s33p) / 5 / c30 * 100 <= 0.05) & (np.abs(s65 - s65p) / 5 / c30 * 100 <= 0.05)  # (2)
        hi2 = np.fmax(d["d_high_1"], d["d_high_2"])
        hi2 = np.where(np.isfinite(d["d_high_1"]) & np.isfinite(d["d_high_2"]), hi2, np.nan)
        c1 = U.lag(c, k)
        m = conv & flat & (c > hi2) & (c1 <= hi2)                                     # (3)
        m &= U.f(df, "volumeRatio") >= 1.5                                            # (4)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = hi2 - 0.25 * a5
        tgt = np.full(n, np.nan)
        m &= np.isfinite(stop) & (stop < c)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        n = len(df)
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])
