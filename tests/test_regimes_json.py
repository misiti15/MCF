"""docs/live/regimes.json schema (research/bdi/regime1022; dashboard "Best conditions" column). Educational only - not
financial advice."""
import json

from mcf.report.regimes import PATH, validate


def test_regimes_json_valid():
    d = json.loads(PATH.read_text())
    assert validate(d) == []
    assert d["setups"]


def test_validator_catches_bad_rows():
    d = json.loads(PATH.read_text())
    name = next(iter(d["setups"]))
    bad = json.loads(json.dumps(d))
    bad["setups"][name]["best"] = "Sunny"
    assert validate(bad)
    bad = json.loads(json.dumps(d))
    del bad["setups"][name]["by_regime"]["Quiet"]
    assert validate(bad)


def test_regx_hindsight_label_and_reliability_tags():
    # REGX (owner yes 2026-11-21, display only): hindsight label + trustworthy / weak / false tag per rated setup
    from collections import Counter
    from pathlib import Path

    from mcf.report.regimes import HINDSIGHT
    d = json.loads(PATH.read_text())
    assert d["hindsight"] == HINDSIGHT == "hindsight (known at close)"
    v = Counter(s["regx"]["verdict"] for s in d["setups"].values() if "regx" in s)
    assert v == {"trustworthy": 15, "weak": 11, "false": 6}            # research/bdi/regx/NOTES.md: 32 in scope
    assert d["setups"]["L3-gap-slope-fromopen-FD"]["regx"]["verdict"] == "false"
    bad = json.loads(json.dumps(d))
    bad["setups"]["L3-gap-slope-fromopen-FD"]["regx"]["verdict"] = "great"
    assert validate(bad)
    html = (Path(PATH).parent / "index.html").read_text()
    assert "hindsight (known at close)" in html and "x.rg.regx" in html and "rg.regx" in html
