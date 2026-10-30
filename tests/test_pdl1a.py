"""PDL-1a (owner exception 2026-10-30, Testing 2): the regime-day R2A legs CWT14-failbrk-pdl-p05-R2A-{long,short} and the
opt-in daily index context `spy_prng` they read. Parity with the research on the history: research/bdi/pdl1030/pdl1a.
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml

from mcf.strategies import lab_context as LC

ROOT = Path(__file__).resolve().parents[1]
NY = "America/New_York"
NAMES = ("CWT14-failbrk-pdl-p05-R2A-long", "CWT14-failbrk-pdl-p05-R2A-short")
CUT = 0.7956493496894836


def _spy(prng: float):
    return SimpleNamespace(prev_high=100.0 + prng * 5.0, prev_low=100.0, atr=5.0)


def _cfg(monkeypatch, acct="testing2"):
    from mcf.config import load_config

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    return load_config()


# ------------------------------------------------------------------------------------------------ the context column
def test_spy_prng_is_opt_in_by_name_only():
    assert LC.parse_context(["spy_prng"]) == ("spy_prng",)
    assert "spy_prng" not in LC.parse_context(True)          # `context: true` is unchanged for every other setup
    assert LC.daily_context_symbols(["spy_prng", "spy_fo"]) == {"SPY"}
    assert LC.daily_context_symbols(LC.CONTEXT_COLS) == set()
    assert LC.context_symbols(["spy_prng"]) == set()         # needs SPY's daily prior, not its intraday bars
    with pytest.raises(ValueError):
        LC.parse_context(["spy_prngx"])


def test_add_context_sets_the_daily_value_or_nan():
    f = pd.DataFrame({"close": [1.0, 2.0, 3.0]})
    g = LC.add_context(f, None, ("spy_prng",), {"SPY": _spy(1.25)})
    assert np.allclose(g["spy_prng"], 1.25) and "spy_prng" not in f
    assert np.isnan(LC.add_context(f, None, ("spy_prng",), None)["spy_prng"]).all()
    assert np.isnan(LC.add_context(f, None, ("spy_prng",), {"SPY": SimpleNamespace(prev_high=2, prev_low=1, atr=0)})["spy_prng"]).all()


# ------------------------------------------------------------------------------------------------ config
def test_config_testing2_only_and_labeled(monkeypatch):
    t2 = (ROOT / "config/account_testing2.yaml").read_text()
    assert "owner exception PDL-1a 2026-10-30: below the BAR90 bar (t 1.14 vs 4.355), forward observation" in t2
    cfg = _cfg(monkeypatch)
    for n in NAMES:
        s = cfg["strategies"][n]
        assert s["enabled"] and s["context"] == ["spy_prng"] and s["live_scale_out"]
        assert abs(s["scale_out_r"] - 0.25 / 3) < 1e-12 and "owner-exception" in s["tags"]
        assert n in cfg["live"]["setup_order"]
    for f in ("default.yaml", "account_testing.yaml", "account_gen.yaml", "account_graveyard.yaml"):
        st = yaml.safe_load((ROOT / "config" / f).read_text()).get("strategies") or {}
        assert not any(n in st for n in NAMES), f                  # Primary and the other accounts untouched


def _bars(lo_poke=98.5, reclaim=99.6, price_scale=1.0):
    """09:30-10:29 1-minute bars: flat 100, the 09:55 bucket pokes under the prior-day low 99 and closes under it, the
    10:00 bucket closes back above it (a failed prior-day-low break), then flat."""
    idx = pd.date_range("2026-11-02 09:30", periods=60, freq="1min", tz=NY)
    c = np.full(60, 100.0)
    lo = c - 0.05
    hi = c + 0.05
    k = (idx.hour == 9) & (idx.minute >= 55)
    c[k], lo[k], hi[k] = 98.9, lo_poke, 99.2
    k = (idx.hour == 10) & (idx.minute < 5)
    c[k], lo[k], hi[k] = reclaim, reclaim - 0.1, reclaim + 0.1
    s = price_scale
    return pd.DataFrame({"open": c * s, "high": hi * s, "low": lo * s, "close": c * s, "volume": 5000.0}, index=idx)


def _ctx(bars, spy, atr=5.0, s=1.0):
    return SimpleNamespace(symbol="PDLT", date=bars.index[0].date(), bars=bars, prior5=None, atr=atr * s,
                           prev_close=100.0 * s, prev_high=101.0 * s, prev_low=99.0 * s, avg_dollar_volume=2e8,
                           peers=None, index_priors=None if spy is None else {"SPY": spy})


def _legs(monkeypatch):
    from mcf.strategies.setups import build_strategies

    st = {s.name: s for s in build_strategies(_cfg(monkeypatch)) if s.name in NAMES}
    assert set(st) == set(NAMES)
    return st[NAMES[0]], st[NAMES[1]]


@pytest.mark.parametrize("prng,fires", [(CUT + 0.2, "long"), (CUT - 0.2, "short"), (CUT, None), (None, None)])
def test_regime_picks_exactly_one_leg(monkeypatch, prng, fires):
    from mcf.strategies.setups import _LAB_FRAMES

    lg, sh = _legs(monkeypatch)
    assert lg.structural and sh.structural and lg.daily_context_symbols == {"SPY"}
    _LAB_FRAMES.clear()
    ctx = _ctx(_bars(), None if prng is None else _spy(prng))
    got = {s.mod.SIDE: s.signals(ctx) for s in (lg, sh)}
    fired = [k for k, v in got.items() if v]
    assert fired == ([] if fires is None else [fires])
    if fires:
        (sig,) = got[fires]
        sd = 1 if fires == "long" else -1
        px = 99.6
        assert sig.side == sd
        assert sig.stop == pytest.approx(px - sd * 0.75 * 5.0)      # 3 x R1 (R1 = 0.25 ATR): same $ risk, 1/3 shares
        assert sig.target == pytest.approx(px + sd * 0.125 * 5.0)   # the parent's +0.5 R1 target price
        # scale-out level = entry + side x scale_out_r x |entry - stop| = +0.25 R1 = 0.0625 ATR, as scored
        assert sig.scale_out_r * abs(px - sig.stop) == pytest.approx(0.0625 * 5.0)


def test_cost_filter_on_the_first_signal_bar_only(monkeypatch):
    """Cost > 5% of R1 on the day's first signal bar skips the symbol-day (a later bar never replaces it)."""
    from mcf.strategies.setups import _LAB_FRAMES

    lg, _ = _legs(monkeypatch)
    _LAB_FRAMES.clear()
    # ATR 0.8 -> R1 0.2; cost ~ 2.4 x (0.01 + 1 bp) ~ 0.048 = 24% of R1 -> skipped
    assert lg.signals(_ctx(_bars(lo_poke=98.9, reclaim=99.2), _spy(CUT + 0.2), atr=0.8)) == []
    import pdl1a_lib as P   # loaded by the module (its folder is on sys.path)

    # ATR 3.5 (R1 0.875): the 10:05 reclaim costs 5.5% of R1 (x1.4 before 10:30) -> the symbol-day is skipped, although
    # the 11:00 reclaim alone would pass (4.6%)
    f = pd.DataFrame({"tod": [1000, 1005, 1100], "close": [99.0, 99.5, 99.4], "high": [99.2, 99.6, 99.5],
                      "low": [98.5, 99.4, 98.0], "atr_d": 3.5, "gap": 0.0, "fromOpen": 0.0, "dist_pdh_atr": 1.0,
                      "dist_pdl_atr": [0.0, 0.5 / 3.5, 0.4 / 3.5], "vwapDistPct": 0.0, "volumeRatio": 1.0,
                      "vol_climax": 0.0})
    assert not P.entries(f).any()
    assert list(P.entries(f.iloc[[0, 2]].reset_index(drop=True))) == [False, True]


