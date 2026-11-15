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


# ------------------------------------------------------------------ Workbench v2: engine view + trade teardown (2026-11-15)
from mcf.report import engine as E  # noqa: E402


def test_engine_parts_numbering_and_roles_L3():
    bp = B.extract(L3, with_record=False)
    st = E.engine_parts(bp)
    assert [s["key"] for s in st] == ["INTAKE", "TIMER", "SENSORS", "GATES", "ENTRY", "EXHAUST"]
    pids = [p["pid"] for p in E.all_parts(st)]
    assert pids == [f"P{i}" for i in range(1, len(pids) + 1)]
    sens = {p["role"]: p["value"] for p in st[2]["parts"]}
    assert sens == {"cond.fromOpen": "fromOpen > 3.4603", "cond.gap": "gap <= -2.6574",
                    "cond.sma20_slope_pct": "sma20_slope_pct > 0.3724"}
    roles = {p["role"] for p in E.all_parts(st)}
    assert {"prefilter", "borrow", "window", "noentry", "refire", "cap_setup", "latch", "order", "risk", "stop", "target",
            "time"} <= roles
    assert E.pref(st, "stop") and E.pref(st, "time") != E.pref(st, "stop") and E.pref(st, "nope") == ""
    assert int(E.pref(st, "time")[1:]) > int(E.pref(st, "cond.gap")[1:]) > int(E.pref(st, "window")[1:])   # left to right


def test_engine_stack_sensor_checks_ST7():
    bp = B.extract(ST7, with_record=False)
    st = E.engine_parts(bp)
    ck = [E.sensor_check(c, "long") for c in bp["module"]["conds"]]
    assert [(c["col"], c["op"], c["thr"], c["cross"]) for c in ck] == [("rsi", "<", 50.0, True), ("rsi", "<=", 30.0, False),
                                                                       ("fromOpen", "<", -1.0, False), ("buyPressure", ">", 0.0, False)]
    assert st[2]["parts"][0]["label"].startswith("Trigger: RSI(14) crosses below 50")
    assert "borrow" not in {p["role"] for p in E.all_parts(st)}          # long setup: no short-borrow part


def test_heat_and_pick():
    bp = B.extract(L3, with_record=False)
    st = E.engine_parts(bp)
    tr = [dict(id=i, r=r, exit_reason=x, acct="primary") for i, (r, x) in
          enumerate([(-1.2, "stop"), (1.0, "target"), (0.3, "flatten"), (-1.7, "stop")])]
    sig = [dict(status="submitted", reason="ok")] * 4 + [dict(status="skipped", reason="not shortable/ETB")] * 4 + \
          [dict(status="skipped", reason="setup daily loss limit")] * 2
    h = E.apply_heat(st, tr, sig)
    parts = {p["role"]: p for p in E.all_parts(st)}
    assert parts["stop"]["heat"] == 0.5 and parts["target"]["heat"] == 0.25 and parts["time"]["heat"] == 0.25
    assert parts["borrow"]["heat"] == 0.4 and parts["latch"]["heat"] == 0.2 and parts["window"]["heat"] is None
    assert h["exits"] == {"stop": 2, "target": 1, "time": 1}
    assert [t["id"] for t in E.pick_trades(tr, "worst2")] == [3, 0] and E.pick_trades(tr, "best1")[0]["id"] == 1
    assert E.pick_trades(tr, "id:primary:2")[0]["id"] == 2 and E.pick_trades(tr, "id:9") == []
    with pytest.raises(ValueError):
        E.pick_trades(tr, "median")


def _synthetic_day(day="2026-11-10", n_days=25):
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(7)
    frames, px = [], 20.0
    for d in pd.bdate_range(end=day, periods=n_days):
        idx = pd.date_range(f"{d.date()} 09:30", periods=390, freq="1min", tz=E.TZ)
        if str(d.date()) == day:
            px *= 0.96                                                  # gap down, then a steady rally from the open
            steps = np.r_[np.full(60, 0.0012), rng.normal(0, 0.0004, 330)]
        else:
            steps = rng.normal(0, 0.0008, 390)
        c = px * np.exp(np.cumsum(steps))
        o = np.r_[px, c[:-1]]
        frames.append(pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0005, "low": np.minimum(o, c) * 0.9995,
                                    "close": c, "volume": 1000.0}, index=idx))
        px = c[-1]
    return pd.concat(frames)


def test_teardown_synthetic_trade_cites_engine_parts(tmp_path):
    bp = B.extract(L3, with_record=False)
    st = E.engine_parts(bp)
    m1 = _synthetic_day()
    fr = E.lab_frame(m1)
    day = m1[m1.index.date == m1.index[-1].date()]
    ent = float(day["close"].iloc[61])
    t = dict(id=1, acct="primary", symbol="SYN", side=-1, date="2026-11-10", signal_time="2026-11-10T15:31:10+00:00",
             entry_time="2026-11-10 15:31:12+00:00", entry=ent, stop=ent * 1.01, target=ent * 0.99,
             exit_time="2026-11-10 17:02:00+00:00", exit=ent * 1.011, exit_reason="stop", r=-1.1, mfe_r=0.2, mae_r=-1.05,
             shares=100, slip_bps=1.0)
    td = E.teardown_data(bp, st, t, m1, fr)
    assert str(td["sb"].time()) == "10:25:00"                         # bucket 10:25-10:30 closed before the 10:31 signal
    tags = [c["tag"] for c in td["callouts"]]
    assert tags == ["A", "B", "C", "D", "E"]
    txt = {c["tag"]: c["text"] for c in td["callouts"]}
    assert E.pref(st, "stop") + " stop hit" in txt["E"] and txt["B"].startswith(E.pref(st, "order"))
    assert E.pref(st, "window") in txt["A"]
    sens = {x["pid"]: x for x in td["sensors"]}
    assert set(sens) == {E.pref(st, k) for k in ("cond.fromOpen", "cond.gap", "cond.sma20_slope_pct")}
    assert sens[E.pref(st, "cond.fromOpen")]["value"] > 3.46 and sens[E.pref(st, "cond.fromOpen")]["ok"]
    out = tmp_path / "td.png"
    E.render_teardown(bp, st, td, out)
    assert out.stat().st_size > 20000
    E.render_engine(bp, st, None, tmp_path / "eng.png")
    assert (tmp_path / "eng.png").stat().st_size > 20000
    md = "\n".join(E.engine_markdown(st, None) + E.teardown_markdown(td, "td.png"))
    assert "| P1 | INTAKE |" in md and "stop hit" in md


def test_daily_priors_override_gap():
    import pandas as pd

    m1 = _synthetic_day()
    fr = E.lab_frame(m1)
    days = sorted(set(m1.index.date))
    daily = pd.DataFrame({"open": 1.0, "high": 30.0, "low": 10.0, "close": 25.0, "volume": 1.0}, index=days[:-1])
    f2 = E.apply_daily(fr, daily, str(days[-1]))
    row = f2[f2.index.date == days[-1]].iloc[0]
    o = float(m1[m1.index.date == days[-1]]["open"].iloc[0])
    assert abs(row["gap"] - (o / 25.0 - 1) * 100) < 1e-6 and abs(row["atr_d"] - 20.0) < 1e-9
