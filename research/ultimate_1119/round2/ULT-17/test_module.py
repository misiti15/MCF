"""Smoke test: ULT-17 SECTOR-LAG module imports and runs under the live LabStrategy (context spy_fo, GEOM "S"); fails
safe without the sector columns (the documented live gap); with the sector columns supplied (simulating the runner
extension: sector ETF fromOpen per bar + sector ATR% + beta) it fires long when the sector jumps and the name lags,
short on the mirror, not when the name already followed, gives the 2u catastrophic stop, honours the universal
filters, and its features are point-in-time.
    pytest -q research/ultimate_1119/round2/ULT-17/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-17.py")
TZ = "America/New_York"
SYM = "AAPL"     # a lab stock (module SYMBOLS)


def _load(name="ult17"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bars(px, day="2026-11-18"):
    px = np.asarray(px, float)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=len(px), freq="1min", tz=TZ)
    return pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01,
                         "close": px, "volume": 20000.0}, index=idx)


def _day(sgn=1, follow=False, spy_mode="flat", jump_at=240):
    """Sector ETF drifts flat, then moves sgn x 0.9% over 10 minutes ending at minute jump_at (13:30); the name stays
    flat (lags) unless follow=True (it moves 1.8% with the sector)."""
    t = np.arange(390)
    leg = np.clip((t - (jump_at - 10)) / 10, 0, 1)
    sec = 50 * (1 + sgn * 0.009 * leg) + 0.001 * np.sin(t)
    name = 100 * (1 + (sgn * 0.018 * leg if follow else 0)) + 0.002 * np.sin(t)
    if spy_mode == "flat":
        s = 600 + 0.01 * np.sin(t)
    else:   # "falling": SPY -0.5% from the open and falling over the last 30 min at 13:30
        s = 600 * (1 - 0.005 * np.clip((t - 150) / 90, 0, 1))
    return _bars(name), _bars(sec), _bars(s)


def _patch_sector(monkeypatch, secb, atrp=1.2, beta=1.0):
    """Simulates the runner extension: add sec_fo / sec_atrp / sec_beta to the setup's frame copy."""
    import mcf.strategies.lab_context as lc
    orig = lc.add_context

    def add(f, peers, cols, index_priors=None):
        g = orig(f, peers, cols, index_priors)
        d5 = secb.resample("5min", label="left", closed="left").agg({"open": "first", "close": "last"})
        fo = (d5["close"] / float(d5["open"].iloc[0]) - 1) * 100
        g["sec_fo"] = fo.reindex(f.index).to_numpy(float)
        g["sec_atrp"] = atrp
        g["sec_beta"] = beta
        return g
    monkeypatch.setattr(lc, "add_context", add)


def _ctx(bars, spyb):
    return SimpleNamespace(symbol=SYM, date=bars.index[0].date(), bars=bars, prior5=None, atr=3.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers={"SPY": spyb})


def _sigs(name, bars, spyb):
    from mcf.strategies.setups import LabStrategy, _LAB_FRAMES, _LAB_D5
    import mcf.strategies.lab_context as lc
    _LAB_FRAMES.clear(); _LAB_D5[:] = [None, None]; lc._CACHE.clear()   # synthetic days share cache keys
    st = LabStrategy(name, MOD, window=[1015, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=50_000_000, symbols="module")
    return st.signals(_ctx(bars, spyb))


def test_fail_safe_without_sector_columns():
    b, _, s = _day(1)
    assert _sigs("ULT-17-L", b, s) == []


@pytest.mark.parametrize("sgn,name", [(1, "ULT-17-L"), (-1, "ULT-17-S")])
def test_fires_in_sector_direction_when_name_lags(monkeypatch, sgn, name):
    b, sec, s = _day(sgn)
    _patch_sector(monkeypatch, sec)
    sig = _sigs(name, b, s)
    assert 1 <= len(sig) <= 2, sig
    t = b.index[sig[0].bar_index]
    assert pd.Timestamp("2026-11-18 13:25", tz=TZ) <= t <= pd.Timestamp("2026-11-18 13:40", tz=TZ), t
    assert sig[0].side == sgn
    e = float(b["close"].iloc[sig[0].bar_index])
    assert sig[0].target is None
    assert abs(sgn * (e - sig[0].stop) - 2 * 0.25 * 3.0) < 0.05     # 2u catastrophic stop


@pytest.mark.parametrize("sgn,other", [(1, "ULT-17-S"), (-1, "ULT-17-L")])
def test_other_side_and_followed_name_do_not_fire(monkeypatch, sgn, other):
    b, sec, s = _day(sgn)
    _patch_sector(monkeypatch, sec)
    assert _sigs(other, b, s) == []
    b2, sec2, s2 = _day(sgn, follow=True)
    _patch_sector(monkeypatch, sec2)
    assert _sigs("ULT-17-L" if sgn > 0 else "ULT-17-S", b2, s2) == []


def test_universal_long_filter_blocks_into_falling_spy(monkeypatch):
    b, sec, s = _day(1, spy_mode="falling")
    _patch_sector(monkeypatch, sec)
    assert _sigs("ULT-17-L", b, s) == []


def test_etf_not_traded():
    m = _load()
    assert "SPY" not in m.SYMBOLS and "XLK" not in m.SYMBOLS and SYM in m.SYMBOLS


def test_point_in_time():
    m = _load()
    n = 60
    mins = 9 * 60 + 50 + 5 * np.arange(n)
    tod = (mins // 60) * 100 + mins % 60
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"tod": tod, "close": 100 + rng.normal(0, 0.3, n).cumsum(), "atr_d": 3.0, "gap": 0.2,
                       "rsi5": 50 + rng.normal(0, 10, n), "spy_fo": rng.normal(0, 0.3, n),
                       "sec_fo": rng.normal(0, 0.5, n).cumsum() * 0.1, "sec_atrp": 1.2, "sec_beta": 1.1,
                       "date": "2026-11-18", "symbol": SYM})
    full = m.features(df)
    cut = m.features(df.iloc[:40].copy())
    for k in ("sret3", "nret3", "lag", "spy_r30", "intake"):
        a, c = np.asarray(full[k])[:40], np.asarray(cut[k])
        assert np.allclose(np.nan_to_num(a.astype(float), nan=-9), np.nan_to_num(c.astype(float), nan=-9)), k
