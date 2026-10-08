"""Collect the live setups' entry signals on 2026-07-15..2026-09-15 exactly as mcf.backtest.engine.Backtester.run
generates them (same universe, in-play filter, ranking, eligibility, cost tier), plus the 1-minute bars of each
signal's symbol-day, so stop caps / exit rules can be re-simulated and re-allocated with the production engine.
Locked dates (>= 2026-09-16) are never loaded: BarStore.load(end=...) cuts them before anything is computed.
Output: research/oct7/exits/data/sigs.pkl (gitignored). Educational only - not financial advice."""
import pickle, time
from dataclasses import asdict
from mcf.backtest.engine import SymbolHistory, in_play_filter, rank_contexts, universe_ok, is_extended
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.setups import build_strategies

FIRST, LAST_EXCL = "2026-07-15", "2026-09-16"
cfg = load_config()
strats = build_strategies(cfg)
store = BarStore(cfg["data"]["cache_dir"])
t0 = time.time()
data = {}
for s in store.symbols():
    for _ in range(3):
        try:
            df = store.load(s, start="2026-06-01", end=LAST_EXCL); break
        except Exception:
            time.sleep(2); df = None
    if df is not None and len(df):
        data[s] = df
print(f"loaded {len(data)} symbols ({time.time()-t0:.0f}s)", flush=True)
hist = {s: SymbolHistory(s, df) for s, df in data.items()}
del data
dates = sorted({d for h in hist.values() for d in h.by_day if FIRST <= str(d) < LAST_EXCL})
out, bars = [], {}
for n, d in enumerate(dates):
    ctxs = [c for h in hist.values() if (c := h.context(d)) is not None and universe_ok(c, cfg)]
    orv = []
    for c in ctxs:
        rv = c.rvol()
        orv.append(rv.iloc[min(4, len(rv) - 1)] if len(rv) else float("nan"))
    ctxs, orv = in_play_filter(ctxs, orv, cfg)
    rank_contexts(ctxs)
    for c in ctxs:
        for s in strats:
            if not s.eligible(c):
                continue
            for sig in s.signals(c):
                out.append({"date": str(d), "symbol": c.symbol, "atr": c.atr, "ext": bool(is_extended(c, cfg)),
                            "sig": asdict(sig)})
                bars[(c.symbol, str(d))] = c.bars[["open", "high", "low", "close", "volume"]].copy()
    if n % 5 == 0:
        print(f"{d}: {len(out)} signals ({time.time()-t0:.0f}s)", flush=True)
pickle.dump({"signals": out, "bars": bars, "dates": [str(d) for d in dates], "setups": [s.name for s in strats]},
            open("research/oct7/exits/data/sigs.pkl", "wb"))
print(f"done: {len(out)} signals, {len(dates)} sessions, {time.time()-t0:.0f}s", flush=True)
