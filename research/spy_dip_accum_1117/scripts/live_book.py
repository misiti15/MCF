"""Daily live intraday book (run_id = 1 = live paper) from the ten intraday journals on the mcf-data* state branches
(git show origin/<branch>:journal.db, read-only temp copy, removed after). Sessions 2026-10-06 onward.
R after costs = pnl_adj / risk (mcf.costs.cost_r convention), P/L = pnl_adj where booked else pnl.
Usage: python live_book.py OUT.csv. Educational only - not financial advice."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(os.environ.get("MCF_ROOT", "/home/user/MCF"))
BRANCHES = {"primary": "mcf-data", "ondeck": "mcf-data-testing", "testing_a": "mcf-data-testing2",
            "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen", "testing_b": "mcf-data-explore1",
            "testing_c": "mcf-data-livelab", "testing_d": "mcf-data-testingd", "testing_e": "mcf-data-testinge",
            "testing_f": "mcf-data-testingf"}


def main(out):
    frames = []
    for acct, br in BRANCHES.items():
        fd, p = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            blob = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], capture_output=True)
            if blob.returncode or not blob.stdout:
                print("no journal", acct)
                continue
            Path(p).write_bytes(blob.stdout)
            c = sqlite3.connect(p)
            df = pd.read_sql("select date, strategy, entry, stop, shares, pnl, pnl_adj from trades "
                             "where run_id = 1 and date >= '2026-10-06'", c)
            c.close()
        finally:
            os.unlink(p)
        df["account"] = acct
        frames.append(df)
    t = pd.concat(frames, ignore_index=True)
    t["pl"] = t.pnl_adj.fillna(t.pnl)
    risk = (t.entry - t.stop).abs() * t.shares.abs()
    t["R"] = (t.pl / risk).where(risk > 0)
    day = t.groupby("date").agg(trades=("pl", "size"), pl=("pl", "sum"), R=("R", "sum"),
                                pl_primary=("pl", lambda s: s[t.loc[s.index, "account"] == "primary"].sum()))
    day.to_csv(out, float_format="%.4f")
    print(day.describe().round(2).to_string())
    print(t.groupby("account").agg(n=("pl", "size"), pl=("pl", "sum"), R=("R", "sum")).round(1).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
