"""L3 gap-slope family (fromopen-FD, rsi5hi-FD): taken trades vs what-if of signals skipped 'not shortable/ETB', every
account journal, all days. Answers: on Primary day 1 (10-30) 41 of 46 L3-fromopen signals were not shortable; is the L3
record (taken) different from the not-shortable what-if? What-if R is before costs (journal run 2 r_multiple); taken
trades shown both as r_multiple (before costs) and pnl_adj / $risk (after costs).
Usage: python l3etb.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
pd.set_option("display.width", 250)
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, run_id, strategy, symbol, entry, stop, shares, r_multiple, pnl_adj, meta from trades where strategy like 'L3-gap-slope%'", c)
    t["acct"] = a
    rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["why"] = np.where(T.run_id == 1, "taken", T.meta.fillna("").str.extract(r"why=([^;0-9]+)")[0].str.strip().fillna("other"))
T["why"] = T.why.str.replace(r"spread.*", "spread", regex=True)
risk = (T.entry - T.stop).abs() * T.shares
T["radj"] = T.pnl_adj.astype(float) / risk.replace(0, np.nan).astype(float)
T.loc[T.run_id != 1, "radj"] = np.nan
out = []
g = T.groupby(["strategy", "why"]).agg(n=("r_multiple", "size"), days=("date", "nunique"), avgR=("r_multiple", "mean"),
                                       sumR=("r_multiple", "sum"), avgR_adj=("radj", "mean"), win=("r_multiple", lambda x: (x > 0).mean()))
out.append("== by strategy x reason (all accounts, all days)\n" + g.round(3).to_string())
for st in sorted(T.strategy.unique()):
    d = T[(T.strategy == st) & T.why.isin(["taken", "not shortable/ETB"])]
    p = d.pivot_table(index="date", columns="why", values="r_multiple", aggfunc=["size", "mean"]).round(3)
    out.append(f"\n== {st}: per day, taken vs not shortable (r_multiple, before costs)\n" + p.to_string())
    dd = d.groupby(["date", "why"]).r_multiple.mean().unstack()
    if {"taken", "not shortable/ETB"} <= set(dd.columns):
        x = dd.dropna()
        out.append(f"days with both: {len(x)}; corr of daily mean R {x.corr().iloc[0,1]:.2f}; NTSB > taken on {(x['not shortable/ETB'] > x['taken']).sum()} days")
txt = "\n".join(out) + "\n\nEducational only - not financial advice.\n"
open(OUT / "l3etb_out.txt", "w").write(txt); print(txt)
