"""pdl1030/structure-exit step 2: score the PLAN.md rows (TRAIN / VALID only) on the cached p05 / p10 paths.
sim2 = top5_1028 sim generalised to per-trade stop / target / scale prices and structural exits; same costs.
Educational only - not financial advice.
"""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd, numba
sys.path[:0] = ["/home/user/MCF"]
from mcf.research import gates  # noqa
HERE = Path(__file__).resolve().parent
C = HERE / "cache"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
N_PRIOR, N_ME = 121459, 18
BAR = 0.9 * max(1.5, math.sqrt(2 * math.log(N_PRIOR + 3 * N_ME)))
BAR = max(BAR, 1.35)


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
def sim2(off, H, L, Cc, TOD, E, tier, stop0, tgt, Ru, spx, be, trl_trig, trl_lvl, cstop, tsb, sof):
    """Long only. Stop first. Codes 1 target, 2 stop, 3 moved stop, 4 time stop, 6 flatten 15:55, 7 close-based exit.
    r in units of Ru (the per-trade $ risk per share)."""
    n = len(E)
    r = np.full(n, np.nan)
    code = np.zeros(n, np.int8)
    mfe_o = np.full(n, np.nan)
    for q in range(n):
        a, b = off[q], off[q + 1]
        R = Ru[q]
        if not (R > 0):
            continue
        e = E[q]
        ec = (0.01 + e * 1e-4) * _mult(TOD[a])
        stop = stop0[q]
        scaled = False
        mfe = 0.0
        x, cd = 0.0, 0
        for k in range(a + 1, b):
            if L[k] <= stop:
                x = stop
                cd = 2 if stop < e - 0.999 * (e - stop0[q]) else 3
                break
            mfe = max(mfe, (H[k] - e) / R)
            if H[k] >= tgt[q]:
                x, cd = tgt[q], 1
                break
            if Cc[k] < cstop[q]:
                x, cd = Cc[k], 7
                break
            if tsb[q] > 0 and (k - a) >= tsb[q]:
                x, cd = Cc[k], 4
                break
            if be[q] > 0 and mfe >= be[q]:
                stop = max(stop, e)
            if trl_trig[q] > 0 and mfe >= trl_trig[q]:
                stop = max(stop, trl_lvl[q])
            if (not scaled) and spx[q] > 0 and H[k] >= spx[q]:
                scaled = True
                stop = max(stop, e)
        if cd == 0:
            x, cd = Cc[b - 1], 6
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if (cd == 2 or cd == 3) else 0.0))
        g = (x - e) / R
        if scaled:
            g = sof * (spx[q] - e) / R + (1 - sof) * g
            xc = (1 - sof) * xc
        r[q] = g - tier[q] * (ec + xc) / R
        code[q] = cd
        mfe_o[q] = mfe
    return r, code, mfe_o


def load(setup):
    T, offs, Hs, Ls, Cs, TODs = [], [], [], [], [], []
    base = 0
    for m in MONTHS:
        t = pd.read_parquet(C / f"tr_{m}.parquet")
        z = np.load(C / f"paths_{m}.npz")
        off = z["off"]
        sel = np.flatnonzero((t["setup"] == setup).to_numpy())
        ln = np.diff(off)
        rowsel = np.repeat(np.isin(np.arange(len(ln)), sel), ln)
        Hs.append(z["h"][rowsel]); Ls.append(z["l"][rowsel]); Cs.append(z["c"][rowsel]); TODs.append(z["tod"][rowsel])
        offs.extend(ln[sel].tolist())
        T.append(t.iloc[sel])
    T = pd.concat(T, ignore_index=True)
    d = T["date"].astype(str)
    assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not ((d >= "2026-04-01") & (d <= "2026-06-30")).any()
    assert (d <= "2026-09-15").all()
    T["split"] = np.where(d <= "2025-12-31", "train", "valid")
    T["month"] = d.str[:7]
    off = np.r_[0, np.cumsum(offs)].astype(np.int64)
    P = dict(off=off, H=np.concatenate(Hs).astype(np.float64), L=np.concatenate(Ls).astype(np.float64),
             C=np.concatenate(Cs).astype(np.float64), TOD=np.concatenate(TODs).astype(np.int64))
    return T, P


