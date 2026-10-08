"""Diagnosis only (2 live days are not evidence, RESEARCH_RULES): replay each 2026-10-06/07 live paper trade on SIP
1-minute bars with its live stop/target, and show its peak (MFE), its worst point (MAE), and what the % caps and
the give-back rules would have done. Fill is approximated by the open of the live entry minute's bar.
Educational only - not financial advice."""
import json
import sys

import numpy as np
import pandas as pd

from mcf.backtest.engine import Backtester
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.journal import Journal
from mcf.strategies.base import Signal, t
from research.oct7.exits.sim import simulate2

J = sys.argv[1]
EXTRA = sys.argv[2] if len(sys.argv) > 2 else None    # pickle of fetched bars for symbols missing from the cache
cfg = load_config()
bt = Backtester([], cfg)
store = BarStore(cfg["data"]["cache_dir"])
extra = pd.read_pickle(EXTRA) if EXTRA else None
j = Journal(J)
tr = j.trades(j.get_or_create_run("paper", "MCF Update (live paper)"))

RULES = {"current": {}, "cap1.5%": {"cap": 1.5}, "cap3%": {"cap": 3.0},
         "be0.5": {"be_at_r": 0.5}, "trail0.75after1": {"trail_r": 0.75, "trail_after_r": 1.0},
         "scale0.5x0.5": {"scale_out_r": 0.5, "scale_out_frac": 0.5}, "gb(0.75->0.25)": {"gb": (0.75, 0.25)},
         "late15:30>0": {"late": ("15:30", 0.0)}}
if len(sys.argv) > 3:
    RULES.update(json.loads(sys.argv[3]))


def day_bars(sym, day):
    if extra is not None and sym in extra.index.get_level_values(0):
        df = extra.xs(sym, level=0).copy()
        df.index = df.index.tz_convert("America/New_York")
    else:
        df = store.load(sym, start=day)
    if df.empty:
        return df
    df = df[(df.index.date == pd.Timestamp(day).date())]
    return df.between_time("09:30", "15:59")[["open", "high", "low", "close", "volume"]]


rows = []
for r in tr.itertuples():
    day = str(r.date)[:10]
    b = day_bars(r.symbol, day)
    if b.empty:
        continue
    et = pd.Timestamp(r.entry_time).tz_convert("America/New_York").floor("min")
    jx = int(np.searchsorted(b.index, et))
    if jx <= 0 or jx >= len(b):
        continue
    ref = float(r.entry)
    out = {"symbol": r.symbol, "setup": r.strategy, "side": int(r.side), "date": day, "entry_min": str(et.time())[:5],
           "stop_pct": round(abs(ref - r.stop) / ref * 100, 2), "live_r": round(float(r.r_multiple), 2),
           "live_pnl": round(float(r.pnl), 2), "live_exit": r.exit_reason}
    for name, v in RULES.items():
        stop = float(r.stop)
        if "cap" in v and abs(ref - stop) / ref * 100 > v["cap"]:
            stop = ref - r.side * ref * v["cap"] / 100
        sig = Signal(symbol=r.symbol, strategy=r.strategy, side=int(r.side), bar_index=jx - 1, stop=stop,
                     target=None if pd.isna(r.target) else float(r.target),
                     **{k: val for k, val in v.items() if k in ("be_at_r", "trail_r", "trail_after_r", "scale_out_r",
                                                                "scale_out_frac")})
        x = simulate2(sig, b, bt.flatten, bt.costs, gb=v.get("gb"), lock=v.get("lock"),
                      late=(t(v["late"][0]), v["late"][1]) if "late" in v else None)
        if x is None:
            out[name] = None
            continue
        r0 = x.side * (x.exit - x.entry) / abs(x.entry - float(r.stop))
        if name == "current":
            out.update(sim_r=round(r0, 2), mfe_r=round(x.mfe_r, 2), mae_r=round(x.mae_r, 2),
                       mae_pct=round(x.mae_r * abs(x.entry - x.stop) / x.entry * 100, 2),
                       mfe_pct=round(x.mfe_r * abs(x.entry - x.stop) / x.entry * 100, 2), sim_exit=x.exit_reason,
                       sim_exit_time=str(x.exit_time.time())[:5])
        else:
            out[name] = f"{r0:+.2f}R {x.exit_reason}@{str(x.exit_time.time())[:5]}"
    rows.append(out)
df = pd.DataFrame(rows)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
print(df.to_string(index=False))
df.to_csv("research/oct7/exits/live_days.csv", index=False)
