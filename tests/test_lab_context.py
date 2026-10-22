"""Lab features for near-miss forward tests (owner 2026-10-17, Q8 = A): point-in-time context columns (spy_fo, qqq_fo,
breadth, breadth_open), the lab `symbols` allow-list, and the t05s05 / hold / holdtr geometries. All opt-in.
Educational only - not financial advice."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from mcf.backtest.engine import Costs, pinned_symbols, simulate
from mcf.data.bars import resample
from mcf.data.synthetic import make_universe
from mcf.research.heat import heat_frame
from mcf.strategies import lab_context as LC
from mcf.strategies.setups import _LAB_FRAMES, LabStrategy, build_strategies

SYMS = ["SPY", "QQQ"] + [f"S{i:02d}" for i in range(10)]
CTX = ["spy_fo", "qqq_fo", "breadth", "breadth_open", "qqq_vwap"]

MOD_SRC = '''
import numpy as np
SIDE = "long"
GEOM = "t1s1"
LAYERS = ["ctx test"]
SEEN = []
def mask(df):
    SEEN.append(df.copy())
    if "spy_fo" not in df:
        return np.zeros(len(df), bool)
    with np.errstate(invalid="ignore"):
        return (df["spy_fo"].to_numpy(float) > THRESH) & (df["breadth"].to_numpy(float) >= 0.0)
'''


def _universe(days=3):
    data = make_universe(SYMS, days=days, start="2025-03-03")
    return {s: df for s, df in data.items()}


def _day(data, i=-1):
    d = sorted({x for df in data.values() for x in df.index.date})[i]
    return {s: df[df.index.date == d] for s, df in data.items()}


def _cut(peers, n):
    """Live view after n completed minutes: every peer's bars before 09:30 + n."""
    t0 = min(b.index[0] for b in peers.values()).normalize() + pd.Timedelta(hours=9, minutes=30)
    cut = t0 + pd.Timedelta(minutes=n)
    return {s: b[b.index < cut] for s, b in peers.items()}, cut


@pytest.fixture(autouse=True)
def _clear():
    LC._CACHE.clear()
    _LAB_FRAMES.clear()


def _mod(tmp_path, thresh):
    p = tmp_path / f"ctx_mod_{str(thresh).replace('.', '_').replace('-', 'm')}.py"
    p.write_text(MOD_SRC.replace("THRESH", repr(float(thresh))))
    return str(p)


def test_parse_context():
    assert LC.parse_context(None) == () and LC.parse_context(False) == ()
    assert LC.parse_context(True) == tuple(CTX)
    assert LC.parse_context(["qqq_fo", "spy_fo", "qqq_fo"]) == ("qqq_fo", "spy_fo")
    assert LC.context_symbols(("spy_fo", "breadth")) == {"SPY"}
    assert LC.context_symbols(("qqq_vwap",)) == {"QQQ"} and LC.parse_context(["qqq_vwap"]) == ("qqq_vwap",)
    with pytest.raises(ValueError):
        LC.parse_context(["spy_fromOpen"])


def test_context_table_is_point_in_time():
    peers = _day(_universe())
    full = LC.context_table(peers, CTX)
    assert not full.empty and full[CTX].notna().all().all()
    for n in (5, 23, 60, 137, 300, 389):
        LC._CACHE.clear()
        live_peers, cut = _cut(peers, n)
        part = LC.context_table(live_peers, CTX)
        done = part.index[part.index + pd.Timedelta(minutes=5) <= cut]   # completed 5-minute bars only
        assert len(done) == n // 5
        pd.testing.assert_frame_equal(part.loc[done, CTX], full.loc[done, CTX], check_freq=False)
    # changing the future does not change the past
    LC._CACHE.clear()
    fut = {s: b.copy() for s, b in peers.items()}
    later = fut["SPY"].index >= fut["SPY"].index[200]
    for s, b in fut.items():
        b.loc[b.index >= b.index[200], ["open", "high", "low", "close"]] *= 1.5
        b.loc[b.index >= b.index[200], "volume"] *= 9
    alt = LC.context_table(fut, CTX)
    keep = full.index[full.index + pd.Timedelta(minutes=5) <= fut["SPY"].index[200]]
    pd.testing.assert_frame_equal(alt.loc[keep, CTX], full.loc[keep, CTX], check_freq=False)
    assert later.any() and not np.allclose(alt["spy_fo"].iloc[-1], full["spy_fo"].iloc[-1])


