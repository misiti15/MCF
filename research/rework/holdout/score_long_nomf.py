"""One-time locked-holdout scoring of the t4 rework finalist long_nomf (lineage t4_rel_strength: look 1 -> t >= 1.0).
Production engine and costs via research/reddit_bt/common.py. Lead, 2026-10-06. Educational only - not financial advice."""
import json
import os
import sys

sys.path.insert(0, ".")
os.environ["MCF_RBT_ALLOW_HOLDOUT"] = "1"
from research.reddit_bt import common as C
from research.rework.web_families import f_t4_rs as M

out = {}
for split in ("test", "q2"):
    m = C.run(M.signals, M.VARIANTS["long_nomf"], split, universe=M._U)
    rows = m.pop("_rows", None)
    if rows is not None and len(rows):
        m["random_baseline"] = C.random_baseline(rows, split, M.VARIANTS["long_nomf"].get("stop", 0.25), None)
    out[split] = m
    print(split, json.dumps(m, default=str), flush=True)
    C._hist.cache_clear()
json.dump(out, open("research/rework/holdout/long_nomf.json", "w"), indent=1, default=str)
