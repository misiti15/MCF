"""IDXHEDGE-1127 index inputs (PREREG.md): SPY / QQQ 1-min close grids (390 bars from 09:30) with SPY session VWAP,
calendar close per day (half days: bars at/after 13:00 dropped), QQQ point-in-time 60-session beta to SPY, and gd_share
(share of the 469-name universe gapping down >= 1% at the open). GET-free (local caches only). Locked block
2024-11-01..2025-02-28 filtered at read and asserted absent.
Usage (cwd repo): python research/idxhedge_1127/ih_index.py OUTDIR. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads

sys.path.insert(0, "."); sys.path.insert(0, "research/idxdip_1127")
from idx_sim import close_for  # noqa: E402  (calendar close incl. pre-2024 half days)

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load(p):
    if not p.exists():
        return None
    f = pads.field("__index_level_0__")
    flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
    b = pads.dataset(str(p), format="parquet").to_table(filter=flt).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index(); b = b[~b.index.duplicated(keep="last")]
    mm = b.index.hour * 60 + b.index.minute
    b = b[(mm >= 570) & (mm < 960)]
    d = b.index.date.astype(str)
    b = b[~((d >= LOCK[0]) & (d <= LOCK[1]))]
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def sym_frame(sym):
    parts = []
    for src, lo, hi in ((FRESH, "0000", "2024-09-14"), (HIST, "2024-09-14", "9999")):
        b = load(src / f"{sym}.parquet")
        if b is None:
            continue
        d = b.index.date.astype(str)
        parts.append(b[(d >= lo) & (d < hi)])
    b = pd.concat(parts)
    d = b.index.date.astype(str)
    mm = (b.index.hour * 60 + b.index.minute).to_numpy()
    CL = {x: close_for(x) for x in np.unique(d)}
    cl = np.array([CL[x] for x in d])
    return b[mm < cl], CL


def grids(sym, CL):
    b, _ = sym_frame(sym)
    d = b.index.date.astype(str)
    out = {}
    for day, g in b.groupby(d):
        mm = (g.index.hour * 60 + g.index.minute).to_numpy() - 570
        c = np.full(390, np.nan); v = np.zeros(390); tp = np.full(390, np.nan)
        c[mm] = g.close.to_numpy(float); v[mm] = g.volume.to_numpy(float)
        tp[mm] = ((g.high + g.low + g.close) / 3).to_numpy(float)
        ncl = CL[day] - 570
        cf = pd.Series(c[:ncl]).ffill().bfill().to_numpy()
        tpv = np.nan_to_num(tp[:ncl]) * v[:ncl]
        cv = np.cumsum(v[:ncl])
        vw = np.where(cv > 0, np.cumsum(tpv) / np.where(cv > 0, cv, 1), np.nan)
        vw = pd.Series(vw).ffill().bfill().to_numpy()
        C = np.full(390, np.nan); V = np.full(390, np.nan); C[:ncl] = cf; V[:ncl] = vw
        out[day] = (C, V)
    return out


def gap_job(sym):
    rows = []
    try:
        b, CL = sym_frame(sym)
    except Exception:
        return rows
    d = b.index.date.astype(str)
    g = pd.DataFrame({"o": b.open.to_numpy(float), "c": b.close.to_numpy(float), "d": d})
    agg = g.groupby("d").agg(o=("o", "first"), c=("c", "last")).reset_index()
    agg["dt"] = pd.to_datetime(agg.d)
    agg["pc"] = agg.c.shift(1)
    agg.loc[agg.dt.diff().dt.days > 5, "pc"] = np.nan
    agg["gd"] = agg.o <= 0.99 * agg.pc
    agg = agg[agg.pc.notna()]
    return list(zip(agg.d, agg.gd.astype(int)))


if __name__ == "__main__":
    uni = sorted(p.stem for p in FRESH.glob("*.parquet"))
    print("universe", len(uni), flush=True)
    _, CL = sym_frame("SPY")
    S = grids("SPY", CL); Q = grids("QQQ", CL)
    D = sorted(set(S) & set(Q)); no_locked(D)
    np.save(OUT / "spy.npy", np.stack([np.stack(S[d]) for d in D]))
    np.save(OUT / "qqq.npy", np.stack([Q[d][0] for d in D]))
    # QQQ beta to SPY, 60 sessions, point in time (strictly before the day), no bridge over > 5-day gaps
    sc = pd.Series({d: S[d][0][~np.isnan(S[d][0])][-1] for d in D}); qc = pd.Series({d: Q[d][0][~np.isnan(Q[d][0])][-1] for d in D})
    dt = pd.to_datetime(pd.Series(D)); brk = (dt.diff().dt.days > 5).to_numpy()
    rs, rq = sc.pct_change().to_numpy().copy(), qc.pct_change().to_numpy().copy(); rs[brk] = np.nan; rq[brk] = np.nan
    x = pd.DataFrame({"s": rs, "q": rq}).where(lambda t: t.s.notna() & t.q.notna())
    mu = lambda z: z.rolling(60, min_periods=20).mean()  # noqa: E731
    beta = ((mu(x.s * x.q) - mu(x.s) * mu(x.q)) / (mu(x.s * x.s) - mu(x.s) ** 2)).shift(1)
    nob = x.s.rolling(60, min_periods=20).count().shift(1)
    bq = np.where(nob.ge(20) & beta.notna(), beta, 1.2)
    with Pool(3) as p:
        res = p.map(gap_job, uni, chunksize=8)
    gd = pd.DataFrame([r for rr in res for r in rr], columns=["date", "gd"])
    no_locked(gd.date.unique())
    gs = gd.groupby("date").gd.agg(["mean", "count"])
    meta = pd.DataFrame({"date": D, "close_min": [CL[d] for d in D], "beta_qqq": bq})
    meta["gd_share"] = meta.date.map(gs["mean"]); meta["gd_n"] = meta.date.map(gs["count"])
    meta.to_csv(OUT / "idx_meta.csv", index=False)
    print("days", len(D), "half days", int((meta.close_min < 960).sum()), "gd_share median %.3f" % meta.gd_share.median(),
          "beta_qqq median %.2f" % np.median(bq))
