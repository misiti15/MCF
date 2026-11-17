"""Shadow mode (owner 2026-11-16): shadow never places orders or uses account resources, shadow lot lifecycle, journal
separation by run, trust-check metrics on a synthetic day, effective-session math, leaderboard band with and without
shadow data. Educational only - not financial advice."""
import json
import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from mcf.config import load_config
from mcf.execution import runner as R
from mcf.execution import shadow as SH
from mcf.journal import Journal
from mcf.research import effective as E
from mcf.research import shadow_calib as C
from mcf.strategies.base import Signal

NY = "America/New_York"
ROOT = Path(__file__).resolve().parents[1]


class Broker:
    def __init__(self):
        self.submitted, self.cancels, self.held = [], [], {}

    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):
        return dict(self.held)

    def submit_bracket(self, sig, qty, coid):
        self.submitted.append(coid)
        return SimpleNamespace(id=f"o{len(self.submitted)}")

    def cancel(self, *a, **k):          # never called by shadow
        self.cancels.append(a)

    def __getattr__(self, name):        # any other broker call by shadow would show up here
        if name.startswith(("close", "move", "scale", "flatten", "cancel")):
            raise AssertionError(f"broker.{name} called")
        raise AttributeError(name)


class Strat:
    """Fires once per symbol on the bar at `at` (HH:MM, the decision bar), long by default."""

    def __init__(self, name, at="10:00", side=1, stop_off=1.0, tgt_off=2.0, **sig_kw):
        self.name, self.at, self.side, self.stop_off, self.tgt_off, self.kw = name, at, side, stop_off, tgt_off, sig_kw
        self.params = {}
        self.calls = 0

    def eligible(self, ctx):
        return True

    def signals(self, ctx):
        self.calls += 1
        last = len(ctx.bars) - 1
        if f"{ctx.bars.index[-1]:%H:%M}" == self.at:
            px = float(ctx.bars["close"].iloc[-1])
            yield Signal(ctx.symbol, self.name, self.side, last, stop=px - self.side * self.stop_off,
                         target=None if self.tgt_off is None else px + self.side * self.tgt_off, **self.kw)


def _bars(day="2026-11-16", start="09:30", n=60, px=100.0, path=None):
    idx = pd.date_range(f"{day} {start}", periods=n, freq="1min", tz=NY)
    c = [px] * n if path is None else list(path) + [path[-1]] * (n - len(path))
    return pd.DataFrame({"open": c, "high": [x + 0.05 for x in c], "low": [x - 0.05 for x in c], "close": c,
                         "volume": [1e6] * n}, index=idx)


def _runner(tmp_path, monkeypatch, live=(), extras=(), cfg_over=None):
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["live"]["no_entry_before"] = "09:50"
    cfg["shadow"] = {"enabled": True, "of_live": True, "budget_frac": 0.10, "latency_bps": 0.0}
    cfg["shadow_setups"] = []
    for k, v in (cfg_over or {}).items():
        cfg.setdefault(k, {}).update(v)
    b = Broker()
    r = R.PaperRunner(cfg, list(live), {}, broker=b)
    r.dry_run = False
    if extras:
        r.shadow.extras = list(extras)
        r.shadow.extra_names = {s.name for s in extras}
    r.restore(pd.Timestamp("2026-11-16").date())
    live_q = []
    monkeypatch.setattr(r, "_quote", lambda sym: (live_q.append(sym), r._poll_quotes.__setitem__(sym, (99.99, 100.01, None)),
                                                  (99.99, 100.01))[-1])
    monkeypatch.setattr(r.shadow, "fetch_quotes", lambda syms: {s: (99.99, 100.01, None) for s in syms})
    monkeypatch.setattr(r, "_check_data", lambda now, bars: False)
    r._live_quotes = live_q
    return r, b


