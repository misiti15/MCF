"""Smoke test for beg07.py: universe pass (ranking, pin filter, ETB, ETF, price/ADV), the walk, and the live
Strategy interface + mcf.backtest.engine.simulate. Educational only - not financial advice."""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import beg07 as G  # noqa: E402
from mcf.backtest.engine import Costs, simulate  # noqa: E402
from mcf.strategies.base import DayContext  # noqa: E402


def snap():
    rows = []
    for i in range(15):                       # 15 losers -5%..-12%, not pinned
        rows.append(dict(symbol=f"L{i:02d}", c=100 * (1 - (5 + i * 0.5) / 100), pc=100, dh=101, dl=80, atr=3,
                         adv=1e8, is_etf=False, etb=1.0))
    for i in range(15):                       # 15 winners +5%..+12%
        rows.append(dict(symbol=f"W{i:02d}", c=100 * (1 + (5 + i * 0.5) / 100), pc=100, dh=125, dl=99, atr=3,
                         adv=1e8, is_etf=False, etb=1.0))
    rows += [dict(symbol="PINLO", c=70, pc=100, dh=101, dl=69.8, atr=3, adv=1e8, is_etf=False, etb=1.0),  # pinned at low
             dict(symbol="PINHI", c=130, pc=100, dh=130.1, dl=99, atr=3, adv=1e8, is_etf=False, etb=1.0),
             dict(symbol="HTB", c=140, pc=100, dh=150, dl=99, atr=3, adv=1e8, is_etf=False, etb=0.2),     # hard to borrow
             dict(symbol="ETFX", c=60, pc=100, dh=101, dl=50, atr=3, adv=1e8, is_etf=True, etb=1.0),
             dict(symbol="CHEAP", c=6, pc=10, dh=10, dl=5, atr=0.5, adv=1e8, is_etf=False, etb=1.0),
             dict(symbol="THIN", c=50, pc=100, dh=101, dl=40, atr=3, adv=2e7, is_etf=False, etb=1.0),
             dict(symbol="SMALL", c=98, pc=100, dh=101, dl=90, atr=3, adv=1e8, is_etf=False, etb=1.0)]   # -2%: no
    return pd.DataFrame(rows)


def main():
    s = snap()
    pk = G.pick(s)
    lo, hi = pk[pk.side == 1], pk[pk.side == -1]
    assert len(lo) == 10 and len(hi) == 10, (len(lo), len(hi))
    assert set(lo.symbol) == {f"L{i:02d}" for i in range(5, 15)}, sorted(lo.symbol)
    assert set(hi.symbol) == {f"W{i:02d}" for i in range(5, 15)}, sorted(hi.symbol)
    assert not set(pk.symbol) & {"PINLO", "PINHI", "HTB", "ETFX", "CHEAP", "THIN", "SMALL"}
    # walk: long, stop hit at bar 3
    o = np.array([10, 10.1, 10.0, 9.8, 9.9, 10.0]); h = o + 0.05; l = o - 0.05
    hh = np.array([1525, 1526, 1527, 1528, 1529, 1555])
    f, st, px, kind, xt = G.walk(o, h, l, 1, 0.2, G.P, hh)
    assert f == 10 and abs(st - 9.8) < 1e-12 and kind == 1 and px == 9.8 and xt == 1529, (f, st, px, kind, xt)
    f, st, px, kind, xt = G.walk(o, h, l, -1, 0.5, G.P, hh)
    assert kind == 0 and px == 10.0 and xt == 1555
    # live interface
    day = date(2025, 6, 2)
    G.BEG07.universe_pass(day, s)
    idx = pd.date_range("2025-06-02 09:30", "2025-06-02 15:59", freq="1min", tz="America/New_York")
    c = np.linspace(100, 90, len(idx)); c[-40:] = 90.0
    b = pd.DataFrame({"open": c, "high": c + 0.05, "low": c - 0.05, "close": c, "volume": 1e5}, index=idx)
    strat = G.BEG07()
    ctx = DayContext(symbol="L10", date=day, bars=b, prev_close=100.0, prev_high=101, prev_low=99, atr=3.0,
                     avg_dollar_volume=1e8)
    sig = strat.signals(ctx)
    assert len(sig) == 1 and sig[0].side == 1 and abs(sig[0].stop - (90 - 0.6)) < 1e-9, sig
    assert b.index[sig[0].bar_index].strftime("%H%M") == "1524"
    early = DayContext(symbol="L10", date=day, bars=b.iloc[:300], prev_close=100.0, prev_high=101, prev_low=99,
                       atr=3.0, avg_dollar_volume=1e8)
    assert strat.signals(early) == []
    other = DayContext(symbol="L00", date=day, bars=b, prev_close=100.0, prev_high=101, prev_low=99, atr=3.0,
                       avg_dollar_volume=1e8)
    assert strat.signals(other) == []
    tr = simulate(sig[0], b, pd.Timestamp("15:55").time(), Costs(bps=0, per_share=0, stop_extra_per_share=0))
    assert tr is not None
    print("ok", len(lo), len(hi), tr.exit_reason, round(tr.r_multiple, 3))


if __name__ == "__main__":
    main()
