"""MOVEHUNT_1127 build: per symbol-day 09:50 features, the after-09:50 target and the S1/S2/S3 candidate trades
(every symbol-day; selection by ranker happens in score.py). Locked block 2024-11-01..2025-02-28 never read.
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
    b = b.sort_index()
    return b


def sim(o, h, l, c, mm, i0, side, stop, iexit):
    """walk from bar i0 (entry at o[i0]) to bar iexit inclusive; stop-first; gap through stop fills at open."""
    for i in range(i0, iexit + 1):
        if side > 0:
            if o[i] <= stop:
                return o[i], 1, mm[i]
            if l[i] <= stop:
                return stop, 1, mm[i]
        else:
            if o[i] >= stop:
                return o[i], 1, mm[i]
            if h[i] >= stop:
                return stop, 1, mm[i]
    return c[iexit], 0, mm[iexit]


def day_rows(sym, b):
    mmall = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
    keep = (mmall >= 0) & (mmall < 390)
    b = b[keep]
    mmall = mmall[keep]
    dates = b.index.date.astype(str)
    O, H, L, C, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    rows = []
    starts = np.flatnonzero(np.r_[True, dates[1:] != dates[:-1]])
    ends = np.r_[starts[1:], len(dates)]
    for s, e in zip(starts, ends):
        d = dates[s]
        o, h, l, c, v, mm = O[s:e], H[s:e], L[s:e], C[s:e], V[s:e], mmall[s:e]
        r = {"symbol": sym, "date": d, "d_open": o[0], "d_high": h.max(), "d_low": l.min(), "d_close": c[-1],
             "dvol": float((c * v).sum()), "last_mm": int(mm[-1])}
        w = mm < 20
        r["n20"] = int(w.sum())
        if r["n20"] >= 1 and (mm >= 20).any():
            r["open"] = o[0] if mm[0] == 0 else np.nan
            r["p50"] = c[w][-1]
            r["h20"], r["l20"], r["v20"] = h[w].max(), l[w].min(), v[w].sum()
            a = mm >= 20
            r["post_h"], r["post_l"] = h[a].max(), l[a].min()
            ie = np.flatnonzero(mm <= 385)[-1]          # 15:55 bar close, or last bar on a half day
            i0 = np.flatnonzero(a)[0]
            r["i0_mm"] = int(mm[i0])
            r["entry"] = o[i0]
            D = np.sign(r["p50"] - (r["open"] if r["open"] == r["open"] else o[0]))
            r["D"] = D
            if D != 0 and ie >= i0:
                rng_mid = (r["h20"] + r["l20"]) / 2
                # S1 CONT
                st = r["l20"] - 0.01 if D > 0 else r["h20"] + 0.01
                px, k, xt = sim(o, h, l, c, mm, i0, D, st, ie)
                r.update(s1_stop=st, s1_px=px, s1_kind=k, s1_xm=xt)
                # S2 FADE (ATR buffer applied later? needs ATR: store extreme; sim done in pass 2) -> store index info
                r["i0"], r["ie"] = int(i0), int(ie)
                # S3 ORB
                lim = np.flatnonzero((mm >= 20) & (mm < 120))
                hit = lim[(c[lim] > r["h20"]) if D > 0 else (c[lim] < r["l20"])]
                if len(hit) and hit[0] + 1 <= ie:
                    j = hit[0] + 1
                    px, k, xt = sim(o, h, l, c, mm, j, D, rng_mid, ie)
                    r.update(s3_entry=o[j], s3_em=int(mm[j]), s3_stop=rng_mid, s3_px=px, s3_kind=k, s3_xm=xt)
        rows.append(r)
    return pd.DataFrame(rows)


def fade_pass(sym, b, df):
    """S2 FADE needs ATR (from the daily pass): stop = first-move extreme +- 0.10 ATR, risk floored at 0.10 ATR."""
    mmall = (b.index.hour * 60 + b.index.minute).to_numpy() - 570
    keep = (mmall >= 0) & (mmall < 390)
    b = b[keep]
    mmall = mmall[keep]
    dates = b.index.date.astype(str)
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    starts = np.flatnonzero(np.r_[True, dates[1:] != dates[:-1]])
    pos = {dates[s]: s for s in starts}
    out = {k: np.full(len(df), np.nan) for k in ("s2_stop", "s2_px", "s2_kind", "s2_xm")}
    for n, r in enumerate(df.itertuples()):
        if not (r.atr == r.atr) or not (r.D == r.D) or r.D == 0 or not (r.i0 == r.i0):
            continue
        s = pos[r.date]
        side = -r.D
        ent = r.entry
        if side < 0:     # first move up -> short; stop above the 20-min high
            st = max(r.h20 + 0.10 * r.atr, ent + 0.10 * r.atr)
        else:
            st = min(r.l20 - 0.10 * r.atr, ent - 0.10 * r.atr)
        i0, ie = s + int(r.i0), s + int(r.ie)
        px, k, xt = sim(O, H, L, C, mmall, i0, side, st, ie)
        out["s2_stop"][n], out["s2_px"][n], out["s2_kind"][n], out["s2_xm"][n] = st, px, k, xt
    for k, v in out.items():
        df[k] = v
    return df


def daily_feats(df):
    df = df.sort_values("date").reset_index(drop=True)
    dd = pd.to_datetime(df.date)
    seg = (dd.diff().dt.days.fillna(99) > 7).cumsum()
    pc = df.groupby(seg).d_close.shift(1)
    tr = np.maximum(df.d_high, pc) - np.minimum(df.d_low, pc)
    tr = tr.where(pc.notna(), df.d_high - df.d_low)
    g = lambda x: x.groupby(seg)  # noqa: E731
    df["prev_close"] = pc
    df["atr"] = g(tr).transform(lambda x: x.shift(1).rolling(14, min_periods=14).mean())
    df["adv20"] = g(df.dvol).transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean())
    df["v20_med"] = g(df.v20).transform(lambda x: x.shift(1).rolling(20, min_periods=15).median())
    df["pdr_raw"] = g(df.d_high - df.d_low).shift(1)
    df["n_prior"] = g(df.date).cumcount()
    return df


def job(args):
    era, p = args
    sym = p.stem
    try:
        b = load(p)
        if len(b) < 1000:
            return None
        no_locked(np.unique(b.index.date.astype(str)))
        df = day_rows(sym, b)
        if not len(df) or "p50" not in df:
            return None
        df = daily_feats(df)
        df = fade_pass(sym, b, df)
        df["era"] = era
        return df
    except Exception as ex:  # noqa: BLE001
        print("ERR", sym, ex, flush=True)
        return None


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for era, src in SRC.items():
        files = sorted(src.glob("*.parquet"))
        with Pool(4) as pool:
            parts = [x for x in pool.imap_unordered(job, [(era, f) for f in files], chunksize=4) if x is not None]
        df = pd.concat(parts, ignore_index=True)
        no_locked(df.date.unique())
        df.to_parquet(OUT / f"days_{era}.parquet", index=False)
        print(era, len(df), df.symbol.nunique(), flush=True)
