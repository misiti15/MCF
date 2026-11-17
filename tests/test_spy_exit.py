"""SPY-since-entry exit (owner "SPYEXIT build yes" 2026-11-16; mcf/spy_exit.py). Opt-in per setup (`spy_exit_pct`,
`spy_exit_only_losing`), default off. One rule in the backtest engine, the live runner and the shadow book.
Educational only - not financial advice."""
import numpy as np
import pandas as pd
import pytest

from mcf import spy_exit as SX
from mcf.backtest.engine import Backtester, simulate
from mcf.strategies.base import Signal, Strategy

from test_lots import DAY, ID, NOW, NY, _enter, _runner

FLAT = pd.Timestamp("15:55").time()


# ------------------------------------------------------------------------------------------------ the rule
def test_rule_short_long_threshold_and_flags():
    assert SX.spy_exit_hit(-1, 600.0, 600.0 * 1.0030, 0.30)               # short: SPY +0.30% -> exit
    assert not SX.spy_exit_hit(-1, 600.0, 600.0 * 1.0029, 0.30)           # +0.29% -> hold
    assert not SX.spy_exit_hit(-1, 600.0, 600.0 * 0.990, 0.30)            # SPY down: a short is fine
    assert SX.spy_exit_hit(1, 600.0, 600.0 * 0.9970, 0.30)                # long mirror: SPY -0.30%
    assert not SX.spy_exit_hit(1, 600.0, 600.0 * 0.9971, 0.30)
    assert not SX.spy_exit_hit(1, 600.0, 600.0 * 1.01, 0.30)
    # only while losing
    assert not SX.spy_exit_hit(-1, 600.0, 602.0, 0.30, only_losing=True, under_water=False)
    assert SX.spy_exit_hit(-1, 600.0, 602.0, 0.30, only_losing=True, under_water=True)
    assert not SX.spy_exit_hit(-1, 600.0, 602.0, 0.30, only_losing=True, under_water=None)
    # off / missing data -> never
    for spy0, now, pct in ((600.0, 610.0, None), (600.0, 610.0, 0), (None, 610.0, 0.3), (600.0, None, 0.3),
                           (600.0, float("nan"), 0.3), (0.0, 610.0, 0.3)):
        assert not SX.spy_exit_hit(-1, spy0, now, pct)


def test_signal_gets_the_setup_params_and_default_is_off():
    class One(Strategy):
        name = "one"

        def generate(self, ctx):
            return [Signal(ctx.symbol, self.name, -1, 5, stop=11.0)]

    ctx = type("C", (), {"symbol": "XYZ"})()
    off = One().signals(ctx)[0]
    assert off.spy_exit_pct is None and off.spy_exit_only_losing is False
    on = One(spy_exit_pct=0.4, spy_exit_only_losing=True).signals(ctx)[0]
    assert on.spy_exit_pct == 0.4 and on.spy_exit_only_losing is True
    assert SX.enabled([One(spy_exit_pct=0.3)]) and not SX.enabled([One(), One(spy_exit_pct=None)])


# ------------------------------------------------------------------------------------------------ engine
def _bars(prices, start="2026-11-17 10:30"):
    idx = pd.date_range(start, periods=len(prices), freq="1min", tz=NY)
    p = np.asarray(prices, float)
    return pd.DataFrame({"open": p, "high": p + 0.01, "low": p - 0.01, "close": p, "volume": 1e5}, index=idx)


def _spy(pcts, base=600.0, start="2026-11-17 10:30"):
    """SPY 1-min bars whose closes are base * (1 + pct/100)."""
    return _bars([base * (1 + x / 100) for x in pcts], start)


# stock flat at 10.0 for 40 minutes; SPY flat, then +0.10% per minute from bar 10
PCTS = [0.0] * 10 + [0.1 * i for i in range(1, 31)]


