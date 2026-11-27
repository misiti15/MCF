"""TAILEFF-1127 scoring (PREREG.md metrics, tail efficiency E, exposure-matched constant cut, random-block control, pass bar).
Usage: python score.py W [NDRAWS]. Educational only - not financial advice."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1]); ND = int(sys.argv[2]) if len(sys.argv) > 2 else 20
LOCK = ("2024-11-01", "2025-02-28")
SHN = ["L3", "RW3", "RW5", "NM-ETF"]
CFGS = ["LO", "G1-3", "LO+B8", "LO+K4+SHK", "LO+S8", "LO+B8+K4"]
JREF = {"LO": "BASE", "G1-3": "BASE"}
PERS = ["FIT", "CHECK", "T2"]


def load(book, cfg):
    x = pd.read_parquet(W / f"day_{book}_{cfg}.parquet")
    assert not ((x.date >= LOCK[0]) & (x.date <= LOCK[1])).any()
    x["R"] = x[[f"R{s}" for s in range(4)]].sum(axis=1)
    x["EX"] = x[[f"E{s}" for s in range(4)]].sum(axis=1)
    x["NL"] = x[[f"N{s}" for s in range(4)]].sum(axis=1)
    return x


def tail(r):
    return -np.sort(r)[:5].sum()


def floor20(r):
    return pd.Series(r).rolling(20).sum().min()


def stats(r):
    yrs = len(r) / 252
    return dict(avg=r.mean(), tot=r.sum(), red_m=(r < -1e-9).mean() * 21, w5=-tail(r), le10=int((r <= -10).sum()),
                floor=floor20(r), yrs=yrs)


def compare(c, f, per):
    c, f = c[c.per == per].reset_index(drop=True), f[f.per == per].reset_index(drop=True)
    assert (c.date.values == f.date.values).all()
    rc, rf = c.R.to_numpy(), f.R.to_numpy()
    yrs = len(rc) / 252
    p = 1 - c.EX.sum() / f.EX.sum(); pl = 1 - c.NL.sum() / f.NL.sum()
    cut = (1 - p) * rf; cutl = (1 - pl) * rf
    Lr, Lc, Lk = tail(rf), tail(rc), tail(cut)
    if p > 0:
        E = (Lr - Lc) / (Lr - Lk)
    else:
        E = np.inf if Lc < Lr else -np.inf
    d = rc - rf; best = d.max()
    sc, sf, sk = stats(rc), stats(rf), stats(cut)
    o = dict(per=per, n=len(rc), p_expo=p, p_lots=pl, E=E, E_lots=(Lr - Lc) / (Lr - tail(cutl)) if pl > 0 else np.nan,
             dR=d.sum(), dRyr=d.sum() / yrs, avg=sc["avg"], ref_avg=sf["avg"], red_m=sc["red_m"], ref_red_m=sf["red_m"],
             cut_red_m=sk["red_m"], w5=sc["w5"], ref_w5=sf["w5"], cut_w5=sk["w5"], le10=sc["le10"], ref_le10=sf["le10"],
             cut_le10=sk["le10"], floor=sc["floor"], ref_floor=sf["floor"], cut_floor=sk["floor"],
             best_share=best / d.sum() if d.sum() > 0 else np.nan, dR_wo_best_day=(d.sum() - best) / max(len(d) - 1, 1),
             k4_yr=c.k4.sum() / yrs, shk_yr=c.shk.sum() / yrs, s8_yr=(c.s8f > 0).sum() / yrs, b8_yr=(c.b8blk > 0).sum() / yrs)
    for s in range(4):
        o[f"d_{SHN[s]}_yr"] = (c[f"R{s}"].sum() - f[f"R{s}"].sum()) / yrs
    return o


rows = []
for book in ("RAW", "Z", "P"):
    D = {k: load(book, k) for k in ["BASE"] + CFGS}
    for cfg in CFGS:
        refs = [JREF.get(cfg, "LO")] + ([] if cfg in JREF else ["BASE"])
        for ref in refs:
            for per in PERS:
                rows.append(dict(book=book, cfg=cfg, ref=ref, judged=ref == refs[0], **compare(D[cfg], D[ref], per)))
R = pd.DataFrame(rows)
R.to_csv(W / "results.csv", index=False)


def verdict(cfg, ref):
    out = {}
    ok = True
    for per in ("CHECK", "T2"):
        z = R[(R.book == "Z") & (R.cfg == cfg) & (R.ref == ref) & (R.per == per)].iloc[0]
        pp = R[(R.book == "P") & (R.cfg == cfg) & (R.ref == ref) & (R.per == per)].iloc[0]
        c1 = z.E >= 1.25
        c2 = (z.floor > z.cut_floor) and (z.le10 < z.cut_le10)
        c3 = (pp.red_m - pp.ref_red_m <= 1.0) and (pp.dRyr >= -40)
        c4 = min(z[f"d_{s}_yr"] for s in SHN) >= -10
        out[per] = dict(E=bool(c1), floor_le10=bool(c2), P_book=bool(c3), setups=bool(c4))
        ok = ok and c1 and c2 and c3 and c4
    out["PASS"] = bool(ok)
    return out


V = {}
for cfg in CFGS:
    V[cfg] = {"judged_ref": JREF.get(cfg, "LO"), "judged": verdict(cfg, JREF.get(cfg, "LO"))}
    if cfg not in JREF:
        V[cfg]["vs_BASE"] = verdict(cfg, "BASE")

# size-matched random block (finding #7)
RBO = {}
for tgt in ("LO+B8", "LO+B8+K4"):
    for book in ("RAW", "Z"):
        c, f = load(book, tgt), load(book, "LO")
        dr = [load(book, f"RBLO~{tgt}~{1127 + i}") for i in range(ND) if (W / f"day_{book}_RBLO~{tgt}~{1127 + i}.parquet").exists()]
        if not dr:
            continue
        for per in ("CHECK", "T2", "FIT"):
            sel = lambda x: x[x.per == per].R.to_numpy()  # noqa: E731
            rc = sel(c); rr = np.stack([sel(x) for x in dr]); m = rr.mean(0)
            dd = rc - m; t = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))
            w5r = np.array([-tail(x) for x in rr]); flr = np.array([floor20(x) for x in rr])
            le = np.array([(x <= -10).sum() for x in rr])
            RBO[f"{tgt}|{book}|{per}"] = dict(n_draws=len(dr), w5=-tail(rc), w5_rand_mean=w5r.mean(),
                                              w5_rand_p90=float(np.quantile(w5r, 0.9)), le10=int((rc <= -10).sum()),
                                              le10_rand_mean=le.mean(), floor=floor20(rc), floor_rand_mean=flr.mean(),
                                              floor_rand_p90=float(np.quantile(flr, 0.9)), ref_w5=-tail(sel(f)),
                                              lots=int(c[c.per == per].NL.sum()),
                                              lots_rand=float(np.mean([x[x.per == per].NL.sum() for x in dr])),
                                              t_daily_vs_rand=t, avg_d_vs_rand=dd.mean())
json.dump(dict(verdict=V, random_block=RBO), open(W / "score.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
cols = ["book", "cfg", "ref", "per", "p_expo", "p_lots", "E", "dRyr", "avg", "ref_avg", "red_m", "ref_red_m", "w5", "ref_w5",
        "cut_w5", "le10", "cut_le10", "floor", "cut_floor", "best_share"] + [f"d_{s}_yr" for s in SHN]
print(R[cols].round(2).to_string())
print(json.dumps(V, indent=1))
print(json.dumps(RBO, indent=1, default=float))
