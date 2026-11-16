"""Shape table (avg win/loss, hold, exit mix, SPY day-type split) for the parent and the WB copies, both tests; live-trade overlap."""
import sys; sys.path.insert(0, "code")
from load import *
import sim2, decl
A = {**decl.ROUND1, **decl.ROUND2, **decl.ROUND3, **decl.ROUND4}
S = pd.read_parquet("spy1m.parquet"); S.index = S.index.tz_convert("America/New_York"); S["d"] = S.index.strftime("%Y-%m-%d")
oc = S.groupby("d").apply(lambda g: (g.close.iloc[-1] / g.open.iloc[0] - 1) * 100)
L = pd.read_parquet("live_joined.parquet")
rows = []
for nm, key in (("PARENT", "PARENT"), ("WB2", "S2 skip SPY > +0.10% since 09:50"), ("WB1", "V06 window end 15:00->13:00 (P6)"), ("WB3", "E3 D10 with 30-min gate 0.20")):
    o = run(A[key])
    for test, t in o.items():
        r = dict(cfg=nm, test=test, n=len(t), avg_win=t.r[t.r > 0].mean(), avg_loss=t.r[t.r <= 0].mean(), hold=(t.xm - t.em).median(),
                 stop=(t.kind == "stop").mean(), target=(t.kind == "target").mean(), time=(t.kind == "time").mean())
        dt = pd.cut(t.date.map(oc), [-99, -0.25, 0.25, 99], labels=["down", "flat", "up"])
        for k, g in t.groupby(dt, observed=True).r: r[f"{k}"] = f"{g.mean():+.3f} ({len(g)})"
        rows.append(r)
        if test == "replay":
            k = set(zip(t.symbol, t.date, t.tod))
            m = L[[(a, b, c) in k for a, b, c in zip(L.symbol, L.date, L.tod)]]
            print(nm, "live trades whose signal bar the copy also takes:", len(m), f"live avg {m.r.mean():+.3f} total {m.r.sum():+.1f}",
                  "| live trades the copy drops:", len(L) - len(m), f"{L.r.sum() - m.r.sum():+.1f}R")
x = pd.DataFrame(rows); print(x.round(3).to_string()); x.round(3).to_csv("extras.csv", index=False)
