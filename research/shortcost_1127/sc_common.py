"""SHORTCOST-1127 shared helpers: pre-trade LIVE-L cost estimate c_ex, the 5 pre-registered rules, LIVE-L cost of a
realised exit, day-clustered t. Educational only - not financial advice."""
import json
import math
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = json.load(open(os.path.join(HERE, "..", "primshorts_1126", "cells_live.json")))
PB = [5, 10, 20, 50, 100, 1e9]; PBL = ["5-10", "10-20", "20-50", "50-100", "100+"]
KW = {"stop": 0.357, "market": 0.283, "target": 0.360}
LOCK = ("2024-11-01", "2025-02-28")
RULES = ["R1", "R2", "R3", "R4", "R5"]


def no_locked(d):
    d = pd.Series(np.asarray(d)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def pbucket(p):
    return pd.cut(np.asarray(p, float), PB, labels=PBL, right=False).astype(str)


def _ab(pb, kind):
    return np.array([CELLS.get(f"{a}|{k}", CELLS[f"*|{k}"])[:2] for a, k in zip(pb, kind)])


def cost_kind(price, risk, kind):
    """LIVE-L cost in R for a realised exit kind (stop/market/target)."""
    price = np.asarray(price, float); w = np.asarray(risk, float) / price * 1e4
    ab = _ab(pbucket(price), np.asarray(kind).astype(str))
    return ab[:, 0] / w + ab[:, 1]


def c_ex(price, risk):
    """pre-trade LIVE-L cost estimate (fixed exit-kind weights)."""
    price = np.asarray(price, float); n = len(price); out = np.zeros(n)
    for k, wt in KW.items():
        out += wt * cost_kind(price, risk, np.full(n, k))
    return out


def rule_skip(rule, side, price, risk, cex, spread=None):
    side = np.asarray(side); price = np.asarray(price, float); w = np.asarray(risk, float) / price * 1e4
    sh = side < 0
    if rule == "R1":
        return sh & (cex >= 0.12)
    if rule == "R2":
        return sh & (cex >= 0.10)
    if rule == "R3":
        return cex >= 0.12
    if rule == "R4":
        return sh & (price >= 100) & (w < 100)
    if rule == "R5":
        if spread is None:
            return np.zeros(len(side), bool)
        sp = np.asarray(spread, float)
        return sh & (sp > 15)   # NaN spread -> kept
    raise ValueError(rule)


def clustered_t(r, d):
    r = pd.Series(np.asarray(r, float)); d = pd.Series(np.asarray(d))
    if len(r) < 3:
        return float("nan")
    m = r.mean(); e = (r - m).groupby(d.values).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(r)
    return float(m / se) if se > 0 else float("nan")


def day_t(x):
    x = pd.Series(x, dtype=float)
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std() > 0 else float("nan")


def bestday(r, d):
    s = pd.Series(np.asarray(r, float)).groupby(np.asarray(d)).sum()
    if not len(s):
        return dict(wo=float("nan"), share=float("nan"), day=None)
    b = s.idxmax(); tot = s.sum(); m = np.asarray(d) != b
    rr = np.asarray(r, float)
    return dict(wo=float(rr[m].mean()) if m.any() else float("nan"),
                share=float(s.max() / tot) if tot > 0 else float("nan"), day=str(b))
