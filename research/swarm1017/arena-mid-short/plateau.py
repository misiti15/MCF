"""Stage 4 (PLAN.md): threshold neighbourhood of the best live near-misses (every threshold moved to the adjacent
screen quantile edge, one at a time, plus the other two geometries). Every point counts toward N. Uses VALID, so
VALID is no longer clean for these families. Also: concentration (without the best day), month table.
python research/swarm1017/arena-mid-short/plateau.py <scratch rows dir>     Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search as S  # noqa: E402
from common import SCREEN, WIN_SCREEN  # noqa: E402

from mcf.research import gates  # noqa: E402
from mcf.research.arena.combine import combo_mask, trades  # noqa: E402

HERE = Path(__file__).resolve().parent
S.ROWS = Path(sys.argv[1])
NEAR = [
    ([("vwap_atr", ">=", 0.3364), ("or_high_dist_atr", "<=", -0.5399), ("emaDiff", ">=", 0.1422)], "t1s1", (1100, 1230)),
    ([("macdPct", "between", (-np.inf, -0.2973)), ("vwap_atr", ">=", 0.1627), ("day_range_atr", ">=", 0.9828)], "t1s05", (1230, 1400)),
    ([("macdPct", "between", (-np.inf, -0.2973)), ("vwap_atr", ">=", 0.1627), ("prev_range_atr", ">=", 0.8259)], "t1s05", (1230, 1400)),
]


def edges(ind):
    s = pd.read_parquet(SCREEN)
    q = s[(s.window == WIN_SCREEN) & (s.indicator == ind) & (s.side == "short") & (s.geom == "t1s1")]
    v = pd.concat([q.lo, q.hi]).astype(float)
    return np.unique(np.round(v[np.isfinite(v)].to_numpy(), 4))


def summ(t):
    if not len(t):
        return {}
    by = t.groupby("date")["r"].sum()
    best = by.idxmax()
    wo = t[t["date"] != best]
    mo = pd.to_datetime(t["date"]).dt.strftime("%Y-%m")
    return {"exp_wo_best_day": float(wo["r"].mean()), "best_day": str(best), "best_day_share_of_pnl": float(by.max() / t["r"].sum()) if t["r"].sum() > 0 else None,
            "months": t.groupby(mo)["r"].agg(["count", "mean"]).round(3).reset_index().values.tolist()}


def main():
    names = sorted({c[0] for cs, _, _ in NEAR for c in cs})
    cols = ["symbol", "date", "tod"] + [f"{p}_short_{g}" for p in ("r", "c") for g in S.GEOMS] + names
    A = S.load_rows(cols)
    ns = pd.Series(A["date"]).nunique()
    prior = json.load(open(HERE / "counts.json"))["N_lineage"]
    pts = []
    for fam, (cs, g, w) in enumerate(NEAR):
        pts.append((fam, "base", cs, g, w))
        for gg in S.GEOMS:
            if gg != g:
                pts.append((fam, f"geom {gg}", cs, gg, w))
        for i, (nm, op, v) in enumerate(cs):
            e = edges(nm)
            if op == "between":
                lo, hi = e[e < v[1] - 1e-3], e[e > v[1] + 1e-3]
                for nv in ([lo[-1]] if len(lo) else []) + ([hi[0]] if len(hi) else []):
                    c2 = list(cs)
                    c2[i] = (nm, op, (v[0], float(nv)))
                    pts.append((fam, f"{nm} hi -> {nv:.4g}", c2, g, w))
                continue
            lo, hi = e[e < v - 1e-3], e[e > v + 1e-3]
            for nv in ([lo[-1]] if len(lo) else []) + ([hi[0]] if len(hi) else []):
                c2 = list(cs)
                c2[i] = (nm, op, float(nv))
                pts.append((fam, f"{nm} -> {nv:.4g}", c2, g, w))
    N = prior + sum(1 for p in pts if p[1] != "base")
    out = []
    for fam, lab, cs, g, w in pts:
        ev = S.full_eval(A, cs, g, w, N, ns)
        t = trades(A.loc[combo_mask(A, cs, w)], cs, "short", g, w)
        row = {"family": fam, "point": lab, "key": S.key(cs), "geom": g, "window": list(w),
               "n_tr": ev["train"].get("n"), "exp_tr": ev["train"].get("exp_r"), "t_tr": ev["train"].get("t"),
               "n_va": ev["valid"].get("n"), "exp_va": ev["valid"].get("exp_r"), "t_va": ev["valid"].get("t"),
               "ex_tr": ev["train"].get("excess"), "ex_va": ev["valid"].get("excess"),
               "up": ev["regime"]["up"].get("exp_r"), "down": ev["regime"]["down"].get("exp_r"),
               "wf": ev["walk_forward"]["share_positive"], "per_day": ev["per_day"],
               "fails": [k for k, v in ev["gates"].items() if not v], **summ(t)}
        out.append(row)
        print(fam, lab, row["n_tr"], round(row["exp_tr"] or 0, 3), round(row["exp_va"] or 0, 3), row["up"], row["down"], row["wf"], row["fails"], flush=True)
    json.dump({"N_lineage_after": N, "bar": gates.t_required(N), "points": out}, open(HERE / "plateau.json", "w"), indent=1, default=str)
    print("N", N, "bar", gates.t_required(N))


if __name__ == "__main__":
    main()
