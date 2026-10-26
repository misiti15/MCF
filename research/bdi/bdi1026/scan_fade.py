"""bdi1026: Coil Burst Fade (short) on the open two-year history (PLAN.md addendum). Coil-k4 kernel of
research/bdi/top5_1021/scan_1021.py, side flipped, no scale-out, two geometries. Costs in. Locked block never loaded.
Usage: python scan_fade.py     Educational only - not financial advice."""
from __future__ import annotations

import os
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, "/home/user/MCF/research/bdi/top5_1021")
import scan_1021 as S  # noqa: E402

F1, F05 = "BDI1026-coilburst-fade-t1s1-short", "BDI1026-coilburst-fade-t05s1-short"
S.COIL.clear(); S.COIL.update({F1: 4, F05: 4})
S.CWT14.clear()
S.BASE.update({F1: dict(side=-1, up=1.0, dn=1.0, win=(950, 1130), adv=95e6, so=0.0, geom="t1s1"),
               F05: dict(side=-1, up=0.5, dn=1.0, win=(950, 1130), adv=95e6, so=0.0, geom="t05s1")})
S.GRID = [(F1, "P", "fade", {}), (F05, "P", "fade", {})]
OUT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1026")

if __name__ == "__main__":
    months = S.lib.months()
    assert not set(months) & set(S.lib.LOCKED_MONTHS)
    with Pool(4) as p:
        T = pd.concat(p.map(S.month_job, months), ignore_index=True)
    T.to_parquet(OUT / "fade_trades.parquet", index=False)
    print(T.groupby("setup", observed=True).agg(n=("r", "size"), exp=("r", "mean")).to_string())
