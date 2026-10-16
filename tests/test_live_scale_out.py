"""Live scale-out (opt-in per setup: `live_scale_out: true` + the setup's own scale_out_r; fix 2026-10-16).

Until 2026-10-16 only the backtest engine scaled out; the owner-approved scale_out_r 0.25 on three Testing 2 setups did
nothing live. The runner now banks floor(qty x scale_out_frac) of a flagged lot once a completed bar reaches
+scale_out_r R from the lot's entry fill, replaces the lot's legs down to the rest with the stop at breakeven, and
reconcile books one row per lot (exit_parts, reason scaled+<remainder exit>). Setups without the flag are untouched.
Educational only - not financial advice."""
from types import SimpleNamespace as NS

import pandas as pd
import pytest

from mcf.backtest.engine import simulate
from mcf.config import load_config
from mcf.execution.alpaca_broker import AlpacaBroker
from mcf.strategies.base import Signal
from mcf.strategies.setups import build_strategies

from test_lots import DAY, NOW, NY, OPEN, FakeAlpaca, ID, _runner

SCALED = ("CWT14-failbrk-orl-p05-long", "CWT14-failbrk-orl-p05-lowvol-long", "CWT14-failbrk-pdl-p05-long")


class ScaleAlpaca(FakeAlpaca):
    """FakeAlpaca whose bracket legs carry their own qty (replaceable, as Alpaca's PATCH /orders allows), reserve that
    qty while working, and fill exactly it."""

    def submit_order(self, req):
        o = super().submit_order(req)
        for leg in o.legs or []:
            leg.qty = o.qty
        return o

    def _reserved(self, sym):
        n = 0.0
        for o in self.orders:
            if o.symbol == sym and o.status == "filled" and o.legs:
                n += max([float(l.qty) for l in o.legs if l.status in OPEN] or [0.0])
        return n

    def replace_order_by_id(self, oid, req):
        leg = next(x for x in self._all() if x.id == oid)
        if req.qty is not None:
            leg.qty = str(req.qty)
        if req.stop_price is not None:
            leg.stop_price = req.stop_price
        self.replaced.append((oid, req.qty, req.stop_price))

    def hit(self, coid, kind, px):
        o = self.by_coid(coid)
        q = 0.0
        for leg in o.legs:
            if (leg.order_type == "limit") == (kind == "target"):
                q = float(leg.qty)
                leg.status, leg.filled_qty, leg.filled_avg_price, leg.filled_at = "filled", str(q), str(px), self._t()
            elif leg.status in OPEN:
                leg.status = "canceled"
        self._net(o.symbol, -(1 if o.side == "buy" else -1) * q)

    def leg(self, coid, kind):
        return next(l for l in self.by_coid(coid).legs if (l.order_type == "limit") == (kind == "target"))


def St(name="A", **params):
    return NS(name=name, params=params)


FLAG = {"live_scale_out": True, "scale_out_r": 0.25, "scale_out_frac": 0.5}


def _r(tmp_path, monkeypatch, strategies, qty=None):
    r, c = _runner(tmp_path, monkeypatch, client=ScaleAlpaca(), strategies=strategies)
    if qty is not None:
        monkeypatch.setattr(r.risk, "size", lambda sig, px: qty)
    return r, c


def _enter(r, name="A", side=1, stop=9.0, target=12.0, now=NOW, scale_out_r=0.25):
    r._enter(Signal("XYZ", name, side, 10, stop=stop, target=target, scale_out_r=scale_out_r, scale_out_frac=0.5),
             10.0, ("XYZ", name), NS(bars=pd.DataFrame({"volume": [1e6] * 5}), avg_dollar_volume=5e8), now)


def _bars(rows, t0=NOW):
    """rows: (open, high, low, close) per minute from t0's minute."""
    idx = pd.date_range(t0.floor("1min"), periods=len(rows), freq="1min")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx).assign(volume=1e5)


def _poll(r, bars):
    now = bars.index[-1] + pd.Timedelta(minutes=1, seconds=5)
    r._now = now
    r.scale_outs(now, {"XYZ": bars})


def _scale_orders(c):
    return [o for o in c.orders if o.client_order_id.endswith("-s")]


def test_scale_split_rounding():
    s = AlpacaBroker.scale_split
    assert [s(q, 0.5) for q in (0, 1, 2, 3, 5, 10, 11)] == [0, 0, 1, 1, 2, 5, 5]
    assert s(4, 0.1) == 1 and s(4, 0.99) == 3       # always banks >= 1 and keeps >= 1


