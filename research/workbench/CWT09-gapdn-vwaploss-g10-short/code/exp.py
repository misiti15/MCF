"""Every one-part copy (and later combos) vs the parent on both tests. Usage: python exp.py <variants module attr> <out csv>
Educational only - not financial advice."""
import sys, pandas as pd
import wb
from variants import V
names = sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] != "all" else list(V)
outcsv = sys.argv[2] if len(sys.argv) > 2 else "exp.csv"
D = {t: wb.load(t) for t in ("replay", "2y")}
rows, keep = [], {}
for t, (s, P) in D.items():
    par = wb.trades(s, P, wb.BASE)
    for vn in ["parent"] + [n for n in names if n != "parent"]:
        cfg = {**wb.BASE, **V[vn][0]} if vn != "parent" else wb.BASE
        tr = par if vn == "parent" else wb.trades(s, P, cfg)
        keep[(t, vn)] = tr
        st = wb.stats(tr); pr = wb.paired(tr, par) if len(tr) else {}
        row = dict(test=t, copy=vn, part=V[vn][1] if vn in V else "-", **st, **pr)
        if len(tr):
            for k, g in tr.groupby("dtype"): row[f"dt_{k}"] = g.r.mean()
            if t == "2y":
                for k, g in tr.groupby(tr.date.map(wb.split)): row[k] = g.r.mean()
            row["exits"] = tr.why.value_counts().to_dict()
        rows.append(row)
R = pd.DataFrame(rows); R.to_csv(wb.OUT + outcsv, index=False)
pd.to_pickle(keep, wb.OUT + outcsv.replace(".csv", "_trades.pkl"))
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 500)
cols = ["test", "copy", "n", "win", "avg", "wo_best", "worst_day", "total", "avg_win", "avg_loss", "hold", "pdiff", "pt", "dt_up", "dt_flat", "dt_down", "train", "valid"]
print(R[[c for c in cols if c in R]].round(3).to_string())
