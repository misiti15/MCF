"""Render the result tables for NOTES.md from results.csv. Educational only - not financial advice."""
import numpy as np
import pandas as pd


def md(df, index=True):
    d = df.reset_index() if index else df
    d = d.copy()
    for k in d.columns:
        if d[k].dtype.kind == "f":
            d[k] = d[k].map(lambda v: "" if pd.isna(v) else f"{v:.3f}")
    cols = [str(c) for c in d.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in d.to_numpy()]
    return "\n".join(out)


r = pd.read_csv("results.csv")
C = ["family", "trigger", "side", "filters", "window", "geom", "tr_n", "tr_exp", "tr_t", "tr_h1", "tr_h2", "va_n", "va_exp",
     "va_t", "va_exbest", "tr_edge", "va_edge"]
parts = []
fam_rows = []
for fam in ["F", "C", "L1", "L2"]:
    x = r[r.family == fam]
    fam_rows.append({"family": fam, "scored": len(x), "train>0": int((x.tr_exp > 0).sum()), "valid>0": int((x.va_exp > 0).sum()),
                     "both>0": int(((x.tr_exp > 0) & (x.va_exp > 0)).sum()),
                     "edge>0 both": int(((x.tr_edge > 0) & (x.va_edge > 0)).sum()),
                     "best tr_exp": x.tr_exp.max(), "best va_exp": x.va_exp.max()})
parts.append("### Per family\n" + md(pd.DataFrame(fam_rows), index=False))
for fam, title in (("F", "Faithful (article side), window 09:50-15:00"), ("C", "Contrarian (opposite side), window 09:50-15:00")):
    f = r[(r.family == fam) & (r.window == "all")]
    p = f.pivot_table(index=["trigger", "side"], columns="geom", values=["tr_exp", "va_exp"])
    p.columns = [f"{a}_{b}" for a, b in p.columns]
    p = p.join(f.groupby(["trigger", "side"])[["tr_n", "va_n"]].first())
    parts.append(f"### {title}: expectancy (R/trade after haircut) by geometry\n" + md(p))
parts.append("### Every configuration positive on train (all " + str(int((r.tr_exp > 0).sum())) + ")\n"
             + md(r[r.tr_exp > 0].sort_values("tr_t", ascending=False)[C], index=False))
parts.append("### Top 15 positive on valid (by valid day-t)\n"
             + md(r[r.va_exp > 0].sort_values("va_t", ascending=False)[C].head(15), index=False))
e = r[(r.tr_edge > 0) & (r.va_edge > 0) & (r.va_n >= 30)].copy()
e["s"] = np.minimum(e.tr_edge, e.va_edge)
parts.append(f"### Largest edge over the random same-window baseline on both splits (top 15 of {len(e)}), absolute expectancy still negative\n"
             + md(e.sort_values("s", ascending=False)[C].head(15), index=False))
b = r.groupby(["side", "geom"])[["tr_base", "va_base"]].first()
parts.append("### Random baselines (window 09:50-15:00 shown in this table; each config is compared with its own window)\n"
             + md(r[r.window == "all"].groupby(["side", "geom"])[["tr_base", "va_base"]].first()))
pass  # tables are pasted into NOTES.md
print("\n\n".join(parts))
