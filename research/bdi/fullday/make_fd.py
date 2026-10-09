"""Generate the full-day (-FD) copies of every lab setup that runs in the primary or the Testing account.

Owner decision 2026-10-09: "for any of our setups, I want full day versions first, then we can identify time frames
that may be better." Each <NAME>-FD.py is a copy of the source module with ONLY the time-of-day clause that limits WHEN
the rule may fire removed; the decision bars become 09:50-15:00 through the YAML window [950, 1500]. Structural uses of
tod (the ST opening range read at the 10:00 bar and its `tod > 1000` trigger guard) are kept. The heat setups get
full-day formula copies (their regime_score call carries the window). Source modules are not edited.

    python research/bdi/fullday/make_fd.py      # (re)writes research/bdi/fullday/*-FD.py and specs.json
Educational only - not financial advice.
"""
from __future__ import annotations

import ast
import json
import re
import textwrap
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FULL = (950, 1500)
LAB_TOD = re.compile(r" & \(tod >= (\d+)\) & \(tod (<=?) (\d+)\)")
L3_TOD = re.compile(r"\n\s+& \(\(c\('tod'\) >= (\d+)\) & \(c\('tod'\) (<=?) (\d+)\)\)\)")
ST_RET = "return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), dtype=bool)"
HEAT_CALL = re.compile(r"(regime_score\(df, \"\w+\", W, )(\d+), (\d+),")
TIME_LAYER = re.compile(r"\d\d:\d\d-\d\d:\d\d ET|tod <|tod >=")
FD_LAYER = "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])"


def lab_setups() -> list[dict]:
    """Every enabled lab setup of config/default.yaml (primary) and config/account_testing.yaml (Testing)."""
    out = []
    for f, acct in (("config/default.yaml", "primary"), ("config/account_testing.yaml", "testing")):
        for name, p in (yaml.safe_load((ROOT / f).read_text())["strategies"] or {}).items():
            if p.get("enabled") and p.get("type") == "lab":
                out.append({"name": name, "account": acct, "source": p["module"], "min_adv": int(p.get("min_adv", 0)),
                            "yaml_window": list(p.get("window") or FULL), "prefilter": p.get("prefilter")})
    return out


def heat_setups() -> list[dict]:
    cfg = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    return [{"name": n, "account": "primary", "source": p["formula"], "config": p}
            for n, p in cfg.items() if p.get("type") == "heat"]


def _replace_node(src: str, node: ast.AST, text: str) -> str:
    lines = src.splitlines(keepends=True)
    return "".join(lines[: node.lineno - 1]) + text + "".join(lines[node.end_lineno:])


def _docstring(spec: dict, removed: str, kept: str, src_doc: str) -> str:
    lo, hi = spec["module_window"]
    run = f"Run with min_adv {spec['min_adv']} and window [950, 1500] (bar close ET)"
    if spec.get("prefilter"):
        run += f", prefilter {spec['prefilter']!r} (as the source)"
    old = re.sub(r"\bRun with\b", "Source ran with", src_doc.strip())
    old = textwrap.indent(old, "    ")
    return (f'"""{spec["name"]}-FD - FULL-DAY version of {spec["name"]} (owner decision 2026-10-09: full-day versions\n'
            f"first, then identify time frames that may be better; Testing account).\n"
            f"Source module: {spec['source']} (copied; logic identical except the removed clause).\n"
            f"Removed: {removed} - the clause that limited WHEN the rule may fire (source module window {lo}-{hi}\n"
            f"ET bar close; source YAML window {spec['yaml_window']}).\n"
            f"Kept: {kept}\n"
            f"{run}.\n"
            f"Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).\n"
            f"Source docstring (provenance only - its results describe the WINDOWED rule, not this one):\n"
            f"{old}\n"
            f'Educational only - not financial advice."""\n')


