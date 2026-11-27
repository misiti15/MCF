"""RWOUT-1127 (PREREG.md): remove every non-empty subset of Primary's shorts (L3, RW3, RW5) from the E4 book (BASE, LO)
vs keep, vs 500 size-matched random removals (same number of keep-run lots, drawn from the three shorts' taken lots,
per period) and a constant cut. Engine = research/cfprimary_1127/e4nb.py (parity vs the Python engine re-checked).
Usage (cwd repo): python research/rwout_1127/rwrun.py W OUTDIR. Educational only - not financial advice."""
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "research/cfprimary_1127")
import e4nb as E  # noqa: E402

W, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NR, SEED = 500, 1127
C, DAYS, ST, PATH, A = E.load(W)
E.no_locked(DAYS)
E.no_locked(C.date.unique())
PER = np.array([C.per.iloc[ST[i]] for i in range(len(DAYS))])
DPC = C.per.to_numpy()
SI = A["si"]
CFG = {"L3-out": [0], "RW3-out": [1], "RW5-out": [2], "L3+RW3-out": [0, 1], "L3+RW5-out": [0, 2],
       "RW3+RW5-out": [1, 2], "all-three-out": [0, 1, 2]}
CTX = {"BASE": False, "LO": True}
ALL = np.arange(len(DAYS))
CT = np.flatnonzero(np.isin(PER, ["CHECK", "T2"]))
SHORT = SI <= 2


