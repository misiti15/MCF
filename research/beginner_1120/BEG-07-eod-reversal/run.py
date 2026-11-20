"""BEG-07 backtest, the "normal way": bench10's costs (add_r: LR8 + 1.2 bp borrow on shorts), testing-arena book
(TESTING_RULES: cap 100, 3 lots/symbol, price >= $5, ETB >= 0.9 for shorts, 0.15R cost filter) and stats(), imported
unchanged from research/ultimate_1119/top10/bench10.py. Universe-level signal at the 15:24 close, exits on 1-min bars.

  python run.py build t1|t2                  per symbol-day window table (14:55..15:55) -> WORK
  python run.py score VARIANT PART           PART in fit | check | t2
  python run.py rand VARIANT PART [N]        N random-side seeds and N random-name draws (same count per day/side)
Locked block 2024-11-01..2025-02-28 is never read (bench10.hist_bars pyarrow filter + no_locked; frames' locked months
skipped; T2 ends 2024-09-13). Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402
import beg07 as G  # noqa: E402

FRAMES = Path("/home/user/MCF/research/history2y/data/frames")
ETB = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult/research/ultimate_1119/top10/etb_rate.parquet")
META = Path("/home/user/MCF/research/swarm1010/w3_daily/assets_meta.csv")
WORK = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/beg07w")
T1_LAST = "2026-11-04"
W0, W1 = 1455, 1555                      # stored window (bar hhmm, inclusive)
MINS = np.array([h * 100 + m for h in (14, 15) for m in range(60) if W0 <= h * 100 + m <= W1])
NW = len(MINS)


def etf_set():
    m = pd.read_csv(META)
    return set(m.loc[m.is_etf, "symbol"].astype(str)) | {"RSP", "MTUM", "USMV", "SPLV", "QUAL", "BIL", "SHY", "IEF",
                                                          "AGG", "VTI"}


def load_variants():
    v = {"base": {}}
    p = HERE / "variants.json"
    if p.exists():
        v.update(json.loads(p.read_text()))
    return v


def rth(b):
    hm = b.index.hour * 100 + b.index.minute
    return b[(hm >= 930) & (hm < 1600)]


def day_table(b, daily):
    """b: RTH 1-min bars of one symbol; daily: DataFrame index date(str) with pc, atr, adv.
    -> rows (date, pc, atr, adv, dh0, dl0) + arrays (o,h,l,c) [n, NW] for W0..W1 (NaN where no bar)."""
    hm = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = b.index.date.astype(str)
    df = pd.DataFrame({"date": day, "hm": hm, "o": b.open.values, "h": b.high.values, "l": b.low.values,
                       "c": b.close.values})
    pre = df[df.hm < W0].groupby("date").agg(dh0=("h", "max"), dl0=("l", "min"), c0=("c", "last"))
    win = df[(df.hm >= W0) & (df.hm <= W1)]
    rows = pre.join(daily, how="inner")
    rows = rows[np.isfinite(rows.pc) & np.isfinite(rows.atr) & (rows.pc > 0) & (rows.adv >= 20e6)]
    if not len(rows):
        return None
    arrs = {}
    for k in ("o", "h", "l", "c"):
        pv = win.pivot(index="date", columns="hm", values=k).reindex(index=rows.index, columns=MINS)
        arrs[k] = pv.to_numpy(np.float32)
    # keep only symbol-days that could ever be candidates: |c/pc - 1| >= 2% at some stored minute up to 15:40
    cc = pd.DataFrame(arrs["c"]).ffill(axis=1).to_numpy()
    rr = np.abs(cc[:, MINS <= 1540] / rows.pc.to_numpy()[:, None] - 1)
    keep = np.nanmax(np.where(np.isfinite(rr), rr, 0), axis=1) >= 0.02
    if not keep.any():
        return None
    rows = rows[keep].reset_index().rename(columns={"index": "date"})
    return rows, {k: v[keep] for k, v in arrs.items()}


def t1_daily():
    out = []
    for p in sorted(FRAMES.glob("month=*")):
        if p.name.split("=")[1] in B.LOCKED_MONTHS:
            continue
        out.append(pads.dataset(str(p), format="parquet").to_table(
            columns=["symbol", "date", "gap", "atr_d", "adv20", "close"], filter=pads.field("tod") == 950).to_pandas())
    f = pd.concat(out, ignore_index=True)
    f["date"] = pd.to_datetime(f["date"]).dt.date.astype(str)
    f["symbol"] = f["symbol"].astype(str)
    B.no_locked(f.date.unique())
    return f[f.date <= T1_LAST]


def job_t1(args):
    sym, fd = args
    try:
        b = rth(B.hist_bars(sym))
    except Exception:
        return None
    o930 = b.groupby(b.index.date.astype(str)).open.first()
    fd = fd.set_index("date")
    fd = fd[fd.index.isin(o930.index)]
    daily = pd.DataFrame({"pc": o930.reindex(fd.index) / (1 + fd.gap / 100), "atr": fd.atr_d, "adv": fd.adv20})
    r = day_table(b, daily)
    if r is None:
        return None
    r[0]["symbol"] = sym
    return r


def job_t2(sym):
    from mcf import features as F
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = rth(b.sort_index())
    ds = pd.Index(b.index.date.astype(str))
    b = b[ds <= B.T2_HI]
    ds = pd.Index(b.index.date.astype(str))
    assert not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    g = b.assign(dv=b.close * b.volume).groupby(ds)
    dd = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(),
                       "dv": g.dv.sum()})
    daily = pd.DataFrame({"pc": dd.close.shift(1), "atr": F.atr(dd).shift(1),
                          "adv": dd.dv.rolling(20, min_periods=15).mean().shift(1)})
    daily = daily[(daily.index >= B.T2_LO) & (daily.index <= B.T2_HI)]
    r = day_table(b, daily)
    if r is None:
        return None
    r[0]["symbol"] = sym
    return r


def build(test):
    etf = etf_set()
    if test == "t1":
        f = t1_daily()
        syms = sorted(set(f.symbol) - etf)
        jobs = [(s, f[f.symbol == s][["date", "gap", "atr_d", "adv20"]]) for s in syms
                if (B.CACHE / f"{s}.parquet").exists()]
        fn = job_t1
    else:
        syms = sorted({p.stem for p in (B.FRESH / "1Min").glob("*.parquet")} - etf)
        jobs, fn = syms, job_t2
    rows, arrs = [], {k: [] for k in "ohlc"}
    with Pool(3) as pool:
        for r in pool.imap_unordered(fn, jobs, chunksize=4):
            if r is None:
                continue
            rows.append(r[0])
            for k in "ohlc":
                arrs[k].append(r[1][k])
    R = pd.concat(rows, ignore_index=True)
    B.no_locked(R.date.unique())
    WORK.mkdir(parents=True, exist_ok=True)
    R.to_parquet(WORK / f"rows_{test}.parquet")
    np.savez_compressed(WORK / f"arr_{test}.npz", **{k: np.concatenate(v) for k, v in arrs.items()})
    print(test, len(R), "candidate symbol-days,", R.symbol.nunique(), "symbols,", R.date.nunique(), "dates")


_D: dict = {}


def data(test):
    if test not in _D:
        R = pd.read_parquet(WORK / f"rows_{test}.parquet")
        A = dict(np.load(WORK / f"arr_{test}.npz"))
        etb = pd.read_parquet(ETB).rate
        R["etb"] = R.symbol.map(etb).fillna(0.0)
        R["is_etf"] = False
        if test != "t2":
            R["half"] = B.half(R.date.values)
        else:
            R["half"] = "t2"
        _D[test] = (R, A, etb)
    return _D[test]


def snapshot(R, A, sig_hhmm):
    """columns at the signal bar close: c = last close <= sig_hhmm, dh/dl = RTH high/low through sig_hhmm."""
    j = int(np.flatnonzero(MINS == sig_hhmm)[0])
    c = pd.DataFrame(A["c"][:, : j + 1]).ffill(axis=1).to_numpy()[:, -1]
    hh = np.fmax(R.dh0.to_numpy(), np.nanmax(np.where(np.isfinite(A["h"][:, : j + 1]), A["h"][:, : j + 1], -np.inf), 1))
    ll = np.fmin(R.dl0.to_numpy(), np.nanmin(np.where(np.isfinite(A["l"][:, : j + 1]), A["l"][:, : j + 1], np.inf), 1))
    c = np.where(np.isfinite(c), c, R.c0.to_numpy())
    return R.assign(c=c, dh=hh, dl=ll)


def trades(part, params, rand_side=None, rand_names=None):
    test = "t2" if part == "t2" else "t1"
    R, A, _ = data(test)
    p = dict(G.P, **{k: v for k, v in params.items() if k in G.P})
    m = (R.half == part).to_numpy()
    S = snapshot(R[m].reset_index(drop=True), {k: v[m] for k, v in A.items()}, p["sig_hhmm"])
    Am = {k: v[m] for k, v in A.items()}
    picks = []
    for d, g in S.groupby("date", sort=True):
        pk = G.pick(g, p)
        if rand_names is not None and len(pk):         # same count per side, random eligible names on that day
            elig = g[(g.c >= p["min_px"]) & (g.adv >= p["min_adv"]) & (g.atr > 0)]
            new = []
            for sd, n in pk.side.value_counts().items():
                pool = elig if sd == 1 else elig[elig.etb >= p["etb_min"]]
                pool = pool[~pool.index.isin([x.name for x in new])] if new else pool
                ch = pool.loc[rand_names.choice(pool.index, size=min(n, len(pool)), replace=False)].assign(side=sd)
                new.extend([r for _, r in ch.iterrows()])
            pk = pd.DataFrame(new)
        picks.append(pk)
    pk = pd.concat(picks) if picks else pd.DataFrame()
    if not len(pk):
        return pd.DataFrame()
    if rand_side is not None:
        pk = pk.assign(side=rand_side.choice([-1, 1], size=len(pk)))
    j0 = int(np.flatnonzero(MINS == p["sig_hhmm"])[0]) + 1
    j1 = int(np.flatnonzero(MINS == p["exit_hhmm"])[0])
    out = []
    for i, r in zip(pk.index, pk.itertuples()):
        o, h, l = Am["o"][i, j0: j1 + 1], Am["h"][i, j0: j1 + 1], Am["l"][i, j0: j1 + 1]
        fin = np.flatnonzero(np.isfinite(o))
        if not len(fin) or fin[0] >= len(o) - 1:
            continue
        s0 = fin[0]                                          # entry at the first bar open at/after 15:25
        last = fin[-1]
        oo, hh_, ll_ = o[s0:], h[s0:], l[s0:]
        mins = MINS[j0 + s0: j1 + 1]
        if not np.isfinite(oo[-1]):                          # no 15:55 bar: exit at the last available open
            k = np.flatnonzero(np.isfinite(oo))[-1]
            oo, hh_, ll_, mins = oo[: k + 1], hh_[: k + 1], ll_[: k + 1], mins[: k + 1]
        dist = p["stop_atr"] * r.atr
        fill, stop, px, kind, xt = G.walk(oo, hh_, ll_, r.side, dist, p, mins)
        gap = 0.0
        out.append((r.symbol, r.date, int(mins[0]), int(r.side), float(fill), float(stop), np.nan, abs(fill - stop),
                    gap, float(px), kind, xt, float((r.c / r.pc - 1) * 100), float(r.atr), float(r.atr / r.pc * 100),
                    float((r.c - r.dl) / r.atr), float((r.dh - r.c) / r.atr), float(r.adv), float(r.c)))
    T = pd.DataFrame(out, columns=["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind",
                                   "xt", "r_sig", "atr", "atr_pct", "lod_dist_atr", "hod_dist_atr", "adv", "c_sig"])
    T["setup"] = "BEG-07"
    return T


_NS: dict = {}


def n_sessions(part):
    if part not in _NS:
        if part == "t2":
            spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
            spy2.index = spy2.index.astype(str)
            spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
            _NS[part] = (len(spy2), spy2)
        else:
            spy1 = B.spy_t1()
            spy1 = spy1[spy1.index <= T1_LAST]
            _NS[part] = (int((B.half(spy1.index) == part).sum()), spy1)
    return _NS[part]


def score(name, part, save=True, rand_side=None, rand_names=None, params=None):
    params = load_variants()[name] if params is None else params
    T = trades(part, params, rand_side, rand_names)
    _, _, etb = data("t2" if part == "t2" else "t1")
    n, spy = n_sessions(part)
    if not len(T):
        return {"trades": 0}, T
    raw = B.add_r(T)
    bk = B.book(raw, B.TESTING_RULES, etb)
    st = B.stats(bk, n, spy)
    st["raw_signals"] = int(len(T))
    st["removed_by_cost_filter"] = int((raw.stop_cost_r > 0.15).sum())
    st["raw_avg_r_no_filter"] = round(float(raw.r.mean()), 4)
    st["stop_rate"] = round(float((bk.kind == 1).mean()), 3) if len(bk) else None
    for sd, nm in ((1, "long"), (-1, "short")):
        x = bk[bk.side == sd]
        st[f"n_{nm}"] = int(len(x))
        st[f"avg_r_{nm}"] = round(float(x.r.mean()), 4) if len(x) else None
        st[f"avg_r_gross_{nm}"] = round(float(x.r_gross.mean()), 4) if len(x) else None
    if save:
        WORK.mkdir(parents=True, exist_ok=True)
        bk.to_parquet(WORK / f"bk_{name}_{part}.parquet")
        res = json.loads((HERE / "results.json").read_text()) if (HERE / "results.json").exists() else {}
        res[f"{name}_{part}"] = st
        (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    return st, bk


def rand(name, part, n=100):
    st0, _ = score(name, part, save=False)
    o = {"setup_avg_r": st0.get("avg_r")}
    for kind in ("side", "names"):
        vals = []
        for s in range(n):
            rng = np.random.default_rng(1000 + s)
            st, _ = score(name, part, save=False, rand_side=rng if kind == "side" else None,
                          rand_names=rng if kind == "names" else None)
            vals.append(st.get("avg_r", np.nan))
        vals = np.array(vals, float)
        o[f"rand_{kind}"] = {"mean_avg_r": round(float(np.nanmean(vals)), 4),
                             "p05": round(float(np.nanpercentile(vals, 5)), 4),
                             "p95": round(float(np.nanpercentile(vals, 95)), 4),
                             "setup_percentile": round(float((vals < st0.get("avg_r", np.nan)).mean() * 100), 1),
                             "seeds": n}
    res = json.loads((HERE / "results.json").read_text()) if (HERE / "results.json").exists() else {}
    res[f"{name}_{part}_random"] = o
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    return o


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build(sys.argv[2])
    elif cmd == "score":
        st, _ = score(sys.argv[2], sys.argv[3])
        print(json.dumps(st, indent=1, default=float))
    elif cmd == "rand":
        print(json.dumps(rand(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 100), indent=1))
