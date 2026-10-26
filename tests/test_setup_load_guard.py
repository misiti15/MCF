"""A setup whose module fails to import is skipped, not fatal for the account (2026-10-26 Gen numba crash)."""

from mcf.strategies import setups


def test_bad_module_is_skipped(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("import a_module_that_does_not_exist_xyz\nSIDE = 'long'\nGEOM = 't1s1'\n")
    cfg = {"strategies": {"BAD": {"enabled": True, "type": "lab", "module": str(bad), "window": [950, 1500]},
                          "orb": {"enabled": True}},
           "universe": {}, "exits": {}, "live": {}}
    out = setups.build_strategies(cfg)
    assert [s.name for s in out] == ["orb"]
    assert setups.LOAD_FAILURES and setups.LOAD_FAILURES[0][0] == "BAD"
    assert "ModuleNotFoundError" in setups.LOAD_FAILURES[0][1]
