"""Poll input log (live.log_poll_inputs, owner 2026-10-21): each poll records what the runner received, compactly, in
gzip chunks under the state dir; it never breaks or slows trading. Educational only - not financial advice."""

import gzip
import os
import time

import numpy as np
import pandas as pd

from mcf.execution import drill
from mcf.execution.runner import poll_record, read_poll_log

DAY = drill.DAY
NY = "America/New_York"


def _bars(last: pd.Timestamp, syms, late=(), gaps=()):
    idx = pd.date_range(pd.Timestamp(f"{DAY} 09:30", tz=NY), last, freq="1min")
    b = pd.DataFrame({"open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0, "volume": 1e5}, index=idx)
    out = {s: b for s in syms}
    for s in late:
        out[s] = b.iloc[:-3]
    for s in gaps:
        out[s] = b.drop(b.index[2])
    return out


def test_poll_record_lists_only_exceptions():
    now = pd.Timestamp(f"{DAY} 10:00:03", tz=NY)
    bars = _bars(now.floor("1min") - pd.Timedelta(minutes=1), ["A", "B", "C", "D"], late=["C"], gaps=["D"])
    rec = poll_record(now, bars, ["A", "B", "C", "D", "E"], {"last_poll_s": 1.25}, False)
    assert rec["exp"] == 30 and rec["lm"] == "09:59" and rec["ms"] == 1250
    assert rec["got"] == 4 and rec["fresh"] == 3 and rec["none"] == ["E"] and rec["none_n"] == 1
    assert rec["late"] == {"0956": ["C"]}
    assert rec["miss"] == {"3": ["C"], "1": ["D"]}          # A and B hold every minute: not listed
    assert rec["stale"] is False


def test_runner_logs_flushes_and_never_raises(tmp_path):
    with drill._no_sleep():
        c = drill.DrillAlpaca(pd.Timestamp(f"{DAY} 10:00:05", tz=NY))
        r = drill._runner(str(tmp_path), c)
        r.watchlist = ["XYZ", "ABC", "DEF"]
        r.poll_log_dir = str(tmp_path / "polls")
        for m in range(5):
            now = pd.Timestamp(f"{DAY} 09:55:03", tz=NY) + pd.Timedelta(minutes=m)
            r.fetch = lambda now, _b=drill._bars(now.floor("1min") - pd.Timedelta(minutes=1)): _b
            r.step(now)
        assert len(r._poll_buf) == 5
        assert r.flush_poll_log(now) is None                  # not due yet (poll_log_flush_min)
        r.write_status(now, "handover")                       # handover / close always flush
        assert r._poll_buf == []
        recs = read_poll_log(str(tmp_path / "polls"), DAY)
        assert [x["t"] for x in recs] == [f"09:{55 + m}:03" for m in range(5)]
        assert all(x["fresh"] == 3 and x["n"] == 3 for x in recs)
        # a broken record never reaches trading
        import mcf.execution.runner as R

        orig = R.poll_record
        R.poll_record = lambda *a, **k: 1 / 0
        try:
            r.fetch = lambda now: drill._bars(now.floor("1min") - pd.Timedelta(minutes=1))
            r.step(now + pd.Timedelta(minutes=1))
        finally:
            R.poll_record = orig
        assert len(r._poll_buf) == 0


def test_chunks_are_never_rewritten(tmp_path):
    with drill._no_sleep():
        c = drill.DrillAlpaca(pd.Timestamp(f"{DAY} 10:00:05", tz=NY))
        r = drill._runner(str(tmp_path), c)
        r.poll_log_dir = str(tmp_path / "polls")
        now = pd.Timestamp(f"{DAY} 10:00:03", tz=NY)
        r._poll_buf = ['{"t":"10:00:03"}']
        p1 = r.flush_poll_log(now, force=True)
        r._poll_buf = ['{"t":"10:00:04"}']
        p2 = r.flush_poll_log(now, force=True)
        assert p1 != p2 and os.path.exists(p1) and os.path.exists(p2)
        assert len(read_poll_log(str(tmp_path / "polls"), DAY)) == 2


def test_overhead_and_size_on_a_live_sized_universe():
    """~4,900 symbols (the live universe), 15% thin names with gaps, 2% late: the record costs a few ms per poll and a
    full session stays far below 10-20 MB compressed."""
    rng = np.random.default_rng(1)
    syms = [f"S{i:04d}" for i in range(4900)]
    lines, worst = [], 0.0
    idx_all = pd.date_range(pd.Timestamp(f"{DAY} 09:30", tz=NY), periods=390, freq="1min")
    base = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}, index=idx_all)
    thin = {s: np.sort(rng.choice(390, 250, replace=False)) for s in syms[:735]}
    for m in range(5, 390, 13):                                # 30 polls spread over the day
        now = idx_all[m] + pd.Timedelta(seconds=3)
        bars = {}
        for s in syms:
            if s in thin:
                k = thin[s][thin[s] < m]
                bars[s] = base.iloc[k]
            else:
                bars[s] = base.iloc[: m - (2 if rng.random() < 0.02 else 0)]
        t0 = time.perf_counter()
        rec = poll_record(now, bars, syms, {"last_poll_s": 2.0}, False)
        lines.append(__import__("json").dumps(rec, separators=(",", ":")))
        worst = max(worst, time.perf_counter() - t0)
    assert worst < 0.25, worst                                 # typically ~10-20 ms; the poll itself takes seconds
    day_bytes = len(gzip.compress("\n".join(lines).encode(), 9)) * 390 / len(lines)
    assert day_bytes < 10e6, day_bytes
