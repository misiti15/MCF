"""End-to-end smoke run of mcf.research.arena.combine on the real open history (train + valid, all symbol-days):
the best single screen cell by train t (gap_atr <= -0.614, short t1s1, 14:00-15:00) and, as a 2-condition example,
the same plus a VWAP condition. Two configurations (counted in NOTES). Educational only - not financial advice."""
import json
import sys
from pathlib import Path

from mcf.research.arena import data as D
from mcf.research.arena.combine import evaluate_combo, write_module

HERE = Path(__file__).resolve().parent
A = D.load(names=["gap_atr", "vwap_atr"], split="all", workers=1, context=False)
N = 20280 + 2
out = []
for conds in ([("gap_atr", "<=", -0.614)], [("gap_atr", "<=", -0.614), ("vwap_atr", "<=", 0.0)]):
    r = evaluate_combo(A, conds, "short", "t1s1", window=(1400, 1530), n_lineage=N)
    out.append(r)
    print(json.dumps({k: r[k] for k in ("conds", "train", "valid", "regime", "walk_forward", "gates", "quality_pass")},
                     default=str), flush=True)
(HERE / "smoke_combo.json").write_text(json.dumps(out, indent=1, default=str))
p = write_module(out[0]["conds"], "short", "t1s1", (1400, 1530), sys.argv[1] + "/AR-demo.py", name="AR-demo")
import importlib.util
spec = importlib.util.spec_from_file_location("ar_demo", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
f = D._lib().load_month("2026-03")
print("module mask hits 2026-03:", int(m.mask(f).sum()))
