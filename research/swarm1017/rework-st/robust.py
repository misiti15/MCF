"""Robustness checks on the de-duplicated finalists (finalists.csv), added after the gate run (NOTES.md amendment;
they only remove candidates): (1) core-tier only (adv20 >= 5M; L3 runs at min_adv 0 and the frames' cost model has no
extended-tier 3x slippage), (2) threshold-neighbour plateau with the same filters/side/geom/window/refire, (3) the same
configuration without a day-of-week filter, (4) per half-year expectancy. Every extra configuration is counted.
Educational only - not financial advice."""
import ast
import json

import numpy as np
import pandas as pd

from common import F, HERE, S, TRAIN, WM, col, core, dcode, dstat, neighbours, trades
from scan import pick_idx
from mcf.research import gates

FN = pd.read_csv(HERE / "finalists.csv")
ADV = col["adv20"]
DATES = pd.to_datetime(S["date"]).to_numpy()
DOWF = {"Mon", "Tue", "Wed", "Thu", "Fri", "notMon", "notFri"}
extra = 0


def run(p, th, filters, side, geom, win, refire, adv_min=0.0):
    global extra
    extra += 1
    m = core(p, th) & WM[win] & (ADV >= adv_min)
    for f in filters:
        m = m & F[f]
    return pick_idx(np.flatnonzero(m), side, geom, refire)


def ev(idx, s, g):
    r = col[f"p_{s}_{g}"][idx].astype(float)
    tr = TRAIN[idx]
    a = dstat(r, dcode[idx])
    return {"n": a[0], "exp": a[1], "t": a[2], "exp_tr": float(r[tr].mean()) if tr.any() else None,
            "exp_va": float(r[~tr].mean()) if (~tr).any() else None, "n_tr": int(tr.sum()), "n_va": int((~tr).sum())}


out = []
for i, r in FN.iterrows():
    th = ast.literal_eval(r.th)
    fl = r.filters.split("+") if isinstance(r.filters, str) and r.filters else []
    rf = bool(r.refire)
    rec = {"rank": i, "parent": r.parent, "stage": r.stage, "th": r.th, "filters": "+".join(fl), "side": r.side,
           "geom": r.geom, "win": r.win, "refire": rf, "t_gate": r.t_gate}
    idx = run(r.parent, th, fl, r.side, r.geom, r.win, rf)
    base = ev(idx, r.side, r.geom)
    rec["base"] = base
    core_t = ev(run(r.parent, th, fl, r.side, r.geom, r.win, rf, 5e6), r.side, r.geom)
    rec["core_tier"] = core_t
    rec["g_tier"] = bool(core_t["n"] >= 200 and (core_t["exp_tr"] or -1) > 0 and (core_t["exp_va"] or -1) > 0)
    nb = []
    for t in neighbours(r.parent, th):
        e = ev(run(r.parent, t, fl, r.side, r.geom, r.win, rf), r.side, r.geom)
        nb.append({"th": repr(t), **e})
    okn = [(x["exp_tr"] or -1) > 0 and (x["exp_va"] or -1) > 0 for x in nb]
    rec["neighbours"] = nb
    rec["plateau_share"] = round(sum(okn) / len(okn), 3) if okn else None
    rec["g_plateau"] = rec["plateau_share"] is not None and rec["plateau_share"] >= 2 / 3
    dw = [f for f in fl if f in DOWF]
    if dw:
        rest = [f for f in fl if f not in DOWF]
        rec["no_dow"] = ev(run(r.parent, th, rest, r.side, r.geom, r.win, rf), r.side, r.geom)
    tr = trades(idx, r.side, r.geom)
    d = pd.to_datetime(tr.date)
    half = np.where(d < "2025-07-01", "25H1", np.where(d < "2026-01-01", "25H2", np.where(d < "2026-07-01", "26H1", "26H2")))
    rec["halves"] = {h: [int((half == h).sum()), round(float(tr.r[half == h].mean()), 4) if (half == h).any() else None]
                     for h in ("25H1", "25H2", "26H1", "26H2")}
    rec["halves_pos"] = sum(1 for v in rec["halves"].values() if v[1] is not None and v[1] > 0)
    rec["module"] = bool(rec["g_tier"] and rec["g_plateau"] and (r.t_gate or 0) >= 2.0)
    out.append(rec)
    print(i, r.parent, r.stage, r.filters, r.side, r.geom, r.win, rf, "t", r.t_gate, "| tier", core_t["n"],
          round(core_t["exp_tr"] or 0, 3), round(core_t["exp_va"] or 0, 3), "| plateau", rec["plateau_share"],
          "| halves", rec["halves"], "| noDOW", {k: round(v, 3) if isinstance(v, float) else v for k, v in rec.get("no_dow", {}).items()},
          "| MODULE" if rec["module"] else "", flush=True)
json.dump({"extra_configs": extra, "finalists": out}, open(HERE / "robust.json", "w"), indent=1, default=float)
print("extra configs", extra, "modules", sum(o["module"] for o in out))
