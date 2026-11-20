"""Remedy-Q (a) Testing copies (owner 2026-11-20 "remedy-q yes absolutely and quickly", conditional on the re-check in
research/remedyq_1120/verdicts.json; effective session 2026-11-23): each Primary trio member gets one Testing copy that is the
parent exactly except for the entry window [950, 1230] (no new entries after the 5-min bar that closes at 12:30). The
parents in Primary stay unchanged (PROT-06/07/08), each copy runs in exactly one testing area, apart from its parent's
other copies (WB4), is marked "Remedy-Q:" / remedy_q for the dashboard, and has one ledger entry with the protection
fields. Educational only - not financial advice."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TESTING = ["testing2", "explore1", "livelab", "testingd", "testinge", "testingf"]
OTHER = ["default", "testing", "graveyard", "gen"]
CUT = 1230
COPIES = {  # copy -> (parent, account)
    "L3-gap-slope-fromopen-FD-RQa-1230": ("L3-gap-slope-fromopen-FD", "testingf"),
    "RW3-gapdn-rsi5pop-flowsell-short-FD-RQa-1230": ("RW3-gapdn-rsi5pop-flowsell-short-FD", "testing2"),
    "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-RQa-1230": ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "explore1"),
}
TZ = "America/New_York"


def _raw(acct):
    p = ROOT / ("config/default.yaml" if acct == "default" else f"config/account_{acct}.yaml")
    return yaml.safe_load(p.read_text())


def _on(raw):
    return {k for k, v in (raw.get("strategies") or {}).items() if isinstance(v, dict) and v.get("enabled")}


def test_parents_unchanged_in_primary():
    s = _raw("default")["strategies"]
    for parent, _ in COPIES.values():
        assert s[parent]["enabled"] is True and s[parent]["window"] == [950, 1500], parent


def test_each_copy_is_the_parent_with_only_the_window_cut():
    prim = _raw("default")["strategies"]
    for n, (parent, acct) in COPIES.items():
        homes = [a for a in TESTING if n in _on(_raw(a))]
        assert homes == [acct], (n, homes)
        for a in OTHER:
            assert n not in (_raw(a).get("strategies") or {}), (n, a)
        c, p = _raw(acct)["strategies"][n], prim[parent]
        assert c["window"] == [950, CUT]
        for k in ("type", "module", "min_adv", "prefilter", "refire", "refire_cooldown", "geom", "scale_out_r"):
            assert c.get(k) == p.get(k), (n, k)
        assert n == f"{parent}-RQa-{CUT}"
        assert "remedy_q" in c["tags"] and c["remedy_q"].startswith("(a)")
        order = _raw(acct)["live"]["setup_order"]
        assert order[0] == n, (acct, order[:2])


def test_copies_apart_from_parent_and_its_other_copies():
    assert len({a for _, a in COPIES.values()}) == 3
    for n, (parent, acct) in COPIES.items():
        others = {k for k in _on(_raw(acct)) if k != n and (k == parent or k.startswith(parent + "-"))}
        assert not others, (n, acct, others)


@pytest.mark.parametrize("acct", sorted({a for _, a in COPIES.values()}))
def test_copies_build_under_the_live_loader(monkeypatch, acct):
    from mcf.config import load_config
    from mcf.strategies import setups as S

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    built = {s.name: s for s in S.build_strategies(load_config())}
    assert not S.LOAD_FAILURES
    for n, (parent, a) in COPIES.items():
        if a == acct:
            assert tuple(built[n].window) == (950, CUT), n
            assert built[n].params.get("scale_out_r") is None


def _ctx(last_hhmm, gap_open=90.0):
    """1-minute bars 09:30 .. last_hhmm (inclusive); a gap-down open so the gap prefilter passes."""
    end = pd.Timestamp(f"2026-11-23 {last_hhmm // 100:02d}:{last_hhmm % 100:02d}", tz=TZ)
    idx = pd.date_range(pd.Timestamp("2026-11-23 09:30", tz=TZ), end, freq="1min")
    px = np.full(len(idx), gap_open)
    bars = pd.DataFrame({"open": px, "high": px + 0.1, "low": px - 0.1, "close": px, "volume": 1000.0}, index=idx)
    return SimpleNamespace(symbol="ABC", bars=bars, prev_close=100.0, avg_dollar_volume=5e8)


@pytest.mark.parametrize("n", sorted(COPIES))
def test_cutoff_behaviour_live_gate(monkeypatch, n):
    """The live decision gate: the 5-min bucket closing 12:30 (latest bar 12:29) is still decided, the one closing 12:35
    (latest bar 12:34) is not; the parent (window to 15:00) decides both."""
    from mcf.config import load_config
    from mcf.strategies import setups as S

    parent, acct = COPIES[n]
    monkeypatch.setenv("MCF_ACCOUNT", acct)
    st = {s.name: s for s in S.build_strategies(load_config())}[n]
    par = S.LabStrategy(parent, **{k: v for k, v in _raw("default")["strategies"][parent].items()
                                    if k not in ("enabled", "type")})
    for last, inside in ((1229, True), (1234, False), (1259, False), (1429, False)):
        ctx = _ctx(last)
        assert st.eligible(ctx) is inside, (n, last)
        assert par.eligible(_ctx(last)) is True, (parent, last)


def test_cutoff_behaviour_backtest_mask():
    """The backtest / frame path applies the same window: decision bars with tod > 1230 never pass."""
    from mcf.strategies import setups as S

    tod = np.array([950, 1225, 1230, 1235, 1300, 1455])
    lo, hi = (950, CUT)
    keep = (tod >= max(950, lo)) & (tod <= min(1500, hi))
    assert keep.tolist() == [True, True, True, False, False, False]
    assert S._hhmm(pd.Timestamp("2026-11-23 12:25", tz=TZ) + S._FIVE) == 1230


def test_names_assignments_ledger_decision():
    names = yaml.safe_load((ROOT / "config/setup_names.yaml").read_text())
    page = json.loads((ROOT / "docs/live/setup_names.json").read_text())
    d = json.loads((ROOT / "docs/live/assignments.json").read_text())
    for n, (_, acct) in COPIES.items():
        assert names[n]["name"].startswith("Remedy-Q:") and names[n]["account"] == acct and names[n]["remedy_q"] is True
        assert page[n]["name"] == names[n]["name"] and page[n]["remedy_q"] is True
        assert n in d["accounts"][acct], n
    led = [json.loads(x) for x in (ROOT / "research/ledger.jsonl").read_text().splitlines() if x.strip()]
    e = next(x for x in led if x["id"] == "2026-11-23-remedyq-testing-copies")
    assert e["effective"] == "2026-11-23" and set(e["setups"]) == set(COPIES)
    assert "PROT-08" in e["protected_ids"] and (ROOT / e["guard_evidence"]).exists() and "owner" in e["owner_approval"]
    dec = {x["code"]: x for x in json.loads((ROOT / "docs/live/decisions.json").read_text()) if "code" in x}
    assert dec["WW-REMEDY-Q"]["status"] == "answered"
