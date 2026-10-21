"""Live scale-out (opt-in per setup: `live_scale_out: true` + the setup's own scale_out_r; fix 2026-10-16).

Until 2026-10-16 only the backtest engine scaled out; the owner-approved scale_out_r 0.25 on three Testing 2 setups did
nothing live. The runner now banks floor(qty x scale_out_frac) of a flagged lot once a completed bar reaches
+scale_out_r R from the lot's entry fill. Alpaca refuses a qty change on bracket legs (2026-10-19), so the broker cancels
the lot's stop + target, sells the banked shares (-s) and protects the rest with the lot's own -p order (OCO target +
breakeven stop, or a plain breakeven stop); reconcile books one row per lot (exit_parts, reason scaled+<remainder
exit>). Setups without the flag are untouched. Educational only - not financial advice."""
import itertools
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
    """FakeAlpaca whose bracket legs carry their own qty, reserve it while working and fill exactly it. Like Alpaca, a
    qty change on a bracket/OTO leg is REJECTED ("qty cannot be changed for advanced orders", Testing 2 2026-10-19), so
    the scale-out cancels the legs and protects the rest with the lot's own -p order: an OCO (limit parent = target,
    nested stop leg) or a plain stop, both resting and reserving their qty. `log` records cancels and submits in order;
    `on_cancel(oid)` runs before a cancel (a leg filling meanwhile); `reject_protect` refuses that many -p submits."""

    def __init__(self):
        super().__init__()
        self.log, self.on_cancel, self.reject_protect = [], None, 0

    def submit_order(self, req):
        oc = _v(getattr(req, "order_class", None) or "")
        if oc == "oco" or getattr(req, "stop_price", None) is not None:
            o = self._resting(req, oc)
        else:
            o = super().submit_order(req)
            for leg in o.legs or []:
                leg.qty = o.qty
        self.log.append(("submit", o.client_order_id))
        return o

    def _resting(self, req, oc):
        coid, side, qty = req.client_order_id, _v(req.side), float(req.qty)
        if coid in self.coids:
            raise RuntimeError('{"code":40010001,"message":"client_order_id must be unique"}')
        if self.reject_protect:
            self.reject_protect -= 1
            raise RuntimeError('{"code":42210000,"message":"stop price must be lower than the base price"}')
        if qty > abs(self.pos.get(req.symbol, 0.0)) - self._reserved(req.symbol) + 1e-9:
            raise RuntimeError('{"code":40310000,"message":"insufficient qty available for order"}')
        base = dict(symbol=req.symbol, side=side, qty=str(qty), filled_qty="0", filled_avg_price=None, filled_at=None,
                    submitted_at=self._t(), status="new", rest=True, replaces=None)
        if oc == "oco":
            leg = NS(id=f"leg-{next(_n)}", client_order_id=f"uuid-{next(_n)}", order_type="stop", order_class="oco",
                     stop_price=req.stop_loss.stop_price, limit_price=None, legs=None, **base)
            o = NS(id=f"ord-{next(_n)}", client_order_id=coid, order_type="limit", order_class="oco",
                   limit_price=req.take_profit.limit_price, stop_price=None, legs=[leg], **base)
        else:
            o = NS(id=f"ord-{next(_n)}", client_order_id=coid, order_type="stop", order_class="simple",
                   stop_price=req.stop_price, limit_price=None, legs=None, **base)
        self.coids.add(coid)
        self.orders.append(o)
        return o

    def _reserved(self, sym):
        n = 0.0
        for o in self.orders:
            if o.symbol != sym:
                continue
            if getattr(o, "rest", False):
                n += float(o.qty) - float(o.filled_qty) if o.status in OPEN else 0.0
            elif o.status == "filled" and o.legs:
                n += max([float(l.qty) for l in o.legs if l.status in OPEN] or [0.0])
        return n

    def cancel_order_by_id(self, oid):
        if self.on_cancel:
            self.on_cancel(oid)
        self.log.append(("cancel", oid))
        super().cancel_order_by_id(oid)

    def replace_order_by_id(self, oid, req):
        o = next(x for x in self._all() if x.id == oid)
        if req.qty is not None and (o.legs or getattr(o, "order_class", None) == "oco" or not getattr(o, "rest", False)):
            raise RuntimeError('{"code":42210000,"message":"qty cannot be changed for advanced orders"}')
        if getattr(o, "rest", False) and o.legs is None and o.order_class == "simple":   # a new order replaces it
            if req.client_order_id in self.coids:
                raise RuntimeError('{"code":40010001,"message":"client_order_id must be unique"}')
            o.status = "replaced"
            new = NS(**{**o.__dict__, "id": f"ord-{next(_n)}", "status": "new", "replaces": o.id,
                        "stop_price": req.stop_price, "client_order_id": req.client_order_id or f"uuid-{next(_n)}"})
            self.coids.add(new.client_order_id)
            self.orders.append(new)
        else:
            o.stop_price = req.stop_price
        self.replaced.append((oid, req.qty, req.stop_price))

    def _group(self, coid):
        """The lot's working exit orders: its bracket legs, else its protection (the -p series)."""
        legs = [l for l in self.by_coid(coid).legs if l.status in OPEN]
        if legs:
            return legs
        return [x for o in self.orders if AlpacaBroker._is_protect(o.client_order_id, coid) and o.status in OPEN
                for x in (o, *(o.legs or [])) if x.status in OPEN]

    def working(self, coid, kind):
        return next((x for x in self._group(coid) if (x.order_type == "limit") == (kind == "target")), None)

    def hit(self, coid, kind, px):
        """The lot's working stop or target fills (bracket leg or protection); its OCO sibling is cancelled."""
        grp, w = self._group(coid), self.working(coid, kind)
        q = float(w.qty)
        w.status, w.filled_qty, w.filled_avg_price, w.filled_at = "filled", str(q), str(px), self._t()
        for x in grp:
            if x is not w and x.status in OPEN:
                x.status = "canceled"
        self._net(w.symbol, -(1 if self.by_coid(coid).side == "buy" else -1) * q)

    def leg(self, coid, kind):
        return next(l for l in self.by_coid(coid).legs if (l.order_type == "limit") == (kind == "target"))


