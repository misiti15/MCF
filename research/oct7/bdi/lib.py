"""Shared helpers for the BDI 2026-10-07 studies. Educational only - not financial advice.

All trades are simulated with the production fill model mcf.backtest.engine.simulate and production costs
(config/default.yaml: 1 bps + 1c/share per side, +2c on stop exits, 3c/share on extended-tier names; next-bar
entries, stop-first inside a bar, gaps through stops fill at the open).

R unit: every result is in R0 = r_atr_frac x prior-day daily ATR at the ORIGINAL signal (0.25 x ATR), never in
a variant's own (possibly tighter) stop distance. Production sizing is notional-bound (slot ~$2,000 vs a 0.25%
risk budget that would need ~$30k), so every trade has the same dollar size and P&L is proportional to the
price move; R0 is the honest common unit (a 0.5R stop loses 0.5 R0, not 1 R).
"""
from __future__ import annotations

import pickle
from datetime import time

import numpy as np
import pandas as pd

from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.strategies.base import Signal

CFG = load_config()
COSTS = Costs.from_cfg(CFG["costs"])
COSTS_EXT = Costs.from_cfg({**CFG["costs"], "slippage_per_share": CFG["costs"]["extended_slippage_per_share"]})
FLAT = time(15, 55)
TRAIN_END, VALID_END = "2026-08-25", "2026-09-15"
D = "research/oct7/bdi/data/"


def split_of(d: str) -> str:
    return "train" if d <= TRAIN_END else ("valid" if d <= VALID_END else "LOCKED")


def load():
    hits, bars, funnel = [], {}, []
    for p in (0, 1):
        x = pickle.load(open(f"{D}hits_{p}.pkl", "rb"))
        hits += x["hits"]
        bars.update(x["bars"])
        funnel += x["funnel"]
    H = pd.DataFrame(hits)
    assert H.date.max() <= VALID_END, "locked dates present"
    H["split"] = H.date.map(split_of)
    return H, bars, pd.DataFrame(funnel).sort_values("date")


def costs_for(ext: bool) -> Costs:
    return COSTS_EXT if ext else COSTS


def run(sig: Signal, b: pd.DataFrame, ext: bool):
    """engine.simulate + the exit bar index (k) of the trade."""
    tr = simulate(sig, b, FLAT, costs_for(ext))
    if tr is None:
        return None, None
    if tr.exit_reason.endswith("time"):
        k = int(b.index.searchsorted(tr.exit_time))
    else:
        k = int(b.index.searchsorted(tr.exit_time - pd.Timedelta(minutes=1)))
    return tr, k


def r0(tr, R0: float) -> float:
    return tr.side * (tr.exit - tr.entry) / R0


def vwap(b: pd.DataFrame) -> np.ndarray:
    tp = (b["high"] + b["low"] + b["close"]).to_numpy() / 3
    v = b["volume"].to_numpy(dtype=float)
    cv = np.cumsum(v)
    return np.where(cv > 0, np.cumsum(tp * v) / np.where(cv > 0, cv, 1), tp)


def five(b: pd.DataFrame):
    """5-minute bars aligned to the session, with the 1-minute index of each bar's LAST minute."""
    g = np.arange(len(b)) // 5
    o = b["open"].to_numpy()[::5]
    h = pd.Series(b["high"].to_numpy()).groupby(g).max().to_numpy()
    l = pd.Series(b["low"].to_numpy()).groupby(g).min().to_numpy()
    c = pd.Series(b["close"].to_numpy()).groupby(g).last().to_numpy()
    last = np.minimum(np.arange(len(o)) * 5 + 4, len(b) - 1)
    return o, h, l, c, last


def day_t(per_day: pd.Series) -> float:
    per_day = per_day.dropna()
    if len(per_day) < 3 or per_day.std(ddof=1) == 0:
        return float("nan")
    return float(per_day.mean() / (per_day.std(ddof=1) / np.sqrt(len(per_day))))


def stats(T: pd.DataFrame, col: str = "r", nsig: int | None = None) -> dict:
    """T: one row per trade leg with date and col (R0). nsig: number of base signals (for R per signal)."""
    if T.empty:
        return dict(n=0)
    d = T.groupby("date")[col].sum()
    return dict(n=len(T), days=len(d), win=round(float((T[col] > 0).mean()), 3), exp=round(float(T[col].mean()), 4),
                tot=round(float(T[col].sum()), 2), t_day=round(day_t(d), 2),
                ex_best=round(float(d.sum() - d.max()), 2), best_day=str(d.idxmax()),
                per_sig=None if not nsig else round(float(T[col].sum() / nsig), 4))


def paired(Tv: pd.DataFrame, Tb: pd.DataFrame, dates) -> dict:
    """Day-clustered paired difference variant - base over the given session dates (0 on no-trade days)."""
    a = Tv.groupby("date")["r"].sum().reindex(dates, fill_value=0.0)
    b = Tb.groupby("date")["r"].sum().reindex(dates, fill_value=0.0)
    diff = a - b
    return dict(diff_tot=round(float(diff.sum()), 2), diff_t=round(day_t(diff), 2),
                diff_ex_best=round(float(diff.sum() - diff.max()), 2), diff_best_day=str(diff.idxmax()))
