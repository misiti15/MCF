"""swarm15_1029 step 1: rank every live setup by total live (paper) trade count since 2026-10-06 across all 5 intraday
accounts (Primary, Testing 1, Testing 2, Setup Generator, Graveyard): reports/<date>.csv on the mcf-data* branches,
run_id 1. Copies of the same setup across accounts are merged (same strategy id). S6 out. GEN included.
Live = paper fills (rule 7). Educational only - not financial advice.

    python research/bdi/swarm15_1029/live_rank.py
"""
import io
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/sw15_1029")
BR = {"p": "mcf-data", "t1": "mcf-data-testing", "t2": "mcf-data-testing2", "gen": "mcf-data-gen", "gy": "mcf-data-graveyard"}


def load():
    fr = []
    for a, b in BR.items():
        names = subprocess.check_output(["git", "-C", str(ROOT), "ls-tree", "--name-only", f"origin/{b}", "reports/"]).decode().split()
        for f in names:
            if not f.endswith(".csv") or f[8:18] < "2026-10-06":
                continue
            raw = subprocess.check_output(["git", "-C", str(ROOT), "show", f"origin/{b}:{f}"])
            t = pd.read_csv(io.BytesIO(raw))
            t["acct"] = a
            fr.append(t)
    t = pd.concat(fr, ignore_index=True)
    t = t[(t.run_id == 1) & t.r_multiple.notna() & ~t.strategy.str.startswith("S6")]
    t["nt"] = pd.to_datetime(t["entry_time"], utc=True, format="mixed").dt.tz_convert("America/New_York")
    t["tod"] = t["nt"].dt.hour * 100 + t["nt"].dt.minute
    return t


def wo_best(g):
    d = g.groupby("date")["r_multiple"].sum()
    tot = d.sum()
    b = d.max()
    n2 = len(g) - (g.date == d.idxmax()).sum()
    return pd.Series({"wo_best": (tot - b) / max(n2, 1), "best_share": b / tot if tot > 0 else float("nan"),
                      "best_day": d.idxmax()})


def main():
    t = load()
    SCR.mkdir(parents=True, exist_ok=True)
    t.drop(columns=["nt"]).to_parquet(SCR / "live.parquet", index=False)
    rank = t.groupby("strategy").agg(n=("id", "size"), accounts=("acct", lambda x: ",".join(sorted(set(x)))),
                                     days=("date", "nunique"), first=("date", "min"), last=("date", "max"),
                                     win=("r_multiple", lambda r: (r > 0).mean()), avg_r=("r_multiple", "mean"),
                                     sum_r=("r_multiple", "sum"), pnl=("pnl", "sum"))
    rank = rank.join(t.groupby("strategy").apply(wo_best)).sort_values("n", ascending=False)
    rank.round(4).to_csv(OUT / "live_rank.csv")
    print("dates:", sorted(t.date.unique())[0], "..", sorted(t.date.unique())[-1], "trades", len(t))
    print(rank.head(30).round(3).to_string())


if __name__ == "__main__":
    main()
