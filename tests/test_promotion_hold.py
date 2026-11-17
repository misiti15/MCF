"""Promotion hold (owner 2026-11-17, answers PROMO2): no On Deck -> Primary promotions until the owner lifts it;
promotion suggestions still show but are marked 'on hold' (display only). Educational only — not financial advice."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_standing_rule_recorded():
    assert "**Promotion hold (owner 2026-11-17):** no On Deck → Primary promotions" in (ROOT / "CLAUDE.md").read_text()
    led = [json.loads(l) for l in (ROOT / "research" / "ledger.jsonl").read_text().splitlines() if l.strip()]
    e = next(x for x in led if x.get("id") == "2026-11-17-promotion-hold")
    assert e["kind"] == "process" and e["patch"] == {} and "hold off" in e["approved_by"]


def test_dashboard_tags_promo_to_primary_on_hold():
    h = (ROOT / "docs" / "live" / "index.html").read_text()
    assert 'const held = w => w.kind === "up" && w.to === "primary";' in h
    assert '${held(w) ? " · on hold" : ""}' in h and "(on hold)" in h


def test_decisions_answered():
    d = json.loads((ROOT / "docs" / "live" / "decisions.json").read_text())
    for code in ("COMPCAL", "PROMO2", "RULE21-DB"):
        x = next(x for x in d if x.get("code") == code)
        assert x["status"] == "answered" and "2026-11-17" in x["answered"] and "Rule21 yes" in x["answered"]
