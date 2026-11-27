"""PYRAMID round 2 team E: early-session longs (09:35-09:50 entries).  Run with cwd = inbox checkout.
  python e.py feat T1|T2     per symbol-day features from 1-min bars (prior-day ATR/ADV/beta/v5avg20, 5-min bars 935-950)
  python e.py sig  T1|T2     candidate signals + controls
  python e.py walk T1|T2     1-minute exits (60-min cap)
Educational only - not financial advice."""
from __future__ import annotations

import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(__file__).resolve().parent
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
import bench10 as B  # noqa: E402

SECT = ["XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"]
TODS = [935, 940, 945, 950]
RANGE = {"T1": ("2024-10-01", "2026-11-04"), "T2": (B.T2_LO, B.T2_HI)}
CONFIGS = {"E1_X3": ("E1", 3.0), "E1_X5": ("E1", 5.0), "E2_G05": ("E2", 0.5), "E2_G10": ("E2", 1.0),
           "E3_S03": ("E3", 0.3), "E3_S06": ("E3", 0.6)}
GEO = {"G1": 1.0, "G2": 2.0}
CAP_MIN = 60


def bars(sym, T):
    if T == "T1":
        return B.hist_bars(sym)
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    return b.sort_index()


def src(T):
    return B.CACHE if T == "T1" else B.FRESH / "1Min"


# ------------------------------------------------------------------------------------------------ features
SPYRET: dict = {}


def feat_job(args):
    sym, T = args
    try:
        b = bars(sym, T)
    except Exception:
        return None
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    if len(b) < 2000:
        return None
    hm = b.index.hour * 100 + b.index.minute
    day = pd.Index(b.index.date.astype(str))
    g = b.assign(day=day, dv=b.close * b.volume).groupby("day")
    d = pd.DataFrame({"o": g.open.first(), "h": g.high.max(), "l": g.low.min(), "c": g.close.last(), "dv": g.dv.sum()})
    d = d.sort_index()
    pc = d.c.shift(1)
    if T == "T1":
        pc[d.index == d.index[d.index >= "2025-03-01"].min()] = np.nan  # first session after the locked gap
    tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1)
    d["pc"] = pc
    d["gap"] = (d.o / pc - 1) * 100
    d["atr"] = tr.rolling(14, min_periods=10).mean().shift(1)
    d["adv20"] = d.dv.rolling(20, min_periods=10).mean().shift(1)
    ret = d.c / pc - 1
    if sym != "SPY":
        s = SPYRET[T].reindex(d.index)
        cov = ret.rolling(60, min_periods=20).cov(s)
        var = s.rolling(60, min_periods=20).var()
        d["beta"] = (cov / var).shift(1)
    else:
        d["beta"] = 1.0
    m = hm < 950
    x = b[m]
    k = ((x.index.hour * 100 + x.index.minute) - 930) // 5
    xg = x.assign(day=day[m], k=np.asarray(k)).groupby(["day", "k"])
    f5 = pd.DataFrame({"o": xg.open.first(), "h": xg.high.max(), "l": xg.low.min(), "c": xg.close.last(),
                       "v": xg.volume.sum()}).unstack("k")
    f5.columns = [f"{a}{TODS[c]}" for a, c in f5.columns]
    d = d.join(f5)
    d["v5avg20"] = d["v935"].rolling(20, min_periods=10).mean().shift(1)
    lo, hi = RANGE[T]
    d = d[(d.index >= lo) & (d.index <= hi)]
    B.no_locked(d.index)
    d = d.drop(columns=["h", "l", "dv"]).reset_index(names="date")
    d.insert(0, "symbol", sym)
    return d