def test_engine_short_exits_at_next_open_once_spy_up_x():
    bars, spy = _bars([10.0] * 40), _spy(PCTS)
    sig = Signal("XYZ", "s", -1, 0, stop=11.0, target=8.0, spy_exit_pct=0.30)
    tr = simulate(sig, bars, FLAT, 0.0, spy=spy)
    # entry bar 1 (spy0 = SPY close of bar 0 = +0.00%); SPY close +0.30% first at bar 12 -> exit at bar 13's open
    assert tr.exit_reason == "spy_exit" and tr.exit_time == bars.index[13] and tr.exit == 10.0
    # off: no exit (holds to the flatten / end of data)
    assert simulate(Signal("XYZ", "s", -1, 0, stop=11.0, target=8.0), bars, FLAT, 0.0, spy=spy).exit_reason == "eod"
    # missing SPY -> exactly as off
    assert simulate(sig, bars, FLAT, 0.0, spy=None).exit_reason == "eod"
    assert simulate(sig, bars, FLAT, 0.0, spy=spy.iloc[:0]).exit_reason == "eod"


def test_engine_long_mirror_and_only_losing():
    bars = _bars([10.0] * 40)
    down = _spy([-x for x in PCTS])
    tr = simulate(Signal("XYZ", "l", 1, 0, stop=9.0, spy_exit_pct=0.30), bars, FLAT, 0.0, spy=down)
    assert tr.exit_reason == "spy_exit" and tr.exit_time == bars.index[13]
    assert simulate(Signal("XYZ", "l", 1, 0, stop=9.0, spy_exit_pct=0.30), bars, FLAT, 0.0,
                    spy=_spy(PCTS)).exit_reason == "eod"                     # SPY up never exits a long
    # short in profit (stock falling) + only_losing -> no SPY exit; under water (stock rising) -> exit
    win = _bars([10.0 - 0.005 * i for i in range(40)])
    lose = _bars([10.0 + 0.005 * i for i in range(40)])
    kw = dict(stop=11.0, spy_exit_pct=0.30, spy_exit_only_losing=True)
    assert simulate(Signal("XYZ", "s", -1, 0, **kw), win, FLAT, 0.0, spy=_spy(PCTS)).exit_reason == "eod"
    tr = simulate(Signal("XYZ", "s", -1, 0, **kw), lose, FLAT, 0.0, spy=_spy(PCTS))
    assert tr.exit_reason == "spy_exit" and tr.exit_time == lose.index[13]


def test_backtester_reads_spy_from_data_or_context_only():
    class One(Strategy):
        name = "one"

        def generate(self, ctx):
            return [Signal(ctx.symbol, self.name, -1, 0, stop=ctx.bars["close"].iloc[0] * 1.1)] if ctx.symbol == "XYZ" else []

    days = pd.bdate_range("2026-10-01", "2026-11-17")
    frames_x, frames_s = [], []
    for d in days:
        frames_x.append(_bars([10.0] * 390, f"{d.date()} 09:30"))
        frames_s.append(_spy([0.0] * 10 + [0.1 * i for i in range(1, 381)], start=f"{d.date()} 09:30"))
    x, s = pd.concat(frames_x), pd.concat(frames_s)
    from mcf.config import load_config
    cfg = load_config()
    cfg["universe"].update(min_avg_dollar_volume=0, extended_min_avg_dollar_volume=0, min_atr_pct=0.0, extended_min_rvol=0.0)
    cfg["costs"]["min_price"] = 1.0
    off = Backtester([One()], cfg).run({"XYZ": x}, spy=s)
    on_ctx = Backtester([One(spy_exit_pct=0.3)], cfg).run({"XYZ": x}, spy=s)
    assert len(off) and len(on_ctx)
    assert set(off.exit_reason) != {"spy_exit"} and set(on_ctx.exit_reason) == {"spy_exit"}


# ------------------------------------------------------------------------------------------------ live runner
def _sym_bars(n, px=10.0, start=NOW):
    idx = pd.date_range(start.floor("1min"), periods=n, freq="1min")
    return pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": 1e5}, index=idx)


