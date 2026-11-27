"""UPDAY_1127 random size-matched control simulator (PREREG (d)). Input: requests parquet (rid, symbol, date, tag, em,
rp = stop distance as fraction of entry, trail). Each request: long at the open of the first bar with minute >= em,
stop = entry x (1 - rp), same walk as up_build (15:55 exit, optional TRAIL). Output: rid, entry, risk, px, kind.
Usage: python up_rand.py REQ.parquet OUT.parquet. Locked block never read. Educational only - not financial advice."""
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import up_build as U  # noqa: E402

REQ = None


def work(key):
    tag, sym = key
    q = REQ[(REQ.tag == tag) & (REQ.symbol == sym)]
    b = U.load(U.SRC[tag] / f"{sym}.parquet")
    mmall = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
    dates = b.index.date.astype(str)
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    starts = np.flatnonzero(np.r_[True, dates[1:] != dates[:-1]])
    ends = np.r_[starts[1:], len(dates)]
    pos = {dates[s]: (s, e) for s, e in zip(starts, ends)}
    out = []
    for r in q.itertuples():
        if r.date not in pos:
            continue
        s, e = pos[r.date]
        mm = mmall[s:e]
        ii = np.flatnonzero(mm >= r.em)
        iec = np.flatnonzero(mm <= 385)
        if not len(ii) or not len(iec) or ii[0] > iec[-1]:
            continue
        i0, ie = ii[0], iec[-1]
        o, h, l, c = O[s:e], H[s:e], L[s:e], C[s:e]
        ent = o[i0]; stop = ent * (1 - r.rp)
        px, k = U.walk(o, h, l, c, i0, ie, stop, bool(r.trail))
        out.append((r.rid, ent, ent - stop, px, k))
    return out


def init(p):
    global REQ
    REQ = pd.read_parquet(p)


if __name__ == "__main__":
    req = pd.read_parquet(sys.argv[1])
    U.no_locked(req.date.unique())
    keys = sorted(set(zip(req.tag, req.symbol)))
    res = []
    with Pool(4, initializer=init, initargs=(sys.argv[1],)) as pool:
        for n, r in enumerate(pool.imap_unordered(work, keys, chunksize=4)):
            res.extend(r)
            if n % 300 == 0:
                print(n, len(keys), flush=True)
    pd.DataFrame(res, columns=["rid", "entry", "risk", "px", "kind"]).to_parquet(sys.argv[2])
