"""Stage 4 (pre-declared in PLAN.md, counted): plateau / neighbourhood of the best near-misses. Per base config:
each threshold moved to the 2 neighbouring screen bin edges (1400-1530 deciles + tails) one at a time, each other
geometry, each other window, each condition dropped in turn. Scored with combine.evaluate_combo (N = lineage incl. these)
plus best-day-removed stats (rule 5). VALID is no longer clean for these. Educational only - not financial advice.
python research/swarm1017/arena-pm-both/plateau.py <rows dir>"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search as S  # noqa: E402
from common import GEOMS, SCREEN, WINDOWS  # noqa: E402

from mcf.research import gates  # noqa: E402
from mcf.research.arena.combine import evaluate_combo, trades  # noqa: E402

S.ROWS = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
BASES = [
    ("A-long-belowvwap-orh-lowpos", "long", "t1s1", (1400, 1530),
     [("vwapDistPct", "<=", -1.3328), ("or_high_dist_atr", ">=", -0.1904), ("day_pos", "<=", 0.1957)]),
    ("B-short-gapdn-belowpdh-rvol", "short", "t1s1", (1400, 1530),
     [("gap_atr", "<=", -0.6141), ("dist_pdh_atr", "<=", -0.1494), ("rvol_day", ">=", 0.8386)]),
    ("C-short-dnpc-abovepdl-sma50", "short", "t1s1", (1400, 1530),
     [("from_pc", "<=", -2.3198), ("dist_pdl_atr", ">=", 1.0546), ("sma50_dist_pct", ">=", 0.0205)]),
]
sc = pd.read_parquet(SCREEN)
sc = sc[sc.window == "1400-1530"]


def edges(ind):
    q = sc[sc.indicator == ind]
    e = np.unique(np.r_[q.lo.to_numpy(float), q.hi.to_numpy(float)])
    return e[np.isfinite(e)]


def neighbours(v, ind):
    e = edges(ind)
    lo = e[e < v - 1e-6]
    hi = e[e > v + 1e-6]
    return ([float(lo[-1])] if len(lo) else []) + ([float(hi[0])] if len(hi) else [])


names = sorted({c[0] for b in BASES for c in b[4]})
cols = ["symbol", "date", "tod"] + [f"{p}_{sd}_{g}" for p in ("r", "c") for sd in ("long", "short") for g in GEOMS] + names
A = S.load_rows(cols)
variants = []
for nm, side, geom, w, cs in BASES:
    variants.append((nm, "base", side, geom, w, cs))
    for i, (ind, op, v) in enumerate(cs):
        for nv in neighbours(v, ind):
            variants.append((nm, f"{ind} {v:+.4g}->{nv:+.4g}", side, geom, w, cs[:i] + [(ind, op, nv)] + cs[i + 1:]))
        variants.append((nm, f"drop {ind}", side, geom, w, cs[:i] + cs[i + 1:]))
    for g in GEOMS:
        if g != geom:
            variants.append((nm, f"geom {g}", side, g, w, cs))
    for ww in WINDOWS:
        if ww != w:
            variants.append((nm, f"window {ww}", side, geom, ww, cs))
N = json.load(open(HERE / "counts.json"))["N_lineage"] + len(variants) - len(BASES)   # bases already counted
out = []
for nm, var, side, geom, w, cs in variants:
    ev = evaluate_combo(A, cs, side, geom, w, n_lineage=N, regimes=S.LIBREG)
    t = trades(A, cs, side, geom, w)
    d = t.groupby("date")["r"].sum()
    tb = t[t.date != d.idxmax()] if len(d) else t
    xb = {sp: gates.summary(tb[tb.split == sp][["date", "r"]]) for sp in ("train", "valid")}
    rb = gates.regime_split(tb[["date", "r"]], S.LIBREG)
    out.append({"base": nm, "variant": var, "side": side, "geom": geom, "window": f"{w[0]}-{w[1]}",
                "conds": json.dumps([list(c) for c in cs]), "quality_pass": ev["quality_pass"],
                "fails": ",".join(k for k, v in ev["gates"].items() if not v),
                "n": ev["all"].get("n"), "per_day": ev["per_day"],
                "tr_n": ev["train"].get("n"), "tr_exp": ev["train"].get("exp_r"), "tr_t": ev["train"].get("t"),
                "va_n": ev["valid"].get("n"), "va_exp": ev["valid"].get("exp_r"), "va_t": ev["valid"].get("t"),
                "va_excess": ev["valid"].get("excess"), "up": ev["regime"].get("up", {}).get("exp_r"),
                "down": ev["regime"].get("down", {}).get("exp_r"), "wf": ev["walk_forward"]["share_positive"],
                "best_day": str(d.idxmax()) if len(d) else None,
                "best_day_share": float(d.max() / t.r.sum()) if len(d) and t.r.sum() > 0 else None,
                "xb_tr_exp": xb["train"].get("exp_r"), "xb_tr_t": xb["train"].get("t"),
                "xb_va_exp": xb["valid"].get("exp_r"), "xb_va_t": xb["valid"].get("t"),
                "xb_up": rb.get("up", {}).get("exp_r"), "xb_down": rb.get("down", {}).get("exp_r")})
    print(nm, var, round(out[-1]["tr_exp"] or 0, 3), round(out[-1]["va_exp"] or 0, 3), flush=True)
P = pd.DataFrame(out)
P.to_csv(HERE / "plateau.csv", index=False, float_format="%.4g")
json.dump({"plateau_configs_new": len(variants) - len(BASES), "N_lineage_final": int(N), "bar_final": gates.t_required(N)},
          open(HERE / "plateau_counts.json", "w"), indent=1)
