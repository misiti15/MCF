"""T2 (2023-01-03..2024-09-13, data/cache_fresh 469 symbols) for trio-family finalists: frames built exactly as bench10.t2_job,
then gd.masks / rows_at, then the 1-minute walk. python gd_t2.py cfg1,cfg2,...  Educational only - not financial advice."""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gd  # noqa: E402
from gd import B, W  # noqa: E402

CFGS: list = []


def job(sym):
    import research.history2y.build_frames as BF
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert ds.min() >= B.T2_WARM and ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return None
    x = x.reset_index(names="ts")
    x = x[[c for c in x.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return None
    f = x.drop(columns=["ts"])
    f["symbol"] = sym
    f = f[(f.tod >= 950) & (f.tod <= 1500)].sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    rng = np.random.default_rng(abs(hash(sym)) % (2 ** 32))
    ms, trio, key = gd.masks(f)
    out = []
    for cfg, (mk, refire) in ms.items():
        if cfg in CFGS:
            o = gd.build(f, cfg, mk, refire, rng, null=True)
            if o is not None:
                out.append(o)
    tod = f["tod"].to_numpy(int)
    hit = np.flatnonzero(trio & (f["atr_d"].to_numpy(float) > 0))
    if len(hit):
        first = hit[np.r_[True, key[hit][1:] != key[hit][:-1]]]
        for D in (3, 6):
            if f"S7-delay-d{D}" not in CFGS:
                continue
            j = first + D
            ok = j < len(f)
            j, fi = j[ok], first[ok]
            m0 = (tod[fi] // 100) * 60 + tod[fi] % 100
            m1 = (tod[j] // 100) * 60 + tod[j] % 100
            ok = (key[j] == key[fi]) & (tod[j] <= 1500) & ((m1 - m0) == 5 * D)
            out.append(gd.rows_at(f, j[ok], f"S7-delay-d{D}", "real", rng, True))
    if not out:
        return None
    o = pd.concat(out, ignore_index=True)
    o = o[(o.risk > 0) & np.isfinite(o.risk)].reset_index(drop=True)
    if not len(o):
        return None
    u = o[["symbol", "date", "tod", "entry", "stop", "tgt", "side"]].drop_duplicates().reset_index(drop=True)
    w = B.walk_trades(u, b)
    a = pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i")
    u = u.join(a)
    return o.merge(u, on=["symbol", "date", "tod", "entry", "stop", "tgt", "side"], how="left")


def init(c):
    CFGS[:] = c


if __name__ == "__main__":
    cf = sys.argv[1].split(",")
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    out = []
    with Pool(3, initializer=init, initargs=(cf,)) as p:
        for o in p.imap_unordered(job, syms):
            if o is not None and len(o):
                out.append(o)
    T = pd.concat(out, ignore_index=True)
    T.to_parquet(W / f"trades_t2_r{gd.ROUND}.parquet")
    print(len(T), T[T.grp == "real"].groupby("cfg").size().to_dict())
