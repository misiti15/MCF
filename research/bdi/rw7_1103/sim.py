"""rw7_1103 pass 2: exit paths on SIP 1-min bars (data/cache_hist/1Min) for every candidate / control row of cands.py.
Short side only. Entry at the decision-bar close (frame close), path from the 1-min bar opening at the decision tod,
stop first inside a bar, out at the 15:55 price (close of the 15:54 bar). Gross R (no costs) per exit geometry:
  t1s1, t15s1, t05s1, part (half at +0.5R, rest stop->entry, target +1R), ts60 (t1s1 + 60-min time stop),
  be05 (t1s1, stop -> entry once +0.5R). Also the exit kind (0 time, 1 stop, 2 target) and exit minute per geometry.
Usage: python sim.py <dir> <cand|ctrl> [workers]   Educational only - not financial advice."""
import os, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
BARS = Path(os.environ.get("MCF_DATA_ROOT", "/home/user/MCF")) / "data" / "cache_hist" / "1Min"
D = Path(sys.argv[1]); WHAT = sys.argv[2]
GEO = ("t1s1", "t15s1", "t05s1", "part", "ts60", "be05")


def first(mask):
    i = np.flatnonzero(mask)
    return int(i[0]) if len(i) else 10 ** 9


def one(px, R, h, l, c, mins):
    """h, l, c: path arrays from the entry minute through the 15:54 bar; mins: minute-of-day. Returns dict per geom."""
    n = len(c)
    out = {}
    if n == 0 or R <= 0:
        return None
    st = first(h >= px + R)

    def bracket(tm, upto=n):
        tg = first(l[:upto] <= px - tm * R)
        s = st if st < upto else 10 ** 9
        if s <= tg and s < upto:
            return -1.0, 1, mins[s]
        if tg < upto:
            return tm, 2, mins[tg]
        return (px - c[upto - 1]) / R, 0, mins[upto - 1]
    out["t1s1"] = bracket(1.0); out["t15s1"] = bracket(1.5); out["t05s1"] = bracket(0.5)
    out["ts60"] = bracket(1.0, min(n, 60))
    a = first(l <= px - 0.5 * R)
    if st <= a:
        out["be05"] = (-1.0, 1, mins[st]) if st < n else out["t1s1"]
        out["part"] = out["be05"]
    else:
        if a >= n:   # never reached 0.5R and no stop: time exit
            out["be05"] = out["part"] = out["t1s1"]
        else:
            rest_h, rest_l = h[a + 1:], l[a + 1:]
            be = first(rest_h >= px); tg = first(l[a:] <= px - R)   # target may fill on the 0.5R bar itself
            tg_rel = tg - 1   # index into rest (tg on bar a -> -1)
            if tg < 10 ** 9 and tg_rel < be:
                rest = (1.0, 2, mins[a + 1 + tg_rel] if tg_rel >= 0 else mins[a])
            elif be < 10 ** 9:
                rest = (0.0, 1, mins[a + 1 + be])
            else:
                rest = ((px - c[-1]) / R, 0, mins[-1])
            out["be05"] = rest
            out["part"] = (0.5 * 0.5 + 0.5 * rest[0], 3 if rest[1] != 2 else 2, rest[2])
    return out


def job(args):
    sym, rows = args
    p = BARS / f"{sym}.parquet"
    res = []
    if not p.exists():
        return res
    b = pd.read_parquet(p)
    b.index = pd.to_datetime(b.index)
    if b.index.tz is None:
        b.index = b.index.tz_localize("UTC")
    b.index = b.index.tz_convert("America/New_York")
    b = b.between_time("09:30", "15:54")
    day = b.index.date
    mod = (b.index.hour * 60 + b.index.minute).to_numpy()
    H, L, Cc = b.high.to_numpy(float), b.low.to_numpy(float), b.close.to_numpy(float)
    bounds = {}
    u, st = np.unique(day, return_index=True)
    en = np.r_[st[1:], len(day)]
    for d_, a_, e_ in zip(u, st, en):
        bounds[str(d_)] = (a_, e_)
    for rid, d, tod, px, atr in rows:
        bd = bounds.get(str(d))
        if bd is None:
            continue
        a_, e_ = bd
        m0 = (tod // 100) * 60 + tod % 100
        i0 = a_ + int(np.searchsorted(mod[a_:e_], m0))
        o = one(px, 0.25 * atr, H[i0:e_], L[i0:e_], Cc[i0:e_], mod[i0:e_])
        if o is None:
            continue
        rec = {"rid": rid}
        for g in GEO:
            rec[f"g_{g}"], rec[f"k_{g}"], rec[f"x_{g}"] = o[g]
        res.append(rec)
    return res


if __name__ == "__main__":
    df = pd.read_parquet(D / f"{WHAT}.parquet", columns=["symbol", "date", "tod", "close", "atr_d"])
    df["rid"] = np.arange(len(df))
    tasks = [(s, list(zip(g.rid, g.date.astype(str), g.tod.astype(int), g.close, g.atr_d))) for s, g in df.groupby("symbol")]
    out = []
    with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 4) as pl:
        for r in pl.imap_unordered(job, tasks, chunksize=4):
            out.extend(r)
    pd.DataFrame(out).sort_values("rid").to_parquet(D / f"{WHAT}_sim.parquet")
    print(WHAT, len(df), "rows,", len(out), "simulated")
