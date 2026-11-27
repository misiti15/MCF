"""LONGBOOK-1127 lot generator: bench10 (research/ultimate_1119/top10) signals, unchanged, for the Primary P4 lineup plus
4 candidate live long setups, with one walk that adds what bench10 lacks for these longs: YAML time_stop_min (ULT-05,
45 min), generator 'hold' / 'holdtr' geometry (stop 1R = 0.25 daily ATR, no target; holdtr trails 1R behind the best
price once +1R, from the next bar), a stress copy (+1 minute entry, same stop/target levels) and K random-minute
shadows per long signal (same symbol-day, entry minute uniform in the setup's window, same %-risk, same exit rule) for
the size-matched random-add control. 1-minute close paths are written per lot for the E4 open marks.
Stages (cwd = repo checkout): python lb_gen.py W sig1 | t2ctx | t2 | walk1.
T2 breadth / breadth_open (needed by the GEN longs) are rebuilt from the 469 cache_fresh names (proxy universe; the lab
universe is ~1,300 names): share of names whose 5-minute close is above session VWAP / above the day's open.
Locked block 2024-11-01..2025-02-28 is never read (bench10 guards + asserts here). Educational only - not financial advice."""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

LONGS = ["CWT14-failbrk-orl-p10-long-WB5", "ULT-05-withgap-cont-long",
         "GEN-261027-10-FlowShiftlem1p2-MACDhge0p079-SMA20dge0p59-LUNCH-BRopgt0p65-holdtr-long",
         "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long"]
B.SETUPS = [("L3-gap-slope-fromopen-FD", "default.yaml", "primary"),
            ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml", "primary"),
            ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml", "primary"),
            ("NM-ETF-late-dip-di-long", "default.yaml", "primary"),
            (LONGS[0], "account_testingd.yaml", "testingd"),
            (LONGS[1], "account_testinge.yaml", "testinge"),
            (LONGS[2], "account_testingd.yaml", "testingd"),
            (LONGS[3], "account_testing2.yaml", "testing2")]
B.GEOMS = dict(B.GEOMS, hold=(np.nan, 1.0), holdtr=(np.nan, 1.0))
TSTOP = {LONGS[1]: 45}
TRAIL = {LONGS[2]}
WIN = {LONGS[0]: (950, 1200), LONGS[1]: (1015, 1400), LONGS[2]: (1130, 1400), LONGS[3]: (1130, 1400)}
K = 20
LOCK = B.LOCK
CTX2 = None


