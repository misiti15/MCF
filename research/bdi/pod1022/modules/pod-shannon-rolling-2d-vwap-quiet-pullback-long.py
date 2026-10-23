"""pod-shannon-rolling-2d-vwap-quiet-pullback-long - Quiet-day pullback to the rolling 2-day VWAP above a rising
5-day VWAP (LONG).

Source: Brian Shannon multi-day VWAP usage (TradingView 'Multi-Day Rolling VWAP [Intraday]', built on ideas from
Shannon's 'Anchored VWAP' book: 1/2/3/4/5-day VWAPs as intraday support).
URL: https://vn.tradingview.com/script/mBkObMct-Multi-Day-Rolling-VWAP-Intraday

VARIANT of pod-shannon-5dma-mtf-pullback-long. Stated change: the support line is the volume-weighted rolling 2-day
VWAP (not the 5-day SMA of closes), the slope filter is the 5-day VWAP, and the setup is gated to quiet days.

Definitions. VWAP2D = sum(price x volume) / sum(volume) from the open of D-1 up to bar i; VWAP5D the same from the open
of D-4. Completed sessions use typical price x volume from the regular-session 1-minute vendor bars; today's bars
(and D-1's bars up to 15:00 for the lag value) use the 5-minute close as the price (the cached intraday volume table
has no typical price). "VWAP5D 63 bars earlier" = the 5D VWAP 63 five-minute session bars back, i.e. D-1's bar 75
minutes later in the day than bar i (78 bars per session).
Rules (plain English, LONG), default universe (adv20 >= $20M):
  1. Quiet day: today's 09:30-10:30 high-low range <= 0.6 x the mean 09:30-10:30 range of the prior 20 sessions (so
     the signal bar closes at 10:30 or later).
  2. VWAP5D at the signal bar > VWAP5D 63 bars earlier (rising) and the close > VWAP5D.
  3. VWAP2D > VWAP5D.
  4. Signal bar: low <= VWAP2D + 0.05 x atr_d and close > VWAP2D, RSI(14) 5m between 35 and 55.
  5. |vwapDistPct| <= 0.4 at the signal bar (near the session VWAP, no chase).
  Entry: the next bar closes above the signal bar's high, bar close 10:30-14:30 ET (10:35 at the earliest).
  Stop (GEOM S): VWAP2D at the signal bar - 0.2 x atr_d. Target: the high of day at entry, or 1.5R when the high of
  day is not above the entry; flat 15:55.
No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r26_bars as RB  # noqa: E402
import _r24_bars as R24  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
LAYERS = ["quiet first hour (<= 0.6 x 20-day mean)", "VWAP5D rising over 63 bars, close > VWAP5D",
          "VWAP2D > VWAP5D", "signal bar tags VWAP2D (+0.05 ATR) and closes above, RSI 35-55",
          "|vwapDistPct| <= 0.4", "entry: next close > signal high", "stop VWAP2D - 0.2 ATR, target HOD or 1.5R"]
_ST = {}
_C = {}


def _daytab():
    if "d" in _C:
        return _C["d"]
    d = RB.day().copy()
    dt = pd.to_datetime(d["date"])
    run = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    g = lambda col, n: d[col].groupby(run).shift(n)
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    out["S1"], out["V1"] = g("S", 1), g("V", 1)
    out["S24"] = g("S", 2) + g("S", 3) + g("S", 4)
    out["V24"] = g("V", 2) + g("V", 3) + g("V", 4)
    out["S25"] = out["S24"] + g("S", 5)
    out["V25"] = out["V24"] + g("V", 5)
    out["dn1"] = g("dn", 1)
    out["fh"] = d["fh_rng"]
    out["fh20"] = d["fh_rng"].groupby(run).transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean())
    for T in RB.LATE_TODS:
        out[f"ctp1_{T}"] = g(f"ctp_{T}", 1)
        out[f"cvl1_{T}"] = g(f"cvl_{T}", 1)
    _C["d"] = out
    return out


def _r24(df, warm=True):
    syms = set(df["symbol"].astype(str))
    ms = R24._months_of(df)
    if warm and ms:
        pm = RB.prev_month(ms[0])
        if pm and pm not in R24._LOCKED_MONTHS:
            ms = [pm] + ms
    parts = []
    for mo in ms:
        p = R24._OUT / "bars" / f"month={mo}.parquet"
        if p.exists():
            b = pd.read_parquet(p, columns=["symbol", "dn", "tod", "c", "v"])
            b["symbol"] = b["symbol"].astype(str)
            parts.append(b[b["symbol"].isin(syms)])
    if not parts:
        return None
    B = pd.concat(parts, ignore_index=True).sort_values(["symbol", "dn", "tod"], kind="mergesort")
    B["cpv"] = B["c"].astype(float) * B["v"].astype(float)
    g = B.groupby(["symbol", "dn"], sort=False)
    B["cs"] = g["cpv"].cumsum()
    B["cv"] = g["v"].cumsum().astype(float)
    return B[["symbol", "dn", "tod", "cs", "cv"]]


def _tod_add(tod, mins):
    t = (tod // 100) * 60 + tod % 100 + mins
    return (t // 60) * 100 + t % 60


def _compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    if not n:
        return m, stop, tgt
    B = _r24(df)
    if B is None:
        return m, stop, tgt
    cols = ["S1", "V1", "S24", "V24", "S25", "V25", "dn1", "fh", "fh20"]
    cols += [f"ctp1_{T}" for T in RB.LATE_TODS] + [f"cvl1_{T}" for T in RB.LATE_TODS]
    D = RB.map_day(df, _daytab(), cols)
    I = RB.map_bars(df, B, ["cs", "cv"])
    tod = df["tod"].to_numpy(np.int64)
    # D-1 bar 75 minutes later in the day (= 63 session bars back)
    tl = _tod_add(tod, 75)
    k = RB.frame_keys(df)
    dn1 = D["dn1"]
    lk = pd.DataFrame({"symbol": k["symbol"], "dn": np.where(np.isfinite(dn1), dn1, -1).astype(np.int64), "tod": tl})
    Bm = B.copy()
    Bm["dn"] = Bm["dn"].astype(np.int64)
    Bm["tod"] = Bm["tod"].astype(np.int64)
    L = lk.merge(Bm, on=["symbol", "dn", "tod"], how="left")
    cs1, cv1 = L["cs"].to_numpy(float).copy(), L["cv"].to_numpy(float).copy()
    for T in RB.LATE_TODS:                                   # D-1 bars after 15:00 from the day table
        sel = tl == T
        cs1[sel] = D[f"ctp1_{T}"][sel]
        cv1[sel] = D[f"cvl1_{T}"][sel]
    with np.errstate(invalid="ignore", divide="ignore"):
        v2 = (D["S1"] + I["cs"]) / (D["V1"] + I["cv"])
        v5 = (D["S1"] + D["S24"] + I["cs"]) / (D["V1"] + D["V24"] + I["cv"])
        v5lag = (D["S25"] + cs1) / (D["V25"] + cv1)
        c, h, l = (df[x].to_numpy(float) for x in ("close", "high", "low"))
        atr = df["atr_d"].to_numpy(float)
        hod = c + df["dist_hod_atr"].to_numpy(float) * atr
        sig = (D["fh"] <= 0.6 * D["fh20"]) & (tod >= 1030)
        sig &= (v5 > v5lag) & (c > v5) & (v2 > v5)
        sig &= (l <= v2 + 0.05 * atr) & (c > v2)
        rsi = df["rsi"].to_numpy(float)
        sig &= (rsi >= 35) & (rsi <= 55)
        sig &= np.abs(df["vwapDistPct"].to_numpy(float)) <= 0.4
        kk = pd.factorize(k["symbol"] + "|" + k["dn"].astype(str))[0]
        same = np.r_[False, kk[1:] == kk[:-1]]
        psig = np.r_[False, sig[:-1]] & same
        ph = np.r_[np.nan, h[:-1]]
        pv2 = np.r_[np.nan, v2[:-1]]
        m = psig & (c > ph) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        s = pv2 - 0.2 * atr
        risk = c - s
        m &= risk > 0
        t = np.where(hod > c, hod, c + 1.5 * risk)
    stop = np.where(m, s, np.nan)
    tgt = np.where(m, t, np.nan)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    m, stop, tgt = _compute(df)
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


def target_price(f, i, stop):
    return float(_get(f)[1][i])
