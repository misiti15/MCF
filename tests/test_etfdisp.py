"""ETFDISP (owner 2026-11-19): the ETF late dip (ULT-32 leg E) traded only after high cross-sectional dispersion days.
The opt-in daily market column `disp_prev` (mcf.strategies.lab_context) is computed before the open from the universe
priors (live runner) or the daily history (backtester), and the setup module runs under the live LabStrategy.
research/ultimate_1119/etfdisp/PLAN.md + RESULTS.md. Educational only - not financial advice."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from mcf.data.priors import Prior, _daily_part
from mcf.strategies import lab_context as LC
from mcf.strategies.base import DayContext
from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

MOD = "research/ultimate_1119/modules/ETFDISP-late-dip-hidisp-long.py"
NAME = "ETFDISP-late-dip-hidisp-long"
TZ = "America/New_York"


@pytest.fixture(autouse=True)
def _clear():
    LC._CACHE.clear()
    _LAB_FRAMES.clear()


def _bars(close, start="2026-11-18 09:30", vol=200_000.0):
    idx = pd.date_range(start, periods=len(close), freq="1min", tz=TZ)
    c = np.asarray(close, float)
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0004, "low": np.minimum(o, c) * 0.9996, "close": c,
                         "volume": np.full(len(c), vol)}, index=idx)


def _dip_day():
    """A 3x-ETF-like day: flat, +1.2% rally 14:10-14:20, then a -0.9% dip 14:20-14:30 (leg E fires at the 14:35 close)."""
    m = np.arange(390)
    return 30.0 * (1 + np.interp(m, [280, 290], [0, 0.012])) * (1 + np.interp(m, [290, 300], [0, -0.009]))


def _strategy():
    return LabStrategy(NAME, MOD, min_adv=95e6, window=[1400, 1500], context=["spy_fo", "disp_prev"],
                       symbols="module", geom="t05s1", refire=True, refire_cooldown=0, time_stop_min=45,
                       time_stop_min_r=99)


def _ctx(index_priors, symbol="SOXL"):
    b = _bars(_dip_day())
    spy = _bars(600 * (1 + 1e-5 * np.arange(390)))
    return DayContext(symbol=symbol, date=b.index[0].date(), bars=b, prev_close=30.0, prev_high=30.5, prev_low=29.5,
                      atr=2.4, avg_dollar_volume=5e8, peers={symbol: b, "SPY": spy}, index_priors=index_priors)


def _prior(ret, adv):
    return Prior(prev_close=10.0, prev_high=10.1, prev_low=9.9, atr=0.3, adv=adv, avg_volume=1e6, avg_cum=None,
                 avg_move=None, prev_ret=ret)


def test_disp_prev_is_opt_in_by_name_only():
    assert LC.parse_context(["spy_fo", "disp_prev"]) == ("spy_fo", "disp_prev")
    assert "disp_prev" not in LC.parse_context(True)          # `context: true` is unchanged for every other setup
    assert LC.market_daily_cols(("spy_fo", "disp_prev")) == ("disp_prev",)
    assert LC.daily_context_symbols(["disp_prev"]) == set() and LC.context_symbols(["disp_prev"]) == set()
    st = _strategy()
    assert st.market_daily_cols == ("disp_prev",) and st.context == ("spy_fo", "disp_prev")
    assert st.symbols == st.mod.SYMBOLS and "SOXL" in st.symbols and len(st.symbols) == 124
    assert (st.up, st.dn) == (0.5, 1.0) and st.params["time_stop_min"] == 45


def test_cross_dispersion_definition():
    rng = np.random.default_rng(7)
    r = rng.normal(0, 0.02, 300)
    r[0], r[1] = 0.9, np.nan                                   # clipped to +50%; NaN dropped
    a = np.full(300, 1e8)
    a[2:12] = 5e7                                              # below $95M: left out
    ok = np.isfinite(r) & (a >= 95e6)
    want = np.std(np.clip(r[ok], -0.5, 0.5), ddof=1) * 100
    assert LC.cross_dispersion(r, a) == pytest.approx(want)
    assert np.isnan(LC.cross_dispersion(r[:50], a[:50]))      # < 100 names: NaN (fail safe)
    pri = {f"S{i}": _prior(x, y) for i, (x, y) in enumerate(zip(r, a))}
    assert LC.market_daily(pri)["disp_prev"] == pytest.approx(want)
    old = {k: SimpleNamespace(adv=1e8) for k in range(200)}    # priors without prev_ret (pickled before ETFDISP)
    assert np.isnan(LC.market_daily(old)["disp_prev"])


def test_priors_record_prev_ret():
    idx = pd.date_range("2026-10-01", periods=25, freq="B", tz="UTC")
    c = 50 + np.arange(25, dtype=float)
    df = pd.DataFrame({"open": c, "high": c + 1, "low": c - 1, "close": c, "volume": 1e6},
                      index=pd.MultiIndex.from_product([["XYZ"], idx]))
    day = (idx[-1] + pd.Timedelta(days=1)).date()
    d = _daily_part(df, day)["XYZ"]
    assert d["prev_ret"] == pytest.approx(c[-1] / c[-2] - 1)
    assert np.isnan(Prior(1, 1, 1, 1, 1, 1, None, None).prev_ret)   # default: unknown


def test_runner_loads_market_context_once():
    from mcf.execution.runner import PaperRunner

    rng = np.random.default_rng(3)
    pri = {f"S{i}": _prior(float(x), 2e8) for i, x in enumerate(rng.normal(0, 0.03, 150))}
    me = SimpleNamespace(index_syms=set(), market_cols=("disp_prev",), index_priors=None, _index_tries=0, priors=pri,
                         health={}, cfg={}, index_priors_client=None)
    out = PaperRunner._load_index_priors(me, pd.Timestamp("2026-11-20").date())
    want = LC.market_daily(pri)["disp_prev"]
    assert out[LC.MARKET_KEY]["disp_prev"] == pytest.approx(want) and me.health["market_daily"]["disp_prev"] > 0
    me2 = SimpleNamespace(index_syms=set(), market_cols=(), index_priors=None, _index_tries=0, priors=pri, health={})
    assert PaperRunner._load_index_priors(me2, None) is None   # no setup asks: nothing changes


@pytest.mark.parametrize("disp, n", [(3.0, 1), (2.6438, 1), (2.64, 0), (float("nan"), 0), (None, 0)])
def test_etfdisp_gate_under_live_engine(disp, n):
    """The module under the live LabStrategy: leg E fires on the fixture dip only when disp_prev >= 2.6438."""
    st = _strategy()
    ip = None if disp is None else {LC.MARKET_KEY: {"disp_prev": disp}}
    ctx = _ctx(ip)
    assert st.eligible(ctx)
    sig = st.signals(ctx)
    assert len(sig) == n
    if n:
        s = sig[0]
        e = s.stop + 0.6                                       # R = 0.25 x daily ATR 2.4 = 0.6
        assert s.side == 1 and s.target == pytest.approx(e + 0.3) and s.time_stop_min == 45
        assert ctx.bars.index[s.bar_index].strftime("%H:%M") == "14:34"   # decided at the 14:35 bar close


def test_etfdisp_only_on_module_symbols():
    st = _strategy()
    ctx = _ctx({LC.MARKET_KEY: {"disp_prev": 3.0}}, symbol="AAPL")
    assert not st.eligible(ctx)


def test_backtester_feeds_disp_prev(tmp_path, monkeypatch):
    """Backtester: disp_prev = dispersion of the PRIOR session's daily returns (from each symbol's own history)."""
    from mcf.backtest.engine import Backtester, daily_from_intraday
    from mcf.config import load_config
    from mcf.data.synthetic import make_universe

    p = tmp_path / "rec_mod.py"
    p.write_text("import numpy as np\nSIDE='long'\nGEOM='t1s1'\nSEEN={}\n"
                 "def mask(df):\n    SEEN.setdefault(str(df.index[0].date()), set()).update(np.unique(df['disp_prev'].to_numpy(float)).tolist())\n"
                 "    return np.zeros(len(df), bool)\n")
    real = LC.cross_dispersion
    monkeypatch.setattr(LC, "cross_dispersion", lambda r, a: real(r, a, min_adv=0.0, min_names=3))
    data = make_universe(["A1", "A2", "A3", "A4", "A5"], days=18, start="2025-03-03")
    st = LabStrategy("rec", str(p), context=["disp_prev"])
    Backtester([st], load_config()).run(data)
    seen = st.mod.SEEN
    days = sorted({d for df in data.values() for d in df.index.date})
    closes = pd.DataFrame({s: daily_from_intraday(df)["close"] for s, df in data.items()})
    rets = closes.pct_change(fill_method=None)
    checked = 0
    for i in range(2, len(days)):
        if str(days[i]) not in seen:
            continue
        want = np.std(rets.iloc[i - 1].to_numpy(float), ddof=1) * 100
        v = seen[str(days[i])]
        assert len(v) == 1 and next(iter(v)) == pytest.approx(want)   # one constant value per session
        checked += 1
    assert checked >= 1


YAML_BLOCK = """
strategies:
  ETFDISP-late-dip-hidisp-long:
    enabled: true
    type: lab
    module: research/ultimate_1119/modules/ETFDISP-late-dip-hidisp-long.py
    symbols: module
    min_adv: 95000000
    window: [1400, 1500]
    geom: t05s1
    context: [spy_fo, disp_prev]
    refire: true
    refire_cooldown: 0
    time_stop_min: 45
    time_stop_min_r: 99
    scale_out_r: null
"""


def test_yaml_block_builds_under_live_loader():
    """The config block for a testing account (research/ultimate_1119/etfdisp/RESULTS.md) builds the live setup."""
    import yaml

    from mcf.strategies.setups import LOAD_FAILURES, build_strategies

    (st,) = build_strategies(yaml.safe_load(YAML_BLOCK))
    assert not LOAD_FAILURES
    assert st.name == NAME and st.market_daily_cols == ("disp_prev",) and st.refire and st.refire_cooldown == 0
    assert st.window == [1400, 1500] and st.min_adv == 95e6 and st.params["time_stop_min"] == 45
    sig = st.signals(_ctx({LC.MARKET_KEY: {"disp_prev": 3.1}}))
    assert len(sig) == 1 and sig[0].time_stop_min == 45 and sig[0].time_stop_min_r == 99
