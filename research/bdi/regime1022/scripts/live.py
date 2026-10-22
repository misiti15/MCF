"""regime1022: live PAPER record per setup from the journals (run 1) of Primary (p), Testing 1 (t1), Testing 2 (t2),
Graveyard (gy) and the Setup Generator (gen), read from origin/mcf-data* (git show, read-only) into the scratchpad.
R after costs = pnl_adj / (|entry - stop| x shares). Educational only - not financial advice."""
from __future__ import annotations

import sqlite3
import subprocess

import numpy as np
import pandas as pd

from rc import ROOT, SCR

BR = {"p": "mcf-data", "t1": "mcf-data-testing", "t2": "mcf-data-testing2", "gy": "mcf-data-graveyard",
      "gen": "mcf-data-gen"}


def journals() -> pd.DataFrame:
    (SCR / "j").mkdir(exist_ok=True)
    rows = []
    for a, br in BR.items():
        f = SCR / "j" / f"{a}.db"
        if not f.exists():
            f.write_bytes(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], check=True,
                                         capture_output=True).stdout)
        c = sqlite3.connect(f)
        t = pd.read_sql("select symbol, strategy, side, date, entry_time, exit_time, entry, stop, shares, pnl_adj, "
                        "r_multiple, exit_reason from trades where run_id=1", c)
        t["acct"] = a
        rows.append(t)
    T = pd.concat(rows, ignore_index=True)
    T["risk"] = (T["entry"] - T["stop"]).abs() * T["shares"]
    T["radj"] = np.where(T["risk"] > 0, T["pnl_adj"] / T["risk"], np.nan)
    T["date"] = pd.to_datetime(T["date"]).dt.date
    return T


def record(t: pd.DataFrame) -> dict:
    t = t.dropna(subset=["radj"])
    if t.empty:
        return {"trades": 0}
    by = t.groupby("date")["radj"].agg(["sum", "size"])
    n = len(t)
    m = t["radj"].mean()
    se = np.sqrt(((by["sum"] - m * by["size"]) ** 2).sum()) / n if len(by) > 1 else np.nan
    w = t[t["radj"] > 0]["radj"]
    lo = t[t["radj"] <= 0]["radj"]
    be = (lo.abs().mean() / (w.mean() + lo.abs().mean())) if len(w) and len(lo) else np.nan
    days = sorted(t["date"].unique())
    l4 = t[t["date"].isin(days[-4:])]
    out = {"trades": n, "sessions": len(days), "win_pct": round(100 * (t["radj"] > 0).mean(), 1),
            "breakeven_win_pct": round(100 * be, 1) if be == be else None, "avg_r": round(m, 3),
            "t": round(m / se, 2) if se and se == se and se > 0 else None, "pnl_adj": round(t["pnl_adj"].sum(), 2),
            "sum_r": round(t["radj"].sum(), 2), "last4_avg_r": round(l4["radj"].mean(), 3),
            "last4_pnl": round(l4["pnl_adj"].sum(), 2), "first": str(days[0]), "last": str(days[-1])}
    return {k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in out.items()}


if __name__ == "__main__":
    T = journals()
    print(T.groupby("acct").agg(n=("radj", "size"), d0=("date", "min"), d1=("date", "max"), pnl=("pnl_adj", "sum")))
