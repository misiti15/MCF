"""Parity: LD2 module on offline TQQQ frame rows (context joined) vs the Part-A scan trades, all open months."""
import importlib.util, json
import numpy as np, pandas as pd
from common import HERE, SCR, lib
spec = importlib.util.spec_from_file_location("ld2", HERE / "modules" / "LD2-qqq-dip015-breadthturn-tqqq-t05s1-long.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A = pd.read_csv(HERE / "trades_A.csv.gz"); A = A[A.cfg == "A-QQQ-abs015-brd-t05s1"]
b = set(zip(A.date.astype(str), A.tod))
a = set()
for mo in lib.months():
    if mo in lib.LOCKED_MONTHS: continue
    df = lib.load_month(mo, columns=["symbol", "date", "tod", "close"], context=True)
    df = df[df.symbol == "TQQQ"].reset_index(drop=True)
    x = m.mask(df)
    a |= set(zip(df.date.astype(str)[x], df.tod[x]))
out = dict(module=len(a), scan=len(b), both=len(a & b), same_day=len({d for d, _ in a} & {d for d, _ in b}))
json.dump(out, open(HERE / "verify_ld2.json", "w")); print(out)