def _spy_live(pct_last, n_after=5, base=600.0):
    """SPY bars 09:30 .. NOW+n_after-1: flat at base through the entry minute, last bar at base * (1 + pct_last %)."""
    idx = pd.date_range(pd.Timestamp("2026-10-13 09:30", tz=NY), NOW.floor("1min") + pd.Timedelta(minutes=n_after - 1),
                        freq="1min")
    c = np.full(len(idx), base)
    c[-1] = base * (1 + pct_last / 100)
    return pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 1e6}, index=idx)


def _short_lot(r, c, **kw):
    _enter(r, "S", side=-1, stop=11.0, target=8.0, spy_exit_pct=0.30, **kw)
    c.fill(ID("S"), 10.0)
    return int(float(c.by_coid(ID("S")).qty))


def test_runner_short_spy_exit_through_time_stop_path_and_journal(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch, strategies=[Strategy(spy_exit_pct=0.30)])
    assert "SPY" in r.watchlist                                          # polled because a setup uses it
    q = _short_lot(r, c)
    assert r.managed[("XYZ", ID("S"))]["spy_exit_pct"] == 0.30
    later = NOW + pd.Timedelta(minutes=5)
    r.manage(later, {"XYZ": _sym_bars(5), "SPY": _spy_live(0.29)})
    assert not any(o.client_order_id.endswith("-x") for o in c.orders)   # +0.29%: hold
    assert r.managed[("XYZ", ID("S"))]["spy0"] == 600.0                 # SPY close of the minute before the entry
    c.price["XYZ"] = 10.05
    r.manage(later, {"XYZ": _sym_bars(5), "SPY": _spy_live(0.30)})
    ex = c.by_coid(ID("S") + "-x")                                       # the lot's own market close (time-stop path)
    assert ex.side == "buy" and float(ex.qty) == q and ("XYZ", ID("S")) not in r.managed
    r.reconcile(DAY)
    t = r.journal.trades(run_id=r.run_id)
    assert len(t) == 1 and t.iloc[0].exit_reason == "spy_exit"


