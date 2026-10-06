"""Screening backtest for the research setups (and the setups already enabled) on SIP 1-minute bars.

Each setup is simulated on its own book (no cross-setup symbol blocking) with MCF's conservative fills
(next-bar-open market entries, stop entries at max(open, trigger), stop-first inside a bar, gaps through
stops at the open, slippage both sides; extended-tier names at 3x slippage). Entries before 09:50 are
reported separately because live trading does not take them.

Paper screen (a setup may paper-trade): >= 30 trades, expectancy > 0R after costs, profit factor > 1,
and still positive without its single best day. This is NOT the promotion gate (that needs 200+ trades
over 6+ months out of sample) — it only decides what is worth collecting live paper evidence on.

Usage: python research/setup_screen.py [start] [end]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd

from mcf.analytics.metrics import summarize
from mcf.backtest.engine import Backtester, Costs, SymbolHistory, in_play_filter, is_extended, rank_contexts, simulate, universe_ok
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.base import t
from mcf.strategies.setups import build_strategies

start, end = (sys.argv[1] if len(sys.argv) > 1 else "2026-07-08"), (sys.argv[2] if len(sys.argv) > 2 else "2026-10-05")
cfg = load_config()
for k, v in cfg["strategies"].items():
    v["enabled"] = True
cfg["account"].update(max_concurrent_positions=10**6, max_positions_per_strategy=10**6, max_trades_per_day=10**6,
                      max_daily_loss_r=10**6)
strats = build_strategies(cfg)
store = BarStore(cfg["data"]["cache_dir"])
t0 = time.time()
data = store.load_many(store.symbols())
hist = {s: SymbolHistory(s, df) for s, df in data.items() if len(df)}
print(f"{len(hist)} symbols loaded ({time.time() - t0:.0f}s)", flush=True)
dates = sorted({d for h in hist.values() for d in h.by_day if str(d) >= start and str(d) <= end})
bt = Backtester(strats, cfg)
flat = t(cfg["session"]["flatten_by"])
cands: dict[str, list] = {s.name: [] for s in strats}
for n, d in enumerate(dates):
    ctxs = [c for h in hist.values() if (c := h.context(d)) is not None and universe_ok(c, cfg)]
    orv = [c.rvol().iloc[min(4, len(c.bars) - 1)] for c in ctxs]
    ctxs, _ = in_play_filter(ctxs, orv, cfg)
    rank_contexts(ctxs)
    for c in ctxs:
        costs = bt.costs_ext if is_extended(c, cfg) else bt.costs
        for s in strats:
            if not s.eligible(c):
                continue
            for sig in s.signals(c):
                tr = simulate(sig, c.bars, flat, costs)
                if tr:
                    cands[s.name].append(tr)
    if n % 10 == 0:
        print(f"{d}: {sum(len(v) for v in cands.values())} candidate trades ({time.time() - t0:.0f}s)", flush=True)

rows, all_trades = [], []
for name, cs in cands.items():
    tr = Backtester([], cfg).allocate(cs)
    if tr.empty:
        rows.append({"setup": name, "trades": 0})
        continue
    tr["strategy"] = name
    all_trades.append(tr)
    et = pd.to_datetime(tr.entry_time)
    early = tr[et.dt.time < t("09:50")]
    live = tr[et.dt.time >= t("09:50")]
    s = summarize(live) if len(live) else {"trades": 0}
    daily = live.groupby("date").r_multiple.sum() if len(live) else pd.Series(dtype=float)
    ex_best = (daily.sum() - daily.max()) / max(1, len(live)) if len(daily) else np.nan
    months = live.groupby(pd.to_datetime(live.date).dt.strftime("%Y-%m")).r_multiple.mean().round(3).to_dict() if len(live) else {}
    screen = bool(s.get("trades", 0) >= 30 and s.get("expectancy_r", 0) > 0 and s.get("profit_factor", 0) > 1 and ex_best > 0)
    rows.append({"setup": name, "trades": s.get("trades", 0), "per_day": round(s.get("trades", 0) / max(1, len(dates)), 2),
                 "success": round(s.get("success_rate", np.nan), 3), "win_rate": round(s.get("win_rate", np.nan), 3),
                 "exp_r": round(s.get("expectancy_r", np.nan), 3), "pf": round(s.get("profit_factor", np.nan), 2),
                 "exp_r_ex_best_day": round(float(ex_best), 3) if np.isfinite(ex_best) else None,
                 "green_days": round(s.get("green_day_rate", np.nan), 3), "by_month_exp_r": months,
                 "pre_0950_trades": int(len(early)), "pre_0950_exp_r": round(float(early.r_multiple.mean()), 3) if len(early) else None,
                 "paper_screen": screen})
res = pd.DataFrame(rows).sort_values("exp_r", ascending=False)
pd.set_option("display.width", 250)
print(res.drop(columns=["by_month_exp_r"]).to_string(index=False))
res.to_json("research/setup_screen.json", orient="records", indent=1)
if all_trades:
    pd.concat(all_trades).to_csv("research/setup_screen_trades.csv", index=False)
print(f"{len(dates)} sessions {dates[0]}..{dates[-1]}, {time.time() - t0:.0f}s")
