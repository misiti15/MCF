"""rdt1030 / F5 build: the two fixed base entries (F1-A both sides via F2/build.py:kernel+sim; F4-01 PDL long via
F4/build.py:run_signal+sim) with the F5 indicator columns read at the signal row, plus a K=5 random control per trade.
Entry/sim code is imported from the F2 and F4 folders (not copied, not edited). TRAIN+VALID only; the locked block and
HOLD months are never loaded. Per-month trade parquet goes to scratch. Educational only - not financial advice.

    python research/bdi/rdt1030/F5/build.py [months...]
"""
import os, sys, time, zlib, importlib.util
sys.dont_write_bytecode = True  # do not write .pyc into the F2/F4 folders
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
SCR_ROOT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F5"
os.environ["NUMBA_CACHE_DIR"] = SCR_ROOT + "/numba"  # keep numba cache out of the F2/F4 folders
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m  # numba cache pickles reference the module by name
    spec.loader.exec_module(m)
    return m


_argv = sys.argv[:]
sys.argv = [sys.argv[0]]  # F4/build.py inspects argv at import time
F2 = _load("rdt_f2_build", ROOT / "research/bdi/rdt1030/F2/build.py")   # F1-A kernel + patched sim; applies the _cut patches
F4 = _load("rdt_f4_build", ROOT / "research/bdi/rdt1030/F4/build.py")   # F4 signals + patched sim
sys.argv = _argv
SC, lib = F2.SC, F2.lib
SCR = Path(SCR_ROOT)
CUT = "2026-09-15"
MONTHS = F2.MONTHS
HOLD = ("2026-04", "2026-05", "2026-06", "2026-10")
SEED, K_CTRL = 20261030, 5
IND = ["vwapDistPct", "rsi", "rsi5", "buyPressure", "sma50_dist_pct", "heat", "fromOpen"]


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in HOLD
    f, fh, P, dend, fh2P = SC.build_paths(month)
    del f
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    key = (ds + "|" + fh["tod"].astype(str)).to_numpy()
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    hP, lP, cP, todP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy().astype(np.int32)
    adv = fh["adv20"].fillna(0).to_numpy(float); atr = fh["atr_d"].to_numpy(float)
    h, l, c = fh["high"].to_numpy(float), fh["low"].to_numpy(float), fh["close"].to_numpy(float)
    sd = fsym.astype(object) + "|" + fdat.astype(object)
    new = np.r_[True, sd[1:] != sd[:-1]]
    sst = np.flatnonzero(new); sen = np.r_[sst[1:] - 1, len(fh) - 1]
    bn = ((ftod // 100) * 60 + ftod % 100 - 570) // 5
    _, sigL, sigS, orh, orl, _, _ = F2.kernel(sst, sen, ftod, bn.astype(np.int32), h, l, c, fh["fromOpen"].to_numpy(float), atr, F2.G_FVG, F2.SW_2R)
    ctx = lib.load_context(month)
    ck = (ctx["date"].astype(str) + "|" + ctx["tod"].astype(str)).to_numpy()
    breadth = pd.Series(ctx["breadth"].to_numpy(float), index=ck)
    sp = (fsym == "SPY")
    spy_day = pd.Series(fh["fromOpen"].to_numpy(float)[sp & (ftod >= 950)], index=fdat[sp & (ftod >= 950)]).groupby(level=0).last()
    indv = {k: fh[k].to_numpy(float) for k in IND}
    with np.errstate(invalid="ignore"):
        uni = (adv >= 95e6) & (atr > 0) & (ftod >= 950)
    uidx = np.flatnonzero(uni)
    ug = pd.Series(uidx).groupby(key[uidx]).apply(lambda s: s.to_numpy()).to_dict()
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])

    def ctrl_for(i, Ratr, up, side, sim_fn):
        ce, cR, cu, cq = [], [], [], []
        for t in range(len(i)):
            pool = ug.get(key[i[t]])
            if pool is None:
                continue
            pool = pool[fsym[pool] != fsym[i[t]]]
            if len(pool) == 0:
                continue
            pk = rng.choice(pool, size=min(K_CTRL, len(pool)), replace=False)
            ce.append(pk); cR.append(Ratr[t] * atr[pk]); cu.append(np.full(len(pk), up[t])); cq.append(np.full(len(pk), t))
        out = np.full(len(i), np.nan)
        if ce:
            ce, cR, cu, cq = np.concatenate(ce), np.concatenate(cR), np.concatenate(cu), np.concatenate(cq)
            rc = sim_fn(fh2P[ce].astype(np.int64), cR, cu)
            out = pd.Series(rc).groupby(cq).mean().reindex(np.arange(len(i))).to_numpy(float)
        return out

    def frame(base, side, i, r, code, up, R, A, e, ctrl):
        cst = ((0.01 + e * 1e-4) * np.where(ftod[i] < 1030, 1.4, 1.0) + 0.01 + e * 1e-4) * tier_fh[i] / R
        fo = indv["fromOpen"][i]
        with np.errstate(invalid="ignore"):
            mfo = (c[i] - c[i] / (1 + fo / 100)) / A
        d = {"base": base, "date": fdat[i], "symbol": fsym[i], "tod": ftod[i], "side": "L" if side == 1 else "S", "r": r,
             "code": code, "up": up, "R_atr": R / A, "cost_rt_R": cst, "ctrl_r": ctrl, "spy_day": spy_day.reindex(fdat[i]).to_numpy(float),
             "mfo_atr": mfo, "breadth": breadth.reindex(key[i]).to_numpy(float)}
        for k in IND[:-1]:
            d[k] = indv[k][i]
        return pd.DataFrame(d)

    out = []
    # --- F1-A (F2 kernel + F2 patched sim, exactly as F2/build.py) ---
    for side, sig in ((1, sigL), (-1, sigS)):
        q = np.flatnonzero(sig >= 0); i = sig[q]
        A = atr[i]; e = c[i]
        stp = np.where(side == 1, l[i - 2], h[i - 2]); R = side * (e - stp)
        with np.errstate(invalid="ignore"):
            ok = (adv[i] >= 95e6) & (A > 0) & (R >= 0.03 * A) & (R <= 1.0 * A)
        i, A, e, R = i[ok], A[ok], e[ok], R[ok]
        up = np.where(R <= F2.SW_2R * A, 2.0, 1.0)
        r, code, _ = F2.sim(hP, lP, cP, todP, dend, tierP, fh2P[i].astype(np.int64), R, side, up, 0.0)
        ctrl = ctrl_for(i, R / A, up, side, lambda ent, RR, uu: F2.sim(hP, lP, cP, todP, dend, tierP, ent, RR, side, uu, 0.0)[0])
        out.append(frame("F1A", side, i, r, code, up, R, A, e, ctrl))
    # --- F4-01 (F4 run_signal PDL, DOL target, formation entry; F4 patched sim) ---
    X = F4.seg_arrays(fh, ds)
    i, px, R, up, sw, side = F4.run_signal(X, "PDL", 0, False)
    univ4 = (adv >= 95e6) & (X["atr"] > 0)
    keep = univ4[i]
    i, px, R, up = i[keep], px[keep], R[keep], up[keep]
    A4 = X["atr"][i]
    e = np.where(np.isnan(px), c[i], px)
    r, mfe, code, _ = F4.sim(hP, lP, cP, todP, dend, tierP, fh2P[i], px, R, side, up, 0.0, False, True)
    ctrl = ctrl_for(i, R / A4, up, side, lambda ent, RR, uu: F4.sim(hP, lP, cP, todP, dend, tierP, ent, np.full(len(ent), np.nan),
                                                                    RR, side, uu, 0.0, False, True)[0])
    out.append(frame("F401", side, i, r, code, up, R, A4, e, ctrl))
    T = pd.concat(out, ignore_index=True)
    T["date"] = T["date"].astype(str)
    print(month, T.groupby(["base", "side"]).size().to_dict(), "sessions", len(set(fdat)), round(time.time() - t0), "s", flush=True)
    return T


if __name__ == "__main__":
    SCR.mkdir(parents=True, exist_ok=True)
    for m in sys.argv[1:] or MONTHS:
        o = SCR / f"tr_{m}.parquet"
        if not o.exists():
            month_job(m).to_parquet(o, index=False)
