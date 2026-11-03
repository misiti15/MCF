"""BETA1 (owner 2026-11-03): "Avg R ex-market" - a setup's average R with the market's move taken out.

Method (per setup, all of its live trades):
  x = SPY's % move over the trade's own holding window (SPY 1-minute close at the exit minute / at the entry minute - 1,
      x 100; the same lookup as mcf.report.eod.spy_adjust), y = the trade's R after costs.
  Ordinary least squares y = a + b * x. "Avg R ex-market" = a = mean(y) - b * mean(x): the average R the setup would
  have made on trades whose window saw a flat SPY. b ("beta") is R per 1% SPY move (negative for most shorts).
  Needs >= MIN_N trades with some spread in x; otherwise None (shown as "-").
The fit is kept as exact sums (n, sum x, sum y, sum x^2, sum x*y) so one setup's records from several accounts merge
exactly (dashboard, daily post). Trades without SPY data for their window are left out of the fit only.
Report only: it never changes which trades are taken. Educational only - not financial advice.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_N = 5
KEYS = ("mkt_n", "mkt_x_sum", "mkt_y_sum", "mkt_xx_sum", "mkt_xy_sum")


def spy_moves(trades: pd.DataFrame, spy: pd.DataFrame | None) -> pd.Series:
    """SPY % move over each trade's entry->exit window (NaN when SPY bars do not cover it)."""
    out = pd.Series(np.nan, index=trades.index, dtype=float)
    if spy is None or not len(spy) or not len(trades) or "entry_time" not in trades or "exit_time" not in trades:
        return out
    c = spy["close"].sort_index()
    idx = c.index
    lo, hi = idx[0], idx[-1] + pd.Timedelta(minutes=1)

    def px(ts):
        t = pd.Timestamp(ts)
        if pd.isna(t):
            return np.nan
        if t.tzinfo is None and idx.tz is not None:
            t = t.tz_localize(idx.tz)
        t = t.floor("1min")
        if t < lo or t > hi:
            return np.nan
        i = idx.searchsorted(t, side="right") - 1
        if i < 0 or idx[i].date() != t.date():      # no SPY bar yet that session
            return np.nan
        return float(c.iloc[i])

    for k, en, ex in zip(trades.index, trades["entry_time"], trades["exit_time"]):
        a, b = px(en), px(ex)
        if np.isfinite(a) and np.isfinite(b) and a > 0:
            out.at[k] = (b / a - 1) * 100
    return out


def sums(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    return {"mkt_n": int(len(x)), "mkt_x_sum": round(float(x.sum()), 6), "mkt_y_sum": round(float(y.sum()), 6),
            "mkt_xx_sum": round(float((x * x).sum()), 6), "mkt_xy_sum": round(float((x * y).sum()), 6)}


def merge(parts) -> dict:
    out = {k: 0.0 for k in KEYS}
    for p in parts:
        if p and p.get("mkt_n"):
            for k in KEYS:
                out[k] += float(p.get(k) or 0)
    out["mkt_n"] = int(out["mkt_n"])
    return out


def fit(s: dict) -> dict:
    """{'exmkt_r': a, 'beta': b} from the sums (None when under MIN_N trades or no spread in SPY's move)."""
    n = int(s.get("mkt_n") or 0)
    if n < MIN_N:
        return {"exmkt_r": None, "beta": None}
    sx, sy, sxx, sxy = (float(s.get(k) or 0) for k in KEYS[1:])
    var = sxx - sx * sx / n
    if var <= 1e-12 * max(1.0, sxx):
        return {"exmkt_r": None, "beta": None}
    b = (sxy - sx * sy / n) / var
    a = sy / n - b * sx / n
    return {"exmkt_r": round(a, 3), "beta": round(b, 3)}


def per_setup(trades: pd.DataFrame, spy: pd.DataFrame | None, col: str = "strategy") -> dict:
    """setup -> {sums..., exmkt_r, beta} for every setup in `trades` (uses a 'spy_move' column when present)."""
    if trades is None or not len(trades):
        return {}
    x = trades["spy_move"] if "spy_move" in trades else spy_moves(trades, spy)
    out = {}
    for s, g in trades.groupby(col):
        sm = sums(x.loc[g.index], g["r_multiple"].astype(float))
        out[str(s)] = {**sm, **fit(sm)}
    return out
