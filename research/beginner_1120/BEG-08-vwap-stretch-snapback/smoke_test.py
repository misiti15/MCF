"""Smoke test for BEG-08 (synthetic bars). python smoke_test.py -> 'OK'. Educational only - not financial advice."""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))
import beg08 as G  # noqa: E402
from mcf.strategies.base import DayContext  # noqa: E402

TZ = "America/New_York"


def session(day, closes):
    idx = pd.date_range(f"{day} 09:30", f"{day} 15:59", freq="1min", tz=TZ)
    c = np.asarray(closes, float)
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.02, "low": np.minimum(o, c) - 0.02, "close": c,
                         "volume": np.full(len(c), 1000.0)}, index=idx)


def build(up=True):
    rng = np.random.default_rng(1)
    prev = session("2025-05-05", 100 + np.cumsum(rng.normal(0, 0.02, 390)))
    n = 390
    c = np.full(n, 100.0)
    c[:60] = 100 + 0.05 * np.arange(60)            # 09:30-10:29: steady trend +3.0
    c[60:90] = c[59] + 0.01 * np.arange(1, 31)      # 10:30-10:59: grind higher (RSI stays high)
    c[90] = c[89] - 0.10                             # 11:00 reversal bar (close below prior low)
    c[91:] = np.maximum(c[90] - 0.05 * np.arange(1, n - 90), 99.0)   # snap back toward VWAP
    if not up:
        c = 200 - c
        prev = prev.copy()
        prev[["open", "high", "low", "close"]] = 200 - prev[["open", "low", "high", "close"]].to_numpy()
    return prev, session("2025-05-06", c)


def main():
    for up in (True, False):
        side = -1 if up else 1
        prev, b = build(up)
        allb = pd.concat([prev, b])
        rsi_all = G.rsi5_on_1min(allb.index, allb["close"].to_numpy())
        rsi = rsi_all[len(prev):]
        # live form (ctx.prior5) agrees with the backtest form
        p5 = prev.resample("5min").agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        rl = G.rsi5_live(b, p5)
        assert np.allclose(rl[60:], rsi[60:], equal_nan=True)
        hh = (b.index.hour * 100 + b.index.minute).to_numpy()
        o, h, l, c, v = (b[k].to_numpy() for k in ("open", "high", "low", "close", "volume"))
        atr = 1.5
        tr = G.day_trades(o, h, l, c, v, hh, rsi, atr)
        assert len(tr) >= 1, tr
        t = tr[0]
        assert t["side"] == side and hh[t["k"]] == 1100 and t["j"] == t["k"] + 1, t
        vw = G.vwap(h, l, c, v)
        assert abs(t["tgt"] - vw[t["k"]]) < 1e-9
        ext = h[t["s0"]:t["k"] + 1].max() if up else l[t["s0"]:t["k"] + 1].min()
        assert abs(t["stop"] - (ext - side * 0.05 * atr)) < 1e-9
        assert abs(t["tgt"] - t["ref"]) >= abs(t["ref"] - t["stop"])
        assert t["kind"] == 2 and t["px"] == t["tgt"], t     # snaps back through VWAP -> target
        # a large ATR kills the stretch condition -> no trades
        assert G.day_trades(o, h, l, c, v, hh, rsi, 20.0) == []
        # min-1R test: a far stop offset -> skip
        assert G.day_trades(o, h, l, c, v, hh, rsi, atr, p=dict(G.P, stop_atr=3.0)) == []
        # window: a trigger at 11:00 is outside a 10:00-10:30 window
        assert G.day_trades(o, h, l, c, v, hh, rsi, atr, p=dict(G.P, win_hi=1030)) == []
        # shorts barred -> the up case has no trade
        if up:
            assert G.day_trades(o, h, l, c, v, hh, rsi, atr, can_short=False) == []
        # live class: signal on the 11:00 bar, none on 10:59
        st = G.Beg08VwapStretchSnapback()
        for kk, want in ((t["k"] - 1, False), (t["k"], True)):
            ctx = DayContext(symbol="XYZ", date=date(2025, 5, 6), bars=b.iloc[:kk + 1], prev_close=100.0,
                             prev_high=101, prev_low=99, atr=atr, avg_dollar_volume=200e6, rank_rvol20=200,
                             prior5=p5)
            sig = st.generate(ctx)
            assert bool(sig) == want, (kk, sig)
            if want:
                s = sig[0]
                assert s.side == side and abs(s.stop - t["stop"]) < 1e-9 and abs(s.target - t["tgt"]) < 1e-9
                assert s.entry_type == "market" and (s.exit_by.hour, s.exit_by.minute) == (11, 46)
        ctx = DayContext(symbol="XYZ", date=date(2025, 5, 6), bars=b.iloc[:t["k"] + 1], prev_close=100.0, prev_high=101,
                         prev_low=99, atr=atr, avg_dollar_volume=200e6, rank_rvol20=20, prior5=p5)
        assert st.generate(ctx) == []          # headline name (rank <= 30) -> out
    # time stop: 45 minutes after the entry bar, at that bar's open
    n = 60
    hh = np.array([1000 + (i // 60) * 100 + i % 60 for i in range(n)])
    o = np.full(n, 10.0); h = o + 0.01; l = o - 0.01; c = o
    px, kind, xt, kx = G.walk(o, h, l, c, hh, 1, 1, 9.0, 11.0)
    assert kind == 0 and xt == 1046 and px == 10.0, (px, kind, xt)
    # stop first, gap-through fills at the worse of open/stop
    o2 = np.array([10, 10, 9.0, 9.0]); h2 = o2 + 0.05; l2 = o2 - 0.05; hh2 = np.array([1000, 1001, 1002, 1003])
    assert G.walk(o2, h2, l2, o2, hh2, 1, 1, 9.5, 11.0)[:2] == (9.0, 1)
    print("OK")


if __name__ == "__main__":
    main()
