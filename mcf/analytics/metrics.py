"""Performance statistics and breakdowns (by setup, time of day, weekday, month, ...)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def summarize(trades: pd.DataFrame) -> dict:
    if trades is None or trades.empty:
        return {"trades": 0}
    r = trades["r_multiple"]
    wins, losses = r[r > 0], r[r <= 0]
    gross_win = trades.loc[trades.pnl > 0, "pnl"].sum()
    gross_loss = -trades.loc[trades.pnl <= 0, "pnl"].sum()
    daily = trades.groupby("date")["pnl"].sum()
    eq = daily.cumsum()
    dd = (eq - eq.cummax()).min() if len(eq) else 0.0
    sharpe = daily.mean() / daily.std() * np.sqrt(252) if len(daily) > 1 and daily.std() > 0 else np.nan
    return {
        "trades": int(len(trades)),
        "win_rate": float((r > 0).mean()),
        "avg_win_r": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss_r": float(losses.mean()) if len(losses) else 0.0,
        "expectancy_r": float(r.mean()),
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "total_pnl": float(trades["pnl"].sum()),
        "max_drawdown": float(dd),
        "daily_sharpe": float(sharpe),
        "green_day_rate": float((daily > 0).mean()) if len(daily) else 0.0,
        "days": int(len(daily)),
        # break-even win rate given this payoff profile: p*W = (1-p)*|L|
        "breakeven_win_rate": float(
            abs(losses.mean()) / (wins.mean() + abs(losses.mean()))
        ) if len(wins) and len(losses) else np.nan,
    }


def _group(trades: pd.DataFrame, key) -> pd.DataFrame:
    g = trades.groupby(key)
    out = pd.DataFrame({
        "trades": g.size(),
        "win_rate": g["r_multiple"].apply(lambda r: (r > 0).mean()),
        "expectancy_r": g["r_multiple"].mean(),
        "total_r": g["r_multiple"].sum(),
        "pnl": g["pnl"].sum(),
    })
    return out


def breakdowns(trades: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if trades is None or trades.empty:
        return {}
    tr = trades.copy()
    et = pd.to_datetime(tr["entry_time"])
    tr["entry_bucket"] = et.dt.floor("30min").dt.strftime("%H:%M")
    tr["weekday"] = et.dt.day_name().str[:3]
    tr["month"] = et.dt.strftime("%Y-%m")
    tr["side_label"] = np.where(tr["side"] > 0, "long", "short")
    return {
        "strategy": _group(tr, "strategy"),
        "time_of_day": _group(tr, "entry_bucket"),
        "weekday": _group(tr, "weekday").reindex(["Mon", "Tue", "Wed", "Thu", "Fri"]).dropna(how="all"),
        "month": _group(tr, "month"),
        "side": _group(tr, "side_label"),
        "exit_reason": _group(tr, "exit_reason"),
        "strategy_x_time": tr.pivot_table(index="strategy", columns="entry_bucket", values="r_multiple", aggfunc="mean"),
    }


def daily_by_strategy(trades: pd.DataFrame) -> pd.DataFrame:
    if trades is None or trades.empty:
        return pd.DataFrame()
    return trades.pivot_table(index="date", columns="strategy", values="pnl", aggfunc="sum").fillna(0).sort_index()


def gate_check(summary: dict, gates: dict) -> tuple[bool, list[str]]:
    """Owner's promotion gates: win rate well above 50% AND positive expectancy, after costs."""
    fails = []
    if summary.get("trades", 0) < gates.get("min_trades", 0):
        fails.append(f"only {summary.get('trades', 0)} trades (< {gates['min_trades']})")
    if summary.get("win_rate", 0) < gates.get("min_win_rate", 0):
        fails.append(f"win rate {summary.get('win_rate', 0):.1%} < {gates['min_win_rate']:.0%}")
    if summary.get("expectancy_r", 0) <= gates.get("min_expectancy_r", 0):
        fails.append(f"expectancy {summary.get('expectancy_r', 0):+.3f}R not above {gates['min_expectancy_r']}")
    if summary.get("profit_factor", 0) < gates.get("min_profit_factor", 0):
        fails.append(f"profit factor {summary.get('profit_factor', 0):.2f} < {gates['min_profit_factor']}")
    return not fails, fails
