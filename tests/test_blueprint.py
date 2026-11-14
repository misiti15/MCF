"""Workbench (owner 2026-11-13): blueprint parameter extraction on real setups and the one-part teardown spawner.
Observation only - the original setup is never edited. Educational only - not financial advice."""
import hashlib
import json

import pytest
import yaml

from mcf.report import blueprint as B
from mcf.research import workbench as W

L3 = "L3-gap-slope-fromopen-FD"
GEN = "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"
ST7 = "ST7-rsi50dn-long-pm-t1s1-FD"


def _rows(bp, sec):
    return {a: (b, c) for a, b, c in bp["sections"][sec]}


def test_lab_module_with_prefilter_L3():
    bp = B.extract(L3, with_record=False)
    m = bp["module"]
    assert m["style"] == "mask" and not m["unparsed"]
    got = {c["key"]: (c["op"], round(c["value"], 4)) for c in m["conds"]}
    assert got == {"cond.gap": ("<=", -2.6574), "cond.sma20_slope_pct": (">", 0.3724), "cond.fromOpen": (">", 3.4603)}
    assert bp["side"] == "short" and bp["geom"] == "t1s1"
    st = _rows(bp, "WHICH STOCKS")
    assert st["Pre-filter"][0] == "gap at the open <= -2.66%" and "gap_le:" in st["Pre-filter"][1]
    assert _rows(bp, "WHEN")["Entry window (5-min bar close)"][0] == "09:50-15:00 ET"
    assert "cooldown 1" in _rows(bp, "WHEN")["Refire"][0]
    assert _rows(bp, "RISK & EXIT")["Scale-out"][0] == "none"
    md = B.to_markdown(bp)
    assert "Educational only" in md and "`cond.fromOpen`" in md
    assert "Educational only — not financial advice" in B.to_html(bp)


def test_gen_setup_conds_and_name_tokens():
    bp = B.extract(GEN, with_record=False)
    m = bp["module"]
    assert m["style"] == "conds"
    assert [(c["col"], c["op"], c["value"]) for c in m["conds"]] == [("breadth", ">", 0.5), ("macd_hist", ">=", 0.12),
                                                                      ("ret3_atr", "<=", -0.069)]
    toks = dict(bp["gen"])
    assert all(w != "(not decoded)" for w in toks.values())
    assert toks["LATE"] == "time window 14:00-15:00 ET" and toks["t05s1"].startswith("target +0.5R")
    assert "macd" in toks["MACDhge0p12"].lower() and toks["261027-01"].startswith("generated 2026-10-27")
    assert _rows(bp, "WHEN")["Module's own window"][0] == "14:00-15:00 ET"
    assert _rows(bp, "RISK & EXIT")["Target"][0] == "+0.5R"


def test_stack_module_trigger_filters_ST7():
    bp = B.extract(ST7, with_record=False)
    m = bp["module"]
    assert m["style"] == "stack"
    assert [c["key"] for c in m["conds"]] == ["cond.trigger", "cond.rsi_ext", "cond.fo_against", "cond.bp_with"]
    assert m["conds"][0]["label"] == "RSI(14) crosses below 50" and m["conds"][1]["value"] == 70
    assert _rows(bp, "WHICH STOCKS")["Liquidity floor (20-day avg $ volume)"][0] == ">= $95M"


def test_record_summary_best_day():
    t = [dict(date="d1", acct="primary", r=2.0, pnl=1), dict(date="d1", acct="primary", r=1.0, pnl=1),
         dict(date="d2", acct="testing", r=-0.5, pnl=-1), dict(date="d3", acct="testing", r=0.5, pnl=1)]
    s = B.summarize(t)
    assert s["trades"] == 4 and s["sessions"] == 3 and s["avg_r"] == 0.75
    assert s["best_day"] == "d1" and s["avg_wo_best"] == 0.0 and s["best_share"] == 1.0 and s["one_day"]


def _hashes():
    files = sorted((B.ROOT / "config").glob("*.yaml")) + [B.ROOT / "research/bdi/fullday/L3-gap-slope-fromopen-FD.py",
                                                           B.ROOT / "research/generator/modules/GEN-261027-01-macdh-hi-late-long.py"]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def test_spawn_changes_one_part_and_leaves_original(tmp_path):
    before = _hashes()
    r = W.spawn(L3, "fromOpen=4", note="later fade", out_dir=tmp_path, today="2026-11-14")
    assert r["id"] == f"{L3}-WB1" and r["param"] == "cond.fromOpen" and r["new"] == 4.0 and r["parent"] == L3
    pdir = tmp_path / L3
    new_mod = (pdir / "modules" / f"{L3}-WB1.py").read_text().splitlines()
    old_mod = (B.ROOT / "research/bdi/fullday/L3-gap-slope-fromopen-FD.py").read_text().splitlines()
    body = [x for x in new_mod if not x.startswith("# ")]
    assert len(body) == len(old_mod) and sum(a != b for a, b in zip(body, old_mod)) == 1
    p = B.parse_module(pdir / "modules" / f"{L3}-WB1.py")
    assert {c["key"]: c["value"] for c in p["conds"]}["cond.fromOpen"] == 4.0
    stub = yaml.safe_load((pdir / f"{L3}-WB1.yaml").read_text())["strategies"][f"{L3}-WB1"]
    assert stub["enabled"] is False and stub["workbench"]["parent"] == L3 and stub["prefilter"].startswith("gap_le:")
    # a config-only change: second variant, WB2, module copied unchanged apart from the header
    r2 = W.spawn(L3, "refire_cooldown=2", out_dir=tmp_path, today="2026-11-14")
    assert r2["id"] == f"{L3}-WB2"
    s2 = yaml.safe_load((pdir / f"{L3}-WB2.yaml").read_text())["strategies"][f"{L3}-WB2"]
    assert s2["refire_cooldown"] == 2 and s2["window"] == [950, 1500]
    lines = [json.loads(x) for x in (pdir / "variants.jsonl").read_text().splitlines()]
    assert [x["id"] for x in lines] == [f"{L3}-WB1", f"{L3}-WB2"] and lines[0]["old"] == pytest.approx(3.4603, abs=1e-4)
    assert "WB1" in (pdir / "README.md").read_text() and "WB2" in (pdir / "README.md").read_text()
    assert _hashes() == before                                      # original config + modules untouched
    assert all(f"{L3}-WB" not in k for k in (B._load("primary").get("strategies") or {}))   # nothing reaches an account


def test_spawn_gen_window_keeps_module_window_in_step(tmp_path):
    r = W.spawn(GEN, "window=1330-1500", out_dir=tmp_path, today="2026-11-14")
    assert r["old"] == [1400, 1500] and r["new"] == [1330, 1500]
    p = B.parse_module(tmp_path / GEN / "modules" / f"{GEN}-WB1.py")
    assert tuple(p["consts"]["WINDOW"]) == (1330, 1500) and p["consts"]["CONDS"] == [("breadth", ">", 0.5),
                                                                                      ("macd_hist", ">=", 0.12), ("ret3_atr", "<=", -0.069)]


def test_spawn_rejects_no_change_and_unknown(tmp_path):
    with pytest.raises(ValueError):
        W.spawn(ST7, "cond.rsi_ext=70", out_dir=tmp_path)
    with pytest.raises(KeyError):
        W.spawn(ST7, "no_such_param=1", out_dir=tmp_path)
    assert not (tmp_path / ST7 / "variants.jsonl").exists()
