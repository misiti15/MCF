"""Benchmark statistics per setup per half (from bench.py's trades.parquet) -> benchmark.json.
    python research/ultimate_1119/benchmark/stats.py WORKDIR LIVE_JSON
SPY day type: SPY 09:30 open -> 15:59 close on the 1-minute cache; up >= +0.30%, down <= -0.30%, flat between.
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
TZ = "America/New_York"
THR = 0.30


def half_of(d: pd.Series) -> np.ndarray:
    s = d.astype(str)
    fit = ((s >= "2024-10-01") & (s <= "2024-10-31")) | ((s >= "2025-03-01") & (s <= "2025-09-30"))
    chk = s >= "2025-10-01"
    assert not ((s >= "2024-11-01") & (s <= "2025-02-28")).any()
    return np.where(fit, "fit", np.where(chk, "check", "none"))


def spy_days() -> pd.DataFrame:
    f = pads.field("__index_level_0__")
    b = pads.dataset(str(CACHE / "SPY.parquet"), format="parquet").to_table(
        filter=(f < pd.Timestamp("2024-11-01", tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b["date"] = b.index.date.astype(str)
    g = b.groupby("date").agg(o=("open", "first"), c=("close", "last"))
    g["ret"] = (g.c / g.o - 1) * 100
    g["type"] = np.where(g.ret >= THR, "up", np.where(g.ret <= -THR, "down", "flat"))
    g = g[g.index >= "2024-10-01"]
    g["half"] = half_of(pd.Series(g.index, index=g.index))
    return g


def stats(t: pd.DataFrame, n_sessions: int, spy: pd.DataFrame, col: str) -> dict:
    t = t[t[col].notna()]
    if not len(t):
        return {"trades": 0}
    day = t.groupby("date")[col].sum()
    tot = float(t[col].sum())
    best = day.idxmax()
    hold = np.where(t.x1 >= 0, ((t.x1 // 100) * 60 + t.x1 % 100) - ((t.tod // 100) * 60 + t.tod % 100), np.nan)
    ty = t.date.map(spy["type"])
    tps = len(t) / day.size
    o = {"trades": int(len(t)), "sessions": int(n_sessions), "sessions_traded": int(day.size),
         "trades_per_session": round(len(t) / n_sessions, 2), "win": round(float((t[col] > 0).mean()), 3),
         "avg_r": round(float(t[col].mean()), 4), "avg_r_wo_best_day": round(float(t.loc[t.date != best, col].mean()), 4),
         "best_day_share": round(float(day.max() / tot), 3) if tot > 0 else None, "total_r": round(tot, 2),
         "total_r_per_session": round(tot / n_sessions, 3), "worst_day": round(float(day.min()), 2),
         "worst_day_per_trade": round(float(day.min()) / tps, 3)}
    for k in ("up", "flat", "down"):
        x = t.loc[ty == k, col]
        o[f"avg_r_spy_{k}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_spy_{k}"] = int(len(x))
    o["median_hold_min"] = float(np.nanmedian(hold))
    return o


if __name__ == "__main__":
    W = Path(sys.argv[1])
    live = json.loads(Path(sys.argv[2]).read_text())
    T = pd.read_parquet(W / "trades.parquet")
    T["half"] = half_of(T["date"])
    spy = spy_days()
    nses = spy.groupby("half").size().to_dict()
    out = {"note": "Educational only - not financial advice. Benchmark of MCF's current best setups on the 2-year history "
                   "(research/ultimate_1119/benchmark/bench.py + stats.py). R after LR8-basis costs, 1-minute exits.",
           "sessions": {k: int(v) for k, v in nses.items() if k != "none"},
           "spy_day_types": {h: spy[spy.half == h]["type"].value_counts().to_dict() for h in ("fit", "check")},
           "setups": {}}
    for s, g in T.groupby("setup"):
        e = {}
        for h in ("fit", "check"):
            gh = g[g.half == h]
            e[h] = stats(gh, nses[h], spy, "r1")
            e[h]["avg_r_5min_walk"] = round(float(gh.r5.mean()), 4) if len(gh) else None
        e["live"] = live.get(s)
        out["setups"][s] = e
    (HERE / "benchmark.json").write_text(json.dumps(out, indent=1, default=float))
    rows = []
    for s, e in out["setups"].items():
        for h in ("fit", "check"):
            rows.append({"setup": s[:34], "half": h, **{k: e[h].get(k) for k in (
                "trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r",
                "total_r_per_session", "worst_day", "worst_day_per_trade", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down",
                "median_hold_min", "avg_r_5min_walk")}})
    pd.set_option("display.width", 300)
    pd.set_option("display.max_columns", 30)
    print(pd.DataFrame(rows).to_string(index=False))
    print(out["sessions"], out["spy_day_types"])
