"""Build metric_map.json, METRIC_MAP.md and one deployable module per finalist from results.csv.
Run from the repo root after scan.py:  python research/primitives/primitives/report.py
Educational only - not financial advice."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MODDIR = HERE.parent                        # research/primitives/<tag>.py (deployable, 'type: lab')
WIN = {"W1": (950, 1030), "W2": (1030, 1130), "W3": (1130, 1300), "W4": (1300, 1430), "W5": (1430, 1501)}
WLABEL = {"W1": "09:50-10:30", "W2": "10:30-11:30", "W3": "11:30-13:00", "W4": "13:00-14:30", "W5": "14:30-15:00"}
DERIVED = {"flowFlip": ("flow3 - flow9prev", "df['flow3'].to_numpy(dtype=float) - df['flow9prev'].to_numpy(dtype=float)"),
           "dayRangePos": ("dist_lod_atr / (dist_hod_atr + dist_lod_atr)",
                           "_rangepos(df)")}


def tag_of(r) -> str:
    band = r.band.replace("==", "eq").replace("-", "m")
    return f"P1-{r.metric}_{band}-{r.side}-{r.window}-{r.geom}"


def fnum(x):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else float(x)


def band_text(m, lo, hi):
    if lo == hi:
        return f"{m} == {lo:g}"
    if not math.isfinite(lo):
        return f"{m} <= {hi:.6g}"
    if not math.isfinite(hi):
        return f"{m} > {lo:.6g}"
    return f"{lo:.6g} < {m} <= {hi:.6g}"


def write_module(r) -> Path:
    tag = tag_of(r)
    a, b = WIN[r.window]
    lo, hi = float(r.lo), float(r.hi)
    if r.metric in DERIVED:
        desc, expr = DERIVED[r.metric]
        mdesc = f"{r.metric} = {desc}"
    else:
        expr, mdesc = f"df['{r.metric}'].to_numpy(dtype=float)", r.metric
    if lo == hi:
        cond = f"(x == {lo!r})"
    elif not math.isfinite(lo):
        cond = f"(x <= {hi!r})"
    elif not math.isfinite(hi):
        cond = f"(x > {lo!r})"
    else:
        cond = f"(x > {lo!r}) & (x <= {hi!r})"
    src = f'''"""{tag} - Layer-1 primitive (single metric) from research/primitives/primitives/scan.py.
{band_text(r.metric, lo, hi)}  [{r.band} band at train quantiles], {WLABEL[r.window]} ET, {r.side}, exit {r.geom}.
Train exp_r {r.exp_r_tr:+.4f}R (n {int(r.n_tr)}), valid exp_r {r.exp_r_va:+.4f}R (n {int(r.n_va)}, day-clustered t {r.t_va:.2f}).
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "{r.side}"
GEOM = "{r.geom}"
LAYERS = [
    "{band_text(mdesc if r.metric in DERIVED else r.metric, lo, hi)} ({r.band} band of {r.metric} at train quantiles)",
    "time window {WLABEL[r.window]} ET (bar close tod {a} <= tod < {b})",
]


def _rangepos(df):
    h = df["dist_hod_atr"].to_numpy(dtype=float)
    lo = df["dist_lod_atr"].to_numpy(dtype=float)
    s = h + lo
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(s > 0, lo / s, np.nan)


