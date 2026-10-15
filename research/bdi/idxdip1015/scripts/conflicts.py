"""Would other Testing-1 setups block the index-dip longs? On every dip day (any variant, locked block excluded) run
every enabled Testing-1 setup (config/account_testing.yaml as of 2026-10-15) on the 8 traded ETFs with the production
backtest path, and list positions held at any time 09:50-10:10 ET. A SHORT held there blocks our long
("opposite side held"); longs only use lots (max_lots_per_symbol 3). Educational only - not financial advice."""
import os

os.environ["MCF_ACCOUNT"] = "testing"
import pandas as pd
from common import OUT, VARIANTS, sample

from mcf.backtest.engine import Costs, SymbolHistory, simulate, universe_ok
from mcf.config import load_config
from mcf.strategies.base import t
from mcf.strategies.setups import build_strategies

cfg = load_config()
strats = build_strategies(cfg)
syms = ["SPY", "QQQ", "SSO", "SPUU", "SPXL", "UPRO", "QLD", "TQQQ"]
hist = {s: SymbolHistory(s, pd.read_parquet(f"{OUT.parents[2]}/data/cache_hist/1Min/{s}.parquet").between_time("09:30", "15:59"))
        for s in syms}
dd = pd.read_csv(OUT / "dipdays.csv")
dates = sorted({pd.Timestamp(d).date() for d in dd.date})
cost = Costs.from_cfg(cfg["costs"])
rows = []
for d in dates:
    if sample(d) == "LOCKED":
        continue
    ctxs = [c for h in hist.values() if (c := h.context(d)) is not None and universe_ok(c, cfg)]
    peers = {s: h.by_day[d] for s, h in hist.items() if d in h.by_day}
    for c in ctxs:
        c.peers = peers
        c.rank_rvol = c.rank_rvol20 = 999      # these ETFs are never top-N in play among ~1,200 names
        for st in strats:
            if not st.eligible(c):
                continue
            for sig in st.signals(c):
                tr = simulate(sig, c.bars, t("15:55"), cost)
                if tr and tr.entry_time.time() <= t("10:10") and tr.exit_time.time() >= t("09:50"):
                    rows.append({"date": d, "symbol": c.symbol, "setup": st.name, "side": tr.side,
                                 "entry": f"{tr.entry_time:%H:%M}", "exit": f"{tr.exit_time:%H:%M}"})
C = pd.DataFrame(rows)
C.to_csv(OUT / "conflicts.csv", index=False)
print(f"{len(dates)} dip days; positions by other Testing setups overlapping 09:50-10:10 on the 8 ETFs:")
print(C.to_string(index=False) if len(C) else "none")
