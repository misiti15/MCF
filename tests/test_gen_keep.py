"""Owner rule 2026-10-19: every generated setup goes into the Setup Generator account and stays enabled; none is
deleted, demoted or removed without the owner's consent. GEN-GRAD (owner 2026-11-11): a graduate stays listed in the gen
account (switched off there) and runs enabled in exactly one testing area. Educational only."""
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
    grads = set()
    for a in ("testing2", "explore1", "livelab", "testingd", "testinge", "testingf"):   # arena A-F (owner 2026-11-12)
        p = ROOT / f"config/account_{a}.yaml"
        if p.exists():
            grads |= {k for k, v in ((yaml.safe_load(p.read_text()) or {}).get("strategies") or {}).items()
                      if k.startswith("GEN-") and (v or {}).get("enabled")}
    # C3-EXIT100 (owner yes 2026-11-18): persistent losers keep trading in the Graveyard (tag "C3-EXIT100")
    gy = (yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text()) or {}).get("strategies") or {}
    # FOOTRACE-EXIT (owner FOOTRACE 2026-11-19, covers the Setup Generator; Friday review 2026-11-20): tag "FOOTRACE-EXIT"
    grads |= {k for k, v in gy.items() if (v or {}).get("enabled")
              and any("C3-EXIT100" in str(t) or "FOOTRACE-EXIT" in str(t) or "GYH V1" in str(t) for t in (v or {}).get("tags") or [])}
    # GYH V1+V3 (owner 2026-11-25): floor moves tagged "GYH V1"; Graveyard archives (archived marker, owner consent) count too
    grads |= {k for k, v in gy.items() if isinstance((v or {}).get("archived"), dict) or isinstance((v or {}).get("retired"), dict)}
    disabled = sorted(n for n in picked if n in strat and not (strat[n] or {}).get("enabled") and n not in grads)
    assert picked, "registry has no generated setups"
    assert not missing, f"generated setups missing from the gen account (owner consent needed): {missing}"
    assert not disabled, f"generated setups disabled in the gen account (owner consent needed): {disabled}"


def test_graduates_show_on_the_main_leaderboard(monkeypatch):
    """GEN-GRAD (owner 2026-11-11): a graduate's rows from a testing account are a testing-area record (main leaderboard),
    while GEN rows from the gen account stay on the generated board only."""
    from mcf.report import daily_post as P

    def row(s, day="2026-11-12"):
        return {"setup": s, "name": s, "trades": 2, "n_win": 2, "win_rate": 1.0, "avg_r": 0.5, "total_r": 1.0, "pnl": 10.0,
                "days": [day], "sessions_traded": 1, "daily": [[day, 2, 1.0, 10.0]]}

    sc = {"mcf-data-testingd": [row("GEN-1"), row("X-SETUP")], "mcf-data-gen": [row("GEN-2")]}
    monkeypatch.setattr(P, "_show", lambda br, path: {"leaderboard": sc.get(br, [])} if path == "reports/scorecard.json" else None)
    monkeypatch.setattr(P, "_local", lambda p: {"setups": {"GEN-1": {"accounts": ["testingd"], "from": ["gen"]},
                                                           "X-SETUP": {"accounts": ["testingd"]},
                                                           "GEN-2": {"accounts": ["gen"]}}} if p.endswith("assignments.json") else None)
    monkeypatch.setattr(P, "_journal", lambda br: None)
    main = {x["setup"] for x in P.leaderboard("2026-11-12")}
    assert {"GEN-1", "X-SETUP"} <= main and "GEN-2" not in main
    assert {x["setup"] for x in P.leaderboard("2026-11-12", gen=True)} == {"GEN-2"}
    html = (ROOT / "docs/live/index.html").read_text()
    assert "!isGen(r.setup) || grad(r.setup)" in html
