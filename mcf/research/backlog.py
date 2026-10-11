"""Strategy backlog: every setup / strategy idea in one list, re-tested on all collected data until it passes or fails.

Owner rule (2026-10-06): housekeeping fixes ship right away; setup and strategy ideas never go straight in. They are
added to research/backlog.jsonl, backtested continuously as data accumulates, and proposed for implementation only
after passing the pre-declared gates below. Approved changes then go in research/ledger.jsonl (conflict-checked).

Entry (one JSON object per line):
  {"id", "title", "added", "source", "category": "setup|exit|strategy|risk", "hypothesis",
   "module": "research.reddit_bt.t2_orb15" | null, "variant": "<name in module.VARIANTS>" | null,
   "status": "idea|coded|testing|failed|rework|finalist|forward_wait|holdout_passed|holdout_failed|probation|proposed|live|retired",
   "notes", optional: "parent" (id it was reworked from), "holdout_burned" (true when an ancestor already used the
   locked holdouts), "configs_tried" (cumulative across the whole lineage)}

Pre-declared gates (never changed to fit a candidate):
  finalist        train and valid both exp_r > 0 after costs, valid n >= 30, valid day-clustered t >= 1.5
  holdout_passed  each exact version is scored ONCE on each locked holdout (test, q2): exp_r > 0 and t >= the bar
                  on both. Owner rule (2026-10-06): a REWORKED version may be scored on the holdouts again, but
                  every extra look by the same lineage raises the bar, because each look leaks a little of the
                  holdout into the choice: look 1 t >= 1.0, look 2 >= 1.5, look 3 >= 2.0, look 4 >= 2.5; after 4
                  looks the lineage can only be judged on forward data (forward_wait).
  probation       a version that passes on look 2+ goes to paper as "probation" (labelled as a holdout re-look),
                  and is confirmed or retired automatically on forward data (>= 20 sessions, >= 60 trades)
  plateau         if the module defines NEIGHBORS = {variant: [nearby variant names]} (one parameter one step away),
                  their mean valid exp_r must also be > 0: a plateau, not a lone spike
  forward_wait    a lineage that has used its 4 holdout looks must pass on sessions collected after it was frozen:
                  >= 20 sessions, >= 60 trades, exp_r > 0, t >= 1.0
  forward         after registration every candidate keeps being scored on new sessions (> 2026-10-05) as they
                  arrive; frozen rules, monitoring only. A live setup whose forward exp_r falls below 0 over
                  >= 100 trades is flagged for review.

    python -m mcf.research.backlog list
    python -m mcf.research.backlog run [--id ID]      # module entries: train / valid / forward (reddit_bt);
                                                      # lab_module entries: re-test on the 1-minute cache (below)
    python -m mcf.research.backlog holdout ID         # locked-holdout scoring: once per version, <= 4 looks per lineage
Lab entries (`lab_module`: path to a lab module with SIDE, GEOM, mask(df); optional `lab_window`, `lab_min_adv`,
`approved`) are scored by mcf/research/backlog_lab.py on data/cache/1Min (open / forward data, 2026-06-15 on) with the
research pipeline and production + time-of-day costs: n, win rate, exp R, day-clustered t, up / down sessions, and the
same after the approval date (split "lab_cache"; monitoring only, no status change). `run` exits 1 when runnable
entries exist and none could be scored.
Results append to research/backlog_results.jsonl; research/BACKLOG.md is regenerated on every command.
Educational only — not financial advice.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKLOG = ROOT / "research" / "backlog.jsonl"
RESULTS = ROOT / "research" / "backlog_results.jsonl"
REPORT = ROOT / "research" / "BACKLOG.md"
RUNNABLE = {"coded", "testing", "rework", "finalist", "forward_wait", "holdout_passed", "probation", "proposed", "live"}
MAX_LOOKS = 4
GATE = {"finalist_valid_n": 30, "finalist_valid_t": 1.5, "holdout_t": 1.0, "forward_review_n": 100,
        "forward_sessions": 20, "forward_n": 60, "forward_t": 1.0}


def entries() -> list[dict]:
    return [json.loads(l) for l in BACKLOG.read_text().splitlines() if l.strip()] if BACKLOG.exists() else []


def save(es: list[dict]) -> None:
    BACKLOG.write_text("".join(json.dumps(e) + "\n" for e in es))


def results() -> list[dict]:
    return [json.loads(l) for l in RESULTS.read_text().splitlines() if l.strip()] if RESULTS.exists() else []


def _score(e: dict, split: str, variant: str | None = None) -> dict:
    from research.reddit_bt import common

    mod = importlib.import_module(e["module"])
    uni = mod.UNIVERSE
    if uni == "top300":
        uni = (ROOT / "research" / "reddit_bt" / "top300.txt").read_text().split()
    m = common.run(mod.signals, mod.VARIANTS[variant or e["variant"]], split, universe=uni)
    m.pop("_rows", None)
    return m


def _record(e: dict, split: str, m: dict) -> None:
    row = {"id": e["id"], "run_date": str(date.today()), "split": split, "metrics": m}
    with RESULTS.open("a") as f:
        f.write(json.dumps(row, default=str) + "\n")


def _passes(m: dict, n_min: int, t_min: float) -> bool:
    return m.get("n", 0) >= n_min and m.get("exp_r", -1) > 0 and (m.get("t_day_clustered") or 0) >= t_min


def _run_module(e: dict, es: list[dict]) -> None:
    """Old research/reddit_bt path: train / valid / forward splits and the status gates (entries with `module`)."""
    got = {}
    for split in ("train", "valid", "forward"):
        m = _score(e, split)
        if split == "forward" and not m.get("n"):
            continue
        _record(e, split, m)
        got[split] = m
        print(e["id"], split, {k: m.get(k) for k in ("n", "win_rate", "exp_r", "t_day_clustered")})
    if e["status"] in ("coded", "testing", "rework"):
        ok = got["train"].get("exp_r", -1) > 0 and _passes(got["valid"], GATE["finalist_valid_n"], GATE["finalist_valid_t"])
        nb = getattr(importlib.import_module(e["module"]), "NEIGHBORS", {}).get(e["variant"], [])
        if ok and nb:
            vals = [_score(e, "valid", v).get("exp_r", -1) for v in nb]
            e["plateau_valid_exp_r"] = round(sum(vals) / len(vals), 4)
            ok = e["plateau_valid_exp_r"] > 0
        e["status"] = ("finalist" if holdout_looks(e, es) < MAX_LOOKS else "forward_wait") if ok else "failed"
    if e["status"] in ("forward_wait", "probation"):
        f = got.get("forward", {})
        if f.get("days", 0) >= GATE["forward_sessions"] and f.get("n", 0) >= GATE["forward_n"]:
            good = _passes(f, GATE["forward_n"], GATE["forward_t"])
            e["status"] = ("live" if e["status"] == "probation" else "proposed") if good else \
                ("retired" if e["status"] == "probation" else "failed")
    f = got.get("forward", {})
    if e["status"] == "live" and f.get("n", 0) >= GATE["forward_review_n"] and f.get("exp_r", 0) < 0:
        e["notes"] = (e.get("notes", "") + f" | {date.today()}: FLAG forward exp_r {f['exp_r']} over {f['n']} trades").strip(" |")


def _summary(lines: list[str]) -> None:
    """Print, and append to the GitHub job summary when running in Actions."""
    print("\n".join(lines))
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a") as f:
            f.write("\n".join(["### Backlog re-test", ""] + [f"- {x}" for x in lines]) + "\n")


def run(only: str | None = None, cache: str | Path | None = None, workers: int | None = None) -> int:
    """Re-test every runnable entry. `module` entries: the old reddit_bt splits and gates. `lab_module` entries:
    the lab pipeline on the 1-minute cache (mcf/research/backlog_lab.py; split "lab_cache", monitoring only).
    Prints how many entries were scored / skipped and why. Returns 1 when runnable entries exist but none was scored."""
    from . import backlog_lab as BL

    t0 = time.time()
    es = entries()
    runnable = [e for e in es if e["status"] in RUNNABLE and (not only or e["id"] == only)]
    scored, skipped, specs = [], {}, []
    for e in runnable:
        if e.get("module"):
            try:
                _run_module(e, es)
                scored.append(e["id"])
            except Exception as ex:                   # noqa: BLE001 - reported, never silent
                skipped[e["id"]] = f"module scoring failed: {type(ex).__name__}: {ex}"
        elif e.get("lab_module"):
            try:
                specs.append(BL.spec_for(e))
            except Exception as ex:                   # noqa: BLE001
                skipped[e["id"]] = f"lab module unusable: {type(ex).__name__}: {ex}"
        else:
            skipped[e["id"]] = "no module / lab_module (not coded as a lab setup)"
    info = {}
    if specs:
        res, errors, info = BL.score(specs, cache or BL.CACHE, workers=workers)
        for s in specs:
            if s["id"] in res:
                m = res[s["id"]]
                _record({"id": s["id"]}, "lab_cache", m)
                scored.append(s["id"])
                fw = m.get("forward", {})
                print(f"{s['id']:<44} n {m.get('n', 0):>5} win {m.get('win_rate')} exp {m.get('exp_r')} t {m.get('t_day_clustered')}"
                      f" | up {m['up'].get('exp_r')} ({m['up'].get('n')}) down {m['down'].get('exp_r')} ({m['down'].get('n')})"
                      f" | since {fw.get('since')}: n {fw.get('n', 0)} exp {fw.get('exp_r')} t {fw.get('t_day_clustered')}")
            elif s["id"] in errors:
                skipped[s["id"]] = errors[s["id"]]
            else:
                skipped[s["id"]] = f"no bars in the cache ({info.get('cache')}: {info.get('symbols', 0)} symbols)"
        if errors.get("_symbols"):
            print(f"WARNING: {len(errors['_symbols'])} symbol files failed to load, first: {errors['_symbols'][0]}")
    save(es)
    report()
    lines = [f"runnable entries: {len(runnable)} · scored: {len(scored)} · skipped: {len(skipped)} · {time.time() - t0:.0f}s"]
    if info.get("sessions"):
        lines.append(f"lab cache: {info['symbols']} symbols, {info['sessions']} sessions {info['first']}..{info['last']} "
                     f"(locked block 2024-11-01..2025-02-28 excluded)")
    reasons: dict[str, list[str]] = {}
    for i, why in skipped.items():
        reasons.setdefault(why, []).append(i)
    for why, ids in sorted(reasons.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"skipped {len(ids)}: {why} -> {', '.join(ids[:12])}{' ...' if len(ids) > 12 else ''}")
    _summary(lines)
    if runnable and not scored:
        print("ERROR: runnable backlog entries exist but none was scored", file=sys.stderr)
        return 1
    return 0


def _root(e: dict, by_id: dict) -> str:
    while e.get("parent") in by_id:
        e = by_id[e["parent"]]
    return e["id"]


def holdout_looks(e: dict, es: list[dict]) -> int:
    """Holdout looks already used by e's lineage (every version sharing its root, including e itself).
    A legacy holdout_burned flag counts as one look when no scoring of it was recorded here."""
    by_id = {x["id"]: x for x in es}
    root = _root(e, by_id)
    lineage = [x for x in es if _root(x, by_id) == root]
    scored = {r["id"] for r in results() if r["split"] in ("test", "q2")}
    looks = sum(1 for x in lineage if x["id"] in scored)
    if looks == 0 and any(x.get("holdout_burned") for x in lineage):
        looks = 1
    return looks


def holdout(eid: str) -> None:
    es = entries()
    e = next(x for x in es if x["id"] == eid)
    if any(r["id"] == eid and r["split"] in ("test", "q2") for r in results()):
        raise SystemExit(f"{eid} was already scored on the locked holdouts; each version is scored once")
    if e["status"] != "finalist":
        raise SystemExit(f"{eid} is '{e['status']}'; only finalists are scored on the holdouts")
    look = holdout_looks(e, es) + 1
    if look > MAX_LOOKS:
        raise SystemExit(f"{eid}: its lineage has used all {MAX_LOOKS} holdout looks; forward data only")
    bar = GATE["holdout_t"] + 0.5 * (look - 1)
    os.environ["MCF_RBT_ALLOW_HOLDOUT"] = "1"
    try:
        ms = {s: _score(e, s) for s in ("test", "q2")}
    finally:
        os.environ.pop("MCF_RBT_ALLOW_HOLDOUT", None)
    for s, m in ms.items():
        m["holdout_look"], m["t_required"] = look, bar
        _record(e, s, m)
        print(eid, s, f"look {look} (t >= {bar})", {k: m.get(k) for k in ("n", "win_rate", "exp_r", "t_day_clustered")})
    passed = all(_passes(m, 1, bar) for m in ms.values())
    e["holdout_look"] = look
    e["status"] = ("holdout_passed" if look == 1 else "probation") if passed else "holdout_failed"
    save(es)
    report()


def _lab_cell(e: dict, last: dict) -> str:
    r = last.get((e["id"], "lab_cache"))
    if not r:
        return "–"
    m = r["metrics"]
    f = lambda x: "–" if x is None else f"{x:+.3f}"
    out = f"{f(m.get('exp_r'))}R n{m.get('n', 0)} t{m.get('t_day_clustered')} ({m.get('sample', '')}; up {f(m.get('up', {}).get('exp_r'))} / dn {f(m.get('down', {}).get('exp_r'))})"
    fw = m.get("forward")
    if fw:
        out += f" · since {fw['since']}: {f(fw.get('exp_r'))}R n{fw.get('n', 0)} t{fw.get('t_day_clustered')}"
        if e.get("status") == "live" and fw.get("n", 0) >= GATE["forward_review_n"] and (fw.get("exp_r") or 0) < 0:
            out += " **FLAG**"
    return out + f" [{r.get('run_date')}]"


def report() -> None:
    last: dict[tuple, dict] = {}
    for r in results():
        last[(r["id"], r["split"])] = r
    cell = lambda e, s: (lambda m: "–" if not m else f"{m.get('exp_r', 0):+.3f}R n{m.get('n', 0)} t{m.get('t_day_clustered')}")(
        last.get((e["id"], s), {}).get("metrics"))
    order = ["live", "probation", "proposed", "holdout_passed", "finalist", "forward_wait", "rework", "testing", "coded", "idea",
             "holdout_failed", "failed", "retired"]
    es = sorted(entries(), key=lambda e: order.index(e["status"]) if e["status"] in order else 99)
    lines = ["# Strategy backlog", "", "*Educational only — not financial advice. Generated by `python -m mcf.research.backlog`.*", "",
             "Every setup / strategy idea lives here until it passes the pre-declared gates (see mcf/research/backlog.py) "
             "or fails. Costs are always in; holdouts are scored once; failures stay listed.", "",
             f"Total ideas: {len(es)} · coded: {sum(1 for e in es if e.get('module') or e.get('lab_module'))} · "
             f"failed: {sum(1 for e in es if e['status'] in ('failed', 'holdout_failed'))} · "
             f"configurations tried (all lineages): {sum(e.get('configs_tried') or 0 for e in es)}", "",
             "A failed idea is reworked (parameter neighbourhood, swapped indicator lengths, one condition added or removed, "
             "paired tweaks) before it is dropped; reworked versions may be scored on the locked holdouts again, with a higher bar for each extra look "
             "(t >= 1.0 / 1.5 / 2.0 / 2.5, max 4 per lineage); a pass on a re-look goes to paper as probation and is "
             "confirmed or retired on forward data.", "",
             "Forward re-test: lab entries scored weekly on the 1-minute research cache (open data since 2026-06-15, production "
             "+ time-of-day costs): exp R, n, day-clustered t on the whole cache, up / down sessions, and the same after the "
             "entry's approval date (the true forward sample). FLAG = live with forward exp < 0 over >= "
             f"{GATE['forward_review_n']} trades.", "",
             "| Status | ID | Idea | Source | Train | Valid | Test (once) | Q2 (once) | Forward | Forward re-test |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for e in es:
        lines.append(f"| {e['status']} | {e['id']} | {e['title']} | {e.get('source', '')} | {cell(e, 'train')} | {cell(e, 'valid')} | "
                     f"{cell(e, 'test')} | {cell(e, 'q2')} | {cell(e, 'forward')} | {_lab_cell(e, last)} |")
    REPORT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "run", "holdout", "report"])
    ap.add_argument("id", nargs="?")
    ap.add_argument("--id", dest="only")
    ap.add_argument("--cache", help="research bar cache root (default data/cache; reads <cache>/1Min)")
    ap.add_argument("--workers", type=int, help="processes for the lab re-test (default min(4, CPUs))")
    a = ap.parse_args()
    if a.cmd == "list":
        for e in entries():
            print(f"{e['status']:<15} {e['id']:<28} {e['title']}")
    elif a.cmd == "run":
        sys.exit(run(a.only or a.id, a.cache, a.workers))
    elif a.cmd == "holdout":
        holdout(a.id)
    else:
        report()