def test_matches_history_frame_definition():
    """Live/backtest table == the history table built from heat-frame rows (spy_fo = SPY fromOpen at the same bar,
    breadth = mean(vwapDistPct > 0), breadth_open = mean(fromOpen > 0)), on several days."""
    data = _universe(days=3)
    rows = []
    for s, df in data.items():
        f = heat_frame(resample(df, "5min"))
        f["symbol"], f["date"] = s, f.index.date
        rows.append(f[["symbol", "date", "tod", "fromOpen", "vwapDistPct"]])
    hist = LC.context_from_frames(pd.concat(rows))
    live = LC.context_table(data, CTX)
    end = live.index + pd.Timedelta(minutes=5)
    live = live.assign(date=live.index.date, tod=end.hour * 100 + end.minute)
    m = hist.merge(live, on=["date", "tod"], suffixes=("_h", "_l"))
    assert len(m) == len(live) == len(hist)
    for c in CTX:
        np.testing.assert_allclose(m[f"{c}_h"], m[f"{c}_l"], rtol=1e-9, atol=1e-12)
    # a hand check of one bar
    spy5 = resample(data["SPY"], "5min")
    d0 = spy5[spy5.index.date == spy5.index.date[0]]
    assert live["spy_fo"].iloc[10] == pytest.approx((d0["close"].iloc[10] / d0["open"].iloc[0] - 1) * 100)


def _ctx(sym, bars, peers):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=2.0, prev_close=float(
        bars["open"].iloc[0]), prev_high=1e9, prev_low=0.0, avg_dollar_volume=1e9, peers=peers)


def test_lab_strategy_live_equals_backtest(tmp_path):
    peers = _day(_universe())
    full = LC.context_table(peers, CTX)
    thr = float(np.nanquantile(full["spy_fo"], 0.6))   # fires on part of the day, not on the first bar
    st = LabStrategy("ctx", _mod(tmp_path, thr), window=[950, 1500], context=True, refire=True, refire_cooldown=0)
    sym = "S03"
    bt = [s.bar_index for s in st.signals(_ctx(sym, peers[sym], peers))]
    assert bt, "the test needs some signals"
    bt_frame = st.mod.SEEN[-1][CTX].copy()
    live, last_frames = [], {}
    for n in range(25, 391, 5):
        LC._CACHE.clear()
        _LAB_FRAMES.clear()
        lp, _ = _cut(peers, n)
        st.mod.SEEN.clear()
        sigs = st.signals(_ctx(sym, lp[sym], lp)) if st.eligible(_ctx(sym, lp[sym], lp)) else []
        live += [s.bar_index for s in sigs if s.bar_index == n - 1]   # live acts on the latest bar only
        if st.mod.SEEN:
            last_frames[n] = st.mod.SEEN[-1][CTX].iloc[-1]
    assert live == [b for b in bt if b >= 24]
    for n, row in last_frames.items():   # each live frame's newest bar equals the backtest's value for that bar
        ts = peers[sym].index[0] + pd.Timedelta(minutes=n - 5)
        pd.testing.assert_series_equal(row, bt_frame.loc[ts], check_names=False)


def test_context_is_opt_in_and_does_not_leak(tmp_path):
    peers = _day(_universe())
    sym = "S01"
    plain = LabStrategy("plain", _mod(tmp_path, 0.0), window=[950, 1500])
    withc = LabStrategy("withc", _mod(tmp_path, -99.0), window=[950, 1500], context=["spy_fo", "breadth"])
    assert plain.context == () and plain.context_symbols == set()
    assert withc.context_symbols == {"SPY"}
    ctx = _ctx(sym, peers[sym], peers)
    withc.signals(ctx)
    plain.signals(ctx)
    assert {"spy_fo", "breadth"} <= set(withc.mod.SEEN[-1].columns)
    assert not set(CTX) & set(plain.mod.SEEN[-1].columns)          # the shared cached frame stays without them
    assert not set(CTX) & set(next(iter(_LAB_FRAMES.values())).columns)
    assert plain.signals(ctx) == []                                  # module without the column: fail safe
    # no peers (e.g. a caller that does not pass them): columns are NaN, the mask fires nothing
    _LAB_FRAMES.clear()
    assert withc.signals(_ctx(sym, peers[sym], None)) == []
    assert withc.mod.SEEN[-1]["spy_fo"].isna().all()


