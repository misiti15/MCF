"""F1 (prev-day > +1% & stop >= 12 spreads) detail on live non-Graveyard longs: by SPY day type, by week, per account.
Usage: python f1_detail.py <scratch>. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
L = pd.read_parquet(f"{sys.argv[1]}/longs2.parquet"); A = L[L.book != "graveyard"].copy()
A["F1"] = (A.prev_ret > 1) & (A.stop_spreads >= 12)
A["wk"] = pd.to_datetime(A.date).dt.to_period("W-FRI").astype(str).str[:10]
for dim in ["spy_day", "wk", "account", "inst"]:
    print(f"\n-- {dim}"); print(A.pivot_table(index=dim, columns="F1", values="r", aggfunc=["count", "mean", "sum"], observed=True).round(3).to_string())
