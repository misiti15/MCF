"""pdh1022: rework grid of CWT14-failbrk-pdh-p10-short on the open two-year history (PLAN.md, written before this ran).
Reuses top5_1019/scan_1019.py unchanged (build_paths with 09:35-09:45 head rows, sim, base_ok, next_after) and
top5_1015/scan_1015.py (same-minute random-control pool). New: `_b3s`, the short prior-day-high failed-break kernel with
the poke row and the excursion high as outputs (parity: flag == cwt_live_lib.b3 on 2025-06). The rule-19 locked block
2024-11-01..2025-02-28 is never loaded. Educational only - not financial advice.

    python research/bdi/pdh1022/pdh_scan.py parity
    python research/bdi/pdh1022/pdh_scan.py stage1          # -> $SCR/trades_stage1.parquet (scratch)
    python research/bdi/pdh1022/pdh_scan.py stage2          # pairs from stage2.json (written by report.py) -> trades_stage2.parquet
"""
from __future__ import annotations

import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1019")]
import scan_1019 as S19  # noqa: E402
from scan_1019 import CL, S5, T4, lib, gates, sim, build_paths, next_after  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdh1022")
SEED = 20261022
K_CTRL = 5
S = "CWT14-failbrk-pdh-p10-short"
BASE = dict(side=-1, up=0.5, dn=1.0, win=(950, 1200), adv=95e6)
EX0 = dict(p=0.10, k=3, conf=0.0, em=0, lh=False, vf=False, hv=False, xmax=None, xmin=None, ff=False, kind="std",
           win=None, filt=(), up=0.5, dn=1.0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555)

STAGE1 = [
    ("P", "parent", {}),
    ("D05", "depth0.05", dict(p=0.05)), ("D20", "depth0.20", dict(p=0.20)),
    ("C05", "close_below_pdh_0.05atr", dict(conf=0.05)), ("C10", "close_below_pdh_0.10atr", dict(conf=0.10)),
    ("K1", "fail_within_1bar", dict(k=1)),
    ("LH", "lower_high_next_bar", dict(lh=True, em=2)),
    ("VF", "volume_fade", dict(vf=True)), ("HV", "poke_vr_ge1", dict(hv=True)),
    ("W1", "wait1", dict(em=2)),
    ("XS", "ext_le_0.30atr", dict(xmax=0.30)), ("XD", "ext_gt_0.30atr", dict(xmin=0.30)),
    ("T075", "target0.75", dict(up=0.75)), ("T100", "target1.0", dict(up=1.0)),
    ("SO35", "scaleout0.35", dict(so=0.35)), ("BE35", "be_after0.35", dict(be=0.35)),
    ("T100BE50", "target1.0_be_after0.5", dict(up=1.0, be=0.5)),
    ("TS30", "timestop30", dict(tsb=6, tsr=0.2)), ("TS60", "timestop60", dict(tsb=12, tsr=0.25)),
    ("S125", "stop_x1.25_same$", dict(dn=1.25)), ("S150", "stop_x1.5_same$", dict(dn=1.5)),
    ("WF10", "from1000", dict(win=(1000, 1200))), ("WF1030", "from1030", dict(win=(1030, 1200))),
    ("WU11", "until1100", dict(win=(950, 1100))), ("WU1430", "until1430", dict(win=(950, 1430))),
    ("FF", "first_failure_of_day", dict(ff=True)), ("RE", "reentry_cd30", dict(kind="reentry")),
    ("FSV", "spy_below_vwap", dict(filt=("spy_vwap",))), ("FSO", "spy_below_open", dict(filt=("spy_open",))),
    ("FQO", "qqq_below_open", dict(filt=("qqq_open",))), ("FBF", "breadth_falling", dict(filt=("breadth_fall",))),
    ("FBL", "breadth_lt0.5", dict(filt=("breadth_low",))), ("FRS", "rs_weak", dict(filt=("rs_weak",))),
    ("G05", "skip_gapup_gt0.5", dict(filt=("gap05",))), ("G1", "skip_gapup_gt1", dict(filt=("gap1",))),
    ("G2", "skip_gapup_gt2", dict(filt=("gap2",))),
]
DEF1 = {v: ov for v, _, ov in STAGE1}
ENTRY_KNOBS = ["D05", "D20", "C05", "C10", "K1", "LH", "VF", "HV", "W1", "XS", "XD", "WF10", "WF1030", "WU11", "WU1430",
               "FF", "RE", "FSV", "FSO", "FQO", "FBF", "FBL", "FRS", "G05", "G1", "G2"]
