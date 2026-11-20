"""Outside exit methods (PLAN.md): walk the first signal per (setup, symbol, day) of bt_lab1104 on cache_hist 1-minute
bars with BEREPLAY geometry/costs, and score 22 exit configs (O1 chandelier, O2 scale-out, O3 SPY turn, O4 clock) as
paired deltas vs the base exit. Locked block 2024-11-01..2025-02-28 filtered at read and asserted absent.
Usage: python walk.py OUT.parquet [procs]. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research/guild/1109/bereplay"))
import bereplay as BR  # noqa
from bereplay import G  # noqa
XTRA = 0.01
CFG = ([("O1", a, k) for a in (0.5, 1.0) for k in (3, 6, 10)] + [("O2", x, r) for x in (0.5, 1.0) for r in ("orig", "BE")]
       + [("O3", z, m) for z in (0.25, 0.5) for m in (-99.0, 0.5)] + [("O4", tc, c) for tc in (720, 780, 840, 900) for c in ("all", "win")])
NAMES = [f"{c}_{a}_{b}" for c, a, b in CFG]
assert len(CFG) == 22
ix = "__index_level_0__"


def load(sym):
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists(): return None
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < BR.TL0) | (pds.field(ix) >= BR.TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= BR.TL0) & (df.index < BR.TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); keep = (mm >= 570) & (mm < 955)
    return df[keep], mm[keep]


SPY = None
def spy_init():
    global SPY
    df, mm = load("SPY"); dd = df.index.date; c = df.close.to_numpy(float)
    st = np.r_[0, np.flatnonzero(dd[1:] != dd[:-1]) + 1]; en = np.r_[st[1:], len(dd)]
    SPY = {dd[a]: (mm[a:b], c[a:b]) for a, b in zip(st, en)}


def first(m):
    return int(np.argmax(m)) if m.any() else 10 ** 9


def gwalk(o, h, l, c, e, s, lev, U, i0=0):
    n = len(c)
    fav = (h - e) if s > 0 else (e - l)
    hit = (l <= lev) if s > 0 else (h >= lev)
    i_s = first(hit[i0:]) + i0; i_t = first(fav[i0:] >= U) + i0 if np.isfinite(U) else 10 ** 9
    if i_s <= i_t and i_s < n:
        return (o[i_s] if s * (o[i_s] - lev[i_s]) <= 0 else lev[i_s]), 1, i_s
    if i_t < n: return e + s * U, 2, i_t
    return c[-1], 0, n - 1


def sym_job(args):
    sym, tr = args
    if SPY is None: spy_init()
    x = load(sym)
    if x is None: return None
    df, mm = x; dd = df.index.date
    O, H, L, C = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    st = np.r_[0, np.flatnonzero(dd[1:] != dd[:-1]) + 1]; en = np.r_[st[1:], len(dd)]
    pc = np.r_[C[0], C[:-1]]; pc[st] = C[st]  # previous close within the day (first bar: own close -> TR = h-l basically)
    TR = np.maximum(H - L, np.maximum(np.abs(H - pc), np.abs(L - pc))); TR[st] = (H - L)[st]
    span = {dd[a]: (a, b) for a, b in zip(st, en)}
    cs = np.r_[0, np.cumsum(TR)]
    out = []
    for r in tr.itertuples(index=False):
        if r.date not in span or r.date not in SPY: continue
        a, b = span[r.date]; t0 = r.tod // 100 * 60 + r.tod % 100
        j = a + int(np.searchsorted(mm[a:b], t0))
        if j >= b: continue
        o, h, l, c, m_ = O[j:b], H[j:b], L[j:b], C[j:b], mm[j:b]; n = len(c)
        e = float(r.close); R = .25 * float(r.atr_d); up, dn = BR.GK[r.geom]; D = dn * R; U = up * R; s = r.side
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0
        ecost = (BR.SL + e * BP_) * float(G.tod_cost_mult(np.array([r.tod]))[0])

        def net(px, kd, extra=0.0):
            xc = (0.0 if kd == 2 else BR.SL + px * BP_) + (BR.SX if kd == 1 else 0.0) + extra
            return (s * (px - e) / R - tier * (ecost + xc) / R) / dn
        lev0 = np.full(n, e - s * D)
        bpx, bkd, bix = gwalk(o, h, l, c, e, s, lev0, U); base = net(bpx, bkd)
        mark = s * (c - e) / D
        res = []
        # O1 chandelier
        g = np.arange(j, b); lo = np.maximum(g - 1 - 13, a); hi = np.maximum(g - 1, a)  # ATR over bars lo..hi (through i-1)
        atrp = (cs[hi + 1] - cs[lo]) / (hi - lo + 1)
        cb = np.maximum.accumulate(c) if s > 0 else np.minimum.accumulate(c); pcb = np.r_[e, cb[:-1]]
        for _, A, K in CFG[:6]:
            armed = s * (pcb - e) >= A * D
            lev = np.where(armed, pcb - s * K * atrp, e - s * D)
            lev = np.maximum.accumulate(np.maximum(lev, e - D)) if s > 0 else np.minimum.accumulate(np.minimum(lev, e + D))
            px, kd, ii = gwalk(o, h, l, c, e, s, lev, U)
            res.append(net(px, kd, XTRA if (kd == 1 and lev[ii] != e - s * D) else 0.0) - base)
        # O2 scale-out
        fav = (h - e) if s > 0 else (e - l); hit0 = (l <= e - s * D) if s > 0 else (h >= e + s * D)
        i_s = first(hit0)
        for _, X, RR in CFG[6:10]:
            if X * D >= U: res.append(0.0); continue
            i_x = first(fav >= X * D)
            if i_x >= n or i_s <= i_x: res.append(0.0); continue
            n1 = net(e + s * X * D, 0, XTRA)
            lev = lev0.copy()
            if RR == "BE" and i_x + 1 < n: lev[i_x + 1:] = e
            px, kd, ii = gwalk(o, h, l, c, e, s, lev, U, i0=i_x)
            res.append(0.5 * n1 + 0.5 * net(px, kd, XTRA if (kd == 1 and RR == "BE" and ii > i_x) else 0.0) - base)
        # O3 SPY turn
        sm, sc_ = SPY[r.date]
        k0 = int(np.searchsorted(sm, m_[0], "left")) - 1; spy0 = sc_[max(k0, 0)]
        ki = np.clip(np.searchsorted(sm, m_, "right") - 1, 0, len(sm) - 1); sc = sc_[ki]
        if s > 0:
            best = np.maximum.accumulate(np.maximum(sc, spy0)); retr = (best - sc) / best * 100
        else:
            best = np.minimum.accumulate(np.minimum(sc, spy0)); retr = (sc - best) / best * 100
        for _, Z, M in CFG[10:14]:
            f = first((retr >= Z) & (mark >= M))
            res.append(net(c[f], 0, XTRA) - base if f < bix else 0.0)
        # O4 clock
        for _, TC, CC in CFG[14:]:
            f = int(np.searchsorted(m_, TC - 1))
            ok = f < bix and f < n and (CC == "all" or mark[f] >= 0.5)
            res.append(net(c[f], 0, XTRA) - base if ok else 0.0)
        out.append([r.setup, s, r.geom, r.date, base, float(r.r)] + res)
    return out


BP_ = BR.BP


def main():
    OUT = sys.argv[1]; procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    t = BR.load_lists(None)
    t = t.sort_values(["setup", "symbol", "date", "tod"]).drop_duplicates(["setup", "symbol", "date"]).reset_index(drop=True)
    print("first-per-day trades", len(t), flush=True)
    rows = []
    with Pool(procs) as pool:
        for k, res in enumerate(pool.imap_unordered(sym_job, [(s, g) for s, g in t.groupby("symbol")], chunksize=4)):
            if res: rows += res
            if k % 200 == 0: print(f"symbols {k}", flush=True)
    X = pd.DataFrame(rows, columns=["setup", "side", "geom", "date", "base", "r5"] + NAMES)
    for k in ["base", "r5"] + NAMES: X[k] = X[k].astype("float32")
    X.to_parquet(OUT, index=False); print("rows", len(X), "avg base", X.base.mean())


if __name__ == "__main__":
    main()
