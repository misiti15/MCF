"""hf1027: Coil Under the High (4 bars) CWT12-coil-k4-long on the open two-year history (2024-09..2026-10-07, the locked
block 2024-11..2025-02 never loaded), first signal per symbol-day, 09:50-11:30, ADV >= 95M, R = 0.25 x daily ATR,
stop 1R, flat 15:55. Reuses research/bdi/top5_1021/scan_1021.py unchanged (coil kernel, sim, costs, same-minute random
control). Configurations: P parent_live (0.5R target, 0.35R scale-out, as live), and 3 target settings without the
scale-out: tgt050 / tgt075 / tgt100. Also records the entry price and ATR so the cost share of R can be filtered later.
Usage: python scan_hf.py  -> <scratch>/hf/coil2y.parquet     Educational only - not financial advice."""
from __future__ import annotations
import os, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, "/home/user/MCF/research/bdi/top5_1021")
import scan_1021 as S  # noqa: E402
OUT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/hf")
S.GRID = [(S.C4, "P", "parent_live", {}), (S.C4, "T050", "tgt050", dict(so=0.0)),
          (S.C4, "T075", "tgt075", dict(so=0.0, up=0.75)), (S.C4, "T100", "tgt100", dict(so=0.0, up=1.0))]
_orig_paths = S.build_paths

def job(month):
    # same as S.month_job, plus entry close / ATR per trade (looked up after the run on the same frames)
    out = S.month_job(month)
    f = S.lib.load_month(month)[["symbol", "date", "tod", "close", "atr_d"]]
    f["symbol"] = f["symbol"].astype(str)
    o = out.assign(symbol=out.symbol.astype(str)).merge(f.rename(columns={"tod": "sig_tod"}), on=["symbol", "date", "sig_tod"], how="left")
    return o

if __name__ == "__main__":
    months = S.lib.months()
    assert not set(months) & set(S.lib.LOCKED_MONTHS)
    with Pool(3) as p:
        T = pd.concat(p.map(job, months), ignore_index=True)
    T.to_parquet(OUT / "coil2y.parquet", index=False)
    print(T.groupby("var", observed=True).agg(n=("r", "size"), exp=("r", "mean"), px=("close", lambda x: x.notna().mean())).to_string())