def mask(df) -> np.ndarray:
    x = {expr}
    tod = df["tod"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return {cond} & (tod >= {a}) & (tod < {b})
'''
    p = MODDIR / f"{tag}.py"
    p.write_text(src)
    return p


def main():
    w = pd.read_csv(HERE / "results.csv")
    meta = json.load(open(HERE / "scan_meta.json"))
    n_cfg = len(w)
    # ------------------------------------------------------------------ metric_map.json (every config)
    keep = ["band", "lo", "hi", "geom", "n_tr", "exp_r_tr", "edge_tr", "t_tr", "n_va", "exp_r_va", "exp_r_prod_va",
            "edge_va", "t_va", "t_edge_va", "ex_best_day_va", "green_days_va", "plateau_tr", "plateau_va",
            "survivor", "finalist"]
    mm = {}
    for (m, win, side), g in w.groupby(["metric", "window", "side"]):
        pick = g[g.n_tr >= 100].sort_values("edge_tr", ascending=False).head(1)
        recs = [{k: (fnum(v) if isinstance(v, float) else (bool(v) if isinstance(v, (bool, np.bool_)) else v))
                 for k, v in zip(keep, row)} for row in g[keep].itertuples(index=False)]
        mm.setdefault(m, {}).setdefault(win, {})[side] = {
            "best_on_train": recs[g[keep].index.get_loc(pick.index[0])] if len(pick) else None,
            "n_survivors": int(g.survivor.sum()), "n_finalists": int(g.finalist.sum()), "configs": recs}
    out = {"key": "primitives", "educational_only": "Educational only - not financial advice.",
           "configs_tried": n_cfg, "windows": WLABEL, "bands": meta["bands"],
           "baseline_train": meta["baseline_train"], "baseline_valid": meta["baseline_valid"],
           "gate": "train exp_r>0, valid exp_r>0, edge vs same-side same-window random baseline >0 on train and valid, "
                   "valid n>=30, valid day-clustered t>=1.5, plateau (one-step neighbour bands) mean exp_r>0 on train and valid",
           "survivor_rule": "train exp_r>0, valid exp_r>0, edge>0 on train and valid, valid n>=30",
           "map": mm}
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        if isinstance(o, float) and not math.isfinite(o):
            return None if math.isnan(o) else ("inf" if o > 0 else "-inf")
        return o

    json.dump(clean(out), open(HERE / "metric_map.json", "w"), indent=0, default=float, allow_nan=False)

    # ------------------------------------------------------------------ METRIC_MAP.md
    L = ["# Layer-1 metric map (key: primitives)", "", "*Educational only - not financial advice.*", "",
         f"Configurations tried: **{n_cfg:,}** (metric x band x window x side x geometry). Train = to 2026-08-25 (40 sessions), "
         "valid = 2026-08-26..09-15 (14 sessions). Lab costs (flat 1c/side); `prod` adds 1 bps/side and +2c on stops "
         "(extended-tier 3c not identifiable in the frame, so prod is still slightly optimistic for those names).", "",
         "Edge = exp_r minus the same-side same-window random baseline (mean R of every bar in the window). "
         "t = day-clustered t of exp_r.", "",
         "## Same-window random baselines (t1s1, R per trade)", "",
         "| window | long train | long valid | short train | short valid |", "|---|---|---|---|---|"]
    bt, bv = meta["baseline_train"], meta["baseline_valid"]
    for k, lab in WLABEL.items():
        L.append(f"| {lab} | {bt[f'{k}|r_long_t1s1']['random']:+.3f} | {bv[f'{k}|r_long_t1s1']['random']:+.3f} | "
                 f"{bt[f'{k}|r_short_t1s1']['random']:+.3f} | {bv[f'{k}|r_short_t1s1']['random']:+.3f} |")
    L += ["", "Valid was a weak tape for longs (long baseline about -0.1R/trade in every window), so raw-exp_r gates favour shorts. "
          "The edge column removes that drift.", "",
          "## Map: best band per cell picked on TRAIN edge, shown as valid edge (valid t) [survivors in cell]", "",
          "Cell = `band/geom: valid edge (t)`. A cell picked on train and still positive on valid is the honest read.", "",
          "| metric | " + " | ".join(f"{WLABEL[k]} {s}" for k in WLABEL for s in ("L", "S")) + " |",
          "|---|" + "---|" * 10]
    for m in sorted(mm):
        cells = []
        for k in WLABEL:
            for s in ("long", "short"):
                c = mm[m][k][s]
                b = c["best_on_train"]
                if not b or b["exp_r_va"] is None:
                    cells.append("-")
                    continue
                star = "**" if c["n_finalists"] else ""
                cells.append(f"{star}{b['band']}/{b['geom']}: {b['edge_va']:+.3f} ({b['t_va']:+.1f}) [{c['n_survivors']}]{star}")
        L.append(f"| {m} | " + " | ".join(cells) + " |")
    cols = ["tag", "rule", "n_tr", "exp_r_tr", "edge_tr", "t_tr", "n_va", "exp_r_va", "exp_r_prod_va", "edge_va",
            "t_va", "ex_best_day_va", "green_days_va", "plateau_tr", "plateau_va"]

    def table(df):
        rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for r in df.itertuples(index=False):
            d = r._asdict()
            d["tag"] = tag_of(r)
            d["rule"] = band_text(r.metric, float(r.lo), float(r.hi))
            rows.append("| " + " | ".join(f"{d[c]:+.4f}" if isinstance(d[c], float) and c not in ("t_tr", "t_va", "green_days_va")
                                          else (f"{d[c]:.2f}" if isinstance(d[c], float) else str(d[c])) for c in cols) + " |")
        return rows

    fin = w[w.finalist].sort_values("t_va", ascending=False)
    sur = w[w.survivor].sort_values("t_va", ascending=False)
    L += ["", f"## Finalists ({len(fin)}) - full gate", ""] + table(fin)
    L += ["", f"## All survivors ({len(sur)}) - cleared train AND valid (exp_r>0, edge>0, valid n>=30)", ""] + table(sur)
    (HERE / "METRIC_MAP.md").write_text("\n".join(L) + "\n")

    paths = [write_module(r) for r in fin.itertuples(index=False)]
    print("finalists", len(fin), "survivors", len(sur), "modules", len(paths))


if __name__ == "__main__":
    main()
