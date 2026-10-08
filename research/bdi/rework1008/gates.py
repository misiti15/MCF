"""Apply the pre-declared gates + plateau to data/grid.parquet. Writes data/gated.parquet.
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from grid import F1_M, F2_B, F2_H, F2_W, F3_BEAR, F3_BULL, F3_W  # noqa: E402


def adj(lst):
    return {a: lst[max(0, i - 1):i] + lst[i + 1:i + 2] for i, a in enumerate(lst)}


M_ADJ = {}
for d in ("up", "dn"):
    M_ADJ.update(adj([f"{d}>{p}%" for p in (1, 2, 3, 4)]))
    M_ADJ.update(adj([f"{d}>{a}atr" for a in (0.5, 0.75, 1.0, 1.5)]))
NEIGH = {
    "F1": {1: M_ADJ, 2: {"rsi>=60": ["rsi>=70"], "rsi>=70": ["rsi>=60"], "rsi<=30": ["rsi<=40"], "rsi<=40": ["rsi<=30"]},
           "w": {"early": ["am"], "am": ["early", "mid", "all"], "mid": ["am", "pm"], "pm": ["mid", "all"], "all": ["am", "pm"]}},
    "F2": {0: adj(F2_H), 1: adj(F2_B), 2: {"rsi5>70": ["rsi5>80"], "rsi5>80": ["rsi5>70"]}, "w": adj(list(F2_W))},
    "F3bear": {0: adj(F3_BEAR[0]), 1: adj(F3_BEAR[1]), "w": adj(list(F3_W))},
    "F3bull": {0: adj(F3_BULL[0]), 1: adj(F3_BULL[1]), "w": adj(list(F3_W))},
}


def key(fam, cs, w, side, g):
    return (fam, *cs, w, side, g)


def main():
    r = pd.read_parquet(HERE / "data" / "grid.parquet")
    r["c3"] = r["c3"].fillna("")
    cols = ["c0", "c1", "c2", "c3"]
    lut = {key(f, (a, b, c, d), w, s, g): (te, ve) for f, a, b, c, d, w, s, g, te, ve in
           zip(r.family, r.c0, r.c1, r.c2, r.c3, r.window, r.side, r.geom, r.tr_exp, r.va_exp)}
    r["g_pos"] = (r.tr_exp > 0) & (r.va_exp > 0)
    r["g_n"] = r.va_n >= 30
    r["g_t"] = r.va_t >= 1.5
    r["g_halves"] = (r.tr_h1 > 0) & (r.tr_h2 > 0)
    r["g_base"] = (r.tr_exp > r.tr_base) & (r.va_exp > r.va_base)
    pre = r.g_pos & r.g_n & r.g_t & r.g_halves & r.g_base
    pl_n, pl_tr, pl_va, pl_frac, pl_ok = [], [], [], [], []
    for i in np.flatnonzero(pre.to_numpy()):
        x = r.iloc[i]
        cs = [x[c] for c in cols]
        nb = []
        for dim, mp in NEIGH[x.family].items():
            if dim == "w":
                for w2 in mp.get(x.window, []):
                    nb.append(key(x.family, tuple(cs), w2, x.side, x.geom))
            else:
                for v in mp.get(cs[dim], []):
                    c2 = list(cs)
                    c2[dim] = v
                    nb.append(key(x.family, tuple(c2), x.window, x.side, x.geom))
        vals = [lut[k] for k in nb if k in lut and np.isfinite(lut[k][1])]
        if len(vals) < 2:
            pl_n.append(len(vals)); pl_tr.append(np.nan); pl_va.append(np.nan); pl_frac.append(np.nan); pl_ok.append(False)
            continue
        te = np.array([v[0] for v in vals]); ve = np.array([v[1] for v in vals])
        frac = (ve > 0).mean()
        pl_n.append(len(vals)); pl_tr.append(te.mean()); pl_va.append(ve.mean()); pl_frac.append(frac)
        pl_ok.append(bool(te.mean() > 0 and ve.mean() > 0 and frac >= 2 / 3))
    for c in ("pl_n", "pl_tr", "pl_va", "pl_frac", "g_plateau"):
        r[c] = np.nan if c != "g_plateau" else False
    ii = np.flatnonzero(pre.to_numpy())
    r.loc[r.index[ii], "pl_n"] = pl_n
    r.loc[r.index[ii], "pl_tr"] = pl_tr
    r.loc[r.index[ii], "pl_va"] = pl_va
    r.loc[r.index[ii], "pl_frac"] = pl_frac
    r.loc[r.index[ii], "g_plateau"] = pl_ok
    r["g_all"] = pre & r.g_plateau.astype(bool)
    r["score"] = np.minimum(r.tr_t, r.va_t)
    r.to_parquet(HERE / "data" / "gated.parquet")
    print("scored", len(r))
    for g in ("g_pos", "g_n", "g_t", "g_halves", "g_base", "g_plateau", "g_all"):
        print(g, int(r[g].sum()))
    print("pre-plateau pass", int(pre.sum()))
    print(r.groupby("family")[["g_pos", "g_t", "g_all"]].sum())
    pd.set_option("display.width", 250)
    show = ["family", "conds", "window", "side", "geom", "tr_n", "tr_exp", "tr_t", "tr_h1", "tr_h2", "va_n", "va_exp",
            "va_t", "va_exbest", "pl_va", "pl_frac", "score"]
    print(r[r.g_all].sort_values("score", ascending=False)[show].head(60).to_string())


if __name__ == "__main__":
    main()
