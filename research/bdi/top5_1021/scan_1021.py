"""top5_1021 step 3-4: execution variants of the 4 scored setups (PLAN.md, written before this was run).
Reuses top5_1019/scan_1019.py and top5_1020/scan_1020.py unchanged (sim, build_paths, next_after, spy_fo, base_ok,
filt_mask); adds the coil kernel (top5_1015._b4a == cwt_live_lib.b4a). Locked block never loaded.
Educational only - not financial advice.

    python research/bdi/top5_1021/scan_1021.py parity
    python research/bdi/top5_1021/scan_1021.py          # -> $SCR/trades.parquet (scratch)
"""
from __future__ import annotations

import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1019")]
import scan_1019 as S19  # noqa: E402
from scan_1019 import CL, S5, S6, T4, lib, gates, sim, build_paths, next_after, spy_fo, base_ok, filt_mask  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/t5tune1021")
SEED = 20261021
K_CTRL = 5
INF = np.inf

C4, C6 = "CWT12-coil-k4-long", "CWT12-coil-k6-long"
PDH10V, PDL10V = "CWT14-failbrk-pdh-p10-lowvol-short", "CWT14-failbrk-pdl-p10-lowvol-long"
CWT14 = {PDH10V: dict(level="PD", p=0.10, vr=1.0, side=-1), PDL10V: dict(level="PD", p=0.10, vr=1.0, side=1)}
COIL = {C4: 4, C6: 6}
BASE = {C4: dict(side=1, up=0.5, dn=1.0, win=(950, 1130), adv=95e6, so=0.35, geom="t05s1"),
        PDH10V: dict(side=-1, up=0.5, dn=1.0, win=(950, 1500), adv=95e6, so=0.0, geom="t05s1"),
        PDL10V: dict(side=1, up=0.5, dn=1.0, win=(950, 1500), adv=95e6, so=0.0, geom="t05s1"),
        C6: dict(side=1, up=1.0, dn=0.5, win=(950, 1130), adv=95e6, so=0.0, geom="t1s05")}
S19.BASE = BASE
SETUPS = tuple(BASE)
EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, sof=0.5, xt=1555, kind="std", sig="P", win=None, filt=None)
SO_ALT = {C4: (0.0, 0.25, 0.45), PDH10V: (0.25, 0.35, 0.15), PDL10V: (0.25, 0.35, 0.15), C6: (0.5, 0.25, 0.75)}


def grid():
    G = []
    for s in SETUPS:
        b = BASE[s]
        r0, e6, e7 = SO_ALT[s]
        dn = b["dn"]
        G += [(s, "P", "parent_live", {}),
              (s, "R0", f"scale{r0:.2f}", dict(so=r0)),
              (s, "E01", "timestop30", dict(tsb=6, tsr=0.2)), (s, "E02", "timestop60", dict(tsb=12, tsr=0.25)),
              (s, "E03", "stop_x085", dict(dn=round(dn * 0.85, 4))), (s, "E04", "stop_x125", dict(dn=dn * 1.25)),
              (s, "E05", "stop_x150", dict(dn=dn * 1.5)),
              (s, "E06", f"scale{e6:.2f}", dict(so=e6)), (s, "E07", f"scale{e7:.2f}", dict(so=e7)),
              (s, "E08", "wait1", dict(em=2)),
              (s, "E09", "from1000", dict(win=(1000, b["win"][1]))),
              (s, "E10", "from1030", dict(win=(1030, b["win"][1]))),
              (s, "E11", "until1100", dict(win=(b["win"][0], min(1100, b["win"][1])))),
              (s, "E12", "spy_against_after1030", dict(filt="spy1030")),
              (s, "E13", "reentry_cd30", dict(kind="reentry")),
              (s, "T1", "thr-20", dict(sig="PL")), (s, "T2", "thr+20", dict(sig="PH"))]
        if s == C6:
            G += [(s, "E14", "be_after_0.25u", dict(be=0.25)), (s, "E15", "be_after_0.5u", dict(be=0.5))]
    return G


GRID = grid()


def masks(fh):
    x = CL.arrays(fh)
    lev = S6.levels(x)
    out = {}
    with np.errstate(invalid="ignore"):
        for s, d in CWT14.items():
            L = lev[(d["level"], d["side"])]
            out[s] = {k: S6.b3_any(x, L, d, d["p"] * m) for k, m in (("P", 1.0), ("PL", 0.8), ("PH", 1.2))}
        for s, k in COIL.items():
            out[s] = {kk: np.asarray(S5._b4a(x.new, x.c, x.h, x.l, x.hod, x.atr, k, 0.5 * m, 0.25), bool)
                      for kk, m in (("P", 1.0), ("PL", 0.8), ("PH", 1.2))}
    return out


