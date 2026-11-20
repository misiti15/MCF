"""Load all live paper trades (run_id=1, LR8 costs in pnl_adj) from the 10 account journals -> live_trades.parquet.
R = LR8 on every row (mcf.costs.cost_r_lr8, DQ-P3 one basis). Educational only - not financial advice."""
import sqlite3, glob, sys, pandas as pd, numpy as np
J = sys.argv[1]; OUT = sys.argv[2]
ACC = {"mcf-data": "Primary", "mcf-data-testing": "Testing1", "mcf-data-testing2": "Testing2", "mcf-data-livelab": "LiveLab",
       "mcf-data-explore1": "Explore1", "mcf-data-graveyard": "Graveyard", "mcf-data-testingd": "TestingD",
       "mcf-data-testinge": "TestingE", "mcf-data-testingf": "TestingF", "mcf-data-gen": "Gen"}
parts = []
for b, a in ACC.items():
    c = sqlite3.connect(f"{J}/{b}.db")
    d = pd.read_sql("select id,symbol,strategy,side,date,signal_time,entry_time,entry,stop,target,exit_time,exit,exit_reason,"
                    "r_multiple,mae_r,mfe_r,shares,pnl,pnl_adj,slip_bps,meta from trades where run_id=1", c)
    d["account"] = a; parts.append(d)
d = pd.concat(parts, ignore_index=True)
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from mcf import costs  # LR8 on every row (DQ-P3 one basis)
d["R"] = costs.cost_r_lr8(d, costs._report_cfg()).astype(float)
d["R_booked"] = costs.cost_r(d).astype(float)
import re
d["spread_bps"] = d.meta.fillna("").map(lambda m: float(re.search(r'"spread_bps": ([0-9.]+)', m).group(1)) if re.search(r'"spread_bps": ([0-9.]+)', m) else np.nan)
d = d.drop(columns="meta")
d["tgtR"] = (d.target - d.entry).abs() / (d.entry - d.stop).abs()
for k in ("entry_time", "exit_time"):
    d[k] = pd.to_datetime(d[k], utc=True, format="ISO8601").dt.tz_convert("America/New_York")
d["hold_min"] = (d.exit_time - d.entry_time).dt.total_seconds() / 60
d["family"] = np.where(d.strategy.str.startswith("GEN"), "GEN", d.strategy.str.split("-").str[0])
d.to_parquet(OUT, index=False)
print(len(d), d.groupby("account").size().to_dict()); print(d.R.describe())
