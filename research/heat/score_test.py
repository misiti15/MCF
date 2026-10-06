"""Final, one-shot evaluation of heat candidates on the locked test split (lead only).

Usage: MCF_HEAT_ALLOW_TEST=1 python research/heat/score_test.py <locked_dir>
Prints train / valid / test stats per candidate so overfitting shows up as a valid->test drop.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

from mcf.research.heat import evaluate, load

locked = Path(sys.argv[1])
splits = {"train": load("train"), "valid": load("valid"), "test": load("test", locked)}
rows = []
sys.path.insert(0, str(Path("research/heat/candidates").resolve()))
for f in sorted(Path("research/heat/candidates").glob("*.py")):
    if f.stem.startswith("_") and f.stem != "_original":
        continue  # shared helper modules
    spec = importlib.util.spec_from_file_location(f.stem, f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    row = {"candidate": f.stem}
    for name, df in splits.items():
        res = evaluate(df, m.score(df), getattr(m, "LONG_AT", None), getattr(m, "SHORT_AT", None))
        for side, st in res.items():
            for k in ("n", "per_day", "success", "win_rate", "exp_r", "exp_r_se", "profit_factor", "green_days"):
                row[f"{name}.{side}.{k}"] = st.get(k)
    rows.append(row)
    print(f.stem, {k: v for k, v in row.items() if k.endswith(("exp_r", ".n"))}, flush=True)
out = pd.DataFrame(rows)
out.to_csv("research/heat/test_results.csv", index=False)
print(json.dumps(rows, default=str)[:200])
