"""WW-PROTECT (owner 2026-11-20): the protected list in docs/PROTECTED.md is an evidence gate, not a freeze. Any ledger
entry dated 2026-11-21 or later that touches a protected item (config key / setup name in its patch keys, title, moves
or setups; a listed term in its title) must carry protected_ids, guard_evidence (an existing path) and owner_approval.
Educational only - not financial advice."""
import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "PROTECTED.md"
LEDGER = ROOT / "research" / "ledger.jsonl"
GATE_FROM = "2026-11-21"


def _cells(v: str) -> list[str]:
    return re.findall(r"`([^`]+)`", v)


def protected() -> dict[str, dict]:
    """PROT id -> {keys, setups, row} from the docs/PROTECTED.md table."""
    out = {}
    for line in DOC.read_text().splitlines():
        if not line.startswith("| PROT-"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        out[c[0]] = {"area": c[1], "keys": _cells(c[3]), "setups": _cells(c[4]), "strength": c[5], "guard": c[6]}
    return out


def _entries() -> list[dict]:
    return [json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()]


def _wb(tok: str) -> str:
    return rf"(?<![\w-]){re.escape(tok)}(?![\w-])"


def _patch_paths(e: dict) -> list[str]:
    return [re.sub(r"\s*\(.*$", "", str(k)).strip() for k in (e.get("patch") or {})]


def touches(e: dict, item: dict) -> list[str]:
    """What in ledger entry `e` touches the protected item (empty = untouched)."""
    title = str(e.get("title") or "")
    paths = _patch_paths(e)
    hits = []
    for k in item["keys"]:
        if "." in k:
            leaf = k.rsplit(".", 1)[1]
            if any(p == k or p.startswith(k + ".") for p in paths) or re.search(_wb(k), title) or (
                    "_" in leaf and re.search(_wb(leaf), title)):
                hits.append(k)
        elif "_" in k:
            if any(k in p.split(".") for p in paths) or re.search(_wb(k), title):
                hits.append(k)
        elif re.search(_wb(k), title, flags=re.I):
            hits.append(k)
    text = [title, *map(str, (e.get("patch") or {})), *map(str, e.get("moves") or []),
            *map(str, (e.get("setups") or {}) if isinstance(e.get("setups"), dict) else (e.get("setups") or []))]
    for s in item["setups"]:
        if any(re.search(_wb(s), t) for t in text):
            hits.append(s)
    return hits


def missing(e: dict, prot: dict) -> list[str]:
    """Gate failures for one entry (empty = passes)."""
    if str(e.get("date") or "") < GATE_FROM:
        return []
    hit = {pid for pid, it in prot.items() if touches(e, it)}
    if not hit:
        return []
    bad = []
    ids = set(e.get("protected_ids") or [])
    if not hit <= ids:
        bad.append(f"protected_ids lacks {sorted(hit - ids)}")
    ev = e.get("guard_evidence")
    paths = [ev] if isinstance(ev, str) else list(ev or [])
    if not paths or not all((ROOT / str(p)).exists() for p in paths):
        bad.append("guard_evidence missing or not a path in the repo")
    if not str(e.get("owner_approval") or "").strip():
        bad.append("owner_approval missing")
    return bad


# ------------------------------------------------------------------------------------------------- the list itself
def test_list_matches_whatworks_report():
    prot = protected()
    rep = (ROOT / "research/whatworks_1120/REPORT.md").read_text()
    sec = rep[rep.index("## 2. Protected list"):]
    n = len(re.findall(r"^\| \d+ \|", sec[:sec.index("\n---")], flags=re.M))
    assert n == 32 and list(prot) == [f"PROT-{i:02d}" for i in range(1, n + 1)]
    for pid, it in prot.items():
        assert it["keys"] or it["setups"], pid
        assert it["strength"] and it["guard"], pid
    assert "Educational only" in DOC.read_text() and "not a\nfreeze" in DOC.read_text()


def test_listed_config_keys_exist():
    """Every dotted config key in the list exists in config/default.yaml or is read by the code with a default (a renamed
    key would silently drop out of the gate)."""
    cfg = yaml.safe_load((ROOT / "config/default.yaml").read_text())
    code = "\n".join(p.read_text() for p in (ROOT / "mcf").rglob("*.py"))
    for it in protected().values():
        for k in it["keys"]:
            if "." not in k or k.split(".")[0] not in cfg:
                continue
            d, ok = cfg, True
            for part in k.split("."):
                if not (isinstance(d, dict) and part in d):
                    ok = False
                    break
                d = d[part]
            assert ok or f'"{k.rsplit(".", 1)[1]}"' in code, k


def test_listed_setups_exist():
    names = (ROOT / "config/default.yaml").read_text()
    for it in protected().values():
        for s in it["setups"]:
            assert re.search(rf"^  {re.escape(s)}:", names, flags=re.M), s


# ------------------------------------------------------------------------------------------------------ the gate
def test_ledger_entries_after_gate_carry_protection_fields():
    prot = protected()
    bad = {e["id"]: m for e in _entries() if (m := missing(e, prot))}
    assert not bad, bad


@pytest.mark.parametrize("entry,ids", [
    ({"title": "raise spread cap", "patch": {"live.max_spread_bps (testingd)": [30, 40]}}, {"PROT-19"}),
    ({"title": "x", "patch": {"strategies.L3-gap-slope-fromopen-FD.window": [[950, 1500], [950, 1300]]}},
     {"PROT-06", "PROT-07", "PROT-08", "PROT-09", "PROT-30"}),
    ({"title": "new WB copy", "patch": {"strategies.L3-gap-slope-fromopen-FD-WB9 (testingd)": [None, "added"]}}, set()),
    ({"title": "change the C3-BAR2 best-day share", "patch": {}}, {"PROT-14"}),
    ({"title": "tighten max_stop_cost_r", "patch": {"max_stop_cost_r (testingd)": [0.15, 0.10]}},
     {"PROT-10", "PROT-22", "PROT-32"}),
    ({"title": "move", "patch": {}, "moves": ["NM-ETF-late-dip-di-long: Primary -> Testing D"]}, {"PROT-29"}),
    ({"title": "Testing-arena rotation block", "patch": {"strategies.GEN-1 (testingd)": [None, "added"]}}, set()),
])
def test_matching(entry, ids):
    prot = protected()
    assert {pid for pid, it in prot.items() if touches(entry, it)} == ids


def test_gate_requires_fields_only_from_1121():
    prot = protected()
    e = {"id": "x", "date": "2026-11-21", "title": "raise", "patch": {"live.max_spread_bps": [30, 40]}}
    assert len(missing(e, prot)) == 3
    assert missing({**e, "date": "2026-11-20"}, prot) == []
    ok = {**e, "protected_ids": ["PROT-19"], "guard_evidence": "research/whatworks_1120/REPORT.md",
          "owner_approval": "owner 2026-11-28 (chat)"}
    assert missing(ok, prot) == []
    assert missing({**ok, "guard_evidence": "no/such/file.md"}, prot)
    assert missing({**ok, "protected_ids": ["PROT-01"]}, prot)
    untouched = {"id": "y", "date": "2026-11-30", "title": "dashboard colour", "patch": {"docs/live/index.html": [0, 1]}}
    assert missing(untouched, prot) == []
