"""R2 universe random long-bar control (pre-registered in PREREG.md). Educational only - not financial advice."""
import sys
from multiprocessing import Pool
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX); sys.path.insert(0, INBOX + "/research/ultimate_1119/top10")
import bench10 as B
import importlib.util
sp = importlib.util.spec_from_file_location("etfm", INBOX + "/research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py")
M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
ETF = set(M.SYMBOLS)
TZ = "America/New_York"
WIN = {"C3": (1000, 1200), "A1": (1400, 1500), "NM": (1400, 1500), "A3": (1300, 1500), "B3": (1430, 1430)}
EXIT = {"C3": 2.0, "A1": 0.5, "NM": 0.5, "A3": 0.5, "B3": np.nan}
POOL = {"C3": "p20", "A1": "p20", "A3": "p150", "B3": "p50", "NM": "etf"}
K = 60

def bars(sym, src):
    if src == "T1":
        return B.hist_bars(sym)
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet"); b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    return b.sort_index()

def daily(b, sym):
    hm = b.index.hour * 100 + b.index.minute
    r = b[(hm >= 930) & (hm < 1600)]
    g = r.groupby(r.index.date.astype(str))
    d = pd.DataFrame({"o": g.open.first(), "h": g.high.max(), "l": g.low.min(), "c": g.close.last(),
                      "dv": (r.close * r.volume).groupby(r.index.date.astype(str)).sum()})
    pc = d.c.shift(1)
    tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14, min_periods=10).mean().shift(1)
    d["adv20"] = d.dv.shift(1).rolling(20, min_periods=5).mean()
    d["pc"] = pc
    d["gap"] = (d.o / pc - 1) * 100
    d["symbol"] = sym
    return d.reset_index(names="date")

def d_job(a):
    sym, src = a
    try:
        return daily(bars(sym, src), sym)
    except Exception:
        return None

def tods(lo, hi):
    return [t for t in range(lo, hi + 1, 5) if t % 100 < 60]

def w_job(a):
    sym, src, T = a
    b = bars(sym, src)
    hm = b.index.hour * 100 + b.index.minute
    day = b.index.date.astype(str)
    cl = pd.Series(b.close.to_numpy(float), index=pd.MultiIndex.from_arrays([day, hm]))
    rows = []
    for r in T.itertuples():
        t1 = r.tod - 1 if r.tod % 100 else r.tod - 41      # bar labelled T-1
        px = cl.get((r.date, t1))
        if px is None or not np.isfinite(px):
            continue
        rows.append((r.cand, r.date, r.tod, px, r.atr, r.gap))
    if not rows:
        return None
    x = pd.DataFrame(rows, columns=["cand", "date", "tod", "entry", "atr", "gap"])
    x["symbol"] = sym; x["side"] = 1; x["risk"] = 0.25 * x.atr
    x["stop"] = x.entry - x.risk
    x["tgt"] = x.entry + x.cand.map(EXIT) * x.risk
    x = x.reset_index(drop=True)
    w = B.walk_trades(x, b)
    return x.join(pd.DataFrame(w, columns=["i", "px", "kind", "xt"]).set_index("i"))

def run(src):
    if src == "T1":
        syms = sorted(p.stem for p in B.CACHE.glob("*.parquet"))
    else:
        syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    with Pool(3) as p:
        D = pd.concat([d for d in p.imap_unordered(d_job, [(s, src) for s in syms], chunksize=8) if d is not None])
    D = D[D.atr > 0]
    if src == "T1":
        D = D[(D.date >= "2024-10-01") & (D.date <= "2026-11-04")]
    else:
        D = D[(D.date >= B.T2_LO) & (D.date <= B.T2_HI)]
    B.no_locked(D.date.unique())
    rng = np.random.default_rng(20261125 + (src == "T2"))
    pools = {"p20": (D.adv20 >= 20e6) & (D.pc >= 5), "p150": (D.adv20 >= 150e6) & (D.pc >= 5),
             "p50": (D.adv20 >= 50e6) & (D.pc >= 10), "etf": D.symbol.isin(ETF) & (D.adv20 >= 95e6)}
    picks = []
    for cand, pool in POOL.items():
        E = D[pools[pool]]
        if pool != "etf":
            E = E.assign(u=rng.random(len(E))).sort_values("u").groupby("date").head(K)
        tl = tods(*WIN[cand])
        picks.append(E[["symbol", "date", "atr", "gap"]].assign(cand=cand, tod=rng.choice(tl, len(E))))
    P = pd.concat(picks, ignore_index=True)
    print(src, "symbol-days", P.groupby("cand").size().to_dict(), flush=True)
    jobs = [(s, src, g) for s, g in P.groupby("symbol")]
    with Pool(3) as p:
        out = [o for o in p.imap_unordered(w_job, jobs, chunksize=4) if o is not None]
    T = pd.concat(out, ignore_index=True)
    T.to_parquet(f"r2_{src}.parquet")
    print(src, len(T))

if __name__ == "__main__":
    run(sys.argv[1])
