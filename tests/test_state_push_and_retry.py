"""Housekeeping 2026-10-19: the state push must survive a rejected push on a runner with no git identity, and the
broker retries read-only calls on a dropped connection (never orders). Educational only."""
import subprocess

import pytest
import requests

from mcf.execution.alpaca_broker import _RetryGets
from mcf.execution import session as S


def _git(cwd, *a, env=None):
    subprocess.run(["git", "-C", str(cwd), *a], check=True, capture_output=True, env=env)


def test_push_rebases_without_global_identity(tmp_path, monkeypatch):
    ident = ["-c", "user.name=t", "-c", "user.email=t@t"]
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "mcf-data-x", str(remote)], check=True)
    a, b = tmp_path / "a", tmp_path / "b"
    subprocess.run(["git", "init", "-q", "-b", "mcf-data-x", str(a)], check=True)
    (a / "f.txt").write_text("1")
    _git(a, "add", "f.txt"); _git(a, *ident, "commit", "-q", "-m", "init")
    _git(a, "remote", "add", "origin", str(remote)); _git(a, "push", "-q", "origin", "mcf-data-x")
    subprocess.run(["git", "clone", "-q", "-b", "mcf-data-x", str(remote), str(b)], check=True)
    (b / "eod.txt").write_text("eod")                          # another job (EOD) pushes first
    _git(b, "add", "eod.txt"); _git(b, *ident, "commit", "-q", "-m", "EOD report"); _git(b, "push", "-q")
    # runner: no global identity at all
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "none"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.delenv("GIT_AUTHOR_NAME", raising=False); monkeypatch.delenv("GIT_COMMITTER_NAME", raising=False)
    monkeypatch.delenv("EMAIL", raising=False)
    (a / "status.json").write_text("{}")
    S.Publisher(a).push(["status.json"], "status closed")
    log = subprocess.run(["git", "-C", str(remote), "log", "--format=%s", "mcf-data-x"], capture_output=True, text=True).stdout
    assert "status closed" in log and "EOD report" in log
    assert not (a / ".git" / "rebase-merge").exists()


def test_retry_gets_only():
    calls = {"get": 0, "submit": 0}

    class C:
        def get_all_positions(self):
            calls["get"] += 1
            if calls["get"] < 3:
                raise requests.exceptions.ConnectionError("dropped")
            return ["ok"]

        def submit_order(self, *_):
            calls["submit"] += 1
            raise requests.exceptions.ConnectionError("dropped")

    c = _RetryGets(C(), sleep=lambda s: None)
    assert c.get_all_positions() == ["ok"] and calls["get"] == 3
    with pytest.raises(requests.exceptions.ConnectionError):
        c.submit_order(1)
    assert calls["submit"] == 1                                  # orders are never retried
