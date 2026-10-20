"""Markdown tables for NOTES.md: per-setup autopsy per account (trades.csv).
Usage: python tables.py > tables_out.md   Educational only - not financial advice."""
from pathlib import Path
import pandas as pd
OUT = Path(__file__).resolve().parent
T = pd.read_csv(OUT / "trades.csv")
ab = lambda s: s.replace("-flowsell", "-fs").replace("failbrk-", "")
def tab(d, extra=None):
    rows = []
    for k, g in d.groupby("strategy"):
        w, l = g[g.pnl_adj > 0], g[g.pnl_adj <= 0]
        r = dict(setup=ab(k), n=len(g), win=f"{(g.pnl_adj > 0).mean()*100:.0f}%", avgR=f"{g.radj.mean():+.2f}", pl=g.pnl_adj.sum(),
                 mfe_w=f"{w.mfe.median():.2f}" if len(w) else "-", mae_l=f"{l.mae.median():.2f}" if len(l) else "-",
                 never=f"{int(g.never.sum())}/{len(l)}", lost05=str(int(g.lost_after_half.sum())), gb_w=f"{(w.mfe - w.radj).median():.2f}" if len(w) else "-",
                 tmfe=f"{w.t_mfe.median():.0f}/{l.t_mfe.median():.0f}" if len(w) and len(l) else "-", clus=str(int(g.cluster.max())), twin=str(int(g.twin.sum())),
                 lat=f"{g.lat.median():.1f}")
        if extra is not None:
            e = extra[extra.strategy == k]
            r["missing est"] = f"{len(e)} / {e.pnl_adj.sum():+.0f}" if len(e) else ""
        rows.append(r)
    if extra is not None:
        for k, e in extra[~extra.strategy.isin(d.strategy)].groupby("strategy"):
            rows.append(dict(setup=ab(k), n=0, pl=0.0, **{"missing est": f"{len(e)} / {e.pnl_adj.sum():+.0f}"}))
    R = pd.DataFrame(rows).sort_values("pl").fillna("")
    R["pl"] = R.pl.map(lambda v: f"{v:+.2f}")
    cols = list(R.columns)
    s = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    for r in R.itertuples(index=False):
        s += "| " + " | ".join(str(x) for x in r) + " |\n"
    return s
for a in ("p", "t1", "t2", "gen"):
    print(f"### {a}\n"); print(tab(T[T.acct == a]))
