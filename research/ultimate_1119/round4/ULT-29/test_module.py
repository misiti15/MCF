"""Smoke test: ULT-29 EARN-CONFL module imports and runs under the live LabStrategy (context spy_fo) for its two setups
(base from the setup name), never fires as frozen (the FIT base gate closed every base), fires on an opened copy when
>= CONF gated triggers coincide on a reaction-day base, needs a reaction day (RD file / earn_rd column), gives the GEOM
"S" 2u stop, fails safe without SPY context, its features are point-in-time, and rd_events() maps bmo / amc correctly
and never jumps a gap in the session list.
    pytest -q research/ultimate_1119/round4/ULT-29/test_module.py
Educational only - not financial advice."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

MOD = Path(__file__).resolve().parents[2] / "modules" / "ULT-29.py"
TZ = "America/New_York"
OPEN_SRC = {
    'BASE_OPEN = {"EB-L": {"H": False, "X": False}, "EB-S": {"H": False, "X": False}}':
        'BASE_OPEN = {"EB-L": {"H": True, "X": True}, "EB-S": {"H": True, "X": True}}',
    'SURVIVE = {"EB-L": (), "EB-S": ()}': 'SURVIVE = {"EB-L": ("L1", "L2", "L3", "L4"), "EB-S": ("S1", "S2", "S3", "S4")}',
}
DAY = "2026-11-18"


def _load(path=MOD, name="ult29"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _open_dir(tmp_path, rd_syms=("NVDA",), day=DAY, file_day=None):
    src = MOD.read_text()
    for a, b in OPEN_SRC.items():
        assert a in src
        src = src.replace(a, b)
    src = src.replace('d = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")', f'd = "{day}"')
    p = tmp_path / "ULT-29.py"
    p.write_text(src)
    (tmp_path / "ULT-29_rd.json").write_text(json.dumps({file_day or day: list(rd_syms)}))
    return str(p)


def _gap_day(day=DAY, gap=+0.05, prev=100.0):
    """Gap-up open, quiet drift, then from minute 60 a rally of 5-min bars with rising volume (new highs, close above
    VWAP, prior close beaten, RSI5 resetting above 40 after a dip at minutes 50-60)."""
    o = prev * (1 + gap)
    px = [o]
    for k in range(1, 390):
        if k < 50:
            step = 0.01 * (1 if k % 2 else -1)
        elif k < 60:
            step = -0.03
        elif k < 90:
            step = 0.06
        else:
            step = 0.005 * (1 if k % 2 else -1)
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    vol = np.full(390, 40000.0)
    vol[60:90] = 200000.0
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01, "close": px,
                         "volume": vol}, index=idx)
    t = np.arange(390)
    s = 600 + 0.01 * np.sin(t)
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, atr=6.0, sym="NVDA", prev=100.0):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=atr,
                           prev_close=prev, prev_high=prev + 1, prev_low=prev - 1, avg_dollar_volume=5e9, peers=peers)


def _st(path, name, geom=None, symbols="module"):
    from mcf.strategies.setups import LabStrategy
    return LabStrategy(name, path, window=[1000, 1300], context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=30e6, geom=geom, symbols=symbols)


def test_names_pick_bases_and_frozen_never_fires():
    from mcf.strategies.setups import _LAB_FRAMES
    assert _load(name="ult-29").BASE == "EB-L"
    s = _load(name="ult-29-s")
    assert s.BASE == "EB-S" and s.SIDE == "short"
    _LAB_FRAMES.clear()
    b, p = _gap_day()
    assert _st(str(MOD), "ULT-29", symbols=None).signals(_ctx(b, p)) == []     # gates closed: never fires as frozen


def test_long_confluence_fires_when_opened_and_needs_rd(tmp_path):
    from mcf.strategies.setups import _LAB_FRAMES
    path = _open_dir(tmp_path)
    _LAB_FRAMES.clear()
    b, p = _gap_day()
    sigs = _st(path, "ULT-29").signals(_ctx(b, p))
    assert 1 <= len(sigs) <= 2, sigs
    s = sigs[0]
    t = b.index[s.bar_index]
    assert pd.Timestamp(f"{DAY} 10:00", tz=TZ) <= t <= pd.Timestamp(f"{DAY} 13:05", tz=TZ), t   # window
    entry_close = float(b["close"].iloc[s.bar_index])
    assert s.side == 1 and s.target is None and abs((entry_close - s.stop) - 2 * 0.25 * 6.0) < 0.05   # 2u stop
    _LAB_FRAMES.clear()
    st = _st(path, "ULT-29")
    assert st.eligible(_ctx(b, p)) and not st.eligible(_ctx(b, p, sym="AAPL"))  # runner/engine gate: RD names only
    _LAB_FRAMES.clear()
    assert _st(path, "ULT-29").signals(_ctx(b, None)) == []                    # no SPY context -> no signal
    _LAB_FRAMES.clear()
    b2, p2 = _gap_day(gap=0.0)
    assert _st(path, "ULT-29").signals(_ctx(b2, p2)) == []                     # no >= +2% gap: base closed
    _LAB_FRAMES.clear()
    assert _st(path, "ULT-29").signals(_ctx(b, p, atr=0.5)) == []              # cost_r > 0.08 on a tiny ATR
    _LAB_FRAMES.clear()
    (tmp_path / "y").mkdir()
    path2 = _open_dir(tmp_path / "y", file_day="2026-11-17")
    assert _st(path2, "ULT-29").signals(_ctx(b, p)) == []                      # RD file has no entry for today


def _frame(n=63, seed=0, sym="NVDA", rd=True):
    rng = np.random.default_rng(seed)
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
    h, lo = c * (1 + rng.uniform(0, 0.004, n)), c * (1 - rng.uniform(0, 0.004, n))
    return pd.DataFrame({"symbol": sym, "date": "2025-06-02", "tod": tod, "close": c, "high": h, "low": lo,
                         "fromOpen": (c / c[0] - 1) * 100, "gap": 3.0, "atr_d": 6.0, "adv20": 5e9,
                         "spy_fo": np.cumsum(rng.normal(0, 0.05, n)), "rsi5": rng.uniform(10, 95, n),
                         "volumeRatio": rng.uniform(0.5, 3, n), "vwapDistPct": rng.normal(0, 0.5, n),
                         "dist_hod_atr": rng.uniform(0, 0.1, n), "dist_lod_atr": rng.uniform(0, 0.1, n),
                         "earn_rd": rd})


def test_features_point_in_time(tmp_path):
    m = _load(_open_dir(tmp_path), "ult29open")
    df = _frame()
    full = m.features(df)
    fm = m.mask(df)
    assert fm.any()
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("cost_r", "spy_r30", "vwap"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, i)
        for k in full["trig"]:
            assert bool(full["trig"][k][i]) == bool(part["trig"][k][i]), (k, i)
        for k in full["bases"]:
            assert bool(full["bases"][k][i]) == bool(part["bases"][k][i]), (k, i)
        assert bool(fm[i]) == bool(m.mask(df.iloc[: i + 1].reset_index(drop=True))[i])
    assert not m.mask(_frame(rd=False)).any()                                  # not a reaction day -> never
    assert not m.features(df)["bases"]["EB-L"][df.tod.to_numpy() < 1000].any()  # window 10:00-13:00


def test_rd_events_bmo_amc_and_gaps():
    m = _load(name="ult29rd")
    sessions = ["2024-10-29", "2024-10-30", "2024-10-31", "2025-03-03", "2025-03-04", "2025-03-05"]
    e = pd.DataFrame({"symbol": ["A", "B", "C", "D", "E", "A"],
                      "date": pd.to_datetime(["2024-10-29", "2024-10-29", "2024-10-31", "2025-03-03", "2025-03-04",
                                              "2025-03-04"]),
                      "session": ["bmo", "amc", "amc", "dmh", "amc", "bmo"]})
    ev = m.rd_events(e, sessions)
    got = set(zip(ev.symbol, ev.rd))
    assert ("A", "2024-10-29") in got and ("B", "2024-10-30") in got
    assert not any(s == "C" for s, _ in got)          # amc 10-31 -> next listed session 03-03: gap > 5 days, dropped
    assert not any(s == "D" for s, _ in got)          # dmh excluded
    assert ("E", "2025-03-05") in got
    assert ("A", "2025-03-04") not in got             # repeat within 10 sessions keeps the first
