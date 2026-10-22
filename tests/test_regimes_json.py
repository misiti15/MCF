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