def test_runner_long_mirror_only_losing_and_off(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    _enter(r, "L", side=1, stop=9.0, target=12.0, spy_exit_pct=0.30, spy_exit_only_losing=True)
    _enter(r, "O", side=1, stop=9.0, target=12.0)                       # no spy_exit_pct: never managed for it
    c.fill(ID("L"), 10.0)
    c.fill(ID("O"), 10.0)
    assert ("XYZ", ID("O")) not in r.managed
    later = NOW + pd.Timedelta(minutes=5)
    r.manage(later, {"XYZ": _sym_bars(5, px=10.10), "SPY": _spy_live(-0.50)})   # in profit: only_losing holds
    assert not any(o.client_order_id.endswith("-x") for o in c.orders)
    c.price["XYZ"] = 9.95
    r.manage(later, {"XYZ": _sym_bars(5, px=9.95), "SPY": _spy_live(-0.50)})    # under water: exit
    assert c.by_coid(ID("L") + "-x").side == "sell"
    assert not any(o.client_order_id == ID("O") + "-x" for o in c.orders)


def test_runner_missing_or_stale_spy_holds_and_logs_once(tmp_path, monkeypatch, capsys):
    r, c = _runner(tmp_path, monkeypatch)
    _short_lot(r, c)
    later = NOW + pd.Timedelta(minutes=5)
    r.manage(later, {"XYZ": _sym_bars(5)})                               # no SPY at all
    r.manage(later, {"XYZ": _sym_bars(5)})
    stale = _spy_live(1.0).loc[: NOW.floor("1min")]                      # last SPY bar 5 minutes old
    r.manage(later, {"XYZ": _sym_bars(5), "SPY": stale})
    assert not any(o.client_order_id.endswith("-x") for o in c.orders)
    assert capsys.readouterr().out.count("SPY data missing or stale") == 1


def test_runner_spy0_taken_at_the_entry_poll(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    r._step_bars = {"SPY": _spy_live(0.0, n_after=1, base=601.0)}         # entry poll: last completed SPY close 601
    _short_lot(r, c)
    assert r.managed[("XYZ", ID("S"))]["spy0"] == 601.0


# ------------------------------------------------------------------------------------------------ parity
def test_backtest_live_parity_on_a_synthetic_path(tmp_path, monkeypatch):
    """Same SPY path: the engine exits at the open of the bar the runner's poll closes the lot in."""
    start = NOW.floor("1min") - pd.Timedelta(minutes=1)                  # signal bar 09:59 -> market entry bar 10:00
    n = 40
    stock = _bars([10.0] * n, str(start.tz_localize(None)))
    pcts = [0.0] * 6 + [0.07 * i for i in range(1, n - 5)]
    spy = _spy(pcts, start=str(start.tz_localize(None)))
    for side, pct, only in ((-1, 0.30, False), (-1, 0.40, False), (1, 0.30, False)):
        path = spy if side == -1 else _spy([-x for x in pcts], start=str(start.tz_localize(None)))
        sig = Signal("XYZ", "P", side, 0, stop=10.0 - side, spy_exit_pct=pct, spy_exit_only_losing=only)
        tr = simulate(sig, stock, FLAT, 0.0, spy=path)
        assert tr.exit_reason == "spy_exit"
        sub = tmp_path / f"{side}_{pct}"
        sub.mkdir()
        r, c = _runner(sub, monkeypatch)
        name = "P"
        _enter(r, name, side=side, stop=10.0 - side, target=None, spy_exit_pct=pct)
        c.fill(ID(name), 10.0)
        closed = None
        for k in range(1, n):                                            # poll in minute k sees bars < k
            poll = stock.index[k] + pd.Timedelta(seconds=3)
            bars = {"XYZ": stock.iloc[:k], "SPY": path.iloc[:k]}
            r.manage(poll, bars)
            if any(o.client_order_id == ID(name) + "-x" for o in c.orders):
                closed = stock.index[k]
                break
        assert closed == tr.exit_time, (side, pct, closed, tr.exit_time)


# ------------------------------------------------------------------------------------------------ shadow book
def test_shadow_lot_spy_exit(tmp_path, monkeypatch):
    import test_shadow_mode as T

    class OnlyAAA(T.Strat):
        def signals(self, ctx):
            return T.Strat.signals(self, ctx) if ctx.symbol == "AAA" else iter(())

    s = OnlyAAA("SX", side=-1, tgt_off=None, spy_exit_pct=0.30)
    s.params = {"spy_exit_pct": 0.30}
    r, b = T._runner(tmp_path, monkeypatch, extras=[s])
    bars = {"AAA": T._bars(n=390), "SPY": T._bars(n=390, path=T._path({"10:05": 601.2, "10:06": 602.4}, base=600.0))}
    for p in ("10:01", "10:03", "10:06"):
        T._poll(r, monkeypatch, T._t(p), bars)
    assert len(r.shadow.lots) == 1 and r.journal.trades(run_id=r.shadow.run_id).empty   # +0.20%: hold
    T._poll(r, monkeypatch, T._t("10:07"), bars)                         # SPY +0.40% since entry: exit
    tr = r.journal.trades(run_id=r.shadow.run_id)
    assert len(tr) == 1 and tr.exit_reason.iloc[0] == "spy_exit" and b.submitted == []


# ------------------------------------------------------------------------------------------------ the 11-17 swap
def test_rw3_rw5_wb4_replace_wb3_with_spy_exit():
    """Owner "SPYEXIT build yes": WB4 in WB3's account and slot, WB3 off (promotion = move), spy_exit_pct set."""
    from pathlib import Path

    import yaml
    root = Path(__file__).resolve().parents[1]
    for acct, base, pct in (("livelab", "RW3-gapdn-rsi5pop-flowsell-short-FD", 0.30),
                            ("testingd", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", 0.40)):
        c = yaml.safe_load((root / f"config/account_{acct}.yaml").read_text())
        st, order = c["strategies"], c["live"]["setup_order"]
        assert st[f"{base}-WB4"]["enabled"] and st[f"{base}-WB4"]["spy_exit_pct"] == pct
        assert not st[f"{base}-WB3"]["enabled"] and f"{base}-WB3" not in order
        assert order[0] == f"{base}-WB4"
