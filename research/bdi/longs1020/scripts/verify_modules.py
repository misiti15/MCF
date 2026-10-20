"""Parity: LD1 module mask on offline frames vs the scan's B5-NS1-BRDUP trades (two months)."""
import importlib.util, json
import numpy as np, pandas as pd
from common import HERE, SCR, lib
from mcf.research import gates
spec = importlib.util.spec_from_file_location("ld1", HERE / "modules" / "LD1-ns1-breadthup-t05s1-long.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
T = pd.read_parquet(SCR / "b_trades.parquet"); T = T[T.base == "B5-NS1-BRDUP"]; T["date"] = pd.to_datetime(T["date"]).dt.date
out = {}
for mo in ("2025-04", "2026-06"):
    df = lib.load_month(mo, context=True); df = df[df.adv20 >= 95e6].reset_index(drop=True)
    idx = gates.first_per_symbol_day(df.symbol.to_numpy(), df.date.to_numpy(), m.mask(df) & np.isfinite(df.r_long_t05s1.to_numpy()))
    a = set(zip(df.symbol.to_numpy()[idx], df.date.to_numpy()[idx], df.tod.to_numpy()[idx]))
    t = T[pd.to_datetime(T.date).dt.strftime("%Y-%m") == mo]
    b = set(zip(t.symbol, t.date, t.tod))
    out[mo] = dict(module=len(a), scan=len(b), both=len(a & b))
json.dump(out, open(HERE / "verify_modules.json", "w")); print(out)
