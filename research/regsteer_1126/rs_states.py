"""REGSTEER-1126 point-in-time states for every bench day (2023-01-03..2024-09-13 from data/cache_fresh, 2024-09-16..
2026-11-04 from data/cache_hist; the locked block 2024-11-01..2025-02-28 is never read: pyarrow filter + assert).
  S1 = SPY open gap (first RTH 1-min open / prior session's last RTH close - 1), known at 09:30.
  S2 = W60 compass (mcf/report/compass_live.compute rules, re-implemented vectorised on the cached 1-min bars and checked
       for parity against compute() itself): votes = SPY from-open sign + SPY session-VWAP side + breadth side (share of the
       Hunch-200 names above their open, 0.5 at 09:45) + SPY/QQQ/IWM agreement + 60-min persistence; level -2..+2.
       Breadth proxy: only the 177 Hunch names present in BOTH caches (so T2 and T1 use the same names); live uses 200.
Usage (repo root): python research/regsteer_1126/rs_states.py OUTDIR  -> OUTDIR/marks.parquet (date, T, level, votes),
OUTDIR/gap.parquet (date, gap). Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.report import compass_live as CL  # noqa: E402

TZ = "America/New_York"
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
LOCK = ("2024-11-01", "2025-02-28")
T2_LO, T2_HI, T1_LO, T1_HI = "2023-01-03", "2024-09-13", "2024-09-16", "2026-11-04"
MARKS = CL.MARKS


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def bars(sym, src):
    f = pads.field("__index_level_0__")
    flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
    b = pads.dataset(str(src / f"{sym}.parquet"), format="parquet").to_table(filter=flt).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    m = b.index.hour * 60 + b.index.minute
    b = b[(m >= 570) & (m < 960)]
    d = b.index.date.astype(str)
    lo, hi = (T2_LO, T2_HI) if src == FRESH else (T1_LO, T1_HI)
    b = b[(d >= lo) & (d <= hi)]
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def snaps(sym):
    """per (date, T): fo, vw of the bars that start before T (CL.snap), both caches; plus day open / last close."""
    out, days = [], []
    for src in (FRESH, HIST):
        if not (src / f"{sym}.parquet").exists():
            continue
        b = bars(sym, src)
        if not len(b):
            continue
        d = b.index.date.astype(str)
        m = (b.index.hour * 60 + b.index.minute).to_numpy()
        tp = ((b.high + b.low + b.close) / 3).to_numpy(float); v = b.volume.to_numpy(float); c = b.close.to_numpy(float)
        o = b.open.to_numpy(float)
        starts = np.flatnonzero(np.r_[True, d[1:] != d[:-1]]); ends = np.r_[starts[1:], len(d)]
        for a, e in zip(starts, ends):
            mm = m[a:e]; cpv = np.cumsum(tp[a:e] * v[a:e]); cv = np.cumsum(v[a:e])
            days.append((d[a], o[a], c[e - 1]))
            for T in MARKS:
                k = np.searchsorted(mm, T) - 1          # last bar starting before T
                if k < 0:
                    continue
                vw = cpv[k] / cv[k] if cv[k] > 0 else np.nan
                out.append((d[a], T, c[a + k] / o[a] - 1, c[a + k] / vw - 1 if np.isfinite(vw) else np.nan))
    s = pd.DataFrame(out, columns=["date", "T", "fo", "vw"]); s["sym"] = sym
    dd = pd.DataFrame(days, columns=["date", "open", "close"]); dd["sym"] = sym
    return s, dd


sg = lambda x: np.nan_to_num(np.sign(np.asarray(x, float))).astype(int)  # noqa: E731


def compass(S, names):
    """W60 per (date, T) from the per-symbol snaps, exactly compute()'s rules."""
    spy = S[S.sym == "SPY"].set_index(["date", "T"])
    q = S[S.sym == "QQQ"].set_index(["date", "T"]).fo.reindex(spy.index)
    w = S[S.sym == "IWM"].set_index(["date", "T"]).fo.reindex(spy.index)
    N = S[S.sym.isin(names)].copy(); N["up"] = (N.fo > 0).astype(float)
    bo = N.groupby(["date", "T"]).up.mean().reindex(spy.index)
    bo[spy.index.get_level_values("T") == 585] = 0.5
    s = sg(spy.fo)
    agree = np.where((sg(q.fillna(0)) == s) & (sg(w.fillna(0)) == s) & q.notna() & w.notna(), s, 0)
    bside = np.where(bo > 0.5, 1, np.where(bo < 0.5, -1, 0)); bside[~np.isfinite(bo.to_numpy())] = 0
    x = pd.DataFrame({"s": s, "base": s + sg(spy.vw) + bside + agree}, index=spy.index).reset_index()
    out = []
    for dte, g in x.groupby("date"):
        sd = dict(zip(g["T"], g.s)); bd = dict(zip(g["T"], g.base))
        for T in g["T"]:
            mk = [t for t in MARKS if T - 60 < t <= T]
            ss = [sd.get(t, 0) for t in mk]
            pw = ss[-1] if ss[-1] != 0 and all(v == ss[-1] for v in ss) else 0
            v = bd[T] + pw
            out.append((dte, T, v, CL.level(v, pw, len(mk) >= 2)))
    return pd.DataFrame(out, columns=["date", "T", "votes", "level"])


if __name__ == "__main__":
    OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
    names = [n for n in CL.universe() if (HIST / f"{n}.parquet").exists() and (FRESH / f"{n}.parquet").exists()]
    syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + names))
    with Pool(2) as p:
        res = p.map(snaps, syms, chunksize=4)
    S = pd.concat([r[0] for r in res], ignore_index=True); D = pd.concat([r[1] for r in res], ignore_index=True)
    no_locked(S.date.unique())
    S.to_parquet(OUT / "snaps.parquet")
    sp = D[D.sym == "SPY"].sort_values("date").reset_index(drop=True)
    sp["gap"] = sp.open / sp.close.shift(1) - 1
    sp.loc[sp.date == "2025-03-03", "gap"] = np.nan    # prior session lies in the locked block: never read
    sp[["date", "gap"]].to_parquet(OUT / "gap.parquet")
    M = compass(S, names)
    M.to_parquet(OUT / "marks.parquet")
    print(len(names), "breadth names;", M.date.nunique(), "days;", M.level.value_counts().sort_index().to_dict())
