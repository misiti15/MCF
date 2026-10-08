"""BDI collector: every QUALIFYING bar (not only the first) of each live setup on 2026-07-15..2026-09-15,
built exactly like mcf.backtest.engine.Backtester.run (same universe, in-play filter, ranking, eligibility,
cost tier), plus the 1-minute bars of every symbol-day with a hit. Used for the falling-knife management
study (task 1) and the trade-frequency / re-entry study (task 2).
Locked dates (>= 2026-09-16) are cut by BarStore.load(end=...) before anything is computed.

usage: python research/oct7/bdi/collect.py PART NPARTS      (dates split round-robin across parts)
Output: research/oct7/bdi/data/hits_<PART>.pkl (gitignored). Educational only - not financial advice."""
import pickle
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.backtest.engine import SymbolHistory, in_play_filter, rank_contexts, universe_ok, is_extended  # noqa: E402
from mcf.config import load_config  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import extra_features  # noqa: E402
from mcf.strategies.setups import HeatStrategy, LabStrategy, build_strategies  # noqa: E402

PART, NPARTS = int(sys.argv[1]), int(sys.argv[2])
FIRST, LAST_EXCL = "2026-07-15", "2026-09-16"
cfg = load_config()
strats = build_strategies(cfg)
store = BarStore(cfg["data"]["cache_dir"])


def frame5(ctx, lab=False):
    bars = ctx.bars
    d5 = resample(bars, "5min")
    hist = d5 if ctx.prior5 is None or ctx.prior5.empty else pd.concat([ctx.prior5, d5])
    f = heat_frame(hist)
    f["atr_d"] = ctx.atr
    if lab:
        f = f.join(extra_features(hist, f))
    f = f.iloc[-len(d5):].copy()
    f["gap"] = (float(d5["open"].iloc[0]) / ctx.prev_close - 1) * 100
    if lab:
        f["dist_pdh_atr"] = (ctx.prev_high - f["close"]) / ctx.atr
        f["dist_pdl_atr"] = (f["close"] - ctx.prev_low) / ctx.atr
    return d5, f


def all_hits(s, ctx):
    """[(bar_index_1m_end, side, px, score)] for every qualifying 5-minute bar (production takes the first)."""
    bars = ctx.bars
    if isinstance(s, HeatStrategy):
        d5, f = frame5(ctx)
        sc = np.asarray(s.mod.score(f), dtype=float)
        lo, hi = s.window or (950, 1500)
        tod = f["tod"].to_numpy()
        ok = (tod >= max(950, lo)) & (tod <= min(1500, hi))
        sides = []
        if s.sides in ("both", "long") and getattr(s.mod, "LONG_AT", None) is not None:
            sides.append((1, ok & (sc >= s.mod.LONG_AT)))
        if s.sides in ("both", "short") and getattr(s.mod, "SHORT_AT", None) is not None:
            sides.append((-1, ok & (sc <= s.mod.SHORT_AT)))
    elif isinstance(s, LabStrategy):
        d5, f = frame5(ctx, lab=True)
        tod = f["tod"].to_numpy()
        lo, hi = s.window or (950, 1500)
        m = np.asarray(s.mod.mask(f), dtype=bool) & (tod >= max(950, lo)) & (tod <= min(1500, hi))
        sc = np.zeros(len(f))
        sides = [(s.side, m)]
    else:
        return None
    out = []
    for side, m in sides:
        for i in np.flatnonzero(m):
            end = min(bars.index.searchsorted(d5.index[i] + pd.Timedelta(minutes=4)), len(bars) - 1)
            out.append((int(end), side, float(d5["close"].iloc[i]), float(sc[i])))
    return out


t0 = time.time()
data = {}
for sym in store.symbols():
    df = store.load(sym, start="2026-06-01", end=LAST_EXCL)
    if df is not None and len(df):
        data[sym] = df
hist = {s: SymbolHistory(s, df) for s, df in data.items()}
del data
dates = sorted({d for h in hist.values() for d in h.by_day if FIRST <= str(d) < LAST_EXCL})
mine = dates[PART::NPARTS]
print(f"part {PART}: {len(mine)} of {len(dates)} sessions, {len(hist)} symbols ({time.time()-t0:.0f}s)", flush=True)
hits, bars, funnel = [], {}, []
for n, d in enumerate(mine):
    ctxs = [c for h in hist.values() if (c := h.context(d)) is not None and universe_ok(c, cfg)]
    n_univ = len(ctxs)
    orv = []
    for c in ctxs:
        rv = c.rvol()
        orv.append(rv.iloc[min(4, len(rv) - 1)] if len(rv) else float("nan"))
    ctxs, orv = in_play_filter(ctxs, orv, cfg)
    rank_contexts(ctxs)
    fun = {"date": str(d), "universe": n_univ, "in_play": len(ctxs)}
    for c in ctxs:
        for s in strats:
            if not s.eligible(c):
                continue
            fun[f"elig_{s.name}"] = fun.get(f"elig_{s.name}", 0) + 1
            meta = {"date": str(d), "symbol": c.symbol, "setup": s.name, "atr": c.atr, "ext": bool(is_extended(c, cfg)),
                    "adv": c.avg_dollar_volume, "prev_close": c.prev_close, "gap": c.gap_pct}
            h = all_hits(s, c)
            if h is None:   # simple setups: their own signals (one per day by design)
                for sig in s.signals(c):
                    hits.append({**meta, "kind": "sig", "end": sig.bar_index, "side": sig.side, "stop": sig.stop,
                                 "target": sig.target, "entry_type": sig.entry_type, "entry_price": sig.entry_price,
                                 "entry_valid_bars": sig.entry_valid_bars,
                                 "exit_by": None if sig.exit_by is None else str(sig.exit_by), "score": 0.0, "px": None})
                    bars[(c.symbol, str(d))] = c.bars[["open", "high", "low", "close", "volume"]].copy()
                continue
            for end, side, px, sc in h:
                hits.append({**meta, "kind": "all", "end": end, "side": side, "px": px, "score": sc})
            if h:
                bars[(c.symbol, str(d))] = c.bars[["open", "high", "low", "close", "volume"]].copy()
    funnel.append(fun)
    print(f"{d}: {len(hits)} hits ({time.time()-t0:.0f}s)", flush=True)
pickle.dump({"hits": hits, "bars": bars, "funnel": funnel}, open(f"research/oct7/bdi/data/hits_{PART}.pkl", "wb"))
print(f"done part {PART}: {len(hits)} hits, {time.time()-t0:.0f}s", flush=True)
