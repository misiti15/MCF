"""PAIRS-1127 diagnostic summary: zero-latency gross vs next-minute gross per config and split (bp of stock notional).
Usage: python pr_diag_score.py SIMDIR DIAGDIR OUT.json. Educational only - not financial advice."""
import json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pr_score import split  # noqa: E402

a = pd.read_pickle(Path(sys.argv[1]) / "trades.pkl"); z = pd.read_pickle(Path(sys.argv[2]) / "trades.pkl")
out = {}
for name, t in (("next_minute", a), ("zero_latency", z)):
    t = t.copy(); t["split"] = t.date.map(split); t = t[t.split != "PRE"]
    g = t.groupby(["cfg", "split"]).g1.mean().unstack().round(2)
    out[name] = g.to_dict("index")
    print(name); print(g.to_string())
json.dump(out, open(sys.argv[3], "w"), indent=1)