def _poll(r, monkeypatch, now, bars):
    """One runner poll at `now` on `bars` (symbol -> full-day 1-minute bars; the poll sees bars before its minute)."""
    cut = pd.Timestamp(now).floor("1min")
    seen = {s: b[b.index < cut] for s, b in bars.items()}
    r.bars = dict(seen)
    monkeypatch.setattr(r, "fetch", lambda now: seen)
    monkeypatch.setattr(r, "_contexts", lambda b, today: [SimpleNamespace(symbol=s, bars=x, avg_dollar_volume=5e8)
                                                          for s, x in b.items()])
    r.step(pd.Timestamp(now))


def _t(hhmm):
    return pd.Timestamp(f"2026-11-16 {hhmm}:03", tz=NY)


# --------------------------------------------------------------------------------------- no orders, no resources
def test_shadow_never_places_orders_or_uses_account_resources(tmp_path, monkeypatch):
    live = Strat("LIVE1")
    extra = Strat("ONLY1")
    r, b = _runner(tmp_path, monkeypatch, live=[live], extras=[extra])
    r.risk.a["max_concurrent_positions"] = 0                # the account has no free slot: live must skip
    bars = {"AAA": _bars(n=120)}
    _poll(r, monkeypatch, _t("10:01"), bars)
    assert b.submitted == [] and b.cancels == []
    sig = r.journal.signals(r.run_id, "2026-11-16")
    assert list(sig.status) == ["skipped"] and sig.reason.iloc[0] == "max concurrent positions"
    # shadow took both: the live setup (blocked by the slot) and the shadow-only one
    assert {l["strategy"] for l in r.shadow.lots.values()} == {"LIVE1", "ONLY1"}
    st = r.risk.state
    assert st.trades_today == 0 and not st.open_symbols and not st.halted and not r.lots and not r.pending
    assert not r.managed and not r.scaling and "AAA" not in r.fired
    # shadow-of-live reuses the live signal objects: the live strategy was called once, not twice
    assert live.calls == 1 and extra.calls == 1
    # free the slot: live enters AAA once; shadow keeps its own book
    r.risk.a["max_concurrent_positions"] = 10
    live2 = Strat("LIVE2", at="10:05")
    r.strategies.append(live2)
    _poll(r, monkeypatch, _t("10:06"), bars)
    assert b.submitted == ["mcf-LIVE2-AAA-20261116-1005"] if r.same_setup_reentry else len(b.submitted) == 1
    assert r.risk.state.trades_today == 1                   # only the real entry counted
    assert sum(1 for l in r.shadow.lots.values() if l["strategy"] == "LIVE2") == 1


def test_shadow_respects_live_timing_gates(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch, extras=[Strat("EARLY", at="09:40")])
    _poll(r, monkeypatch, _t("09:41"), {"AAA": _bars(n=60)})
    assert not r.shadow.lots
    s = r.journal.signals(r.shadow.run_id, "2026-11-16")
    sk = s[s.status == "shadow_skipped"]
    assert len(sk) == 1 and sk.reason.iloc[0].startswith("before 09:50")


# --------------------------------------------------------------------------------------- lot lifecycle
def _one_lot(tmp_path, monkeypatch, path, polls, strat=None):
    r, b = _runner(tmp_path, monkeypatch, extras=[strat or Strat("S", tgt_off=2.0)])
    bars = {"AAA": _bars(n=390, path=path)}
    for p in polls:
        if p == "flatten":
            r.bars = {s: x[x.index < _t("15:55").floor("1min")] for s, x in bars.items()}
            r._shadow_flatten(_t("15:55"))
        else:
            _poll(r, monkeypatch, _t(p), bars)
    tr = r.journal.trades(run_id=r.shadow.run_id)
    return r, b, tr


def _path(moves: dict, base=100.0, n=390):
    """Close path: bar i (09:30 + i min) = base unless set in moves {HH:MM: price}."""
    out = [base] * n
    for k, v in moves.items():
        h, m = map(int, k.split(":"))
        out[(h - 9) * 60 + m - 30] = v
    return out


