"""Test the concrete fixes the 10-07 autopsy suggested, on train/valid ONLY (sessions 2026-07-15..2026-09-15).

Entries: the live setups' collected pre-allocation entries (research/exits/data/signals.pkl, same production
engine), re-simulated with mcf.backtest.engine.simulate + Costs (costs in, next-bar fills, stop-first, gap
fills at the open). Bars are read with end='2026-09-16' so the locked Sep 16 - Oct 5 holdout is never read.

Money, not R: position size = min(0.25% of $100k / per-share risk, slot $2,000 / price), as the allocator
does; because the slot cap binds for most names, a tighter stop does NOT buy more shares (the R-unit trap in
EXIT_STUDY.md), so every variant is scored in dollars and in the ORIGINAL R units.

Families (all counted):
  maxloss_<x>   : stop capped at x% from the fill (owner's "-1.5% max loss" idea), x in 1,1.5,2,2.5,3
                  applied per setup and to all four non-index setups at once
  orbw_pct_<x>  : orb20_a filter, skip when the 20-minute opening range is wider than x% of price
  orbw_atr_<x>  : orb20_a filter, skip when the opening range is wider than x daily ATRs
  exit_<...>    : give-back exits on each setup (rework of the EXIT_STUDY lineage, already 489 configs)
Educational only - not financial advice.
"""
import json
import pickle
import sys
from dataclasses import fields

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.data.bars import rth
from mcf.data.store import BarStore
from mcf.strategies.base import Signal, t

OUT = "research/oct7/autopsy/"
LO, TRAIN_END, HI, END = "2026-07-15", "2026-08-25", "2026-09-15", "2026-09-16"
cfg = load_config()
store = BarStore(cfg["data"]["cache_dir"])
costs = Costs.from_cfg(cfg["costs"])
FLAT = t(cfg["session"]["flatten_by"])
FIELDS = {f.name for f in fields(Signal)}
RISK_D, SLOT = 250.0, 2000.0
SETUPS = ["orb20_a", "heat_fade_short", "heat_fade_long", "exhaustion_short"]

sigs = [s for s in pickle.load(open("research/exits/data/signals.pkl", "rb"))["signals"]
        if LO <= s["date"] <= HI and s["sig"]["strategy"] in SETUPS]
by_sym = {}
for s in sigs:
    by_sym.setdefault(s["symbol"], []).append(s)

VARIANTS = {"base": {}}
for x in (1.0, 1.5, 2.0, 2.5, 3.0):
    VARIANTS[f"maxloss_{x}"] = {"max_loss_pct": x}
for k, v in {"be0.5": {"be_at_r": 0.5}, "be0.75": {"be_at_r": 0.75},
             "trail0.5_after0.5": {"trail_r": 0.5, "trail_after_r": 0.5}, "tp0.5": {"target_r": 0.5}}.items():
    VARIANTS[f"exit_{k}"] = v


def run_one(s, bars, v):
    d = {k: val for k, val in s["sig"].items() if k in FIELDS}
    ref = d["entry_price"] if d.get("entry_price") is not None else float(bars["close"].iloc[d["bar_index"]])
    side = d["side"]
    risk0 = abs(ref - d["stop"])
    if "target_r" in v:
        d["target"] = ref + side * v["target_r"] * risk0
    for k in ("be_at_r", "trail_r", "trail_after_r"):
        if k in v:
            d[k] = v[k]
    if "max_loss_pct" in v:
        cap = ref * (1 - side * v["max_loss_pct"] / 100)
        d["stop"] = max(d["stop"], cap) if side == 1 else min(d["stop"], cap)
    tr = simulate(Signal(**d), bars, FLAT, costs)
    if tr is None:
        return None
    per_share = abs(tr.entry - tr.stop)
    shares = int(min(RISK_D / per_share, SLOT / tr.entry)) if per_share > 0 else 0
    if shares < 1:
        return None
    pnl = side * (tr.exit - tr.entry) * shares     # costs already in the fills
    return dict(entry=tr.entry, exit=tr.exit, reason=tr.exit_reason, shares=shares, pnl=pnl,
                notional=shares * tr.entry, r_live=tr.r_multiple, mae_r=tr.mae_r, mfe_r=tr.mfe_r,
                entry_time=tr.entry_time, exit_time=tr.exit_time)


rows = []
for n, (sym, ss) in enumerate(sorted(by_sym.items())):
    df = store.load(sym, end=END)
    if df.empty:
        continue
    days = {str(d): g for d, g in df.groupby(df.index.date)}
    for s in ss:
        bars = days.get(s["date"])
        if bars is None or s["sig"]["bar_index"] >= len(bars):
            continue
        meta = s["sig"].get("meta") or {}
        base_r0 = None
        for name, v in VARIANTS.items():
            r = run_one(s, bars, v)
            if r is None:
                continue
            if name == "base":
                # path MAE in % for the recovery table: worst adverse % from the fill while held
                p = bars[(bars.index > r["entry_time"]) & (bars.index <= r["exit_time"])]
                adv = (p["low"].min() if s["sig"]["side"] == 1 else p["high"].max()) if len(p) else r["entry"]
                r["mae_pct"] = -abs(min(0.0, s["sig"]["side"] * (adv - r["entry"]) / r["entry"] * 100))
                r["risk_pct"] = abs(r["entry"] - s["sig"]["stop"]) / r["entry"] * 100
            rows.append(dict(variant=name, setup=s["sig"]["strategy"], symbol=sym, date=s["date"],
                             atr=s["atr"], or_width=meta.get("or_width"), **r))
    if n % 100 == 0:
        print(n, len(by_sym), flush=True)

R = pd.DataFrame(rows)
R["split"] = np.where(R["date"] <= TRAIN_END, "train", "valid")
R.drop(columns=["entry_time", "exit_time"]).to_parquet(OUT + "fix_trades.parquet")
print("rows", len(R))
