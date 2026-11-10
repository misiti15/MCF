"""Owner rule 2026-10-19: every generated setup goes into the Setup Generator account and stays enabled; none is
deleted, demoted or removed without the owner's consent. Educational only."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_every_generated_setup_is_in_the_gen_account_and_enabled():
    picked = set()
    for line in (ROOT / "research/generator/registry.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("name"):
            picked.add(r["name"])
    strat = (yaml.safe_load((ROOT / "config/account_gen.yaml").read_text()) or {}).get("strategies") or {}
    missing = sorted(n for n in picked if n not in strat)
    disabled = sorted(n for n in picked if n in strat and not (strat[n] or {}).get("enabled"))
    assert picked, "registry has no generated setups"
    assert not missing, f"generated setups missing from the gen account (owner consent needed): {missing}"
    assert not disabled, f"generated setups disabled in the gen account (owner consent needed): {disabled}"