def feat(T):
    # need SPY returns for warm-up days too: recompute on the full span
    b = bars("SPY", T)
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    c = b.groupby(b.index.date.astype(str)).close.last().sort_index()
    r = c / c.shift(1) - 1
    if T == "T1":
        r[r.index == r.index[r.index >= "2025-03-01"].min()] = np.nan
    SPYRET[T] = r
    syms = sorted(p.stem for p in src(T).glob("*.parquet"))
    out = []
    with Pool(3, initializer=_init, initargs=(T, r)) as p:
        for o in p.imap_unordered(feat_job, [(s_, T) for s_ in syms], chunksize=8):
            if o is not None and len(o):
                out.append(o)
    f = pd.concat(out, ignore_index=True)
    for c_ in f.columns:
        if f[c_].dtype == np.float64:
            f[c_] = f[c_].astype(np.float32)
    f.to_parquet(W / f"feat_{T}.parquet")
    print(T, f.shape, f.symbol.nunique(), f.date.nunique())


def _init(T, r):
    SPYRET[T] = r


# ------------------------------------------------------------------------------------------------ signals
def fo(f, t):
    return (f[f"c{t}"] / f.o - 1) * 100


def signals(T):
    f = pd.read_parquet(W / f"feat_{T}.parquet")
    f["date"] = f.date.astype(str)
    B.no_locked(f.date.unique())
    smap = pd.read_json(W.parent / "L1/secmap.json", typ="series").to_dict()
    etf = f[f.symbol.isin(SECT + ["SPY"])].copy()
    ctx = {}
    for t in TODS:
        ctx[t] = etf.assign(fo=fo(etf, t)).pivot_table(index="date", columns="symbol", values="fo")
    f["sector"] = f.symbol.map(smap)
    rng = np.random.default_rng(20261125)
    base = (f.c935 >= 5) & (f.adv20 >= 2e7) & (f.atr > 0) & f.c950.notna() & f.c935.notna()
    base100 = base & (f.adv20 >= 1e8)
    out = []

    def mk(h, cfg, kind_, tod, entry):
        return pd.DataFrame({"cfg": cfg, "kind_": kind_, "symbol": h.symbol.values, "date": h.date.values,
                             "tod": np.asarray(tod, int), "entry": np.asarray(entry, float),
                             "risk": 0.25 * h.atr.values.astype(float), "gap": h.gap.fillna(0).values.astype(float)})

    def rand_bar(h, choices, cfg, kind_):
        k = rng.integers(0, len(choices), len(h))
        tods = np.array(choices)[k]
        ent = np.array([h[f"c{t}"].values for t in choices])[k, np.arange(len(h))]
        return mk(h, cfg, kind_, tods, ent)

    # sector context per row
    sec_fo = {}
    for t in TODS:
        c = ctx[t]
        sec_fo[t] = pd.Series([np.nan] * len(f), index=f.index, dtype=float)
        m = f.sector.notna()
        idx = pd.MultiIndex.from_arrays([f.date[m], f.sector[m]])
        st = c[SECT].stack()
        sec_fo[t][m] = st.reindex(idx).values
    spy = {t: f.date.map(ctx[t]["SPY"]) for t in TODS}
    top940 = ctx[940][SECT].idxmax(axis=1)
    topfo940 = ctx[940][SECT].max(axis=1)
    rng1 = (f.h935 - f.l935)
    pos = (f.c935 - f.l935) / rng1.where(rng1 > 0)
    rvol5 = f.v935 / f.v5avg20
    rvol10 = (f.v935 + f.v940) / (2 * f.v5avg20)
    for name, (cnd, p) in CONFIGS.items():
        if cnd == "E1":
            m = base & (rvol5 >= p) & (f.c935 > f.o935) & (pos >= 0.8) & (sec_fo[935] - spy[935] >= 0.10)
            h = f[m.fillna(False)]
            out.append(mk(h, name, "sig", np.full(len(h), 935), h.c935))
            out.append(rand_bar(h, TODS, name, "ctl_sd"))
        elif cnd == "E2":
            pool = base100 & (f.gap <= -p) & (f.beta <= 0.8) & (f.c935 < f.o935)
            pool = pool.fillna(False)
            h = f[pool]
            hit = np.column_stack([(h[f"c{t}"] > h.h935).values for t in (940, 945, 950)])
            any_ = hit.any(1)
            first = np.argmax(hit, 1)
            hh = h[any_]
            tods = np.array([940, 945, 950])[first[any_]]
            ent = np.array([hh[f"c{t}"].values for t in (940, 945, 950)])[first[any_], np.arange(len(hh))]
            out.append(mk(hh, name, "sig", tods, ent))
            out.append(rand_bar(hh, TODS, name, "ctl_sd"))
            out.append(rand_bar(h, [940, 945, 950], name, "ctl_pool"))
        else:
            tp = f.date.map(top940)
            lead = f.date.map(topfo940) - spy[940]
            m = base & f.sector.notna() & (f.sector == tp) & (lead >= p) & (fo(f, 940) > 0) & (rvol10 >= 1.5)
            h = f[m.fillna(False)].assign(rv=rvol10[m.fillna(False)])
            h = h.sort_values(["date", "rv"], ascending=[True, False]).groupby("date").head(5)
            out.append(mk(h, name, "sig", np.full(len(h), 940), h.c940))
            out.append(rand_bar(h, TODS, name, "ctl_sd"))
    # same-universe random controls (per session, up to 30 names, random bar 935-950)
    for tag, pool in (("U20", base), ("U100", base100)):
        h = f[pool.fillna(False)]
        h = h.assign(u=rng.random(len(h))).sort_values("u").groupby("date").head(30)
        out.append(rand_bar(h, TODS, tag, "ctl_u"))
    o = pd.concat(out, ignore_index=True)
    o = o[np.isfinite(o.entry) & (o.risk > 0)]
    o["side"] = 1
    o["stop"] = o.entry - o.risk
    o.to_parquet(W / f"sig_{T}.parquet")
    print(T, o.groupby(["cfg", "kind_"]).size().to_string())


