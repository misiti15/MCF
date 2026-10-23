"""pod-charm-preopex-week-pm-vwap-hold-index-long-ctrl-nonopex - CONTROL (OPEX = False: Mon-Thu of non-opex weeks) of Pre-OpEx-week charm/vanna grind: afternoon VWAP hold on SPY / QQQ /
IWM, Monday-Thursday before the monthly expiry (LONG).

Source: eksOr 'Charm/Vanna Window' (TradingView script) and the LuxAlgo 'Vanna & Charm flows' concept page (Cem Karsan
style dealer-flow commentary).
URL: https://www.tradingview.com/script/mvEJiFm7-eksOr-Charm-Vanna-Window-Monthly-OPEX

VARIANT of the opex family (parents pod-cal-opex-friday-strike-pin-fade and pod-options-strike-pin-magnet-long). What
changes: the window is the sessions BEFORE monthly expiry, not opex Friday; long only; drift rather than a pin.
Rules (plain English, LONG; SPY, QQQ, IWM each on its own bars, one trade per day per ETF):
  1. Date: Monday-Thursday of the week whose Friday is the third-Friday monthly expiry (when that Friday is an NYSE
     holiday the expiry is Thursday, and the window is Monday-Wednesday).
  2. Vol falling: VXX at the 13:00 bar close < VXX's prior-day close, and VXX's prior-day close < the median of its
     last 20 daily closes (D-20..D-1). VIX itself is not in the history; VXX (front VIX futures) is the declared proxy.
  3. Quiet: SPY's 09:30-13:00 range < 1.0 x the mean of the same 09:30-13:00 range over the 20 prior sessions.
  4. Between 13:00 and 15:00 ET the ETF pulls back to VWAP: a bar whose low is within 0.05% of session VWAP (or
     through it) after the 13:00 close was above VWAP + 0.05% (a pull BACK), and no 5m close since 13:00 more than
     0.10% below VWAP (the day is dropped once that happens).
  Entry: the first 5m close above the prior 5m bar's high on a bar after the touch (bar close <= 15:00).
  Stop (GEOM S): session VWAP - 0.6 x ATR5m(14) at the entry bar. Target +1.2R; otherwise flat 15:55 (MOC drift).
CONTROL (the -ctrl-nonopex module, OPEX = False): the same rules on Monday-Thursday of every other week. The edge
exists only if opex weeks beat that control after costs.
Pre-declared choices: the '13:00 close above VWAP + 0.05%' reading of 'pulls back'; VXX as the VIX proxy. No tweak
used. No tuning on valid. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are
used. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r311_util as U  # noqa: E402
import _r24_bars as R24  # noqa: E402
import _r25_util as U25  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1305, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM"]
OPEX = False
LAYERS = ["Mon-Thu of monthly opex week", "VXX 13:00 < VXX prior close, VXX D-1 close < 20d median",
          "SPY 09:30-13:00 range < 20d mean", "13:00 close > VWAP+0.05%, later bar low <= VWAP+0.05%",
          "no close < VWAP-0.10% since 13:00", "entry close > prior bar high after the touch",
          "stop VWAP - 0.6 ATR5, target 1.2R, flat 15:55"]
HOLIDAYS = {"2025-04-18", "2026-04-03", "2026-06-19"}
_S = U.Stash()
_MEM = {}


def _gate_days():
    opex, other = set(), set()
    for ms in pd.date_range("2024-01-01", "2027-01-01", freq="MS"):
        fr = [d for d in pd.date_range(ms, ms + pd.offsets.MonthEnd(0)) if d.weekday() == 4][2]
        last = 3 if fr.strftime("%Y-%m-%d") not in HOLIDAYS else 2          # Mon..Thu or Mon..Wed
        mon = fr - pd.Timedelta(days=4)
        for j in range(last + 1):
            opex.add((mon + pd.Timedelta(days=j)).strftime("%Y-%m-%d"))
    for d in pd.date_range("2024-01-01", "2027-01-01", freq="D"):
        s = d.strftime("%Y-%m-%d")
        if d.weekday() <= 3 and s not in opex:
            # exclude the whole opex week (incl. the Thursday of a holiday week) from the control
            fr = d + pd.Timedelta(days=4 - d.weekday())
            if not (15 <= fr.day <= 21):
                other.add(s)
    return opex, other


_OPEX, _OTHER = _gate_days()


def _spy_quiet():
    if "q" in _MEM:
        return _MEM["q"]
    S = R24.spy_bars()
    t = S[S["tod"] == 1300][["date", "run_h", "run_l"]].copy()
    t["date"] = t["date"].astype(str)
    t = t.sort_values("date").reset_index(drop=True)
    t["rng"] = t["run_h"] - t["run_l"]
    dt = pd.to_datetime(t["date"])
    g = ((dt - dt.shift()).dt.days > 7).cumsum()
    t["avg20"] = t.groupby(g)["rng"].transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean())
    t["quiet"] = (t["rng"] < 1.0 * t["avg20"]).astype(float)
    _MEM["q"] = t[["date", "quiet"]]
    return _MEM["q"]


def _vxx_daily():
    d = U.daily_tab()
    v = d[d["symbol"] == "VXX"][["date", "c1"]].reset_index(drop=True)
    # median of the last 20 daily closes D-20..D-1 (c1 series is D-1's close at row D)
    dt = pd.to_datetime(v["date"])
    g = ((dt - dt.shift()).dt.days > 7).cumsum()
    v["med20"] = v.groupby(g)["c1"].transform(lambda x: x.rolling(20, min_periods=20).median())
    return v


@numba.njit(cache=False)
def _kern(k, tod, h, l, c, vw, gate):
    n = len(c)
    m = np.zeros(n)
    i = 0
    while i < n:
        j = i
        while j < n and k[j] == k[i]:
            j += 1
        # segment i..j-1 (one symbol-day, sorted by tod)
        armed = False         # 13:00 close above VWAP + 0.05%
        touched = False
        dead = False
        for q in range(i, j):
            if gate[q] != 1.0 or dead:
                continue
            if tod[q] == 1300:
                armed = c[q] > vw[q] * 1.0005
                continue
            if tod[q] < 1305 or not armed:
                continue
            if c[q] < vw[q] * (1 - 0.0010):
                dead = True
                continue
            if touched and q > i and c[q] > h[q - 1]:
                m[q] = 1.0
                dead = True
                continue
            if l[q] <= vw[q] * 1.0005:
                touched = True
        i = j
    return m


def mask(df) -> np.ndarray:
    n = len(df)
    z = np.zeros(n, bool)
    nanv = np.full(n, np.nan)
    _S.put(df, s=nanv, t=nanv)
    if not n:
        return z
    b = U.base(df)
    k = U.key(df)
    ds = pd.Series(df["date"].to_numpy()).astype(str)
    cal = ds.isin(_OPEX if OPEX else _OTHER).to_numpy()
    vx = U25.vxx_rows(df, "VXX")
    if vx is None:
        return z
    v13 = vx[vx["tod"] == 1300][["date", "vc"]].rename(columns={"vc": "v13"})
    vd = _vxx_daily().merge(v13, on="date", how="left")
    vd["volok"] = ((vd["v13"] < vd["c1"]) & (vd["c1"] < vd["med20"])).astype(float)
    volok = np.nan_to_num(U.map_date(df, vd, ["volok"])["volok"])
    quiet = np.nan_to_num(U.map_date(df, _spy_quiet(), ["quiet"])["quiet"])
    gate = (cal & (volok == 1.0) & (quiet == 1.0)).astype(float)
    m = _kern(k.astype(np.int64), b["tod"], b["h"], b["l"], b["c"], b["vwap"], gate) == 1.0
    with np.errstate(invalid="ignore"):
        stop = b["vwap"] - 0.6 * b["atr5"]
        tgt = b["c"] + 1.2 * (b["c"] - stop)
        m &= np.isfinite(stop) & (stop < b["c"])
    _S.put(df, s=stop, t=tgt)
    return np.asarray(m, bool)


def stop_price(f, i):
    return float(_S.get(f, "s", mask)[i])


def target_price(f, i, stop):
    return float(_S.get(f, "t", mask)[i])