def met(ref, cfg, rm):
    r, c = ref.sum(1), cfg.sum(1); d = c - r; n = len(d)
    sd = d.std(ddof=1)
    t = d.mean() / (sd / np.sqrt(n)) if sd > 0 else 0.0
    w5 = lambda x: np.sort(x)[:5].mean()  # noqa: E731
    fl = lambda x: pd.Series(x).rolling(20).sum().min()  # noqa: E731
    tot = d.sum(); bi = int(np.argmax(d))
    own = ref[:, rm].sum(1)
    return dict(n=n, ref=r.mean(), avg_cfg=c.mean(), dR=d.mean(), t=t, red_ref=(r < 0).mean() * 21,
                red_cfg=(c < 0).mean() * 21, w5_ref=w5(r), w5_cfg=w5(c), le10_ref=int((r <= -10).sum()),
                le10_cfg=int((c <= -10).sum()), floor_ref=fl(r), floor_cfg=fl(c),
                best_share=(d[bi] / tot) if tot > 0 else np.nan, dR_wo_best=np.delete(d, bi).mean(),
                setup_dR_month=list((cfg - ref).sum(0) / n * 21),
                removed_own_R_month=own.sum() / n * 21, removed_own_wo_best=(own.sum() - own.max()) / (n - 1),
                removed_own_best_share=(own.max() / own.sum()) if own.sum() > 0 else np.nan)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sys.path.insert(0, "research/rwout_1127")
    from cfrun_parity import py_day  # noqa: E402  (cfrun.py py_day verbatim, A/PATH passed in)
    res = {"cands": int(len(C)), "by_setup": {E.SETUPS[s]: int((SI == s).sum()) for s in range(4)},
           "days": {p: int((PER == p).sum()) for p in ("FIT", "CHECK", "T2")}}
    rng = np.random.default_rng(0)
    sample = np.sort(rng.choice(len(DAYS), 80, replace=False))
    par = {}
    for cx, lo in CTX.items():
        for nm, rm in (("keep", []), ("RW3+RW5-out", [1, 2])):
            kp = ~np.isin(SI, rm)
            Rn, _, _ = E.run(A, ST, PATH, sample, kp, lo)
            Rp = np.array([py_day(A, PATH, ST[d], ST[d + 1], kp, lo) for d in sample])
            par[f"{cx}|{nm}"] = float(np.abs(Rn.sum(1) - Rp.sum(1)).max())
    res["parity_max_abs_day_diff"] = par
    print("parity", par, flush=True)
    assert max(par.values()) < 0.01, "numba engine parity failed"
    rows, daily = [], {}
    for cx, lo in CTX.items():
        Rref, Nref, TKref = E.run(A, ST, PATH, ALL, np.ones(len(C), bool), lo)
        daily[(cx, "keep")] = Rref
        for cfg, rm in CFG.items():
            mask = ~np.isin(SI, rm)
            Rc, Nc, _ = E.run(A, ST, PATH, ALL, mask, lo)
            daily[(cx, cfg)] = Rc
            fday = np.ones(len(DAYS)); sh = {}; nrm = {}
            for p in ("FIT", "CHECK", "T2"):
                inp = DPC == p
                nrm[p] = int((TKref & inp & ~mask).sum())
                sh[p] = nrm[p] / max((TKref & inp).sum(), 1); fday[PER == p] = 1 - sh[p]
            Rk, _, _ = E.run(A, ST, PATH, ALL, np.ones(len(C), bool), lo, fday)
            daily[(cx, cfg + "|CUT")] = Rk
            g = np.random.default_rng(SEED)
            pools = {p: np.flatnonzero(TKref & SHORT & (DPC == p)) for p in ("CHECK", "T2")}
            rnd = np.zeros((NR, len(CT)))
            for j in range(NR):
                kr = np.ones(len(C), bool)
                for p, ix in pools.items():
                    kr[g.choice(ix, min(nrm[p], len(ix)), replace=False)] = False
                Rr, _, _ = E.run(A, ST, PATH, CT, kr, lo)
                rnd[j] = Rr.sum(1)
            np.save(OUT / f"rnd_{cx}_{cfg}.npy", rnd.astype(np.float32))
            for p in ("FIT", "CHECK", "T2"):
                ix = np.flatnonzero(PER == p)
                m = met(Rref[ix], Rc[ix], rm); mk = met(Rref[ix], Rk[ix], rm)
                row = dict(ctx=cx, cfg=cfg, per=p, n_removed_lots=nrm[p], cut_s=sh[p], lots_ref=int(Nref[ix].sum()),
                           lots_cfg=int(Nc[ix].sum()), cut_dR=mk["dR"], cut_red=mk["red_cfg"], cut_w5=mk["w5_cfg"],
                           cut_floor=mk["floor_cfg"], **m)
                if p != "FIT":
                    sel = np.isin(CT, ix)
                    rd = rnd[:, sel].mean(1) - Rref[ix].sum(1).mean()
                    row.update(rnd_p95=float(np.percentile(rd, 95)), rnd_mean=float(rd.mean()),
                               pctile=float((rd < m["dR"]).mean() * 100), sel_value=m["dR"] - float(rd.mean()))
                    keepers = [s for s in range(4) if s not in rm]
                    ok = [m["dR"] > 0, m["dR"] > row["rnd_p95"] and m["t"] >= 2.8, m["red_ref"] - m["red_cfg"] >= 0.5,
                          m["w5_cfg"] >= 1.05 * m["w5_ref"], m["floor_cfg"] >= m["floor_ref"],
                          m["dR"] > 0 and m["best_share"] < 0.25,
                          min(m["setup_dR_month"][s] for s in keepers) >= -2.0]
                    row.update({f"bar{i + 1}": bool(v) for i, v in enumerate(ok)}, all_bar=bool(all(ok)))
                rows.append(row)
                print({k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for k, v in row.items()
                       if k != "setup_dR_month"}, flush=True)
            print(cx, cfg, "done", round(time.time() - t0), "s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "results.csv", index=False)
    for (cx, cfg), R in daily.items():
        pd.DataFrame(R, columns=E.SETUPS).assign(date=DAYS, per=PER).to_parquet(OUT / f"day_{cx}_{cfg.replace('|', '_')}.parquet")
    verdict = {}
    for cfg in CFG:
        sub = df[(df.cfg == cfg) & (df.per != "FIT")]
        verdict[cfg] = "PASS" if sub.all_bar.all() else "FAIL"
    res["verdict_bench"] = verdict
    json.dump(res, open(OUT / "summary.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
