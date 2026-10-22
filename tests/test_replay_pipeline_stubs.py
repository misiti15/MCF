"""docs/live/replay.json and docs/live/pipeline.json: the files the dashboard reads for the Replay columns and the
New setup pipeline card (owner 2026-10-21). They start as empty stubs; the replay engine / pipeline build fills them.

replay.json schema:
  {"generated": null | "YYYY-MM-DD HH:MM ET", "window": optional "YYYY-MM-DD to YYYY-MM-DD",
   "setups": {"<setup code>": {"trades": int, "sessions": int, "win_rate": 0..1, "avg_r": float, "t": float | null,
                               "total_r": float}}}
pipeline.json schema:
  {"generated": null | str,
   "setups": {"<setup code>": {"stage": "backtest" | "replay" | "live" | str,
                               "backtest": {"trades", "win", "be_win", "avg_r", "t"} | null,
                               "replay": {same} | null, "live": {same} | null}}}
  (live may be left out: the dashboard then takes it from the merged leaderboard.)
Every figure may be null; the dashboard shows "—". Educational only — not financial advice.
"""
import json
from pathlib import Path

LIVE = Path(__file__).resolve().parents[1] / "docs" / "live"
REPLAY_KEYS = {"trades", "sessions", "win_rate", "avg_r", "t", "total_r"}
STAGE_KEYS = {"trades", "win", "be_win", "avg_r", "t"}


def _num(v):
    return v is None or isinstance(v, (int, float))


def check_replay(d: dict) -> None:
    assert set(d) >= {"generated", "setups"} and isinstance(d["setups"], dict)
    for k, v in d["setups"].items():
        assert isinstance(k, str) and set(v) <= REPLAY_KEYS | {"t_stat", "date"}, k
        assert all(_num(v.get(x)) for x in REPLAY_KEYS), k
        assert v.get("win_rate") is None or 0 <= v["win_rate"] <= 1, k


def check_pipeline(d: dict) -> None:
    assert set(d) >= {"generated", "setups"} and isinstance(d["setups"], dict)
    for k, v in d["setups"].items():
        assert "stage" in v, k
        for st in ("backtest", "replay", "live"):
            o = v.get(st)
            assert o is None or (set(o) <= STAGE_KEYS and all(_num(o.get(x)) for x in STAGE_KEYS)), (k, st)


def test_replay_file_valid():
    check_replay(json.loads((LIVE / "replay.json").read_text()))


def test_pipeline_file_valid():
    check_pipeline(json.loads((LIVE / "pipeline.json").read_text()))


def test_schema_examples():
    check_replay({"generated": "2026-10-22 18:00 ET", "window": "2026-09-01 to 2026-10-21",
                  "setups": {"A": {"trades": 40, "sessions": 20, "win_rate": 0.55, "avg_r": 0.12, "t": 1.8, "total_r": 4.8}}})
    check_pipeline({"generated": None, "setups": {"A": {"stage": "replay",
                    "backtest": {"trades": 300, "win": 0.5, "be_win": 0.45, "avg_r": 0.08, "t": 2.1}, "replay": None}}})


def test_dashboard_reads_both():
    html = (LIVE / "index.html").read_text()
    assert "../live/replay.json" in html and "../live/pipeline.json" in html
