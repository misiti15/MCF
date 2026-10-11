"""Stage B selection (NOTES 1.4): per side, the 12 singles with the highest TRAIN lift for Y(3) (train fires >= 5,000);
all 220 triples of them. Output: data/triples.json. Educational only - not financial advice."""
import json
from itertools import combinations

import pandas as pd

from common import DATA, NC

s = pd.read_parquet(DATA / "scores_A.parquet")
s = s[(s.line == "t1s1") & (s.ncond == 1)]
out, chosen = {}, {}
for side in ("long", "short"):
    x = s[(s.side == side) & (s.fires_train >= 5000)].sort_values("lift3_train", ascending=False).head(12)
    idx = [eval(c)[0] for c in x["combo"]]
    chosen[side] = list(zip(x["cond"], x["lift3_train"].round(3)))
    out[side] = [list(c) for c in combinations(sorted(idx), 3)]
(DATA / "triples.json").write_text(json.dumps(out))
print(json.dumps(chosen, indent=1), {k: len(v) for k, v in out.items()})
