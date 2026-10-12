"""Live-path spot check: real SIP 1-minute bars through mcf.strategies.setups.LabStrategy.generate (heat_frame on
today's bars, ctx levels) for scored trade days and no-trade days of each module. Educational only - not financial
advice. The locked block is never loaded.

    python research/bdi/reddit1012liq/live/spot_live.py      # -> spot_live.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y")); sys.path.insert(0, str(STUDY))
import lib  # noqa: E402
import score as S  # noqa: E402
from verify import MODS  # noqa: E402
from mcf.strategies.setups import _LAB_FRAMES, LabStrategy  # noqa: E402

TZ = "America/New_York"


def day_bars(sym, d):
    t = pd.read_parquet(ROOT / "data" / "cache_hist" / "1Min" / f"{sym}.parquet",
                        filters=[("__index_level_0__", ">=", pd.Timestamp(d, tz=TZ)),
                                 ("__index_level_0__", "<", pd.Timestamp(d, tz=TZ) + pd.Timedelta(days=1))])
    t.index = pd.DatetimeIndex(t.index).tz_convert(TZ)
    m = t.index.hour * 60 + t.index.minute
    return t[(m >= 570) & (m < 960)][["open", "high", "low", "close", "volume"]]


def main():
    rng = np.random.default_rng(7)
    dates = list(lib.regimes().index)
    dayidx = {d: i for i, d in enumerate(dates)}
    out = {}
    for name, (sg, ex) in MODS.items():
        st = LabStrategy(name, f"research/bdi/reddit1012liq/live/{name}.py", window=[950, 1500])
        checks = []
        for month in ("2025-06", "2026-03"):
            M = S.Month(month, dayidx)
            rows, E, _ = M.candidates(*sg)
            T = S.run_exits(M, rows, E, sg[1], ex)
            tr = T["row"].astype(np.int64)
            pick = rng.choice(tr, size=min(6, len(tr)), replace=False)
            segs_tr = set(M.seg[tr])
            nont = [s for s in rng.choice(M.seg.max() + 1, 40, replace=False) if s not in segs_tr][:6]
            cases = [(i, True) for i in pick] + [(np.searchsorted(M.seg, s), False) for s in nont]
            for i, traded in cases:
                sym, d = M.b["symbol"].iloc[i], M.b["date"].iloc[i]
                bars = day_bars(sym, d)
                if len(bars) < 300:
                    continue
                _LAB_FRAMES.clear()
                ctx = SimpleNamespace(symbol=sym, date=d, bars=bars, prior5=None, atr=float(M.atr[i]),
                                      prev_close=float(M.b["c"].iloc[i]), prev_high=float(M.b["pdh"].iloc[i]),
                                      prev_low=float(M.b["pdl"].iloc[i]), avg_dollar_volume=2e8)
                sig = st.generate(ctx)
                if traded:
                    end = bars.index[sig[0].bar_index] + pd.Timedelta(minutes=1) if sig else None
                    got = None if end is None else end.hour * 100 + end.minute
                    e, st0, tg0, *_ = S.trade_params(M, np.array([i]), E[rows == i][:1], sg[1], ex[1], ex[2])
                    ok = got == int(M.tod[i]) and abs(sig[0].stop - st0[0]) < 0.02 and abs(sig[0].target - tg0[0]) < 0.05
                    checks.append({"sym": sym, "date": str(d), "scored_tod": int(M.tod[i]), "live_tod": got,
                                   "stop": [round(st0[0], 3), round(sig[0].stop, 3) if sig else None],
                                   "target": [round(tg0[0], 3), round(sig[0].target, 3) if sig else None], "agree": bool(ok)})
                else:
                    checks.append({"sym": sym, "date": str(d), "scored_tod": None,
                                   "live_tod": None if not sig else "signal", "agree": not sig})
            del M
        out[name] = {"checks": checks, "agree": sum(c["agree"] for c in checks), "n": len(checks)}
        print(name, out[name]["agree"], "/", out[name]["n"], flush=True)
        for c in checks:
            if not c["agree"]:
                print("  miss", c)
    json.dump(out, open(HERE / "spot_live.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
