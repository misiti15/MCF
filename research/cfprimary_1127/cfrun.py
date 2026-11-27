"""CF-PRIMARY Part B (PREREG.md): CF-15 / CF-LL15 on the E4 Primary book (BASE, LO, LO+L3-OUT) vs REF, 500 same-share
random removals per (setup, period) stratum, and a constant cut. Step 0 = parity of the numba engine with the Python
E4 engine (hedgeb_1126 sim_day copy) on REF. Usage (cwd repo): python cfrun.py W OUTDIR.
Educational only - not financial advice."""
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H)); sys.path.insert(0, "research/primshorts_1126")
import e4nb as E  # noqa: E402
import calib_live as CL  # noqa: E402

W, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NR, SEED = 500, 1127
C, DAYS, ST, PATH, A = E.load(W)
E.no_locked(DAYS)
PER = np.array([C.per.iloc[ST[i]] for i in range(len(DAYS))])
CELLS = json.load(open("research/primshorts_1126/cells_live.json"))
cf15 = ((2 * (0.01 + C.entry * 1e-4) + 0.02) / C.risk > 0.15).to_numpy()
cfll = (CL.predict_R(CELLS, C.entry.to_numpy(), C.risk.to_numpy(), np.full(len(C), "stop")) > 0.15)
CFG = {"CF-15": ~cf15, "CF-LL15": ~cfll}
CTX = {"BASE": (False, False), "LO": (True, False), "LO+L3-OUT": (True, True)}
ALL = np.arange(len(DAYS))
CT = np.flatnonzero(np.isin(PER, ["CHECK", "T2"]))
DAYPER_C = C.per.to_numpy()


def py_day(a, b, keep, lo):
    """hedgeb_1126/hsim.py sim_day (RAW, no hedge state), verbatim logic, for the parity check."""
    si, sym, side, ent, risk, lc = A["si"][a:b], A["sym"][a:b], A["side"][a:b], A["ent"][a:b], A["risk"][a:b], A["lc"][a:b]
    em, xm, off, n, rr = A["em"][a:b], A["xm"][a:b], A["off"][a:b], A["n"][a:b], A["rr"][a:b]
    keep = keep[a:b]; N = 4
    by_m = {}
    for k in np.flatnonzero(keep):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); latched = np.zeros(N, bool); olat = np.zeros(N, bool)
    open_ = []; cnt = np.zeros(N, int); symcnt = {}; halted = False; recent = [[] for _ in range(N)]
    if not by_m:
        return realized
    m0, last = min(by_m), max(by_m)

    def realize(m):
        nonlocal open_
        kp = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1
            else:
                kp.append(k)
        open_ = kp
    for m in range(m0, 956):
        if m > last and not open_:
            break
        realize(m)
        latched[realized <= -2.0 + 1e-12] = True
        for k in by_m.get(m, ()):
            s = si[k]
            if halted or latched[s] or olat[s]:
                continue
            if len(open_) >= 77 or cnt[s] >= 30 or symcnt.get((s, sym[k]), 0) >= 3:
                continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); open_.append(k); cnt[s] += 1
            symcnt[(s, sym[k])] = symcnt.get((s, sym[k]), 0) + 1
        realize(m)
        if open_:
            o = np.array(open_)
            j = np.minimum(m - em[o], n[o] - 1)
            c = PATH[off[o] + np.maximum(j, 0)]
            mk = side[o] * (c - ent[o]) / risk[o] - lc[o]
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
        else:
            ps = realized.copy()
        if lo:
            olat |= ps <= -2.0 + 1e-12
        if ps.sum() <= -20.0 + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += rr[k]
    return realized


def ctx_keep(l3out):
    return (A["si"] != 0) if l3out else np.ones(len(C), bool)


