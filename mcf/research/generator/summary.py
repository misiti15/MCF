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


def expected_live(root: Path, on: dict, live: list) -> dict:
    """GX5 (owner 2026-10-26): per enabled GEN setup, the 2-year screen per_day next to a realistic expected live
    trades/day (mcf/research/generator/expect.py). Sources, newest last wins: the backfill
    research/generator/expected_live.json, then each run report's `expected_live` (every run refreshes all setups)."""
    from .expect import basis, set_total

    got: dict = {}
    bf = root / "research" / "generator" / "expected_live.json"
    if bf.exists():
        got.update(json.loads(bf.read_text()).get("setups") or {})
    for p in sorted((root / "research" / "generator" / "runs").glob("*.json")):
        got.update(json.loads(p.read_text()).get("expected_live") or {})
    setups = {}
    for k in sorted(on):
        e = dict(got.get(k) or {})
        e["per_day"] = (((on[k].get("gen") or {}).get("screen") or {}).get("per_day")
                        if e.get("per_day") is None else e["per_day"])
        if e.get("per_day") is None and e.get("expected_live_per_day") is None:
            continue
        setups[k] = {"screen_per_day": e.get("per_day"), "per_day_median60": e.get("per_day_median60"),
                     "per_day_mean60": e.get("per_day_mean60"), "recent_window": e.get("recent_window"),
                     "expected_live_per_day": e.get("expected_live_per_day"),
                     "expected_live_mean_basis": e.get("expected_live_mean_basis")}

    def tot(f):
        xs = [setups[k][f] for k in live if k in setups and setups[k][f] is not None]
        return round(sum(xs), 1) if xs else None
    st = set_total([got[k] for k in live if k in got])
    return {"setups": setups, "live_screen_per_day_total": tot("screen_per_day"),
            # set level: median of the live setups' daily TOTAL x factor (the per-setup medians understate a set of
            # sparse, regime-gated setups; their sum is kept for reference)
            "live_expected_per_day_total": st["expected_live_per_day"] if st else tot("expected_live_per_day"),
            "live_set": st, "live_sum_of_setup_expected": tot("expected_live_per_day"),
            "live_sum_of_setup_mean_basis": tot("expected_live_mean_basis"), "basis": basis()}


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
    on = {k: v for k, v in (gen.get("strategies") or {}).items()
          if k.startswith("GEN-") and isinstance(v, dict) and v.get("enabled")}
    # hand-added observation setups (owner 2026-10-23, pod1022: tag `observation`) run in the Gen account but were not
    # produced by the generator, so they are counted apart from the generated ones
    obs = sorted(k for k, v in on.items() if "observation" in (v.get("tags") or []))
    live = sorted(k for k in on if k not in obs)
    promoted = {}
    for acct, f in CONFIGS.items():
        cfg = yaml.safe_load((root / "config" / f).read_text()) or {}
        for k, v in (cfg.get("strategies") or {}).items():
            if k.startswith("GEN-") and isinstance(v, dict) and v.get("enabled"):
                promoted.setdefault(k, []).append(acct)
    reg = root / "research" / "generator" / "registry.jsonl"
    n_reg = sum(1 for _ in reg.open()) if reg.exists() else 0
    return {"generated": runs[-1]["date"] if runs else None, "runs": runs[-30:], "specs_screened": n_reg,
            "setups_generated": sum(r["picked"] for r in runs), "live_in_gen": len(live), "observation_in_gen": len(obs),
            "promoted": [{"setup": k, "accounts": v} for k, v in sorted(promoted.items())],
            "expected_live": expected_live(root, on, live),
            "note": "Quick screen on the open history, costs in; not a tested edge. Educational only - not financial advice."}


def write(root: Path = ROOT) -> dict:
    d = build(root)
    (root / "docs" / "live" / "generator_lab.json").write_text(json.dumps(d, indent=1) + "\n")
    return d
