"""pod-qtr-end-window-dressing-winner-pm-long - Quarter-end window-dressing: six-month winners bought in the last hour
(LONG).

Source: Schaeffer's Research 'Indicator of the week: how window dressing can help you pick winners' (2015-09-16):
the top prior-6-month performers averaged +0.22% vs -0.39% for the losers over a quarter's last two weeks; Wharton
study (funds beat the S&P on the quarter's last day, then lag).
URL: https://www.schaeffersresearch.com/content/analysis/2015/09/16/indicator-of-the-week-how-window-dressing-can-help-you-pick-winners

VARIANT of pod-cal-tom-vwap-pullback-stock-long and pod-cal-monthend-rebalance-contra-index. Stated change:
quarter-end only, a cross-sectional six-month-winner selection and a last-hour window (fund buying into the marking
close, not the turn-of-month inflow).

Rules (plain English, LONG). Universe: adv20 >= $50M, price >= $10.
  1. Today is one of the last 2 trading days of March / June / September / December (exchange calendar, known in
     advance; taken from the SPY daily dates).
  2. The stock is in the top decile of the universe (adv20 >= $50M and close >= $10 at D-1) by its ~126-day
     (six-month) return as of the D-1 close. The return is D-1 close / the close nearest to D-1 minus 182 calendar
     days (within 75 days) - 1, because 126 trading-day counting cannot cross the rule-19 locked block: for the
     2025-03 and 2025-06 quarter ends the base close is the nearest OPEN date (2024-10-01 / 2024-10-31); no locked
     row is read.
  3. At the 14:55 bar (bar closing 14:55): close > session VWAP and fromOpen >= 0.
  4. SPY fromOpen >= -0.5% at the 14:55 bar (context spy_fo; no broad selloff).
  Entry: the close of the bar closing 15:00. Stop (GEOM S): entry - 0.35 x atr_d. No target; flat 15:55.
Low frequency (two days per quarter, 7 open quarter ends). No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r26_bars as RB  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1500, 1500)
MIN_ADV = 50e6
CONTEXT = ["spy_fo"]
LAYERS = ["last 2 trading days of a quarter", "top decile 6-month return at D-1 (adv >= $50M, px >= $10)",
          "14:55 bar: close > VWAP, fromOpen >= 0", "SPY fromOpen >= -0.5% at 14:55",
          "entry 15:00 close, stop entry - 0.35 ATR, flat 15:55"]
_ST = {}
_C = {}


def _winners():
    """{date str D: set of top-decile symbols} for the last 2 trading days of each quarter month."""
    if "w" in _C:
        return _C["w"]
    d = RB.daily()
    cal = sorted(d.loc[d["symbol"] == "SPY", "date"].unique())
    cal_s = pd.Series(pd.to_datetime(cal))
    ym = cal_s.dt.strftime("%Y-%m")
    qdays = []
    for m, g in cal_s.groupby(ym):
        if int(m[5:7]) in (3, 6, 9, 12):
            qdays += [x.strftime("%Y-%m-%d") for x in g.sort_values().iloc[-2:]]
    pos = {x: i for i, x in enumerate(cal)}
    out = {}
    for D in qdays:
        i = pos[D]
        if i == 0:
            continue
        D1 = cal[i - 1]
        if (pd.Timestamp(D) - pd.Timestamp(D1)).days > 7:
            continue
        x = d[d["date"] == D1][["symbol", "close", "adv20"]]
        x = x[(x["adv20"] >= 50e6) & (x["close"] >= 10)]
        tgt = pd.Timestamp(D1) - pd.Timedelta(days=182)
        lo, hi = (tgt - pd.Timedelta(days=75)).strftime("%Y-%m-%d"), (tgt + pd.Timedelta(days=75)).strftime("%Y-%m-%d")
        h = d[(d["date"] >= lo) & (d["date"] <= hi)][["symbol", "date", "close"]].copy()
        h["dist"] = (pd.to_datetime(h["date"]) - tgt).dt.days.abs()
        h = h.sort_values(["symbol", "dist", "date"]).drop_duplicates("symbol")
        x = x.merge(h[["symbol", "close"]].rename(columns={"close": "c0"}), on="symbol", how="inner")
        x["ret"] = x["close"] / x["c0"] - 1
        x = x[np.isfinite(x["ret"])]
        if len(x) < 50:
            continue
        thr = x["ret"].quantile(0.9)
        out[D] = set(x.loc[x["ret"] >= thr, "symbol"])
    _C["w"] = out
    return out


def _compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    if "spy_fo" not in df or not n:
        return m, stop
    W = _winners()
    ds = pd.Series(df["date"].to_numpy()).astype(str).to_numpy()
    sy = df["symbol"].astype(str).to_numpy()
    sel = np.array([(d in W) and (s in W[d]) for d, s in zip(ds, sy)], bool)
    if not sel.any():
        return m, stop
    tod = df["tod"].to_numpy(np.int64)
    c = df["close"].to_numpy(float)
    vd = df["vwapDistPct"].to_numpy(float)
    fo = df["fromOpen"].to_numpy(float)
    spy = df["spy_fo"].to_numpy(float)
    atr = df["atr_d"].to_numpy(float)
    k = pd.factorize(pd.Series(sy) + "|" + pd.Series(ds))[0]
    same = np.r_[False, k[1:] == k[:-1]]
    pt = np.r_[0, tod[:-1]]
    pv, pf, ps = np.r_[np.nan, vd[:-1]], np.r_[np.nan, fo[:-1]], np.r_[np.nan, spy[:-1]]
    with np.errstate(invalid="ignore"):
        m = sel & (tod == 1500) & same & (pt == 1455) & (pv > 0) & (pf >= 0) & (ps >= -0.5) & (c >= 10)
        stop = np.where(m, c - 0.35 * atr, np.nan)
    return m, stop


def mask(df) -> np.ndarray:
    m, stop = _compute(df)
    _ST.clear()
    _ST[id(df)] = stop
    return np.asarray(m, bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