def met(ref, cfg, per_days):
    """ref/cfg: (D, 4) daily R by setup over per_days. Pass-bar metrics."""
    r, c = ref.sum(1), cfg.sum(1); d = c - r; n = len(d)
    t = d.mean() / (d.std(ddof=1) / np.sqrt(n)) if d.std(ddof=1) > 0 else 0.0
    w5 = lambda x: np.sort(x)[:5].mean()  # noqa: E731
    fl = lambda x: pd.Series(x).rolling(20).sum().min()  # noqa: E731
    tot = d.sum(); bi = np.argmax(d) if tot > 0 else np.argmin(d)
    return dict(n=n, ref=r.mean(), avg_cfg=c.mean(), dR=d.mean(), t=t, red_ref=(r < 0).mean() * 21, red_cfg=(c < 0).mean() * 21,
                w5_ref=w5(r), w5_cfg=w5(c), le10_ref=int((r <= -10).sum()), le10_cfg=int((c <= -10).sum()),
                floor_ref=fl(r), floor_cfg=fl(c), best_share=(d[bi] / tot) if tot else np.nan,
                dR_wo_best=np.delete(d, np.argmax(d)).mean(),
                setup_dR_month=list((cfg - ref).sum(0) / n * 21))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    res = {"cands": int(len(C)), "days": {p: int((PER == p).sum()) for p in ("FIT", "CHECK", "T2")},
           "flag_share": {k: {p: float((~v[DAYPER_C == p]).mean()) for p in ("FIT", "CHECK", "T2")} for k, v in CFG.items()},
           "flag_share_by_setup": {k: {E.SETUPS[s]: float((~v[A["si"] == s]).mean()) for s in range(4)} for k, v in CFG.items()},
           "overlap_cf15_cfll": float((cf15 & cfll).sum() / max((cf15 | cfll).sum(), 1))}
    # Step 0 parity
    par = {}
    rng = np.random.default_rng(0)
    sample = np.sort(rng.choice(len(DAYS), 80, replace=False))
    for cx, (lo, l3) in CTX.items():
        kp = ctx_keep(l3)
        Rn, _, _ = E.run(A, ST, PATH, sample, kp, lo)
        Rp = np.array([py_day(ST[d], ST[d + 1], kp, lo) for d in sample])
        par[cx] = float(np.abs(Rn.sum(1) - Rp.sum(1)).max())
    res["parity_max_abs_day_diff"] = par
    print("parity", par, round(time.time() - t0), "s", flush=True)
    assert max(par.values()) < 0.01, "numba engine parity failed"
    rows, daily = [], {}
    for cx, (lo, l3) in CTX.items():
        kp = ctx_keep(l3)
        Rref, Nref, TKref = E.run(A, ST, PATH, ALL, kp, lo)
        daily[(cx, "REF")] = Rref
        for cfg, mask in CFG.items():
            Rc, Nc, _ = E.run(A, ST, PATH, ALL, kp & mask, lo)
            daily[(cx, cfg)] = Rc
            # constant cut: s = CF-flagged share of REF lots taken, per period
            fday = np.ones(len(DAYS)); sh = {}
            for p in ("FIT", "CHECK", "T2"):
                inp = DAYPER_C == p
                s = (TKref & inp & ~mask).sum() / max((TKref & inp).sum(), 1)
                sh[p] = float(s); fday[PER == p] = 1 - s
            Rk, _, _ = E.run(A, ST, PATH, ALL, kp, lo, fday)
            daily[(cx, cfg + "|CUT")] = Rk
            # random removals (CHECK + T2 days): same count removed per (setup, period) stratum
            rnd = np.zeros((NR, len(CT)))
            g = np.random.default_rng(SEED)
            strata = [np.flatnonzero(kp & (A["si"] == s) & (DAYPER_C == p)) for s in range(4) for p in ("CHECK", "T2")]
            remove_n = [int((~mask[ix]).sum()) for ix in strata]
            t1 = time.time()
            for j in range(NR):
                kr = kp.copy()
                for ix, rn in zip(strata, remove_n):
                    if rn:
                        kr[g.choice(ix, rn, replace=False)] = False
                Rr, _, _ = E.run(A, ST, PATH, CT, kr, lo)
                rnd[j] = Rr.sum(1)
            np.save(OUT / f"rnd_{cx}_{cfg}.npy", rnd.astype(np.float32))
            print(cx, cfg, "random done", round(time.time() - t1), "s", flush=True)
            for p in ("FIT", "CHECK", "T2"):
                ix = np.flatnonzero(PER == p)
                m = met(Rref[ix], Rc[ix], ix)
                mk = met(Rref[ix], Rk[ix], ix)
                row = dict(ctx=cx, cfg=cfg, per=p, cut_s=sh[p], lots_ref=int(Nref[ix].sum()), lots_cfg=int(Nc[ix].sum()),
                           cut_dR=mk["dR"], cut_t=mk["t"], cut_red=mk["red_cfg"], cut_w5=mk["w5_cfg"], **m)
                if p != "FIT":
                    sel = np.isin(CT, ix)
                    rd = rnd[:, sel].mean(1) - Rref[ix].sum(1).mean()
                    row.update(rnd_p95=float(np.percentile(rd, 95)), rnd_mean=float(rd.mean()),
                               cf_pctile=float((rd < m["dR"]).mean() * 100))
                    ok = [m["dR"] > 0, m["dR"] > row["rnd_p95"] and m["t"] >= 2.8, m["red_ref"] - m["red_cfg"] >= 0.5,
                          m["w5_cfg"] >= 1.05 * m["w5_ref"], m["best_share"] < 0.25 and m["dR"] > 0,
                          min(m["setup_dR_month"][s] for s in range(4) if not (l3 and s == 0)) >= -2.0]
                    row.update({f"bar{i + 1}": bool(v) for i, v in enumerate(ok)}, all_bar=bool(all(ok)))
                rows.append(row)
                print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items() if k != "setup_dR_month"},
                      flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "results.csv", index=False)
    for (cx, cfg), R in daily.items():
        pd.DataFrame(R, columns=E.SETUPS).assign(date=DAYS, per=PER).to_parquet(OUT / f"day_{cx}_{cfg.replace('|', '_')}.parquet")
    verdict = {}
    for cfg in CFG:
        sub = df[(df.cfg == cfg) & (df.per != "FIT")]
        core = sub[sub.ctx.isin(["BASE", "LO"])].all_bar.all()
        l3 = (sub[sub.ctx == "LO+L3-OUT"].dR > 0).all()
        verdict[cfg] = "PASS" if core and l3 else ("INCONCLUSIVE" if core else "FAIL")
    res["verdict"] = verdict
    json.dump(res, open(OUT / "summary.json", "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
    print("total", round(time.time() - t0), "s")
