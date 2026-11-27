"""STOPFLOOR-1127 shared scoring helpers: R per lot under LIVE-L and LR8 for a given risk/exit. Educational only - not financial advice."""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE + "/../..")
from mcf.research.gates import tod_cost_mult  # noqa: E402
CELLS = json.load(open(HERE + "/../primshorts_1126/cells_live.json"))
LOCK = ("2024-11-01", "2025-02-28")
PB = [5, 10, 20, 50, 100, 1e9]; PBL = ["5-10", "10-20", "20-50", "50-100", "100+"]
KIND = {0: "market", 1: "stop", 2: "target"}
FAM = {"L3-gap-slope-fromopen-FD": "gapdown-short", "RW3-gapdn-rsi5pop-flowsell-short-FD": "gapdown-short",
       "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "gapdown-short", "NM-ETF-late-dip-di-long": "etf-long"}
SHORT = {"L3-gap-slope-fromopen-FD": "L3", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
         "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5", "NM-ETF-late-dip-di-long": "NM-ETF"}


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def liveL_cost(price, risk, kind):
    price = np.asarray(price, float); risk = np.asarray(risk, float); kind = np.asarray(kind)
    pb = pd.cut(price, PB, labels=PBL, right=False).astype(str)
    a = np.empty(len(price)); b = np.empty(len(price))
    for p in set(pb):
        for k in (0, 1, 2):
            m = (pb == p) & (kind == k)
            if m.any():
                ab = CELLS.get(f"{p}|{KIND[k]}", CELLS[f"*|{KIND[k]}"])
                a[m], b[m] = ab[0], ab[1]
    return a / (risk / price * 1e4) + b


def lr8_cost(entry, px, risk, kind, side, tod, gap):
    gap = np.asarray(gap, float)
    tier = np.where((np.abs(gap) >= 0.20) | (np.asarray(entry) < 5), 3.0, 1.0)
    ec = (0.01 + entry * 1e-4) * tod_cost_mult(np.asarray(tod))
    xc = np.where(kind == 2, 0.0, 0.01 + px * 1e-4) + np.where(kind == 1, 0.02, 0.0)
    br = np.where(side < 0, 1.2e-4 * entry, 0.0)
    return (tier * (ec + xc) + br) / risk


def lot_R(entry, px, risk, kind, side, tod, gap):
    g = side * (px - entry) / risk
    return g, g - liveL_cost(entry, risk, kind), g - lr8_cost(entry, px, risk, kind, side, tod, gap)


def dstats(d, x, all_days):
    """day sums of x (indexed by date d) over all_days (missing = 0): total, mean/day, clustered t, best-day share."""
    g = pd.Series(np.asarray(x, float)).groupby(np.asarray(d)).sum().reindex(all_days, fill_value=0.0)
    n = len(g); m = g.mean(); se = g.std(ddof=1) / np.sqrt(n)
    tot = g.sum(); best = g.max()
    return dict(days=n, tot=round(float(tot), 2), per_day=round(float(m), 4), t=round(float(m / se), 2) if se > 0 else 0.0,
                best_share=round(float(best / tot), 3) if tot > 0 else None, wo_best_per_day=round(float((tot - best) / (n - 1)), 4))
