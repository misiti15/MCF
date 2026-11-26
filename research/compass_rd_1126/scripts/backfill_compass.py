import sys, pandas as pd
sys.path.insert(0, sys.argv[1])
from mcf.report import compass_live as CL
out = sys.argv[2]; NY = CL.NY; days = sys.argv[3].split(",")
names = CL.universe(); syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + names))
rows = []
for d in days:
    try:
        bars = CL.fetch(d, syms, pd.Timestamp(f"{d} 16:30", tz=NY), log=lambda *a: None)
        r = CL.compute(bars, d, pd.Timestamp(f"{d} 16:30", tz=NY), names=names)
        rows += r; print(d, len(r), flush=True)
        pd.DataFrame(rows).to_parquet(out)
    except Exception as e:
        print(d, "ERR", e, flush=True)
