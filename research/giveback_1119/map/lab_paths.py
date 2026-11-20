"""Giveback map, 2-year lab part: walk the first signal per (setup, symbol, day) of the bt_lab1104 lists on 1-minute
cache_hist bars with BEREPLAY conventions (live geometry, stop-first, bt_all costs) and record path stats + checkpoint
states (PLAN.md). Locked block 2024-11-01..2025-02-28 filtered at read and asserted absent.
Usage: python lab_paths.py OUT.parquet [procs]. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research/guild/1109/bereplay"))
import bereplay as BR  # noqa
from bereplay import G, lib  # noqa
CK = (5, 10, 15, 30, 45, 60, 90, 120); XTRA = 0.01


def sym_job(args):
    sym, tr = args
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists(): return None
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < BR.TL0) | (pds.field(ix) >= BR.TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= BR.TL0) & (df.index < BR.TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); keep = (mm >= 570) & (mm < 955)
    df = df[keep]; mm = mm[keep]; dd = df.index.date
    O, H, L, C = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    st = np.r_[0, np.flatnonzero(dd[1:] != dd[:-1]) + 1]; en = np.r_[st[1:], len(dd)]
    span = {dd[a]: (a, b) for a, b in zip(st, en)}
    out = []
    for r in tr.itertuples(index=False):
        if r.date not in span: continue
        a, b = span[r.date]; t0 = r.tod // 100 * 60 + r.tod % 100
        j = a + int(np.searchsorted(mm[a:b], t0))
        o, h, l, c, m_ = O[j:b], H[j:b], L[j:b], C[j:b], mm[j:b]
        n = len(c)
        if n == 0: continue
        e = float(r.close); R = .25 * float(r.atr_d); up, dn = BR.GK[r.geom]; D = dn * R; U = up * R; s = r.side
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0
        ecost = (BR.SL + e * BR.BP) * float(G.tod_cost_mult(np.array([r.tod]))[0])
        fav = ((h - e) if s > 0 else (e - l)) / D; adv = ((e - l) if s > 0 else (h - e)) / D
        hit = (l <= e - D) if s > 0 else (h >= e + D)
        i_s = BR.first(hit); i_t = BR.first(fav * D >= U)
        if i_s <= i_t and i_s < n:
            px = o[i_s] if s * (o[i_s] - (e - s * D)) <= 0 else e - s * D; kd = 1; ex = i_s
        elif i_t < n: px = e + s * U; kd = 2; ex = i_t
        else: px = c[-1]; kd = 0; ex = n - 1
        xcost = (0.0 if kd == 2 else BR.SL + px * BR.BP) + (BR.SX if kd == 1 else 0.0)
        fin = (s * (px - e) / R - tier * (ecost + xcost) / R) / dn
        fv = fav[:ex + 1]; av = adv[:ex + 1]
        if kd == 1 and ex > 0: fv = fav[:ex]  # stop-first: the stop bar's high does not count toward MFE
        mfe = float(fv.max()); tm = int(fv.argmax()); mae = float(av.max())
        row = [r.setup, s, r.geom, sym, r.date, r.tod, fin, kd, ex + 1, int(m_[ex]), mfe, mae, tm + 1, up / dn]
        for t in CK:
            if ex > t - 1:
                cc = c[t - 1]; mk = s * (cc - e) / D
                xn = (s * (cc - e) / R - tier * (ecost + BR.SL + cc * BR.BP + XTRA) / R) / dn
                row += [mk, float(fav[:t].max()), float(adv[:t].max()), fin - xn]
            else:
                row += [np.nan] * 4
        out.append(row)
    return out


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
    cols = ["setup", "side", "geom", "symbol", "date", "tod", "fin", "kind", "hold", "xmin", "mfe", "mae", "tmfe", "tgtR"]
    for t_ in CK: cols += [f"mk{t_}", f"mf{t_}", f"ma{t_}", f"rem{t_}"]
    X = pd.DataFrame(rows, columns=cols)
    for k in X.columns:
        if X[k].dtype == float: X[k] = X[k].astype("float32")
    X.to_parquet(OUT, index=False); print("rows", len(X), "avg fin", X.fin.mean())


if __name__ == "__main__":
    main()
