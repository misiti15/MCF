"""ROTA1 step 0: setup-day R matrices (2-year lab lists + live journals), same capping rule for both.
One trade per symbol per setup-day (first), first 5 in entry order, -2R per-setup daily latch.
Old holdouts (2026-04-01..06-30, 2026-09-16..10-05) dropped; locked block 2024-11..2025-02 never loaded.
Educational only — not financial advice.

    python research/rota1/build.py <scratch_dir>    # needs <scratch>/<branch>.db journal copies (git show origin/<b>:journal.db)
"""
import glob
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

S = Path(sys.argv[1])
BT = Path("/home/user/MCF/research/history2y/data/bt_lab1104")
BRANCHES = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-gen", "mcf-data-graveyard",
            "mcf-data-explore1", "mcf-data-livelab"]


def cap(t, order):
    t = t.sort_values(["setup", "date", order])
    t = t.drop_duplicates(["setup", "date", "symbol"], keep="first")
    t["k"] = t.groupby(["setup", "date"]).cumcount()
    t = t[t.k < 5].copy()
    t["cum_before"] = t.groupby(["setup", "date"]).r.cumsum() - t.r
    # latch: blocked once the day's cumulative R (of taken trades) <= -2; taken trades are a prefix
    t["blocked"] = (t.cum_before <= -2).astype(int)
    t["blk"] = t.groupby(["setup", "date"]).blocked.cummax()
    t = t[t.blk == 0]
    g = t.groupby(["date", "setup"]).r.agg(["sum", "size"]).reset_index()
    R = g.pivot(index="date", columns="setup", values="sum").fillna(0.0).sort_index()
    N = g.pivot(index="date", columns="setup", values="size").fillna(0).astype(int).sort_index()
    return R, N


def bt():
    files = sorted(glob.glob(str(BT / "sig_*.parquet")))
    assert not any(m in f for f in files for m in ("2024-11", "2024-12", "2025-01", "2025-02"))
    T = pd.concat(pd.read_parquet(f, columns=["setup", "symbol", "date", "tod", "r"]) for f in files)
    d = T.date
    hold = ((d >= "2026-04-01") & (d <= "2026-06-30")) | ((d >= "2026-09-16") & (d <= "2026-10-05"))
    T = T[~hold]
    assert not ((T.date >= "2024-11-01") & (T.date <= "2025-02-28")).any()
    R, N = cap(T, "tod")
    # all sessions (any setup traded) -> union of dates in the lists
    return R, N


def live():
    fr = []
    for b in BRANCHES:
        c = sqlite3.connect(S / f"{b}.db")
        x = pd.read_sql("select symbol, strategy, date, entry_time, entry, stop, shares, pnl, pnl_adj from trades "
                        "where run_id=1 and exit is not null", c)
        x["acct"] = b
        fr.append(x)
    t = pd.concat(fr, ignore_index=True)
    t["pnl_adj"] = t.pnl_adj.fillna(t.pnl)
    t["r"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares)
    t = t[np.isfinite(t.r)].rename(columns={"strategy": "setup"})
    t.to_parquet(S / "live_trades_rota1.parquet")
    return cap(t, "entry_time")


if __name__ == "__main__":
    R, N = bt()
    R.to_parquet(S / "bt_R.parquet"); N.to_parquet(S / "bt_N.parquet")
    print("bt", R.shape, R.index.min(), R.index.max())
    R, N = live()
    R.to_parquet(S / "live_R.parquet"); N.to_parquet(S / "live_N.parquet")
    print("live", R.shape, R.index.min(), R.index.max())
