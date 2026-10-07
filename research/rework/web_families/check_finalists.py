"""Reproduce the t4 finalists through the standalone module f_t4_long_rs (common.run path, guarded loader) and
run them with ATR(10)/ATR(20). Educational only - not financial advice."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from research.rework.web_families import lib as L  # noqa: E402  (guard first)
from research.rework.web_families import f_t4_rs as F  # noqa: E402

U = [s for s in L.ROOT_U]
out = {}
for atr in ("atr", "atr10", "atr20"):
    L.ATR_COL = atr
    F._T.clear(); F._P.clear()
    for v in F.FINALISTS + ["long_emamf"]:
        for sp in L.SPLITS:
            m = L.C.run(F.signals, F.VARIANTS[v], sp, universe=U)
            m.pop("_rows", None)
            out.setdefault(f"{v}|{atr}", {})[sp] = m
            print(v, atr, sp, m.get("n"), m.get("exp_r"), m.get("t_day_clustered"), flush=True)
(Path(__file__).parent / "finalist_checks.json").write_text(json.dumps(out, indent=1, default=str))
