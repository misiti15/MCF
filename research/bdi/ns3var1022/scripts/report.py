"""ns3var1022: render the variant and diagnosis tables (markdown) used by NOTES.md -> tables_out.md.
Educational only - not financial advice."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from nv import HERE

REG = ["Bull", "Bear", "Choppy", "Quiet"]


def f(x, d=3, sign=True):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "–"
    return (f"{x:+.{d}f}" if sign else f"{x:.{d}f}")


def vtable(v: pd.DataFrame) -> str:
    h = ("| variant | what | trades (train / valid) | kept % | avg R train / valid | total R train / valid | t (2y) | "
         "Bull / Bear / Choppy / Quiet avg R (2y) | vs random entries (train / valid) | vs random thinning (train / valid) | "
         "diff-t vs P0 | worst day | best-day share | edit tests failed | merit |\n|" + "---|" * 15 + "\n")
    out = []
    for _, r in v.iterrows():
        merit = "TESTING BAR" if r["testing_bar"] else ("near-miss" if r["near_miss_merit"] else "no")
        out.append(
            f"| {r['variant']} | {r['desc']} | {int(r['train_n'])} / {int(r['valid_n'])} | "
            f"{100 * r['train_kept']:.0f} / {100 * r['valid_kept']:.0f} | {f(r['train_avg'])} / {f(r['valid_avg'])} | "
            f"{f(r['train_tot'], 0)} / {f(r['valid_tot'], 0)} | {f(r['all_t'], 2)} | "
            + " / ".join(f(r[f'all_{g}_avg']) for g in REG)
            + f" | {f(r['train_excess'])} / {f(r['valid_excess'])} | {f(r['train_vs_thin'], 0)} / {f(r['valid_vs_thin'], 0)} | "
            f"{f(r['all_diff_t'], 2)} | {f(r['worst_day'], 1)} | {f(r['best_day_share'], 2, False)} | "
            f"{r['edit_fails'] if isinstance(r['edit_fails'], str) and r['edit_fails'] else ('none' if r['variant'] != 'P0' else '–')} | {merit} |")
    return h + "\n".join(out) + "\n"


def dtable(d: pd.DataFrame, fam: str, scope="all days") -> str:
    x = d[(d["family"] == fam) & (d["scope"] == scope)]
    piv = {}
    for _, r in x.iterrows():
        piv.setdefault(r["bucket"], {})[r["split"]] = r
    h = (f"| {fam} | n (2y) | share | avg R train | avg R valid | avg R 2y | total R 2y | t 2y | random same-minute 2y | "
         "excess 2y |\n|---|---|---|---|---|---|---|---|---|---|\n")
    out = []
    for b, s in piv.items():
        a = s.get("2y")
        if a is None:
            continue
        tr, va = s.get("train"), s.get("valid")
        out.append(f"| {b} | {int(a['n'])} | {a['share']:.2f} | {f(tr['avg_r'] if tr is not None else None)} | "
                   f"{f(va['avg_r'] if va is not None else None)} | {f(a['avg_r'])} | {f(a['tot_r'], 0)} | "
                   f"{f(a['t'], 2)} | {f(a['ctrl_avg'])} | {f(a['excess'])} |")
    return h + "\n".join(out) + "\n"


def main():
    v = pd.concat([pd.read_csv(HERE / "variants.csv"), pd.read_csv(HERE / "explore.csv"),
                   pd.read_csv(HERE / "plateau.csv")], ignore_index=True)
    d = pd.read_csv(HERE / "diag.csv")
    c = json.load(open(HERE / "counts.json"))
    parts = [f"counts: {json.dumps(c)}\n"]
    for fam in ["P", "A", "B", "C", "D", "E", "F", "X", "PL"]:
        parts.append(f"\n### family {fam}\n\n" + vtable(v[v["fam"] == fam]))
    for fam in d["family"].unique():
        parts.append(f"\n#### {fam}\n\n" + dtable(d, fam))
    for fam in ("time of day", "entry #k of the day (symbol)", "SPY vs its VWAP at entry", "RS vs SPY (fromOpen - SPY fromOpen)",
                "reclaim size (% above VWAP)", "bars below VWAP before"):
        parts.append(f"\n#### Bull+Choppy days only: {fam}\n\n" + dtable(d, fam, "Bull+Choppy days"))
    (HERE / "tables_out.md").write_text("".join(parts))


if __name__ == "__main__":
    main()
