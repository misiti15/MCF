"""heat_fade_short entry delayed 1 / 2 / 3 minutes (owner: CHTR 10-07 'one extra minute or two'). Same stop/target
levels; market entry k bars later. 3 configs, train/valid only, bars read with end=2026-09-16. $ sizing as the allocator.
Educational only - not financial advice."""
import pickle, sys
from dataclasses import fields
import numpy as np
import pandas as pd
sys.path.insert(0, ".")
from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.base import Signal, t
cfg = load_config()
store, costs, FLAT = BarStore(cfg["data"]["cache_dir"]), Costs.from_cfg(cfg["costs"]), t(cfg["session"]["flatten_by"])
FIELDS = {f.name for f in fields(Signal)}
hs = [s for s in pickle.load(open("research/exits/data/signals.pkl", "rb"))["signals"]
      if s["sig"]["strategy"] == "heat_fade_short" and "2026-07-15" <= s["date"] <= "2026-09-15"]
rows = []
for sym in sorted({s["symbol"] for s in hs}):
    df = store.load(sym, end="2026-09-16")
    days = {str(d): g for d, g in df.groupby(df.index.date)}
    for s in [x for x in hs if x["symbol"] == sym]:
        bars = days.get(s["date"])
        if bars is None:
            continue
        for k in (0, 1, 2, 3):
            d = {kk: v for kk, v in s["sig"].items() if kk in FIELDS}
            d["bar_index"] += k
            tr = simulate(Signal(**d), bars, FLAT, costs)
            if tr is None:
                continue
            ps = abs(tr.entry - tr.stop)
            sh = int(min(250 / ps, 2000 / tr.entry)) if ps > 0 else 0
            if sh < 1:
                continue
            rows.append(dict(k=k, date=s["date"], symbol=sym, pnl=tr.side * (tr.exit - tr.entry) * sh, reason=tr.exit_reason,
                             adverse_at_entry=tr.side * (tr.entry - float(bars["close"].iloc[s["sig"]["bar_index"]]))))
D = pd.DataFrame(rows)
D["split"] = np.where(D.date <= "2026-08-25", "train", "valid")
for sp in ("train", "valid"):
    b = D[(D.k == 0) & (D.split == sp)].groupby("date").pnl.sum()
    for k in (1, 2, 3):
        v = D[(D.k == k) & (D.split == sp)]
        dv = v.groupby("date").pnl.sum().reindex(b.index, fill_value=0) - b
        print(sp, f"delay {k}m", "n", len(v), "$/trade", round(v.pnl.mean(), 2), "base $/trade", round(D[(D.k == 0) & (D.split == sp)].pnl.mean(), 2),
              "d total", round(dv.sum(), 1), "t_day", round(dv.mean() / (dv.std(ddof=1) / np.sqrt(len(dv))), 2), "ex-best", round(dv.sum() - dv.max(), 1),
              "stops", int((v.reason == "stop").sum()))
D.to_csv("research/oct7/autopsy/hfs_delay.csv", index=False)
