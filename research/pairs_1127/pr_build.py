"""PAIRS-1127 builder: 1-min SIP caches -> per-symbol 5-minute arrays (close, first-minute open, second-minute open) on a
fixed session calendar, plus daily dollar volume. Never reads the locked block 2024-11-01..2025-02-28 (row filter + assert).
Usage: python pr_build.py OUTDIR   (outputs are scratch, not committed). Educational only - not financial advice."""
from __future__ import annotations
import sys
from datetime import date
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

DATA = Path("/home/user/MCF/data")
SRC = [DATA / "cache_fresh" / "1Min", DATA / "cache_hist" / "1Min"]
TZ = "America/New_York"
LOCK_A, LOCK_B = date(2024, 11, 1), date(2025, 2, 28)
RANGES = [("2022-10-01", "2024-11-01"), ("2025-03-01", "2026-11-05")]
HALF_DAYS = {pd.Timestamp(x).date() for x in ["2022-11-25", "2023-07-03", "2023-11-24", "2024-07-03", "2024-11-29",
                                              "2024-12-24", "2025-07-03", "2025-11-28", "2025-12-24"]}
NB = 78


def read_sym(sym):
    parts = []
    for base in SRC:
        f = base / f"{sym}.parquet"
        if not f.exists():
            continue
        names = pq.read_schema(f).names
        col = "__index_level_0__" if "__index_level_0__" in names else "timestamp"
        for a, b in RANGES:
            df = pq.read_table(f, columns=["open", "close", "volume", col],
                               filters=[(col, ">=", pd.Timestamp(a, tz=TZ)), (col, "<", pd.Timestamp(b, tz=TZ))]).to_pandas()
            if col in df.columns:
                df = df.set_index(col)
            if len(df):
                parts.append(df)
    if not parts:
        return None
    df = pd.concat(parts)
    df.index = pd.DatetimeIndex(df.index).tz_convert(TZ)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    dd = df.index.date
    assert not ((dd >= LOCK_A) & (dd <= LOCK_B)).any(), "locked block read"
    m = df.index.hour * 60 + df.index.minute
    return df[(m >= 570) & (m < 960)]


def build(sym, cal, out):
    df = read_sym(sym)
    if df is None or len(df) < 1000:
        return sym, 0
    di = {d: i for i, d in enumerate(cal)}
    d = pd.Series(df.index.date).map(di)
    keep = d.notna().to_numpy()
    df = df[keep]; d = d[keep].astype(int).to_numpy()
    m = (df.index.hour * 60 + df.index.minute).to_numpy()
    b = (m - 570) // 5
    D = len(cal)
    C = np.full((D, NB), np.nan, np.float32); O1 = C.copy(); O2 = C.copy()
    key = d * NB + b
    o = df.open.to_numpy(); c = df.close.to_numpy(); v = df.volume.to_numpy()
    # rows are time-sorted: first / second / last per key
    first = np.r_[True, key[1:] != key[:-1]]
    last = np.r_[key[1:] != key[:-1], True]
    fi = np.nonzero(first)[0]
    C.flat[key[last]] = c[last]
    O1.flat[key[fi]] = o[fi]
    sec = fi + 1
    ok = (sec < len(key)) & (key[np.minimum(sec, len(key) - 1)] == key[fi])
    O2.flat[key[fi[ok]]] = o[sec[ok]]
    O2.flat[key[fi[~ok]]] = c[fi[~ok]]
    dv = np.bincount(d, weights=c * v, minlength=D).astype(np.float64)
    nbars = np.bincount(d, minlength=D)
    np.savez_compressed(out / f"{sym}.npz", C=C, O1=O1, O2=O2, dv=dv, nmin=nbars)
    return sym, int((nbars > 0).sum())


def _w(a):
    try:
        return build(*a)
    except Exception as ex:  # noqa: BLE001
        print("ERR", a[0], ex, flush=True)
        return a[0], -1


def main(outdir):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    spy = read_sym("SPY")
    cal = sorted(set(spy.index.date) - HALF_DAYS)
    cal = [x for x in cal if not (LOCK_A <= x <= LOCK_B)]
    np.save(out / "_cal.npy", np.array([x.isoformat() for x in cal]))
    syms = sorted({p.stem for s in SRC for p in s.glob("*.parquet")})
    print("sessions", len(cal), "symbols", len(syms), flush=True)
    with Pool(4) as pool:
        for i, (s, n) in enumerate(pool.imap_unordered(_w, [(s, cal, out) for s in syms], chunksize=4)):
            if i % 100 == 0:
                print(i, s, n, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
