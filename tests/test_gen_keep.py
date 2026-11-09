"""Owner rule 2026-10-19: every generated setup goes into the Setup Generator account and stays enabled; none is
deleted, demoted or removed without the owner's consent. Educational only."""
import json
from pathlib import Path

import yaml

# EXPO1109 (owner 2026-11-09, ledger 2026-11-09-expo1109-gen-temp-moves): 5 GEN setups trade TEMPORARILY in Testing 1 / 2
# for the 11-09 / 11-10 sessions and go back to Gen after the 11-10 close; the exemption lapses after 2026-11-10.
import datetime as _dt
EXPO1109 = {"GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long",
            "GEN-261019-03-Ret15mATRlem0p12-FromOpenATRlem0p34-SMA20slopege0p29-PM-BRoplt0p5-t05s1-long",
            "GEN-261026-02-VolRatioge2-SMA20dlem0p58-BarsSinceLODle1-LATE-BRoplt0p35-t1s1-long",
            "GEN-261022-07-Z12lem1p9-FlowShiftlem0p96-ATRdge3p6-AM-BRopgt0p5-t1s1-short",
            "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short"} \
    if _dt.date.today() <= _dt.date(2026, 11, 10) else set()

ROOT = Path(__file__).resolve().parents[1]


def test_every_generated_setup_is_in_the_gen_account_and_enabled():
    picked = set()
    for line in (ROOT / "research/generator/registry.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("name"):
            picked.add(r["name"])
    strat = (yaml.safe_load((ROOT / "config/account_gen.yaml").read_text()) or {}).get("strategies") or {}
    missing = sorted(n for n in picked if n not in strat)
    disabled = sorted(n for n in picked if n in strat and not (strat[n] or {}).get("enabled") and n not in EXPO1109)
    assert picked, "registry has no generated setups"
    assert not missing, f"generated setups missing from the gen account (owner consent needed): {missing}"
    assert not disabled, f"generated setups disabled in the gen account (owner consent needed): {disabled}"
