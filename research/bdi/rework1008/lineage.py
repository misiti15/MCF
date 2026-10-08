"""Post-hoc (disclosed) lineage grouping of the gate passers: overlap coefficient |A&B|/min(|A|,|B|) of valid
symbol-days > 0.5 -> same lineage (it can only remove finalists). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from combos import Ctx  # noqa: E402
from finalists import EXTRA_COLS, cand_entries  # noqa: E402

p = pd.read_parquet(HERE / "data" / "passers.parquet").reset_index(drop=True)
cx = Ctx(EXTRA_COLS)
sets = []
for _, x in p.iterrows():
    ent, _, _ = cand_entries(cx, x)
    sets.append(set(cx.sp["valid"].sid[ent["valid"]].tolist()) | {("t", k) for k in cx.sp["train"].sid[ent["train"]].tolist()})
n = len(p)
oc = np.array([[len(sets[i] & sets[j]) / max(1, min(len(sets[i]), len(sets[j]))) for j in range(n)] for i in range(n)])
lin = [-1] * n
for i in range(n):              # p is sorted by score: the first member of a lineage is its representative
    if lin[i] < 0:
        lin[i] = i
        for j in range(i + 1, n):
            if lin[j] < 0 and oc[i, j] > 0.5:
                lin[j] = i
p["lineage"] = lin
p["rep"] = p.index == p.lineage
p.to_parquet(HERE / "data" / "passers.parquet")
pd.DataFrame(oc.round(2), index=range(n), columns=range(n)).to_csv(HERE / "data" / "overlap.csv")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 100)
print(p[["family", "conds", "window", "score", "va_tpd", "lineage", "rep", "corr_max_setup", "corr_max", "overlap_live"]].round(3).to_string())
