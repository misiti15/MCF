"""Collect every entry signal the live setups would have taken (SIP 1-minute store), once, so exit rules can be
re-simulated on exactly the same entries. Output: research/exits/data/signals.pkl (gitignored).
Educational only — not financial advice."""
import pickle, time, sys
from dataclasses import asdict
from pathlib import Path
from mcf.backtest.engine import SymbolHistory, in_play_filter, rank_contexts, universe_ok
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.setups import build_strategies

cfg = load_config()
strats = build_strategies(cfg)                      # exactly the setups trading live now
store = BarStore(cfg["data"]["cache_dir"])
t0 = time.time()
data = store.load_many(store.symbols())
hist = {s: SymbolHistory(s, df) for s, df in data.items() if len(df)}
dates = sorted({d for h in hist.values() for d in h.by_day if str(d) >= "2026-07-08"})
out = []
for n, d in enumerate(dates):
    ctxs = [c for h in hist.values() if (c := h.context(d)) is not None and universe_ok(c, cfg)]
    orv = [c.rvol().iloc[min(4, len(c.bars) - 1)] for c in ctxs]
    ctxs, _ = in_play_filter(ctxs, orv, cfg)
    rank_contexts(ctxs)
    for c in ctxs:
        for s in strats:
            if s.eligible(c):
                for sig in s.signals(c):
                    out.append({"date": str(d), "symbol": c.symbol, "atr": c.atr, "sig": asdict(sig)})
    if n % 5 == 0:
        print(f"{d}: {len(out)} signals ({time.time()-t0:.0f}s)", flush=True)
Path("research/exits/data").mkdir(parents=True, exist_ok=True)
pickle.dump({"signals": out, "setups": [s.name for s in strats], "dates": [str(d) for d in dates]},
            open("research/exits/data/signals.pkl", "wb"))
print(f"done: {len(out)} signals, {len(dates)} sessions, {time.time()-t0:.0f}s", flush=True)
