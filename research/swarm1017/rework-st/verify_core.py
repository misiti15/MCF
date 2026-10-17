"""Check stcore against the FD modules' own masks on one open month (bar-for-bar). Educational only - not financial advice."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from research.history2y import lib  # noqa: E402
from stcore import PARENT, ST, Frame, l3  # noqa: E402

FD = {"ST1": "ST1-ordn-long-pm-t05s1", "ST2": "ST2-slope20up-long-am-t05s1", "ST3": "ST3-rsi5up-short-pm-t1s1",
      "ST4": "ST4-emadn-long-am-t1s05", "ST5": "ST5-pdbrkup-short-mid-t05s1", "ST6": "ST6-volspikeup-short-mid-t1s1",
      "ST7": "ST7-rsi50dn-long-pm-t1s1", "ST8": "ST8-volspikedn-long-pm-t1s1", "L3a": "L3-gap-slope-fromopen",
      "L3b": "L3-gap-slope-lowdist", "L3c": "L3-gap-slope-rsi5hi"}
month = sys.argv[1] if len(sys.argv) > 1 else "2025-06"
d = lib.load_month(month)
key = d.symbol.astype(str).to_numpy() + "|" + d.date.astype(str).to_numpy()
new = np.r_[True, key[1:] != key[:-1]]
cols = {c: d[c].to_numpy(float) for c in d.columns if c not in ("symbol", "date", "ts")}
fr = Frame(cols, new)
out = {}
for p, name in FD.items():
    spec = importlib.util.spec_from_file_location(name, ROOT / "research/bdi/fullday" / f"{name}-FD.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    a = np.asarray(mod.mask(d), bool)
    b = fr.st(p, PARENT[p]) if p in ST else l3(cols, p, PARENT[p])
    out[p] = {"module_true": int(a.sum()), "core_true": int(b.sum()), "equal": bool((a == b).all())}
    print(p, out[p], flush=True)
json.dump({"month": month, "checks": out}, open(HERE / "verify_core.json", "w"), indent=1)
