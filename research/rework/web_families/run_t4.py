"""Run the pre-declared T4 rework grid (NOTES.md). Educational only - not financial advice.
    python research/rework/web_families/run_t4.py
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from research.rework.web_families import lib as L  # noqa: E402
from research.rework.web_families import t4_rs as M  # noqa: E402

OUT = Path(__file__).resolve().parent / "t4_results.json"
B = M.BASE


def V(**kw):
    v = dict(B)
    v.update(kw)
    return v


def name(v):
    diff = [f"{k}={v[k]}" for k in B if v[k] != B[k]]
    return "t4[" + (",".join(diff) or "base") + "]"


def stage_a():
    vs = [V()]
    vs += [V(c=x) for x in (0.25, 0.375, 0.625, 0.75, 1.0)]
    vs += [V(mf=x) for x in ("vwap", "ema", "none", "qqq", "sector")]
    vs += [V(rsmode=x) for x in ("open", "r60", "r30")]
    vs += [V(bench="sector"), V(bench="sector", mf="sector"), V(beta="b1"), V(trend=False), V(vwapc=False)]
    vs += [V(rvol=x) for x in (0.0, 1.0, 1.5, 2.0)]
    vs += [V(w0=x) for x in (599, 614, 644, 659)] + [V(w1=x) for x in (659, 674, 719, 749, 779)]
    vs += [V(stop=x) for x in (0.2, 0.3, 0.35)] + [V(tgt=x) for x in (0.75, 1.5, 2.0)]
    vs += [V(cap=x) for x in (5, 20)] + [V(side="long"), V(side="short")]
    vs += [V(add=x) for x in ("gap", "or30", "pdhl")] + [V(ema=(5, 13)), V(ema=(20, 50))]
    return {name(v): v for v in vs}


def neighbours(v):
    out = []
    for k, steps in M.STEPS.items():
        if v[k] in steps:
            i = steps.index(v[k])
            for j in (i - 1, i + 1):
                if 0 <= j < len(steps):
                    out.append(dict(v, **{k: steps[j]}))
    return out


def evaluate(variants, res):
    todo = {k: v for k, v in variants.items() if k not in res}
    if not todo:
        return
    for sp in L.SPLITS:
        t0 = time.time()
        m = M.run(todo, sp)
        for k in todo:
            res.setdefault(k, {"variant": {kk: (list(x) if isinstance(x, tuple) else x) for kk, x in todo[k].items()}})
            res[k][sp] = m[k]
        print(sp, len(todo), f"{time.time() - t0:.0f}s", flush=True)


def main():
    res: dict = {}
    A = stage_a()
    evaluate(A, res)
    for k in A:
        res[k]["stage"] = "A"
    # stage B: pairs of the 6 best singles on TRAIN
    singles = [k for k in A if k != name(B) and res[k]["train"].get("n", 0) >= 60]
    singles.sort(key=lambda k: -res[k]["train"].get("exp_r", -9))
    top = singles[:6]
    Bv = {}
    for a, b in itertools.combinations(top, 2):
        va, vb = A[a], A[b]
        da = {k for k in B if va[k] != B[k]}
        db = {k for k in B if vb[k] != B[k]}
        if da & db:
            continue
        v = dict(va)
        v.update({k: vb[k] for k in db})
        Bv[name(v)] = v
    evaluate(Bv, res)
    for k in Bv:
        res[k].setdefault("stage", "B")
    # stage C: plateau neighbours for candidates
    allv = {**A, **Bv}
    cand = [k for k in allv if res[k]["train"].get("exp_r", -1) > 0 and res[k]["valid"].get("exp_r", -1) > 0
            and res[k]["valid"].get("n", 0) >= 30]
    Cv = {}
    for k in cand:
        for nv in neighbours(allv[k]):
            Cv[name(nv)] = nv
    evaluate(Cv, res)
    for k in Cv:
        res[k].setdefault("stage", "C")
    allv.update(Cv)
    # plateau + baseline for candidates
    for k in cand:
        nb = [name(nv) for nv in neighbours(allv[k])]
        vals = [res[x]["valid"].get("exp_r", 0) for x in nb]
        res[k]["neighbours"] = {x: res[x]["valid"].get("exp_r") for x in nb}
        res[k]["plateau_mean_valid"] = round(sum(vals) / len(vals), 4) if vals else None
        res[k]["plateau_frac_pos"] = round(sum(x > 0 for x in vals) / len(vals), 3) if vals else None
        res[k]["baseline_valid"] = L.baseline(res[k]["valid"]["_rows"], "valid", M.U)
        res[k]["gate"] = L.gate(res[k]["train"], res[k]["valid"], res[k]["plateau_mean_valid"], res[k]["baseline_valid"])
    for k in res:
        for sp in L.SPLITS:
            res[k][sp] = L.strip(res[k][sp])
    OUT.write_text(json.dumps({"family": "t4_rs", "configs_tried": len(res), "top6_train": top, "candidates": cand,
                               "results": res}, indent=1, default=str))
    print("configs", len(res), "candidates", cand)


if __name__ == "__main__":
    main()