def arrays(T, cfg):
    """cfg keys: stop (A1..A5 / parent), tgt (parent / vwap / open / pc / mm1 / mm2 / r1), so (bool parent scale),
    be (R), trail (bool C2), tsb (bars), c4 (scale at parent target, runner to tgt)."""
    n = len(T)
    e, A, lod, pdl = (T[k].to_numpy(float) for k in ("e", "A", "lod", "pdl"))
    R0 = 0.25 * A
    st = cfg.get("stop", "parent")
    cstop = np.full(n, -np.inf)
    if st == "parent":
        stop = e - R0
    elif st == "A1":
        stop = lod - 0.02 * A
    elif st == "A2":
        stop = lod - 0.10 * A
    elif st == "A3":
        stop = lod - 0.25 * A
    elif st == "A4":
        stop = np.minimum(lod - 0.05 * A, e - R0)
    elif st == "A5":
        stop = lod - 0.25 * A
        cstop = lod.copy()
    Ru = e - stop
    ptgt = e + 0.125 * A            # parent target price (0.5 R0)
    tg = cfg.get("tgt", "parent")
    if tg == "parent":
        tgt = ptgt
    else:
        lvl = {"vwap": T["vwap"].to_numpy(float), "open": T["open"].to_numpy(float), "pc": T["pc"].to_numpy(float),
               "mm1": pdl + 1.0 * (pdl - lod), "mm2": pdl + 2.0 * (pdl - lod), "r1": e + Ru}[tg]
        lvl = np.where(np.isfinite(lvl), lvl, ptgt)
        tgt = np.maximum(lvl, ptgt)
    spx = np.full(n, -1.0)
    if cfg.get("so"):
        spx = e + 0.0625 * A        # parent scale-out price (0.25 R0)
    if cfg.get("c4"):
        spx = ptgt.copy()           # half at the parent target, runner to tgt
    be = np.full(n, float(cfg.get("be", 0.0)))
    trig = np.full(n, 0.25 if cfg.get("trail") else 0.0)
    tlvl = pdl - 0.02 * A
    tsb = np.full(n, int(cfg.get("tsb", 0)), np.int64)
    return stop, tgt, Ru, spx, be, trig, tlvl, cstop, tsb


def run(T, P, cfg):
    stop, tgt, Ru, spx, be, trig, tlvl, cstop, tsb = arrays(T, cfg)
    r, code, mfe = sim2(P["off"], P["H"], P["L"], P["C"], P["TOD"], T["e"].to_numpy(float), T["tier"].to_numpy(float),
                        stop, tgt, Ru, spx, be, trig, tlvl, cstop, tsb, 0.5)
    out = T[["date", "symbol", "split", "month", "spy_day"]].copy()
    out["r"], out["code"], out["Ru_A"] = r, code, Ru / T["A"].to_numpy(float)
    return out[np.isfinite(r)]


def stats(o, nsess):
    res = {}
    for sp in ("train", "valid"):
        s = gates.summary(o[o.split == sp][["date", "r"]])
        res[f"n_{sp}"], res[f"avg_{sp}"], res[f"t_{sp}"] = s["n"], s["exp_r"], s["t"]
    s = gates.summary(o[["date", "r"]])
    g = o.groupby("date")["r"].sum()
    res.update(n_tv=s["n"], avg_tv=s["exp_r"], t_tv=s["t"], ex_best=s["ex_best_day"],
               best_share=round(float(g.max() / g.sum()), 3) if g.sum() > 0 else None,
               per_session=round(s["n"] / nsess, 1))
    up = o[o.spy_day > 0]; dn = o[o.spy_day < 0]
    res["up_day_r"], res["down_day_r"] = round(float(up.r.mean()), 4), round(float(dn.r.mean()), 4)
    mm = o.groupby("month")["r"].mean()
    res["wf_pct"] = round(float((mm > 0).mean() * 100), 1)
    res["stop_pct"] = round(float(o.code.isin([2]).mean() * 100), 1)
    res["tgt_pct"] = round(float((o.code == 1).mean() * 100), 1)
    res["Ru_A_med"] = round(float(o.Ru_A.median()), 3)
    return res


PAR_P05 = dict(train=-0.0677, valid=-0.0675)


