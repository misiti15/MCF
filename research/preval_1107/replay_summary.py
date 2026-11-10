"""Summarise the as-live replays (replay.py output) next to actual Primary and the journal recomputation.
Usage: python replay_summary.py <replay outdir> <scratch>   Writes replay_days.csv, replay_setups.csv. Educational only - not financial advice."""
import sys, json, glob, sqlite3
from pathlib import Path
import pandas as pd, numpy as np
D, S = Path(sys.argv[1]), Path(sys.argv[2]); OUT = Path(__file__).resolve().parent
rows, per = [], []
for f in sorted(D.glob("*.json")):
    r = json.load(open(f)); tr = pd.DataFrame(r["trades"])
    R = tr.r.sum() if len(tr) else 0.0
    rows.append(dict(book=r["book"], date=r["date"], trades=len(tr), R=R, pnl=tr.pnl.sum() if len(tr) else 0, secs=r["seconds"]))
    if len(tr):
        for s, g in tr.groupby("strategy"): per.append(dict(book=r["book"], date=r["date"], setup=s, trades=len(g), R=g.r.sum()))
X = pd.DataFrame(rows); X.to_csv(OUT / "replay_days.csv", index=False, float_format="%.3f")
P = pd.DataFrame(per); P.to_csv(OUT / "replay_setups.csv", index=False, float_format="%.3f")
pv = X.pivot(index="date", columns="book", values="R")
act = pd.read_sql("select date, sum(pnl_adj / (abs(entry-stop)*shares)) R from trades where run_id=1 and exit is not null group by date",
                  sqlite3.connect(S / "p" / "journal.db")).set_index("date").R
pv["actual"] = act.reindex(pv.index)
J = pd.read_csv(OUT / "jrecomp_days.csv").pivot(index="date", columns="book", values="R").add_prefix("j_")
pv = pv.join(J)
print(pv.round(2).to_string())
def summ(v):
    v = v.dropna(); return {"total R": round(v.sum(), 2), "avg R/day": round(v.mean(), 2), "green": f"{int((v > 0).sum())}/{len(v)}",
                            "worst day": f"{v.min():+.2f} ({v.idxmin()[5:]})", "11-05": round(v.get("2026-11-05", np.nan), 2), "11-06": round(v.get("2026-11-06", np.nan), 2),
                            "w/o best day": round(v.sum() - v.max(), 2)}
cols = [c for c in ["actual", "asis", "opt1", "opt1b", "opt2", "opt2b", "j_asis", "j_opt1", "j_opt1b", "j_opt2", "j_opt2b"] if c in pv]
print(pd.DataFrame({c: summ(pv[c]) for c in cols}).T.to_string())
print(P.groupby(["setup", "book"]).agg(trades=("trades", "sum"), R=("R", "sum")).unstack("book").round(2).to_string())