def test_trigger_breakeven_and_one_journal_row(tmp_path, monkeypatch):
    r, c = _r(tmp_path, monkeypatch, [St(**FLAG)])
    _enter(r)
    q = int(float(c.by_coid(ID("A")).qty))
    assert ("XYZ", ID("A")) in r.scaling and q >= 2
    _poll(r, _bars([(10, 10.1, 9.9, 10)]))          # entry not filled yet: nothing happens
    c.fill(ID("A"), 10.0)
    _poll(r, _bars([(10, 10.2, 9.9, 10.1)]))        # +0.2R: below the +0.25R level
    assert not _scale_orders(c)
    c.price["XYZ"] = 10.26
    _poll(r, _bars([(10, 10.2, 9.9, 10.1), (10.1, 10.3, 10.05, 10.2)]))
    n, rem = q // 2, q - q // 2
    (s,) = _scale_orders(c)
    assert s.client_order_id == ID("A") + "-s" and s.side == "sell" and float(s.qty) == n
    stop, tgt = c.leg(ID("A"), "stop"), c.leg(ID("A"), "target")
    assert stop.stop_price == 10.0 and float(stop.qty) == rem and float(tgt.qty) == rem and tgt.limit_price == 12.0
    assert c.pos["XYZ"] == rem and r.scaling == {} and r.health["scale_outs"][0]["qty"] == n
    _poll(r, _bars([(10, 10.2, 9.9, 10.1), (10.1, 10.3, 10.05, 10.2), (10.2, 10.4, 10.2, 10.3)]))
    assert len(_scale_orders(c)) == 1                # once per lot
    # partial: one open lot, not a residual even under a frac above what the scale-out left
    r.risk.residual_frac = 0.6
    r.reconcile(DAY)
    r._sync_open()
    assert r.journal.trades(run_id=r.run_id).empty and r.risk.state.residual == {}
    assert r.health["partial_lots"][0]["scaled_out"] == n
    c.hit(ID("A"), "stop", 10.0)                     # the rest stops at breakeven
    assert "XYZ" not in c.pos
    r.reconcile(DAY)
    (t,) = r.journal.trades(run_id=r.run_id).itertuples()
    assert t.exit_reason == "scaled+breakeven" and t.shares == q
    assert t.pnl == pytest.approx(0.26 * n) and t.exit == pytest.approx((10.26 * n + 10.0 * rem) / q)
    assert f"scaleout:{n:g}@10.26" in t.meta and "XYZ" not in r.lots


def test_short_lot_scales_and_runner_hits_target(tmp_path, monkeypatch):
    r, c = _r(tmp_path, monkeypatch, [St(**FLAG)], qty=7)
    _enter(r, side=-1, stop=11.0, target=9.0)
    c.fill(ID("A"), 10.0)
    c.price["XYZ"] = 9.75
    _poll(r, _bars([(10, 10.1, 9.75, 9.8)]))
    (s,) = _scale_orders(c)
    assert s.side == "buy" and float(s.qty) == 3 and c.leg(ID("A"), "stop").stop_price == 10.0 and c.pos["XYZ"] == -4
    c.hit(ID("A"), "target", 9.0)
    r.reconcile(DAY)
    (t,) = r.journal.trades(run_id=r.run_id).itertuples()
    assert t.exit_reason == "scaled+target" and t.pnl == pytest.approx(3 * 0.25 + 4 * 1.0)


@pytest.mark.parametrize("bar,why", [((10, 10.3, 8.9, 9.0), "stop"), ((10, 10.4, 9.9, 10.3), "target")])
def test_bar_touching_scale_level_and_stop_or_target_never_scales(tmp_path, monkeypatch, bar, why):
    """simulate(): a bar that touches the stop (or the target) and the scale level is a stop (target) exit."""
    r, c = _r(tmp_path, monkeypatch, [St(**FLAG)])
    _enter(r, target=10.4)
    c.fill(ID("A"), 10.0)
    _poll(r, _bars([bar]))
    assert not _scale_orders(c) and r.scaling == {} and not c.replaced


def test_setups_without_the_flag_never_scale_out(tmp_path, monkeypatch):
    # B inherits exits.scale_out_r (1.0) the way build_strategies merges it, but has no live_scale_out flag
    r, c = _r(tmp_path, monkeypatch, [St("B", scale_out_r=1.0, scale_out_frac=0.5), St("C", live_scale_out=True)])
    _enter(r, "B", scale_out_r=1.0)
    _enter(r, "C", scale_out_r=None)                 # flag without a scale_out_r: nothing to do
    assert r.scaling == {}
    for n in "BC":
        c.fill(ID(n), 10.0)
    c.price["XYZ"] = 11.5
    _poll(r, _bars([(10, 11.5, 9.9, 11.4)]))
    assert not _scale_orders(c) and not c.replaced


def test_qty_below_two_is_never_scaled(tmp_path, monkeypatch):
    r, c = _r(tmp_path, monkeypatch, [St(**FLAG)], qty=1)
    _enter(r)
    c.fill(ID("A"), 10.0)
    c.price["XYZ"] = 10.3
    _poll(r, _bars([(10, 10.3, 9.9, 10.2)]))
    assert not _scale_orders(c) and not c.replaced and r.scaling == {} and c.pos["XYZ"] == 1


