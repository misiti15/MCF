"""Production backtest of every live setup (config/default.yaml) on data/cache sessions 2026-07-15..2026-09-15.
Loads with end='2026-09-16' (locked holdout never read). Educational only - not financial advice."""
import sys, time
sys.path.insert(0, ".")
import pandas as pd
from mcf.backtest.engine import Backtester
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.setups import build_strategies

OUT = "research/primitives/winning_periods/"
cfg = load_config()
store = BarStore(cfg["data"]["cache_dir"])
t0 = time.time()
data = store.load_many(store.symbols(), start="2026-06-01", end="2026-09-16")
print("symbols", len(data), round(time.time() - t0), "s", flush=True)
strats = build_strategies(cfg)
print([s.name for s in strats], flush=True)
bt = Backtester(strats, cfg)
tr = bt.run(data, progress=True)
tr = tr[pd.to_datetime(tr["date"]) >= pd.Timestamp("2026-07-15")]
tr.to_csv(OUT + "trades_live_setups.csv", index=False)
print("trades", len(tr), round(time.time() - t0), "s")
print(tr.groupby("strategy")["r_multiple"].agg(["size", "mean", "sum"]))
