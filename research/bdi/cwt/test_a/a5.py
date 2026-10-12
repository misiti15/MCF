"""A5 CWT19 Opening Print Fair-Value Fade: daily context from the 10-year official daily bars (open = the opening
auction print), exits on the 1-minute cache. Locked-block rows are dropped right after the load; returns that span the
dropped block are set to NaN before any rolling window. Educational only - not financial advice.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from engine import LOCKED, ROOT, SLIP_BPS, SLIP_PS, tod_cost_mult

DAILY = ROOT / "research" / "swarm1010" / "w3_daily" / "data" / "daily_2016.parquet"
KS, HS, HEDGE = (0.3, 0.5, 0.75), (5, 15, 30), ("none", "spy")
A5_CONFIGS = list(itertools.product(KS, HS, HEDGE))


def daily_context() -> pd.DataFrame:
    d = pd.read_parquet(DAILY, columns=["symbol", "date", "open", "high", "low", "close", "volume"])
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    d = d[(d["date"] >= "2024-01-01") & ((d["date"] < LOCKED[0]) | (d["date"] > LOCKED[1]))]   # drop locked at load
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = d.groupby("symbol")
    prev_dt = g["date"].shift(1)
    contiguous = (dt - pd.to_datetime(prev_dt)).dt.days <= 5
    d["pc"] = np.where(contiguous, g["close"].shift(1), np.nan)
    d["ret"] = d["close"] / d["pc"] - 1
    tr = np.maximum(d["high"] - d["low"], np.maximum((d["high"] - d["pc"]).abs(), (d["low"] - d["pc"]).abs()))
    tr = tr.where(np.isfinite(d["pc"]), d["high"] - d["low"])
    seg = (d["date"] > LOCKED[1]).astype(int)
    d["atr"] = tr.groupby([d["symbol"], seg]).transform(lambda x: x.rolling(14, min_periods=10).mean().shift(1))
    dv = d["close"] * d["volume"]
    d["adv20"] = dv.groupby([d["symbol"], seg]).transform(lambda x: x.rolling(20, min_periods=10).mean().shift(1))
    spy = d[d["symbol"] == "SPY"].set_index("date")
    d["spy_ret"] = d["date"].map(spy["ret"])
    d["spy_gap"] = d["date"].map(spy["open"] / spy["pc"] - 1)

    def beta(x):
        r, m = x["ret"], x["spy_ret"]
        cov = (r * m).rolling(60, min_periods=40).mean() - r.rolling(60, min_periods=40).mean() * m.rolling(60, min_periods=40).mean()
        var = (m * m).rolling(60, min_periods=40).mean() - m.rolling(60, min_periods=40).mean() ** 2
        return (cov / var).shift(1)

    d["beta60"] = d.groupby([d["symbol"], seg], group_keys=False)[["ret", "spy_ret"]].apply(beta)
    d["rank"] = d.groupby("date")["adv20"].rank(ascending=False, method="first")
    d = d[d["date"] >= "2024-10-01"]
    d["top300"] = d["rank"] <= 300
    d["fair"] = d["pc"] * (1 + d["beta60"] * d["spy_gap"])
    d["disl"] = (d["open"] - d["fair"]) / d["atr"]
    return d[["symbol", "date", "open", "high", "pc", "atr", "beta60", "top300", "disl"]]


def a5_symbol(s, ctx: pd.DataFrame, spy_s, spy_ctx: pd.DataFrame, rows, ctl):
    """rows: (config index, day index, side, net r, gross r). ctl: dict (date, H) -> list of unconditional long open->H returns in R
    (the same-time control: every top-300 name that day, before costs)."""
    c = ctx[ctx["top300"]].set_index("date")
    if c.empty:
        return
    pos = {dt: i for i, dt in enumerate(s.dates)}
    spos = {dt: i for i, dt in enumerate(spy_s.dates)}
    for dt, x in c.iterrows():
        d = pos.get(dt)
        j = spos.get(dt)
        if d is None or j is None or not np.isfinite(x["atr"]) or x["atr"] <= 0:
            continue
        h1 = np.nanmax(s.H[d])
        if not np.isfinite(h1) or h1 <= 0:
            continue
        f = x["high"] / h1                                   # adjusted daily / raw 1-minute scale
        o = x["open"] / f
        R = 0.25 * x["atr"] / f
        sx = spy_ctx.loc[dt] if dt in spy_ctx.index else None
        if sx is None:
            continue
        fs = sx["high"] / np.nanmax(spy_s.H[j])
        so = sx["open"] / fs
        for H in HS:
            px = s.C[d, H - 1]
            if np.isfinite(px):
                ctl.setdefault((dt, H), []).append((px - o) / R)
        dis = x["disl"]
        if not np.isfinite(dis):
            continue
        side = -1 if dis > 0 else 1
        beta = x["beta60"] if np.isfinite(x["beta60"]) else 1.0
        for ci, (k, H, hedge) in enumerate(A5_CONFIGS):
            if abs(dis) < k:
                continue
            px = s.C[d, H - 1]
            if not np.isfinite(px):
                continue
            xm = float(tod_cost_mult(np.array([(570 + H) // 60 * 100 + (570 + H) % 60]))[0])
            cost = (SLIP_PS + o * SLIP_BPS) * 2.0 + (SLIP_PS + px * SLIP_BPS) * xm
            pnl = side * (px - o)
            if hedge == "spy":
                spx = spy_s.C[j, H - 1]
                q = beta * o / so
                pnl += -side * q * (spx - so)
                cost += q * ((SLIP_PS + so * SLIP_BPS) * 2.0 + (SLIP_PS + spx * SLIP_BPS) * xm)
            rows.append((ci, d, side, float((pnl - cost) / R), float(pnl / R)))
