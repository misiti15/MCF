"""Global indicator-length swap (rule 18): every family's best-by-train config re-run with daily ATR(10) and ATR(20)
in place of ATR(14) at the same time, plus EMA 5/13 and 20/50 in t5. Educational only - not financial advice.
    python research/rework/web_families/run_swaps.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from research.rework.web_families import lib as L  # noqa: E402
from research.rework.web_families import t2_orb, t3_rvol, t5_ib, t7_nb, t4_rs  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "swaps_results.json"


def best(fam):
    d = json.loads((HERE / f"{fam}_results.json").read_text())
    r = d["results"]
    k = max(r, key=lambda k: r[k]["train"].get("exp_r", -9) if r[k]["train"].get("n", 0) >= 30 else -9)
    v = r[k]["variant"]
    if "ema" in v:
        v["ema"] = tuple(v["ema"])
    return k, v


res = {}
for atr in ("atr10", "atr20"):
    L.ATR_COL = atr
    for fam, M in (("t2_orb", t2_orb), ("t3_rvol", t3_rvol), ("t5_ib", t5_ib), ("t7_nb", t7_nb), ("t4", t4_rs)):
        k, v = best(fam)
        for sp in L.SPLITS:
            if fam == "t4":
                m = t4_rs.run({k: v}, sp)[k]
            else:
                U = M.UNIVERSE if isinstance(M.UNIVERSE, list) else L.ROOT_U
                m = L.run_multi(M.signals, {k: v}, sp, U)[k]
            res.setdefault(f"{k}|{atr}", {"family": fam, "variant": v, "swap": atr})[sp] = L.strip(m)
        print(k, atr, {sp: (res[f'{k}|{atr}'][sp].get('n'), res[f'{k}|{atr}'][sp].get('exp_r')) for sp in L.SPLITS}, flush=True)
L.ATR_COL = "atr"
k, v = best("t5_ib")
for ema in ((5, 13), (20, 50)):
    vv = dict(v, ema=ema)
    for sp in L.SPLITS:
        m = L.run_multi(t5_ib.signals, {k: vv}, sp, L.ROOT_U)[k]
        res.setdefault(f"{k}|ema{ema}", {"family": "t5_ib", "variant": vv, "swap": f"ema{ema}"})[sp] = L.strip(m)
    print(k, ema, flush=True)
OUT.write_text(json.dumps({"configs_tried": len(res), "results": res}, indent=1, default=str))
print("swaps", len(res))
