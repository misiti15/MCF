import numpy as np, pandas as pd
from live import *
print("pool", len(T), T.src.value_counts().to_dict(), T.groupby("acct").date.nunique().to_dict())
print("stop exits rc: median %.3f p10 %.3f p90 %.3f" % tuple(T[T.exit_reason == "stop"].rc.quantile([.5, .1, .9])))
LEVELS = [-1.0 - 0.25 * i for i in range(13)] + [None]
rows, tk = [], {}
for x in LEVELS:
    k = "none" if x is None else f"{x:.2f}"
    tk[k] = replay(T, x)
for acct_sel in (["Primary"], ["Primary", "On Deck"]):
    sub = T[T.acct.isin(acct_sel)]
    base = None
    prev = None
    for k, m in tk.items():
        x = sub[m[sub.index]]
        r = dict(sample="+".join(acct_sel), level=k, **stats(x))
        if prev is not None:
            a = sub[tk[prev][sub.index]]; r["days_differ_vs_next_tighter"] = int(sum(set(a[a.date == d].index) != set(x[x.date == d].index) for d in sub.date.unique()))
        prev = k
        rows.append(r)
df = pd.DataFrame(rows); df.to_csv("A_live.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250); print(df.round(3).to_string())
# day-level table Primary
dl = pd.DataFrame({k: T[m].groupby(["acct", "date"]).rc.sum() for k, m in tk.items()}).fillna(0)
dl.to_csv("A_live_days.csv", float_format="%.3f"); print(dl.loc["Primary"].round(2).to_string())