_n = itertools.count(10_000)


def _v(x):
    return str(getattr(x, "value", x)).lower()


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
    assert all(l.status == "canceled" for l in c.by_coid(ID("A")).legs) and not c.replaced
    p = c.by_coid(ID("A") + "-p")                    # the rest: OCO exit, target unchanged, stop at breakeven
    assert p.order_class == "oco" and p.side == "sell" and float(p.qty) == rem and p.limit_price == 12.0
    assert p.legs[0].stop_price == 10.0 and float(p.legs[0].qty) == rem
    legs = [l.id for l in c.by_coid(ID("A")).legs]
    assert c.log[-4:] == [("cancel", legs[0]), ("cancel", legs[1]), ("submit", ID("A") + "-s"),
                          ("submit", ID("A") + "-p")]
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
    p = c.by_coid(ID("A") + "-p")
    assert s.side == "buy" and float(s.qty) == 3 and c.pos["XYZ"] == -4
    assert p.side == "buy" and float(p.qty) == 4 and p.limit_price == 9.0 and p.legs[0].stop_price == 10.0
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


def test_config_flags_exactly_the_testing2_setups(monkeypatch):
    monkeypatch.setenv("MCF_ACCOUNT", "testing2")
    cfg = load_config()
    flagged = {n for n, p in cfg["strategies"].items() if (p or {}).get("live_scale_out")}
    scaled35 = {"CWT14-failbrk-pdh-p05-lowvol-short", "CWT14-failbrk-orl-p10-long", "CWT14-failbrk-orl-p10-lowvol-long",
                "CWT12-coil-k4-long"}                        # owner 2026-10-17 (Q17)
    assert flagged == set(SCALED) | scaled35
    assert all(cfg["strategies"][n]["scale_out_r"] == 0.25 for n in SCALED)
    assert all(cfg["strategies"][n]["scale_out_r"] == 0.35 for n in scaled35)
    monkeypatch.setenv("MCF_ACCOUNT", "primary")
    assert not any((p or {}).get("live_scale_out") for p in load_config()["strategies"].values())
    # 2026-10-21 reallocation: setups that scale out live may run in Testing 1 too, under the same 2/day cap
    monkeypatch.setenv("MCF_ACCOUNT", "testing")
    t1 = load_config()
    if any((p or {}).get("live_scale_out") and (p or {}).get("enabled") for p in t1["strategies"].values()):
        assert t1["live"]["scale_out_max_per_day"] == 2
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
        st, tg = c.working(ID("A"), "stop"), c.working(ID("A"), "target")
        if st is not None and ((lo <= st.stop_price) if side == 1 else (hi >= st.stop_price)):
            c.hit(ID("A"), "stop", st.stop_price)
        elif tg is not None and ((hi >= tg.limit_price) if side == 1 else (lo <= tg.limit_price)):
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


