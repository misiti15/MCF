"""Generator Lab summary for the dashboard (owner 2026-10-19): brief updates and trends, not a list of setups.

Rebuilds docs/live/generator_lab.json from every run report (research/generator/runs/*.json), the Setup Generator
account config and the registry. Written by every --apply run; `python -m mcf.research.generator summary` rebuilds it.
Educational only - not financial advice.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "research" / "generator" / "runs"
REGISTRY = ROOT / "research" / "generator" / "registry.jsonl"
OUT = ROOT / "docs" / "live" / "generator_lab.json"
CONFIGS = {"primary": "default.yaml", "testing": "account_testing.yaml", "testing2": "account_testing2.yaml"}


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    return None if not xs else round(xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2, 4)


def build(root: Path = ROOT) -> dict:
    runs = []
    for p in sorted((root / "research" / "generator" / "runs").glob("*.json")):
        r = json.loads(p.read_text())
        picks = r.get("picks") or []
        va = [(x["screen"].get("valid") or {}).get("exp_r") for x in picks]
        runs.append({"date": r["date"], "tried": r.get("n_tried"), "tier1": r.get("n_tier1"), "picked": len(picks),
                     "seeded_from_lab": sum(1 for x in picks if (x.get("screen") or {}).get("seed")),
                     "median_valid_r": _median(va), "best_valid_r": max((v for v in va if v is not None), default=None),
                     "best_t": max(((x["screen"].get("all") or {}).get("t") for x in picks
                                    if (x["screen"].get("all") or {}).get("t") is not None), default=None),
                     "positive_both": sum(1 for x in picks if ((x["screen"].get("train") or {}).get("exp_r") or -1) > 0
                                          and ((x["screen"].get("valid") or {}).get("exp_r") or -1) > 0)})
    gen = yaml.safe_load((root / "config" / "account_gen.yaml").read_text()) or {}
    live = sorted(k for k, v in (gen.get("strategies") or {}).items()
                  if k.startswith("GEN-") and isinstance(v, dict) and v.get("enabled"))
    promoted = {}
    for acct, f in CONFIGS.items():
        cfg = yaml.safe_load((root / "config" / f).read_text()) or {}
        for k, v in (cfg.get("strategies") or {}).items():
            if k.startswith("GEN-") and isinstance(v, dict) and v.get("enabled"):
                promoted.setdefault(k, []).append(acct)
    reg = root / "research" / "generator" / "registry.jsonl"
    n_reg = sum(1 for _ in reg.open()) if reg.exists() else 0
    return {"generated": runs[-1]["date"] if runs else None, "runs": runs[-30:], "specs_screened": n_reg,
            "setups_generated": sum(r["picked"] for r in runs), "live_in_gen": len(live),
            "promoted": [{"setup": k, "accounts": v} for k, v in sorted(promoted.items())],
            "note": "Quick screen on the open history, costs in; not a tested edge. Educational only - not financial advice."}


def write(root: Path = ROOT) -> dict:
    d = build(root)
    (root / "docs" / "live" / "generator_lab.json").write_text(json.dumps(d, indent=1) + "\n")
    return d
