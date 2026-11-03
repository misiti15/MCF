"""livelab extra2: $ risk per trade and per-setup peak concurrent lots per account. Usage: python extra2.py <scratch>.
Educational only - not financial advice."""
import sqlite3, sys, json
from pathlib import Path
import pandas as pd, numpy as np
S = Path(sys.argv[1]); OUT = Path(__file__).parent
A = {"primary": "mcf-data", "testing1": "mcf-data-testing", "testing2": "mcf-data-testing2", "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen"}
res = {}
for a, b in A.items():
    t = pd.read_sql("select * from trades where run_id=1", sqlite3.connect(S / f"{b}.db"))
    t["risk"] = (t.entry - t.stop).abs() * t.shares; t["notional"] = t.entry * t.shares
    pk = []
    for (s, d), g in t.dropna(subset=["entry_time", "exit_time"]).groupby(["strategy", "date"]):
        ev = sorted([(x, 1) for x in g.entry_time] + [(x, -1) for x in g.exit_time], key=lambda z: (z[0], z[1]))
        c = m = 0
        for _, e in ev: c += e; m = max(m, c)
        pk.append(m)
    pk = np.array(pk)
    res[a] = dict(risk_usd_p10_med_p90=[round(float(x), 1) for x in t.risk.quantile([.1, .5, .9])],
                  notional_med=round(float(t.notional.median())), setup_day_peak_med=float(np.median(pk)),
                  setup_day_peak_p90=float(np.quantile(pk, .9)), setup_day_peak_max=int(pk.max()))
json.dump(res, open(OUT / "extra2.json", "w"), indent=1); print(json.dumps(res, indent=1))
