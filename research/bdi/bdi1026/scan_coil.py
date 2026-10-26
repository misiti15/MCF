"""bdi1026: parent coil trades (CWT12-coil-k4-long / k6-long, live geometry) on the open two-year history, for the
burst-skip test in PLAN.md. Reuses research/bdi/top5_1021/scan_1021.py unchanged (kernel, sim, costs, random control)
with the grid cut to the parent variant. Locked block never loaded.  Usage: python scan_coil.py [month]
Educational only - not financial advice."""
from __future__ import annotations

import os
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, "/home/user/MCF/research/bdi/top5_1021")
import scan_1021 as S  # noqa: E402

S.GRID = [g for g in S.grid() if g[0] in (S.C4, S.C6) and g[1] == "P"]
OUT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1026")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    months = sys.argv[1:] or S.lib.months()
    assert not set(months) & set(S.lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(S.month_job, months), ignore_index=True)
    T.to_parquet(OUT / ("coil_trades.parquet" if len(months) > 1 else f"coil_{months[0]}.parquet"), index=False)
    print(T.groupby("setup", observed=True).agg(n=("r", "size"), exp=("r", "mean")).to_string())
