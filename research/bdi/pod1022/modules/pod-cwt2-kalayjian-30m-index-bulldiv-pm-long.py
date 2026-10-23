"""pod-cwt2-kalayjian-30m-index-bulldiv-pm-long - Afternoon 30-minute RSI bullish divergence on index ETFs with 5-min
agreement (LONG).

Source: Chat With Traders ep 322, Stephen Kalayjian; record ep322 'Multi-timeframe indicator divergence reversal
(30-min signal on index ETFs)'. Low fidelity: the guest's signal is proprietary.
URL: https://chatwithtraders.com

VARIANT of bdi-rdt-r12-rsi-div (failed: 5-min RSI divergence on single STOCKS, full day). Stated change: a higher
timeframe (30-min) divergence on INDEX ETFs only, which must agree with a 5-min divergence, afternoon only, held to the
close.

Rules (plain English). SYMBOLS = SPY, QQQ, IWM. Only completed bars up to the decision bar i are used.
  30-min bars (09:30-10:00, ..., 15:30-16:00) are built from the 5-minute frame bars plus the 09:35-09:45 and
  15:05-15:55 bars of the same symbol from the head/tail table (prior days' tails; today's head) - continuous across
  the days of the scored month. RSI(14) (Wilder) on the 30-min closes; the first 28 30-min bars of a month are warm-up.
  1. The latest COMPLETED 30-min bar k (ending at or before the decision bar's close) closes at a new 2-day low:
     below the prior-day low and below the lows of today's earlier 30-min bars.
  2. Divergence: the most recent 30-min swing low p (low below both neighbours, confirmed, within the last 26 30-min
     bars = 2 days) has a higher low than bar k's low, and RSI14_30m(k) > RSI14_30m(p).
  3. The 5-minute bull_div == 1 on one of bars i-2..i.
  4. Trigger: the 5-minute close_i > high_{i-1}.
  Entry: close_i, bar close 13:30-15:00. Stop (GEOM S): the session low - 0.05 x atr_d. Target: none, hold to 15:55
  (the source's example rallies into the close; the stated alternative, the session VWAP, is NOT used).
  Costs in (scorer). No tweak used.
Educational only - not financial advice."""
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1330, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM"]
CONTEXT = []
LAYERS = ["latest completed 30m bar closes at a new 2-day low (below PDL and today's earlier 30m lows)",
          "30m RSI(14) higher than at the previous 30m swing low (within 2 days), price lower",
          "5m bull_div within the last 3 bars", "5m close > prior 5m high", "13:30-15:00 ET",
          "stop session low - 0.05 ATR, hold to 15:55"]

_ROOT = Path(__file__).resolve().parents[4]
_HEADTAIL = _ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
_LOCKED = ("2024-11-01", "2025-02-28")
_STASH = {}


def _rsi(x, n=14):
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    d = np.diff(x)
    up = np.where(d > 0, d, 0.0)
    dn = np.where(d < 0, -d, 0.0)
    au = up[:n].mean()
    ad = dn[:n].mean()
    for k in range(n, len(x)):
        if k > n:
            au = (au * (n - 1) + up[k - 1]) / n
            ad = (ad * (n - 1) + dn[k - 1]) / n
        out[k] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    return out


def _min(t):
    return (t // 100) * 60 + t % 100


def compute(df):
    n = len(df)
    m = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    if n == 0:
        return m, stop, np.full(n, np.nan)
    sym = df["symbol"].astype(str).to_numpy()
    dates = df["date"].to_numpy()
    tod = df["tod"].to_numpy(np.int64)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore"):
        lod = c - f("dist_lod_atr") * atr
        pdl = c - f("dist_pdl_atr") * atr
    bd = f("bull_div")
    d0, d1 = pd.Timestamp(min(dates)), pd.Timestamp(max(dates))
    if str(d0.date()) <= _LOCKED[1] and str(d1.date()) >= _LOCKED[0]:
        return m, stop, np.full(n, np.nan)                       # never touch the locked block
    try:
        ht = pd.read_parquet(_HEADTAIL, columns=["symbol", "date", "tod", "h", "l", "c"],
                             filters=[("symbol", "in", SYMBOLS), ("date", ">=", d0), ("date", "<=", d1)])
        ht["symbol"] = ht["symbol"].astype(str)
        ht["date"] = pd.to_datetime(ht["date"]).dt.date
        ht = ht[(ht["tod"] < 950) | (ht["tod"] > 1500)]
    except Exception:
        ht = pd.DataFrame(columns=["symbol", "date", "tod", "h", "l", "c"])
    for s in SYMBOLS:
        rows = np.flatnonzero(sym == s)
        if not len(rows):
            continue
        fr = pd.DataFrame({"date": dates[rows], "tod": tod[rows], "h": h[rows], "l": l[rows], "c": c[rows]})
        hs = ht[ht["symbol"] == s][["date", "tod", "h", "l", "c"]]
        hs = hs[hs["date"].isin(set(fr["date"]))]
        p = pd.concat([fr, hs.astype({"tod": np.int64})], ignore_index=True).sort_values(["date", "tod"])
        p["b"] = -(-(_min(p["tod"].to_numpy(np.int64))) // 30) * 30           # bucket end, minutes
        g = p.groupby(["date", "b"], sort=True).agg(H=("h", "max"), L=("l", "min"), C=("c", "last")).reset_index()
        g["rsi"] = _rsi(g["C"].to_numpy(float))
        g.loc[g.index < 28, "rsi"] = np.nan
        L = g["L"].to_numpy(float)
        C = g["C"].to_numpy(float)
        R = g["rsi"].to_numpy(float)
        gd = g["date"].to_numpy()
        pdl_d = dict(zip(dates[rows], pdl[rows]))
        div = np.zeros(len(g), bool)
        for k in range(len(g)):
            pd_l = pdl_d.get(gd[k], np.nan)
            if not (C[k] < pd_l):
                continue
            today = [q for q in range(max(0, k - 13), k) if gd[q] == gd[k]]
            if today and not (C[k] < min(L[q] for q in today)):
                continue
            pv = -1
            for q in range(k - 2, max(0, k - 26), -1):          # pivot q confirmed by q+1 <= k-1
                if q >= 1 and L[q] < L[q - 1] and L[q] < L[q + 1]:
                    pv = q
                    break
            if pv < 0 or not (L[pv] > L[k]) or not (R[k] > R[pv]):
                continue
            div[k] = True
        key = {(gd[k], int(g["b"].iloc[k])): div[k] for k in range(len(g))}
        for q, i in enumerate(rows):
            if q < 3 or tod[i] < WINDOW[0] or tod[i] > WINDOW[1]:
                continue
            ip = rows[q - 1]
            if dates[ip] != dates[i] or dates[rows[q - 2]] != dates[i]:
                continue
            kend = (_min(tod[i]) // 30) * 30                      # latest completed 30m bar end
            if not key.get((dates[i], kend), False):
                continue
            if not (bd[i] == 1 or bd[ip] == 1 or bd[rows[q - 2]] == 1):
                continue
            if not (c[i] > h[ip]):
                continue
            sp = lod[i] - 0.05 * atr[i]
            if sp < c[i]:
                m[i] = True
                stop[i] = sp
    return m, stop, np.full(n, np.nan)


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])
