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
A, B = sys.argv[1], sys.argv[2]           # keep trades on sessions A..B (inclusive); warm-up starts 31 days before A
end = min(pd.Timestamp(B) + pd.Timedelta(days=1), pd.Timestamp("2026-09-16"))
data = store.load_many(store.symbols(), start=str((pd.Timestamp(A) - pd.Timedelta(days=31)).date()), end=str(end.date()))
print("symbols", len(data), round(time.time() - t0), "s", flush=True)
strats = build_strategies(cfg)
print([s.name for s in strats], flush=True)
bt = Backtester(strats, cfg)
tr = bt.run(data, progress=True)
dt = pd.to_datetime(tr["date"])
tr = tr[(dt >= pd.Timestamp(A)) & (dt <= pd.Timestamp(B))]
tr.to_csv(OUT + f"trades_live_setups_{A}.csv", index=False)
print("trades", len(tr), round(time.time() - t0), "s")
print(tr.groupby("strategy")["r_multiple"].agg(["size", "mean", "sum"]))