FILTER_KNOBS = ["FSV", "FSO", "FQO", "FBF", "FBL", "FRS", "G05", "G1", "G2"]
EXIT_PAIR = ["S150", "SO35", "T075"]


def combine(a, b):
    out = {**DEF1[a]}
    for k, v in DEF1[b].items():
        out[k] = tuple(out.get(k, ())) + tuple(v) if k == "filt" else v
    return out


def stage2_grid():
    j = json.load(open(OUT / "stage2.json"))
    return [(f"{a}+{b}", f"{a}+{b}", combine(a, b)) for a, b in j["pairs"]]


@numba.njit(cache=True)
def _b3s(new, L, h, c, atr, p, kmax):
    """cwt_live_lib.b3(level='PD', side='short', lowvol=False) with the reclaim window kmax as a knob; also returns the
    poke row (first bar >= p ATR above L) and the excursion's max high, for every flagged row."""
    n = len(c)
    flag = np.zeros(n, np.bool_)
    poke = np.full(n, -1, np.int64)
    xh = np.full(n, np.nan)
    inexc = False
    stale = False
    st = 0
    mx = 0.0
    for i in range(n):
        if new[i]:
            inexc = False
            stale = False
        if np.isnan(L[i]):
            continue
        beyond = h[i] >= L[i] + p * atr[i]
        inside = c[i] < L[i]
        if (not inexc) and (not stale) and beyond:
            inexc = True
            st = i
            mx = h[i]
        if inexc:
            if h[i] > mx:
                mx = h[i]
            if inside:
                if i - st <= kmax:
                    flag[i] = True
                    poke[i] = st
                    xh[i] = mx
                inexc = False
            elif i - st > kmax:
                inexc = False
                stale = True
        elif stale and inside:
            stale = False
    return flag, poke, xh