def test_shadow_lot_hits_target(tmp_path, monkeypatch):
    r, b, tr = _one_lot(tmp_path, monkeypatch, _path({"10:03": 102.5}), ["10:01", "10:02", "10:05"])
    assert len(tr) == 1 and tr.exit_reason.iloc[0] == "target"
    row = tr.iloc[0]
    assert row.entry == pytest.approx(100.01 + 0.072, abs=1e-4)   # fills B: ask + 2.0 x 3.6 bp median slip (min 2 cents)
    assert "fill_model=B:" in row.meta
    assert row.exit == pytest.approx(102.5)                 # gap through the 102.0 target: the bar's open
    assert row.pnl_adj < row.pnl                            # LR8 costs in
    assert "mode=only" in row.meta and row.broker_order_id.startswith("shadow-S-AAA-20261116-")
    assert not r.shadow.lots and b.submitted == []


def test_shadow_lot_hits_stop(tmp_path, monkeypatch):
    r, b, tr = _one_lot(tmp_path, monkeypatch, _path({"10:02": 99.5, "10:03": 98.0}), ["10:01", "10:03", "10:04"])
    assert len(tr) == 1 and tr.exit_reason.iloc[0] == "stop"
    row = tr.iloc[0]
    assert row.exit < 99.0                                  # gap through the 99.0 stop: the open, less half the spread
    risk = abs(row.entry - row.stop) * row.shares
    assert row.pnl_adj / risk < -1.0                        # a gap stop loses more than 1R after costs


def test_shadow_lot_time_stop_and_flatten(tmp_path, monkeypatch):
    s = Strat("TS", tgt_off=None, time_stop_min=10, time_stop_min_r=0.5)
    r, b, tr = _one_lot(tmp_path, monkeypatch, _path({}), ["10:01", "10:05", "10:12"], strat=s)
    assert len(tr) == 1 and tr.exit_reason.iloc[0] == "timestop"
    r, b, tr = _one_lot(tmp_path / "f", monkeypatch, _path({}), ["10:01", "10:30", "flatten"], strat=Strat("FL", tgt_off=None))
    assert len(tr) == 1 and tr.exit_reason.iloc[0] == "flatten"
    o = pd.read_sql("SELECT status FROM orders WHERE run_id=?", r.journal.db, params=[r.shadow.run_id])
    assert list(o.status) == ["closed"]


def test_shadow_breakeven_and_restart_restore(tmp_path, monkeypatch):
    s = Strat("BE", tgt_off=None, be_at_r=1.0)
    r, b = _runner(tmp_path, monkeypatch, extras=[s])
    bars = {"AAA": _bars(n=390, path=_path({"10:02": 101.2, "10:05": 99.9}))}
    _poll(r, monkeypatch, _t("10:01"), bars)
    _poll(r, monkeypatch, _t("10:03"), bars)
    lot = next(iter(r.shadow.lots.values()))
    assert lot["stop"] == pytest.approx(100.0)             # +1R reached: stop to breakeven (reference price)
    # a new job (restart) picks the open lot and today's dedupe up from the shadow run
    r2, _ = _runner(tmp_path, monkeypatch, extras=[Strat("BE", tgt_off=None, be_at_r=1.0)])
    assert set(r2.shadow.lots) == set(r.shadow.lots) and r2.shadow.lots[lot["sid"]]["stop"] == pytest.approx(100.0)
    _poll(r2, monkeypatch, _t("10:06"), bars)
    tr = r2.journal.trades(run_id=r2.shadow.run_id)
    assert len(tr) == 1 and tr.exit_reason.iloc[0] == "stop" and tr.exit.iloc[0] > 99.8   # at breakeven, not 99.0


# --------------------------------------------------------------------------------------- journal separation
def test_journal_separation_by_run(tmp_path, monkeypatch):
    r, b, tr = _one_lot(tmp_path, monkeypatch, _path({"10:03": 102.5}), ["10:01", "10:05"])
    runs = r.journal.runs().set_index("id")
    assert runs.loc[1, "kind"] == "paper" and runs.loc[2, "kind"] == "whatif" and runs.loc[3, "kind"] == "shadow"
    assert r.shadow.run_id == 3 == SH.shadow_run_id(r.journal)
    assert r.journal.trades(run_id=r.run_id).empty and r.journal.signals(r.run_id).empty
    assert len(r.journal.trades(kind="shadow")) == 1 and r.journal.trades(kind="whatif").empty
    assert r.journal.open_orders(r.run_id).empty            # live restore never sees shadow lots


