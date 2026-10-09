"""W4 step 2 (NOTES.md 1.3-1.4): 1-minute path simulation of every unique entry of books P and T under the base exits
and the exit variants E1-E11 (+ the heat_fade_short scratch exits X15/X30/X45).

1-minute bars from data/cache_hist/1Min; rows dated 2024-11-01..2025-02-28 (the rule-19 locked block) are dropped
right after reading, before any computation. One process, one symbol at a time.

Output (git-ignored): data/sim.parquet (one row per unique entry: r per variant, base exit minute, swing risk)
    python research/swarm1010/w4_exits_sizing/sim.py
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = ROOT / "data" / "cache_hist" / "1Min"
LOCKED = ("2024-11-01", "2025-02-28")
GEOMK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
SLIP_PS, SLIP_BPS, STOP_EXTRA = 0.01, 1e-4, 0.02
FLAT, FLAT_1530 = 15 * 60 + 54, 15 * 60 + 29          # minute START of the last bar (closes 15:55 / 15:30)
INF = np.inf

# variant -> engine params (NOTES.md 1.4)
VARIANTS = {
    "base": {},
    "E1": {"trail_k": 1.0, "no_target": True}, "E2": {"trail_k": 1.5, "no_target": True},
    "E3": {"trail_k": 2.0, "no_target": True},
    "E4": {"ts": (30, 0.25)}, "E5": {"ts": (60, 0.25)}, "E6": {"ts": (90, 0.25)},
    "E7": {"swing": 30}, "E8": {"swing": 60},
    "E9": {"scale": 1.0, "no_target": True},
    "E10": {"be": 0.75},
    "E11": {"flat": FLAT_1530},
    "X15": {"ts": (15, 0.5)}, "X30": {"ts": (30, 0.5)}, "X45": {"ts": (45, 0.5)},
}


def engine(s, e, R, H, L, C, EL, last, up_k, dn_k, trail_D=None, be=None, ts=None, scale=None):
    """Vectorised over trades. s side (+1/-1), e entry, R risk (price), H/L/C (n x m) path from the bar after entry,
    EL elapsed minutes at each bar's close, last = index of the flatten bar. Returns (r in R incl. costs, exit idx)."""
    n, m = H.shape
    stop = e - s * dn_k * R
    tgt = e + s * up_k * R                     # +-inf when no target
    so_px = e + s * scale * R if scale else None
    alive = np.ones(n, bool)
    scaled = np.zeros(n, bool)
    best = np.zeros(n)                          # MFE in R
    bestpx = e.copy()
    res = np.zeros(n)                           # gross R accumulated
    cost = (SLIP_PS + e * SLIP_BPS) / R         # entry side
    mkt = (SLIP_PS + e * SLIP_BPS) / R
    xi = np.full(n, -1)
    rem = np.ones(n)                            # remaining fraction
    for j in range(m):
        h, l, c = H[:, j], L[:, j], C[:, j]
        act = alive & np.isfinite(c) & (j <= last)
        if not act.any():
            if (j > last).all():
                break
            continue
        fav = np.where(s == 1, h, l)
        adv = np.where(s == 1, l, h)
        hit_s = act & (s * (adv - stop) <= 0)
        res[hit_s] += rem[hit_s] * s[hit_s] * (stop[hit_s] - e[hit_s]) / R[hit_s]
        cost[hit_s] += rem[hit_s] * (mkt[hit_s] + STOP_EXTRA / R[hit_s])
        alive[hit_s] = False
        xi[hit_s] = j
        act2 = act & ~hit_s
        if so_px is not None:
            hs = act2 & ~scaled & (s * (fav - so_px) >= 0)
            res[hs] += 0.5 * scale
            rem[hs] = 0.5
            scaled[hs] = True
            stop[hs] = np.where(s[hs] == 1, np.maximum(stop[hs], e[hs]), np.minimum(stop[hs], e[hs]))
        hit_t = act2 & (s * (fav - tgt) >= 0)
        res[hit_t] += rem[hit_t] * up_k[hit_t]
        alive[hit_t] = False
        xi[hit_t] = j
        act3 = act2 & ~hit_t
        f = np.where(act3, s * (fav - e) / R, -INF)
        best = np.maximum(best, f)
        bestpx = np.where(act3 & (s * (fav - bestpx) > 0), fav, bestpx)
        if trail_D is not None:
            tr = bestpx - s * trail_D
            stop = np.where(act3, np.where(s == 1, np.maximum(stop, tr), np.minimum(stop, tr)), stop)
        if be is not None:
            b = act3 & (best >= be)
            stop = np.where(b, np.where(s == 1, np.maximum(stop, e), np.minimum(stop, e)), stop)
        fin = act3 & (j == last)
        if ts is not None:
            fin = fin | (act3 & (EL[:, j] >= ts[0]) & (best < ts[1]))
        res[fin] += rem[fin] * s[fin] * (c[fin] - e[fin]) / R[fin]
        cost[fin] += rem[fin] * mkt[fin]
        alive[fin] = False
        xi[fin] = j
    # trades with no bar after entry (entry at the flatten): flat at entry
    left = alive
    cost[left] += mkt[left]
    return res - cost, xi


