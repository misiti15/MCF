"""swarm15_1029 step 2: variant swarm on the 15 most-traded live setups (PLAN.md, written before this was run).
Entries per month on the open two-year frames (CWT14 / coil / LIQ / RW2 kernels from top5_1015-1019, heat_fade_short-FD
score, RW7-FD and L3-fromopen-FD live modules); exits = the top5_1028 simulator (stop first, costs in, x3 extended tier).
The locked block 2024-11-01..2025-02-28 is never loaded (lib.months() is open months only; asserts).
Educational only - not financial advice.

    SW15_PROCS=2 python research/bdi/swarm15_1029/scan_15.py     # -> $SCR/trades.parquet (scratch)
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
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1028"), str(ROOT / "research" / "bdi" / "top5_1019"),
                str(ROOT / "research" / "bdi" / "gates1021" / "scripts")]
from scan_1019 import lib, build_paths, spy_fo, next_after, S5, S6, CL, T4, liq_mask, rw2_mask  # noqa: E402
from scan_1028 import sim  # noqa: E402  (top5_1028 simulator: limit entry, clock exit, x3 tier)
from scan_1015 import _mult  # noqa: E402
from _regime_common import regime_score  # noqa: E402
from common import load_mod, chain  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/sw15_1029")
SEED = 20261029
K_CTRL = 3
INF = np.inf
LOCK = (pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28"))

# setup specs: kind, side, target (up), scale-out (so), window, min ADV; from the setup's current account config
CW = lambda level, p, vr, side, win=(950, 1500), so=0.0: dict(kind="cwt", level=level, p=p, vr=vr, side=side, up=0.5,  # noqa: E731
                                                            so=so, win=win, adv=95e6)
SPEC = {
    "CWT14-failbrk-orl-p05-long": CW("OR", 0.05, INF, 1),                       # Graveyard, live_scale_out false
    "CWT14-failbrk-pdl-p05-long": CW("PD", 0.05, INF, 1, so=0.25),              # Testing 1, live_scale_out true 0.25
    "CWT14-failbrk-orl-p05-lowvol-long": CW("OR", 0.05, 1.0, 1),                # Graveyard
    "heat_fade_short-FD": dict(kind="heat", side=-1, up=1.0, so=0.0, win=(950, 1500), adv=125e6),
    "CWT12-coil-k4-long": dict(kind="coil", side=1, up=0.5, so=0.0, win=(950, 1130), adv=95e6),  # Graveyard, no scale
    "CWT14-failbrk-pdl-p05-lowvol-long": CW("PD", 0.05, 1.0, 1),                # Testing 2, scale_out null
    "CWT14-failbrk-orl-p10-long": CW("OR", 0.10, INF, 1, win=(950, 1200)),      # Graveyard
    "CWT14-failbrk-pdl-p10-long": CW("PD", 0.10, INF, 1),                       # Testing 2, scale_out null
    "CWT14-failbrk-orl-p10-lowvol-long": CW("OR", 0.10, 1.0, 1),                # Graveyard
    "CWT14-failbrk-pdh-p05-lowvol-short": CW("PD", 0.05, 1.0, -1),              # Graveyard
    "CWT14-failbrk-pdh-p10-short": CW("PD", 0.10, INF, -1, win=(950, 1200)),    # Graveyard
    "RW7-gapdn-bounce-early-short-FD": dict(kind="mod", module="research/bdi/fullday/RW7-gapdn-bounce-early-short-FD.py",
                                            side=-1, up=1.0, so=0.0, win=(950, 1500), adv=95e6),
    "RW2-exhaustion-noon-adv150-short-FD": dict(kind="rw2", side=-1, up=1.0, so=0.0, win=(950, 1500), adv=150e6),
    "LIQ-orl-sweep-open15-s25-long": dict(kind="liq", side=1, up=2.5, so=0.0, win=(950, 1500), adv=95e6),
    "L3-gap-slope-fromopen-FD": dict(kind="mod", module="research/bdi/fullday/L3-gap-slope-fromopen-FD.py", side=-1,
                                     up=1.0, so=0.0, win=(950, 1500), adv=0.0, refire=True, gap_le=-2.6573517322540283),
}
SETUPS = tuple(SPEC)

# rows already scored on a setup in an earlier top5 / hf run (PLAN.md section 3; listed in NOTES)
PDL3 = ("CWT14-failbrk-pdl-p05-long", "CWT14-failbrk-pdl-p05-lowvol-long", "CWT14-failbrk-pdl-p10-long")
DROP = {("S1", s) for s in PDL3 + ("CWT12-coil-k4-long", "RW7-gapdn-bounce-early-short-FD")}
DROP |= {("S2", "RW7-gapdn-bounce-early-short-FD"), ("T1", "CWT12-coil-k4-long"),
         ("T1", "CWT14-failbrk-pdh-p05-lowvol-short"), ("T1", "RW7-gapdn-bounce-early-short-FD"),
         ("T2", "CWT14-failbrk-pdh-p05-lowvol-short"), ("T2", "RW7-gapdn-bounce-early-short-FD"),
         ("W1", "CWT12-coil-k4-long"), ("K1", "CWT12-coil-k4-long")}


def grid(s):
    b = SPEC[s]
    up = b["up"]
    late = b["win"][1] <= 1200
    l3 = b.get("refire", False)
    g = [("P", "parent", {}),
         ("S1", "stop_x2.0", dict(dn=2.0)), ("S2", "stop_x2.5", dict(dn=2.5)), ("S3", "stop_x3.0", dict(dn=3.0)),
         ("T1", f"target{2 * up:g}", dict(up=2 * up, so=0.0)),
         ("T2", f"half_at{up:g}_be_runner{2 * up:g}", dict(up=2 * up, so=up)),
         ("X1", "timestop45_lt0.05", dict(tsb=9, tsr=0.05)), ("X2", "timestop180_lt0.25", dict(tsb=36, tsr=0.25)),
         ("W1", "until1030" if late else "until1400", dict(win=(950, 1030) if late else (950, 1400))),
         ("W2", "from1100", dict(win=(1100, 1500))),
         ("C1", "qqq_vwap_with_side", dict(keep="qqq_with")), ("C2", "qqq_vwap_against_side", dict(keep="qqq_against")),
         ("C3", "breadth_agrees", dict(keep="breadth")), ("C4", "spy_gap_agrees", dict(keep="spygap")),
         ("C5", "skip_prior_spy_abs_gt1", dict(keep="prev_big")), ("C6", "skip_prior_spy_abs_lt0.3", dict(keep="prev_quiet")),
         ("R1", "refire_cd12" if l3 else "reentry_cd60_cap2", dict(cd=12) if l3 else dict(reentry=12)),
         ("R2", "cap2_per_symbol_day" if l3 else "first10_per_day", dict(symcap=2) if l3 else dict(daycap=10)),
         ("R3", "first5_per_day", dict(daycap=5)),
         ("K1", "cost_entry_le5pct", dict(cost=("entry", 0.05))), ("K2", "cost_rt_le10pct", dict(cost=("rt", 0.10)))]
    return [r for r in g if (r[0], s) not in DROP]


EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, sof=0.5, xt=1555, lim=0.0, dn=1.0, keep=None, win=None, cd=1, reentry=0,
           symcap=0, daycap=0, cost=None)


def context(f, fh):
    """Per fh row: QQQ vwapDistPct, breadth, SPY gap (day), prior-day SPY close-to-close %, SPY fromOpen."""
    key = fh[["date", "tod"]].copy()
    ctx = lib.load_context(fh_month(fh))
    q = f[f["symbol"] == "QQQ"][["date", "tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "qqq_vd"})
    sp = f[f["symbol"] == "SPY"].groupby("date", sort=False)["gap"].first().rename("spy_gap").reset_index()
    kd = key["date"].astype(str)
    ctx = ctx.assign(_k=ctx["date"].astype(str) + "|" + ctx["tod"].astype(str)).set_index("_k")
    q = q.assign(_k=q["date"].astype(str) + "|" + q["tod"].astype(str)).set_index("_k")
    kk = kd + "|" + key["tod"].astype(str)
    out = pd.DataFrame(index=fh.index)
    out["breadth"] = ctx["breadth"].reindex(kk).to_numpy(float)
    out["qqq_vd"] = q["qqq_vd"].reindex(kk).to_numpy(float)
    out["spy_gap"] = sp.assign(date=sp["date"].astype(str)).set_index("date")["spy_gap"].reindex(kd).to_numpy(float)
    out["spy_prev"] = SPY_PREV.reindex(kd).to_numpy(float)
    return out


def fh_month(fh):
    return str(pd.Timestamp(fh["date"].iloc[0]).strftime("%Y-%m"))


def _spy_prev():
    d = lib.daily()
    spy = d[d["symbol"] == "SPY"].sort_values("date")
    dd = pd.to_datetime(spy["date"])
    prev = spy["close"].pct_change() * 100
    prev[(dd.diff().dt.days > 5).to_numpy()] = np.nan   # first open day after the locked gap: unknown
    return pd.Series(prev.to_numpy(), index=pd.to_datetime(spy["date"]).dt.strftime("%Y-%m-%d").to_numpy())


SPY_PREV = None


def hits_for(f, fh, f2fh, x, lev):
    """{setup: (fh row indices of every qualifying bar before window/ADV, fixed stop price over fh or None)}"""
    out = {}
    with np.errstate(invalid="ignore"):
        for s, b in SPEC.items():
            stp = None
            if b["kind"] == "cwt":
                m = np.asarray(S6.b3_any(x, lev[(b["level"], b["side"])], b, b["p"]), bool)
            elif b["kind"] == "coil":
                m = np.asarray(S5._b4a(x.new, x.c, x.h, x.l, x.hod, x.atr, 4, 0.5, 0.25), bool)
            elif b["kind"] == "liq":
                m, stp = liq_mask(fh, 0.15)
                m = np.asarray(m, bool)
            elif b["kind"] == "rw2":
                m = np.asarray(rw2_mask(fh), bool)
            else:
                if b["kind"] == "heat":
                    mf = np.asarray(regime_score(f, "short", T4.W9, 950, 1500, gate="fo-", k_cost=8.0, use_heat=False) <= -11.3, bool)
                else:
                    mod = load_mod(s, b["module"])
                    mf = np.asarray(mod.mask(f), bool)
                    if "gap_le" in b:
                        mf &= f["gap"].to_numpy(float) <= b["gap_le"]
                m = np.zeros(len(fh), bool)
                fi = np.flatnonzero(mf)
                m[f2fh[fi]] = True
            out[s] = (m, stp)
    return out


def costfrac(c, tod, tier, R, mode):
    mult = np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))
    ent = (0.01 + c * 1e-4) * mult
    if mode == "rt":
        ent = ent + 0.01 + c * 1e-4 + 0.02
    return tier * ent / R


def month_job(month):
    global SPY_PREV
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    if SPY_PREV is None:
        SPY_PREV = _spy_prev()
    f, fh, P, dend, fh2P = build_paths(month)
    dts = pd.to_datetime(fh["date"])
    assert not ((dts >= LOCK[0]) & (dts <= LOCK[1])).any()
    spy = spy_fo(f, fh)
    cx = context(f, fh)
    f2fh = np.full(len(f), -1, np.int64)
    fi = fh["_fi"].to_numpy()
    f2fh[fi[fi >= 0]] = np.flatnonzero(fi >= 0)
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P))
    tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float),
                    P["tod"].to_numpy(np.int32))
    atrP = P["atr"].to_numpy(float)
    sym, dat = P["symbol"].to_numpy(), P["date"].astype(str).to_numpy()
    fsym, fdat = fh["symbol"].to_numpy(), fh["date"].astype(str).to_numpy()
    ftod = fh["tod"].to_numpy()
    fclose = fh["close"].to_numpy(float)
    adv = fh["adv20"].fillna(0).to_numpy()
    atr_ok = fh["atr_d"].to_numpy(float) > 0
    x = CL.arrays(fh)
    lev = S6.levels(x)
    H = hits_for(f, fh, f2fh, x, lev)
    pool = S5.ctrl_pool(P, 95e6)
    S5.K_CTRL = K_CTRL
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    qv, br, sg, sp = (cx[k].to_numpy(float) for k in ("qqq_vd", "breadth", "spy_gap", "spy_prev"))
    rows = []

    def run(ent, Rv, side, prm):
        return sim(h, l, c, tod, dend, tierP, ent.astype(np.int64), Rv, side, prm["up"], prm["dn"], prm["em"],
                   prm["tsb"], prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["xt"], prm["lim"])

    for s, b in SPEC.items():
        side = b["side"]
        m0, stp = H[s]
        risk_fh = (fclose - stp) if stp is not None else 0.25 * fh["atr_d"].to_numpy(float)
        for vid, knob, ov in grid(s):
            prm = {**EX0, "up": b["up"], "so": b["so"], **ov}
            lo, hi = prm["win"] or b["win"]
            with np.errstate(invalid="ignore"):
                m = m0 & (ftod >= max(950, lo)) & (ftod <= min(1500, hi)) & (adv >= b["adv"]) & atr_ok \
                    & np.isfinite(risk_fh) & (risk_fh > 0)
                k = prm["keep"]
                if k == "qqq_with":
                    m &= side * qv > 0
                elif k == "qqq_against":
                    m &= side * qv < 0
                elif k == "breadth":
                    m &= side * (br - 0.5) > 0
                elif k == "spygap":
                    m &= side * sg >= 0
                elif k == "prev_big":
                    m &= ~(np.abs(sp) > 1.0)
                elif k == "prev_quiet":
                    m &= ~(np.abs(sp) < 0.3)
                if prm["cost"] is not None:
                    mode, th = prm["cost"]
                    m &= costfrac(fclose, ftod, tier_fh, risk_fh, mode) <= th
            hit = np.flatnonzero(m)
            if b.get("refire"):
                pos = chain(fsym[hit], fdat[hit], ftod[hit], True, prm["cd"])
                e1 = hit[pos]
                if prm["symcap"]:
                    kk = pd.Series(fsym[e1].astype(str)) + "|" + pd.Series(fdat[e1])
                    e1 = e1[(kk.groupby(kk).cumcount() < prm["symcap"]).to_numpy()]
            else:
                e1 = gates.first_per_symbol_day(fsym, fdat, m)
            if prm["daycap"]:
                o = np.lexsort((fsym[e1].astype(str), ftod[e1], fdat[e1]))
                e1 = e1[o]
                rk = pd.Series(fdat[e1]).groupby(fdat[e1]).cumcount().to_numpy()
                e1 = np.sort(e1[rk < prm["daycap"]])
            ent = fh2P[e1]
            Rv = risk_fh[e1]
            res = run(ent, Rv, side, prm)
            second = np.zeros(len(ent), bool)
            if prm["reentry"]:
                allrows = np.sort(fh2P[hit])
                nx = next_after(allrows, res[5], dend, prm["reentry"])
                P2fh = P["_fhi"].to_numpy()
                e2 = P2fh[nx[nx >= 0]]
                ent2, Rv2 = fh2P[e2], risk_fh[e2]
                res2 = run(ent2, Rv2, side, prm)
                ent, Rv = np.r_[ent, ent2], np.r_[Rv, Rv2]
                res = tuple(np.r_[a, a2] for a, a2 in zip(res, res2))
                second = np.r_[second, np.ones(len(e2), bool)]
            r, mfe, mae, cd, et, xr = res
            # random control: same date and bar, same risk in ATR units, same mechanics
            ae = atrP[np.maximum(ent, 0)]
            katr = Rv / np.where(ae > 0, ae, np.nan)
            cr = S5.ctrl_rows(pool, ent, rng)
            cr_r = np.full(cr.shape, np.nan)
            for kq in range(K_CTRL):
                rq = cr[:, kq]
                Rc = np.where(rq >= 0, katr * atrP[np.maximum(rq, 0)], np.nan)
                cr_r[:, kq] = run(rq, Rc, side, prm)[0]
            cnt = np.isfinite(cr_r).sum(1)
            ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan)
            fhe = np.r_[e1, e2] if prm["reentry"] else e1
            t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "tod": et, "r": r / prm["dn"],
                              "mfe": mfe, "code": cd, "ctrl": ctrl / prm["dn"], "second": second,
                              "spy_fo": spy[fhe]})
            t["setup"], t["var"], t["knob"] = s, vid, knob
            rows.append(t[np.isfinite(t["r"].to_numpy())])
    out = pd.concat(rows, ignore_index=True)
    out = out.astype({"setup": "category", "var": "category", "knob": "category", "symbol": "category",
                      "r": "float32", "mfe": "float32", "ctrl": "float32", "spy_fo": "float32"})
    print(month, len(out), round(time.time() - t0), flush=True)
    return out


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    if len(sys.argv) > 1:
        months = sys.argv[1:]
    n = sum(len(grid(s)) - 1 for s in SETUPS)
    print("variants (excl parents):", n, {s: len(grid(s)) - 1 for s in SETUPS}, flush=True)
    with Pool(int(os.environ.get("SW15_PROCS", 2)), maxtasksperchild=1) as p:
        T = pd.concat(p.map(month_job, months, chunksize=1), ignore_index=True)
    T.to_parquet(SCR / ("trades.parquet" if len(sys.argv) == 1 else "trades_test.parquet"), index=False)
    print(T.groupby(["setup", "var"], observed=True).agg(n=("r", "size"), exp=("r", "mean")).round(4).to_string())


if __name__ == "__main__":
    main()
