"""Render the length grid from results.json as markdown tables (one per setup, train and valid). Educational only."""
import json
import sys
from pathlib import Path

R = json.loads((Path(__file__).resolve().parent / "results.json").read_text())


def cell(m):
    if not m or m.get("n", 0) < 2:
        return f"n{m.get('n', 0) if m else 0}"
    return f"{m['exp_r']:+.3f} n{m['n']} t{m['t']}"


def main(only=None):
    out = []
    by = {}
    for r in R["rows"]:
        by.setdefault(r["candidate"], []).append(r)
    for name, rows in by.items():
        if only and name != only:
            continue
        out += [f"### {name} ({rows[0]['side']} {rows[0]['geom']})", "",
                "| setting | train exp n t | valid exp n t | valid base | valid ex-best-day | plateau valid mean (all+) |",
                "|---|---|---|---|---|---|"]
        for r in sorted(rows, key=lambda r: -(r["valid"].get("exp_r") or -9)):
            s = ",".join(f"{k}{v}" for k, v in r["setting"].items()) + (" **base**" if r["is_base"] else "")
            v = r["valid"]
            out.append(f"| {s} | {cell(r['train'])} | {cell(v)} | {v.get('base', '')} | {v.get('ex_best_day', '')} | "
                       f"{r['plateau_valid_mean']} ({'y' if r['plateau_valid_all_pos'] else 'n'}) |")
        out.append("")
    out += ["### global settings (all candidates pooled, rsis5)", "", "| setting | train exp n t (#cands+) | valid exp n t (#cands+) |", "|---|---|---|"]
    for g in sorted(R["global"], key=lambda g: -g["valid"]["exp_r"]):
        s = ",".join(f"{k}{v}" for k, v in g["setting"].items())
        out.append(f"| {s} | {g['train']['exp_r']:+.3f} n{g['train']['n']} t{g['train']['t']} ({g['train']['n_cands_pos']}/9) | "
                   f"{g['valid']['exp_r']:+.3f} n{g['valid']['n']} t{g['valid']['t']} ({g['valid']['n_cands_pos']}/9) |")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
