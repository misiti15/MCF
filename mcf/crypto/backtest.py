"""24/7 crypto backtest harness (engine label "E5 crypto", rule 31: a new asset class needs its own engine; it
reuses the equity engine's fill conventions and R accounting).

Fills (conservative, as in mcf/backtest/engine.py):
  * a signal is decided on bar i's close; entry at bar i+1's open
  * stop = entry - side * stop_atr * ATR(i), target = entry + side * target_atr * ATR(i) (None = no target)
  * stop first when stop and target are both inside a bar; a gap through the stop fills at the bar's open
  * time stop: exit at the close of the hold_bars-th bar after entry (counting the entry bar)
  * one open trade per pair; signals while a trade is open are ignored
  * costs (mcf/crypto/costs.py) are charged per trade in R using the trade's own stop distance
Sides: Alpaca crypto is LONG ONLY (no shorting, no margin). side=-1 is computed for research only ("if available
elsewhere") and every short result is flagged `short_research_only`.
Sessions: trades are bucketed by UTC day (`day`) for day-clustered stats; `session_mask` builds configurable
windows (US / EU / Asia / weekend) for entries.

Educational only — not financial advice.
"""
from __future__ import annotations

from dataclasses import dataclass

import numba
import numpy as np
import pandas as pd

from .costs import CostModel

WINDOWS = {                       # UTC minute-of-day [start, end)
    "any": (0, 1440),
    "asia_open": (0, 120),        # Tokyo/HK morning
    "asia": (0, 480),
    "eu_open": (420, 540),
    "eu": (420, 930),
    "us_open": (810, 900),        # 13:30-15:00 UTC (US cash open; 14:30-16:00 in winter is not modelled)
    "us": (810, 1200),
    "us_close": (1140, 1260),
}


def session_mask(index: pd.DatetimeIndex, window: str = "any", days: str = "all") -> np.ndarray:
    a, z = WINDOWS[window]
    m = index.hour * 60 + index.minute
    ok = (m >= a) & (m < z)
    dow = index.dayofweek
    if days == "weekday":
        ok &= dow < 5
    elif days == "weekend":
        ok &= dow >= 5
    return np.asarray(ok)


@dataclass(frozen=True)
class Exit:
    stop_atr: float = 2.0
    target_atr: float | None = 3.0
    hold_bars: int = 12


@numba.njit(cache=True)
def _simulate(sig, o, h, l, c, atr, side, stop_atr, target_atr, hold):
    n = len(o)
    out_i = np.empty(n, np.int64)
    out_x = np.empty(n, np.int64)
    out_entry = np.empty(n)
    out_exit = np.empty(n)
    out_risk = np.empty(n)
    out_kind = np.empty(n, np.int8)          # 0 time, 1 stop, 2 target, 3 end of data
    k = 0
    i = 0
    while i < n - 1:
        if not sig[i] or not (atr[i] > 0):
            i += 1
            continue
        e = o[i + 1]
        risk = stop_atr * atr[i]
        stop = e - side * risk
        tgt = e + side * target_atr * atr[i] if target_atr > 0 else np.nan
        last = min(n - 1, i + hold)
        x = -1
        px = 0.0
        kind = 3
        for j in range(i + 1, last + 1):
            if side > 0:
                if l[j] <= stop:
                    px = min(o[j], stop) if j > i + 1 else stop
                    x, kind = j, 1
                    break
                if tgt == tgt and h[j] >= tgt:
                    px = max(o[j], tgt) if j > i + 1 else tgt
                    x, kind = j, 2
                    break
            else:
                if h[j] >= stop:
                    px = max(o[j], stop) if j > i + 1 else stop
                    x, kind = j, 1
                    break
                if tgt == tgt and l[j] <= tgt:
                    px = min(o[j], tgt) if j > i + 1 else tgt
                    x, kind = j, 2
                    break
        if x < 0:
            x = last
            px = c[last]
            kind = 0 if last == i + hold else 3
        out_i[k], out_x[k], out_entry[k], out_exit[k], out_risk[k], out_kind[k] = i + 1, x, e, px, risk, kind
        k += 1
        i = x + 1 if x > i else i + 1
    return out_i[:k], out_x[:k], out_entry[:k], out_exit[:k], out_risk[:k], out_kind[:k]


def run_pair(pair: str, f: pd.DataFrame, sig: np.ndarray, ex: Exit, side: int = 1,
             costs: CostModel | None = None) -> pd.DataFrame:
    """Trades for one pair. `f` needs o/h/l/c/atr/filled on a regular bar grid; `sig` is a boolean array."""
    costs = costs or CostModel()
    arr = lambda k: np.ascontiguousarray(f[k].to_numpy(np.float64))  # noqa: E731
    sig = np.asarray(sig, dtype=np.bool_) & np.isfinite(arr("atr"))
    ii, xx, en, xp, risk, kind = _simulate(sig, arr("o"), arr("h"), arr("l"), arr("c"), arr("atr"), float(side),
                                           float(ex.stop_atr), float(ex.target_atr or 0.0), int(ex.hold_bars))
    if len(ii) == 0:
        return pd.DataFrame(columns=["pair", "entry_time", "exit_time", "day", "side", "entry", "exit", "risk",
                                     "kind", "gross_r", "cost_r", "r"])
    t_in = f.index[ii]
    thin = f["filled"].to_numpy()[ii]
    years = t_in.year.to_numpy()
    cost_frac = np.array([costs.round_trip(pair, int(y), stop_exit=bool(k == 1), thin=bool(th))
                          for y, k, th in zip(years, kind, thin)])
    gross = side * (xp - en) / risk
    cost_r = cost_frac * en / risk
    return pd.DataFrame({"pair": pair, "entry_time": t_in, "exit_time": f.index[xx], "day": t_in.floor("D"),
                         "side": side, "entry": en, "exit": xp, "risk": risk, "kind": kind, "gross_r": gross,
                         "cost_r": cost_r, "r": gross - cost_r})


def summarize(trades: pd.DataFrame) -> dict:
    """R stats with the owner's checks: avg R, w/o best day, best-day share, day-clustered t, cost share."""
    n = len(trades)
    if n == 0:
        return {"n": 0, "avg_r": 0.0, "avg_r_wo_best": 0.0, "best_day_share": 1.0, "day_t": 0.0, "days": 0,
                "total_r": 0.0, "avg_cost_r": 0.0, "avg_gross_r": 0.0, "win": 0.0}
    r = trades["r"].to_numpy()
    day_tot = trades.groupby("day")["r"].sum()
    day_n = trades.groupby("day")["r"].size()
    best = day_tot.idxmax()
    total = float(r.sum())
    wo = (total - day_tot[best]) / max(1, n - int(day_n[best]))
    share = float(day_tot[best] / total) if total > 0 else 1.0
    dm = trades.groupby("day")["r"].mean()
    t = float(dm.mean() / dm.std(ddof=1) * np.sqrt(len(dm))) if len(dm) > 1 and dm.std(ddof=1) > 0 else 0.0
    return {"n": n, "avg_r": float(r.mean()), "avg_r_wo_best": float(wo), "best_day_share": share, "day_t": t,
            "days": int(len(dm)), "total_r": total, "avg_cost_r": float(trades["cost_r"].mean()),
            "avg_gross_r": float(trades["gross_r"].mean()), "win": float((r > 0).mean())}
