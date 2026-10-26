"""GX5 (owner 2026-10-26): realistic expected live trades/day per GEN setup next to the 2-year screen per_day
(mcf/research/generator/expect.py; factors from research/ops/genexposure1025.md). Display only. Educational only."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from mcf.research.generator import expect as E
from mcf.research.generator import summary

ROOT = Path(__file__).resolve().parents[1]


def test_factors_and_formula():
    assert (E.LIVE_GATE_SHARE, E.OUTSIDE_SHARE, E.FILTER_SHARE, E.RECENT_SESSIONS) == (0.97, 0.40, 0.19, 60)
    assert E.expected_live_per_day(10) == pytest.approx(10 * 0.97 * 1.4 * 0.81, abs=0.005)
    assert E.expected_live_per_day(0) == 0 and E.expected_live_per_day(None) is None
    b = E.basis()
    assert b["source"] == "research/ops/genexposure1025.md" and b["factor"] == pytest.approx(1.1, abs=0.001)
    assert set(b["why"]) == {"median_day", "live_gate_share", "outside_share", "filter_share"}


def test_recent_median_counts_zero_days_and_uses_the_latest_sessions():
    # 70 sessions, factorize order is NOT date order (the panel's rows run month by month, symbol by symbol)
    dates = [f"2026-{m:02d}-{d:02d}" for m in (7, 8, 9) for d in range(1, 29)][:70]
    rng = np.random.default_rng(0)
    perm = rng.permutation(70)
    P = SimpleNamespace(days=np.array(dates, dtype=object)[perm], n_days=70)
    code = {d: i for i, d in enumerate(P.days)}
    last60 = sorted(dates)[-60:]
    # 3 trades on each of the 10 OLDEST sessions (outside the window), 2 trades on 20 of the last 60, none elsewhere
    day = [code[d] for d in sorted(dates)[:10] for _ in range(3)] + [code[d] for d in last60[::3] for _ in range(2)]
    st = E.recent_stats(P, np.array(day))
    assert st["per_day_median60"] == 0.0                      # 40 of 60 recent sessions have none
    assert st["per_day_mean60"] == pytest.approx(40 / 60, abs=1e-3)
    assert st["recent_window"] == [last60[0], last60[-1]]
    day2 = [code[d] for d in last60 for _ in range(4)]
    assert E.recent_stats(P, np.array(day2))["per_day_median60"] == 4.0
    assert E.recent_stats(P, np.array([], dtype=int))["per_day_median60"] == 0.0


def test_entry_fields():
    e = E.entry({"per_day": 9.4, "per_day_median60": 5.0, "per_day_mean60": 6.1, "recent_window": ["a", "b"]})
    assert e == {"per_day": 9.4, "per_day_median60": 5.0, "per_day_mean60": 6.1, "recent_window": ["a", "b"],
                 "expected_live_per_day": round(5.0 * E.factor(), 2),
                 "expected_live_mean_basis": round(6.1 * E.factor(), 2), "counts60": None}


def test_set_total_is_the_median_of_the_daily_total():
    """Two sparse setups that fire on alternate days: each per-setup median is 0, the set trades every day."""
    a = {"recent_window": ["x", "y"], "counts60": [4, 0] * 30}
    b = {"recent_window": ["x", "y"], "counts60": [0, 4] * 30}
    st = E.set_total([a, b])
    assert st["median_day_total"] == 4.0 and st["expected_live_per_day"] == round(4 * E.factor(), 1)
    assert E.set_total([a, {"recent_window": ["x", "z"], "counts60": [1] * 60}]) is None   # different windows
    assert E.set_total([{"counts60": None}]) is None


def test_screen_evaluate_carries_the_recent_median():
    import inspect

    from mcf.research.generator import apply, screen
    assert "recent_stats(P, day)" in inspect.getsource(screen.evaluate)
    src = inspect.getsource(apply.run)
    assert '"expected_live":' in src and '"expected_live_basis": E.basis()' in src   # every run report fills it
    assert '"expected_live_per_day"' in inspect.getsource(apply._apply)


def _root(tmp_path, runs: dict, backfill: dict | None = None):
    (tmp_path / "research" / "generator" / "runs").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    (tmp_path / "docs" / "live").mkdir(parents=True)
    for d, r in runs.items():
        (tmp_path / "research" / "generator" / "runs" / f"{d}.json").write_text(json.dumps(r))
    if backfill is not None:
        (tmp_path / "research" / "generator" / "expected_live.json").write_text(json.dumps({"setups": backfill}))
    gen = {"strategies": {
        "GEN-A": {"enabled": True, "type": "lab", "gen": {"screen": {"per_day": 12.0}}},
        "GEN-B": {"enabled": True, "type": "lab", "gen": {"screen": {"per_day": 3.0}}},
        "GEN-OBS": {"enabled": True, "type": "lab", "tags": ["observation"]},
        "GEN-OFF": {"enabled": False, "type": "lab", "gen": {"screen": {"per_day": 1.0}}}}}
    import yaml
    (tmp_path / "config" / "account_gen.yaml").write_text(yaml.safe_dump(gen))
    for f in ("default.yaml", "account_testing.yaml", "account_testing2.yaml"):
        (tmp_path / "config" / f).write_text("strategies: {}\n")
    return tmp_path


def test_summary_expected_live(tmp_path):
    root = _root(tmp_path, {
        "2026-10-26": {"date": "2026-10-26", "picks": [], "expected_live": {
            "GEN-A": E.entry({"per_day": 12.0, "per_day_median60": 6.0}),
        }}}, backfill={"GEN-A": E.entry({"per_day": 12.0, "per_day_median60": 1.0}),
                       "GEN-B": E.entry({"per_day": 3.0, "per_day_median60": 2.0})})
    d = summary.build(root)
    ex = d["expected_live"]
    assert ex["setups"]["GEN-A"]["expected_live_per_day"] == round(6.0 * E.factor(), 2)   # run report beats backfill
    assert ex["setups"]["GEN-B"]["expected_live_per_day"] == round(2.0 * E.factor(), 2)   # backfill only
    assert ex["setups"]["GEN-A"]["screen_per_day"] == 12.0 and "GEN-OFF" not in ex["setups"]
    assert ex["live_screen_per_day_total"] == 15.0
    assert ex["live_expected_per_day_total"] == pytest.approx(round(6.0 * E.factor(), 2) + round(2.0 * E.factor(), 2), abs=0.06)
    assert ex["basis"]["source"] == "research/ops/genexposure1025.md"


def test_published_generator_lab_has_expected_live():
    d = json.loads((ROOT / "docs" / "live" / "generator_lab.json").read_text())
    ex = d["expected_live"]
    assert ex["basis"]["factor"] == pytest.approx(E.factor(), abs=1e-4)
    assert ex["setups"] and all("expected_live_per_day" in v and "screen_per_day" in v for v in ex["setups"].values())


def test_dashboard_column():
    html = (ROOT / "docs" / "live" / "index.html").read_text()
    gen = html[html.index("// Generated setups leaderboard (owner 2026-10-19)"):]
    gen = gen[:gen.index("</script>")]
    assert '["exp_live", "Expected live /day"]' in gen and '["scr_day", "Screen /day"]' in gen
    assert "../live/generator_lab.json" in gen and "expected_live_per_day" in gen
    assert '"Expected live /day":' in html                       # hover glossary
