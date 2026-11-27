"""setup-freeze PR check (mcf/research/setup_freeze.py, OPS-FREEZE inspector 11-27). Educational only - not financial
advice."""

import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from mcf.research import setup_freeze as sf

ROOT = Path(__file__).resolve().parents[1]
NY = sf.NY
DEFAULT = yaml.safe_dump({"strategies": {"orb": {"enabled": True}}, "risk": {"latch_counts_open": False},
                          "account": {"slots": 77}, "costs": {"slippage_bps": 1.0}, "session": {"close": "16:00"},
                          "report": {"x": 1}, "shadow": {"y": 1}})
ACCT = "# header\nstrategies_exclusive: true\nstrategies:\n  orb:\n    enabled: true\n"


def _check(old_files: dict, new_files: dict, changed=()):
    accts = [p for p in set(old_files) | set(new_files) if p.startswith("config/account_")]
    return sf.setup_changes(list(changed), old_files.get, new_files.get, accts)


def _with(base: dict, **edits):
    d = yaml.safe_load(base)
    for k, v in edits.items():
        d[k] = v
    return yaml.safe_dump(d)


def test_unchanged_config_and_comment_only_edits_pass():
    old = {"config/default.yaml": DEFAULT, "config/account_testing.yaml": ACCT, "config/longhold.yaml": "band: 0.0\n"}
    new = dict(old)
    new["config/account_testing.yaml"] = "# a new comment\n" + ACCT.replace("# header", "# header edited")
    new["config/longhold.yaml"] = "# note\nband: 0.0   # same value\n"
    assert _check(old, new, changed=["config/account_testing.yaml", "docs/x.md", "mcf/report/daily_post.py"]) == []


def test_default_yaml_risk_account_costs_session_blocks_are_covered():
    old = {"config/default.yaml": DEFAULT}
    for key, val in [("risk", {"latch_counts_open": True}), ("account", {"slots": 80}),
                     ("costs", {"slippage_bps": 2.0}), ("session", {"close": "13:00"}),
                     ("strategies", {"orb": {"enabled": False}})]:
        assert _check(old, {"config/default.yaml": _with(DEFAULT, **{key: val})}) == [f"config/default.yaml: {key}"]
    # non-trading blocks stay free
    assert _check(old, {"config/default.yaml": _with(DEFAULT, report={"x": 2}, shadow={"y": 2})}) == []


def test_account_files_and_longhold_are_covered():
    old = {"config/default.yaml": DEFAULT, "config/account_testing.yaml": ACCT, "config/longhold.yaml": "band: 0.0\n"}
    moved = dict(old, **{"config/account_testing.yaml": ACCT.replace("enabled: true", "enabled: false")})
    assert _check(old, moved) == ["config/account_testing.yaml"]
    added = dict(old, **{"config/account_new.yaml": ACCT})
    assert _check(old, added) == ["config/account_new.yaml: added"]
    removed = {k: v for k, v in old.items() if k != "config/account_testing.yaml"}
    assert _check(old, removed) == ["config/account_testing.yaml: removed"]
    lh = dict(old, **{"config/longhold.yaml": "band: 0.1\n"})
    assert _check(old, lh) == ["config/longhold.yaml"]


def test_strategy_and_candidate_paths_still_covered():
    same = {"config/default.yaml": DEFAULT}
    r = _check(same, same, changed=["mcf/strategies/beginner_setups.py", "research/heat/candidates/x.json",
                                    "mcf/strategiesX/y.py", "research/heat/other.json"])
    assert r == ["mcf/strategies/beginner_setups.py", "research/heat/candidates/x.json"]


def test_window_is_the_fixed_market_hours_on_weekdays():
    at = lambda d, h, m: datetime(2026, 11, d, h, m, tzinfo=NY)    # noqa: E731
    assert sf.frozen(at(27, 9, 30)) and sf.frozen(at(27, 15, 59))
    assert sf.frozen(at(27, 13, 30))                 # half day (close 13:00): the freeze still runs to 16:00, not loosened
    assert sf.frozen(at(26, 12, 0))                  # weekday holiday: still frozen (no calendar shortcut)
    assert not sf.frozen(at(27, 9, 29)) and not sf.frozen(at(27, 16, 0)) and not sf.frozen(at(27, 21, 40))
    assert not sf.frozen(at(28, 12, 0))              # Saturday


