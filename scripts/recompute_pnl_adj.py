"""LR8 (owner 2026-11-11): recompute the historical pnl_adj of live trades under the new live cost model, as a REPORT.

The journals are opened read-only and never changed: history keeps the pnl_adj it was booked with (flat $0.02 stop
allowance before 2026-11-12); new trades get the LR8 model at booking (mcf/execution/reconcile.py). This script writes
a CSV with one row per trade (pnl_adj as booked, pnl_adj_lr8 as if the model had applied, both R after costs) and
prints a per-account / per-setup summary, so old and new periods can be compared like for like.

    python scripts/recompute_pnl_adj.py --journal path/to/journal.db [--journal ...] [--out research/live_ready/pnl_adj_lr8.csv]

A journal may be a state branch's journal.db (e.g. `git show origin/mcf-data:journal.db > /tmp/j.db`). Known limits:
the target price improvement is measured against the journal's target column; a trade booked in several parts uses its
meta exit_parts. Educational only - not financial advice.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r, live_model, lot_costs, parts_from_row  # noqa: E402


def recompute(trades: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """pnl_adj_lr8 / r_lr8 for every trade (the model applied regardless of its effective date)."""
    model = dict(live_model(cfg) or {})
    model.pop("effective_from", None)
    t = trades.copy()
    adj, parts_n = [], []
    for _, r in t.iterrows():
        parts = parts_from_row(r)
        tgt = r.get("target")
        c = lot_costs(int(r["side"]), float(r["entry"]), float(r["shares"]), parts, tgt, str(r["date"]), model)
        adj.append(float(r["pnl"]) - c["total"])
        parts_n.append(len(parts))
    t["pnl_adj_lr8"] = adj
    risk = (t["entry"].astype(float) - t["stop"].astype(float)).abs() * t["shares"].astype(float)
    t["r_booked"] = cost_r(t)
    t["r_lr8"] = (t["pnl_adj_lr8"] / risk).where(risk > 0)
    t["r_raw"] = t["r_multiple"]
    return t


def load(path: str) -> pd.DataFrame:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return pd.read_sql("SELECT t.* FROM trades t JOIN runs r ON r.id = t.run_id WHERE r.kind = 'paper'", con)
    finally:
        con.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--journal", action="append", required=True, help="journal.db path (repeatable)")
    ap.add_argument("--out", default="research/live_ready/pnl_adj_lr8.csv")
    a = ap.parse_args(argv)
    cfg = load_config()
    frames = []
    for j in a.journal:
        t = load(j)
        t["journal"] = j
        frames.append(recompute(t, cfg))
    t = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    keep = ["journal", "date", "symbol", "strategy", "side", "entry", "stop", "target", "exit", "exit_reason", "shares",
            "pnl", "pnl_adj", "pnl_adj_lr8", "r_raw", "r_booked", "r_lr8"]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    t[[c for c in keep if c in t]].to_csv(a.out, index=False)
    if len(t):
        g = t.groupby(["journal", "strategy"]).agg(n=("r_lr8", "size"), raw=("r_raw", "mean"), booked=("r_booked", "mean"),
                                                   lr8=("r_lr8", "mean")).round(3)
        print(g.to_string())
        print(f"\nall {len(t)} trades: raw {t.r_raw.mean():+.3f}R, booked {t.r_booked.mean():+.3f}R, "
              f"LR8 {t.r_lr8.mean():+.3f}R per trade")
    print(f"wrote {a.out} (journals were opened read-only). Educational only - not financial advice.")


if __name__ == "__main__":
    main()