def test_time_stop_after_scale_out_closes_only_what_is_left(tmp_path, monkeypatch):
    r, c = _r(tmp_path, monkeypatch, [St(**FLAG)], qty=10)
    _enter(r)
    c.fill(ID("A"), 10.0)
    c.price["XYZ"] = 10.25
    _poll(r, _bars([(10, 10.3, 9.9, 10.2)]))
    assert c.pos["XYZ"] == 5
    assert r.broker.close_mcf_lot("XYZ", ID("A"), "mcf-", sleep=lambda s: None)
    assert float(c.by_coid(ID("A") + "-x").qty) == 5 and "XYZ" not in c.pos


def test_config_flags_exactly_the_three_testing2_setups(monkeypatch):
    monkeypatch.setenv("MCF_ACCOUNT", "testing2")
    cfg = load_config()
    flagged = {n for n, p in cfg["strategies"].items() if (p or {}).get("live_scale_out")}
    assert flagged == set(SCALED)
    assert all(cfg["strategies"][n]["scale_out_r"] == 0.25 for n in SCALED)
    for acct in ("primary", "testing"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        assert not any((p or {}).get("live_scale_out") for p in load_config()["strategies"].values())
    with pytest.raises(ValueError, match="own scale_out_r"):
        build_strategies({"exits": {"scale_out_r": 1.0}, "strategies": {"x": {"live_scale_out": True}}})


# ---------------------------------------------------------------- parity with simulate() on a synthetic path
def _live_vs_backtest(tmp_path, monkeypatch, side, rows, stop, target):
    """Market long/short: signal on bar 0 (09:59), entry at bar 1's open (10:00). The broker fake fills the lot's legs
    when a bar touches them (at the leg price), the scale-out at the touched level; every bar is then polled."""
    t0 = pd.Timestamp("2026-10-13 09:59", tz=NY)
    bars = _bars(rows, t0)
    sig = Signal("XYZ", "A", side, 0, stop=stop, target=target, scale_out_r=0.25, scale_out_frac=0.5)
    bt = simulate(sig, bars, pd.Timestamp("15:55").time(), 0.0)

    r, c = _r(tmp_path, monkeypatch, [St(**FLAG)], qty=10)
    _enter(r, side=side, stop=stop, target=target, now=NOW)
    c.fill(ID("A"), bars.open.iloc[1])
    level = bars.open.iloc[1] + side * 0.25 * side * (bars.open.iloc[1] - stop)
    for k in range(1, len(bars)):
        hi, lo = bars.high.iloc[k], bars.low.iloc[k]
        st, tg = c.leg(ID("A"), "stop"), c.leg(ID("A"), "target")
        if st.status in OPEN and ((lo <= st.stop_price) if side == 1 else (hi >= st.stop_price)):
            c.hit(ID("A"), "stop", st.stop_price)
        elif tg.status in OPEN and ((hi >= tg.limit_price) if side == 1 else (lo <= tg.limit_price)):
            c.hit(ID("A"), "target", tg.limit_price)
        c.price["XYZ"] = level
        _poll(r, bars.iloc[1:k + 1])
    r.reconcile(DAY)
    (t,) = r.journal.trades(run_id=r.run_id).itertuples()
    return bt, t


@pytest.mark.parametrize("side,rows,stop,target,reason", [
    # +0.25R touched on bar 2, the rest stops at breakeven on bar 3
    (1, [(10, 10, 10, 10), (10, 10.1, 9.9, 10), (10.1, 10.3, 10.05, 10.2), (10.2, 10.2, 9.95, 10), (10, 10, 10, 10)],
     9.0, 11.0, "scaled+breakeven"),
    # short: scaled on bar 1, target on bar 3
    (-1, [(10, 10, 10, 10), (10, 10.1, 9.7, 9.8), (9.8, 9.9, 9.5, 9.6), (9.6, 9.6, 8.9, 9.0), (9, 9, 9, 9)],
     11.0, 9.0, "scaled+target"),
    # scale level and stop in one bar: a full stop, no scale-out
    (1, [(10, 10, 10, 10), (10, 10.3, 8.9, 9.0), (9, 9, 9, 9)], 9.0, 11.0, "stop"),
])
def test_parity_with_backtest_engine(tmp_path, monkeypatch, side, rows, stop, target, reason):
    bt, live = _live_vs_backtest(tmp_path, monkeypatch, side, rows, stop, target)
    assert bt.exit_reason == live.exit_reason == reason
    assert live.r_multiple == pytest.approx(bt.r_multiple) and live.exit == pytest.approx(bt.exit)