def test_runner_loads_index_priors_only_when_asked(monkeypatch):
    """The runner gives contexts SPY's daily prior only when a setup reads spy_prng (fetched when SPY is not in the
    universe priors; never added to the watchlist); other accounts' runners are unchanged (index_priors None)."""
    from mcf.execution import runner as R
    from mcf.strategies.setups import build_strategies

    calls = []

    def fake_build(syms, day, feed="sip", exact_symbols=(), client=None, log=print):
        calls.append(list(syms))
        return {s: _spy(1.0) for s in syms}

    import mcf.data.priors as DP

    monkeypatch.setattr(DP, "build_priors", fake_build)
    cfg = _cfg(monkeypatch)
    st = [s for s in build_strategies(cfg) if s.name in NAMES]
    r = R.PaperRunner(cfg, st, {}, broker=SimpleNamespace(equity=lambda: 1e5))
    assert r.index_syms == {"SPY"} and "SPY" not in r.watchlist
    ip = r._load_index_priors(pd.Timestamp("2026-11-02").date())
    assert set(ip) == {"SPY"} and calls == [["SPY"]]
    r._load_index_priors(pd.Timestamp("2026-11-02").date())
    assert calls == [["SPY"]]                                    # loaded once per session
    cfg1 = _cfg(monkeypatch, "primary")
    r1 = R.PaperRunner(cfg1, build_strategies(cfg1), {}, broker=SimpleNamespace(equity=lambda: 1e5))
    assert r1.index_syms == set() and r1._load_index_priors(None) is None