def test_main_on_a_real_git_repo(tmp_path, monkeypatch, capsys):
    def git(*a):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=tmp_path, check=True,
                       capture_output=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "config/default.yaml").write_text(DEFAULT)
    (tmp_path / "config/account_testing.yaml").write_text(ACCT)
    git("init", "-q")
    git("add", "-A")
    git("commit", "-qm", "base")
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True).stdout.strip()
    monkeypatch.chdir(tmp_path)
    assert sf.main(["--base", base]) == 0 and "no setup changes" in capsys.readouterr().out
    (tmp_path / "config/account_testing.yaml").write_text(ACCT.replace("enabled: true", "enabled: false"))
    git("commit", "-qam", "move")
    monkeypatch.setattr(sf, "frozen", lambda now: True)
    assert sf.main(["--base", base]) == 1
    assert "config/account_testing.yaml" in capsys.readouterr().out
    monkeypatch.setattr(sf, "frozen", lambda now: False)       # after hours: allowed
    assert sf.main(["--base", base]) == 0 and "outside market hours: OK" in capsys.readouterr().out


def test_workflow_runs_the_module_on_pull_requests():
    wf = yaml.safe_load((ROOT / ".github/workflows/setup-freeze.yml").read_text())
    assert "pull_request" in wf[True]
    run = wf["jobs"]["check"]["steps"][-1]["run"]
    assert "python3 -m mcf.research.setup_freeze --base" in run and "pull_request.base.sha" in run
    assert wf["jobs"]["check"]["steps"][0]["with"]["fetch-depth"] == 0
    # the real repo's config parses and the current tree has no change against itself
    accts = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "config").glob("account_*.yaml"))
    assert len(accts) >= 5
    read = lambda p: (ROOT / p).read_text() if (ROOT / p).exists() else None    # noqa: E731
    assert sf.setup_changes([], read, read, accts) == []


def test_live_setup_module_files_are_covered():
    """OPS-FREEZE2 (reviewer 11-27): live setups load code from research/... module files named in the configs; an
    edit to one (base or PR side) counts, an unrelated research file does not."""
    acct = ACCT + "  gen1:\n    enabled: true\n    module: research/generator/modules/G1.py\n"
    dflt = _with(DEFAULT, strategies={"x": {"module": "./research/bdi/x.py"}})
    old = {"config/default.yaml": dflt, "config/account_testing.yaml": acct}
    assert _check(old, dict(old), changed=["research/generator/modules/G1.py"]) == ["research/generator/modules/G1.py"]
    assert _check(old, dict(old), changed=["research/bdi/x.py"]) == ["research/bdi/x.py"]
    assert _check(old, dict(old), changed=["research/generator/modules/G2.py", "research/bdi/notes.md"]) == []
    # removed from the config in the same PR: still counts (the base side ran it)
    new = dict(old, **{"config/account_testing.yaml": ACCT})
    assert "research/generator/modules/G1.py" in _check(old, new, changed=["research/generator/modules/G1.py"])
    assert sf.module_paths("a: [1, {module: m.py}]\nb: {c: {module: ''}}\n") == {"m.py"}
    assert sf.module_paths(None) == set() and sf.module_paths(": : bad") == set()


def test_arena_rotation_and_risk_rotation_code_are_covered():
    old = {"config/default.yaml": _with(DEFAULT, arena_rotation={"enabled": True}),
           "docs/live/arena_reps.json": '{"A": 3}'}
    new = dict(old, **{"config/default.yaml": _with(DEFAULT, arena_rotation={"enabled": False}),
                       "docs/live/arena_reps.json": '{"A": 4}'})
    out = _check(old, new)
    assert "config/default.yaml: arena_rotation" in out and "docs/live/arena_reps.json" in out
    assert _check(old, dict(old, **{"docs/live/arena_reps.json": '{ "A" : 3 }\n'})) == []
    assert _check(old, dict(old), changed=["mcf/execution/risk.py", "mcf/rotation.py", "mcf/execution/drill.py"]) \
        == ["mcf/execution/risk.py", "mcf/rotation.py"]


def test_git_errors_are_printed(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert sf._git("show", "deadbeef:nope") == ""
    assert "setup-freeze: git show" in capsys.readouterr().err
