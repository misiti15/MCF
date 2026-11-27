"""Layer-1 candidates on live poll snapshots (all accounts). Educational only - not financial advice."""
import pandas as pd, numpy as np
p = pd.read_parquet("polls.parquet")
p = p[p.has_mtm].copy()
p["ts"] = pd.to_datetime(p.date + " " + p.t)
p = p[(p.ts.dt.hour * 60 + p.ts.dt.minute >= 570) & (p.ts.dt.hour * 60 + p.ts.dt.minute <= 960)]
p["tot"] = p.rr.astype(float) + p.ur.astype(float)
p["nullfrac"] = np.where(p.nlots > 0, p.n_null_ur / p.nlots.clip(lower=1), 0)
rows = []
for (a, d), g in p.groupby(["account", "date"]):
    g = g.sort_values("ts").drop_duplicates("ts", keep="last")
    s = g.set_index("ts").tot
    def wd(mins):
        best, at = 0.0, None
        v, ti = s.to_numpy(), s.index.to_numpy()
        for i in range(len(v)):
            j = np.searchsorted(ti, ti[i] - np.timedelta64(mins * 60 + 30, "s"))
            if j < i:
                x = v[i] - v[j:i].max()
                if x < best:
                    best, at = x, str(s.index[i].time())[:5]
        return best, at
    d2, a2 = wd(2); d10, a10 = wd(10)
    nf = (g.nullfrac >= 0.25) & (g.nlots >= 4)
    run = (nf.astype(int).groupby((~nf).cumsum()).cumsum()).max()
    rows.append(dict(account=a, date=d, polls=len(g), final=round(s.iloc[-1], 2), trough=round(s.min(), 2),
                     drop2=round(d2, 2), at2=a2, drop10=round(d10, 2), at10=a10, peak_lots=int(g.nlots.max()),
                     maxsym=int(g.maxsym.max()), maxsym_name=g.loc[g.maxsym.idxmax(), "maxsym_name"],
                     null_run=int(run), gross_peak=g.gross.max(), stale_polls=int(g.stale.sum()), mism_polls=int((g.mism > 0).sum()),
                     worst_lot=g.minlot_ur.min()))
D = pd.DataFrame(rows)
D.to_csv("l1_live_days.csv", index=False)
pd.set_option("display.width", 250)
print(D.describe().round(2).to_string())
print("Primary:"); print(D[D.account == "primary"].to_string(index=False))
print("worst drop2 anywhere"); print(D.sort_values("drop2").head(15).to_string(index=False))
print("worst drop10 anywhere"); print(D.sort_values("drop10").head(15).to_string(index=False))
print("maxsym top"); print(D.sort_values("maxsym", ascending=False).head(10).to_string(index=False))
print("null runs"); print(D.sort_values("null_run", ascending=False).head(10).to_string(index=False))
print("worst single lot uR"); print(D.sort_values("worst_lot").head(10).to_string(index=False))
