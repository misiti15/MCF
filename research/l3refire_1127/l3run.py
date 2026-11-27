"""L3REFIRE-1127 bench (PREREG.md): 7 L3-only repeat-lot rules on Primary's E4 book (BASE, LO) vs keep, vs 500
size-matched random L3 skips, a constant cut and L3-OUT. Engine e4l3.py (mode 0 parity vs e4nb asserted first).
Usage (cwd repo): python research/l3refire_1127/l3run.py W OUTDIR. Educational only - not financial advice."""
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "research/l3refire_1127")
import e4l3 as L  # noqa: E402
E = L.E

W, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NR, SEED = 500, 1127
C, DAYS, ST, PATH, A = L.load(W)
E.no_locked(DAYS); E.no_locked(C.date.unique())
assert not C.date.between("2024-11-01", "2025-02-28").any(), "locked block row found"
PER = np.array([C.per.iloc[ST[i]] for i in range(len(DAYS))])
DPC = C.per.to_numpy(); SI = A["si"]; RR = A["rr"]
IS_L3 = SI == 0
BIG = 10 ** 6
CFG = {"OPEN1": (1, 1), "OPEN2": (1, 2), "GAP30": (2, 30), "GAP60": (2, 60), "GAP120": (2, 120), "NOSTOP": (3, 0),
       "FIRST1": (2, BIG)}
CTX = {"BASE": False, "LO": True}
ALL = np.arange(len(DAYS))
CT = np.flatnonzero(np.isin(PER, ["CHECK", "T2"]))
ONES = np.ones(len(C), bool)


def tstat(d):
    sd = d.std(ddof=1)
    return d.mean() / (sd / np.sqrt(len(d))) if sd > 0 else 0.0