def month_job(month, parity=False):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, fh2P = build_paths(month)
    spy = spy_fo(f, fh)
    M = masks(fh)
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float),
                    P["tod"].to_numpy(np.int32))
    atrP = P["atr"].to_numpy(float)
    sym, dat = P["symbol"].to_numpy(), P["date"].to_numpy()
    pool = S5.ctrl_pool(P, 95e6)
    S5.K_CTRL = K_CTRL
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    spyP = np.full(len(P), np.nan)
    spyP[fh2P] = spy
    P2fh = P["_fhi"].to_numpy()
    rows = []

    def run(ent_fh, s, prm):
        ent = fh2P[ent_fh]
        Rv = 0.25 * atrP[np.maximum(ent, 0)]
        res = sim(h, l, c, tod, dend, ent.astype(np.int64), Rv, np.full(len(ent), np.nan), BASE[s]["side"], prm["up"],
                  prm["dn"], prm["em"], prm["tsb"], prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["xt"])
        return ent, Rv, res

    for s, vid, knob, ov in GRID:
        b = BASE[s]
        prm = {**EX0, "up": b["up"], "dn": b["dn"], "so": b["so"], **ov}
        sig = np.asarray(M[s][prm["sig"]], bool) & base_ok(fh, s, prm["win"]) & filt_mask(fh, spy, s, prm["filt"])
        e1 = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fh["date"].to_numpy(), sig)
        ent, Rv, res = run(e1, s, prm)
        second = np.zeros(len(ent), bool)
        if prm["kind"] == "reentry":
            allrows = np.sort(fh2P[np.flatnonzero(sig)])
            nx = next_after(allrows, res[5], dend, 6)
            e2 = P2fh[nx[nx >= 0]]
            ent2, Rv2, res2 = run(e2, s, prm)
            ent, Rv = np.r_[ent, ent2], np.r_[Rv, Rv2]
            res = tuple(np.r_[a, b2] for a, b2 in zip(res, res2))
            second = np.r_[second, np.ones(len(e2), bool)]
        r, mfe, mae, cd, et, xr = res
        scale = prm["dn"] / b["dn"]             # same $ risk vs the parent stop
        katr = Rv / np.where(atrP[np.maximum(ent, 0)] > 0, atrP[np.maximum(ent, 0)], np.nan)
        cr = S5.ctrl_rows(pool, ent, rng)
        cr_r = np.full(cr.shape, np.nan)
        for k in range(K_CTRL):
            rk = cr[:, k]
            Rc = np.where(rk >= 0, katr * atrP[np.maximum(rk, 0)], np.nan)
            cr_r[:, k] = sim(h, l, c, tod, dend, rk.astype(np.int64), Rc, np.full(len(rk), np.nan), b["side"],
                             prm["up"], prm["dn"], prm["em"], prm["tsb"], prm["tsr"], prm["be"], prm["so"], prm["sof"],
                             prm["xt"])[0]
        cnt = np.isfinite(cr_r).sum(1)
        ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan)
        t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": tod[ent], "tod": et, "r": r / scale,
                          "r_unscaled": r, "mfe": mfe / scale, "mae": mae / scale, "code": cd, "ctrl": ctrl / scale,
                          "filled": np.isfinite(r), "second": second, "spy_fo": spyP[ent]})
        t["setup"], t["var"], t["knob"] = s, vid, knob
        rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    if parity:
        return out, fh
    out = out.astype({"setup": "category", "var": "category", "knob": "category", "symbol": "category",
                      "r": "float32", "r_unscaled": "float32", "spy_fo": "float32", "mfe": "float32", "mae": "float32",
                      "ctrl": "float32"})
    print(month, len(out), round(time.time() - t0), flush=True)
    return out


def check_parity(month="2025-06"):
    out, fh = month_job(month, parity=True)
    sub = fh.iloc[:300_000].reset_index(drop=True)
    xs = CL.arrays(sub)
    for s, d in CWT14.items():
        sd = "short" if d["side"] == -1 else "long"
        a = CL.b3(sub, level=d["level"], p=d["p"], lowvol=d["vr"] == 1.0, side=sd)
        b = S6.b3_any(xs, S6.levels(xs)[(d["level"], d["side"])], d, d["p"])
        assert (np.asarray(a, bool) == b).all(), (s, int((np.asarray(a, bool) != b).sum()))
    for s, k in COIL.items():
        a = np.asarray(CL.b4a(sub, nco=k), bool)
        b = np.asarray(S5._b4a(xs.new, xs.c, xs.h, xs.l, xs.hod, xs.atr, k, 0.5, 0.25), bool)
        assert (a == b).all(), (s, int((a != b).sum()))
    print("kernel parity ok (2 CWT14 + 2 coil)")
    for s in SETUPS:
        b = BASE[s]
        v = "R0" if b["so"] > 0 else "P"
        p = out[(out.setup == s) & (out["var"] == v)]
        sd = "short" if b["side"] == -1 else "long"
        if s in CWT14:
            d = CWT14[s]
            m = CL.b3(fh, level=d["level"], p=d["p"], lowvol=d["vr"] == 1.0, side=sd)
        else:
            m = CL.b4a(fh, nco=COIL[s])
        lt = T4.trades(fh, m, {"win": b["win"], "adv": b["adv"], "side": sd, "geom": b["geom"]})
        j = lt.merge(p[["date", "symbol", "tod", "r_unscaled"]], on=["date", "symbol", "tod"], how="outer")
        dd = (j.r - j.r_unscaled).abs()
        print(s, "lab n", len(lt), "sim n", len(p), "matched", int(dd.notna().sum()), "mean|d|", round(dd.mean(), 5),
              "share<0.01", round((dd < 0.01).mean(), 4), "exp lab", round(lt.r.mean(), 4), "sim", round(p.r_unscaled.mean(), 4))


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, months), ignore_index=True)
    T.to_parquet(SCR / "trades.parquet", index=False)
    print(T.groupby(["setup", "var"], observed=True).agg(n=("r", "size"), filled=("filled", "mean"), exp=("r", "mean")).to_string())


if __name__ == "__main__":
    if sys.argv[1:] == ["parity"]:
        check_parity()
    else:
        main()
