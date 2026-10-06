"""Exit-rule harness: re-simulate the live setups' collected entries under different exit rules.

Same fills and costs as the backtester (mcf.backtest.engine.simulate + Costs): conservative, slippage in.
Splits by date (RESEARCH_RULES.md): train < 2026-08-26, valid 2026-08-26..2026-09-15, test >= 2026-09-16
(locked: the lead scores finalists once). Educational only — not financial advice.

    from research.exits.harness import load, run
    sigs = load()                                  # all collected entries
    res = run(sigs, "orb20_a", {"time_stop_min": 45, "time_stop_min_r": 0.3}, split="train")
    -> {"n", "win_rate", "exp_r", "exp_r_se", "pf", "green_days", "avg_minutes", "exit_reasons", "exp_r_ex_best_day"}
Variant keys: stop_mult (scale the stop distance), target_r (None = no target; else target at entry + target_r R),
be_at_r, trail_r, trail_after_r, time_stop_min, time_stop_min_r, exit_by ("HH:MM").
"""
from __future__ import annotations

import os
import pickle
from dataclasses import fields
from functools import lru_cache

import numpy as np
import pandas as pd

from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.base import Signal, t

SPLITS = {"train": ("0000", "2026-08-25"), "valid": ("2026-08-26", "2026-09-15"), "test": ("2026-09-16", "9999")}
_cfg = load_config()
_store = BarStore(_cfg["data"]["cache_dir"])
_costs = Costs.from_cfg(_cfg["costs"])
_flat = t(_cfg["session"]["flatten_by"])
_SIG_FIELDS = {f.name for f in fields(Signal)}


def load(path: str = "research/exits/data/signals.pkl") -> list[dict]:
    return pickle.load(open(path, "rb"))["signals"]


@lru_cache(maxsize=2048)
def _sym(symbol: str) -> dict:
    df = _store.load(symbol)
    return {str(d): g for d, g in df.groupby(df.index.date)}


def _day(symbol: str, date: str) -> pd.DataFrame:
    return _sym(symbol).get(date, pd.DataFrame())


def run(sigs: list[dict], setup: str, variant: dict | None = None, split: str = "train") -> dict:
    if split == "test" and not os.environ.get("MCF_EXITS_ALLOW_TEST"):
        raise PermissionError("the test split is locked until final verification")
    lo, hi = SPLITS[split]
    v = dict(variant or {})
    rows = []
    for s in sigs:
        if s["sig"]["strategy"] != setup or not (lo <= s["date"] <= hi):
            continue
        d = {k: val for k, val in s["sig"].items() if k in _SIG_FIELDS}
        bars = _day(s["symbol"], s["date"])
        if bars.empty or d["bar_index"] >= len(bars):
            continue
        ref = d["entry_price"] if d.get("entry_price") is not None else float(bars["close"].iloc[d["bar_index"]])
        risk0 = abs(ref - d["stop"])
        if "stop_mult" in v:
            d["stop"] = ref - np.sign(ref - d["stop"]) * risk0 * v["stop_mult"]
            risk0 = abs(ref - d["stop"])
        if "target_r" in v:
            d["target"] = None if v["target_r"] is None else ref + d["side"] * v["target_r"] * risk0
        for k in ("be_at_r", "trail_r", "trail_after_r", "time_stop_min", "time_stop_min_r"):
            if k in v:
                d[k] = v[k]
        if "exit_by" in v:
            d["exit_by"] = t(v["exit_by"])
        tr = simulate(Signal(**d), bars, _flat, _costs)
        if tr is None:
            continue
        mins = (tr.exit_time - tr.entry_time).total_seconds() / 60
        rows.append((s["date"], tr.r_multiple, tr.exit_reason, mins))
    if not rows:
        return {"n": 0}
    df = pd.DataFrame(rows, columns=["date", "r", "reason", "min"])
    r = df["r"].to_numpy()
    daily = df.groupby("date")["r"].sum()
    gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
    return {"n": int(len(r)), "win_rate": round(float((r > 0).mean()), 4), "exp_r": round(float(r.mean()), 4),
            "exp_r_se": round(float(r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 1 else 0.0, 4),
            "pf": round(float(gw / gl), 3) if gl > 0 else None, "green_days": round(float((daily > 0).mean()), 3),
            "exp_r_ex_best_day": round(float((daily.sum() - daily.max()) / len(r)), 4),
            "avg_minutes": round(float(df["min"].mean()), 1),
            "exit_reasons": df["reason"].value_counts().to_dict()}