# ------------------------------------------------------------------------------------------------ exits
def walk_cap(T, b):
    hhmm = b.index.hour * 100 + b.index.minute
    mins = b.index.hour * 60 + b.index.minute
    day = b.index.date.astype(str)
    O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {dd: np.flatnonzero(day == dd) for dd in np.unique(day)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            res.append((r.Index, np.nan, -1, -1))
            continue
        em = (r.tod // 100) * 60 + r.tod % 100
        mm = mins[ix]
        sel = ix[(mm >= em) & (mm < em + CAP_MIN) & (hhmm[ix] < 1555)]
        after = ix[mm >= em + CAP_MIN]
        px = None
        for k in sel:
            if Lo[k] <= r.stop:
                px, kd, xt = min(O[k], r.stop), 1, hhmm[k]
                break
            if H[k] >= r.tgt + 0.01:
                px, kd, xt = r.tgt, 2, hhmm[k]
                break
        if px is None:
            if len(after):
                px, kd, xt = O[after[0]], 0, hhmm[after[0]]
            elif len(sel):
                px, kd, xt = C[sel[-1]], 0, hhmm[sel[-1]] + 1
            else:
                res.append((r.Index, np.nan, -1, -1))
                continue
        res.append((r.Index, px, kd, xt))
    return res


def walk_job(args):
    sym, T, g = args
    return walk_cap(g, bars(sym, T))


def walk(T):
    s = pd.read_parquet(W / f"sig_{T}.parquet")
    s = pd.concat([s.assign(geo=k, tgt=s.entry + v * s.risk) for k, v in GEO.items()], ignore_index=True)
    B.no_locked(s.date.unique())
    jobs = [(sym, T, g) for sym, g in s.groupby("symbol")]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
    s = s.join(a)
    s.to_parquet(W / f"trades_{T}.parquet")
    print(T, len(s), int((s.kind.isna() | (s.kind < 0)).sum()), "without path")


if __name__ == "__main__":
    {"feat": feat, "sig": signals, "walk": walk}[sys.argv[1]](sys.argv[2])
