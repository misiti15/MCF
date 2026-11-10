"""Markdown tables for RESULTS.md from priority.csv. Educational only - not financial advice."""
import sys
import pandas as pd, numpy as np
P = pd.read_csv("priority.csv").rename(columns=lambda c: c.replace(".", "_"))
def f(x, n=3):
    return "" if pd.isna(x) else f"{x:+.{n}f}"
def short(s): return s if len(s) <= 42 else s[:39] + "..."
def tab(df):
    out = ["| P | setup | lab n tr/va | lab R tr / va (k=1) | best k TRAIN | VALID d (t) | stop eff. VALID | plateau | verdict | live n (sess) | live R / w/o best day | live best k | live d k0.75 / k1.25 / k1.5 | lab vs live |",
           "|" + "---|" * 14]
    for r in df.to_dict("records"):
        cov = not pd.isna(r["n_train"]); ch = cov and not pd.isna(r["best_tr"]) and r["best_tr"] != 1.0
        lab = f"{int(r['n_train'])}/{int(r['n_valid'])}" if cov else "not covered"
        avg = f"{f(r['tr1_0'])} / {f(r['va1_0'])}" if cov else ""
        bk = "" if not cov or pd.isna(r["best_tr"]) else f"{r['best_tr']:g}"
        dv = f"{f(r['dva_best'])} ({r['tva_best']:.2f})" if ch else ""
        se = f(r["seva_best"]) if ch else ""
        pl = (("edge," if r["best_tr"] in (0.75, 1.5) else "") + ("yes" if r["plateau_va"] == True else "no")) if ch else ""
        vd = ("PASS+stop" if r["pass_stop"] == True else "pass(size)" if r["pass"] == True else "fail") if ch else ("keep 1.0" if cov and r["best_tr"] == 1.0 else "")
        live = not pd.isna(r["n_live"])
        ln = f"{int(r['n_live'])} ({int(r['sessions'])}){' <20' if r['lt20'] == True else ''}" if live else ""
        la = f"{f(r['avgR'], 2)} / {f(r['avgR_wo_bestday'], 2)}" if live else ""
        lb = f"{r['best_live']:g}" if live else ""
        ld = f"{f(r['dlv0_75'], 2)} / {f(r['dlv1_25'], 2)} / {f(r['dlv1_5'], 2)}" if live else ""
        ag = "" if pd.isna(r["agree_dir"]) else r["agree_dir"]
        out.append(f"| {r['priority']} | {short(r['setup'])} | {lab} | {avg} | {bk} | {dv} | {se} | {pl} | {vd} | {ln} | {la} | {lb} | {ld} | {ag} |")
    return "\n".join(out)
which = sys.argv[1]
print(tab(P[P.priority <= 2]) if which == "pri" else tab(P[P.priority == 3]))
