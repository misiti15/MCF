"""pod-shannon-30m-higher-high-flat5dma-long - 30-minute higher-high break above a flat-to-rising 5-day MA, stop under
the 30-minute higher low (LONG).

Source: Brian Shannon, Alpha Trends talk 'The science of technical analysis vs. the art of trading' (videohighlight
summary: buys a higher high above a flat-to-rising 5-day MA, stop below the most recent relevant higher low, uses the
30-minute chart for risk / reward); Benzinga interview (daily, then a 30 / 65-minute drill-down).
URL: https://videohighlight.com/v/Wu57GWTm1_U

VARIANT of pod-shannon-5dma-mtf-pullback-long. Stated change: no touch of the MA is needed; the trigger is a break of
the last completed 30-minute bar's high (higher high), only after a confirmed 30-minute higher low, and the stop is
that 30-minute higher low (structural), not MA - k x ATR.

Rules (plain English, LONG), default universe (adv20 >= $20M). 30-minute bars are built from today's 5-minute bars
from 09:30 (09:30-10:00, 10:00-10:30, ...; the 09:35-09:45 bars come from the head/tail table); a 30m bar is used only
once it is complete.
  1. Daily SMA5 at D-1 >= SMA5 at D-2 (flat to rising) and the D-1 close > the daily SMA20.
  2. The latest confirmed 30m swing low today (a completed 30m bar whose low is below both neighbours, the right
     neighbour complete too) is above the previous 30m swing low today, or above the PDL when there is none.
  3. Close > session VWAP and > the intraday 5-day MA ((the D-4..D-1 closes + the current close) / 5).
  4. Trigger: a 5-minute close above the high of the last completed 30m bar, that high being the highest 30m high
     since the swing low (higher high), with volumeRatio >= 1.2.
  Entry: trigger close, bar close 10:30-14:30 ET, max one per symbol-day. Stop (GEOM S): the 30m higher low - 0.05 x
  atr_d; skip if the risk > 0.6 x atr_d. Target 2R, else flat 15:55.
No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r26_bars as RB  # noqa: E402

_HEADTAIL = Path(__file__).resolve().parents[4] / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
_LOCKED = ("2024-11-01", "2025-02-28")

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
LAYERS = ["daily SMA5 flat/rising, D-1 > SMA20", "30m higher low (vs previous 30m swing low or PDL)",
          "close > VWAP and > intraday 5-day MA", "5m close > last completed 30m high = highest since the HL",
          "volumeRatio >= 1.2", "stop 30m HL - 0.05 ATR (<= 0.6 ATR), target 2R"]
_ST = {}
_C = {}


@numba.njit(cache=False)
def _state(H, L, pdl):
    """For each symbol-day g and number of completed 30m bars nc: (higher-low price or NaN, last completed high or
    NaN when it is not the highest since the higher low)."""
    G, K = H.shape
    hl = np.full((G, K + 1), np.nan)
    hh = np.full((G, K + 1), np.nan)
    for g in range(G):
        for nc in range(3, K + 1):
            j1, j0 = -1, -1
            for j in range(nc - 2, 0, -1):
                if L[g, j] < L[g, j - 1] and L[g, j] < L[g, j + 1]:
                    if j1 < 0:
                        j1 = j
                    else:
                        j0 = j
                        break
            if j1 < 0:
                continue
            ref = L[g, j0] if j0 >= 0 else pdl[g]
            if not (L[g, j1] > ref):
                continue
            hlast = H[g, nc - 1]
            ok = True
            for j in range(j1, nc - 1):
                if H[g, j] >= hlast:
                    ok = False
                    break
            if not ok or hlast != hlast:
                continue
            hl[g, nc] = L[g, j1]
            hh[g, nc] = hlast
    return hl, hh


def _daily():
    if "d" in _C:
        return _C["d"]
    d = RB.daily()
    g = d.groupby("run")["close"]
    s5 = g.transform(lambda x: x.rolling(5, min_periods=5).mean())
    s20 = g.transform(lambda x: x.rolling(20, min_periods=20).mean())
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    out["s5_1"] = s5.groupby(d["run"]).shift(1)
    out["s5_2"] = s5.groupby(d["run"]).shift(2)
    out["s20_1"] = s20.groupby(d["run"]).shift(1)
    out["c4"] = g.transform(lambda x: x.shift(1).rolling(4, min_periods=4).sum())
    out["c_1"] = g.shift(1)
    _C["d"] = out
    return out


def _compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    if not n:
        return m, stop, tgt
    ds = pd.Series(df["date"].to_numpy()).astype(str)
    sy = df["symbol"].astype(str).to_numpy()
    a, b = ds.min(), ds.max()
    assert not (a <= _LOCKED[1] and b >= _LOCKED[0]), "locked"
    ht = pd.read_parquet(_HEADTAIL, columns=["symbol", "date", "tod", "h", "l"],
                         filters=[("date", ">=", pd.Timestamp(a)), ("date", "<=", pd.Timestamp(b)),
                                  ("tod", "<", 950)])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.strftime("%Y-%m-%d")
    fr = pd.DataFrame({"symbol": sy, "date": ds.to_numpy(), "tod": df["tod"].to_numpy(np.int64),
                       "h": df["high"].to_numpy(float), "l": df["low"].to_numpy(float)})
    key = fr[["symbol", "date"]].drop_duplicates()
    ht = ht.merge(key, on=["symbol", "date"], how="inner")
    P = pd.concat([fr, ht[["symbol", "date", "tod", "h", "l"]].astype({"tod": np.int64})], ignore_index=True)
    mins = (P["tod"] // 100) * 60 + P["tod"] % 100
    P["k"] = (mins - 571) // 30
    A = P.groupby(["symbol", "date", "k"], sort=True).agg(h=("h", "max"), l=("l", "min")).reset_index()
    gk = pd.factorize(A["symbol"] + "|" + A["date"])[0]
    G, K = gk.max() + 1, 13
    H = np.full((G, K), np.nan)
    L = np.full((G, K), np.nan)
    kk = A["k"].to_numpy(np.int64)
    ok = (kk >= 0) & (kk < K)
    H[gk[ok], kk[ok]] = A["h"].to_numpy(float)[ok]
    L[gk[ok], kk[ok]] = A["l"].to_numpy(float)[ok]
    gid_tab = pd.DataFrame({"sd": (A["symbol"] + "|" + A["date"]).to_numpy(), "g": gk}).drop_duplicates("sd")
    c, atr = df["close"].to_numpy(float), df["atr_d"].to_numpy(float)
    pdl = c - df["dist_pdl_atr"].to_numpy(float) * atr
    sd = pd.Series(sy) + "|" + ds
    g_row = sd.map(pd.Series(gid_tab["g"].to_numpy(), index=gid_tab["sd"].to_numpy())).to_numpy()
    pdl_g = np.full(G, np.nan)
    pdl_g[g_row.astype(np.int64)] = pdl
    hl, hh = _state(H, L, pdl_g)
    tod = df["tod"].to_numpy(np.int64)
    mm = (tod // 100) * 60 + tod % 100
    nc = np.clip((mm - 600) // 30 + 1, 0, K)
    gi = g_row.astype(np.int64)
    HL, HH = hl[gi, nc], hh[gi, nc]
    D = RB.map_day(df, _daily(), ["s5_1", "s5_2", "s20_1", "c4", "c_1"])
    with np.errstate(invalid="ignore"):
        ma5 = (D["c4"] + c) / 5
        m = (D["s5_1"] >= D["s5_2"]) & (D["c_1"] > D["s20_1"])
        m &= (df["vwapDistPct"].to_numpy(float) > 0) & (c > ma5)
        m &= np.isfinite(HL) & (c > HH) & (df["volumeRatio"].to_numpy(float) >= 1.2)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        s = HL - 0.05 * atr
        risk = c - s
        m &= (risk > 0) & (risk <= 0.6 * atr)
    stop = np.where(m, s, np.nan)
    tgt = np.where(m, c + 2 * risk, np.nan)
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
