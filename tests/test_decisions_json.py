"""docs/live/decisions.json feeds the dashboard card "Your decisions" (owner 2026-10-22): one hand-maintained list of
owner decisions, refreshed by the nightly brief. Schema guard. Educational only - not financial advice."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = {"code", "title", "what", "recommend", "numbers", "why", "link", "status", "answered"}


def _load():
    return json.loads((ROOT / "docs/live/decisions.json").read_text())


def test_schema():
    d = _load()
    assert isinstance(d, list) and d   # an empty open list is fine: the card says 'No open decisions'
    codes = [x["code"] for x in d]
    assert len(codes) == len(set(codes)), "duplicate decision codes"
    for x in d:
        assert set(x) == KEYS, x.get("code")
        assert re.fullmatch(r"[A-Z][A-Za-z0-9.-]{0,15}", x["code"]), x["code"]
        for k in ("title", "what", "why", "link"):
            assert isinstance(x[k], str) and x[k].strip(), (x["code"], k)
        assert re.match(r"(Yes|No|Optional)\b", x["recommend"]), (x["code"], x["recommend"])
        assert isinstance(x["numbers"], list) and 1 <= len(x["numbers"]) <= 3 and all(isinstance(n, str) and n for n in x["numbers"])
        assert x["status"] in ("open", "answered")
        if x["status"] == "open":
            assert x["answered"] is None, x["code"]
        else:
            assert isinstance(x["answered"], str) and re.search(r"\d{4}-\d{2}-\d{2}", x["answered"]), x["code"]
        if not x["link"].startswith("http"):
            assert (ROOT / x["link"]).exists(), x["link"]          # research notes live in the repo


def test_2026_10_22_state():
    d = {x["code"]: x for x in _load()}
    for k in ("S1", "V1", "P0", "R1", "R2"):   # R1 / R2 answered by the owner ~11:30 ET
        assert d[k]["status"] == "answered" and d[k]["answered"].startswith("yes, 2026-10-22")


def test_card_on_top_of_the_dashboard():
    html = (ROOT / "docs/live/index.html").read_text()
    assert "../live/decisions.json" in html and 'id="dec-card"' in html
    assert html.index('id="glance"') < html.index('id="dec-card"') < html.index('id="live"')   # right under At a glance
    assert "Educational only" in html[html.index('id="dec-card"'):html.index('id="dec-card"') + 3000]
