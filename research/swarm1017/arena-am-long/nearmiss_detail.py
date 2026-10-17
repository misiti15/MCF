"""Detail of the near-miss plateau point (ret12 <= -1.6145 & gap_atr <= -0.4056 & rvol_day <= 0.80, long t1s1 09:50-11:00):
entry-time histogram, monthly expectancy, all-split summary (already counted in neighbors.py). Educational only."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search  # noqa: E402
from mcf.research.arena.combine import evaluate_combo, trades  # noqa: E402

C = [("ret12", "<=", -1.6145), ("gap_atr", "<=", -0.4056), ("rvol_day", "<=", 0.80)]
A = search.load_rows(["symbol", "date", "tod", "r_long_t1s1", "c_long_t1s1", "ret12", "gap_atr", "rvol_day", "gap"])
print("ret12 first non-NaN tod:", A.loc[A.ret12.notna(), "tod"].min())
t = trades(A, C, "long", "t1s1", (950, 1100))
print(t.tod.value_counts().sort_index().to_dict())
t["mo"] = pd.to_datetime(t.date).dt.strftime("%Y-%m")
print(t.groupby("mo").r.agg(["size", "mean"]).round(3).to_string())
print("top symbols", t.symbol.value_counts().head(8).to_dict(), "unique", t.symbol.nunique())
e = evaluate_combo(A, C, "long", "t1s1", (950, 1100), n_lineage=20282 + 23032 + 26)
(Path(__file__).resolve().parent / "nearmiss_detail.json").write_text(json.dumps(e, indent=1, default=str))
print({k: e[k] for k in ("train", "valid", "all", "per_day", "walk_forward", "gates")})
print({k: (v.get("n"), v.get("exp_r"), v.get("t")) for k, v in e["regime"].items() if k != "pass"})
