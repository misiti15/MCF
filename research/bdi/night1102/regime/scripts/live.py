"""night1102/regime: live PAPER trades (run_id 1) of all five accounts since 2026-10-06, read from journals pulled
with `git show origin/<branch>:journal.db` (read-only). R after costs = pnl_adj / (|entry-stop| x shares), as in
regime1022. Educational only - not financial advice."""
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BR = {"P": "mcf-data", "T1": "mcf-data-testing", "T2": "mcf-data-testing2", "GY": "mcf-data-graveyard",
      "GEN": "mcf-data-gen"}


def trades(scr: Path) -> pd.DataFrame:
    rows = []
    for a, br in BR.items():
        c = sqlite3.connect(scr / "j" / f"{br}.db")
        t = pd.read_sql("select symbol, strategy, side, date, signal_time, entry_time, exit_time, entry, stop, shares,"
                        " pnl_adj, r_multiple, exit_reason from trades where run_id=1", c)
        t["acct"] = a
        rows.append(t)
    T = pd.concat(rows, ignore_index=True)
    T["risk"] = (T["entry"] - T["stop"]).abs() * T["shares"]
    T["R"] = np.where(T["risk"] > 0, T["pnl_adj"] / T["risk"], np.nan)
    T["date"] = pd.to_datetime(T["date"]).dt.date
    T = T[T["date"] >= pd.Timestamp("2026-10-06").date()].dropna(subset=["R"])
    et = pd.to_datetime(T["entry_time"], utc=True, format="mixed").dt.tz_convert("America/New_York")
    T["etod"] = et.dt.hour * 100 + et.dt.minute
    return T.reset_index(drop=True)


if __name__ == "__main__":
    T = trades(Path(sys.argv[1]))
    print(T.groupby("acct").agg(n=("R", "size"), d0=("date", "min"), d1=("date", "max"), R=("R", "sum")))
    print(T["etod"].describe())
    g = T.groupby(["strategy"]).agg(n=("R", "size"), R=("R", "sum"), side=("side", "mean"), acct=("acct", lambda s: ",".join(sorted(set(s)))))
    print((g["n"] >= 30).sum(), "setups with 30+ trades of", len(g))
    print(g[g.n >= 30].sort_values("R").to_string())
