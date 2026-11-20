"""Targets class, 2-year lab: parent bracket vs C1..C6 (PLAN.md) on bt_lab1104 first signals, BEREPLAY walk as
map/lab_paths.py. Locked block 2024-11-01..2025-02-28 filtered at read and asserted absent.
Usage: python lab_walk.py OUT.parquet [procs]. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research/guild/1109/bereplay"))
import bereplay as BR  # noqa
from bereplay import G  # noqa
XTRA = 0.01
VARS = ["P", "C1", "C2", "C3", "C4", "C5", "C6"]


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
        o, h, l, c = O[j:b], H[j:b], L[j:b], C[j:b]
        n = len(c)
        if n == 0: continue
        e = float(r.close); R = .25 * float(r.atr_d); up, dn = BR.GK[r.geom]; D = dn * R; s = r.side
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0
        ecost = (BR.SL + e * BR.BP) * float(G.tod_cost_mult(np.array([r.tod]))[0])
        fav = ((h - e) if s > 0 else (e - l)) / D
        hit = (l <= e - D) if s > 0 else (h >= e + D)
        i_s = BR.first(hit)
        stop_px = (o[i_s] if s * (o[i_s] - (e - s * D)) <= 0 else e - s * D) if i_s < n else np.nan
        Tu = up / dn  # parent target in stop units (inf for hold)

        def unit(px, xc):  # R in stop units, entry cost + exit cost xc ($/sh)
            return s * (px - e) / D - tier * (ecost + xc) / (R * dn)

        def stop_r(): return unit(stop_px, BR.SL + stop_px * BR.BP + BR.SX)
        def flat_r(k): return unit(c[k], BR.SL + c[k] * BR.BP)

        def bracket(L, early):  # full exit at level L (stop units) or stop or EOD
            i_t = BR.first(fav >= L) if np.isfinite(L) else 10 ** 9
            if i_s <= i_t and i_s < n: return stop_r(), 1
            if i_t < n:
                px = e + s * L * D
                return unit(px, (BR.SL + px * BR.BP + XTRA) if early else 0.0), 2
            return flat_r(n - 1), 0
        rp, kp = bracket(Tu, False)
        res = [rp]
        for Lp in (0.6, 0.8):  # C1, C2 partial 50%
            if Lp < Tu:
                i_p = BR.first(fav >= Lp)
                if i_p < min(i_s, n):
                    px = e + s * Lp * D
                    res.append(0.5 * unit(px, BR.SL + px * BR.BP + XTRA) + 0.5 * rp); continue
            res.append(rp)
        for Lc in (1.0, 1.5):  # C3, C4 cap
            res.append(bracket(Lc, True)[0] if Lc < Tu else rp)
        res.append(stop_r() if i_s < n else flat_r(n - 1))  # C5 no target, EOD
        hz = 120  # C6 no target, 120-minute exit
        if i_s < min(hz, n): res.append(stop_r())
        elif n > hz: res.append(unit(c[hz - 1], BR.SL + c[hz - 1] * BR.BP + XTRA))
        else: res.append(flat_r(n - 1))
        out.append([r.setup, s, r.geom, sym, r.date, Tu] + res)
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
    X = pd.DataFrame(rows, columns=["setup", "side", "geom", "symbol", "date", "tgtR"] + VARS)
    for k in ["tgtR"] + VARS: X[k] = X[k].astype("float32")
    X.to_parquet(OUT, index=False); print("rows", len(X), X[VARS].mean().round(4).to_dict())


if __name__ == "__main__":
    main()
