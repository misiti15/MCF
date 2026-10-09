"""Parity check: the 2-year frames (built from data/cache_hist with the setups2 pipeline) must reproduce the existing
research/setups2/data/train.parquet rows (built 2026-10-06 from data/cache, which starts 2026-06-15).
Rows are matched on (symbol, ts). Reported per column: max abs diff, and the share of rows differing by > 1e-4
(relative to max(1, |value|)), over all train dates and over train dates from 2026-07-15 (after the old cache's
warm-up: atr_d needs 14 prior sessions and the recursive EMAs ~100 bars). Writes research/history2y/parity.json.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from lib import load_month  # noqa: E402

old = pd.read_parquet(ROOT / "research/setups2/data/train.parquet")
old["date"] = pd.to_datetime(old["date"]).dt.date
lo, hi = min(old["date"]), max(old["date"])
new = pd.concat([load_month(m) for m in ("2026-06", "2026-07", "2026-08")])
new = new[(new["date"] >= lo) & (new["date"] <= hi)]
for d in (old, new):
    d["ts"] = pd.to_datetime(d["ts"])
    d["symbol"] = d["symbol"].astype(str)
j = old.merge(new, on=["symbol", "ts"], how="outer", suffixes=("_old", "_new"), indicator=True)
res = {"train_dates": [str(lo), str(hi)], "old_rows": int(len(old)), "new_rows": int(len(new)),
       "matched": int((j["_merge"] == "both").sum()), "only_old": int((j["_merge"] == "left_only").sum()),
       "only_new": int((j["_merge"] == "right_only").sum()),
       "only_old_symbols": int(j.loc[j["_merge"] == "left_only", "symbol"].nunique()),
       "only_new_symbols": int(j.loc[j["_merge"] == "right_only", "symbol"].nunique()), "columns": {}}
b = j[j["_merge"] == "both"]
late = pd.to_datetime(b["date_old"]) >= pd.Timestamp("2026-07-15")
cols = [c for c in old.columns if c not in ("symbol", "ts", "date") and pd.api.types.is_numeric_dtype(old[c])]
for c in cols:
    x, y = b[f"{c}_old"].to_numpy(float), b[f"{c}_new"].to_numpy(float)
    both_nan = np.isnan(x) & np.isnan(y)
    d = np.where(both_nan, 0.0, np.abs(x - y))
    d = np.where(np.isnan(d), np.inf, d)          # NaN on one side only counts as a mismatch
    rel = d / np.maximum(1.0, np.abs(np.nan_to_num(x)))
    res["columns"][c] = {"max_abs": float(np.max(d[np.isfinite(d)])) if np.isfinite(d).any() else None,
                         "nan_mismatch": int(np.isinf(d).sum()), "share_diff_all": round(float((rel > 1e-4).mean()), 5),
                         "share_diff_from_0715": round(float((rel[late.to_numpy()] > 1e-4).mean()), 5),
                         "max_abs_from_0715": float(np.max(np.where(np.isinf(d), 0, d)[late.to_numpy()])) if late.any() else None}
out = Path(__file__).parent / "parity.json"
out.write_text(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k != "columns"}, indent=1))
w = pd.DataFrame(res["columns"]).T.sort_values("share_diff_all", ascending=False)
print(w.to_string())