def make_lab(spec: dict) -> dict:
    src_path = ROOT / spec["source"]
    src = src_path.read_text()
    kept = "every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note)."
    if ST_RET in src:                                    # stack1009 ST modules: WINDOW constant + final clause
        mo = re.search(r"WINDOW = \((\d+), (\d+)\)", src)
        lo, hi, strict = int(mo.group(1)), int(mo.group(2)), False
        removed = f"`m & (tod >= WINDOW[0]) & (tod <= WINDOW[1])` with WINDOW = ({lo}, {hi})"
        src = src.replace(ST_RET, "return np.asarray(m, dtype=bool)")
        src = src.replace(mo.group(0), f"WINDOW = None  # full day (source: WINDOW = ({lo}, {hi})); window = YAML [950, 1500]")
        kept = ("every other condition; the 09:30-10:00 opening range read at the 10:00 bar (`tod == 1000`) and the "
                "OR trigger's `tod > 1000` guard are structural, not a window, and stay.")
        n = 1
    elif L3_TOD.search(src):                             # layering finalists: c('tod') clause on its own line
        mo = L3_TOD.search(src)
        lo, strict, hi = int(mo.group(1)), mo.group(2) == "<", int(mo.group(3))
        removed = f"`(c('tod') >= {lo}) & (c('tod') {mo.group(2)} {hi})`"
        n = len(L3_TOD.findall(src))
        src = L3_TOD.sub(")", src)
    else:
        found = LAB_TOD.findall(src)
        n = len(found)
        if n:
            a, op, b = found[0]
            lo, strict, hi = int(a), op == "<", int(b)
            removed = f"`(tod >= {a}) & (tod {op} {b})`"
            src = LAB_TOD.sub("", src)
        else:                                            # MF5: no module clause (already 09:50-15:00)
            lo, hi, strict = FULL[0], FULL[1], False
            removed = "nothing (the source has no time-of-day clause; its window was already [950, 1500])"
    assert n <= 1, (spec["name"], n)
    if "vwap_band_block" in src:
        kept = ("every other condition; the owner's VWAP +2 SD band guard (vwap_band_block, copied verbatim, fail-safe "
                "without volume) stays.")
    spec.update(module_window=[lo, hi], strict_hi=strict, clauses_removed=n)
    tree = ast.parse(src)
    # LAYERS: replace the time layer by the full-day note
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "LAYERS":
            layers = [x for x in ast.literal_eval(node.value) if not TIME_LAYER.search(x)] + [FD_LAYER]
            src = _replace_node(src, node, "LAYERS = " + json.dumps(layers, indent=4).replace("\n]", ",\n]") + "\n")
            break
    tree = ast.parse(src)
    doc = ast.get_docstring(tree, clean=False) or ""
    src = _replace_node(src, tree.body[0], _docstring(spec, removed, kept, doc))
    out = HERE / f"{spec['name']}-FD.py"
    out.write_text(src)
    spec["fd_module"] = str(out.relative_to(ROOT))
    return spec


def make_heat(spec: dict) -> dict:
    src = (ROOT / spec["source"]).read_text()
    mo = HEAT_CALL.search(src)
    lo, hi = int(mo.group(2)), int(mo.group(3))
    src = HEAT_CALL.sub(lambda m: f"{m.group(1)}{FULL[0]}, {FULL[1]},", src)
    # the formula imports _regime_common from its own directory: point it at the source directory
    src = src.replace("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))",
                      "sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "
                      "'..', '..', 'heat', 'candidates'))  # research/heat/candidates/_regime_common.py")
    assert "'heat', 'candidates'" in src
    tree = ast.parse(src)
    doc = ast.get_docstring(tree, clean=False) or ""
    cfg = spec["config"]
    new_doc = (f'"""{spec["name"]}-FD - FULL-DAY version of {spec["name"]} (owner decision 2026-10-09; Testing account).\n'
               f"Source formula: {spec['source']} (copied; weights, threshold, gate, cost term unchanged).\n"
               f"Removed: the time-of-day gate of regime_score ({lo}, {hi}) -> ({FULL[0]}, {FULL[1]}); the heat score "
               f"itself carries the\nwindow, so widening the YAML window alone would not widen the setup.\n"
               f"Run with type heat, sides {cfg['sides']}, gate {cfg.get('gate')}, min_adv {cfg['min_adv']} and window "
               f"[950, 1500] (bar close ET).\n"
               f"Check: research/bdi/fullday/verify.json.\n"
               f"Source docstring (provenance only):\n{textwrap.indent(doc.strip(), '    ')}\n"
               f'Educational only - not financial advice."""\n')
    src = _replace_node(src, tree.body[0], new_doc)
    out = HERE / f"{spec['name']}-FD.py"
    out.write_text(src)
    spec.update(module_window=[lo, hi], strict_hi=False, clauses_removed=1, fd_module=str(out.relative_to(ROOT)),
                min_adv=int(cfg["min_adv"]), yaml_window=list(cfg.get("window") or FULL))
    spec.pop("config")
    return spec


def main():
    specs = [make_lab(s) for s in lab_setups()] + [make_heat(s) for s in heat_setups()]
    (HERE / "specs.json").write_text(json.dumps(specs, indent=1) + "\n")
    for s in specs:
        print(f"{s['name']:42s} {s['account']:8s} window {s['module_window']} strict {s['strict_hi']} "
              f"removed {s['clauses_removed']} -> {s['fd_module']}")


if __name__ == "__main__":
    main()
