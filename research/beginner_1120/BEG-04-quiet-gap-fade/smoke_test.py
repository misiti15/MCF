"""Smoke test for BEG-04 (synthetic bars). python smoke_test.py  -> 'OK'. Educational only - not financial advice."""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))
import beg04 as G  # noqa: E402
from mcf.strategies.base import DayContext  # noqa: E402

TZ = "America/New_York"


def bars(gap_up=True):
    """Gap up to 102 vs prev 100; 09:30-09:49 range 101.5-102.5; then drift down to 100.4 by 11:00, flat after."""
    idx = pd.date_range("2025-05-06 09:30", "2025-05-06 15:59", freq="1min", tz=TZ)
    n = len(idx)
    hh = idx.hour * 100 + idx.minute
    c = np.full(n, 102.0)
    r20 = hh <= 949
    c[r20] = 102 + 0.4 * np.sin(np.arange(r20.sum()))
    rest = np.flatnonzero(~r20)
    c[rest] = np.maximum(102.0 - 0.03 * np.arange(1, len(rest) + 1), 99.5)
    if not gap_up:
        c = 200 - c
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + 0.05
    lo = np.minimum(o, c) - 0.05
    v = np.full(n, 1000.0)
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "volume": v}, index=idx)


def main():
    for up in (True, False):
        b = bars(up)
        hh = (b.index.hour * 100 + b.index.minute).to_numpy()
        o, h, l, c, v = (b[k].to_numpy() for k in ("open", "high", "low", "close", "volume"))
        pc = 100.0 if up else 100.0 + 0.0
        if not up:
            pc = 100.0      # mirror: open ~98 vs prev 100 -> gap down
        side = G.universe_ok(pc, o[0], 80e6, 0.9, 400)
        assert side == (-1 if up else 1), side
        assert G.universe_ok(pc, o[0], 80e6, 1.6, 400) == 0      # unusual volume -> out
        assert G.universe_ok(pc, o[0], 80e6, 0.9, 50) == 0       # top-100 rvol rank -> out
        assert G.universe_ok(pc, o[0], 30e6, 0.9, 400) == 0      # ADV < $50M -> out
        e = G.find_entry(o, h, l, c, v, hh, side, pc, atr=3.0)
        assert e is not None and e["j"] == e["k"] + 1 and hh[e["k"]] >= 950
        # trigger bar: close beyond R20 and beyond VWAP
        r20 = hh <= 949
        if up:
            assert c[e["k"]] < l[r20].min() and e["stop"] <= h[r20].max() + 0.02 + 1e-9 and e["tgt"] == pc
        else:
            assert c[e["k"]] > h[r20].max() and e["stop"] >= l[r20].min() - 0.02 - 1e-9 and e["tgt"] == pc
        assert abs(e["ref"] - e["stop"]) <= 0.35 * 3.0 + 1e-9
        assert abs(e["tgt"] - e["ref"]) >= 1.2 * abs(e["ref"] - e["stop"])
        px, kind, xt = G.walk(o, h, l, c, hh, e["j"], side, e["stop"], e["tgt"])
        assert kind == 2 and px == pc, (px, kind, xt)       # drifts through prev_close -> target
        # tight ATR cap: stop = 0.35*ATR; a tiny ATR makes the 1.2R test pass more easily
        e2 = G.find_entry(o, h, l, c, v, hh, side, pc, atr=0.5)
        assert e2 is not None and abs(abs(e2["ref"] - e2["stop"]) - 0.175) < 1e-9
        # the 1.2R test skips the day when prev_close is too close
        e3 = G.find_entry(o, h, l, c, v, hh, side, pc + (1.6 if up else -1.6), atr=3.0)
        assert e3 is None
        # live class emits the same order on the trigger bar and nothing before / after
        st = G.Beg04QuietGapFade() if G.Strategy is not object else None
        if st is not None:
            acv = np.full(390, 1000.0 * 20 / 1.0)
            acv[19] = 20000.0 / 0.9
            for kk, want in ((e["k"] - 1, False), (e["k"], True), (e["k"] + 3, False)):
                ctx = DayContext(symbol="XYZ", date=date(2025, 5, 6), bars=b.iloc[:kk + 1], prev_close=pc,
                                 prev_high=pc, prev_low=pc, atr=3.0, avg_dollar_volume=80e6, avg_cum_volume=acv,
                                 rank_rvol20=400)
                sig = st.generate(ctx)
                assert bool(sig) == want, (kk, sig)
                if want:
                    s = sig[0]
                    assert s.side == side and abs(s.stop - e["stop"]) < 1e-9 and s.target == e["tgt"]
                    assert s.entry_type == "market" and s.exit_by.hour == 15 and s.exit_by.minute == 55
    # stop path: a long that reverses hits its stop at the stop price
    o = np.array([10, 10, 10.2, 9.0]); h = o + 0.05; l = o - 0.05; c = o; hh = np.array([1000, 1001, 1002, 1003])
    assert G.walk(o, h, l, c, hh, 1, 1, 9.5, 11.0) == (9.5, 1, 1004)
    assert G.walk(o, h, l, c, np.array([1553, 1554, 1555, 1556]), 1, 1, 8.0, 11.0) == (10.2, 0, 1555)
    print("OK")


if __name__ == "__main__":
    main()
