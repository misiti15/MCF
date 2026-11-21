"""cov-long engine: bench10.py signals / 1-minute walk / LR8 costs / book, with cov-long masks.
python eng.py spy | sig1 | walk1 | t2 | null1 | null2
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
INBOX = S / "inbox"
W = S / "fp" / "cov-long"
sys.path.insert(0, str(INBOX))
sys.path.insert(0, str(W))
spec = importlib.util.spec_from_file_location("bench10", INBOX / "research/ultimate_1119/top10/bench10.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
import os
if os.environ.get('CL2') == 'r3_':
    import cands3 as C  # noqa: E402
elif os.environ.get('CL2'):
    import cands2 as C  # noqa: E402
else:
    import cands as C  # noqa: E402
PFX = os.environ.get('CL2', '')

NPROC = 3


class M:
    def __init__(self, f):
        self.mask = f


def inv():
    return [dict(setup=k, side=1, geom="t1s1", w_lo=950, w_hi=1500, min_adv=C.ADV, refire=False, cooldown=1,
                 prefilter="", struct=False, cwt=False) for k in C.CANDS]


MODS = {k: M(f) for k, f in C.CANDS.items()}


# ------------------------------------------------------------------ SPY context (decision time) + day labels
def spy_tables(path, lo, hi):
    b = pd.read_parquet(path)
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    d = b.index.date.astype(str)
    b = b.assign(date=d)
    s = pd.Series(d)
    keep = ~((s >= B.LOCK[0]) & (s <= B.LOCK[1])).to_numpy()
    b = b[keep]
    day = b.groupby("date").agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"))
    day["pc"] = day.c.shift(1)
    # prior close across the locked gap is not valid for the first day after it: blank it
    day.loc[day.index == "2025-03-03", "pc"] = np.nan
    day["spy_gap"] = (day.o / day.pc - 1) * 100
    day["ret"] = (day.c / day.o - 1) * 100
    day["rng"] = (day.h - day.l) / day.o * 100
    mn = b.index.hour * 60 + b.index.minute
    b = b.assign(barclose=((mn - 570) // 5 + 1) * 5 + 570)
    g = b.groupby(["date", "barclose"]).agg(h=("high", "max"), l=("low", "min"), c=("close", "last")).reset_index()
    g["hh"] = g.groupby("date").h.cummax()
    g["ll"] = g.groupby("date").l.cummin()
    g = g.merge(day[["o", "spy_gap"]], left_on="date", right_index=True)
    g["tod"] = (g.barclose // 60) * 100 + g.barclose % 60
    ctx = pd.DataFrame({"date": g.date, "tod": g.tod.astype(int), "spy_fo2": (g.c / g.o - 1) * 100,
                        "spy_rng": (g.hh - g.ll) / g.o * 100, "spy_gap": g.spy_gap})
    day = day[(day.index >= lo) & (day.index <= hi)]
    ctx = ctx[(ctx.date >= lo) & (ctx.date <= hi)]
    B.no_locked(day.index)
    return ctx, day


def stage_spy():
    c1, d1 = spy_tables(B.CACHE / "SPY.parquet", "2024-10-01", "2026-12-31")
    c2, d2 = spy_tables(B.FRESH / "1Min" / "SPY.parquet", B.T2_LO, B.T2_HI)
    c1.to_parquet(W / "ctx1.parquet"); d1.to_parquet(W / "day1.parquet")
    c2.to_parquet(W / "ctx2.parquet"); d2.to_parquet(W / "day2.parquet")
    print(len(d1), len(d2))


# ------------------------------------------------------------------ T1 signals
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    f = lib.load_month(month, context=False)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    B.no_locked(f["date"].unique())
    ctx = pd.read_parquet(W / "ctx1.parquet")
    f = f.merge(ctx, on=["date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    o = B.signals(f, None, inv(), MODS)
    o.to_parquet(W / (PFX + f"sig1_{month}.parquet"))
    # null pool: eligible rows (adv, atr>0, price >= 5, window) per (date, tod) - compact
    ok = (f.adv20.fillna(0) >= C.ADV) & (f.atr_d > 0) & (f.close >= 5)
    if hasattr(C, "ETF"):
        ok &= f.symbol.astype(str).isin(C.ETF)
    pool = f[ok][["symbol", "date", "tod", "close", "atr_d", "gap"]]
    if len(o):
        pool = pool.merge(o[["date", "tod"]].drop_duplicates(), on=["date", "tod"])
    pool.astype({"close": "float32", "atr_d": "float32", "gap": "float32"}).to_parquet(W / (PFX + f"pool1_{month}.parquet"))
    return month, len(o), o.groupby("setup").size().to_dict() if len(o) else {}


def stage_sig1():
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / (PFX + f"sig1_{m}.parquet")).exists()]
    with Pool(2) as p:
        for r in p.imap_unordered(month_job, ms):
            print(r[0], r[1], flush=True)


def walk1_job(args):
    sym, T = args
    return B.walk_trades(T, B.hist_bars(sym))


def stage_walk(src, dst):
    sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob(src))], ignore_index=True)
    B.no_locked(sig["date"].unique())
    jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
    with Pool(NPROC) as p:
        out = [x for r in p.imap_unordered(walk1_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
    sig = sig.join(a)
    sig.to_parquet(W / dst)
    print(len(sig), dst)


# ------------------------------------------------------------------ T2
CTX2 = {}


def t2_job(sym):
    import research.history2y.build_frames as BF
    p = B.FRESH / "1Min" / f"{sym}.parquet"
    b = pd.read_parquet(p)
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return sym, None, None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return sym, None, None
    x = x.reset_index(names="ts")
    x = x[[c for c in x.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return sym, None, None
    if "c" not in CTX2:
        CTX2["c"] = pd.read_parquet(W / "ctx2.parquet")
    f = x.drop(columns=["ts"]).merge(CTX2["c"], on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    o = B.signals(f, None, inv(), MODS)
    ok = (f.adv20.fillna(0) >= C.ADV) & (f.atr_d > 0) & (f.close >= 5)
    if hasattr(C, "ETF"):
        ok &= f.symbol.astype(str).isin(C.ETF)
    pool = f[ok][["symbol", "date", "tod", "close", "atr_d", "gap"]]
    if len(o):
        w = B.walk_trades(o, b)
        a = pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i")
        o = o.join(a)
    return sym, o, pool


def stage_t2():
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    if hasattr(C, "ETF"):
        syms = [x for x in syms if x in C.ETF or x == "SPY"]
    out, pools = [], []
    with Pool(NPROC) as p:
        for sym, o, pool in p.imap_unordered(t2_job, syms):
            if o is not None and len(o):
                out.append(o)
            if pool is not None and len(pool):
                pools.append(pool)
    pd.concat(out, ignore_index=True).to_parquet(W / (PFX + "trades_t2.parquet"))
    pd.concat(pools, ignore_index=True).to_parquet(W / (PFX + "pool2.parquet"))
    print(sum(len(o) for o in out), "T2 signals")


# ------------------------------------------------------------------ matched random-entry null
def make_null(sig, pool, seed=7, reps=1):
    """for each signal, a random eligible symbol at the same (date, tod) (not the same symbol), long, same geometry."""
    rng = np.random.default_rng(seed)
    pool = pool.reset_index(drop=True)
    gi = pool.groupby(["date", "tod"]).indices
    rows = []
    for r in sig.itertuples():
        ix = gi.get((r.date, int(r.tod)))
        if ix is None or len(ix) < 2:
            continue
        for _ in range(reps):
            j = ix[rng.integers(len(ix))]
            if pool.symbol.iat[j] == r.symbol:
                j = ix[rng.integers(len(ix))]
            e = pool.close.iat[j]
            R = 0.25 * pool.atr_d.iat[j]
            rows.append((r.setup, pool.symbol.iat[j], r.date, int(r.tod), 1, e, e - R, e + R, R, pool.gap.iat[j]))
    return pd.DataFrame(rows, columns=["setup", "symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap"])


def stage_null1(setups):
    sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob(PFX + "sig1_*.parquet"))], ignore_index=True)
    sig = sig[sig.setup.isin(setups)]
    out = []
    for m in sorted({d[:7] for d in sig.date}):
        pool = pd.read_parquet(W / (PFX + f"pool1_{m}.parquet"))
        out.append(make_null(sig[sig.date.str[:7] == m], pool, reps=2))
    n = pd.concat(out, ignore_index=True)
    for i, ch in enumerate(np.array_split(np.arange(len(n)), 1)):
        n.iloc[ch].to_parquet(W / (PFX + f"nsig1_{i}.parquet"))
    stage_walk(PFX + "nsig1_*.parquet", PFX + "null_t1.parquet")


def null2_job(args):
    sym, T = args
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    return B.walk_trades(T, b.sort_index())


def stage_null2(setups):
    sig = pd.read_parquet(W / (PFX + "trades_t2.parquet"))
    sig = sig[sig.setup.isin(setups)]
    pool = pd.read_parquet(W / (PFX + "pool2.parquet"))
    pool["date"] = pool.date.astype(str)
    n = make_null(sig, pool, reps=2)
    jobs = [(s, g) for s, g in n.groupby("symbol")]
    with Pool(NPROC) as p:
        out = [x for r in p.imap_unordered(null2_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
    n.join(a).to_parquet(W / (PFX + "null_t2.parquet"))
    print(len(n), "null t2")


if __name__ == "__main__":
    st = sys.argv[1]
    if st == "spy":
        stage_spy()
    elif st == "sig1":
        stage_sig1()
    elif st == "walk1":
        stage_walk(PFX + "sig1_*.parquet", PFX + "trades_t1.parquet")
    elif st == "t2":
        stage_t2()
    elif st == "null1":
        stage_null1(sys.argv[2].split(","))
    elif st == "null2":
        stage_null2(sys.argv[2].split(","))
