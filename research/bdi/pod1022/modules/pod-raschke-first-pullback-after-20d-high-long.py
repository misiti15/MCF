"""pod-raschke-first-pullback-after-20d-high-long - Raschke 'buy the first pullback after a new high': the first
5-minute pullback after an intraday 20-day-high break (LONG).

Source: Linda Raschke trading rules ('buy the first pullback after a new high, sell the first rally after a new low';
'best reversals in the morning'), as compiled from Street Smarts-era rule lists.
URL: https://www.scribd.com/document/942776286/Trading-Rules-Linda-Raschke

VARIANT of pod-smb-20d-high-time-acceptance-long. Stated change: no 15-minute time acceptance; the entry is the FIRST
orderly pullback (2-6 bars of lower highs on falling volume) that holds above the broken 20-day high, bought on a
break of the prior bar's high.
Rules (plain English):
  1. L = max high of D-20..D-1 (completed days); today's open < L; a 5-minute close above L happened before 11:30.
  2. The leg from min(open, LOD before the HOD) to the HOD is >= 0.6 x atr_d.
  3. Pullback: 2-6 consecutive bars with lower highs right after the HOD bar, retracing 25-62% of the leg; the
     pullback low >= L - 0.05 x atr_d, every pullback bar's low >= its session VWAP, mean volumeRatio of the pullback
     bars <= 0.9.
  4. Trigger: the bar that ends the lower-high run closes above the previous bar's high with volumeRatio >= 1.1. Only
     the first pullback per symbol-day qualifies (the first lower-high run of >= 2 bars after the break is used up
     whether it triggers or not).
  Entry: trigger close, 10:00-13:30 ET. Stop (GEOM S): pullback low - 0.05 x atr_d. Target: HOD + 0.5 x pullback
  depth (measured move), or 2R if nearer; flat 15:55.
Harness notes (pre-declared): 'falling volume' is read as mean volumeRatio <= 0.9 (no raw volume in the frame). The
close above L may come from a 09:35-09:45 bar (5m closes from the _r24_bars cache); the HOD bar and the pullback must
be visible in the frame (09:50+). A lower-high run that breaks without a new HOD ends the chain until the next new
HOD. No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r27_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1330)
CONTEXT = []
LAYERS = ["open < 20d high L, 5m close > L before 11:30", "leg >= 0.6 ATR",
          "first pullback: 2-6 lower highs, 25-62% retrace, low >= L - 0.05 ATR and >= VWAP, mean volumeRatio <= 0.9",
          "close > prior bar high, volumeRatio >= 1.1", "10:00-13:30", "stop pullback low - 0.05 ATR, target HOD + 0.5 depth or 2R"]
_ST = {}


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


@numba.njit(cache=False)
def _scan(st, tod, h, l, c, hod, lod, opn, vw, vr, atr, L, xt):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    i = 0
    while i < n:
        e = i + 1
        while e < n and not st[e]:
            e += 1
        if np.isfinite(L[i]) and np.isfinite(xt[i]) and xt[i] <= 1130 and opn[i] < L[i]:
            hb = -1
            chain = False
            used = False
            for t in range(i, e):
                if used:
                    break
                if tod[t] < xt[i]:
                    continue
                newhod = h[t] >= hod[t] - 1e-9 * max(1.0, abs(hod[t]))
                if hb >= 0 and chain and t > hb and not newhod and h[t] >= h[t - 1]:
                    npb = t - 1 - hb
                    if npb >= 2:
                        used = True                      # the first pullback is consumed here
                        if npb <= 6:
                            H = hod[hb]
                            pbl = 1e300
                            vs = 0.0
                            okv = True
                            for j in range(hb + 1, t):
                                if l[j] < pbl:
                                    pbl = l[j]
                                vs += vr[j]
                                if not (l[j] >= vw[j]):
                                    okv = False
                            leg = H - min(opn[t], lod[hb])
                            depth = H - pbl
                            a = atr[t]
                            ok = okv and leg >= 0.6 * a and leg > 0
                            ok = ok and depth >= 0.25 * leg and depth <= 0.62 * leg
                            ok = ok and pbl >= L[i] - 0.05 * a and vs / npb <= 0.9
                            ok = ok and c[t] > h[t - 1] and vr[t] >= 1.1
                            if ok:
                                s = pbl - 0.05 * a
                                r = c[t] - s
                                if r > 0:
                                    mm = H + 0.5 * depth
                                    tt = c[t] + 2 * r
                                    if mm > c[t] and mm < tt:
                                        tt = mm
                                    m[t] = True
                                    stop[t] = s
                                    tgt[t] = tt
                        continue
                if newhod:
                    hb = t
                    chain = True
                elif hb >= 0 and t > hb and chain:
                    if not (h[t] < h[t - 1]):
                        chain = False
        i = e
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n:
        return np.zeros(0, bool)
    k = U.key(df)
    st = U.start(k)
    b = U.base(df)
    D = U.map_daily(df, k, ["hi201"])
    B = U.vol_bars(df)
    if B is None:
        return np.zeros(n, bool)
    # first 5m close above L (09:35..) per symbol-day
    sym = df["symbol"].astype(str).to_numpy()[st]
    dn = pd.to_datetime(pd.Series(df["date"].to_numpy()[st]).astype(str)).to_numpy("datetime64[D]").astype(np.int64)
    u = pd.DataFrame({"symbol": sym, "dn": dn, "L": D["hi201"][st]})
    x = B[["symbol", "dn", "tod", "c"]].merge(u, on=["symbol", "dn"], how="inner")
    x = x[x["c"] > x["L"]].groupby(["symbol", "dn"])["tod"].min().rename("xt").reset_index()
    xt = u.merge(x, on=["symbol", "dn"], how="left")["xt"].to_numpy(float)[np.cumsum(st) - 1]
    with np.errstate(invalid="ignore"):
        m, stop, tgt = _scan(st, b["tod"], b["h"], b["l"], b["c"], b["hod"], b["lod"], b["opn"], b["vwap"],
                             U.f(df, "volumeRatio"), b["atr"], D["hi201"], xt)
        m &= (b["tod"] >= WINDOW[0]) & (b["tod"] <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), bool)