def context(f, fh, month):
    """Per fh row: SPY vwapDistPct, spy_fo, qqq_fo, breadth, breadth 3 bars earlier (same date; fewer -> first row)."""
    cx = lib.load_context(month).sort_values(["date", "tod"]).reset_index(drop=True)
    g = cx.groupby("date")["breadth"]
    pos = cx.groupby("date").cumcount()
    lag = g.shift(3)
    first = g.transform("first")
    cx["breadth_lag3"] = np.where(pos >= 3, lag, np.where(pos >= 1, first, np.nan))
    sp = f[f["symbol"] == "SPY"][["date", "tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "spy_vwap"})
    k = fh[["date", "tod"]].merge(cx[["date", "tod", "spy_fo", "qqq_fo", "breadth", "breadth_lag3"]], on=["date", "tod"],
                                  how="left").merge(sp, on=["date", "tod"], how="left")
    return {c: k[c].to_numpy(float) for c in ("spy_vwap", "spy_fo", "qqq_fo", "breadth", "breadth_lag3")}


def filt_mask(fh, ctx, filt):
    m = np.ones(len(fh), bool)
    fo = fh["fromOpen"].to_numpy(float)
    gap = fh["gap"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        for f in filt:
            if f == "spy_vwap":
                m &= ctx["spy_vwap"] < 0
            elif f == "spy_open":
                m &= ctx["spy_fo"] < 0
            elif f == "qqq_open":
                m &= ctx["qqq_fo"] < 0
            elif f == "breadth_fall":
                m &= ctx["breadth"] < ctx["breadth_lag3"]
            elif f == "breadth_low":
                m &= ctx["breadth"] < 0.5
            elif f == "rs_weak":
                m &= fo < ctx["spy_fo"]
            elif f in ("gap05", "gap1", "gap2"):
                m &= ~(gap > {"gap05": 0.5, "gap1": 1.0, "gap2": 2.0}[f])
            else:
                raise ValueError(f)
    return m


def base_ok(fh, win):
    lo, hi = win or BASE["win"]
    tod = fh["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        return (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (fh["adv20"].fillna(0).to_numpy() >= BASE["adv"]) \
            & (fh["atr_d"].to_numpy(float) > 0)


def signal(fh, x, ctx, cache, prm):
    key = (prm["p"], prm["k"])
    if key not in cache:
        cache[key] = _b3s(x.new, x.pdh, x.h, x.c, x.atr, prm["p"], prm["k"])
    flag, poke, xh = cache[key]
    m = flag.copy()
    vr = x.vr
    with np.errstate(invalid="ignore"):
        if prm["conf"] > 0:
            m &= x.c <= x.pdh - prm["conf"] * x.atr
        ext = (xh - x.pdh) / x.atr
        if prm["xmax"] is not None:
            m &= ext <= prm["xmax"]
        if prm["xmin"] is not None:
            m &= ext > prm["xmin"]
        vpk = np.where(poke >= 0, vr[np.maximum(poke, 0)], np.nan)
        if prm["vf"]:
            m &= vr < vpk
        if prm["hv"]:
            m &= vpk >= 1.0
        if prm["lh"]:
            nx = np.r_[np.arange(1, x.n), x.n - 1]
            same = np.r_[~x.new[1:], False]
            m &= same & (x.h[nx] < x.h) & (x.c[nx] < x.pdh[nx])
    if prm["ff"]:
        first = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fh["date"].to_numpy(), flag)
        fm = np.zeros(len(m), bool)
        fm[first] = True
        m &= fm
    sig = m & base_ok(fh, prm["win"]) & filt_mask(fh, ctx, prm["filt"])
    feats = {"ext_atr": ext, "bars_to_fail": np.where(poke >= 0, np.arange(x.n) - poke, -1), "vr_poke": vpk,
             "vr_fail": vr}
    return sig, feats


def month_job(month, grid=None, parity=False):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    grid = grid or STAGE1
    f, fh, P, dend, fh2P = build_paths(month)
    x = CL.arrays(fh)
    ctx = context(f, fh, month)
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float),
                    P["tod"].to_numpy(np.int32))
    atrP = P["atr"].to_numpy(float)
    sym, dat = P["symbol"].to_numpy(), P["date"].to_numpy()
    pool = S5.ctrl_pool(P, BASE["adv"])
    S5.K_CTRL = K_CTRL
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    P2fh = P["_fhi"].to_numpy()
    fo = fh["fromOpen"].to_numpy(float)
    gap = fh["gap"].to_numpy(float)
    cache, rows = {}, []

    def run(ent_fh, prm):
        ent = fh2P[ent_fh]
        Rv = 0.25 * atrP[np.maximum(ent, 0)]
        res = sim(h, l, c, tod, dend, ent.astype(np.int64), Rv, np.full(len(ent), np.nan), BASE["side"], prm["up"],
                  prm["dn"], prm["em"], prm["tsb"], prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["xt"])
        return ent, Rv, res

    for vid, knob, ov in grid:
        prm = {**EX0, **ov}
        sig, feats = signal(fh, x, ctx, cache, prm)
        e1 = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fh["date"].to_numpy(), sig)
        ent, Rv, res = run(e1, prm)
        efh = e1
        second = np.zeros(len(ent), bool)
        if prm["kind"] == "reentry":
            allrows = np.sort(fh2P[np.flatnonzero(sig)])
            nx = next_after(allrows, res[5], dend, 6)
            e2 = P2fh[nx[nx >= 0]]
            ent2, Rv2, res2 = run(e2, prm)
            ent, Rv = np.r_[ent, ent2], np.r_[Rv, Rv2]
            res = tuple(np.r_[a, b2] for a, b2 in zip(res, res2))
            second = np.r_[second, np.ones(len(e2), bool)]
            efh = np.r_[e1, e2]
        r, mfe, mae, cd, et, xr = res
        scale = prm["dn"]                       # same $ risk vs the parent's 1R stop
        katr = Rv / np.where(atrP[np.maximum(ent, 0)] > 0, atrP[np.maximum(ent, 0)], np.nan)
        cr = S5.ctrl_rows(pool, ent, rng)
        cr_r = np.full(cr.shape, np.nan)
        for k in range(K_CTRL):
            rk = cr[:, k]
            Rc = np.where(rk >= 0, katr * atrP[np.maximum(rk, 0)], np.nan)
            cr_r[:, k] = sim(h, l, c, tod, dend, rk.astype(np.int64), Rc, np.full(len(rk), np.nan), BASE["side"],
                             prm["up"], prm["dn"], prm["em"], prm["tsb"], prm["tsr"], prm["be"], prm["so"], prm["sof"],
                             prm["xt"])[0]
        cnt = np.isfinite(cr_r).sum(1)
        ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan)
        t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": tod[ent], "tod": et, "r": r / scale,
                          "r_unscaled": r, "mfe": mfe / scale, "mae": mae / scale, "code": cd, "ctrl": ctrl / scale,
                          "filled": np.isfinite(r), "second": second,
                          "ext_atr": feats["ext_atr"][efh], "bars_to_fail": feats["bars_to_fail"][efh],
                          "vr_poke": feats["vr_poke"][efh], "vr_fail": feats["vr_fail"][efh], "gap": gap[efh],
                          "rs": fo[efh] - ctx["spy_fo"][efh], "spy_vwap": ctx["spy_vwap"][efh],
                          "spy_fo": ctx["spy_fo"][efh], "qqq_fo": ctx["qqq_fo"][efh], "breadth": ctx["breadth"][efh],
                          "breadth_d3": ctx["breadth"][efh] - ctx["breadth_lag3"][efh]})
        t["var"], t["knob"] = vid, knob
        rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    if parity:
        return out, fh, x
    out = out.astype({"var": "category", "knob": "category", "symbol": "category", "r": "float32",
                      "r_unscaled": "float32", "mfe": "float32", "mae": "float32", "ctrl": "float32"})
    print(month, len(out), round(time.time() - t0), flush=True)
    return out


