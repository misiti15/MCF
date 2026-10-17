"""Robustness of the gate survivors and the strongest near-misses: ex-top-5-days, per-half-year, monthly share,
2025-04 excluded, hit rate. -> robust.json. Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd

from common import HERE, dcode, dstat, trades
from gate import idx_of

G = pd.read_csv(HERE / "gate_all.csv", low_memory=False)
sel = pd.concat([G[G.cand], G[G.regime_pass & ~G.cand].sort_values("t_all", ascending=False).head(12)])
out = []
for _, r in sel.iterrows():
    idx = idx_of(r)
    t = trades(idx, r["side"], r["exit"])
    day = t.groupby("date")["r"].agg(["sum", "size"])
    top5 = set(day["sum"].nlargest(5).index)
    big5 = set(day["size"].nlargest(5).index)
    d = dcode[t["ri"].to_numpy()]
    def st(m):
        n, mu, tt = dstat(t["r"].to_numpy()[m], d[m])
        return {"n": n, "exp": round(mu, 4) if n else None, "t": round(tt, 2) if n > 1 else None}
    h = pd.to_datetime(t["date"]).dt.to_period("Q").astype(str).to_numpy()
    halves = {q: st(h == q) for q in sorted(set(h))}
    apr = pd.to_datetime(t["date"]).dt.strftime("%Y-%m").to_numpy() != "2025-04"
    o = {"cfg": f"{r['stage']} {r['L']} p{r['p']} k{r['k']} {r['vol']} [{r['filters']}] {r['side']} {r['exit']} "
                f"{r['win']} refire={r['refire']}", "cand": bool(r["cand"]),
         "all": st(np.ones(len(t), bool)), "ex_top5_pnl_days": st(~t.date.isin(top5).to_numpy()),
         "ex_5_busiest_days": st(~t.date.isin(big5).to_numpy()), "ex_2025_04": st(apr),
         "win_rate": round(float((t.r > 0).mean()), 3), "per_quarter": halves,
         "busiest_days": {str(k): int(v) for k, v in day["size"].nlargest(3).items()}}
    out.append(o)
    print(o["cfg"], o["all"], "exTop5", o["ex_top5_pnl_days"], "exBusy5", o["ex_5_busiest_days"], "exApr", o["ex_2025_04"],
          o["busiest_days"])
json.dump(out, open(HERE / "robust.json", "w"), indent=1)