def verdict(st):
    return bool(st["t_tv"] is not None and st["t_tv"] >= BAR and st["wf_pct"] >= 54 and st["avg_train"] > 0
                and st["avg_valid"] > 0 and st["avg_train"] > PAR_P05["train"] and st["avg_valid"] > PAR_P05["valid"]
                and (st["per_session"] >= 76.6 or st["per_session"] >= 25))


def main():
    rows, count = [], 0
    data = {s: load(s) for s in ("p05", "p10")}
    nsess = data["p05"][0]["date"].nunique()

    def score(id_, setup, cfg, rule):
        nonlocal count
        count += 1
        T, P = data[setup]
        o = run(T, P, cfg)
        st = stats(o, nsess)
        st.update(id=id_, setup=setup, rule=rule, cfg=json.dumps(cfg), passes=verdict(st))
        rows.append(st)
        print(id_, setup, rule, {k: st[k] for k in ("avg_train", "avg_valid", "t_tv", "wf_pct", "per_session", "up_day_r",
                                                   "down_day_r", "stop_pct", "tgt_pct", "Ru_A_med")}, flush=True)
        return st

    p05 = score("P05", "p05", dict(stop="parent", tgt="parent", so=True), "parent p05")
    p10 = score("P10", "p10", dict(stop="parent", tgt="parent"), "parent p10")
    par_ok = abs(p05["avg_train"] - (-0.0677)) <= 0.005 and abs(p05["avg_valid"] - (-0.0675)) <= 0.005 \
        and abs(p10["avg_tv"] - (-0.0880)) <= 0.005
    print("PARITY", par_ok, flush=True)
    if not par_ok:
        pd.DataFrame(rows).to_csv(HERE / "results.csv", index=False)
        return
    A = {}
    for a, rule in [("A1", "stop LOD-0.02A"), ("A2", "stop LOD-0.10A"), ("A3", "stop LOD-0.25A"),
                    ("A4", "stop min(LOD-0.05A, e-0.25A)"), ("A5", "stop LOD-0.25A + exit on a close below LOD")]:
        A[a] = score(a, "p05", dict(stop=a, tgt="parent", so=True), rule + "; parent target/scale prices")
    sstar = max(A, key=lambda k: A[k]["avg_train"])
    print("STOP*", sstar, flush=True)
    B = {"A*": (A[sstar], dict(stop=sstar, tgt="parent", so=True))}
    for b, tg, rule in [("B1", "vwap", "target VWAP"), ("B2", "open", "target today's open"), ("B3", "pc", "target prior close"),
                        ("B4", "mm1", "target PDL + 1x depth"), ("B5", "mm2", "target PDL + 2x depth"),
                        ("B6", "r1", "target 1:1 structural R")]:
        cfg = dict(stop=sstar, tgt=tg)
        B[b] = (score(b, "p05", cfg, f"stop {sstar}; {rule} (floor e+0.125A), no scale"), cfg)
    tstar = max(B, key=lambda k: B[k][0]["avg_train"])
    print("TGT*", tstar, flush=True)
    base = dict(B[tstar][1])
    Cr = {tstar: (B[tstar][0], base)}
    for c_, ov, rule in [("C1", dict(be=0.5), "break-even after +0.5R"), ("C2", dict(trail=True), "stop to PDL-0.02A after +0.25R"),
                         ("C3", dict(tsb=12), "hard 60-min time stop"),
                         ("C4", dict(c4=True, so=False), "half at parent target, stop to e, runner to target")]:
        cfg = {**base, **ov}
        Cr[c_] = (score(c_, "p05", cfg, f"{tstar} base + {rule}"), cfg)
    allr = {**{k: (A[k], dict(stop=k, tgt="parent", so=True)) for k in A}, **{k: v for k, v in B.items() if k != "A*"},
            **{k: v for k, v in Cr.items() if k.startswith("C")}}
    best = max(allr, key=lambda k: allr[k][0]["avg_train"])
    cfg = dict(allr[best][1])
    score("D1", "p10", cfg, f"best TRAIN row {best} on the p10 entry")
    print("count", count, "bar", round(BAR, 3), flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(HERE / "results.csv", index=False)
    print(R[["id", "setup", "avg_train", "avg_valid", "t_tv", "wf_pct", "per_session", "up_day_r", "down_day_r", "ex_best",
             "best_share", "stop_pct", "tgt_pct", "Ru_A_med", "passes"]].to_string())


if __name__ == "__main__":
    main()
