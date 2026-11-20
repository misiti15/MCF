"""Smoke test for beg06.py (synthetic trend-up day, mirror down day, a stop-out, and the live Strategy interface).
Educational only - not financial advice."""
import sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import beg06 as G
from mcf.strategies.base import DayContext

MOVE = np.full(390, 0.002)   # 0.2% noise band at every minute


def synth(sign=1, shock=False):
    idx = pd.date_range("2025-06-02 09:30", "2025-06-02 15:59", freq="1min", tz="America/New_York")
    n = len(idx)
    c = 500 + sign * np.linspace(0.0, 8.0, n)          # steady trend: +1.6% by the close
    if shock:
        c[100:] -= sign * 12.0                         # 11:10 crash through the hard stop
    o = np.r_[500.0, c[:-1]]
    h, l = np.maximum(o, c) + 0.05, np.minimum(o, c) - 0.05
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": np.full(n, 1e5)}, index=idx)


def arrs(b):
    hh = (b.index.hour * 100 + b.index.minute).to_numpy()
    return [b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")], hh


def run(sign):
    b = synth(sign)
    a, hh = arrs(b)
    assert G.is_check(hh).sum() == 11 and hh[G.is_check(hh)][0] == 959 and hh[G.is_check(hh)][-1] == 1459
    tr = G.session_trades(*a, hh, 500.0, 6.0, MOVE)
    assert len(tr) == 1, tr
    t = tr[0]
    assert t["side"] == sign and t["check"] >= 1000 and t["kind"] == G.KIND_TIME and t["xt"] == 1555, t
    assert abs(abs(t["fill"] - t["stop"]) - 1.5) < 1e-9
    # no band -> no trade when the band is huge
    assert G.session_trades(*a, hh, 500.0, 6.0, np.full(390, 0.5)) == []
    # stop-out then re-entry
    a2, hh2 = arrs(synth(sign, shock=True))
    tr2 = G.session_trades(*a2, hh2, 500.0, 6.0, MOVE)
    assert tr2[0]["kind"] == G.KIND_STOP and tr2[0]["xt"] == 1111, tr2
    ctx = DayContext(symbol="SPY", date=date(2025, 6, 2), bars=b, prev_close=500.0, prev_high=501, prev_low=499,
                     atr=6.0, avg_dollar_volume=5e10, avg_move=MOVE)
    st = G.BEG06()
    assert st.eligible(ctx) and not st.eligible(DayContext(symbol="IWM", date=ctx.date, bars=b, prev_close=1,
                                                         prev_high=1, prev_low=1, atr=1, avg_dollar_volume=1,
                                                         avg_move=MOVE))
    sigs = st.generate(ctx)
    assert len(sigs) == 1 and sigs[0].side == sign and sigs[0].bar_index == t["k"], sigs
    early = DayContext(symbol="SPY", date=ctx.date, bars=b.iloc[:t["k"]], prev_close=500.0, prev_high=501,
                       prev_low=499, atr=6.0, avg_dollar_volume=5e10, avg_move=MOVE)
    assert st.generate(early) == []                    # nothing before the trigger check
    print("ok", sign, {k: t[k] for k in ("check", "side", "fill", "stop", "kind", "xt")}, "shock:",
          [(x["side"], x["kind"], x["xt"]) for x in tr2])


if __name__ == "__main__":
    run(1)
    run(-1)
