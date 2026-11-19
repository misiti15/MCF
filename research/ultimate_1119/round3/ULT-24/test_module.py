"""Smoke test: ULT-24 CONFL-2 module imports and runs under the live LabStrategy (context spy_fo) for its three setups
(base from the setup name), never fires as frozen (the FIT base gate closed every base), fires on an opened copy when
>= CONF gated triggers coincide on a base, honours the base tape / cost rules, gives the GEOM "S" 2u stop, fails safe
without SPY context, and its features are point-in-time.
    pytest -q research/ultimate_1119/round3/ULT-24/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

MOD = Path(__file__).resolve().parents[2] / "modules" / "ULT-24.py"
TZ = "America/New_York"
OPEN_SRC = {
    'BASE_OPEN = {"BQ-L": {"H": False, "X": False}, "BM-L": {"H": False, "X": False}, "BM-S": {"H": False, "X": False}}':
        'BASE_OPEN = {"BQ-L": {"H": True, "X": True}, "BM-L": {"H": True, "X": True}, "BM-S": {"H": True, "X": True}}',
    'SURVIVE = {"BQ-L": (), "BM-L": (), "BM-S": ()}':
        'SURVIVE = {"BQ-L": ("TL-B", "TL-C"), "BM-L": ("TL-A", "TL-C", "TL-D"), "BM-S": ("TS-1", "TS-2", "TS-4")}',
}


def _load(path=MOD, name="ult24"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture()
def open_path(tmp_path):
    src = MOD.read_text()
    for a, b in OPEN_SRC.items():
        assert a in src
        src = src.replace(a, b)
    p = tmp_path / "ULT-24.py"
    p.write_text(src)
    (tmp_path / "ULT-24_symbols.json").write_text((MOD.parent / "ULT-24_symbols.json").read_text())
    return str(p)


def _pop_day(day="2026-11-18", spy="flat"):
    """Flat drift, then a 20-minute run-up from minute 100 (RSI5 >= 80, RSI2 >= 95), then a 5-minute bar that closes
    lower with an upper wick (roll-over), then flat."""
    px = [100.0]
    for k in range(1, 390):
        if k < 100:
            step = 0.004 * (1 if k % 2 else -1)
        elif k < 120:
            step = 0.12
        elif k < 125:
            step = -0.08
        else:
            step = 0.002 * (1 if k % 2 else -1)
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    hi = np.maximum(op, px) + 0.02
    hi[120:125] += 0.6                                  # upper wick on the roll-over bar
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    bars = pd.DataFrame({"open": op, "high": hi, "low": np.minimum(op, px) - 0.02, "close": px,
                         "volume": 50000.0}, index=idx)
    t = np.arange(390)
    s = 600 + 0.01 * np.sin(t) if spy == "flat" else 600 * (1 + 0.006 * np.clip(t / 60, 0, 1))
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, atr=6.0):
    return SimpleNamespace(symbol="NVDA", date=bars.index[0].date(), bars=bars, prior5=None, atr=atr,
                           prev_close=100.0, prev_high=101.0, prev_low=99.0, avg_dollar_volume=5e9, peers=peers)


def _st(path, name, geom=None):
    from mcf.strategies.setups import LabStrategy
    return LabStrategy(name, path, window=[1030, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=1e9, geom=geom)


def test_names_pick_bases_and_frozen_never_fires():
    from mcf.strategies.setups import _LAB_FRAMES
    assert _load(name="ult-24").BASE == "BQ-L" and _load(name="ult-24-m").BASE == "BM-L"
    s = _load(name="ult-24-s")
    assert s.BASE == "BM-S" and s.SIDE == "short"
    _LAB_FRAMES.clear()
    b, p = _pop_day()
    assert _st(str(MOD), "ULT-24-S").signals(_ctx(b, p)) == []          # gates closed: never fires as frozen


def test_short_confluence_fires_when_opened(open_path):
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    b, p = _pop_day()
    st = _st(open_path, "ULT-24-S")
    sigs = st.signals(_ctx(b, p))
    assert 1 <= len(sigs) <= 2, sigs
    s = sigs[0]
    t = b.index[s.bar_index]
    assert pd.Timestamp("2026-11-18 11:20", tz=TZ) <= t <= pd.Timestamp("2026-11-18 11:50", tz=TZ), t
    entry_close = float(b["close"].iloc[s.bar_index])
    assert s.side == -1 and s.target is None and abs((s.stop - entry_close) - 2 * 0.25 * 6.0) < 0.05   # 2u stop
    _LAB_FRAMES.clear()
    assert _st(open_path, "ULT-24-S").signals(_ctx(b, None)) == []        # no SPY context -> no signal
    _LAB_FRAMES.clear()
    b2, p2 = _pop_day(day="2026-11-17", spy="up")
    assert _st(open_path, "ULT-24-S").signals(_ctx(b2, p2)) == []         # SPY up > 0.20% since 09:50: base closed
    _LAB_FRAMES.clear()
    assert _st(open_path, "ULT-24-S").signals(_ctx(b, p, atr=3.0)) == []  # cost_r > 0.05 on a small ATR


def _frame(n=63, seed=0, sym="NVDA"):
    rng = np.random.default_rng(seed)
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
    h, lo = c * (1 + rng.uniform(0, 0.004, n)), c * (1 - rng.uniform(0, 0.004, n))
    return pd.DataFrame({"symbol": sym, "date": "2025-06-02", "tod": tod, "close": c, "high": h, "low": lo,
                         "fromOpen": (c / c[0] - 1) * 100, "gap": 0.0, "atr_d": 6.0, "adv20": 5e9,
                         "spy_fo": np.cumsum(rng.normal(0, 0.05, n)), "rsi": rng.uniform(20, 80, n),
                         "rsi5": rng.uniform(10, 95, n), "lower_wick": rng.uniform(0, 1, n),
                         "upper_wick": rng.uniform(0, 1, n), "volumeRatio": rng.uniform(0.5, 3, n),
                         "dist_lod_atr": rng.uniform(0, 1.5, n), "sma20_dist_pct": rng.normal(0, 2, n)})


def test_features_point_in_time(open_path):
    m = _load(open_path, "ult24open")
    df = _frame()
    full = m.features(df)
    fm = m.mask(df)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("cost_r", "spy60", "since950", "spy_r30", "rsi2"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, i)
        for k in full["trig"]:
            assert bool(full["trig"][k][i]) == bool(part["trig"][k][i]), (k, i)
        for k in full["bases"]:
            assert bool(full["bases"][k][i]) == bool(part["bases"][k][i]), (k, i)
        assert bool(fm[i]) == bool(m.mask(df.iloc[: i + 1].reset_index(drop=True))[i])


def test_universe_and_spy60_reference(open_path):
    m = _load(open_path, "ult24open2")
    df = pd.concat([_frame(sym="NVDA"), _frame(sym="GLD").assign(date="2025-06-03")], ignore_index=True)
    r = m.features(df)
    nv, gl = df.symbol.to_numpy() == "NVDA", df.symbol.to_numpy() == "GLD"
    assert not r["bases"]["BM-L"][gl].any() and not r["bases"]["BM-S"][gl].any()     # a fund is never MEGA
    assert not r["bases"]["BQ-L"][nv].any()                                           # a stock is never EQB
    # 10:30 -> reference = the open (spy60 = spy_fo); 10:40 -> the 09:50 bar; 11:00 -> exactly 09:55... t-60
    i1030 = int(np.flatnonzero(nv & (df.tod.to_numpy() == 1030))[0])
    assert abs(r["spy60"][i1030] - df.spy_fo[i1030]) < 1e-9
    i1100 = int(np.flatnonzero(nv & (df.tod.to_numpy() == 1100))[0])
    ref = float(df.spy_fo[np.flatnonzero(nv & (df.tod.to_numpy() == 1000))[0]])
    assert abs(r["spy60"][i1100] - ((1 + df.spy_fo[i1100] / 100) / (1 + ref / 100) - 1) * 100) < 1e-9