def test_reports_exclude_shadow_trades():
    for p in ("mcf/report/daily_post.py", "mcf/report/team.py", "mcf/report/reconcile_pl.py"):
        src = (ROOT / p).read_text()
        assert "r.kind != 'whatif'" not in src and "NOT IN ('whatif', 'shadow')" in src, p


# --------------------------------------------------------------------------------------- trust check
def _sig(day, setup, sym, side, bar, status, reason="ok", oid=None, mode=None):
    info = {"bar_time": bar}
    if mode:
        info["mode"] = mode
    return {"day": day, "ts": f"{day}T{bar[:2]}:{bar[2:]}:03-05:00", "symbol": sym, "strategy": setup, "side": side,
            "status": status, "reason": reason, "broker_order_id": oid, "info": json.dumps(info)}


def _tr(day, setup, oid, r_after, entry=100.0, stop=99.0, shares=100):
    return {"date": day, "strategy": setup, "broker_order_id": oid, "entry": entry, "stop": stop, "shares": shares,
            "pnl": r_after * 100, "pnl_adj": r_after * 100, "exit_time": f"{day}T15:55:00"}


def test_calibration_metrics_on_synthetic_day():
    d = "2026-11-16"
    ls = pd.DataFrame([_sig(d, "AB-x", "AAA", 1, "1000", "submitted", oid="L1"),
                       _sig(d, "AB-x", "BBB", 1, "1010", "submitted", oid="L2"),
                       _sig(d, "AB-x", "CCC", -1, "1100", "submitted", oid="L3"),     # shadow misses it
                       _sig(d, "AB-x", "DDD", 1, "1200", "skipped", "max concurrent positions")])
    lt = pd.DataFrame([_tr(d, "AB-x", "L1", 1.0), _tr(d, "AB-x", "L2", -1.0), _tr(d, "AB-x", "L3", 0.5)])
    ss = pd.DataFrame([_sig(d, "AB-x", "", 0, "0000", "shadow_session", mode="of_live"),
                       _sig(d, "AB-x", "AAA", 1, "1001", "shadow_entered", oid="S1", mode="of_live"),   # +1 min: match
                       _sig(d, "AB-x", "BBB", 1, "1010", "shadow_entered", oid="S2", mode="of_live"),
                       _sig(d, "AB-x", "DDD", 1, "1200", "shadow_entered", oid="S3", mode="of_live"),   # resource
                       _sig(d, "AB-x", "EEE", 1, "1300", "shadow_entered", oid="S4", mode="of_live"),   # extra
                       _sig(d, "ZZ-only", "AAA", 1, "1000", "shadow_entered", oid="S5", mode="only")])
    st = pd.DataFrame([_tr(d, "AB-x", "S1", 1.02), _tr(d, "AB-x", "S2", -0.98), _tr(d, "AB-x", "S3", 2.0),
                       _tr(d, "AB-x", "S4", 0.3), _tr(d, "ZZ-only", "S5", 1.0)])
    rows = C.day_rows(ls, lt, ss, st, d, "t")
    assert [x["setup"] for x in rows] == ["AB-x"]           # shadow-only setups are not part of the trust check
    x = rows[0]
    assert (x["live_entries"], x["shadow_entries"], x["matched"], x["missing"], x["extra"], x["resource_blocked"]) == \
        (3, 4, 2, 1, 1, 1)
    assert x["r_n"] == 2 and x["r_sum"] == pytest.approx(0.04)
    s = C.summarize(rows * 3 and [dict(r, day=f"2026-11-1{i}") for i, r in enumerate(rows * 3, 3)])
    o = s["overall"]
    assert o["match"] == pytest.approx(2 / 3, abs=1e-3) and o["extra_rate"] == pytest.approx(1 / 3, abs=1e-3)
    assert o["bias_r"] == pytest.approx(0.02)                # shadow 0.02R optimistic per matched trade
    f = s["families"]["AB"]
    assert f["optimistic"] and f["tier"] == "uncalibrated" and f["haircut_r"] == pytest.approx(0.04)
    assert s["setups"]["AB-x"]["gap_r"] == pytest.approx(0.02)


