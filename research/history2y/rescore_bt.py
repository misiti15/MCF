"""Re-score the live 1-minute setups that are not lab-frame setups (orb20_a, intraday_momentum) on the 2-year history
with the production backtester path of research/setup_screen.py (mcf.backtest.engine: SymbolHistory contexts,
universe filters, in-play filter, opening-rvol ranks, conservative fills and production costs; one book per setup,
no slot limits). Runs in chunks of calendar months with ~2 months of warm-up so memory stays bounded. The rule-19
locked block (2024-11..2025-02) is never simulated. Output: research/history2y/data/bt_trades.parquet.

    python research/history2y/rescore_bt.py [--chunk-months 3]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.backtest.engine import Backtester, SymbolHistory, in_play_filter, is_extended, rank_contexts, simulate, universe_ok  # noqa: E402
from mcf.config import load_config  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.strategies.base import t  # noqa: E402
from mcf.strategies.setups import build_strategies  # noqa: E402

SETUPS = ["orb20_a", "intraday_momentum"]
LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
OUT = ROOT / "research" / "history2y" / "data" / "bt_trades.parquet"


def main(chunk_months: int):
    cfg = load_config()
    for k, v in cfg["strategies"].items():
        v["enabled"] = k in SETUPS
    cfg["account"].update(max_concurrent_positions=10**6, max_positions_per_strategy=10**6, max_trades_per_day=10**6,
                          max_daily_loss_r=10**6)
    strats = build_strategies(cfg)
    assert sorted(s.name for s in strats) == sorted(SETUPS), [s.name for s in strats]
    store = BarStore(ROOT / "data" / "cache_hist")
    syms = store.symbols()
    flat = t(cfg["session"]["flatten_by"])
    bt = Backtester(strats, cfg)
    months = [str(p) for p in pd.period_range("2024-10", "2026-10", freq="M") if str(p) not in LOCKED_MONTHS]
    chunks, cur = [], []
    for m in months:     # contiguous runs of open months, cut every chunk_months
        if cur and (pd.Period(m, "M") - pd.Period(cur[-1], "M")).n != 1 or len(cur) == chunk_months:
            chunks.append(cur); cur = []
        cur.append(m)
    chunks.append(cur)
    done = set()
    if OUT.exists():
        prev = pd.read_parquet(OUT)
        done = set(prev["chunk"].unique())
    out = [pd.read_parquet(OUT)] if OUT.exists() else []
    t0 = time.time()
    for ch in chunks:
        tag = f"{ch[0]}..{ch[-1]}"
        if tag in done:
            continue
        lo = pd.Period(ch[0], "M").start_time
        warm = (lo - pd.Timedelta(days=62)).strftime("%Y-%m-%d")
        hi = (pd.Period(ch[-1], "M").end_time + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        data = store.load_many(syms, start=warm, end=hi)
        hist = {s: SymbolHistory(s, df) for s, df in data.items() if len(df)}
        del data
        dates = sorted({d for h in hist.values() for d in h.by_day if str(d)[:7] in ch})
        cands = {s.name: [] for s in strats}
        for d in dates:
            ctxs = [c for h in hist.values() if (c := h.context(d)) is not None and universe_ok(c, cfg)]
            orv = [c.rvol().iloc[min(4, len(c.bars) - 1)] for c in ctxs]
            ctxs, _ = in_play_filter(ctxs, orv, cfg)
            rank_contexts(ctxs)
            for c in ctxs:
                costs = bt.costs_ext if is_extended(c, cfg) else bt.costs
                for s in strats:
                    if s.eligible(c):
                        for sig in s.signals(c):
                            tr = simulate(sig, c.bars, flat, costs)
                            if tr:
                                cands[s.name].append(tr)
        for name, cs in cands.items():
            tr = Backtester([], cfg).allocate(cs)
            if len(tr):
                tr["strategy"], tr["chunk"] = name, tag
                out.append(tr)
        del hist
        pd.concat(out, ignore_index=True).to_parquet(OUT, index=False)
        print(f"{tag}: {len(dates)} sessions, {sum(len(v) for v in cands.values())} trades ({time.time() - t0:.0f}s)", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-months", type=int, default=3)
    main(ap.parse_args().chunk_months)
