"""COMPASSIDX-1126 CI-2 build: REGSTEER's Primary-4 candidate lots (regsteer cand.parquet: bench10, LIVE-L shorts / LR8
longs) + 1-min close paths and point-in-time 60-session betas (squeeze_1125/build.py job() and betas(), reused unchanged)
+ an open-mark cost (LIVE-L market cost, approximation). Usage (cwd = repo root): python research/compassidx_1126/ci2_build.py
OUTDIR. Locked block never read (asserted here and in the reused loaders). Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

OUTD = Path(sys.argv[1]); OUTD.mkdir(parents=True, exist_ok=True)
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parents[1] / "research/squeeze_1125")); sys.path.insert(0, str(H.parents[1] / "research/primshorts_1126"))
sys.path.insert(0, str(H))
import build as SB  # noqa: E402  (squeeze_1125; module-level W = sys.argv[1] is unused here)
import calib_live as CLV  # noqa: E402
import ci_lib as C  # noqa: E402

PRIMARY4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
            "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]

if __name__ == "__main__":
    t = pd.read_parquet(C.SCR / "rsw/cand.parquet")
    t = t[t.setup.isin(PRIMARY4)].reset_index(drop=True)
    C.no_locked(t.date.unique())
    bb = SB.betas(t)
    t = t.merge(bb, on=["symbol", "date"], how="left")
    raw = t.beta.copy()
    t["beta"] = np.where(t.nobs.ge(20) & raw.notna(), np.clip(0.67 * raw + 0.33, -3, 3), 1.0)
    t["lc"] = CLV.predict_R(C.CELLS, t.entry.to_numpy(), t.risk.to_numpy(), np.full(len(t), "market"))
    print("beta default share %.3f median %.2f neg %.3f" % ((~(t.nobs.ge(20) & raw.notna())).mean(), t.beta.median(),
                                                           (t.beta < 0).mean()))
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    paths = {}
    with Pool(2) as p:
        for res in p.imap_unordered(SB.job, jobs, chunksize=8):
            for i, a in res:
                paths[i] = a
    miss = int((~t.index.isin(paths.keys())).sum())
    t = t[t.index.isin(paths.keys())].copy()
    off, n, arr, pos = [], [], [], 0
    for i in t.index:
        a = paths[i]; off.append(pos); n.append(len(a)); arr.append(a); pos += len(a)
    t["off"], t["n"] = off, n
    np.save(OUTD / "paths.npy", np.concatenate(arr).astype(np.float32))
    t.drop(columns=["nobs"]).to_parquet(OUTD / "cand.parquet", index=False)
    print("candidates", len(t), "missing paths", miss, "floats", pos)