def hm2m(x):
    x = np.asarray(x, int)
    return (x // 100) * 60 + x % 100


def m2hm(m):
    return (m // 60) * 100 + m % 60


from numba import njit  # noqa: E402


@njit(cache=True)
def _walk(day_m, O, H, Lo, C, e_idx, e, stop, tgt, s, tstop, trail, buf):
    """numba walk. tstop < 0 = none. Returns px, kind (1 stop, 2 target, 0 market/time, -1 none), exit minute, path len."""
    R = abs(e - stop)
    nb = len(day_m)
    em = day_m[e_idx] if e_idx < nb else 955
    hi_end = 955 if tstop < 0 else min(955, em + tstop)
    best = 0.0; st = stop; npth = 0
    for k in range(e_idx, nb):
        if day_m[k] >= hi_end:
            return O[k], 0, day_m[k], npth
        if (s == 1 and Lo[k] <= st) or (s == -1 and H[k] >= st):
            px = min(O[k], st) if s == 1 else max(O[k], st)
            buf[npth] = st; npth += 1
            return px, 1, day_m[k], npth
        if tgt == tgt and ((s == 1 and H[k] >= tgt + 0.01) or (s == -1 and Lo[k] <= tgt - 0.01)):
            buf[npth] = tgt; npth += 1
            return tgt, 2, day_m[k], npth
        buf[npth] = C[k]; npth += 1
        if trail:
            fav = H[k] if s == 1 else Lo[k]
            best = max(best, s * (fav - e) / R)
            if best >= 1.0:
                ts = e + s * (best - 1.0) * R
                st = max(st, ts) if s == 1 else min(st, ts)
    if npth == 0:
        return np.nan, -1, -1, 0
    return C[nb - 1], 0, min(day_m[nb - 1] + 1, 955), npth


def walk_one(day_m, O, H, Lo, C, e_idx, e, stop, tgt, s, tstop, trail):
    buf = np.empty(len(day_m) + 2)
    px, kd, xm, npth = _walk(day_m.astype(np.int64), O, H, Lo, C, int(e_idx), float(e), float(stop), float(tgt),
                             int(s), -1 if tstop is None else int(tstop), bool(trail), buf)
    if kd < 0:
        return None
    return px, int(kd), int(xm), buf[:max(npth, 1)].astype(np.float32) if npth else np.asarray([px], np.float32)


def walk_sym(T, b, rng):
    m_all = (b.index.hour * 60 + b.index.minute).to_numpy()
    dn = (b.index.year * 10000 + b.index.month * 100 + b.index.day).to_numpy()
    O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    for dd in set(T.date):
        v = int(dd.replace("-", ""))
        lo_, hi_ = np.searchsorted(dn, v, "left"), np.searchsorted(dn, v, "right")
        if hi_ > lo_:
            byday[dd] = np.arange(lo_, hi_)
    out = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            continue
        ix = ix[(m_all[ix] >= 570) & (m_all[ix] < 960)]
        dm, o_, h_, l_, c_ = m_all[ix], O[ix], H[ix], Lo[ix], C[ix]
        em = int(hm2m(r.tod))
        e0 = int(np.searchsorted(dm, em))
        ts, tr = TSTOP.get(r.setup), r.setup in TRAIL
        w = walk_one(dm, o_, h_, l_, c_, e0, r.entry, r.stop, r.tgt, r.side, ts, tr)
        if w is None:
            continue
        rec = dict(i=r.Index, shadow=-1, px=w[0], kind=w[1], xm=w[2], em=em, entry=r.entry, risk=abs(r.entry - r.stop),
                   path=w[3])
        # stress: entry at the close of the first 1-min bar after the decision, same stop / target levels
        if e0 < len(dm):
            e1 = c_[e0]
            if (e1 - r.stop) * r.side > 0:
                w1 = walk_one(dm, o_, h_, l_, c_, e0 + 1, e1, r.stop, r.tgt, r.side, ts, tr)
                if w1 is not None:
                    rec.update(px_s=w1[0], kind_s=w1[1], entry_s=e1, risk_s=abs(e1 - r.stop))
        out.append(rec)
        if r.setup in WIN:
            lo, hi = hm2m(WIN[r.setup][0]), hm2m(WIN[r.setup][1])
            cand = np.flatnonzero((dm >= lo) & (dm <= hi))
            if not len(cand):
                continue
            frac = abs(r.entry - r.stop) / r.entry
            tfrac = (r.tgt - r.entry) / r.entry if r.tgt == r.tgt else np.nan
            for k in range(K):
                j = int(rng.choice(cand))         # decision at close of bar j-1 -> walk from j; entry = close[j-1]
                if j == 0:
                    continue
                e = c_[j - 1]; stp = e * (1 - r.side * frac); tg = e * (1 + tfrac) if tfrac == tfrac else np.nan
                ws = walk_one(dm, o_, h_, l_, c_, j, e, stp, tg, r.side, ts, tr)
                if ws is None:
                    continue
                out.append(dict(i=r.Index, shadow=k, px=ws[0], kind=ws[1], xm=ws[2], em=int(dm[j]), entry=e,
                                risk=abs(e - stp), path=ws[3]))
    return out


def walk1_job(args):
    sym, T = args
    return walk_sym(T, B.hist_bars(sym), np.random.default_rng(abs(hash(sym)) % 2 ** 32))


def save_walk(sig, res, W, tag):
    a = pd.DataFrame([{k: v for k, v in r.items() if k != "path"} for r in res])
    paths = [r["path"] for r in res]
    off = np.r_[0, np.cumsum([len(p) for p in paths])[:-1]]
    a["off"], a["n"] = off, [len(p) for p in paths]
    np.save(Path(W) / f"paths_{tag}.npy", np.concatenate(paths).astype(np.float32))
    a = a.merge(sig.drop(columns=["entry", "risk"]), left_on="i", right_index=True, how="left")
    B.no_locked(a.date.unique())
    a.to_parquet(Path(W) / f"walk_{tag}.parquet")
    print(tag, "rows", len(a), "real", int((a.shadow < 0).sum()), a[a.shadow < 0].groupby("setup").size().to_dict())


def walk1(W):
    sig = pd.concat([pd.read_parquet(p) for p in sorted(Path(W).glob("sig1_*.parquet"))], ignore_index=True)
    B.no_locked(sig["date"].unique())
    jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        res = [x for r in p.imap_unordered(walk1_job, jobs, chunksize=4) for x in r]
    save_walk(sig, res, W, "t1")


def t2ctx_job(sym):
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b[(b.index.date.astype(str) >= B.T2_LO) & (b.index.date.astype(str) <= B.T2_HI)]
    mm = b.index.hour * 60 + b.index.minute
    b = b[(mm >= 570) & (mm < 960)]
    if not len(b):
        return None
    x = pd.DataFrame({"date": b.index.date.astype(str), "m": (b.index.hour * 60 + b.index.minute).to_numpy(),
                      "o": b.open.to_numpy(), "h": b.high.to_numpy(), "l": b.low.to_numpy(), "c": b.close.to_numpy(),
                      "v": b.volume.to_numpy()})
    x["bk"] = ((x.m - 570) // 5 + 1) * 5 + 570
    x["tp"] = (x.h + x.l + x.c) / 3 * x.v
    g = x.groupby(["date", "bk"]).agg(c=("c", "last"), tp=("tp", "sum"), v=("v", "sum")).reset_index()
    op = x.groupby("date").o.first()
    g["vw"] = g.groupby("date").tp.cumsum() / g.groupby("date").v.cumsum().replace(0, np.nan)
    g["a_vw"] = (g.c > g.vw).astype(np.int8)
    g["a_op"] = (g.c > g.date.map(op)).astype(np.int8)
    g["tod"] = m2hm(g.bk)
    return g[["date", "tod", "a_vw", "a_op"]]


def t2ctx(W):
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    with Pool(3) as p:
        parts = [r for r in p.imap_unordered(t2ctx_job, syms, chunksize=8) if r is not None]
    a = pd.concat(parts).groupby(["date", "tod"]).agg(breadth=("a_vw", "mean"), breadth_open=("a_op", "mean"),
                                                      nb=("a_vw", "size")).reset_index()
    c = pd.read_parquet(B.FRESH / "ctx.parquet")
    c["date"] = c.date.astype(str)
    c = c.merge(a, on=["date", "tod"], how="left")
    B.no_locked(c.date.unique())
    c.to_parquet(Path(W) / "ctx_t2.parquet")
    print("ctx_t2", len(c), "breadth NaN share", float(c.breadth.isna().mean()), "median names", float(a.nb.median()))


def t2_init(W):
    c = pd.read_parquet(Path(W) / "ctx_t2.parquet")
    c["date"] = c.date.astype(str)
    B.WCTX["ctx"] = c.drop(columns=["nb"])


def t2_job(sym):
    import research.history2y.build_frames as BF
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert ds.min() >= B.T2_WARM and ds.max() <= B.T2_HI and not ((ds >= LOCK[0]) & (ds <= LOCK[1])).any()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return sym, None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return sym, None
    x = x.reset_index(names="ts")
    x = x[[c for c in x.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return sym, None
    f = x.drop(columns=["ts"]).merge(B.WCTX["ctx"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    h = B.head_rows_from_1min(sym, b)
    fx = B.with_head(f, h) if len(h) else f
    inv = B.inventory()
    mods = {st["setup"]: B.load_mod(st["setup"], st["module"]) for st in inv}
    o = B.signals(f, fx, inv, mods)
    if not len(o):
        return sym, None
    o.index = [f"{sym}|{i}" for i in range(len(o))]
    res = walk_sym(o, b, np.random.default_rng(abs(hash(sym)) % 2 ** 32))
    return sym, (o, res)


def t2(W):
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    sigs, res = [], []
    with Pool(3, initializer=t2_init, initargs=(W,)) as p:
        for sym, r in p.imap_unordered(t2_job, syms):
            if r is not None:
                sigs.append(r[0]); res.extend(r[1])
    save_walk(pd.concat(sigs), res, W, "t2")


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    st = sys.argv[2]
    if st == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        if len(sys.argv) > 3:
            ms = [m for m in ms if m in sys.argv[3].split(",")]
        with Pool(3) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif st == "walk1":
        walk1(W)
    elif st == "t2ctx":
        t2ctx(W)
    elif st == "t2":
        t2(W)
