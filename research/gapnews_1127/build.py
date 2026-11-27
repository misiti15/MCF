"""GAPNEWS_1127 build: per symbol-day 09:50 features (MOVEHUNT set + direction features), the remaining-move target and
candidate trades for both sides (X1 range stop, X2 0.5 ATR stop; entry 09:50 and 09:51) plus the N1/N2 OCO bracket.
Selection (K6 list) happens in score.py. Locked block 2024-11-01..2025-02-28 never read.
Usage: python build.py OUTDIR. Educational only - not financial advice."""
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


def sim(o, h, l, c, i0, side, stop, iexit, chk_entry_bar=True):
    """entry at o[i0] (caller passes price separately for brackets); stop-first; gap through stop fills at open."""
    for i in range(i0, iexit + 1):
        if side > 0:
            if o[i] <= stop and (i > i0 or chk_entry_bar):
                return o[i], 1
            if l[i] <= stop:
                return stop, 1
        else:
            if o[i] >= stop and (i > i0 or chk_entry_bar):
                return o[i], 1
            if h[i] >= stop:
                return stop, 1
    return c[iexit], 0


def bars(b):
    mmall = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
    keep = (mmall >= 0) & (mmall < 390)
    b = b[keep]
    return b, mmall[keep]


def pass1(sym, b):
    b, mmall = bars(b)
    dates = b.index.date.astype(str)
    O, H, L, C, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    rows = []
    starts = np.flatnonzero(np.r_[True, dates[1:] != dates[:-1]])
    ends = np.r_[starts[1:], len(dates)]
    for s, e in zip(starts, ends):
        o, h, l, c, v, mm = O[s:e], H[s:e], L[s:e], C[s:e], V[s:e], mmall[s:e]
        r = {"symbol": sym, "date": dates[s], "d_open": o[0], "d_high": h.max(), "d_low": l.min(), "d_close": c[-1],
             "dvol": float((c * v).sum()), "last_mm": int(mm[-1]), "s": int(s)}
        w = mm < 20
        r["n20"] = int(w.sum())
        if r["n20"] >= 1 and (mm >= 20).any():
            r["open"] = o[0] if mm[0] == 0 else np.nan
            r["p50"] = c[w][-1]
            r["h20"], r["l20"], r["v20"] = h[w].max(), l[w].min(), v[w].sum()
            tp = (h[w] + l[w] + c[w]) / 3
            r["vwap20"] = float((tp * v[w]).sum() / v[w].sum()) if v[w].sum() > 0 else np.nan
            up, dn = c[w] > o[w], c[w] < o[w]
            r["vimb"] = float((v[w][up].sum() - v[w][dn].sum()) / v[w].sum()) if v[w].sum() > 0 else np.nan
            a = mm >= 20
            r["i0"] = int(np.flatnonzero(a)[0])
            r["ie"] = int(np.flatnonzero(mm <= 385)[-1])
            r["i0_mm"] = int(mm[r["i0"]])
        rows.append(r)
    return pd.DataFrame(rows)


def daily_feats(df):
    df = df.sort_values("date").reset_index(drop=True)
    dd = pd.to_datetime(df.date)
    seg = (dd.diff().dt.days.fillna(99) > 7).cumsum()
    g = lambda x: x.groupby(seg)  # noqa: E731
    pc = g(df.d_close).shift(1)
    tr = np.maximum(df.d_high, pc) - np.minimum(df.d_low, pc)
    tr = tr.where(pc.notna(), df.d_high - df.d_low)
    df["prev_close"] = pc
    df["atr"] = g(tr).transform(lambda x: x.shift(1).rolling(14, min_periods=14).mean())
    df["adv20"] = g(df.dvol).transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean())
    df["v20_med"] = g(df.v20).transform(lambda x: x.shift(1).rolling(20, min_periods=15).median())
    df["pdr_raw"] = g(df.d_high - df.d_low).shift(1)
    pdh, pdl = g(df.d_high).shift(1), g(df.d_low).shift(1)
    df["pcl"] = (pc - pdl) / (pdh - pdl)
    df["r5"] = pc / g(df.d_close).shift(6) - 1
    df["r20d"] = pc / g(df.d_close).shift(21) - 1
    df["cc_ret"] = df.d_close / pc - 1       # used only as a lagged input (prior 60 days) for the ETF map in score.py
    return df


