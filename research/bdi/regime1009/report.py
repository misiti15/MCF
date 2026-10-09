"""Markdown tables for NOTES.md section 2 from gates.csv / signals.csv. Educational only - not financial advice."""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
G = pd.read_csv(HERE / "gates.csv")
f = lambda x, d=3: "-" if pd.isna(x) else f"{x:+.{d}f}"  # noqa: E731


def row(r):
    return (f"| {r.list.replace('|', ' / ')} | {r.gate} | {int(r.n) if r.n == r.n else 0} | {f(r.exp)} | {r.t if r.t == r.t else '-'} | {r.t_req} | "
            f"{f(r.up_exp)} ({int(r.up_n) if r.up_n == r.up_n else 0}) | {f(r.flat_exp)} | {f(r.down_exp)} ({int(r.down_n) if r.down_n == r.down_n else 0}) | "
            f"{r.wf_share if r.wf_share == r.wf_share else '-'} | {f(r.ex_best_day)} | {r.busiest_day if r.busiest_day == r.busiest_day else '-'} | "
            f"{f(r.plateau_mean) if 'plateau_mean' in r else '-'} | {r.verdict} |")


hdr = ("| list | gate | n | exp R | t | t req | up exp (n) | flat exp | down exp (n) | WF share | ex-best-day | busiest day | "
       "plateau mean | verdict |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
out = []
out.append("#### Lab setups, live window (32 lists): base, G1, G3, G5, G6\n")
out.append(hdr)
cur = G[G.list.str.endswith("|current") & G.gate.isin(["base", "G1 brd0", "G3 spy0", "G5 brd1000", "G6 brdWF"])]
for _, r in cur.iterrows():
    out.append(row(r))
out.append("\n#### Full-day lab lists (30) and Reddit base rules (40): G1 and G3 only (all gates in gates.csv)\n")
out.append(hdr)
oth = G[~G.list.str.endswith("|current") & G.gate.isin(["base", "G1 brd0", "G3 spy0"])]
for _, r in oth.iterrows():
    out.append(row(r))
(HERE / "data" / "tables.md").write_text("\n".join(out))
print(len(out))