# ---------------------------------------------------------------- cancel -> bank -> protect (2026-10-19 fix)
BAR = [(10, 10.3, 9.9, 10.2)]                        # reaches +0.25R (10.25) without touching stop 9 / target 12


def _scaled(tmp_path, monkeypatch, qty=10, target=12.0, strategies=None):
    r, c = _r(tmp_path, monkeypatch, strategies or [St(**FLAG)], qty=qty)
    _enter(r, target=target)
    c.fill(ID("A"), 10.0)
    c.price["XYZ"] = 10.25
    return r, c


def _trade(r):
    r.reconcile(DAY)
    (t,) = r.journal.trades(run_id=r.run_id).itertuples()
    return t


def test_leg_qty_is_never_replaced_and_target_after_scale(tmp_path, monkeypatch):
    r, c = _scaled(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match="qty cannot be changed"):   # the fake refuses it like Alpaca
        c.replace_order_by_id(c.leg(ID("A"), "stop").id, NS(qty=5, stop_price=None, client_order_id=None))
    _poll(r, _bars(BAR))
    assert not c.replaced and c.pos["XYZ"] == 5 and r.health["scale_outs"][0]["left"] == 5
    assert float(c.by_coid(ID("A") + "-s").qty) == 5 and float(c.by_coid(ID("A") + "-p").qty) == 5
    c.hit(ID("A"), "target", 12.0)
    assert "XYZ" not in c.pos
    t = _trade(r)
    assert t.exit_reason == "scaled+target" and t.shares == 10 and t.pnl == pytest.approx(5 * 0.25 + 5 * 2.0)
    assert "scaleout:5@10.25" in t.meta and "target:5@12" in t.meta and "XYZ" not in r.lots


def test_lot_without_target_gets_plain_breakeven_stop_that_moves(tmp_path, monkeypatch):
    from mcf.execution.outage import open_lots

    r, c = _scaled(tmp_path, monkeypatch, target=None)
    _poll(r, _bars(BAR))
    p = c.by_coid(ID("A") + "-p")
    assert p.order_class == "simple" and p.order_type == "stop" and p.stop_price == 10.0 and float(p.qty) == 5
    r.broker.move_lot_stop("XYZ", ID("A"), 10.1, "mcf-")   # trailing / breakeven moves find the protective stop
    p1 = c.by_coid(ID("A") + "-p1")
    assert p.status == "replaced" and p1.replaces == p.id and p1.stop_price == 10.1
    (lot,) = open_lots(r.broker, "mcf-")
    assert lot["coid"] == ID("A") and lot["stop"] == 10.1
    r.broker.move_lot_stop("XYZ", ID("A"), 10.15, "mcf-")
    assert c.by_coid(ID("A") + "-p2").stop_price == 10.15
    c.hit(ID("A"), "stop", 10.15)
    t = _trade(r)
    assert t.exit_reason == "scaled+breakeven" and t.pnl == pytest.approx(5 * 0.25 + 5 * 0.15)


def test_oco_stop_leg_moves_in_place(tmp_path, monkeypatch):
    r, c = _scaled(tmp_path, monkeypatch)
    _poll(r, _bars(BAR))
    r.broker.move_lot_stop("XYZ", ID("A"), 10.1, "mcf-")
    assert c.by_coid(ID("A") + "-p").legs[0].stop_price == 10.1


def test_leg_fills_while_cancelling_is_closed(tmp_path, monkeypatch):
    r, c = _scaled(tmp_path, monkeypatch)

    def stop_fills(oid):
        c.on_cancel = None
        c.hit(ID("A"), "stop", 9.0)                  # the stop fills just before the cancel reaches it

    c.on_cancel = stop_fills
    _poll(r, _bars(BAR))
    assert not _scale_orders(c) and not any(o.client_order_id.endswith("-p") for o in c.orders)
    assert "XYZ" not in c.pos and r.scaling == {} and "scale_outs" not in r.health
    assert _trade(r).exit_reason == "stop"


def test_protection_refused_closes_the_rest(tmp_path, monkeypatch):
    r, c = _scaled(tmp_path, monkeypatch)
    c.reject_protect = 99
    _poll(r, _bars(BAR))
    u = c.by_coid(ID("A") + "-u")
    assert float(u.qty) == 5 and u.side == "sell" and "XYZ" not in c.pos      # never left without a stop
    assert r.scaling == {} and "closed at market" in r.health["scale_out_failed"][0]
    t = _trade(r)
    assert t.exit_reason == "scaled+unprotected" and t.shares == 10


