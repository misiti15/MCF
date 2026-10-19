"""Adversarial checks for the N1 candidate (PLAN.md amendment 2026-10-17): excess t, beta hedge, top-300 universe,
2x costs, excess by year, wider cluster blocks. Locked block NaN as in common.py. Educational only - not financial advice.
Run: python research/bdi/sat1017/diag_n1.py -> diag_n1.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "bdi" / "cwt" / "test_c"))
import common as cm  # noqa: E402
from common import C, Cn, Cx, ELIG, Ox, SPY, T, book, dates, locked, clust_t  # noqa: E402

lr = np.log(C / C.shift(1)); m = lr["SPY"]
var_m = m.rolling(252, min_periods=200).var()
BETA = lr.rolling(252, min_periods=200).cov(pd.DataFrame({s: m for s in C.columns}), pairwise=False).div(var_m, axis=0).to_numpy()
prevC = np.vstack([np.full(Cn.shape[1], np.nan), Cn[:-1]])
with np.errstate(invalid="ignore", divide="ignore"):
    ON = pd.DataFrame(np.log(cm.On / prevC), index=dates); ID = pd.DataFrame(np.log(Cn / cm.On), index=dates)
dser = pd.Series(np.arange(T), index=dates); iso = dates.isocalendar()
WEEK_END = dser.groupby([iso.year.values, iso.week.values]).max().to_numpy()
ADVR = (C * cm.V).rolling(20, min_periods=15).median().to_numpy()


def signals(feat, L, top300=False):
    son = ON.rolling(L, min_periods=int(0.8 * L)).sum().to_numpy(); sid = ID.rolling(L, min_periods=int(0.8 * L)).sum().to_numpy()
    F = son if feat == "ON" else son - sid
    sig = np.zeros_like(ELIG)
    for i in WEEK_END:
        ok = ELIG[i] & np.isfinite(F[i])
        if top300:
            a = np.where(ok, ADVR[i], -np.inf); ok &= a >= np.sort(a)[-300]
        if ok.sum() < 50:
            continue
        sig[i] = ok & (F[i] >= np.quantile(F[i, ok], 0.9))
    return sig


def make_h(H):
    def make(i, j):
        ei = i + 1
        if ei >= T or locked[ei] or not np.isfinite(Ox[ei, j]):
            return None
        r = cm.walk(j, ei, Ox[ei, j], 1, "O", None, None, None, i + H)
        return None if r is None else {"i": i, "j": j, "ei": ei, "ep": Ox[ei, j], "ek": "O", "xi": r[0], "xp": r[1], "xk": r[2]}
    return make


SPL = {"train": ("2016-01-01", "2022-12-31"), "valid1": ("2023-01-01", "2024-10-31"), "valid2": ("2025-03-01", "2026-12-31"),
       "trval": ("2016-01-01", "2024-10-31")}
rows = []
for feat, L, H in (("ONID", 20, 20), ("ON", 20, 20), ("ONID", 60, 20), ("ONID", 20, 5)):
    for uni in ("all", "top300"):
        t = book(signals(feat, L, uni == "top300"), 1, make_h(H))
        t["bench"] = cm.bench(t)
        cst = cm.cost(t.ep) + cm.cost(t.xp)
        t["exc_net"] = t.gross - t.bench - cst          # net excess (costs charged to the strategy only)
        b = np.clip(np.nan_to_num(BETA[t.i, t.j], nan=1.0), 0, 3)
        se, sx = Ox[t.ei, SPY], Cx[t.xi, SPY]
        days = np.maximum((dates[t.xi.to_numpy()] - dates[t.ei.to_numpy()]).days.to_numpy(), 1)
        t["hedged"] = t.net - b * (sx / se - 1) - b * (cm.cost(se) + cm.cost(sx)) - b * 0.03 * days / 365
        t["net2x"] = t.net - cst
        for k, (a, z) in SPL.items():
            g = t[(t.date >= a) & (t.date <= z)]
            row = {"cfg": f"N1_{feat}_L{L}_H{H}", "uni": uni, "split": k, "n": len(g)}
            for c in ("net", "exc_net", "hedged", "net2x"):
                x = g[c].to_numpy(float)
                row[f"{c}_bps"] = round(x.mean() * 1e4, 1)
                row[f"{c}_t40"] = round(clust_t(x, g.i.to_numpy() // 40), 2)
                row[f"{c}_t80"] = round(clust_t(x, g.i.to_numpy() // 80), 2)
            row["beta"] = round(float(b[(t.date >= a) & (t.date <= z)].mean()), 2)
            rows.append(row)
        if (feat, L, H, uni) == ("ONID", 20, 20, "all"):
            yr = t.groupby(t.date.dt.year)[["net", "exc_net", "hedged"]].mean().mul(1e4).round(1)
            yr["n"] = t.groupby(t.date.dt.year).size()
            print(yr.to_string())
            yr.to_csv(HERE / "diag_n1_years.csv")
        print(feat, L, H, uni, flush=True)
d = pd.DataFrame(rows)
d.to_csv(HERE / "diag_n1.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(d.to_string())
