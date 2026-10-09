"""Load every live / candidate lab and heat setup twice: as configured (current window) and with its time-of-day layer
removed (full decision day 09:50-15:00). The modules are NOT edited: their source is read, the literal tod clause is
stripped in memory, and the copy is executed as a separate module (NOTES.md 0.2). Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import types
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
FULL = (950, 1500)

TOD_CLAUSE = re.compile(r"\(tod >= \d+\) & \(tod <=? \d+\)")
HEAT_CALL = re.compile(r"(regime_score\(df, \"\w+\", W, )(\d+), (\d+),")


def _exec(src: str, path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(src, str(path), "exec"), m.__dict__)
    return m


def load_orig(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def load_free(path: Path, name: str, kind: str):
    """The module with its tod clause removed. Returns (module, n_clauses_stripped)."""
    src = path.read_text()
    if kind == "heat":
        n = len(HEAT_CALL.findall(src))
        src = HEAT_CALL.sub(lambda mo: f"{mo.group(1)}{FULL[0]}, {FULL[1]},", src)
        return _exec(src, path, name + "_free"), n
    if "WINDOW = (" in src:                      # stack1009 ST modules: the window is a module constant
        m = _exec(src, path, name + "_free")
        m.WINDOW = FULL
        return m, 1
    n = len(TOD_CLAUSE.findall(src))
    src = TOD_CLAUSE.sub("(tod == tod)", src)
    return _exec(src, path, name + "_free"), n


def setups() -> list[dict]:
    """The 30 setups of NOTES.md 0.2 with their current window (module window intersected with the YAML window)."""
    cfg = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    out = []
    for name, p in cfg.items():
        if not p.get("enabled") or p.get("type") not in ("lab", "heat"):
            continue
        kind = p["type"]
        path = ROOT / (p["module"] if kind == "lab" else p["formula"])
        out.append({"setup": name, "kind": kind, "path": path, "min_adv": float(p.get("min_adv", 0)),
                    "yaml_window": tuple(p.get("window") or FULL), "sides": p.get("sides"),
                    "group": "live" if not name.startswith(("MF", "NS", "RW6G1")) else "live probation"})
    for d, grp in (("research/bdi/stack1009/modules", "ST candidate"), ("research/bdi/rework1008/modules", "RW backlog")):
        for path in sorted((ROOT / d).glob("*.py")):
            txt = path.read_text()
            mn = re.search(r"min_adv (\d+)", txt)
            w = re.search(r"window \[(\d+), (\d+)\]", txt)
            out.append({"setup": path.stem, "kind": "lab", "path": path, "min_adv": float(mn.group(1)) if mn else 0.0,
                        "yaml_window": (int(w.group(1)), int(w.group(2))) if w else FULL, "sides": None, "group": grp})
    return out


def module_window(path: Path, kind: str) -> tuple[int, int]:
    src = path.read_text()
    if kind == "heat":
        mo = HEAT_CALL.search(src)
        return int(mo.group(2)), int(mo.group(3))
    mo = re.search(r"WINDOW = \((\d+), (\d+)\)", src)
    if mo:
        return int(mo.group(1)), int(mo.group(2))
    mo = TOD_CLAUSE.search(src)
    if mo:
        a, b = map(int, re.findall(r"\d+", mo.group(0)))
        return a, b
    return FULL


def prepare() -> list[dict]:
    sts = setups()
    for s in sts:
        nm = re.sub(r"\W", "_", s["setup"])
        s["orig"] = load_orig(s["path"], "o_" + nm)
        s["free"], s["stripped"] = load_free(s["path"], "f_" + nm, s["kind"])
        mw = module_window(s["path"], s["kind"])
        yw = s["yaml_window"]
        s["window"] = (max(950, mw[0], yw[0]), min(1500, mw[1], yw[1]))
        if s["kind"] == "lab":
            s["side"], s["geom"] = s["orig"].SIDE, getattr(s["orig"], "GEOM", "t1s1")
        else:
            s["side"], s["geom"] = s["sides"], "t1s1"
        s["needs_block"] = hasattr(s["orig"], "vwap_band_block")
    return sts


if __name__ == "__main__":
    for s in prepare():
        print(f"{s['setup']:45s} {s['kind']:4s} {s['side']:5s} {s['geom']:6s} window {s['window']} "
              f"min_adv {s['min_adv']:.0f} stripped {s['stripped']} block {s['needs_block']}")