def sym_days(sym: str):
    df = pd.read_parquet(CACHE / f"{sym}.parquet")
    idx = df.index
    di = np.asarray(idx.year * 10000 + idx.month * 100 + idx.day)
    u, inv = np.unique(di, return_inverse=True)
    d = np.array([f"{x // 10000:04d}-{x // 100 % 100:02d}-{x % 100:02d}" for x in u])[inv]
    keep = (d < LOCKED[0]) | (d > LOCKED[1])             # drop the locked block before anything else
    df, d, idx = df[keep], d[keep], idx[keep]
    mins = idx.hour * 60 + idx.minute
    ok = (mins >= 570) & (mins <= FLAT)
    df, d, mins = df[ok], d[ok], np.asarray(mins[ok])
    out = {}
    if not len(df):
        return out
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    b = np.flatnonzero(np.r_[True, d[1:] != d[:-1], True])
    for a, z in zip(b[:-1], b[1:]):
        out[d[a]] = (mins[a:z], h[a:z], l[a:z], c[a:z])
    return out


def run_symbol(sym: str, tr: pd.DataFrame) -> pd.DataFrame:
    days = sym_days(sym)
    n = len(tr)
    tmin = (tr["tod"].to_numpy() // 100) * 60 + tr["tod"].to_numpy() % 100      # bar END = first path minute start
    m = FLAT - 590 + 2
    H = np.full((n, m), np.nan); L = H.copy(); C = H.copy(); EL = H.copy()
    last = np.full(n, -1); last1530 = np.full(n, -1)
    c1 = np.full(n, np.nan); sw30 = np.full(n, np.nan); sw60 = np.full(n, np.nan)
    s = np.where(tr["side"].to_numpy() == "long", 1, -1)
    for i, (dt, tm) in enumerate(zip(tr["date"].to_numpy(), tmin)):
        x = days.get(dt)
        if x is None:
            continue
        mins, h, l, c = x
        a = np.searchsorted(mins, tm)
        z = np.searchsorted(mins, FLAT, "right")
        k = z - a
        if a > 0 and mins[a - 1] == tm - 1:
            c1[i] = c[a - 1]
        if k > 0:
            H[i, :k], L[i, :k], C[i, :k] = h[a:z], l[a:z], c[a:z]
            EL[i, :k] = mins[a:z] - tm + 1
            last[i] = k - 1
            last1530[i] = np.searchsorted(mins[a:z], FLAT_1530, "right") - 1
        for w, arr in ((30, sw30), (60, sw60)):
            p0 = np.searchsorted(mins, tm - w)
            if a > p0:
                arr[i] = l[p0:a].min() if s[i] == 1 else h[p0:a].max()
    e = tr["close"].to_numpy(float)
    R = 0.25 * tr["atr_d"].to_numpy(float)
    gk = np.array([GEOMK[g] for g in tr["geom"]])
    up, dn = gk[:, 0], gk[:, 1]
    out = {"c1": c1}
    for v, p in VARIANTS.items():
        RR, upk, dnk = R, up, dn
        if "swing" in p:
            sw = sw30 if p["swing"] == 30 else sw60
            dist = s * (e - sw) + 0.01
            RR = np.clip(np.where(np.isfinite(dist), dist, R), 0.5 * R, 3.0 * R)
            dnk = np.ones(n)                   # risk = the swing distance; size by it
            out[f"{v}_risk"] = RR / R
        if p.get("no_target"):
            upk = np.full(n, INF)
        D = p["trail_k"] * tr["atrPct"].to_numpy(float) * e / 100 if "trail_k" in p else None
        lst = last1530 if p.get("flat") == FLAT_1530 else last
        r, xi = engine(s, e, RR, H, L, C, EL, lst, upk, dnk, trail_D=D, be=p.get("be"), ts=p.get("ts"),
                       scale=p.get("scale"))
        out[v] = r
        if v == "base":
            el = np.where(xi >= 0, EL[np.arange(n), np.maximum(xi, 0)], 0)
            out["exit_min"] = tmin + np.nan_to_num(el)
    o = pd.DataFrame(out)
    o.insert(0, "key", tr["key"].to_numpy())
    return o


def main():
    t = pd.read_parquet(HERE / "data" / "trades_lab.parquet")
    t["key"] = t["symbol"] + "|" + t["date"] + "|" + t["tod"].astype(str) + "|" + t["side"] + "|" + t["geom"]
    u = t.drop_duplicates("key")[["key", "symbol", "date", "tod", "side", "geom", "close", "atr_d", "atrPct"]]
    u = u[(u["atr_d"] > 0) & np.isfinite(u["close"])]
    only = sys.argv[1:] or None
    syms = sorted(u["symbol"].unique()) if not only else only
    print(f"unique entries {len(u)}, symbols {len(syms)}", flush=True)
    res, t0 = [], time.time()
    for k, sym in enumerate(syms):
        tr = u[u["symbol"] == sym].reset_index(drop=True)
        res.append(run_symbol(sym, tr))
        if k % 50 == 0:
            print(f"{k}/{len(syms)} {sym} {len(tr)} {time.time() - t0:.0f}s", flush=True)
    o = pd.concat(res, ignore_index=True)
    name = "sim.parquet" if not only else "sim_test.parquet"
    o.to_parquet(HERE / "data" / name, index=False)
    print("done", len(o), f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
