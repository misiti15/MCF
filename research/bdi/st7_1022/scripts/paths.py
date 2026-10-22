"""st7_1022 step 2: forward 5-minute paths (bar close tod > entry tod, through the 15:55 bar) for every candidate and
partner row, rebuilt from the 1-minute SIP cache (data/cache_hist/1Min). The lab frames stop at 15:00, so the 15:05-15:55
bars come from here. The cache is read with a row filter that excludes the locked block 2024-11-01..2025-02-28.
Also writes the 5-minute bar AT the entry (h/l/c) for the frame-parity check. Educational only - not financial advice.

    python research/bdi/st7_1022/scripts/paths.py 4     # -> $W/paths.npz
"""
from __future__ import annotations

import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from sc import NP, ROOT, W, no_locked

CACHE = ROOT / "data" / "cache_hist" / "1Min"
TZ = "America/New_York"


def five(sym: str, dates: set) -> pd.DataFrame:
    lo, hi = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    col = "__index_level_0__"
    t = pq.read_table(CACHE / f"{sym}.parquet", filters=[[(col, "<", lo)], [(col, ">=", hi)]]).to_pandas()
    t.index = pd.DatetimeIndex(t.index).tz_convert(TZ)
    d = t.index.date
    no_locked(pd.unique(d))
    keep = np.isin(np.asarray(d).astype(str), list(dates))
    t = t[keep]
    m = t.index.hour * 60 + t.index.minute
    t = t[(m >= 570) & (m < 960)]
    m = t.index.hour * 60 + t.index.minute
    close_min = ((m - 570) // 5 + 1) * 5 + 570
    t = t.assign(date=np.asarray(t.index.date).astype(str), tod=(close_min // 60) * 100 + close_min % 60)
    return t.groupby(["date", "tod"]).agg(h=("high", "max"), l=("low", "min"), c=("close", "last")).reset_index()


def sym_job(args):
    sym, req = args          # req: DataFrame rows (rid, date, tod)
    try:
        b = five(sym, set(req["date"]))
    except FileNotFoundError:
        return sym, None
    g = {d: x for d, x in b.groupby("date")}
    n = len(req)
    H, L, C, T = (np.full((n, NP), np.nan, np.float32) for _ in range(4))
    E = np.full((n, 3), np.nan, np.float32)
    for j, (d, t0) in enumerate(zip(req["date"], req["tod"])):
        x = g.get(d)
        if x is None:
            continue
        at = x[x["tod"] == t0]
        if len(at):
            E[j] = at[["h", "l", "c"]].to_numpy()[0]
        fw = x[(x["tod"] > t0) & (x["tod"] <= 1555)].head(NP)
        k = len(fw)
        H[j, :k], L[j, :k], C[j, :k], T[j, :k] = (fw[c].to_numpy() for c in ("h", "l", "c", "tod"))
    return sym, (req["rid"].to_numpy(), H, L, C, T, E)


def main():
    cand = pd.concat([pd.read_parquet(p) for p in sorted((W / "cand").glob("*.parquet"))], ignore_index=True)
    part = pd.concat([pd.read_parquet(p) for p in sorted((W / "part").glob("*.parquet"))], ignore_index=True)
    req = pd.concat([cand[["symbol", "date", "tod"]].assign(rid="c" + cand.index.astype(str)),
                     part[["symbol", "date", "tod"]].assign(rid="p" + part.index.astype(str))], ignore_index=True)
    no_locked(req["date"].unique())
    jobs = [(s, g.reset_index(drop=True)) for s, g in req.groupby("symbol")]
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    res = {}
    miss = []
    with Pool(workers) as p:
        for k, (s, r) in enumerate(p.imap_unordered(sym_job, jobs)):
            if r is None:
                miss.append(s)
                continue
            for i, rid in enumerate(r[0]):
                res[rid] = (r[1][i], r[2][i], r[3][i], r[4][i], r[5][i])
            if k % 100 == 0:
                print(k, len(jobs), flush=True)
    for name, frame, pre in (("cand", cand, "c"), ("part", part, "p")):
        n = len(frame)
        A = {k: np.full((n, NP), np.nan, np.float32) for k in ("H", "L", "C", "T")}
        E = np.full((n, 3), np.nan, np.float32)
        for i in range(n):
            v = res.get(f"{pre}{i}")
            if v is None:
                continue
            A["H"][i], A["L"][i], A["C"][i], A["T"][i], E[i] = v
        np.savez_compressed(W / f"paths_{name}.npz", E=E, **A)
    print("missing symbols", miss)


if __name__ == "__main__":
    main()
