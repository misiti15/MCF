"""COMPASS-LEARN round 1, step 5 (PLAN.md): midday FLIP detector - can we tell that the morning side has reversed?
Usage: python flip.py <scratch> (after study.py). Writes flip.csv, flip_days_live.csv. Educational only."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402

S = Path(sys.argv[1])
P = pd.read_parquet(S / "panel.parquet")
A = pd.read_parquet(S / "hunch_agg.parquet"); A = A[A.scored].copy(); A["T"] = 573 + 3 * A.b
pan = E.Panel(P, A.sort_values(["date", "T"])[["date", "T", "share_up"]])
C = pd.read_csv(HERE / "configs.csv")
coefs = pd.read_pickle(S / "coefs.pkl")
best = C[C.family != "BASE"].sort_values("VALID_S", ascending=False).iloc[0]
bestL = C[C.family == "LOGIT"].sort_values("VALID_S", ascending=False).iloc[0]
print("best compass", best.config, "best logit", bestL.config)


def held_of(p, cfg):
    r = C.set_index("config").loc[cfg]
    if cfg == "B-W60":
        return E.vote(p, 15, 60, 0.0)[0]
    if r.family == "VOTE":
        return E.vote(p, int(r.I), int(r.W), float(r.theta))[0]
    if r.family == "CHK":
        return E.chk(p, int(r.I), float(r.theta), int(r.W) or None)[0]
    if r.family == "LOGIT":
        return E.logit_read(E.logit_P(p, r.model, coefs[r.model]), int(r.I), float(r.pstar))[0]
    if r.family == "ADD1":
        if r.base == "B-W60":
            return E.vote(p, 15, 60, 0.0, filt=E.filters(p)[r.filt])[0]
        b = C.set_index("config").loc[r.base]
        return E.chk(p, int(b.I), float(b.theta), int(b.W) or None, filt=E.filters(p)[r.filt])[0]
    raise ValueError(cfg)


def detectors(p):
    fo = p.m["fo"]; vw = p.m["vw"]; br = p.m["br"]
    PL = E.logit_P(p, bestL.model, coefs[bestL.model])
    hw = held_of(p, "B-W60"); hb = held_of(p, best.config)
    D = {}
    for k in (1, 2, 3):
        D[f"D1-open-k{k}"] = lambda M, k=k: _consec(np.sign(np.nan_to_num(fo)) == -M, k)
    for rho in (0.5, 0.75):
        def d2(M, rho=rho):
            fav = np.where(M > 0, p.m["mfe_up"], -p.m["mfe_dn"])
            return (np.nan_to_num(vw) * M < 0) & (np.nan_to_num(fo) * M <= (1 - rho) * fav)
        D[f"D2-vwap-giveback{int(rho * 100)}"] = d2
    D["D3-W60-against"] = lambda M: hw == -M
    D[f"D3-{best.config}-against"] = lambda M: hb == -M
    D["D4-breadth-vwap"] = lambda M: ((np.nan_to_num(br, nan=0.5) - 0.5) * M <= -0.05) & (np.nan_to_num(vw) * M < 0)
    for q in (0.5, 0.4, 0.3):
        D[f"D5-logit-q{int(q * 100)}"] = lambda M, q=q: np.where(M > 0, PL, 1 - PL) < q
    return D


def _consec(x, k):
    out = np.zeros_like(x, bool)
    run = np.zeros(x.shape[0])
    for j in range(x.shape[1]):
        run = np.where(x[:, j], run + 1, 0); out[:, j] = run >= k
    return out


rows, live = [], []
for per in ["TRAIN", "VALID", "FWD", "LIVE"]:
    p = pan.sub(pan.period == per)
    D = detectors(p)
    for St in (660, 720, 780):
        j0 = E.mi(St)
        fS = p.m["fo"][:, j0]
        has = np.abs(np.nan_to_num(fS)) >= 0.002
        M = np.where(has, np.sign(np.nan_to_num(fS)), 0)[:, None]
        R1 = (p.eod != M[:, 0]) & has & (p.eod != 0)
        R2 = has & ((p.close / p.m["px"][:, j0] - 1) * M[:, 0] <= -0.0025)
        for name, fn in D.items():
            F = fn(M).astype(bool); F[:, :j0] = False
            fl = F.any(1) & has
            ft = np.where(fl, E.MARKS[np.argmax(F, 1)], np.nan)
            jj = np.argmax(F, 1)
            pxf = p.m["px"][np.arange(len(jj)), jj]
            left = (p.close / pxf - 1) * (-M[:, 0]) * 1e4
            for tn, tr in (("R1", R1), ("R2", R2)):
                n_r, n_nr = (tr & has).sum(), (~tr & has).sum()
                tp, fp = (fl & tr).sum(), (fl & ~tr & has).sum()
                rec = tp / max(n_r, 1); far = fp / max(n_nr, 1)
                rows.append(dict(period=per, start=E.lab(St), detector=name, truth=tn, days=int(has.sum()),
                                 rev_days=int(n_r), flagged=int(fl.sum()), recall=rec, false_flag=far, J=rec - far,
                                 precision=tp / max(fl.sum(), 1),
                                 med_flag=E.lab(int(np.nanmedian(ft[fl & tr]))) if (fl & tr).any() else "",
                                 left_bps_tp=float(np.nanmean(left[fl & tr])) if (fl & tr).any() else np.nan,
                                 left_bps_all=float(np.nanmean(left[fl])) if fl.any() else np.nan,
                                 correct_day=list(((fl & tr) | (~fl & ~tr))[has].astype(int))))
            if per == "LIVE" and St == 720:
                for i, d in enumerate(p.dates):
                    live.append(dict(date=d, detector=name, morning_side=int(M[i, 0]), reversed_R1=bool(R1[i]),
                                     flag=E.lab(int(ft[i])) if np.isfinite(ft[i]) else ""))
F = pd.DataFrame(rows)
# paired day-level t vs D1-open-k1 (same days)
ref = {(r.period, r.start, r.truth): np.array(r.correct_day) for r in F[F.detector == "D1-open-k1"].itertuples()}
F["t_vs_D1k1"] = [E.paired_t(np.array(r.correct_day, float), ref[(r.period, r.start, r.truth)].astype(float))
                  for r in F.itertuples()]
F = F.drop(columns="correct_day")
F.to_csv(HERE / "flip.csv", index=False)
pd.DataFrame(live).to_csv(HERE / "flip_days_live.csv", index=False)
W = F[(F.truth == "R1") & (F.start == "12:00")].pivot_table(index="detector", columns="period",
                                                            values=["J", "recall", "false_flag", "precision"])
pd.set_option("display.width", 250)
print(F[(F.truth == "R1") & (F.start == "12:00") & (F.period.isin(["TRAIN", "VALID"]))].round(3).to_string())
