"""STOPX-1127 Step 1 walk: Primary's 4 setups' bench10 candidate lots (regsteer_1126 rs_cand.py output) re-walked on
1-minute OHLC bars under 4 stop rules (PREREG.md):
  BASE  bench10 walk: stop on intrabar touch (gap-through at the worse of open/stop), target traded through by $0.01, stop first
  C1    close-confirmed stop: a 1-min bar CLOSE at/through the stop fires it; fill = next 1-min bar open
  C2    C1 + intrabar catastrophe stop at 2x the stop distance (checked first; worse of open / level)
  C3    clock-aligned 5-min bar close at/through the stop fires it (fill = next 1-min open) + C2's catastrophe stop
Flat at the 15:55 open. Also stores each lot's 1-min close path (entry minute .. 15:55) for the book's open marks.
Usage (repo root): python research/stopx_1127/sx_walk.py CAND.parquet OUT_DIR. Locked block 2024-11-01..2025-02-28 never
read (bar loads filter it out and assert; lot table asserted). Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
PRIMARY4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
            "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
TGT_MULT = {s: (0.5 if s.startswith("NM-ETF") else 1.0) for s in PRIMARY4}   # t05s1 / t1s1
CONFIGS = ["BASE", "C1", "C2", "C3"]


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load(sym, src):
    p = src / f"{sym}.parquet"
    if not p.exists():
        return None
    f = pads.field("__index_level_0__")
    flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
    b = pads.dataset(str(p), format="parquet").to_table(
        filter=flt, columns=["open", "high", "low", "close", "__index_level_0__"]).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def first(mask):
    return int(np.argmax(mask)) if mask.any() else -1


def walk_lot(s, e, risk, tmult, tod, hm, O, H, Lo, C, bucket):
    """One lot on its day's bars (arrays of the whole day). Returns {config: (px, kind, xt_hhmm)} and the close path."""
    stop, tgt, cat = e - s * risk, e + s * tmult * risk, e - s * 2.0 * risk
    selm = (hm >= tod) & (hm < 1555)
    sel = np.flatnonzero(selm)
    after = np.flatnonzero(hm >= 1555)
    out = {}
    if not len(sel):
        return None
    Os, Hs, Ls, Cs = O[sel], H[sel], Lo[sel], C[sel]
    if s == 1:
        st_t, tg_t, cl_t, ct_t = Ls <= stop, Hs >= tgt + 0.01, Cs <= stop, Ls <= cat
    else:
        st_t, tg_t, cl_t, ct_t = Hs >= stop, Ls <= tgt - 0.01, Cs >= stop, Hs >= cat
    # 5-min bucket end: next bar (in the day) is in another bucket or there is none
    nxt = sel + 1
    bend = np.ones(len(sel), bool)
    inday = nxt < len(hm)
    bend[inday] = bucket[nxt[inday]] != bucket[sel[inday]]
    cl5 = cl_t & bend

    def flat():
        if len(after):
            return (O[after[0]], 0, 1555)
        return (Cs[-1], 0, int(hm[sel[-1]]) + 1)

    def nextfill(j):
        k = sel[j] + 1
        if k < len(hm):
            return (O[k], 1, int(hm[k]))
        return (Cs[j], 1, int(hm[sel[j]]) + 1)

    worse = (lambda o, lvl: min(o, lvl)) if s == 1 else (lambda o, lvl: max(o, lvl))
    # BASE
    j = first(st_t | tg_t)
    if j < 0:
        out["BASE"] = flat()
    elif st_t[j]:
        out["BASE"] = (worse(Os[j], stop), 1, int(hm[sel[j]]))
    else:
        out["BASE"] = (tgt, 2, int(hm[sel[j]]))
    for name, trig, use_cat in (("C1", cl_t, False), ("C2", cl_t, True), ("C3", cl5, True)):
        ev = trig | tg_t | (ct_t if use_cat else False)
        j = first(ev)
        if j < 0:
            out[name] = flat()
        elif use_cat and ct_t[j]:
            out[name] = (worse(Os[j], cat), 1, int(hm[sel[j]]))
        elif trig[j]:
            out[name] = nextfill(j)
        else:
            out[name] = (tgt, 2, int(hm[sel[j]]))
    return out


def grid(mm, C):
    g = np.full(390, np.nan)
    ok = (mm >= 0) & (mm < 390)
    g[mm[ok]] = C[ok]
    return pd.Series(g).ffill().bfill().to_numpy()


def job(args):
    sym, T = args
    res = []
    for src, sub in ((HIST, T[T.date >= "2024-09-16"]), (FRESH, T[T.date < "2024-09-16"])):
        if not len(sub):
            continue
        b = load(sym, src)
        if b is None:
            continue
        day = b.index.date.astype(str)
        hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
        mins = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
        O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        for d, g in sub.groupby("date"):
            ix = np.flatnonzero(day == d)
            if not len(ix):
                continue
            hm, mm = hhmm[ix], mins[ix]
            bucket = np.floor_divide(mm, 5)
            G = grid(mm, C[ix])
            for r in g.itertuples():
                w = walk_lot(int(r.side), float(r.entry), float(r.risk), TGT_MULT[r.setup], int(r.tod), hm,
                             O[ix], H[ix], Lo[ix], C[ix], bucket)
                if w is None:
                    continue
                a = int(r.em) - 570
                res.append((r.Index, w, G[a:max(a + 1, 955 - 570)].astype(np.float32)))
    return res


if __name__ == "__main__":
    CAND, OUT = Path(sys.argv[1]), Path(sys.argv[2])
    OUT.mkdir(parents=True, exist_ok=True)
    c = pd.read_parquet(CAND)
    c = c[c.setup.isin(PRIMARY4)].reset_index(drop=True)
    no_locked(c.date.unique())
    jobs = [(s, g) for s, g in c.groupby("symbol")]
    W, P = {}, {}
    with Pool(3) as p:
        for res in p.imap_unordered(job, jobs, chunksize=8):
            for i, w, path in res:
                W[i], P[i] = w, path
    c = c[c.index.isin(W.keys())].copy()
    for k in CONFIGS:
        c[f"px_{k}"] = [W[i][k][0] for i in c.index]
        c[f"kind_{k}"] = [W[i][k][1] for i in c.index]
        xt = np.array([W[i][k][2] for i in c.index])
        c[f"xm_{k}"] = (xt // 100) * 60 + xt % 100
    off, n, arr, pos = [], [], [], 0
    for i in c.index:
        a = P[i]; off.append(pos); n.append(len(a)); arr.append(a); pos += len(a)
    c["off"], c["n"] = off, n
    np.save(OUT / "paths.npy", np.concatenate(arr).astype(np.float32))
    c.reset_index(drop=True).to_parquet(OUT / "walk.parquet", index=False)
    print("lots", len(c), "path floats", pos)
