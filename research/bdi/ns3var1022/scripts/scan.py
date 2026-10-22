"""ns3var1022 step 1: every NS3-family candidate bar on the open two-year frames, with entry features and the forward
5-minute path (for the exit simulator), plus one random same-minute partner (same filters on liquidity) with its path.

Candidate superset (PLAN.md): vwapDistPct > 0 & previous bar's vwapDistPct <= 0 & fromOpen < -1.5, bar close
09:50-15:00, adv20 >= 95M, daily ATR > 0, finite lab outcome. The P0 mask adds sma50_dist_pct > 0 & fromOpen < -2.
Also stores, per candidate, the reclaim-hold flags used by the long ideas (E2-E4).
The locked block (2024-11-01..2025-02-28) is never read (history2y/lib refuses it; asserted below).
Educational only - not financial advice.

    python research/bdi/ns3var1022/scripts/scan.py 3      # -> $NV22/cand/<month>.npz
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from nv import G21SCR, NV, lib, no_locked

NP = 80          # max forward bars stored (09:55..15:00 from the frame; 15:05..15:55 appended by load.py from tail.py)
FEATS = ["close", "atr_d", "gap", "adv20", "fromOpen", "vwapDistPct", "sma50_dist_pct", "volumeRatio", "atrPct", "rsi",
         "rsi5", "spy_fo", "qqq_fo", "breadth", "r_short_t1s1", "win_short_t1s1", "r_short_t05s1", "win_short_t05s1",
         "r_short_t1s05", "win_short_t1s05", "r_long_t1s1", "win_long_t1s1"]


def runs_below(v, newkey):
    """Consecutive bars with vwapDistPct <= 0 ending at the PREVIOUS bar (per symbol-day)."""
    n = len(v)
    out = np.zeros(n, np.int32)
    cnt = 0
    for i in range(n):
        if newkey[i]:
            cnt = 0
        out[i] = cnt
        cnt = cnt + 1 if v[i] <= 0 else 0
    return out


def month_job(month):
    t0 = time.time()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    sym = f["symbol"].to_numpy()
    dat = f["date"].astype(str).to_numpy()
    key = np.char.add(np.char.add(sym.astype(str), "|"), dat.astype(str))
    newk = np.r_[True, key[1:] != key[:-1]]
    tod = f["tod"].to_numpy()
    v = f["vwapDistPct"].to_numpy(float)
    pv = np.r_[np.nan, v[:-1]]
    pv[newk] = np.nan
    rb = runs_below(v, newk)
    # min vwapDistPct over the 6 bars before this one (same symbol-day)
    lag = []
    for k in range(1, 7):
        x = np.r_[np.full(k, np.nan), v[:-k]]
        kk = np.r_[np.full(k, ""), key[:-k]]
        lag.append(np.where(kk == key, x, np.nan))
    with np.errstate(invalid="ignore"), __import__("warnings").catch_warnings():
        __import__("warnings").simplefilter("ignore")
        mn6 = np.nanmin(np.vstack(lag), axis=0)
    # breadth 2-bar change (same day, from 10:00), as gates1021 context_extra
    c = lib.load_context(month).sort_values(["date", "tod"]).reset_index(drop=True)
    b = c["breadth"].to_numpy(float)
    same = np.r_[False, False, c["date"].to_numpy()[2:] == c["date"].to_numpy()[:-2]]
    prev2 = np.r_[np.nan, np.nan, b[:-2]]
    c["d2"] = np.where(same & (c["tod"].to_numpy() >= 1000), b - prev2, np.nan)
    f = f.merge(c[["date", "tod", "d2"]], on=["date", "tod"], how="left")      # keeps row order (left merge)
    assert (f["symbol"].to_numpy() == sym).all()
    # SPY / QQQ own VWAP side at (date, tod)
    ix = f[f["symbol"].isin(["SPY", "QQQ"])].pivot_table(index=["date", "tod"], columns="symbol", values="vwapDistPct")
    ix.columns = [f"{x.lower()}_vwap" for x in ix.columns]
    f = f.merge(ix.reset_index(), on=["date", "tod"], how="left")
    assert (f["symbol"].to_numpy() == sym).all()
    adv = f["adv20"].fillna(0).to_numpy()
    atr = f["atr_d"].to_numpy(float)
    fo = f["fromOpen"].to_numpy(float)
    fin = np.isfinite(f["r_short_t1s1"].to_numpy(float))
    base = (adv >= 95e6) & (atr > 0) & fin & (tod >= 950) & (tod <= 1500)
    cand = base & (v > 0) & (pv <= 0) & (fo < -1.5)
    idx = np.flatnonzero(cand)
    # day end positions
    ends = np.r_[np.flatnonzero(newk)[1:], len(f)]
    starts = np.flatnonzero(newk)
    grp = np.cumsum(newk) - 1
    endpos = ends[grp]
    H, L, C, T = (f[k].to_numpy(float) for k in ("high", "low", "close", "tod"))

    def paths(ii):
        n = len(ii)
        out = {k: np.full((n, NP), np.nan, np.float32) for k in ("h", "l", "c", "t", "v")}
        for j, i in enumerate(ii):
            a, e = i + 1, min(endpos[i], i + 1 + NP)
            m = e - a
            if m <= 0:
                continue
            out["h"][j, :m] = H[a:e]
            out["l"][j, :m] = L[a:e]
            out["c"][j, :m] = C[a:e]
            out["t"][j, :m] = T[a:e]
            out["v"][j, :m] = v[a:e]
        return out

    P = paths(idx)
    # random same-minute partner (another symbol, same base liquidity filter), seeded per month
    rng = np.random.default_rng(int(month.replace("-", "")))
    bdf = pd.DataFrame({"i": np.flatnonzero(base)})
    bdf["k"] = dat[bdf["i"]] + "|" + tod[bdf["i"]].astype(str)
    groups = bdf.groupby("k")["i"].apply(np.asarray).to_dict()
    part = np.full(len(idx), -1)
    for j, i in enumerate(idx):
        g = groups.get(dat[i] + "|" + str(tod[i]))
        if g is None:
            continue
        g = g[sym[g] != sym[i]]
        if len(g):
            part[j] = rng.choice(g)
    pi = np.where(part >= 0, part, 0)
    Q = paths(pi)
    for k in Q:
        Q[k][part < 0] = np.nan
    # peer median fromOpen at the bar (gates1021 peers: top-5 by TRAIN daily-return correlation)
    peers = json.load(open(G21SCR / "peers.json"))
    fo_w = f.pivot_table(index=["date", "tod"], columns="symbol", values="fromOpen", aggfunc="first")
    pm = np.full(len(idx), np.nan)
    for j, i in enumerate(idx):
        p = [x for x in peers.get(sym[i], []) if x in fo_w.columns]
        if not p:
            continue
        try:
            vv = fo_w.loc[(f["date"].iat[i], tod[i]), p].to_numpy(float)
        except KeyError:
            continue
        vv = vv[np.isfinite(vv)]
        if len(vv) >= 3:
            pm[j] = float(np.median(vv))
    out = {"symbol": sym[idx].astype(str), "date": dat[idx].astype(str), "tod": tod[idx].astype(np.int32),
           "runs_below": rb[idx], "min6": mn6[idx], "d2": f["d2"].to_numpy(float)[idx],
           "spy_vwap": f["spy_vwap"].to_numpy(float)[idx] if "spy_vwap" in f else np.full(len(idx), np.nan),
           "qqq_vwap": f["qqq_vwap"].to_numpy(float)[idx] if "qqq_vwap" in f else np.full(len(idx), np.nan),
           "peer_med": pm, "p_close": C[pi], "p_atr": atr[pi], "p_gap": f["gap"].to_numpy(float)[pi],
           "p_ok": part >= 0, "p_symbol": sym[pi].astype(str)}
    for k in FEATS:
        out[k] = f[k].to_numpy(float)[idx]
    for k, a in P.items():
        out["P" + k] = a
    for k, a in Q.items():
        out["Q" + k] = a
    np.savez_compressed(NV / "cand" / f"{month}.npz", **out)
    return month, len(idx), round(time.time() - t0, 1)


def main():
    (NV / "cand").mkdir(parents=True, exist_ok=True)
    months = lib.months()
    if len(sys.argv) > 2:
        months = sys.argv[2].split(",")
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    with Pool(workers) as p:
        for r in p.imap_unordered(month_job, months):
            print(r, flush=True)


if __name__ == "__main__":
    main()
