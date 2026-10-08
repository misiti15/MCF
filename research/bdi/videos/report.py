"""Render the scan into markdown tables (printed) and pick the finalists (finalists.json, results.csv).
Usage: python research/bdi/videos/report.py > research/bdi/videos/data/report.md   Educational only - not financial advice."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import scan  # noqa: E402

R = pd.read_parquet(HERE / "data" / "all_results.parquet")
P = pd.read_csv(HERE / "passers.csv") if (HERE / "passers.csv").exists() and (HERE / "passers.csv").stat().st_size > 1 else pd.DataFrame()
counts = json.load(open(HERE / "counts.json"))
COLS = ["fam", "var", "side", "exit", "layers", "window", "tr_n", "tr_exp", "tr_t", "tr_h1", "tr_h2", "va_n", "va_exp", "va_t",
        "va_exbest", "tr_edge", "va_edge"]


def md(df, cols=COLS, nd=3):
    if df is None or len(df) == 0:
        return "(none)\n"
    d = df[cols].copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda x: f"{x:.{nd}f}" if pd.notna(x) else "")
    s = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    for _, r in d.iterrows():
        s += "| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |\n"
    return s


g = {
    "train exp > 0": R.tr_exp > 0, "valid exp > 0": R.va_exp > 0, "valid n >= 30": R.va_n >= 30, "valid day-t >= 1.5": R.va_t >= 1.5,
    "train half 1 > 0": R.tr_h1 > 0, "train half 2 > 0": R.tr_h2 > 0, "edge > 0 train": R.tr_edge > 0, "edge > 0 valid": R.va_edge > 0,
}
print("## Counts\n")
print(json.dumps(counts, indent=1), "\n")
print("## Gate funnel (scored configurations)\n")
print("| gate | alone | cumulative |\n|---|---|---|")
cum = np.ones(len(R), bool)
for k, m in g.items():
    cum &= m.to_numpy()
    print(f"| {k} | {int(m.sum())} | {int(cum.sum())} |")
print(f"| plateau positive | - | {int(P.plateau_ok.sum()) if len(P) else 0} |\n")

print("## Per family\n")
both = (R.tr_exp > 0) & (R.va_exp > 0) & (R.va_n >= 30)
fam = R.assign(both=both, trp=R.tr_exp > 0, vap=R.va_exp > 0, pre=scan.gates_pre(R)).groupby("fam").agg(
    scored=("tr_n", "size"), train_pos=("trp", "sum"), valid_pos=("vap", "sum"), both_pos_n30=("both", "sum"),
    pre_plateau=("pre", "sum"), best_tr=("tr_exp", "max"), best_va=("va_exp", "max"))
if len(P):
    fam["final"] = P[P.plateau_ok].groupby("fam").size()
fam = fam.fillna(0).reset_index()
print(md(fam, list(fam.columns)))

print("## Faithful (no layers, 09:50-15:00): mean over the family's variants, and the best variant by train\n")
L0 = R[(R.nlay == 0) & (R.window == "all")]
rows = []
for (f, sd, ex), d in L0.groupby(["fam", "side", "exit"]):
    b = d.sort_values("tr_exp").iloc[-1]
    rows.append({"fam": f, "side": sd, "exit": ex, "variants": len(d), "mean_tr": d.tr_exp.mean(), "mean_va": d.va_exp.mean(),
                 "best_var": b["var"], "best_tr": b.tr_exp, "best_va": b.va_exp, "best_tr_n": b.tr_n, "best_va_n": b.va_n,
                 "tr_base": b.tr_base, "va_base": b.va_base})
F = pd.DataFrame(rows)
print(md(F, list(F.columns)))

print("## Every configuration positive on both splits with valid n >= 30, top 40 by min(train t, valid t)\n")
B = R[both].copy()
B["score"] = np.minimum(B.tr_t, B.va_t)
print(f"{len(B)} configurations\n")
print(md(B.sort_values("score", ascending=False).head(40)))

print("## Pre-plateau passers (all other gates met)\n")
if len(P):
    P["score"] = np.minimum(P.tr_t, P.va_t)
    print(md(P.sort_values("score", ascending=False), COLS + ["plateau_ok"]))
else:
    print("(none)\n")

# near misses: fail exactly one of the non-plateau gates
gm = pd.DataFrame(g)
fails = (~gm).sum(axis=1)
nm = R[(fails == 1) & (R.va_n >= 30)].copy()
nm["failed"] = (~gm[(fails == 1) & (R.va_n >= 30)]).idxmax(axis=1)
nm["score"] = np.minimum(nm.tr_t, nm.va_t)
print("## Near misses (exactly one gate failed, valid n >= 30), top 25 by min(train t, valid t)\n")
print(f"{len(nm)} configurations; by failed gate: {nm.failed.value_counts().to_dict()}\n")
print(md(nm.sort_values("score", ascending=False).head(25), COLS + ["failed"]))

print("## Baselines (09:50-15:00, every bar, same exit)\n")
bl = R[R.window == "all"].groupby(["side", "exit"])[["tr_base", "va_base"]].first().reset_index()
print(md(bl, list(bl.columns)))

# finalists: plateau-positive passers, duplicates (identical trade sets) collapsed, max 8 by min(t)
fin = []
if len(P) and P.plateau_ok.any():
    sc = scan.S(scan.frame())
    seen = set()
    for _, r in P[P.plateau_ok].sort_values("score", ascending=False).iterrows():
        v = json.loads(r["var"])
        s = 1 if r.side == "long" else -1
        combo = tuple(x for x in r.layers.split("+") if x != "-")
        m = np.asarray(scan.trig(sc.D, r.fam, s, v, dict(scan.BASE[r.fam]), r.exit), bool) & sc.W[r.window]
        for nm_ in combo:
            m &= np.asarray(scan.layer(sc.D, nm_, s), bool)
        rr = sc.outcome(s, r.exit, v, r.fam, dict(scan.BASE[r.fam]))
        i = np.flatnonzero(m & np.isfinite(rr))
        keep = np.r_[True, sc.sid[i][1:] != sc.sid[i][:-1]] if len(i) else np.zeros(0, bool)
        h = hashlib.md5(i[keep].tobytes() + r.exit.encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        fin.append({k: (r[k].item() if hasattr(r[k], "item") else r[k]) for k in COLS})
        if len(fin) >= 8:
            break
json.dump(fin, open(HERE / "finalists.json", "w"), indent=1)
print("## Finalists\n")
print(md(pd.DataFrame(fin)) if fin else "(none)\n")

# results.csv: L0 + every config positive on both splits with valid n >= 30 (+ passers), under 5 MB
out = pd.concat([R[R.nlay == 0], B.drop(columns="score")]).drop_duplicates(["fam", "var", "side", "exit", "layers", "window"])
out.to_csv(HERE / "results.csv", index=False, float_format="%.4f")
print(f"\nresults.csv rows {len(out)}, {(HERE / 'results.csv').stat().st_size / 1e6:.2f} MB")
