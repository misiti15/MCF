"""Q11: exit variants on 1-minute paths for the extracted trades (open history only; PLAN.md Q11).
    python research/swarm1017/followup/q11_sim.py TRADES.parquet OUT.parquet
Per trade: entry = decision 5-minute bar close (lab convention), R = 0.25 x daily ATR, 1-minute bars from the decision
bar close to 15:55. Stop first inside a minute (gap through the stop fills at the open), target = limit at the target,
stop moves (breakeven / trail) from the next minute (mcf/backtest/engine.py, runner.manage). Production costs as
gates.prod_r (entry x tod multiplier, exit side free on targets, +2c on stop-type fills), x3 extended tier.
Educational only - not financial advice."""
import sys
import time
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research import gates  # noqa: E402

M1 = ROOT / "data" / "cache_hist" / "1Min"
INF = 1e9


@numba.njit(cache=True)
def sim(o, h, l, c, a, b, entry, side, R, up, dn, be, tr, tra):
    """Returns (gross R, kind) with kind 0 target, 1 stop/breakeven/trail, 2 time exit, -1 no path."""
    if b <= a:
        return np.nan, -1
    stop = entry - side * dn * R
    tgt = entry + side * up * R
    mfe = 0.0
    for k in range(a, b):
        if side == 1:
            if l[k] <= stop:
                px = o[k] if o[k] < stop else stop
                return (px - entry) / R, 1
            if up < INF / 2 and h[k] >= tgt:
                return up, 0
            fav = (h[k] - entry) / R
        else:
            if h[k] >= stop:
                px = o[k] if o[k] > stop else stop
                return (entry - px) / R, 1
            if up < INF / 2 and l[k] <= tgt:
                return up, 0
            fav = (entry - l[k]) / R
        if fav > mfe:
            mfe = fav
        if mfe >= be:
            if side == 1:
                stop = max(stop, entry)
            else:
                stop = min(stop, entry)
        if mfe >= tra:
            t = entry + side * (mfe - tr) * R
            if side == 1:
                stop = max(stop, t)
            else:
                stop = min(stop, t)
    return side * (c[b - 1] - entry) / R, 2


@numba.njit(cache=True)
def run(o, h, l, c, A, B, entry, side, R, up, dn, be, tr, tra):
    n = len(A)
    g = np.empty(n)
    kd = np.empty(n, np.int8)
    for i in range(n):
        g[i], kd[i] = sim(o, h, l, c, A[i], B[i], entry[i], side[i], R[i], up[i], dn[i], be[i], tr[i], tra[i])
    return g, kd


def cost_r(gross, kind, px, R, tod, tier):
    """Production R from the gross 1-minute R (gates.prod_r cost model, x3 extended tier as arena.data.outcomes)."""
    ent = (gates.SLIP_PS + px * gates.SLIP_BPS) * gates.tod_cost_mult(tod)
    ex = np.where(kind == 0, 0.0, gates.SLIP_PS + px * gates.SLIP_BPS) + np.where(kind == 1, gates.STOP_EXTRA, 0.0)
    return gross - tier * (ent + ex) / R


if __name__ == "__main__":
    T = pd.read_parquet(sys.argv[1])
    fam_c = {"MF", "NS", "RW", "ST", "L3", "CWT"}
    T = T[T.family.isin(fam_c)].reset_index(drop=True)
    T["date"] = pd.to_datetime(T["date"])
    isMF = T.family.eq("MF").to_numpy()
    isB = (T.setup.str.startswith(("CWT12", "CWT14")) & T.side.eq("long")).to_numpy()
    side = np.where(T.side.eq("long"), 1, -1).astype(np.int64)
    up0 = T.geom.map({"t1s1": 1.0, "t05s1": 0.5, "t1s05": 1.0}).to_numpy(float)
    dn0 = T.geom.map({"t1s1": 1.0, "t05s1": 1.0, "t1s05": 0.5}).to_numpy(float)
    R = 0.25 * T.atr_d.to_numpy(float)
    entry = T.close.to_numpy(float)
    V = {  # name: (rows, up, dn, be, trail_r, trail_after)
        "base": (np.ones(len(T), bool), up0, dn0, INF, INF, INF),
        "s05": (np.ones(len(T), bool), up0, np.full(len(T), 0.5), INF, INF, INF),
        "be025": (isMF, up0, dn0, 0.25, INF, INF),
        "be05": (isMF, up0, dn0, 0.5, INF, INF),
        "be075": (isMF, up0, dn0, 0.75, INF, INF),
        "b0_tgt_tr1a1": (isB, up0, dn0, INF, 1.0, 1.0),
        "b1_tr05a05": (isB, np.full(len(T), INF), dn0, INF, 0.5, 0.5),
        "b2_tr05a1": (isB, np.full(len(T), INF), dn0, INF, 0.5, 1.0),
        "b3_tr1a05": (isB, np.full(len(T), INF), dn0, INF, 1.0, 0.5),
        "b4_tr1a1": (isB, np.full(len(T), INF), dn0, INF, 1.0, 1.0),
    }
    G = {k: np.full(len(T), np.nan) for k in V}
    K = {k: np.full(len(T), -1, np.int8) for k in V}
    dkey = (T.date.dt.year * 10000 + T.date.dt.month * 100 + T.date.dt.day).to_numpy(np.int64)
    tod = T.tod.to_numpy(np.int64)
    t0 = time.time()
    for i, (sym, grp) in enumerate(T.groupby("symbol").indices.items()):
        f = M1 / f"{sym}.parquet"
        if not f.exists():
            continue
        x = pd.read_parquet(f)
        ts = x.index
        key = ((ts.year * 10000 + ts.month * 100 + ts.day).to_numpy(np.int64) * 10000 + (ts.hour * 100 + ts.minute).to_numpy(np.int64))
        o, h, l, c = (x[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        A = np.searchsorted(key, dkey[grp] * 10000 + tod[grp])          # first minute after the decision bar close
        B = np.searchsorted(key, dkey[grp] * 10000 + 1555)              # minutes < 15:55 (last = the 15:54 bar)
        okd = (A < len(key)) & (key[np.minimum(A, len(key) - 1)] // 10000 == dkey[grp])
        A = np.where(okd, A, 0)
        B = np.where(okd, B, 0)
        for name, (rows, up, dn, be, tr, tra) in V.items():
            sel = grp[rows[grp]]
            if not len(sel):
                continue
            ss = rows[grp]

            def arr(v):
                return np.broadcast_to(np.asarray(v, float), (len(T),))[sel].copy() if np.ndim(v) else np.full(len(sel), float(v))
            g, kd = run(o, h, l, c, A[ss], B[ss], entry[sel], side[sel], R[sel], arr(up), arr(dn), arr(be), arr(tr), arr(tra))
            G[name][sel], K[name][sel] = g, kd
        if i % 100 == 0:
            print(i, sym, f"{time.time()-t0:.0f}s", flush=True)
    out = T[["setup", "family", "side", "geom", "date", "symbol", "tod", "r", "ctrl", "tier", "spy_fo", "qqq_fo", "breadth"]].copy()
    px, tier, todf = T.close.to_numpy(float), T.tier.to_numpy(float), T.tod.to_numpy(float)
    for name in V:
        out[f"g_{name}"] = G[name].astype(np.float32)
        out[f"k_{name}"] = K[name]
        out[f"r_{name}"] = cost_r(G[name], K[name], px, R, todf, tier).astype(np.float32)
    out.to_parquet(sys.argv[2], index=False)
    print("done", len(out), f"{time.time()-t0:.0f}s")
