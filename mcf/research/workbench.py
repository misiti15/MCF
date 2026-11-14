"""Workbench teardown practice (owner project WORKBENCH, 2026-11-13): change ONE part of a live setup slightly and get a
BRAND-NEW research-only setup with a parent link. The original setup, its config block and its module are never edited.

    python -m mcf.research.workbench spawn L3-gap-slope-fromopen-FD --set cond.fromOpen=4.0 --note "later fade"
    python -m mcf.research.workbench spawn ST7-rsi50dn-long-pm-t1s1-FD --set window=1100-1500
    python -m mcf.research.workbench list L3-gap-slope-fromopen-FD

Parameters are the ones the blueprint lists (python -m mcf.report.blueprint <setup>, "WORKBENCH PARAMETERS"): config
keys of the setup block (window, min_adv, prefilter, refire, refire_cooldown, scale_out_r, geom, r_atr_frac, ...) and the
module's entry conditions as cond.<column> (the bare column name works when it is not also a config key). Values are YAML
(4.0, null, [1000, 1500]); a window may also be written 1000-1500.

Writes, under research/workbench/<parent>/:
  modules/<parent>-WB<n>.py   the parent module with exactly the one literal changed (a copy even for config-only changes)
  <parent>-WB<n>.yaml         a config stub `strategies: {<new id>: {..., enabled: false, workbench: {...}}}` - NOT part of any
                              account config (mcf/config.py never reads it), so nothing goes live
  variants.jsonl              lineage: id, parent, param, old, new, date, note, files
  README.md                   the human log
Next step for a variant is the normal process: a backtest under docs/RESEARCH_RULES.md (costs in, number of configurations
tried reported), a backlog entry, then the testing arena only with the owner's yes. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import date
from pathlib import Path

import yaml

from ..report import blueprint as B

ROOT = B.ROOT
WB_DIR = ROOT / "research" / "workbench"
DROP_KEYS = ("gen", "from_testing2", "former_primary", "ticker_split")


def _value(key: str, raw: str):
    if key == "window" and re.fullmatch(r"\s*\d{3,4}\s*-\s*\d{3,4}\s*", raw):
        return [int(x) for x in raw.split("-")]
    return yaml.safe_load(raw)


def _lit(v, old) -> str:
    if isinstance(old, float) and isinstance(v, int) and not isinstance(v, bool):
        v = float(v)
    return repr(v)


def _splice(src: str, span: list[int], text: str) -> str:
    """Replace the source range (ast lineno / utf-8 byte col_offset, as ast reports it) with text."""
    l0, c0, l1, c1 = span
    lines = src.encode().split(b"\n")
    head = b"\n".join(lines[:l0 - 1] + [lines[l0 - 1][:c0]])
    tail = b"\n".join([lines[l1 - 1][c1:]] + lines[l1:])
    return (head + text.encode() + tail).decode()


def resolve(params: dict, key: str) -> str:
    if key in params:
        return key
    if not key.startswith("cond.") and f"cond.{key}" in params:
        return f"cond.{key}"
    raise KeyError(f"unknown parameter {key!r}; choose one of: {', '.join(params)}")


def next_id(parent: str, pdir: Path) -> str:
    n = 0
    f = pdir / "variants.jsonl"
    if f.exists():
        for line in f.read_text().splitlines():
            m = re.search(r"-WB(\d+)$", json.loads(line).get("id", ""))
            n = max(n, int(m.group(1))) if m else n
    return f"{parent}-WB{n + 1}"


def spawn(parent: str, assignment: str, note: str | None = None, out_dir: Path | str = WB_DIR, today: str | None = None) -> dict:
    """Clone `parent` into <parent>-WB<n> with exactly one parameter changed. Returns the lineage record."""
    if "=" not in assignment:
        raise ValueError("--set needs <param>=<value>")
    key, raw = assignment.split("=", 1)
    bp = B.extract(parent, with_record=False)
    P = B.params(bp)
    key = resolve(P, key.strip())
    old, new = P[key], _value(key, raw.strip())
    if isinstance(old, tuple):
        old = list(old)
    if isinstance(old, float) and isinstance(new, int) and not isinstance(new, bool):
        new = float(new)
    if new == old:
        raise ValueError(f"{key} is already {old!r}: a variant must change the part")
    mod = bp["module"]
    if key.startswith("cond.") and not mod:
        raise ValueError(f"{parent} has no lab module")
    out_dir = Path(out_dir)
    pdir = out_dir / parent
    new_id = next_id(parent, pdir)
    today = today or date.today().isoformat()

    blk = copy.deepcopy(bp["block"])
    for k in DROP_KEYS:
        blk.pop(k, None)
    src = (ROOT / mod["path"]).read_text() if mod else None
    if key.startswith("cond."):
        c = next(x for x in mod["conds"] + mod["time"] if x["key"] == key)
        src = _splice(src, c["span"], _lit(new, old))
    else:
        blk[key] = new
        if src is not None:          # keep the module's own copy of the same value in step (else it would still bind)
            consts = mod["consts"]
            const = {"window": "WINDOW", "min_adv": "MIN_ADV", "geom": "GEOM"}.get(key)
            if const and consts.get(const) is not None:
                import ast
                node = next(n.value for n in ast.parse(src).body if isinstance(n, ast.Assign)
                            and isinstance(n.targets[0], ast.Name) and n.targets[0].id == const)
                v = tuple(new) if const == "WINDOW" else new
                src = _splice(src, [node.lineno, node.col_offset, node.end_lineno, node.end_col_offset], _lit(v, consts[const]))
    files = {}
    if src is not None:
        mp = pdir / "modules" / f"{new_id}.py"
        mp.parent.mkdir(parents=True, exist_ok=True)
        hdr = (f"# WORKBENCH VARIANT {new_id} (research only, not enabled in any account)\n"
               f"# parent: {parent} ({mod['path']}); changed ONE part: {key} {old!r} -> {new!r}; {today}\n"
               f"# Next: backtest under docs/RESEARCH_RULES.md; testing arena only with the owner's yes. "
               f"Educational only - not financial advice.\n")
        mp.write_text(hdr + src)
        rel = str(mp.relative_to(ROOT)) if mp.is_relative_to(ROOT) else str(mp)
        blk["module"] = rel
        files["module"] = rel
        chk = B.parse_module(mp)
        got = {x["key"]: x["value"] for x in chk["conds"] + chk["time"]}
        want = {k: v for k, v in P.items() if k.startswith("cond.")}
        if key.startswith("cond."):
            want[key] = new
        if got != want:
            raise RuntimeError(f"variant module check failed: {got} != {want}")
    blk["enabled"] = False
    blk["tags"] = ["workbench", f"parent:{parent}"]
    rec = dict(id=new_id, parent=parent, param=key, old=old, new=new, date=today, note=note or "",
               parent_account=bp["account"], status="research only (not enabled in any account)")
    pf = str(blk.get("prefilter") or "")
    if key == "cond.gap" and pf.startswith("gap_"):
        rec["warning"] = f"the config prefilter {pf!r} also limits the gap; it is unchanged (one part only)"
    blk["workbench"] = copy.deepcopy({k: rec[k] for k in ("parent", "param", "old", "new", "date", "note")})
    yp = pdir / f"{new_id}.yaml"
    yp.parent.mkdir(parents=True, exist_ok=True)
    yp.write_text(f"# Workbench variant stub (research only). NOT an account config: no account loads this file.\n"
                  f"# Parent {parent}; one change: {key} {old!r} -> {new!r}. Educational only - not financial advice.\n"
                  + yaml.safe_dump({"strategies": {new_id: blk}}, sort_keys=False))
    files["config"] = str(yp.relative_to(ROOT)) if yp.is_relative_to(ROOT) else str(yp)
    rec["files"] = files
    with open(pdir / "variants.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    rd = pdir / "README.md"
    if not rd.exists():
        rd.write_text(f"# Workbench: {bp['name']} (`{parent}`)\n\n"
                      f"Teardown variants of `{parent}`: each changes ONE part and is a brand-new setup (new id, parent link). "
                      "The original is never edited. Variants are research only until backtested under docs/RESEARCH_RULES.md "
                      "and placed in the testing arena with the owner's yes.\n\n## Log\n\n")
    with open(rd, "a") as f:
        f.write(f"- {today} `{new_id}`: `{key}` {old!r} -> {new!r}" + (f" - {note}" if note else "")
                + ". Status: research only; next: backtest.\n")
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description="Workbench teardown variants (one changed part -> a new research-only setup)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("spawn")
    s.add_argument("setup")
    s.add_argument("--set", required=True, dest="assignment", help="<param>=<value>, exactly one")
    s.add_argument("--note")
    s.add_argument("--out", default=str(WB_DIR))
    ls = sub.add_parser("list")
    ls.add_argument("setup")
    ls.add_argument("--out", default=str(WB_DIR))
    a = ap.parse_args(argv)
    if a.cmd == "spawn":
        r = spawn(a.setup, a.assignment, a.note, a.out)
        print(f"{r['id']}: {r['param']} {r['old']!r} -> {r['new']!r} (research only, not enabled anywhere)")
        if r.get("warning"):
            print(f"  warning: {r['warning']}")
        for k, v in r["files"].items():
            print(f"  {k}: {v}")
    else:
        f = Path(a.out) / a.setup / "variants.jsonl"
        for line in (f.read_text().splitlines() if f.exists() else []):
            r = json.loads(line)
            print(f"{r['date']} {r['id']}: {r['param']} {r['old']!r} -> {r['new']!r} {r.get('note', '')}")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
