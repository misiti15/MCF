"""Concentration checks (NOTES amendment B, stricter only): day-equal-weighted expectancy and t (each session counts
once), ex-top-3-days expectancy, share of total R from the top 3 days, and a 10-trades-per-day cap (earliest bars first).
Applied to every de-duplicated finalist. Educational only - not financial advice."""
import ast
import json

import numpy as np
import pandas as pd

from common import F, HERE, S, TRAIN, WM, col, core, tod
from scan import pick_idx

FN = pd.read_csv(HERE / "finalists.csv")
rb = {o["rank"]: o for o in json.load(open(HERE / "robust.json"))["finalists"]}


def conc(idx, s, g):
    t = pd.DataFrame({"date": S["date"].to_numpy()[idx], "tod": tod[idx], "r": col[f"p_{s}_{g}"][idx].astype(float),
                      "tr": TRAIN[idx]})
    out = {}
    for lab, sub in (("all", t), ("tr", t[t.tr]), ("va", t[~t.tr])):
        dm = sub.groupby("date").r.mean()
        out[f"dew_{lab}"] = round(float(dm.mean()), 4) if len(dm) else None
        out[f"dew_t_{lab}"] = round(float(dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm)))), 2) if len(dm) > 2 else None
        out[f"days_{lab}"] = int(len(dm))
    ds = t.groupby("date").r.sum().sort_values(ascending=False)
    top3 = set(ds.index[:3])
    out["top3_share"] = round(float(ds.iloc[:3].sum() / ds.sum()), 3) if ds.sum() > 0 else None
    out["ex_top3_exp"] = round(float(t[~t.date.isin(top3)].r.mean()), 4)
    cap = t.sort_values(["date", "tod"]).groupby("date").head(10)
    out["cap10_n"] = int(len(cap))
    out["cap10_exp_tr"] = round(float(cap[cap.tr].r.mean()), 4)
    out["cap10_exp_va"] = round(float(cap[~cap.tr].r.mean()), 4)
    out["max_day_n"] = int(t.groupby("date").size().max())
    return out


res = []
for i, r in FN.iterrows():
    th = ast.literal_eval(r.th)
    fl = r.filters.split("+") if isinstance(r.filters, str) and r.filters else []
    m = core(r.parent, th) & WM[r.win]
    for f in fl:
        m = m & F[f]
    idx = pick_idx(np.flatnonzero(m), r.side, r.geom, bool(r.refire))
    c = conc(idx, r.side, r.geom)
    c["g_conc"] = bool((c["dew_tr"] or -1) > 0 and (c["dew_va"] or -1) > 0 and c["ex_top3_exp"] > 0
                       and c["cap10_exp_tr"] > 0 and c["cap10_exp_va"] > 0)
    c["module"] = bool(rb[i]["module"] and c["g_conc"])
    res.append({"rank": i, "parent": r.parent, "filters": "+".join(fl), "side": r.side, "geom": r.geom, "win": r.win,
                "refire": bool(r.refire), **c})
    print(res[-1], flush=True)
json.dump(res, open(HERE / "concentration.json", "w"), indent=1)