def test_calibration_tiers():
    c = E.load()
    assert E.tier(0.99, 0.01, -0.005, -0.5, 5, 100, c) == ("calibrated", 0.35)
    assert E.tier(0.99, 0.01, 0.02, 3.0, 5, 100, c) == ("partial", 0.2)       # optimistic: never the top tier
    assert E.tier(0.99, 0.05, 0.0, 0.0, 5, 100, c) == ("partial", 0.2)        # too many extra trades
    assert E.tier(0.96, 0.01, 0.0, 0.0, 5, 100, c) == ("partial", 0.2)
    assert E.tier(0.90, 0.01, 0.0, 0.0, 5, 100, c) == ("below", 0.0)
    assert E.tier(0.99, 0.0, 0.0, 0.0, 1, 100, c) == ("uncalibrated", 0.2)    # too few held-out days


# --------------------------------------------------------------------------------------- effective sessions
def test_effective_session_math():
    c = E.load()
    assert c["live_weight"] == 1.0 and c["haircut_extra_r"] == 0.02 and c["on_deck_min_live_sessions"] == 5
    assert c["history_weight"] == 0.175
    assert E.effective_sessions(4, 6, 10, 0.35, 0.2, c) == pytest.approx(4 + 0.35 * 6 + 0.2 * 10)
    assert E.effective_sessions(2, 3, 0, cfg=c) == pytest.approx(2 + 0.6)      # uncalibrated shadow = lower tier
    assert E.effective_sessions(0, 0, 0, cfg=c, history=40) == pytest.approx(7.0)
    assert E.haircut(0.03, c) == pytest.approx(0.05) and E.haircut(-0.01, c) == pytest.approx(0.02)
    assert E.replay_weight(c) == ("below", 0.0)   # held-out 2026-11-17: 87.1% match, 26.2% extra -> below the 95% tier
    assert not E.on_deck_ready(4, c) and E.on_deck_ready(5, c)


def test_claude_md_records_effective_sessions():
    md = (ROOT / "CLAUDE.md").read_text()
    assert "Effective sessions" in md and "config/effective_sessions.json" in md and "0.35" in md and "0.175" in md


# --------------------------------------------------------------------------------------- shadow scorecard + dashboard
def test_shadow_scorecard_from_journal(tmp_path, monkeypatch):
    from mcf.report import shadow_card

    r, b, tr = _one_lot(tmp_path, monkeypatch, _path({"10:03": 102.5}), ["10:01", "10:05"])
    card = shadow_card.build(r.journal, "testing", global_summary={})
    s = card["setups"]["S"]
    assert s["trades"] == 1 and s["shadow_days"] == ["2026-11-16"] and s["live_days"] == []
    assert s["avg_r_haircut"] == pytest.approx(s["avg_r"] - 0.02) and s["weight"] == 0.2
    p = shadow_card.save(card, tmp_path)
    assert json.loads(p.read_text())["account"] == "testing"


def _band_js() -> str:
    html = (ROOT / "docs" / "live" / "index.html").read_text()
    m = re.search(r"// SHADOW-BAND-BEGIN.*?// SHADOW-BAND-END", html, re.S)
    assert m, "shadow band helper missing"
    return m.group(0)