def test_restart_between_bank_and_protect_resumes(tmp_path, monkeypatch):
    r, c = _scaled(tmp_path, monkeypatch)

    def crash(*a, **k):
        raise RuntimeError("process died")

    r.broker._protect_rest = crash                   # banked, then the job dies before step 3
    _poll(r, _bars(BAR))
    assert len(_scale_orders(c)) == 1 and c.pos["XYZ"] == 5
    assert not any(AlpacaBroker._is_protect(o.client_order_id, ID("A")) for o in c.orders)
    r2, _ = _r(tmp_path, monkeypatch, [St(**FLAG)])
    r2.broker.client = c
    r2.restore(DAY)
    assert ("XYZ", ID("A")) in r2.scaling
    r2.scaling[("XYZ", ID("A"))]["t0"] = NOW          # journal created_at is wall-clock time in tests
    _poll(r2, _bars(BAR))
    p = c.by_coid(ID("A") + "-p")
    assert float(p.qty) == 5 and p.legs[0].stop_price == 10.0 and p.limit_price == 12.0
    assert len(_scale_orders(c)) == 1 and c.pos["XYZ"] == 5 and r2.scaling == {}   # no second banked sale
    assert r2.broker.scale_out_lot("XYZ", ID("A"), 0.5, "mcf-")["status"] == "already"
    assert sum(o.client_order_id.startswith(ID("A") + "-") for o in c.orders) == 2


def test_flatten_and_time_stop_cancel_the_protection(tmp_path, monkeypatch):
    from mcf.execution.outage import open_lots

    r, c = _scaled(tmp_path, monkeypatch)
    _poll(r, _bars(BAR))
    (lot,) = open_lots(r.broker, "mcf-")
    assert lot["stop"] == 10.0
    c.price["XYZ"] = 10.5
    assert r.broker.close_mcf_position("XYZ", "mcf-", sleep=lambda s: None)
    p = c.by_coid(ID("A") + "-p")
    assert p.status == "canceled" and p.legs[0].status == "canceled" and "XYZ" not in c.pos
    t = _trade(r)
    assert t.exit_reason == "scaled+flatten" and t.pnl == pytest.approx(5 * 0.25 + 5 * 0.5)


def test_scale_one_of_two_stacked_lots(tmp_path, monkeypatch):
    r, c = _r(tmp_path, monkeypatch, [St(**FLAG), St("B")], qty=10)
    _enter(r)
    _enter(r, "B")
    c.fill(ID("A"), 10.0)
    c.fill(ID("B"), 10.0)
    c.price["XYZ"] = 10.25
    _poll(r, _bars(BAR))
    assert c.pos["XYZ"] == 15 and float(c.by_coid(ID("A") + "-p").qty) == 5
    assert all(l.status in OPEN for l in c.by_coid(ID("B")).legs)              # the other lot keeps its bracket
    assert r.broker.close_mcf_lot("XYZ", ID("A"), "mcf-", sleep=lambda s: None)  # time stop of the scaled lot
    assert float(c.by_coid(ID("A") + "-x").qty) == 5 and c.pos["XYZ"] == 10
    assert c.by_coid(ID("A") + "-p").status == "canceled"


def test_scale_out_daily_cap_counts_banked_orders_at_the_broker():
    """Owner SO1 2026-10-19: live.scale_out_max_per_day limits new scale-outs; counted from today's -s orders."""
    import types

    import pandas as pd
    import yaml

    from mcf.execution import runner as R

    class O:
        def __init__(self, c):
            self.client_order_id = c

    cls = next(v for v in vars(R).values() if isinstance(v, type) and hasattr(v, "_scale_cap_ok"))
    now = pd.Timestamp("2026-10-20 10:30", tz="America/New_York")
    stub = types.SimpleNamespace(live={"scale_out_max_per_day": 2},
                                 broker=types.SimpleNamespace(orders_today_with_prefix=lambda p, a: [
                                     O(f"{p}A-s"), O(f"{p}A"), O(f"{p}B-p")]))
    assert cls._scale_cap_ok(stub, now) is True                     # 1 banked order < 2
    stub.broker.orders_today_with_prefix = lambda p, a: [O(f"{p}A-s"), O(f"{p}B-s")]
    assert cls._scale_cap_ok(stub, now) is False                    # cap reached
    stub.live = {}
    assert cls._scale_cap_ok(stub, now) is True                     # no cap configured
    cfg = yaml.safe_load(open("config/account_testing2.yaml"))
    assert cfg["live"]["scale_out_max_per_day"] == 2
