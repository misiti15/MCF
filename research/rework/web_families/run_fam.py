"""Run one pre-declared rework grid (t2_orb | t3_rvol | t5_ib | t7_nb). Educational only - not financial advice.
    python research/rework/web_families/run_fam.py t2_orb
"""
from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from research.rework.web_families import lib as L  # noqa: E402

fam = sys.argv[1]
M = importlib.import_module(f"research.rework.web_families.{fam}")
U = M.UNIVERSE if isinstance(M.UNIVERSE, list) else L.ROOT_U
OUT = Path(__file__).resolve().parent / f"{fam}_results.json"


def neighbours(v):
    out = []
    for k, steps in M.STEPS.items():
        if v[k] in steps:
            i = steps.index(v[k])
            for j in (i - 1, i + 1):
                if 0 <= j < len(steps):
                    out.append(dict(v, **{k: steps[j]}))
    return out


def evaluate(vs, res, stage):
    todo = {M.name(v): v for v in vs if M.name(v) not in res}
    if not todo:
        return
    for sp in L.SPLITS:
        t0 = time.time()
        m = L.run_multi(M.signals, todo, sp, U)
        for k in todo:
            res.setdefault(k, {"variant": todo[k], "stage": stage})
            res[k][sp] = m[k]
        print(fam, stage, sp, len(todo), f"{time.time() - t0:.0f}s", flush=True)


def main():
    res: dict = {}
    evaluate(M.GRID, res, "grid")
    s2 = M.stage2(res, M.GRID)
    evaluate(s2, res, "stage2")
    allv = {M.name(v): v for v in M.GRID + s2}
    cand = [k for k in allv if res[k]["train"].get("exp_r", -1) > 0 and res[k]["valid"].get("exp_r", -1) > 0
            and res[k]["valid"].get("n", 0) >= 30]
    nbv = [nv for k in cand for nv in neighbours(allv[k])]
    evaluate(nbv, res, "plateau")
    for k in cand:
        nb = [M.name(nv) for nv in neighbours(allv[k])]
        vals = [res[x]["valid"].get("exp_r", 0) for x in nb]
        res[k]["neighbours"] = {x: res[x]["valid"].get("exp_r") for x in nb}
        res[k]["plateau_mean_valid"] = round(sum(vals) / len(vals), 4) if vals else None
        res[k]["plateau_frac_pos"] = round(sum(x > 0 for x in vals) / len(vals), 3) if vals else None
        res[k]["baseline_valid"] = L.baseline(res[k]["valid"]["_rows"], "valid", U)
        res[k]["gate"] = L.gate(res[k]["train"], res[k]["valid"], res[k]["plateau_mean_valid"], res[k]["baseline_valid"])
    best_train = max(allv, key=lambda k: res[k]["train"].get("exp_r", -9) if res[k]["train"].get("n", 0) >= 30 else -9)
    for k in res:
        for sp in L.SPLITS:
            res[k][sp] = L.strip(res[k][sp])
    OUT.write_text(json.dumps({"family": fam, "configs_tried": len(res), "candidates": cand, "best_train": best_train,
                               "results": res}, indent=1, default=str))
    print(fam, "configs", len(res), "candidates", cand, "best_train", best_train)


if __name__ == "__main__":
    main()