def met(ref, cfg, nref, ncfg):
    r, c = ref.sum(1), cfg.sum(1); d = c - r; n = len(d)
    tot = d.sum(); bi = int(np.argmax(d))
    l3r, l3c = ref[:, 0], cfg[:, 0]
    bl = int(np.argmax(l3c))
    return dict(n=n, ref=r.mean(), avg_cfg=c.mean(), dR=d.mean(), t=tstat(d),
                best_share=(d[bi] / tot) if tot > 0 else np.nan, dR_wo_best=np.delete(d, bi).mean(),
                w5_ref=np.sort(r)[:5].mean(), w5_cfg=np.sort(c)[:5].mean(),
                red_ref=(r < 0).mean() * 21, red_cfg=(c < 0).mean() * 21,
                le10_ref=int((r <= -10).sum()), le10_cfg=int((c <= -10).sum()),
                setup_dR_month=list((cfg - ref).sum(0) / n * 21),
                l3_lots_ref=int(nref[:, 0].sum()), l3_lots_cfg=int(ncfg[:, 0].sum()),
                lots_ref=int(nref.sum()), lots_cfg=int(ncfg.sum()),
                l3_avg_ref=l3r.sum() / max(nref[:, 0].sum(), 1), l3_avg_cfg=l3c.sum() / max(ncfg[:, 0].sum(), 1),
                l3_avg_cfg_wo_best=(l3c.sum() - l3c[bl]) / max(ncfg[:, 0].sum() - ncfg[bl, 0], 1),
                l3_best_share_cfg=(l3c[bl] / l3c.sum()) if l3c.sum() > 0 else np.nan,
                l3_R_day_ref=l3r.mean(), l3_R_day_cfg=l3c.mean())


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    res = {"cands": int(len(C)), "by_setup": {E.SETUPS[s]: int((SI == s).sum()) for s in range(4)},
           "days": {p: int((PER == p).sum()) for p in ("FIT", "CHECK", "T2")}}
    par = {}
    for cx, lo in CTX.items():
        Rn, Nn, Tn = E.run(A, ST, PATH, ALL, ONES, lo)
        Rl, Nl, Tl = L.run(A, ST, PATH, ALL, ONES, lo, 0, 0)
        par[cx] = dict(max_abs_day=float(np.abs(Rn - Rl).max()), lots_equal=bool((Nn == Nl).all() and (Tn == Tl).all()))
    res["parity_mode0_vs_e4nb"] = par
    print("parity", par, flush=True)
    assert all(v["max_abs_day"] < 1e-9 and v["lots_equal"] for v in par.values()), "e4l3 mode-0 parity failed"
    rows, daily = [], {}
    for cx, lo in CTX.items():
        Rref, Nref, TKref = L.run(A, ST, PATH, ALL, ONES, lo)
        Rout, Nout, _ = L.run(A, ST, PATH, ALL, ~IS_L3, lo)
        daily[(cx, "keep")] = (Rref, Nref); daily[(cx, "L3-OUT")] = (Rout, Nout)
        thr = np.percentile(RR[TKref & IS_L3 & np.isin(DPC, ["CHECK", "T2"])], 90)
        top = TKref & IS_L3 & (RR >= thr) & np.isin(DPC, ["CHECK", "T2"])
        for cfg, (mode, pr) in CFG.items():
            Rc, Nc, TKc = L.run(A, ST, PATH, ALL, ONES, lo, mode, pr)
            daily[(cx, cfg)] = (Rc, Nc)
            nrm = {p: int((TKref & IS_L3 & (DPC == p) & ~TKc).sum()) for p in ("FIT", "CHECK", "T2")}
            # constant cut: L3 lots scaled by the config's L3 lot ratio vs keep (per period); other setups unscaled
            Rk = Rref.copy()
            for p in ("FIT", "CHECK", "T2"):
                ix = PER == p
                ratio = Nc[ix, 0].sum() / max(Nref[ix, 0].sum(), 1)
                Rk[ix, 0] = Rref[ix, 0] * ratio
            g = np.random.default_rng(SEED)
            pools = {p: np.flatnonzero(TKref & IS_L3 & (DPC == p)) for p in ("CHECK", "T2")}
            rnd = np.zeros((NR, len(CT))); rl3 = np.zeros((NR, len(CT)))
            for j in range(NR):
                kr = ONES.copy()
                for p, ixp in pools.items():
                    kr[g.choice(ixp, min(nrm[p], len(ixp)), replace=False)] = False
                Rr, Nr, _ = L.run(A, ST, PATH, CT, kr, lo)
                rnd[j] = Rr.sum(1); rl3[j] = Nr[:, 0]
            np.save(OUT / f"rnd_{cx}_{cfg}.npy", rnd.astype(np.float32))
            for p in ("FIT", "CHECK", "T2"):
                ix = np.flatnonzero(PER == p)
                m = met(Rref[ix], Rc[ix], Nref[ix], Nc[ix])
                row = dict(ctx=cx, cfg=cfg, per=p, l3_lost=nrm[p], **m,
                           cut_dR=float((Rk[ix].sum(1) - Rref[ix].sum(1)).mean()),
                           l3out_dR=float((Rout[ix].sum(1) - Rref[ix].sum(1)).mean()))
                row["capture_of_l3out"] = row["dR"] / row["l3out_dR"] if row["l3out_dR"] != 0 else np.nan
                if p != "FIT":
                    sel = np.isin(CT, ix)
                    rd = rnd[:, sel].mean(1) - Rref[ix].sum(1).mean()
                    row.update(rnd_p95=float(np.percentile(rd, 95)), rnd_mean=float(rd.mean()),
                               pctile=float((rd < m["dR"]).mean() * 100), sel_value=m["dR"] - float(rd.mean()),
                               rnd_l3_lots=float(rl3[:, sel].sum(1).mean()))
                    tb = 3.0 if p == "CHECK" else 2.0
                    ok = [m["dR"] > 0, m["t"] >= tb and m["dR"] > row["rnd_p95"],
                          m["dR"] > 0 and m["best_share"] < 0.25,
                          min(m["setup_dR_month"][s] for s in (1, 2, 3)) >= -2.0,
                          m["w5_cfg"] >= 1.05 * m["w5_ref"]]
                    row.update({f"bar{i + 1}": bool(v) for i, v in enumerate(ok)}, all_bar=bool(all(ok)))
                rows.append(row)
                print({k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for k, v in row.items()
                       if k != "setup_dR_month"}, flush=True)
            res.setdefault("rule30", {})[f"{cx}|{cfg}"] = dict(
                l3_keep_share=float(Nc[CT, 0].sum() / max(Nref[CT, 0].sum(), 1)),
                top_decile_kept=float((top & TKc).sum() / max(top.sum(), 1)))
            print(cx, cfg, "done", round(time.time() - t0), "s", flush=True)
    df = pd.DataFrame(rows)
    df["setup_dR_month"] = df.setup_dR_month.apply(lambda v: json.dumps([round(x, 3) for x in v]))
    df.to_csv(OUT / "results.csv", index=False)
    for (cx, cfg), (R, Nn) in daily.items():
        pd.DataFrame(R, columns=E.SETUPS).assign(date=DAYS, per=PER, l3_lots=Nn[:, 0], lots=Nn.sum(1)).to_parquet(
            OUT / f"day_{cx}_{cfg}.parquet")
    verdict = {}
    for cfg in CFG:
        sub = df[(df.cfg == cfg) & (df.per != "FIT")]
        if sub.all_bar.all():
            verdict[cfg] = "PASS-bench"
        elif all(sub[f"bar{i}"].all() for i in (1, 3, 4, 5)) and all(
                sub[(sub.ctx == cx)].bar2.any() for cx in CTX):
            verdict[cfg] = "LEAD-bench"
        else:
            verdict[cfg] = "FAIL"
    res["verdict_bench"] = verdict
    json.dump(res, open(OUT / "summary.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
