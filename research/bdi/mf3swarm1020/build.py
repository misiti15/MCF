"""Build the MF3 superset on the OPEN two-year history (PLAN.md): per open month, every min_adv (>= 95M) row at bar close
09:50..15:00 is simulated SHORT for every PLAN geometry with one 5-minute path simulator (frame rows + 15:05-15:55 tail
rows from headtail.parquet, flat 15:55; stop first in a bar, then target; trail / time-stop from the next bar; costs 1c +
1 bps per side, entry x tod multiplier, +2c on stops, target free, x3 on the extended tier). Saves
  superset.parquet  rows with heat <= -20 & buyPressure < -0.15 & rsi5 > 55 (+features, context, R per geometry)
  base.parquet      same-minute random baseline: mean R of all min_adv rows per (date, tod) per geometry
The locked block is never loaded: lib.months() lists open months only, headtail is read per open month by date filter.
Usage: python build.py <scratch_out>. Educational only - not financial advice."""
import sys
import time
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research.gates import prod_r  # noqa: E402
from research.history2y import lib  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
HEADTAIL = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
MIN_ADV = 95e6
COLS = ["symbol", "date", "tod", "close", "high", "low", "adv20", "atr_d", "gap", "fromOpen", "vwapDistPct", "heat",
        "buyPressure", "rsi5", "rsi", "r_short_t1s1", "win_short_t1s1"]
# name: (target R (0 = none), stop R, trail_r, trail_after_r, R multiple of 0.25 ATR, time-stop bars, time-stop min R)
GEO = {"t1s1": (1, 1, 0, 0, 1, 0, 0), "t05s1": (.5, 1, 0, 0, 1, 0, 0), "t1s05": (1, .5, 0, 0, 1, 0, 0),
       "t05s05": (.5, .5, 0, 0, 1, 0, 0), "hold": (0, 1, 0, 0, 1, 0, 0), "holdtr": (0, 1, 1, 1, 1, 0, 0),
       "r0.1875": (1, 1, 0, 0, .75, 0, 0), "r0.375": (1, 1, 0, 0, 1.5, 0, 0), "r0.5": (1, 1, 0, 0, 2, 0, 0),
       "ts30": (1, 1, 0, 0, 1, 6, .3), "ts60": (1, 1, 0, 0, 1, 12, .3)}


@numba.njit(cache=True)
def _mult(t):
    if t < 935:
        return 3.8
    if t < 950:
        return 2.1
    if t < 1030:
        return 1.4
    return 1.0


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, ent, R0, cm, up, dn, trr, tra, rm, tsn, tsr):
    side = -1
    n = len(ent)
    r = np.full(n, np.nan, np.float32)
    for q in range(n):
        i = ent[q]
        R = R0[q] * rm
        if not (R > 0):
            continue
        end = dend[i]
        if end <= i:
            continue
        e = c[i]
        ec = (0.01 + e * 1e-4) * _mult(tod[i])
        stop = e - side * dn * R
        tgt = e + side * up * R
        mfe = 0.0
        x = 0.0
        cd = 0
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                x = stop
                cd = 2
                break
            if up > 0 and side * (fav - tgt) >= 0:
                x = tgt
                cd = 1
                break
            mfe = max(mfe, side * (fav - e) / R)
            if tsn > 0 and k - i == tsn and mfe < tsr:
                x = c[k]
                cd = 3
                break
            if trr > 0 and mfe >= tra:
                ts = e + side * (mfe - trr) * R
                stop = max(stop, ts) if side == 1 else min(stop, ts)
        if cd == 0:
            x = c[end]
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
        r[q] = side * (x - e) / R - cm[q] * (ec + xc) / R
    return r


sup, bases, chk = [], [], []
for m in lib.months():
    t0 = time.time()
    df = lib.load_month(m, COLS, context=True)
    df = df[(df.tod >= 950) & (df.tod <= 1500) & (df.adv20 >= MIN_ADV) & (df.atr_d > 0)].reset_index(drop=True)
    df["symbol"] = df.symbol.astype(str)
    a = pd.Timestamp(m + "-01")
    ht = pd.read_parquet(HEADTAIL, columns=["symbol", "date", "tod", "h", "l", "c"],
                         filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht["symbol"] = ht.symbol.astype(str)
    ht["date"] = pd.to_datetime(ht.date).dt.date
    ht = ht[ht.tod > 1500].merge(df[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="inner")
    P = pd.concat([pd.DataFrame({"symbol": df.symbol, "date": df.date, "tod": df.tod.astype(np.int64), "h": df.high.astype(float),
                                 "l": df.low.astype(float), "c": df.close.astype(float), "fi": np.arange(len(df))}),
                   pd.DataFrame({"symbol": ht.symbol, "date": ht.date, "tod": ht.tod.astype(np.int64), "h": ht.h.astype(float),
                                 "l": ht.l.astype(float), "c": ht.c.astype(float), "fi": -1})], ignore_index=True)
    P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    key = pd.factorize(P.symbol + "|" + P.date.astype(str))[0]
    last = np.r_[np.flatnonzero(key[1:] != key[:-1]), len(P) - 1]
    dend = np.repeat(last, np.diff(np.r_[-1, last]))
    ent = np.full(len(df), -1, np.int64)
    fi = P.fi.to_numpy()
    ent[fi[fi >= 0]] = np.flatnonzero(fi >= 0)
    R0 = (0.25 * df.atr_d.to_numpy(float))
    cm = np.where((df.gap.abs().to_numpy(float) >= 20) | (df.close.to_numpy(float) < 5), 3.0, 1.0)
    h, l, c, tod = P.h.to_numpy(), P.l.to_numpy(), P.c.to_numpy(), P.tod.to_numpy()
    for g, (up, dn, trr, tra, rm, tsn, tsr) in GEO.items():
        df["R_" + g] = sim(h, l, c, tod, dend, ent, R0, cm, float(up), float(dn), float(trr), float(tra), float(rm), int(tsn), float(tsr))
    b = df.groupby(["date", "tod"])[["R_" + g for g in GEO]].mean().reset_index()
    bases.append(b)
    s = df[(df.heat <= -20) & (df.buyPressure < -0.15) & (df.rsi5 > 55)].copy()
    ok = np.isfinite(s.r_short_t1s1.to_numpy(float))
    pr = np.full(len(s), np.nan)
    pr[ok] = prod_r(s.r_short_t1s1.to_numpy(float)[ok], s.win_short_t1s1.to_numpy(float)[ok], s.close.to_numpy(float)[ok],
                    s.atr_d.to_numpy(float)[ok], "t1s1", tod=s.tod.to_numpy(float)[ok])
    s["prod_t1s1"] = pr
    sup.append(s.drop(columns=["high", "low", "r_short_t1s1", "win_short_t1s1"]))
    print(m, len(df), len(s), round(time.time() - t0, 1), flush=True)
    del df, P, ht
S = pd.concat(sup, ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
assert not ((S.date.astype(str) >= "2024-11-01") & (S.date.astype(str) <= "2025-02-28")).any()
S.to_parquet(OUT / "superset.parquet")
pd.concat(bases, ignore_index=True).to_parquet(OUT / "base.parquet")
print("done", len(S))