def test_symbols_allow_list(tmp_path):
    peers = _day(_universe())
    st = LabStrategy("etf", _mod(tmp_path, -99.0), window=[950, 1500], context=True, symbols=["SPY", "QQQ"])
    assert st.eligible(_ctx("QQQ", peers["QQQ"], peers))
    assert not st.eligible(_ctx("S01", peers["S01"], peers))
    free = LabStrategy("free", _mod(tmp_path, -99.0), window=[950, 1500])
    assert free.symbols is None and free.eligible(_ctx("S01", peers["S01"], peers))
    # lab symbols restrict only; they pin into the universe only with pin_symbols: true (other types unchanged)
    cfg = {"strategies": {"a": {"enabled": True, "type": "lab", "symbols": ["TQQQ"]},
                          "b": {"enabled": True, "type": "lab", "symbols": ["SOXL"], "pin_symbols": True},
                          "c": {"enabled": True, "class": "index_dip_bounce", "symbols": ["SSO"]}}}
    assert pinned_symbols(cfg) == {"SOXL", "SSO"}


def test_build_strategies_passes_new_keys(tmp_path):
    cfg = {"strategies": {"x": {"type": "lab", "module": _mod(tmp_path, 0.0), "context": ["qqq_fo"],
                                "symbols": ["QQQ"], "geom": "holdtr", "scale_out_r": None}}}
    (st,) = build_strategies(cfg)
    assert st.context == ("qqq_fo",) and st.symbols == {"QQQ"} and st.geom == "holdtr"
    assert st.params["trail_r"] == 1.0 and st.params["trail_after_r"] == 1.0


@pytest.mark.parametrize("geom,tgt,stp,trail", [("t05s05", 0.5, 0.5, None), ("hold", None, 1.0, None),
                                                ("holdtr", None, 1.0, 1.0), ("t1s1", 1.0, 1.0, None)])
def test_geometries(tmp_path, geom, tgt, stp, trail):
    peers = _day(_universe())
    st = LabStrategy("g", _mod(tmp_path, -99.0), window=[950, 1500], context=True, geom=geom)
    (sig,) = st.signals(_ctx("S02", peers["S02"], peers))
    px, r = float(peers["S02"]["close"].iloc[sig.bar_index]), 0.25 * 2.0
    assert sig.stop == pytest.approx(px - stp * r)
    assert (sig.target is None) if tgt is None else sig.target == pytest.approx(px + tgt * r)
    assert sig.trail_r == trail and (trail is None or sig.trail_after_r == 1.0)


def test_holdtr_explicit_trail_wins_and_bad_geom(tmp_path):
    st = LabStrategy("g", _mod(tmp_path, 0.0), geom="holdtr", trail_r=0.5)
    assert st.params["trail_r"] == 0.5 and st.params["trail_after_r"] == 1.0
    with pytest.raises(ValueError):
        LabStrategy("bad", _mod(tmp_path, 0.0), geom="t2s1")


def test_holdtr_simulates_a_1r_trail():
    """No target; the stop trails 1R behind the best price once the trade is +1R; flat at the time exit otherwise."""
    from mcf.strategies.base import Signal

    idx = pd.date_range("2025-03-03 10:00", periods=8, freq="1min", tz="America/New_York")
    c = np.array([100, 100, 101, 102, 103, 102.5, 101.9, 101.5])   # R = 1: best +3R, then back below +2R
    bars = pd.DataFrame({"open": c, "high": c + 0.05, "low": c - 0.05, "close": c, "volume": 1e5}, index=idx)
    sig = Signal("X", "holdtr", 1, 0, stop=99.0, target=None, trail_r=1.0, trail_after_r=1.0)
    tr = simulate(sig, bars, pd.Timestamp("15:55").time(), Costs(0, 0, 0))
    assert tr.exit_reason == "trail" and tr.exit == pytest.approx(101.9)   # stop 102.05 (best 103.05 - 1R), gapped through


def test_runner_polls_context_index_symbols(tmp_path):
    """Live: SPY / QQQ are fetched every poll for setups that ask for spy_fo / qqq_fo (not traded unless in priors)."""
    from mcf.config import load_config
    from mcf.execution import runner as R

    class Broker:
        def equity(self):
            return 1e5

        def positions(self):
            return {}

    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    st = LabStrategy("c", _mod(tmp_path, 0.0), context=["spy_fo", "qqq_fo"])
    plain = LabStrategy("p", _mod(tmp_path, 0.0))
    assert R.PaperRunner(cfg, [plain], {"XYZ": object()}, broker=Broker()).watchlist == ["XYZ"]
    assert R.PaperRunner(cfg, [plain, st], {"XYZ": object()}, broker=Broker()).watchlist == ["QQQ", "SPY", "XYZ"]


