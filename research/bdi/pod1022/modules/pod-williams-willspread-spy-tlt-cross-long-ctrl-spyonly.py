"""pod-williams-willspread-spy-tlt-cross-long-ctrl-spyonly - CONTROL (CTRL = True: SPY alone, no TLT leg) of Will-Spread SPY/TLT intermarket zero-cross long (bonds lead stocks).

Source: Larry Williams, 'Long-Term Secrets to Short-Term Trading' (Will-Spread); TradingView community script
Rak6df4K.
URL: https://www.tradingview.com/script/Rak6df4K

NEW feature family (no TLT or bond-ratio setups in the backlog).
Rules (plain English, LONG; traded symbols SPY and QQQ, each on its own bars):
  R = 100 x SPY / TLT on synchronized 5m closes (09:35..15:00 bars, carried across sessions); WS = EMA5(R) - EMA20(R).
  1. WS crosses from <= 0 to > 0 on the cross bar, whose close is 10:15-14:30 ET.
  2. At the cross bar SPY is above its prior-day close or above its session VWAP.
  3. Williams' filter: the NEXT 5m bar trades above the cross-bar high (buy-stop at cross-bar high + 1 tick, valid 1
     bar). Harness: entry at the close of that next bar, which must close above the trigger.
  4. Skip when TLT is up > +0.8% on the day at the cross bar (TLT close vs its prior-day close).
  Stop (GEOM S+x): the lower of the cross-bar low and the 6-bar swing low (cross bar and the 5 before it), but never
  more than 1 x ATR5m(14) below the entry (cap). Target +1.5R. Exit at the close of the first later bar on which WS
  closes back below 0; flat 15:55.
CTRL = True (the -ctrl-spyonly module) replaces R by SPY alone (EMA5 - EMA20 of the SPY close) to show whether the
bond leg adds information. The optional high-beta stock leg is not run. No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used for the entry.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r311_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+x"
WINDOW = (1020, 1435)
SYMBOLS = ["SPY", "QQQ"]
CTRL = True
LAYERS = ["WS = EMA5(100 SPY/TLT) - EMA20 crosses above 0, cross bar 10:15-14:30",
          "SPY above prior close or above VWAP at the cross", "next bar closes above cross-bar high + 1c",
          "TLT day change <= +0.8%", "stop min(cross low, 6-bar low) capped at 1 ATR5, target 1.5R, exit WS < 0"]
_S = U.Stash()


def _ws(df):
    B = U.sym_bars(df, ["SPY", "TLT"])
    if not len(B):
        return None
    P = B.pivot_table(index=["dn", "date", "tod"], columns="symbol", values="c").reset_index()
    if "SPY" not in P or "TLT" not in P:
        return None
    P = P.sort_values(["dn", "tod"]).dropna(subset=["SPY", "TLT"]).reset_index(drop=True)
    r = P["SPY"] if CTRL else 100.0 * P["SPY"] / P["TLT"]
    P["ws"] = (r.ewm(span=5, adjust=False).mean() - r.ewm(span=20, adjust=False).mean()).to_numpy()
    P.loc[P.index < 40, "ws"] = np.nan                                   # warm-up
    P["tlt"] = P["TLT"]
    return P


def mask(df) -> np.ndarray:
    n = len(df)
    z = np.zeros(n, bool)
    nanv = np.full(n, np.nan)
    _S.put(df, s=nanv, t=nanv, ws=nanv)
    if not n:
        return z
    P = _ws(df)
    if P is None:
        return z
    k = U.key(df)
    b = U.base(df)
    w = U.map_dt(df, P, ["ws", "tlt"])
    ws = w["ws"]
    tl = U.daily_of("TLT", ["c1"])
    tlt_c1 = U.map_date(df, tl, ["c1"])["c1"]
    spy = U.spy_rows(df, ["fromOpen", "gap", "vwapDistPct"])
    with np.errstate(invalid="ignore", divide="ignore"):
        spy_pc = (1 + spy["fromOpen"] / 100) * (1 + spy["gap"] / 100) - 1
        spy_ok = (spy_pc > 0) | (spy["vwapDistPct"] > 0)
        tlt_ok = (w["tlt"] / tlt_c1 - 1) <= 0.008
        cross = (ws > 0) & (U.lag(ws, k, 1) <= 0) & spy_ok & tlt_ok
        tod = b["tod"]
        cross &= (tod >= 1015) & (tod <= 1430)
        x1 = U.lag(cross.astype(float), k, 1) == 1.0
        hx = U.lag(b["h"], k, 1)
        lx = U.lag(b["l"], k, 1)
        swing = np.min(np.vstack([U.lag(b["l"], k, j) for j in range(1, 7)]), axis=0)
        trig = hx + 0.01
        m = x1 & (b["h"] >= trig) & (b["c"] > trig)
        c = b["c"]
        stop = np.minimum(lx, swing)
        stop = np.maximum(stop, c - 1.0 * b["atr5"])
        tgt = c + 1.5 * (c - stop)
        m &= np.isfinite(stop) & (stop < c)
    _S.put(df, s=stop, t=tgt, ws=ws)
    return np.asarray(m, bool)


def stop_price(f, i):
    return float(_S.get(f, "s", mask)[i])


def target_price(f, i, stop):
    return float(_S.get(f, "t", mask)[i])


def exit_index(f, i, stop, target):
    ws = _S.get(f, "ws", mask)
    sym, d = f["symbol"].iat[i], f["date"].iat[i]
    j = i + 1
    while j < len(f) and f["symbol"].iat[j] == sym and f["date"].iat[j] == d:
        if ws[j] < 0:
            return j
        j += 1
    return -1
