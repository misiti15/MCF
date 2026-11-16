"""Simulated leaderboard (owner 2026-11-16, display only): blend math, builder, dashboard card."""
import json
from pathlib import Path

import pytest

from mcf.report import sim_board as S

ROOT = Path(__file__).resolve().parents[1]
W = {"live": 1.0, "replay": 0.2, "backtest": 0.175, "haircut_r": 0.02}


def test_blend_per_trade_weights_and_haircut():
    b = S.blend({"trades": 10, "sessions": 4, "avg_r": 0.1}, {"trades": 100, "sessions": 30, "avg_r": 0.05},
                {"trades": 50, "sessions": 10, "avg_r": 0.02, "weight": 0.2}, W)
    assert b["eff_trades"] == 40 and b["eff_sessions"] == 12
    # replay haircut 0.02; shadow arrives already haircut (no second haircut)
    assert b["avg_r"] == pytest.approx((10 * 0.1 + 20 * 0.03 + 10 * 0.02) / 40)
    assert b["score"] == pytest.approx(b["avg_r"] * 40 / 60, abs=1e-4)


def test_screen_never_in_blend_and_compared_vs_live():
    """Owner 2026-11-16: the 2-year screen is its own source, never blended / ranked; fixed comparison vs live."""
    import inspect
    assert "backtest" not in inspect.signature(S.blend).parameters
    assert S.weights({})["backtest_in_blend"] is False
    c = S.screen_vs_live({"trades": 12, "avg_r": 0.05}, {"trades": 2000, "avg_r": 0.08})
    assert c["diff"] == pytest.approx(-0.03) and c["agree"] is True
    assert S.screen_vs_live({"trades": 12, "avg_r": -0.05}, {"trades": 2000, "avg_r": 0.08})["agree"] is False
    assert S.screen_vs_live({"trades": 9, "avg_r": 0.05}, {"trades": 2000, "avg_r": 0.08}) is None


def test_blend_live_only_matches_real_board_and_zero_rep():
    b = S.blend({"trades": 20, "sessions": 5, "avg_r": 0.1}, None, None, W)
    assert b["avg_r"] == 0.1 and b["score"] == pytest.approx(0.1 * 20 / 40)
    z = S.blend(None, {"trades": 50, "sessions": 10, "avg_r": 0.12}, None, W)   # zero live reps still ranks
    assert z["eff_trades"] == 10 and z["avg_r"] == pytest.approx(0.10)
    assert S.blend(None, None, None, W)["score"] is None


def test_weights_from_config():
    w = S.weights(json.loads((ROOT / "config/effective_sessions.json").read_text()))
    assert w["live"] == 1.0 and w["backtest"] == 0.175 and w["haircut_r"] >= 0.02
    cal = S.weights({"tiers": [{"min_match": 0.98, "max_extra": 0.02, "no_optimism": True, "weight": 0.35},
                               {"min_match": 0.95, "weight": 0.2}], "replay": {"match": 0.99, "extra": 0.01, "optimism_r": 0.0}})
    assert cal["replay"] == 0.35


def test_builder(tmp_path):
    (tmp_path / "docs/live").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "research/generator/runs").mkdir(parents=True)
    (tmp_path / "config/effective_sessions.json").write_text((ROOT / "config/effective_sessions.json").read_text())
    (tmp_path / "docs/live/replay.json").write_text(json.dumps({"window": "2026-09-01 to 2026-10-21", "setups": {
        "A": {"trades": 40, "sessions": 9, "avg_r": 0.05}}}))
    (tmp_path / "research/generator/runs/2026-10-19.json").write_text(json.dumps({"date": "2026-10-19", "picks": [
        {"name": "GEN-1", "screen": {"all": {"n": 300, "exp_r": 0.04, "days": 105}, "train": {"exp_r": 0.05}, "valid": {"exp_r": 0.03}}}]}))
    d = S.build(tmp_path)
    assert d["sources"]["replay"]["from"] == "2026-09-01" and d["sources"]["replay"]["to"] == "2026-10-21"
    assert d["setups"]["A"]["replay"] == {"trades": 40, "sessions": 9, "avg_r": 0.05}
    assert d["setups"]["GEN-1"]["backtest"]["sessions"] == 105 and d["setups"]["GEN-1"]["backtest"]["valid_r"] == 0.03
    assert d["sources"]["weights"]["backtest"] == 0.175 and d["sources"]["backtest"]["in_blend"] is False
    # hook: a fresh all-setups replay run wins over the stale snapshot
    (tmp_path / "research/replay_all").mkdir(parents=True)
    (tmp_path / "research/replay_all/latest.json").write_text(json.dumps({"window": "2026-01-02 to 2026-11-13", "setups": {
        "B": {"trades": 5, "sessions": 2, "avg_r": 0.1}}}))
    d = S.build(tmp_path)
    assert "B" in d["setups"] and "A" not in d["setups"] and d["sources"]["replay"]["label"] == "all-setups replay"


def test_dashboard_sim_card_below_real_board():
    html = (ROOT / "docs/live/index.html").read_text()
    real = html.index('id="lb-card"><h2>Setup leaderboard — all accounts, since start</h2>')
    sim = html.index('id="sim-card"><h2>Simulated leaderboard — live + weighted replay / backtest</h2>')
    assert real < sim < html.index('id="gen-card"')
    for needle in ("sim_inputs.json", "Not live results — a what-if ranking", "Δ rank vs real board", "Effective sessions",
                   "Blended avg R w/o best day", "No simulated inputs yet", "window.MCF.simBlend", "max-width: 640px",
                   "2y screen trades", "Screen vs live", "screening only, not in blend", "Shadow trades / avg R"):
        assert needle in html, needle
    assert (ROOT / "docs/live/sim_inputs.json").exists()
    js = html[html.index("window.MCF.simBlend = "):html.index("(() => {", html.index("window.MCF.simBlend = "))]
    assert "backtest" not in js and "w.backtest" not in js   # the screen never enters the page blend
    assert json.loads((ROOT / "config/effective_sessions.json").read_text())["history_in_blend"] is False