def test_symbols_module_spec(tmp_path):
    p = tmp_path / "sym_mod.py"
    p.write_text(MOD_SRC.replace("THRESH", "0.0") + "\nSYMBOLS = frozenset(['TQQQ', 'SOXL'])\n")
    st = LabStrategy("m", str(p), symbols="module")
    assert st.symbols == {"TQQQ", "SOXL"}
    with pytest.raises(ValueError):
        LabStrategy("m2", _mod(tmp_path, 0.0), symbols="module")
    assert pinned_symbols({"strategies": {"m": {"enabled": True, "type": "lab", "symbols": "module",
                                                "pin_symbols": True}}}) == set()


# ---- qqq_vwap (owner 2026-10-22 S1, research/bdi/st7_1022): QQQ close vs its own session VWAP, % ----------------------
ST7Q = "research/bdi/st7_1022/modules/ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD.py"


def _path_bars(closes5, vols5, day="2025-03-04"):
    """1-minute RTH bars whose 5-minute bars close at closes5 (each 5-minute bar opens at the previous close and moves
    linearly), with vols5 per 5-minute bar spread evenly."""
    idx = pd.date_range(f"{day} 09:30", periods=5 * len(closes5), freq="1min", tz="America/New_York")
    c1, prev = [], float(closes5[0])
    for c in closes5:
        c1 += list(np.linspace(prev, c, 6)[1:])
        prev = float(c)
    c1 = np.array(c1)
    o1 = np.r_[closes5[0], c1[:-1]]
    v1 = np.repeat(np.asarray(vols5, float) / 5, 5)
    return pd.DataFrame({"open": o1, "high": np.maximum(o1, c1) + 0.01, "low": np.minimum(o1, c1) - 0.01,
                         "close": c1, "volume": v1}, index=idx)


def _st7q_day(qqq_up: bool):
    """A stock that drifts up on heavy up-bar volume, then drops 2.5% in the 11:10-11:15 bar (RSI 50+ -> <= 30,
    > 1% below its open, buy pressure still > 0). QQQ trends down all day (below its VWAP) or up (above it)."""
    n = 78
    k = np.arange(n)
    stock = 100 + np.cumsum(np.where(k % 2 == 0, 0.06, -0.04))
    drop = 20
    stock[drop:] -= 2.5 + stock[drop - 1] - 100
    vols = np.where(k % 2 == 0, 30000.0, 10000.0)
    vols[drop] = 20000.0
    qqq = 400 + (1 if qqq_up else -1) * 0.08 * k
    return {"S7": _path_bars(stock, vols), "QQQ": _path_bars(qqq, np.full(n, 1e6)), "SPY": _path_bars(qqq + 100, np.full(n, 1e6))}


