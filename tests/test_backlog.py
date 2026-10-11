import json

import pytest

from mcf.research import backlog as b


def test_gates_and_holdout_once(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "BACKLOG", tmp_path / "backlog.jsonl")
    monkeypatch.setattr(b, "RESULTS", tmp_path / "results.jsonl")
    monkeypatch.setattr(b, "REPORT", tmp_path / "BACKLOG.md")
    b.save([{"id": "x", "title": "X", "status": "testing", "module": None, "variant": None},
            {"id": "y", "title": "Y", "status": "finalist", "module": None, "variant": None}])
    assert b._passes({"n": 40, "exp_r": 0.05, "t_day_clustered": 2.0}, 30, 1.5)
    assert not b._passes({"n": 40, "exp_r": 0.05, "t_day_clustered": 1.0}, 30, 1.5)
    assert not b._passes({"n": 10, "exp_r": 0.5, "t_day_clustered": 3.0}, 30, 1.5)
    with pytest.raises(SystemExit):
        b.holdout("x")                      # not a finalist
    (tmp_path / "results.jsonl").write_text(json.dumps({"id": "y", "split": "test", "metrics": {}}) + "\n")
    with pytest.raises(SystemExit):
        b.holdout("y")                      # already scored once
    b.report()
    assert "| finalist | y |" in (tmp_path / "BACKLOG.md").read_text()


def test_rework_holdout_looks_raise_the_bar(tmp_path, monkeypatch):
    monkeypatch.setattr(b, "BACKLOG", tmp_path / "backlog.jsonl")
    monkeypatch.setattr(b, "RESULTS", tmp_path / "results.jsonl")
    monkeypatch.setattr(b, "REPORT", tmp_path / "BACKLOG.md")
    es = [{"id": "a", "title": "A", "status": "holdout_failed", "holdout_burned": True},
          {"id": "a2", "title": "A rsi10", "status": "finalist", "parent": "a", "module": "m", "variant": "v"}]
    b.save(es)
    assert b.holdout_looks(es[1], es) == 1          # the ancestor's look counts
    monkeypatch.setattr(b, "_score", lambda e, s, v=None: {"n": 50, "exp_r": 0.1, "t_day_clustered": 1.2})
    b.holdout("a2")                                  # look 2 needs t >= 1.5: 1.2 fails
    assert next(e for e in b.entries() if e["id"] == "a2")["status"] == "holdout_failed"
    b.save(b.entries() + [{"id": "a3", "title": "A rsi10+vwap", "status": "finalist", "parent": "a2", "module": "m", "variant": "v"}])
    monkeypatch.setattr(b, "_score", lambda e, s, v=None: {"n": 50, "exp_r": 0.1, "t_day_clustered": 2.1})
    b.holdout("a3")                                  # look 3 needs t >= 2.0: passes -> probation
    assert next(e for e in b.entries() if e["id"] == "a3")["status"] == "probation"


# ---------------------------------------------------------------- lab-module re-test on the 1-minute cache (synthetic bars)
LAB_MODULE = '''"""Synthetic test setup. Run with min_adv 0 and window [950, 1100]."""
import numpy as np
SIDE = "long"
GEOM = "t1s1"


def mask(df):
    return np.asarray(df["tod"].to_numpy() == 1000)
'''


def _bars(days, seed=0):
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed)
    out, px = [], 50.0
    for d in days:
        idx = pd.date_range(f"{d} 09:30", f"{d} 15:59", freq="1min", tz="America/New_York")
        c = px * np.exp(np.cumsum(rng.normal(0, 0.0015, len(idx))))
        o = np.r_[px, c[:-1]]
        out.append(pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0005, "low": np.minimum(o, c) * 0.9995,
                                 "close": c, "volume": rng.integers(1_000, 50_000, len(idx)).astype(float)}, index=idx))
        px = float(c[-1])
    return pd.concat(out)


def _lab_setup(tmp_path, monkeypatch, symbols=("AAA", "BBB")):
    import pandas as pd

    from mcf.data.store import BarStore

    monkeypatch.setattr(b, "BACKLOG", tmp_path / "backlog.jsonl")
    monkeypatch.setattr(b, "RESULTS", tmp_path / "results.jsonl")
    monkeypatch.setattr(b, "REPORT", tmp_path / "BACKLOG.md")
    mod = tmp_path / "LAB1-test-long.py"
    mod.write_text(LAB_MODULE)
    days = [d.date() for d in pd.bdate_range("2026-07-01", "2026-08-14")]
    store = BarStore(tmp_path / "cache")
    for i, s in enumerate(symbols):
        store.save(s, _bars(days, seed=i))
    b.save([{"id": "lab1", "title": "L", "status": "testing", "lab_module": str(mod), "added": "2026-08-01"},
            {"id": "plain", "title": "P", "status": "finalist", "module": None},
            {"id": "idea1", "title": "I", "status": "idea"}])
    return tmp_path / "cache"


def test_lab_retest_scores_on_cache(tmp_path, monkeypatch):
    cache = _lab_setup(tmp_path, monkeypatch)
    assert b.run(cache=cache, workers=1) == 0
    rows = [json.loads(l) for l in (tmp_path / "results.jsonl").read_text().splitlines()]
    assert [r["id"] for r in rows] == ["lab1"] and rows[0]["split"] == "lab_cache"
    m = rows[0]["metrics"]
    assert m["n"] > 0 and m["window"] == [950, 1100] and m["min_adv"] == 0.0 and m["side"] == "long"
    assert {"n", "exp_r"} <= set(m["up"]) and {"n", "exp_r"} <= set(m["down"])
    assert m["forward"]["since"] == "2026-08-01" and 0 < m["forward"]["n"] < m["n"]
    # one trade per symbol-day at the 10:00 bar close, priced with production + time-of-day costs
    assert m["n"] == m["days"] * 2
    md = (tmp_path / "BACKLOG.md").read_text()
    assert "Forward re-test" in md and "since 2026-08-01" in md
    # the entry status is not changed by the monitoring re-test
    assert next(e for e in b.entries() if e["id"] == "lab1")["status"] == "testing"


def test_lab_retest_fails_loudly(tmp_path, monkeypatch, capsys):
    _lab_setup(tmp_path, monkeypatch)
    assert b.run(cache=tmp_path / "empty_cache", workers=1) == 1      # runnable entries, nothing scored
    out = capsys.readouterr()
    assert "scored: 0" in out.out and "no module / lab_module" in out.out and "none was scored" in out.err
    b.save([{"id": "bad", "title": "B", "status": "testing", "lab_module": "research/does/not/exist.py"}])
    assert b.run(cache=tmp_path / "cache", workers=1) == 1
    assert "lab module unusable" in capsys.readouterr().out


def test_lab_retest_never_reads_locked_block(tmp_path):
    import pandas as pd

    from mcf.research import backlog_lab as BL

    days = [d.date() for d in pd.bdate_range("2024-12-02", "2025-01-31")]
    frame, daily = BL.symbol_frame(_bars(days), "LCK")
    assert frame is None and daily.empty                                # every bar is inside the locked block
    mixed = [d.date() for d in pd.bdate_range("2025-01-02", "2025-04-30")]
    frame, daily = BL.symbol_frame(_bars(mixed), "MIX")
    assert min(daily["date"]) > BL.LOCKED[1] and min(frame["date"]) > BL.LOCKED[1]
