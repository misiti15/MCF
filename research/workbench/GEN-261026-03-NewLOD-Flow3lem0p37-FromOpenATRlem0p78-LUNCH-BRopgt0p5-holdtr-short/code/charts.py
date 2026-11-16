"""Mechanic GEN-261026-03: engine view + the 5 worst / 5 best live teardown charts (mcf.report.blueprint, engine style).
holdtr has no target: the teardown renderer formats the target before its None check, so the target is passed as a NaN
float that prints as 'none (holdtr)' and draws nothing (renderer not edited). Educational only - not financial advice."""
import os, shutil, sys
from pathlib import Path
from common import WT, SETUP
from mcf.report import blueprint as B, engine as E

class NoTarget(float):
    def __new__(cls): return float.__new__(cls, float("nan"))
    def __format__(self, spec): return "none (holdtr)"

_td = E.teardown_data
def td(bp, stages, t, m1, fr):
    d = _td(bp, stages, t, m1, fr)
    tt = d.get("trade") if isinstance(d.get("trade"), dict) else None
    for obj in (d, tt, t):
        if isinstance(obj, dict) and "target" in obj and obj["target"] is None:
            obj["target"] = NoTarget()
    return d
E.teardown_data = td
_rt = E.render_teardown
def rt(bp, stages, d, path, rank=""):
    def fix(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "target" and v is None: o[k] = NoTarget()
                else: fix(v)
    fix(d)
    return _rt(bp, stages, d, path, rank)
E.render_teardown = rt
out = Path(WT) / "research/workbench" / SETUP
for how in ("best5", "worst5"):
    B.build(SETUP, out, style="engine", trades=how)
    for f in sorted(out.glob(f"{SETUP}_trade*_*.png")):
        k, rest = f.name[len(SETUP) + 6:].split("_", 1)
        f.rename(out / f"{SETUP}_{how[:-1]}{k}_{rest}")
print(sorted(p.name for p in out.glob("*.png")))
