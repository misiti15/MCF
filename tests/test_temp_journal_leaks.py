"""Temp journal copies are always removed (inspector 11-27 #11/#15: leftover copies filled /tmp). Research/report
housekeeping only - no trading decision is involved. Educational only - not financial advice."""
import importlib.util
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "research" / "owner1120" / "inverse" / "shadow.py"
spec = importlib.util.spec_from_file_location("inverse_shadow_leaks", P)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def _db(tmp_path, name):
    p = tmp_path / name
    c = sqlite3.connect(p)
    c.execute("create table trades (run_id, exit, shares, entry, stop, date, symbol, strategy, side, r_multiple)")
    c.execute("create table signals (run_id, side, day, symbol, strategy, status, reason)")
    c.commit()
    c.close()
    return p


def test_inverse_shadow_unlinks_each_journal_copy(tmp_path, monkeypatch):
    made = []

    def fake_journal(branch, git_dir):
        made.append(_db(tmp_path, f"invshadow_{branch}.db"))
        return made[-1]

    monkeypatch.setattr(S, "_journal", fake_journal)
    df = S.rows_for(["2026-11-25"])
    assert df.empty and len(made) == len(S.BRANCHES)
    assert not any(p.exists() for p in made)


def test_inverse_shadow_unlinks_on_error(tmp_path, monkeypatch):
    bad = tmp_path / "invshadow_bad.db"
    bad.write_bytes(b"x")                                  # sqlite raises on the first query
    monkeypatch.setattr(S, "_journal", lambda b, g: bad)
    try:
        S.rows_for(["2026-11-25"])
    except Exception:
        pass
    assert not bad.exists()


def test_inverse_shadow_journal_copy_is_unique_tempfile(tmp_path, monkeypatch):
    import subprocess
    import tempfile

    class R:
        returncode, stdout = 0, b"blob"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R())
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    p = S._journal("mcf-data", "x")
    assert p.parent == tmp_path and p.name.startswith("invshadow_mcf-data_") and p.read_bytes() == b"blob"
