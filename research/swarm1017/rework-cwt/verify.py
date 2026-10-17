"""Exact gate re-check of every screen survivor / near-miss in results.csv with mcf.research.gates (summary,
regime_split, walk_forward excluding the locked months), concentration (rule 5) and the plateau (PLAN gate 6).
Educational only - not financial advice.   python verify.py <scratch>  -> verify.csv, finalists.csv"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT), str(ROOT / "research" / "history2y")]
import lib  # noqa: E402
import scan as SC  # noqa: E402
from mcf.research import gates as G  # noqa: E402

scr = Path(sys.argv[1])
R = pd.read_csv(HERE / "results.csv")
D = pd.concat([pd.read_parquet(p) for p in sorted(scr.glob("scan_*.parquet"))], ignore_index=True)
S, cuts = SC.load(scr)
FAMS = SC.families()
REG = lib.regimes()
GRID = {"B1": [("a", (1.0, 1.5, 2.0, 2.5, 3.0)), ("d", (0.3, 0.4, 0.5)), ("T", (1, 2))],
        "B2": [("sd", ("above", "below")), ("z", (0.25, 0.5, 0.75, 1.0, 1.25, 1.5))],
        "B4a": [("k", (2, 3, 4, 6, 8)), ("tc", (2, 3, 4))],
        "B4b": [("s", (0.5, 1.0, 1.5, 2.0)), ("pb", ("0.3-0.5", "0.2-0.6", "0.2-0.4", "0.4-0.6"))],
        "B5": [("m", (0.5, 0.75, 1.0, 1.25)), ("v", (2, 3, 5, 8))],
        "A7": [("g", (3, 5, 7, 10, 15)), ("T", (1, 2))]}
CTX = {}


def ctx(fam):
    if fam not in CTX:
        V = {v[0]: v for v in FAMS[fam]}
        m_any = np.zeros(len(S), bool)
        for v in V.values():
            m_any |= v[6](S)
        Sf = S[m_any].reset_index(drop=True)
        CTX[fam] = (Sf, V, SC.Ctx(Sf, "ball" if fam == "A7" else "b95"), SC.filters(Sf, cuts))
    return CTX[fam]


def trades(row):
    Sf, V, C, F = ctx(row.fam)
    m = V[row.vid][6](Sf)
    for f in (row.f1, row.f2):
        if isinstance(f, str) and f:
            m = m & F[f]
    w = tuple(int(x) for x in row.win.split("-"))
    valid = np.isfinite(C.R[("short", "S")][0]) if row.exit == "S" else None
    idx = C.pick(m, w, row.pick == "refire", valid)
    r, x = C.R[(row.side, row.exit)]
    ok = np.isfinite(r[idx])
    idx = idx[ok]
    return pd.DataFrame({"date": Sf["date"].to_numpy()[idx], "symbol": Sf["symbol"].to_numpy()[idx],
                         "tod": Sf["tod"].to_numpy()[idx], "r": r[idx], "x": x[idx]})


def neighbours(fam, vid):
    prm = next(v[1] for v in FAMS[fam] if v[0] == vid)
    out = []
    for k, vals in GRID[fam]:
        i = list(vals).index(prm[k])
        for j in (i - 1, i + 1):
            if 0 <= j < len(vals):
                p2 = dict(prm)
                p2[k] = vals[j]
                for v in FAMS[fam]:
                    if v[1] == p2:
                        out.append(v[0])
    return out


rows = []
key = ["fam", "stage", "side", "exit", "win", "pick", "f1", "f2"]
D["f1"], D["f2"] = D["f1"].fillna(""), D["f2"].fillna("")
R["f1"], R["f2"] = R["f1"].fillna(""), R["f2"].fillna("")
Dk = D.set_index(["fam", "vid", "side", "exit", "win", "pick", "f1", "f2"])
for row in R.itertuples(index=False):
    t = trades(row)
    s = G.summary(t)
    rg = G.regime_split(t, REG)
    wf = G.walk_forward(t, exclude_months=lib.LOCKED_MONTHS)
    g = t.groupby("date")["r"].agg(["size", "sum"])
    maxshare = float(g["size"].max() / len(t))
    tr = pd.to_datetime(t["date"]) < "2026-01-01"
    nb = neighbours(row.fam, row.vid)
    nb_ok = []
    for v in nb:
        try:
            q = Dk.loc[(row.fam, v, row.side, row.exit, row.win, row.pick, row.f1, row.f2)]
            q = q.iloc[0] if isinstance(q, pd.DataFrame) else q
            nb_ok.append(bool(q["exp_tr"] > 0 and q["exp_va"] > 0))
        except KeyError:
            pass       # stage C exists for parent variants only: neighbour not scored
    o = row._asdict()
    o.update({"v_n": s["n"], "v_exp": s["exp_r"], "v_t": s["t"], "ex_best_day": s["ex_best_day"], "max_day_share": round(maxshare, 3),
              "green_days": s["green_days"], "reg_up": rg["up"].get("exp_r"), "reg_up_n": rg["up"].get("n"),
              "reg_dn": rg["down"].get("exp_r"), "reg_dn_n": rg["down"].get("n"), "reg_pass": rg["pass"],
              "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"],
              "xs_tr": float(t.loc[tr, "x"].mean()) if tr.any() else np.nan,
              "xs_va": float(t.loc[~tr, "x"].mean()) if (~tr).any() else np.nan,
              "plateau_n": len(nb_ok), "plateau_pos": int(sum(nb_ok)),
              "per_day": round(len(t) / 426, 3)})
    o["g_conc"] = bool(s["ex_best_day"] is not None and s["ex_best_day"] > 0 and maxshare <= 0.2)
    o["g_wf_exact"] = wf["share_positive"] is not None and wf["share_positive"] >= 0.6
    o["g_plateau"] = sum(nb_ok) >= 1
    o["g_t_exact"] = (s["t"] or 0) >= row.bar
    o["final"] = bool(o["pos"] and o["g_n"] and rg["pass"] and o["xs_tr"] > 0 and o["xs_va"] > 0 and o["g_wf_exact"]
                      and o["g_conc"] and o["g_plateau"] and o["g_t_exact"])
    o["near_clean"] = bool(o["pos"] and o["g_n"] and rg["pass"] and o["xs_tr"] > 0 and o["xs_va"] > 0 and o["g_wf_exact"]
                           and o["g_conc"] and o["g_plateau"] and not o["g_t_exact"])
    rows.append(o)
V = pd.DataFrame(rows).sort_values("v_t", ascending=False)
V.to_csv(HERE / "verify.csv", index=False, float_format="%.4f")
print("checked", len(V), "final", int(V.final.sum()), "near_clean", int(V.near_clean.sum()))
print("fail counts: conc", int((~V.g_conc).sum()), "wf", int((~V.g_wf_exact).sum()), "plateau", int((~V.g_plateau).sum()),
      "t", int((~V.g_t_exact).sum()))
pd.set_option("display.width", 250)
c = ["fam", "stage", "vid", "side", "exit", "win", "pick", "f1", "f2", "v_n", "v_exp", "exp_tr", "exp_va", "v_t", "bar", "ex_best_day",
     "max_day_share", "reg_up", "reg_dn", "wf_share", "plateau_pos", "per_day"]
print(V[V.near_clean][c].head(40).to_string(index=False))
V[V.final | V.near_clean].to_csv(HERE / "finalists.csv", index=False, float_format="%.4f")
