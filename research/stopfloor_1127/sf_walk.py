"""STOPFLOOR-1127 bench walk: Primary's 4 setups' bench10 candidate lots (regsteer_1126 rs_cand.py output) re-walked on
1-minute OHLC under BASE (stopx_1127 BASE rule) and 5 widened-stop variants (PREREG.md): risk' = max(risk, floor),
stop' = entry - side*risk', target' = entry + side*tmult*risk'. Floors: 50/75/100 bp of entry, $0.10, $0.20.
Usage (repo root): python research/stopfloor_1127/sf_walk.py CAND.parquet OUT_DIR. Locked block never read.
Educational only - not financial advice."""
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
TGT_MULT = {s: (0.5 if s.startswith("NM-ETF") else 1.0) for s in PRIMARY4}
VARS = {"BASE": None, "W50": ("bp", 50), "W75": ("bp", 75), "W100": ("bp", 100), "Wc10": ("c", 0.10), "Wc20": ("c", 0.20)}


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def new_risk(entry, risk, v):
    if v is None:
        return risk
    k, x = v
    return max(risk, entry * x * 1e-4) if k == "bp" else max(risk, x)


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


def walk(s, e, risk, tmult, tod, hm, O, H, Lo, C):
    stop, tgt = e - s * risk, e + s * tmult * risk
    sel = np.flatnonzero((hm >= tod) & (hm < 1555))
    after = np.flatnonzero(hm >= 1555)
    if not len(sel):
        return None
    Os, Hs, Ls, Cs = O[sel], H[sel], Lo[sel], C[sel]
    if s == 1:
        st_t, tg_t = Ls <= stop, Hs >= tgt + 0.01
    else:
        st_t, tg_t = Hs >= stop, Ls <= tgt - 0.01
    ev = st_t | tg_t
    if not ev.any():
        if len(after):
            return (O[after[0]], 0, 1555)
        return (Cs[-1], 0, int(hm[sel[-1]]) + 1)
    j = int(np.argmax(ev))
    if st_t[j]:
        return ((min(Os[j], stop) if s == 1 else max(Os[j], stop)), 1, int(hm[sel[j]]))
    return (tgt, 2, int(hm[sel[j]]))


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
        O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        for d, g in sub.groupby("date"):
            ix = np.flatnonzero(day == d)
            if not len(ix):
                continue
            hm = hhmm[ix]
            for r in g.itertuples():
                out, base = {}, None
                for name, v in VARS.items():
                    rk = new_risk(float(r.entry), float(r.risk), v)
                    if name != "BASE" and rk == float(r.risk):
                        out[name] = base + (rk,)
                        continue
                    w = walk(int(r.side), float(r.entry), rk, TGT_MULT[r.setup], int(r.tod), hm, O[ix], H[ix], Lo[ix], C[ix])
                    if w is None:
                        break
                    if name == "BASE":
                        base = w
                    out[name] = w + (rk,)
                if len(out) == len(VARS):
                    res.append((r.Index, out))
    return res


if __name__ == "__main__":
    CAND, OUT = Path(sys.argv[1]), Path(sys.argv[2])
    OUT.mkdir(parents=True, exist_ok=True)
    c = pd.read_parquet(CAND)
    c = c[c.setup.isin(PRIMARY4)].reset_index(drop=True)
    no_locked(c.date.unique())
    W = {}
    with Pool(4) as p:
        for res in p.imap_unordered(job, [(s, g) for s, g in c.groupby("symbol")], chunksize=8):
            for i, w in res:
                W[i] = w
    c = c[c.index.isin(W.keys())].copy()
    for k in VARS:
        c[f"px_{k}"] = [W[i][k][0] for i in c.index]
        c[f"kind_{k}"] = [W[i][k][1] for i in c.index]
        xt = np.array([W[i][k][2] for i in c.index])
        c[f"xm_{k}"] = (xt // 100) * 60 + xt % 100
        c[f"rk_{k}"] = [W[i][k][3] for i in c.index]
    c.reset_index(drop=True).to_parquet(OUT / "walk.parquet", index=False)
    print("lots", len(c), "parity xm", float((c.xm_BASE == c.xm).mean()))
