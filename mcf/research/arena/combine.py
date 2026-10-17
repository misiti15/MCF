"""Arena combiner: score an AND-combination of 2-3 indicator conditions, and write it out as a lab module.

    from mcf.research.arena import data as D
    from mcf.research.arena.combine import evaluate_combo, write_module
    A = D.load(names=["rsi2", "or_high_dist_atr", "vwap_atr"], split="all", workers=1)   # train + valid, ~25 s/month
    conds = [("rsi2", "<=", 10), ("vwap_atr", ">=", 0.2)]
    res = evaluate_combo(A, conds, side="long", geom="t05s1", window=(1100, 1400), n_lineage=500)
    write_module(conds, "long", "t05s1", (1100, 1400), "research/swarm1017/x/modules/AR-rsi2-vwap.py", name="AR-rsi2-vwap")

A condition is (indicator, op, value) with op in <=, <, >=, >, ==, between (value = (lo, hi), lo <= x < hi).
Trades: the FIRST bar per symbol-day in the window (bar close lo <= tod < hi; hi >= 1500 includes the 15:00 bar) where every condition holds; R is the
production R with tod entry costs and x3 extended-tier costs (arena.data.outcomes). Statistics are day-clustered
(gates.summary). Random baseline: per trade, the same-date same-minute universe mean (c_*); excess = r - control.
Gates reported (quality_pass needs all): n_total >= 200, exp > 0 on train AND valid, train day-t >= t_required(N)
with N = n_lineage, regime gate (gates.regime_split on train+valid), walk-forward share >= 0.6 (gates.walk_forward,
open months only), excess over random > 0 on train AND valid. Educational only - not financial advice.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .. import gates
from .indicators import INDICATORS

OPS = ("<=", "<", ">=", ">", "==", "between")
MIN_TRADES = 200
LOCKED_MONTHS = ("2024-11", "2024-12", "2025-01", "2025-02")


def cond_mask(ind, cond) -> np.ndarray:
    """Boolean mask of one condition over an indicator frame (any object with ind[name].to_numpy())."""
    name, op, val = cond
    if name not in INDICATORS:
        raise KeyError(name)
    if op not in OPS:
        raise ValueError(op)
    v = np.asarray(ind[name].to_numpy(), float)
    with np.errstate(invalid="ignore"):
        if op == "<=":
            return v <= val
        if op == "<":
            return v < val
        if op == ">=":
            return v >= val
        if op == ">":
            return v > val
        if op == "==":
            return v == val
        lo, hi = val
        return (v >= lo) & (v < hi)


def combo_mask(frame: pd.DataFrame, conds, window=(950, 1500)) -> np.ndarray:
    lo, hi = window
    tod = frame["tod"].to_numpy(float)
    m = (tod >= lo) & ((tod < hi) | ((hi >= 1500) & (tod <= 1500)))     # hi exclusive; hi >= 1500 keeps the 15:00 bar
    for c in conds:
        m &= cond_mask(frame, c)
    return m


def trades(A: pd.DataFrame, conds, side: str, geom: str, window=(950, 1500)) -> pd.DataFrame:
    """First qualifying bar per symbol-day. Columns date, symbol, tod, r, ctrl, x (= r - ctrl), split, regime."""
    o = f"{side}_{geom}"
    m = combo_mask(A, conds, window) & np.isfinite(A[f"r_{o}"].to_numpy(float)) & np.isfinite(A[f"c_{o}"].to_numpy(float))
    idx = gates.first_per_symbol_day(A["symbol"].to_numpy(), A["date"].to_numpy(), m)
    r = A[f"r_{o}"].to_numpy(float)[idx]
    c = A[f"c_{o}"].to_numpy(float)[idx]
    return pd.DataFrame({"date": A["date"].to_numpy()[idx], "symbol": A["symbol"].to_numpy()[idx],
                         "tod": A["tod"].to_numpy()[idx], "r": r, "ctrl": c, "x": r - c,
                         "split": A["split"].to_numpy()[idx] if "split" in A else "all",
                         "regime": A["regime"].to_numpy()[idx] if "regime" in A else None})


def _exc(t: pd.DataFrame) -> dict:
    s = gates.summary(t[["date"]].assign(r=t["x"].to_numpy()))
    return {"excess": s.get("exp_r"), "t_excess": s.get("t")}


def evaluate_combo(A: pd.DataFrame, conds, side: str, geom: str, window=(950, 1500), n_lineage: int = 1,
                   regimes: pd.DataFrame | None = None) -> dict:
    """Score one AND-combination on arena rows A (arena.data.load(split='all')). Returns per-split summaries,
    excess over random, regime split, walk-forward, the bar t_required(n_lineage) and the gate list."""
    t = trades(A, conds, side, geom, window)
    out = {"conds": [list(c) for c in conds], "side": side, "geom": geom, "window": list(window), "n_lineage": int(n_lineage),
           "t_required": gates.t_required(n_lineage), "live_supported": all(INDICATORS[c[0]].live for c in conds)}
    for sp in ("train", "valid"):
        ts = t[t["split"] == sp]
        out[sp] = {**gates.summary(ts[["date", "r"]]), **_exc(ts)} if len(ts) else {"n": 0}
    out["all"] = {**gates.summary(t[["date", "r"]]), **_exc(t)} if len(t) else {"n": 0}
    if regimes is None:
        from . import data as D

        regimes = D._lib().regimes()
    out["regime"] = gates.regime_split(t[["date", "r"]], regimes)
    wf = gates.walk_forward(t[["date", "r"]], exclude_months=LOCKED_MONTHS)
    out["walk_forward"] = {"share_positive": wf["share_positive"], "n_folds": wf["n_folds"], "trailing_on": wf["trailing_on"]}
    days = pd.Series(t["date"]).nunique() if len(t) else 0
    out["per_day"] = round(len(t) / max(1, A["date"].nunique()), 3)
    out["sessions_with_trade"] = int(days)
    tr, va = out["train"], out["valid"]
    gl = {
        "n_total>=200": out["all"].get("n", 0) >= MIN_TRADES,
        "exp_train>0": (tr.get("exp_r") or -1) > 0,
        "exp_valid>0": (va.get("exp_r") or -1) > 0,
        "t_train>=bar": (tr.get("t") or 0) >= out["t_required"],
        "regime": bool(out["regime"].get("pass")),
        "walk_forward>=0.6": (wf["share_positive"] or 0) >= gates.WF_MIN_SHARE,
        "beats_random_train": (tr.get("excess") or -1) > 0,
        "beats_random_valid": (va.get("excess") or -1) > 0,
    }
    out["gates"] = gl
    out["quality_pass"] = all(gl.values())
    return out


def _fmt(v):
    return repr(tuple(float(x) for x in v)) if isinstance(v, (tuple, list)) else repr(float(v))


def write_module(conds, side: str, geom: str, window, path, name: str, doc: str = "", allow_context: bool = False) -> Path:
    """Emit a lab module (SIDE, GEOM, LAYERS, mask(df)) for research/... -> config `type: lab` (LabStrategy).
    The mask recomputes the needed arena indicators from the frame it is given (history frame or live frame).
    Context (cross-asset/breadth) indicators are refused unless allow_context=True: the live LabStrategy frame has one
    symbol, so they would be NaN live and the setup would never fire."""
    names = sorted({c[0] for c in conds})
    ctx = [n for n in names if not INDICATORS[n].live]
    if ctx and not allow_context:
        raise ValueError(f"context indicators are research-only (not in the live frame): {ctx}")
    if side not in ("long", "short") or geom not in gates.GEOMK:
        raise ValueError((side, geom))
    lo, hi = int(window[0]), int(window[1])
    layers = [f"{c[0]} {c[1]} {c[2]!r} ({INDICATORS[c[0]].desc})" for c in conds]
    layers.append(f"window: bar close {lo} <= tod < {hi} ET (hi >= 1500 includes 15:00) (YAML window [{lo}, {min(hi, 1500)}])")
    cond_src = ",\n    ".join(f"({c[0]!r}, {c[1]!r}, {_fmt(c[2])})" for c in conds)
    note = "\n".join(f"    {ln}" for ln in (doc or "").splitlines())
    src = f'''"""{name} - arena combination (mcf/research/arena, swarm 2026-10-17).
{note}
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: {"uses research-only context indicators (NaN live -> never fires)" if ctx else "all indicators are computable from the live LabStrategy frame"}.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = {side!r}
GEOM = {geom!r}
WINDOW = ({lo}, {hi})
CONDS = [
    {cond_src},
]
LAYERS = {layers!r}


def mask(df) -> np.ndarray:
    x = compute(df, names={names!r}, context=False)
    tod = df["tod"].to_numpy(dtype=float)
    m = (tod >= WINDOW[0]) & ((tod < WINDOW[1]) | ((WINDOW[1] >= 1500) & (tod <= 1500)))
    with np.errstate(invalid="ignore"):
        for nm, op, v in CONDS:
            a = x[nm].to_numpy(dtype=float)
            if op == "<=":
                m &= a <= v
            elif op == "<":
                m &= a < v
            elif op == ">=":
                m &= a >= v
            elif op == ">":
                m &= a > v
            elif op == "==":
                m &= a == v
            else:
                m &= (a >= v[0]) & (a < v[1])
    return np.asarray(m, dtype=bool)
'''
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(src)
    return p
