"""Owner decisions 2026-11-18 evening (research/od1118/NOTES.md): ROT2 caps gate, GY-ARCHIVE-20 config + assignments,
REPS2-LANE shadow lane, RT-UNCAL, UNIT1 account R. Educational only - not financial advice."""
import json
from pathlib import Path

import yaml

from mcf import rotation as ROT
from mcf.execution import shadow as SH

ROOT = Path(__file__).resolve().parents[1]


def _gen_cfg(tmp_path, frac, reps=None):
    res = tmp_path / "res.json"
    if frac is not None:
        res.write_text(json.dumps({"accounts": {"testing2": {"resource_skip_frac": frac}}}))
    rp = tmp_path / "reps.json"
    rp.write_text(json.dumps({"setups": reps or {}}))
    st = {f"GEN-{i}": {"enabled": True} for i in range(8)}
    rc = {"enabled": True, "from": "2026-11-19", "accounts": ["testing2"], "reps_file": str(rp),
          "caps": {"GEN": {"prefix": "GEN-", "cap": 6, "scope": "account"}},
          "min_resource_skip_frac": 0.05, "resource_file": str(res), "never_bench_below_signals": 0.5}
    return {"account_name": "testing2", "strategies": st, "arena_rotation": rc}


def test_rot2_no_cap_at_or_under_the_resource_line(tmp_path):
    for frac in (None, 0.01, 0.05):
        cfg = _gen_cfg(tmp_path / str(frac), frac) if (tmp_path / str(frac)).mkdir() is None else None
        assert ROT.family_caps(cfg, "2026-11-19") == {}
        assert all(v["enabled"] for v in cfg["strategies"].values())          # nobody benched
        assert cfg["rotation"]["family_caps_off"]["line"] == 0.05


def test_rot2_cap_applies_over_the_line_but_never_benches_rare(tmp_path):
    reps = {"GEN-0": {"active_days": 20, "signals": 2}, "GEN-1": {"active_days": 20, "signals": 400}}
    cfg = _gen_cfg(tmp_path, 0.08, reps)
    out = ROT.family_caps(cfg, "2026-11-19")
    on = {k for k, v in cfg["strategies"].items() if v["enabled"]}
    assert "GEN-0" in on and "GEN-0" not in out["GEN"]["benched"]                 # rare: 0.1 signals/day, keeps playing
    assert len(on) == 7 and len(out["GEN"]["benched"]) == 1                      # 7 capped members -> 6 play + rare


def test_default_config_rot2_and_resources_file_keep_caps_off_today():
    cfg = yaml.safe_load((ROOT / "config/default.yaml").read_text())
    rc = cfg["arena_rotation"]
    assert rc["min_resource_skip_frac"] == 0.05 and rc["never_bench_below_signals"] == 0.5
    res = json.loads((ROOT / rc["resource_file"]).read_text())["accounts"]
    assert set(rc["accounts"]) <= set(res) and max(v["resource_skip_frac"] for v in res.values()) <= 0.05


def test_gy_archive_20_blocks_disabled_marked_and_exempt_kept():
    st = yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text())["strategies"]
    arch = [k for k, v in st.items() if isinstance(v, dict) and v.get("archived")
            and v["archived"].get("code") == "GY-ARCHIVE-20"]        # GYH-V3 archives (2026-11-27) are separate
    assert len(arch) == 18
    for k in arch:
        v = st[k]
        assert v["enabled"] is False and v["archived"]["code"] == "GY-ARCHIVE-20" and "benched" not in v
        assert v.get("type") and (v.get("module") or v.get("formula") or v.get("type"))   # block kept, re-testable
    for k in ("CWT14-failbrk-orl-p05-long", "heat_fade_short-FD"):                 # owner exception: exempt, kept
        assert st[k]["enabled"] is True and not st[k].get("archived")


def test_assignments_tag_archived_and_shadow_lane():
    a = json.loads((ROOT / "docs/live/assignments.json").read_text())["setups"]
    assert a["CWT13-vwapstretch-z05-short"]["archived"]["code"] == "GY-ARCHIVE-20"
    assert a["CWT13-vwapstretch-z05-short"]["accounts"] == []
    lane = json.loads((ROOT / "research/reps2/fastlane/lane.json").read_text())["setups"]
    assert lane and all(a.get(n, {}).get("shadow_lane") == "testing2" for n in lane if n in a)


def test_lane_setups_read_from_file_and_missing_file_is_empty(tmp_path):
    f = tmp_path / "lane.json"
    f.write_text(json.dumps({"setups": ["A", "B"]}))
    assert SH.lane_setups({"shadow_setups_from": str(f)}) == ["A", "B"]
    assert SH.lane_setups({"shadow_setups_from": str(tmp_path / "none.json")}) == []
    assert SH.lane_setups({}) == []
    t2 = yaml.safe_load((ROOT / "config/account_testing2.yaml").read_text())
    assert t2["shadow_setups_from"] == "research/reps2/fastlane/lane.json"
    assert len(SH.lane_setups(t2)) >= 1


def test_rt_uncal_weight_zero():
    e = json.loads((ROOT / "config/effective_sessions.json").read_text())
    s = json.dumps(e)
    assert '"uncalibrated_weight": 0.2' not in s and '"uncalibrated_weight": 0' in s.replace("0.0", "0")


def test_unit1_account_r_display_only():
    import pandas as pd

    from mcf.report import c3score as C
    from mcf.report.live_status import _account_r

    assert _account_r({"pnl_adj": 299.0}, 84_000) == round(299.0 / 210.0, 2)      # $ / 0.25% of equity
    assert _account_r({"pnl_adj": 10.0}, None) is None
    t = pd.DataFrame({"date": ["2026-11-18"] * 2, "entry": [10.0, 20.0], "stop": [9.0, 21.0], "shares": [10, 5],
                      "pnl": [-5.0, 30.0], "pnl_adj": [-6.0, 29.0]})
    sc = C.scorecard(C.day_table(t, 100_000, 0.25))
    assert sc["dash_r_day"] == round(-0.6 + 5.8, 2) and sc["acct_r_day"] == round(23.0 / 250.0, 2)
    assert "trade R" in C.line(sc) and "account R" in C.line(sc)
