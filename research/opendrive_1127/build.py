"""OPENDRIVE_1127 build: per symbol-day, for decision times T = 09:35/09:40/09:45/09:50, the window features (bars before T
only), the entry-bar 1-min range (spread proxy), and for both directions the trade outcome (entry at the T bar open and at
T+1 for the stress), stop = opposite window extreme -+ 1c widened to >= 0.15 ATR, stop-first, time exit 15:55.
Locked block 2024-11-01..2025-02-28 never read. Usage: python build.py OUTDIR. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
SRC = {"t1": Path("/home/user/MCF/data/cache_hist/1Min"), "t2": Path("/home/user/MCF/data/cache_fresh/1Min")}
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
TS = (5, 10, 15, 20)


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load(p):
    f = pads.field("__index_level_0__")
    flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
    b = pads.dataset(str(p), format="parquet").to_table(filter=flt).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    return b.sort_index()


def sim(o, h, l, c, i0, ie, side, stop):
    """entry o[i0]; stop-first; gap through stop fills at the open; else close of ie. returns (px, kind)."""
    if side > 0:
        hit = np.flatnonzero(l[i0:ie + 1] <= stop)
        if len(hit):
            i = i0 + hit[0]
            return (o[i] if o[i] <= stop else stop), 1
    else:
        hit = np.flatnonzero(h[i0:ie + 1] >= stop)
        if len(hit):
            i = i0 + hit[0]
            return (o[i] if o[i] >= stop else stop), 1
    return c[ie], 0


def job(args):
    era, p = args
    sym = p.stem
    try:
        b = load(p)
        if len(b) < 1000:
            return None
        mm = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
        k = (mm >= 0) & (mm < 390)
        b, mm = b[k], mm[k]
        dates = b.index.date.astype(str)
        no_locked(np.unique(dates))
        O, H, L, C, V = (b[c].to_numpy(float) for c in ("open", "high", "low", "close", "volume"))
        starts = np.flatnonzero(np.r_[True, dates[1:] != dates[:-1]])
        ends = np.r_[starts[1:], len(dates)]
        rows = []
        for s, e in zip(starts, ends):
            o, h, l, c, v, m = O[s:e], H[s:e], L[s:e], C[s:e], V[s:e], mm[s:e]
            r = {"symbol": sym, "date": dates[s], "d_open": o[0], "d_high": h.max(), "d_low": l.min(), "d_close": c[-1],
                 "dvol": float((c * v).sum()), "last_mm": int(m[-1]), "open": o[0] if m[0] == 0 else np.nan}
            ie = np.flatnonzero(m <= 385)
            r["ie"] = int(ie[-1]) if len(ie) else -1
            r["c_ie"] = c[r["ie"]] if r["ie"] >= 0 else np.nan
            for T in TS:
                w = m < T
                n = int(w.sum())
                r[f"n{T}"] = n
                if n == 0 or not (m >= T).any():
                    continue
                r[f"p{T}"], r[f"h{T}"], r[f"l{T}"], r[f"v{T}"] = c[w][-1], h[w].max(), l[w].min(), v[w].sum()
                i0 = np.flatnonzero(m >= T)[0]
                r[f"i{T}"], r[f"em{T}"], r[f"e{T}"] = int(i0), int(m[i0]), o[i0]
                r[f"br{T}"] = (h[i0] - l[i0]) / c[i0] if c[i0] > 0 else np.nan
                if i0 + 1 < len(m):
                    r[f"e1{T}"] = o[i0 + 1]
            rows.append(r)
        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
        # daily features (prior days only)
        dd = pd.to_datetime(df.date)
        seg = (dd.diff().dt.days.fillna(99) > 7).cumsum()
        pc = df.groupby(seg).d_close.shift(1)
        tr = np.maximum(df.d_high, pc) - np.minimum(df.d_low, pc)
        tr = tr.where(pc.notna(), df.d_high - df.d_low)
        g = lambda x: x.groupby(seg)  # noqa: E731
        df["prev_close"] = pc
        df["atr"] = g(tr).transform(lambda x: x.shift(1).rolling(14, min_periods=14).mean())
        df["adv20"] = g(df.dvol).transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean())
        df["pdr_raw"] = g(df.d_high - df.d_low).shift(1)
        for T in TS:
            if f"v{T}" not in df:
                df[f"v{T}"] = np.nan
            df[f"vmed{T}"] = g(df[f"v{T}"]).transform(lambda x: x.shift(1).rolling(20, min_periods=15).median())
        # trades: both directions per T, entry at T and T+1 (stress)
        pos = dict(zip(dates[starts], starts))
        out = {}
        for T in TS:
            for d, nm in ((1, "L"), (-1, "S")):
                for col in (f"st{T}{nm}", f"px{T}{nm}", f"k{T}{nm}", f"px1{T}{nm}", f"k1{T}{nm}"):
                    out[col] = np.full(len(df), np.nan, dtype=np.float32 if col.startswith("k") else float)
        for n, r in enumerate(df.itertuples(index=False)):
            if not (r.atr == r.atr) or r.atr <= 0 or r.ie < 0 or not (r.adv20 == r.adv20) or r.adv20 < 15e6:
                continue
            s = pos[r.date]
            for T in TS:
                i0 = getattr(r, f"i{T}", np.nan)
                if not (i0 == i0) or i0 > r.ie:
                    continue
                i0 = int(i0)
                ent = getattr(r, f"e{T}")
                hT, lT = getattr(r, f"h{T}"), getattr(r, f"l{T}")
                for d, nm in ((1, "L"), (-1, "S")):
                    st = min(lT - 0.01, ent - 0.15 * r.atr) if d > 0 else max(hT + 0.01, ent + 0.15 * r.atr)
                    out[f"st{T}{nm}"][n] = st
                    if d * (ent - st) <= 0:
                        continue
                    px, kk = sim(O, H, L, C, s + i0, s + r.ie, d, st)
                    out[f"px{T}{nm}"][n], out[f"k{T}{nm}"][n] = px, kk
                    e1 = getattr(r, f"e1{T}", np.nan)
                    if e1 == e1 and i0 + 1 <= r.ie and d * (e1 - st) > 0:
                        px, kk = sim(O, H, L, C, s + i0 + 1, s + r.ie, d, st)
                        out[f"px1{T}{nm}"][n], out[f"k1{T}{nm}"][n] = px, kk
        for c_, v_ in out.items():
            df[c_] = v_
        df["era"] = era
        drop = [c_ for c_ in df.columns if c_.startswith("i") and c_[1:].isdigit()] + ["d_high", "d_low", "dvol"]
        df = df.drop(columns=drop)
        fl = df.select_dtypes("float64").columns
        keep64 = [c_ for c_ in fl if c_.startswith(("px", "st", "e", "p", "h", "l", "open", "prev", "d_", "c_ie", "atr"))]
        df[[c_ for c_ in fl if c_ not in keep64]] = df[[c_ for c_ in fl if c_ not in keep64]].astype(np.float32)
        return df
    except Exception as ex:  # noqa: BLE001
        print("ERR", sym, repr(ex), flush=True)
        return None


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for era, src in SRC.items():
        files = sorted(src.glob("*.parquet"))
        if len(sys.argv) > 2:
            files = files[: int(sys.argv[2])]
        with Pool(4) as pool:
            parts = [x for x in pool.imap_unordered(job, [(era, f) for f in files], chunksize=4) if x is not None]
        df = pd.concat(parts, ignore_index=True)
        no_locked(df.date.unique())
        df.to_parquet(OUT / f"days_{era}.parquet", index=False)
        print(era, len(df), df.symbol.nunique(), flush=True)
