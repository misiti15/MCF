"""pod-hyg-nonconfirm-spy-newlow-long - Credit non-confirmation: SPY makes a new LOD while HYG holds its low (LONG).

Source: Tim Ord / StockCharts and SeeItMarket HYG-SPY divergence commentary; TradingView 'BULLISH signal flash with
2008 failure example'.
URL: https://seeitmarket.com/?p=29634

VARIANT of pod-vixy-nonconfirm-index-newlow-long (and pod-axia-spy-newlow-divergence-long). What changes: the
confirming instrument is high-yield credit (HYG, alternatively JNK) instead of VIX/VIXY or another index; new feature
family.
Rules (plain English, LONG; SPY and QQQ each on its own bars, 5m bars 09:35..15:00):
  1. New-low bar j (bar close 10:30-14:30 ET): low_j <= the running session LOD before bar j x (1 - 0.15%), and that
     prior LOD was set >= 30 minutes (6 bars) before bar j.
  2. At bar j, HYG's bar-j low stays >= 0.03% ABOVE HYG's own session LOD so far (no new HYG low), and HYG's close is above its prior-day close or within 0.10% of it.
  3. The traded ETF's daily close yesterday > its daily SMA50 (completed days).
  4. Within 4 bars after j, a 5m close above the high of bar j. Entry: that close.
  Stop (GEOM S): the session LOD at entry - 0.05%. Target: session VWAP when it is above the entry and below
  entry + 1.5R, else entry + 1.5R (whichever comes first). Flat 15:55.
CONTROL (the -ctrl-nohyg module, NEED_HYG = False): the same SPY / QQQ new-low reclaim without condition 2.
DATA: neither HYG nor JNK (nor any other credit ETF) is in the open history or the 1-minute cache, so condition 2
cannot be evaluated; this module then returns no bars (0 trades, by design - fail-safe). Only the control can score.
No tweak used. No tuning on valid. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision
bar are used. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r311_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1035, 1450)
SYMBOLS = ["SPY", "QQQ"]
NEED_HYG = True
CREDIT = ["HYG", "JNK"]
LAYERS = ["new LOD >= 0.15% below a LOD set >= 30 min earlier, 10:30-14:30",
          "HYG low >= 0.03% above its LOD, HYG >= prior close - 0.10%", "D-1 close > SMA50",
          "close > new-low bar high within 4 bars", "stop LOD - 0.05%, target VWAP or 1.5R, flat 15:55"]
_S = U.Stash()


@numba.njit(cache=False)
def _kern(nd, tod, o, h, l, c, v, atr, ok_hyg, ok_d):
    n = len(c)
    m = np.zeros(n)
    s = np.full(n, np.nan)
    t = np.full(n, np.nan)
    lod = np.nan
    lodi = 0
    pv = 0.0
    vv = 0.0
    sig = -1
    for i in range(n):
        if nd[i] >= 1:
            lod = np.nan
            lodi = i
            pv = 0.0
            vv = 0.0
            sig = -1
        pv += (h[i] + l[i] + c[i]) / 3.0 * v[i]
        vv += v[i]
        vw = pv / vv if vv > 0 else np.nan
        # entry check against an earlier signal bar
        if sig >= 0 and i > sig:
            if i - sig > 4:
                sig = -1
            elif c[i] > h[sig] and ok_d[i] == 1.0:
                cur_lod = min(lod, l[i])
                stop = cur_lod * (1 - 0.0005)
                e = c[i]
                R = e - stop
                tg = e + 1.5 * R
                if vw == vw and vw > e and vw < tg:
                    tg = vw
                if R > 0:
                    m[i] = 1.0
                    s[i] = stop
                    t[i] = tg
                sig = -1
        # new-low signal on this bar
        if lod == lod and tod[i] >= 1030 and tod[i] <= 1430 and l[i] <= lod * (1 - 0.0015) and i - lodi >= 6 \
                and ok_hyg[i] == 1.0:
            sig = i
        if lod != lod or l[i] < lod:
            lod = l[i]
            lodi = i
    return m, s, t


def _hyg_ok(df, X):
    """1.0 where the credit ETF does NOT confirm (holds >= 0.03% above its LOD and is >= prior close - 0.10%)."""
    if not NEED_HYG:
        return np.ones(len(X))
    for sym in CREDIT:
        B = U.sym_bars(df, [sym])
        if len(B):
            # r24 bars carry only the close: the bar low is approximated by the close (pre-declared, never reached
            # with the current data)
            B = B.copy()
            B["lod"] = B.groupby("dn")["c"].cummin()
            d = U.daily_of(sym, ["c1"])
            B = B.merge(d, on="date", how="left")
            B["ok"] = ((B["c"] >= B["lod"] * 1.0003) & (B["c"] >= B["c1"] * (1 - 0.0010))).astype(float)
            return np.nan_to_num(U.map_dt(X, B, ["ok"])["ok"])
    return np.zeros(len(X))


def mask(df) -> np.ndarray:
    n = len(df)
    nanv = np.full(n, np.nan)
    _S.put(df, s=nanv, t=nanv)
    X = U.vbars(df)
    if X is None or not len(X) or not n:
        return np.zeros(n, bool)
    oh = _hyg_ok(df, X)
    if not oh.any():
        return np.zeros(n, bool)
    dd = U.daily_tab()
    k = pd.DataFrame({"symbol": X["symbol"].astype(str).to_numpy(), "date": X["date"].astype(str).to_numpy()})
    mm = k.merge(dd[["symbol", "date", "c1", "sma501"]], on=["symbol", "date"], how="left")
    od = (mm["c1"] > mm["sma501"]).to_numpy(float)
    r = U.run_kernel(df, _kern, extra=(oh, od), cols=("m", "s", "t"))
    _S.put(df, s=r["s"], t=r["t"])
    tod = df["tod"].to_numpy(np.int64)
    return np.asarray(r["m"] & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)


def stop_price(f, i):
    return float(_S.get(f, "s", mask)[i])


def target_price(f, i, stop):
    return float(_S.get(f, "t", mask)[i])
