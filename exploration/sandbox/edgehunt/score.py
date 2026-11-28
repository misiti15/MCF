"""EDGEHUNT scoring (pre-registered in exploration/findings/edgehunt_prereg.md). cwd = repo checkout.
Usage: python score.py HOLD_PARQUET. Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from statistics import NormalDist
class norm:
    @staticmethod
    def sf(x):
        return np.array([1 - NormalDist().cdf(float(v)) for v in np.atleast_1d(x)])
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/primshorts_1126"))
import calib_live as CLV  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402

LOCK = ("2024-11-01", "2025-02-28")
SHORT = {"L3-gap-slope-fromopen-FD": "L3", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
         "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5", "NM-ETF-late-dip-di-long": "NMETF",
         "GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long": "GEN0920"}

c = pd.read_parquet(sys.argv[1])
d = c.date.astype(str)
assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
c["s"] = c.setup.map(SHORT)
c["rp"] = c.risk / c.entry * 100
cells = json.load(open("research/primshorts_1126/cells_live.json"))
kd = np.where(c.hkind == 1, "stop", "market")
c["hgross"] = c.side * (c.hpx - c.entry) / c.risk
liveL = CLV.predict_R(cells, c.entry.to_numpy(), c.risk.to_numpy(), kd)
ecost = (0.01 + c.entry * 1e-4) * tod_cost_mult(c.tod.to_numpy())
xcost = 0.01 + c.hpx * 1e-4 + np.where(c.hkind == 1, 0.02, 0.0)
lr8 = (ecost + xcost) / c.risk
c["hr"] = np.where(c.side < 0, c.hgross - liveL, c.hgross - lr8)
c["hr_liveL"] = c.hgross - liveL
c["year"] = d.str[:4]


def ct(r, dates):
    if len(r) < 3:
        return float("nan")
    m = r.mean(); e = (r - m).groupby(dates).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(r)
    return float(m / se) if se > 0 else float("nan")


def st(g, col):
    r = g[col]
    if not len(r):
        return dict(n=0)
    ds = r.groupby(g.date).sum()
    best = ds.idxmax(); tot = r.sum()
    wo = r[g.date != best]
    return dict(n=len(r), days=int(ds.size), mean=r.mean(), t=ct(r, g.date), tot=tot,
                wo_best=wo.mean() if len(wo) else np.nan, best_share=(ds.max() / tot) if tot > 0 else np.nan,
                rpd=tot / ds.size)


ARMS = {"W1": (lambda g: g.rp >= 1.0, "r"), "W2": (lambda g: g.rp >= 2.0, "r"),
        "H0": (lambda g: g.rp > -1, "hr"), "H1": (lambda g: g.rp >= 1.0, "hr")}
rows = []
for s in SHORT.values():
    for arm, (f, col) in ARMS.items():
        row = dict(setup=s, arm=arm)
        for per in ("CHECK", "T2", "FIT"):
            g0 = c[(c.s == s) & (c.per == per)]
            g = g0[f(g0)]
            x = st(g, col); b = st(g0, "r")
            ndays_base = g0.date.nunique()
            for k, v in x.items():
                row[f"{per}_{k}"] = v
            row[f"{per}_base"] = b.get("mean", np.nan)
            row[f"{per}_dlot"] = x.get("mean", np.nan) - b.get("mean", np.nan)
            row[f"{per}_drpd"] = (g[col].sum() - g0.r.sum()) / max(ndays_base, 1)
        rows.append(row)
R = pd.DataFrame(rows)
pc = norm.sf(R.CHECK_t.fillna(-9)); pt = norm.sf(R.T2_t.fillna(-9))
R["p"] = np.maximum(pc, pt)
o = np.argsort(R.p.to_numpy()); m = len(R); adj = np.empty(m); run = 0
for k, i in enumerate(o):
    run = max(run, min(1.0, (m - k) * R.p.iloc[i])); adj[i] = run
R["p_holm"] = adj
R["PASS"] = ((R.CHECK_n >= 100) & (R.T2_n >= 100) & (R.CHECK_mean > 0) & (R.CHECK_t >= 2) & (R.T2_mean > 0)
             & (R.T2_t >= 2) & (R.p_holm < 0.05) & (R.CHECK_wo_best > 0) & (R.T2_wo_best > 0)
             & (R.CHECK_best_share < 0.5) & (R.T2_best_share < 0.5))
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)
cols = ["setup", "arm"] + [f"{p}_{k}" for p in ("CHECK", "T2") for k in ("n", "mean", "t", "wo_best", "best_share", "base", "dlot", "drpd")] + ["FIT_n", "FIT_mean", "p_holm", "PASS"]
print(R[cols].round(3).to_string())
print("\nPASS cells:", int(R.PASS.sum()), "of", len(R))
print("\nPer arm: setups better / worse per lot vs own base (CHECK, T2); mean dlot")
for arm in ARMS:
    a = R[R.arm == arm]
    print(arm, {p: (int((a[f"{p}_dlot"] > 0).sum()), int((a[f"{p}_dlot"] < 0).sum()), round(a[f"{p}_dlot"].mean(), 3),
                    round(a[f"{p}_drpd"].mean(), 3)) for p in ("CHECK", "T2")})
print("\nGross (before cost) per lot, base cost proxy and hold arms, by setup x split")
for s in SHORT.values():
    for per in ("CHECK", "T2"):
        g = c[(c.s == s) & (c.per == per)]
        print(s, per, "H gross %.3f  H net %.3f  H net(liveL) %.3f  H cost %.3f  hold stop-exit share %.2f  med rp %.2f" % (
            g.hgross.mean(), g.hr.mean(), g.hr_liveL.mean(), (g.hgross - g.hr).mean(), (g.hkind == 1).mean(), g.rp.median()))
print("\nBy year, H0 and W1 net R per lot")
for s in SHORT.values():
    g = c[c.s == s]
    print(s, "H0", g.groupby("year").hr.mean().round(3).to_dict(), "W1", g[g.rp >= 1].groupby("year").r.mean().round(3).to_dict())
print("\nPooled descriptive (not scored): side x arm")
for side, nm in ((-1, "shorts"), (1, "longs")):
    for per in ("CHECK", "T2"):
        g = c[(c.side == side) & (c.per == per)]
        print(nm, per, {"base": round(g.r.mean(), 3), "W1": round(g[g.rp >= 1].r.mean(), 3), "W2": round(g[g.rp >= 2].r.mean(), 3),
                        "H0": round(g.hr.mean(), 3), "H1": round(g[g.rp >= 1].hr.mean(), 3)})
R.to_csv(Path(__file__).parent / "cells.csv", index=False)
