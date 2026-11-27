"""ARENASTARS-1127 Part C build: E4 candidate lots = P4 Primary setups (bench10 lots, LIVE-L on shorts, LR8 on NM-ETF,
as hedgeb_1126/build.py) + G05 / G07 / G37 (LIVE-L) + their random-entry pools (RND-*, at most 30 lots per day per tag,
LIVE-L), price >= $5, shorts ETB >= 90%, 1-minute close paths (hedgeb_1126 job()). Usage (cwd repo): python as_build.py W.
Locked block asserted absent. Educational only - not financial advice."""
import json
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd())); sys.path.insert(0, "research/ultimate_1119/top10"); sys.path.insert(0, "research/primshorts_1126")
sys.path.insert(0, "research/hedgeb_1126")
W = Path(sys.argv[1])
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402
import build as HB  # noqa: E402  (hedgeb_1126/build.py: load / grid / job / period; its __main__ is not run)

SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
P4 = HB.SETUPS
TAGS = {"GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short": "G05",
        "GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short": "G07",
        "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long": "G37"}

if __name__ == "__main__":
    x = pd.concat([pd.read_parquet(W / f"{f}.parquet") for f in ("trades_t1", "trades_t2")], ignore_index=True)
    x["date"] = x.date.astype(str)
    x["tag"] = x.setup.map(TAGS).fillna(x.setup)
    x = x[x.tag.isin(P4 + ["G05", "G07", "G37", "RND-G05", "RND-G07", "RND-G37"])].copy()
    x = B.add_r(x)
    x["per"] = x.date.map(HB.period)
    x = x[x.per != "none"]
    HB.no_locked(x.date.unique())
    etb = pd.read_parquet(SP / "pyramid/S/etb_rate.parquet").rate
    x = x[x.entry >= 5.0]
    x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)]
    rnd = x.tag.str.startswith("RND-")
    rs = x[rnd].sample(frac=1.0, random_state=1127)
    rs = rs[rs.groupby(["tag", "date"]).cumcount() < 30]
    x = pd.concat([x[~rnd], rs])
    cells = json.load(open("research/primshorts_1126/cells_live.json"))
    kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
    x["r_lr8"] = x.r
    ll = x.r_gross - CL.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd)
    x["r"] = np.where((x.side < 0) | ~x.tag.isin(P4), ll, x.r)
    x["lcost"] = x.r_gross - x.r
    t = x[["tag", "symbol", "date", "per", "tod", "side", "entry", "risk", "px", "kind", "em", "xm", "r", "r_lr8", "lcost"]
          ].rename(columns={"tag": "setup"}).reset_index(drop=True)
    print(t.groupby(["setup", "per"]).size().unstack())
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    paths = {}
    with Pool(3) as p:
        for res in p.imap_unordered(HB.job, jobs, chunksize=8):
            for i, a in res:
                paths[i] = a
    miss = (~t.index.isin(paths.keys())).sum()
    t = t[t.index.isin(paths.keys())].copy()
    off, n, arr, pos = [], [], [], 0
    for i in t.index:
        a = paths[i]; off.append(pos); n.append(len(a)); arr.append(a); pos += len(a)
    t["off"], t["n"] = off, n
    np.save(W / "paths.npy", np.concatenate(arr).astype(np.float32))
    HB.no_locked(t.date.unique())
    t.to_parquet(W / "cand.parquet", index=False)
    print("candidates", len(t), "missing paths", miss, "path floats", pos)
