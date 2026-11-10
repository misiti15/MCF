"""stoplab B3 regime check (Guild STOPW found the stop effect negative on DOWN days): global k on TRAIN+VALID split by
SPY day (close vs open), total delta and stop effect (beyond the size-only control r1/k). HOLD never read.
Educational only - not financial advice."""
import glob, math
from pathlib import Path
import numpy as np, pandas as pd
from analyze import split_lab, tday, KS
HERE = Path(__file__).resolve().parent
T = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob("/dev/shm/stopw_b/w_*.parquet"))], ignore_index=True)
T["split"] = split_lab(T.date); T = T[T.split != "hold"]
d = pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet", filters=[("symbol", "==", "SPY")])
d["date"] = d.date.astype(str); spy = dict(zip(d.date, np.where(d.close >= d.open, "up", "down")))
T["spy"] = T.date.map(spy)
rows = []
for k in [k for k in KS if k != 1.0]:
    for (sp, rg), g in T.groupby(["split", "spy"]):
        x = g[f"r{k}"] - g["r1.0"]; y = g[f"r{k}"] - g["r1.0"] / k
        rows.append(dict(k=k, split=sp, spy_day=rg, n=len(g), base=g["r1.0"].mean(), d=x.mean(), t_d=tday(x, g.date),
                         stop_effect=y.mean(), t_stop_effect=tday(y, g.date)))
R = pd.DataFrame(rows); R.to_csv(HERE / "regime_k.csv", index=False, float_format="%.4f")
print(R.round(4).to_string(index=False))