def test_leaderboard_band_columns_present():
    html = (ROOT / "docs" / "live" / "index.html").read_text()
    for k, h in (("sh_live_sess", "Live sessions"), ("sh_sess", "Shadow sessions"), ("sh_rp_sess", "Replay sessions"),
                 ("sh_eff", "Effective sessions"), ("sh_trades", "Shadow trades"),
                 ("sh_avg_r", "Shadow avg R (after haircut)"), ("sh_gap", "Shadow vs live gap")):
        assert f'["{k}", "{h}"]' in html and f'{k}: "shadow"' in html and f"{k}: `<td" in html and f"{k}:" in html
    assert "Shadow / replay" in html and "shadow_scorecard.json" in html and "--band-shadow" in html


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_leaderboard_band_renders_with_and_without_shadow_data(tmp_path):
    js = _band_js() + """
const rows = () => [{ setup: "AB-x", sessions_traded: 4, rp_sessions: 10 }, { setup: "NEW-1", sessions_traded: 0, rp_sessions: null }];
const none = window.MCF_SHADOW.apply(rows(), [], null, null);
const cards = [{ setups: { "AB-x": { live_days: ["2026-11-16", "2026-11-17"], shadow_days: ["2026-11-17"], trades: 4, total_r: 2.0,
    trades_only: 0, gap_r: 0.01, gap_n: 4, weight: 0.3, tier: "uncalibrated", haircut_r: 0.02 },
  "NEW-1": { live_days: [], shadow_days: ["2026-11-16", "2026-11-17", "2026-11-18"], trades: 6, total_r: -0.6, trades_only: 6,
    gap_n: 0, weight: 0.2, tier: "uncalibrated", haircut_r: 0.02 } } }];
const sum = { families: { AB: { tier: "calibrated", weight: 0.35, haircut_r: 0.02 } } };
const withd = window.MCF_SHADOW.apply(rows(), cards, null, sum);
console.log(JSON.stringify({ none, withd }));
"""
    f = tmp_path / "b.js"
    f.write_text("const window = {};\n" + js)
    out = json.loads(subprocess.run(["node", str(f)], capture_output=True, text=True, check=True).stdout)
    a, n = out["none"]
    assert a["sh_trades"] is None and a["sh_avg_r"] is None and a["sh_gap"] is None
    assert a["sh_eff"] == pytest.approx(4 + 0.2 * 10) and n["sh_eff"] == 0
    a, n = out["withd"]
    assert a["sh_live_sess"] == 4 and a["sh_sess"] == 0     # the shadow day was also a live day: not counted twice
    assert a["sh_eff"] == pytest.approx(4 + 0.2 * 10) and a["sh_w"] == 0.35
    assert a["sh_avg_r"] == pytest.approx(0.5 - 0.02) and a["sh_gap"] == pytest.approx(0.01)
    assert n["sh_sess"] == 3 and n["sh_eff"] == pytest.approx(0.2 * 3) and n["sh_avg_r"] == pytest.approx(-0.1 - 0.02)


def test_conservative_fills_touch_is_not_a_target_fill(tmp_path, monkeypatch):
    # target 102.0; the 10:03 bar's high 102.015 is < max(2 cents, 0.03%) through: no fill; 10:04 trades through
    path = _path({"10:03": 101.965, "10:04": 102.3})
    r, b, tr = _one_lot(tmp_path, monkeypatch, path, ["10:01", "10:04"])
    assert tr.empty and len(r.shadow.lots) == 1
    _poll(r, monkeypatch, _t("10:05"), {"AAA": _bars(n=390, path=path)})
    tr = r.journal.trades(run_id=r.shadow.run_id)
    assert len(tr) == 1 and tr.exit_reason.iloc[0] == "target"


def test_conservative_stop_fill_is_worse_than_the_stop(tmp_path, monkeypatch):
    r, b, tr = _one_lot(tmp_path, monkeypatch, _path({"10:03": 99.02}), ["10:01", "10:04"])
    row = tr.iloc[0]
    assert row.exit_reason == "stop" and row.exit == pytest.approx(99.0 - 99.0 * 3e-4, abs=1e-6)   # stop - 0.03%


def test_fill_advice_never_changes_the_profile():
    assert C.fill_advice({"bias_r": 0.01, "r_pairs": 50, "days": 5})["advice"].startswith("tighten to C")
    assert C.fill_advice({"bias_r": -0.02, "r_pairs": 50, "days": 5})["advice"] == "keep B"
    assert C.fill_advice({"bias_r": -0.08, "r_pairs": 50, "days": 5})["advice"].startswith("ease to A")
    assert C.fill_advice({"bias_r": 0.05, "r_pairs": 5, "days": 1})["advice"] == "keep B"
    cfg = load_config()
    assert cfg["shadow"]["fill_profile"] == "B" and cfg["shadow"]["fill_profiles"]["B"]["through_bps"] == 3.0
