"""CF-PRIMARY descriptive: which of Primary's own live trades (run 1, 2026-10-23..11-25) CF-15 / CF-LL15 would have
skipped, and their R after costs (pnl_adj / risk $; LR8 from 11-12, old allowance before). No re-simulation (freed
slots / latch effects not modelled). Usage (cwd repo): python live_primary.py PRIMARY_DB. Educational only."""
import json
import sqlite3
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "research/primshorts_1126")
import calib_live as CL  # noqa: E402

c = sqlite3.connect(sys.argv[1])
t = pd.read_sql("select * from trades where run_id=1 and date between '2026-10-23' and '2026-11-25' and exit_time is not null", c)
c.close()
cells = json.load(open("research/primshorts_1126/cells_live.json"))
info = t.meta.fillna("").str.extract(r'"stop_cost_r": ([0-9.]+)')[0].astype(float)
rps = (t.entry - t.stop).abs()
t["R"] = t.pnl_adj.fillna(t.pnl) / (rps * t.shares)
t["cf15"] = (2 * (0.01 + t.entry * 1e-4) + 0.02) / rps > 0.15
t["cfll"] = CL.predict_R(cells, t.entry.to_numpy(), rps.to_numpy(), np.full(len(t), "stop")) > 0.15
t = t[np.isfinite(t.R)]
out = {"trades": int(len(t)), "sessions": int(t.date.nunique()), "R_per_trade_all": round(t.R.mean(), 4),
       "logged_stop_cost_r_rows": int(info.notna().sum())}
for k in ("cf15", "cfll"):
    s = t[t[k]]; kept = t[~t[k]]
    d = s.groupby("date").R.sum().reindex(sorted(t.date.unique()), fill_value=0)
    out[k] = {"skipped": int(len(s)), "share": round(len(s) / len(t), 3), "skipped_R_total": round(s.R.sum(), 1),
              "skipped_R_per_trade": round(s.R.mean(), 4), "kept_R_per_trade": round(kept.R.mean(), 4),
              "skipped_day_t": round(d.mean() / (d.std(ddof=1) / np.sqrt(len(d))), 2),
              "by_setup": s.groupby("strategy").R.agg(["size", "sum"]).round(1).reset_index().values.tolist()}
print(json.dumps(out, indent=1))
json.dump(out, open("research/cfprimary_1127/live_primary.json", "w"), indent=1)