def check_parity(month="2025-06"):
    out, fh, x = month_job(month, grid=[STAGE1[0]], parity=True)
    a = np.asarray(CL.b3(fh, level="PD", p=0.10, lowvol=False, side="short"), bool)
    b = _b3s(x.new, x.pdh, x.h, x.c, x.atr, 0.10, 3)[0]
    assert (a == b).all(), int((a != b).sum())
    for p in (0.05, 0.20):
        a2 = np.asarray(CL.b3(fh, level="PD", p=p, lowvol=False, side="short"), bool)
        assert (a2 == _b3s(x.new, x.pdh, x.h, x.c, x.atr, p, 3)[0]).all(), p
    print("kernel parity ok: _b3s == cwt_live_lib.b3 (p 0.05 / 0.10 / 0.20) on", month, "rows", len(fh), "flags", int(b.sum()))
    p = out[out["var"] == "P"]
    m = CL.b3(fh, level="PD", p=0.10, lowvol=False, side="short")
    lt = T4.trades(fh, m, {"win": BASE["win"], "adv": BASE["adv"], "side": "short", "geom": "t05s1"})
    j = lt.merge(p[["date", "symbol", "tod", "r_unscaled"]], on=["date", "symbol", "tod"], how="outer")
    dd = (j.r - j.r_unscaled).abs()
    res = {"month": month, "lab_n": len(lt), "sim_n": len(p), "matched": int(dd.notna().sum()),
           "mean_abs_d": round(float(dd.mean()), 6), "share_lt_0.01": round(float((dd < 0.01).mean()), 4),
           "exp_lab": round(float(lt.r.mean()), 4), "exp_sim": round(float(p.r_unscaled.mean()), 4)}
    print(res)
    json.dump(res, open(OUT / "parity_parent.json", "w"), indent=1)


def main(stage):
    SCR.mkdir(parents=True, exist_ok=True)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    grid = STAGE1 if stage == "stage1" else [STAGE1[0]] + stage2_grid()
    from functools import partial
    with Pool(int(os.environ.get("PDH_PROCS", 3))) as p:
        T = pd.concat(p.map(partial(month_job, grid=grid), months), ignore_index=True)
    T.to_parquet(SCR / f"trades_{stage}.parquet", index=False)
    print(T.groupby("var", observed=True).agg(n=("r", "size"), filled=("filled", "mean"), exp=("r", "mean")).to_string())


if __name__ == "__main__":
    if sys.argv[1:] == ["parity"]:
        check_parity()
    else:
        main(sys.argv[1])
