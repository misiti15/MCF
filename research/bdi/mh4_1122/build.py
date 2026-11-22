"""BDI-MH4 1122 build: one pass over the 1-minute caches -> per symbol-day 09:50 decision row + exit outcomes.

  python build.py WORK t1     data/cache_hist/1Min   (locked block 2024-11-01..2025-02-28 filtered out + asserted)
  python build.py WORK t2     data/cache_fresh/1Min  (2022-10-03..2024-09-13)
Outputs WORK/rows_{t1,t2}.parquet: symbol, date, pc, open, c950, atr_d, adv20, gap, move, fo, and for side in (L, S),
exit in (t1s1, hold): px_, kind_ (1 stop, 2 target, 0 time), xt_ (HHMM). Also WORK/daily_{t}.parquet (symbol, date, close).
Conventions: research/ultimate_1119/top10/bench10.py (decision bar close; stop first; target through by $0.01; flat 15:55)
and mcf/research/heat.py (atr_d, gap). Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
SRC = {"t1": Path("/home/user/MCF/data/cache_hist/1Min"), "t2": Path("/home/user/MCF/data/cache_fresh/1Min")}
TOD = 950


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load(test, sym):
    p = SRC[test] / f"{sym}.parquet"
    if test == "t1":
        fld = pads.field("__index_level_0__")
        L0, L1 = pd.Timestamp(LOCK[0], tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
        b = pads.dataset(str(p), format="parquet").to_table(filter=(fld < L0) | (fld >= L1)).to_pandas()
        if "__index_level_0__" in b.columns:
            b = b.set_index("__index_level_0__")
    else:
        b = pd.read_parquet(p)
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    no_locked(np.unique(b.index.date.astype(str)))
    if test == "t2":
        ds = sorted(set(b.index.date.astype(str)))
        assert ds[0] >= "2022-10-03" and ds[-1] <= "2024-09-13"
    return b


def walk(e, R, side, tgt_on, O, H, L, C, hm):
    """minutes from the decision bar on (hm >= 950); returns px, kind, xt"""
    sel = hm < 1555
    stop = e - side * R
    if side == 1:
        hs = np.flatnonzero(L[sel] <= stop)
        ht = np.flatnonzero(H[sel] >= e + R + 0.01) if tgt_on else np.zeros(0, int)
    else:
        hs = np.flatnonzero(H[sel] >= stop)
        ht = np.flatnonzero(L[sel] <= e - R - 0.01) if tgt_on else np.zeros(0, int)
    ks = hs[0] if len(hs) else 10 ** 9
    kt = ht[0] if len(ht) else 10 ** 9
    if ks < 10 ** 9 and ks <= kt:
        px = min(O[ks], stop) if side == 1 else max(O[ks], stop)
        return px, 1, hm[ks]
    if kt < 10 ** 9:
        return e + side * R, 2, hm[kt]
    after = np.flatnonzero(~sel)
    if len(after):
        return O[after[0]], 0, 1555
    n = int(sel.sum())
    if n:
        return C[n - 1], 0, hm[n - 1] + 1
    return np.nan, -1, -1


def job(args):
    test, sym = args
    try:
        b = load(test, sym)
    except Exception as ex:  # noqa: BLE001
        return sym, None, None
    if len(b) < 2000:
        return sym, None, None
    day = b.index.date.astype(str)
    hm = (b.index.hour * 100 + b.index.minute).to_numpy()
    O, H, L, C, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    g = pd.DataFrame({"date": day, "o": O, "h": H, "l": L, "c": C, "dv": C * V}).groupby("date", sort=True)
    d = pd.DataFrame({"open": g.o.first(), "high": g.h.max(), "low": g.l.min(), "close": g.c.last(), "dv": g.dv.sum()})
    dt = pd.to_datetime(d.index)
    seg = np.cumsum(np.r_[True, np.diff(dt.values).astype("timedelta64[D]").astype(int) > 10])
    d["seg"] = seg
    d["pc"] = d.groupby("seg").close.shift(1)
    tr = pd.concat([d.high - d.low, (d.high - d.pc).abs(), (d.low - d.pc).abs()], axis=1).max(axis=1)
    tr[d.pc.isna()] = np.nan
    d["tr"] = tr
    d["atr_d"] = d.groupby("seg").tr.transform(lambda s: s.rolling(14, min_periods=10).mean().shift(1))
    d["adv20"] = d.groupby("seg").dv.transform(lambda s: s.shift(1).rolling(20, min_periods=5).mean())
    daily = pd.DataFrame({"symbol": sym, "date": d.index, "close": d.close.to_numpy(), "seg": seg})
    starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    ends = np.r_[starts[1:], len(day)]
    rows = []
    for a, z in zip(starts, ends):
        dd = day[a]
        r = d.loc[dd]
        if not (r.atr_d > 0) or not np.isfinite(r.pc):
            continue
        h = hm[a:z]
        pre = np.flatnonzero(h < TOD)
        post = np.flatnonzero(h >= TOD)
        if not len(pre) or not len(post) or h[pre[-1]] < 940:
            continue
        e = C[a + pre[-1]]
        R = 0.25 * r.atr_d
        sl = slice(a + post[0], z)
        rec = {"date": dd, "pc": r.pc, "open": r.open, "c950": e, "atr_d": r.atr_d, "adv20": r.adv20}
        for side, sn in ((1, "L"), (-1, "S")):
            for ex, tg in (("t1s1", True), ("hold", False)):
                px, k, xt = walk(e, R, side, tg, O[sl], H[sl], L[sl], C[sl], hm[sl])
                rec[f"px_{sn}_{ex}"], rec[f"kind_{sn}_{ex}"], rec[f"xt_{sn}_{ex}"] = px, k, xt
        rows.append(rec)
    if not rows:
        return sym, None, daily
    x = pd.DataFrame(rows)
    x.insert(0, "symbol", sym)
    x["gap"] = (x.open / x.pc - 1) * 100
    x["move"] = (x.c950 - x.pc) / x.atr_d
    x["fo"] = (x.c950 / x.open - 1) * 100
    return sym, x, daily


if __name__ == "__main__":
    W, test = Path(sys.argv[1]), sys.argv[2]
    syms = sorted(p.stem for p in SRC[test].glob("*.parquet"))
    out, dly = [], []
    with Pool(4) as p:
        for i, (s, x, dl) in enumerate(p.imap_unordered(job, [(test, s) for s in syms], chunksize=4)):
            if x is not None:
                out.append(x)
            if dl is not None:
                dly.append(dl)
            if i % 200 == 0:
                print(i, flush=True)
    X = pd.concat(out, ignore_index=True)
    no_locked(X.date.unique())
    for c in X.columns:
        if X[c].dtype == "float64" and c not in ("c950", "pc", "open", "atr_d") and not c.startswith("px_"):
            X[c] = X[c].astype("float32")
    X.to_parquet(W / f"rows_{test}.parquet")
    pd.concat(dly, ignore_index=True).to_parquet(W / f"daily_{test}.parquet")
    print(test, len(X), "rows", X.symbol.nunique(), "symbols", X.date.min(), X.date.max())