def pass2(b, df):
    b, mmall = bars(b)
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    cols = {}
    def put(k, n, val):  # noqa: E306
        cols.setdefault(k, np.full(len(df), np.nan))[n] = val
    for n, r in enumerate(df.itertuples()):
        if not (r.atr == r.atr) or r.atr <= 0 or not (r.i0 == r.i0):
            continue
        s, i0, ie = int(r.s), int(r.s) + int(r.i0), int(r.s) + int(r.ie)
        if ie < i0:
            continue
        for lag in (0, 1):
            j = i0 + lag
            if j > ie:
                continue
            ent = O[j]
            for side, sn in ((1, "L"), (-1, "S")):
                st1 = (min(r.l20, ent - 0.10 * r.atr) - 0.01) if side > 0 else (max(r.h20, ent + 0.10 * r.atr) + 0.01)
                st2 = ent - side * 0.50 * r.atr
                for xn, st in (("x1", st1), ("x2", st2)):
                    px, k = sim(O, H, L, C, j, side, st, ie)
                    tag = f"{xn}{sn}{lag}"
                    put(f"{tag}_e", n, ent); put(f"{tag}_st", n, st); put(f"{tag}_px", n, px); put(f"{tag}_k", n, k)  # noqa: E702
        # OCO bracket on the 09:30-09:49 range, live 09:50-11:29
        mm = mmall[s:]
        lim_end = s + int(np.flatnonzero(mm[: ie - s + 1] < 120)[-1])
        bu, bd = r.h20 + 0.01, r.l20 - 0.01
        for i in range(i0, min(lim_end, ie) + 1):
            hu, hd = H[i] >= bu, L[i] <= bd
            if not (hu or hd):
                continue
            if hu and hd and not (O[i] >= bu or O[i] <= bd):
                put("nb_both", n, 1)
                side = 1 if (O[i] - r.l20) > (r.h20 - O[i]) else -1   # nearer trigger fills first (scored as -1R anyway)
            else:
                side = 1 if (hu and (O[i] >= bu or not hd)) else -1
            put("nb_side", n, side)
            put("nb_mm", n, mmall[i])
            ent = max(O[i], bu) if side > 0 else min(O[i], bd)
            for xn, st in (("n1", (r.h20 + r.l20) / 2), ("n2", bd if side > 0 else bu)):
                px, k = sim(O, H, L, C, i, side, st, ie, chk_entry_bar=True)
                put(f"{xn}0_e", n, ent); put(f"{xn}0_st", n, st); put(f"{xn}0_px", n, px); put(f"{xn}0_k", n, k)  # noqa: E702
                if i + 1 <= ie:   # +1 minute: market order at the next bar open
                    e1 = O[i + 1]
                    px, k = sim(O, H, L, C, i + 1, side, st, ie)
                    put(f"{xn}1_e", n, e1); put(f"{xn}1_st", n, st); put(f"{xn}1_px", n, px); put(f"{xn}1_k", n, k)  # noqa: E702
            break
    for k, v in cols.items():
        df[k] = v
    return df


def job(args):
    era, p = args
    sym = p.stem
    try:
        b = load(p)
        if len(b) < 1000:
            return None
        no_locked(np.unique(b.index.date.astype(str)))
        df = pass1(sym, b)
        if not len(df) or "p50" not in df:
            return None
        df = daily_feats(df)
        df = pass2(b, df)
        df["era"] = era
        return df.drop(columns=["s"])
    except Exception as ex:  # noqa: BLE001
        print("ERR", sym, ex, flush=True)
        return None


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[2:]   # optional symbol subset for a smoke test
    for era, src in SRC.items():
        files = sorted(src.glob("*.parquet"))
        if only:
            files = [f for f in files if f.stem in only]
        with Pool(4) as pool:
            parts = [x for x in pool.imap_unordered(job, [(era, f) for f in files], chunksize=4) if x is not None]
        df = pd.concat(parts, ignore_index=True)
        no_locked(df.date.unique())
        df.to_parquet(OUT / f"days_{era}.parquet", index=False)
        print(era, len(df), df.symbol.nunique(), flush=True)