def _scan_frame(bars, qqq_bars):
    """The research scan's frame (research/bdi/st7_1022/scripts/scan.py): the stock's lab frame + `qqq_vwap` = QQQ's
    lab-frame vwapDistPct at the same (date, tod)."""
    from mcf.research.setup_lab import extra_features

    d5 = resample(bars, "5min")
    f = heat_frame(d5)
    f["atr_d"] = 2.0
    f = f.join(extra_features(d5, f))
    f["volume"] = d5["volume"].to_numpy(float)
    f["gap"] = 0.0
    q = heat_frame(resample(qqq_bars, "5min"))[["tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "qqq_vwap"})
    return f.reset_index().merge(q, on="tod", how="left").set_index(f.index.name or "index")


@pytest.mark.parametrize("qqq_up", [False, True])
def test_qqq_vwap_live_equals_scan_value(qqq_up):
    """Live table (from the poll's QQQ 1-minute bars so far) == the full-day table == the scan's QQQ frame vwapDistPct,
    on every completed bar, for QQQ below and above its VWAP; and a hand check of one bar."""
    peers = _st7q_day(qqq_up)
    scan = heat_frame(resample(peers["QQQ"], "5min"))["vwapDistPct"]
    full = LC.context_table(peers, ["qqq_vwap"])["qqq_vwap"]
    np.testing.assert_allclose(full.to_numpy(), scan.reindex(full.index).to_numpy(), rtol=1e-12, atol=1e-12)
    assert ((full.iloc[1:] > 0) if qqq_up else (full.iloc[1:] < 0)).all()   # bar 1: close vs its own typical price
    for n in (25, 60, 115, 200, 390):
        LC._CACHE.clear()
        lp, cut = _cut(peers, n)
        part = LC.context_table(lp, ["qqq_vwap"])["qqq_vwap"]
        done = part.index[part.index + pd.Timedelta(minutes=5) <= cut]
        np.testing.assert_allclose(part.loc[done].to_numpy(), scan.loc[done].to_numpy(), rtol=1e-12, atol=1e-12)
    q5 = resample(peers["QQQ"], "5min").iloc[:7]
    typ = (q5["high"] + q5["low"] + q5["close"]) / 3
    vw = float((typ * q5["volume"]).sum() / q5["volume"].sum())
    assert full.iloc[6] == pytest.approx((q5["close"].iloc[6] - vw) / vw * 100)


def test_st7q_fires_with_qqq_vwap_parity():
    """S1 parity: ST7Q through the live LabStrategy (context [qqq_vwap] from the poll) fires on the same bar as the module
    mask on the scan's frame; the backtest (full day) and the live poll-by-poll view agree; QQQ above VWAP or a missing
    column -> nothing (fail safe); the parent's mask fires on the same bar either way."""
    down, up = _st7q_day(False), _st7q_day(True)
    st = LabStrategy("ST7Q", ST7Q, window=[950, 1500], context=["qqq_vwap"], min_adv=95e6)
    assert st.context_symbols == {"QQQ"} and st.side == 1 and st.geom == "t1s1"
    scan = _scan_frame(down["S7"], down["QQQ"])
    hits = np.flatnonzero(st.mod.mask(scan) & (scan["tod"].to_numpy() >= 950) & (scan["tod"].to_numpy() <= 1500))
    assert len(hits) == 1 and scan["tod"].iloc[hits[0]] == 1115
    parent = np.flatnonzero(st.mod.mask(scan.drop(columns="qqq_vwap").assign(qqq_vwap=-1.0)))
    assert list(parent) == list(hits)
    bt = st.signals(_ctx("S7", down["S7"], down))
    assert [(s.bar_index, s.side) for s in bt] == [(hits[0] * 5 + 4, 1)]
    live = []
    for n in range(25, 391, 5):
        LC._CACHE.clear()
        _LAB_FRAMES.clear()
        lp, _ = _cut(down, n)
        c = _ctx("S7", lp["S7"], lp)
        live += [s.bar_index for s in (st.signals(c) if st.eligible(c) else []) if s.bar_index == n - 1]
    assert live == [hits[0] * 5 + 4]
    LC._CACHE.clear()
    _LAB_FRAMES.clear()
    assert st.signals(_ctx("S7", up["S7"], up)) == []                 # QQQ above its VWAP: skipped
    _LAB_FRAMES.clear()
    assert st.signals(_ctx("S7", down["S7"], {"S7": down["S7"]})) == []   # QQQ not polled: NaN -> nothing
    assert not st.mod.mask(scan.drop(columns="qqq_vwap")).any()            # no column at all: nothing


def test_st7q_and_ns3v1_configured(monkeypatch):
    """S1 / V1 (owner 2026-10-22): ST7Q in Testing 1 next to its running parent; NS3V1 in Testing 2 before NS3-FD with
    the twin_group NS3-T2 on both."""
    from pathlib import Path

    import yaml

    from mcf.config import load_config
    from mcf.execution.risk import twin_groups, twin_key
    from mcf.strategies.setups import build_strategies

    root = Path(__file__).resolve().parents[1]
    t1 = yaml.safe_load((root / "config/account_testing.yaml").read_text())
    b = t1["strategies"]["ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD"]
    assert b["enabled"] and b["context"] == ["qqq_vwap"] and b["module"] == ST7Q and b["window"] == [950, 1500]
    assert b["min_adv"] == 95000000 and b["refire"] is False and b["scale_out_r"] is None
    assert t1["strategies"]["ST7-rsi50dn-long-pm-t1s1-FD"]["enabled"]
    o1 = t1["live"]["setup_order"]
    assert o1.index("ST8-volspikedn-long-pm-t1s1-FD") < o1.index("ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD") \
        < o1.index("ST6-volspikeup-short-mid-t1s1-FD")
    monkeypatch.setenv("MCF_ACCOUNT", "testing2")
    cfg = load_config()
    st = {s.name: s for s in build_strategies(cfg)}
    v1 = st["NS3V1-am-widestop-short"]
    assert v1.side == -1 and v1.geom == "t05s1" and v1.r_atr_frac == 0.5 and v1.window == [950, 1130]
    assert v1.refire and v1.refire_cooldown == 1 and v1.min_adv == 95000000
    o2 = cfg["live"]["setup_order"]
    assert o2.index("NS3V1-am-widestop-short") == o2.index("NS3-failed-vwap-reclaim-short-FD") - 1
    g = twin_groups(cfg)
    assert twin_key("NS3V1-am-widestop-short", g) == twin_key("NS3-failed-vwap-reclaim-short-FD", g) == "group:NS3-T2"
