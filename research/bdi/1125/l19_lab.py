"""swing1125-L19 (pre-registered in research/bdi/swings/hypotheses.jsonl before the score stage was run): the gap-down
short family's STOP CLUSTER as a long trigger. Merges backlog nightly-1125-squeeze-stopcluster-flip-long (its arm A, K 10,
ONE config; arms B / K 15 not run).

Family replay = the bench10 pipeline (research/ultimate_1119/top10/bench10.py: live config masks, windows, min_adv,
prefilters, refire chains, home-account book incl. Primary -2R latch / lot caps, 1-minute exits, LR8 research costs),
setup list = the 8 family setups of research/bdi/gapdef_1124/gapdef_lab.py. 22 open months 2024-10..2026-11; the locked
block 2024-11-01..2025-02-28 is never read (bench10 asserts on every load).

Rule (pre-declared, 1 config):
  family stop = a booked family lot that exits on its stop (kind 1) at minute xm.
  Trigger T  = the first minute 10:30..14:30 ET at which >= 10 DISTINCT symbols had a family stop in the last 10 minutes
               (window [m-9, m]).
  Entry      = every symbol whose (first) family stop minute is >= T and <= 14:30: buy at the close of that 1-minute bar
               (one lot per symbol-day; a symbol stopped in two setups counts once, the earliest stop >= T).
  Exit       = stop at entry - risk/share of the stopped short (1R), checked from the next minute; else the 15:55 open.
               No target.  Costs = bench10 add_r (entry tod multiplier, exit 1c + 1 bp, +2c on stops, extended tier x3).
  Control    = same trigger days, buy at T's bar close every family symbol traded that day that was NOT stopped by T
               (same 1R geometry: its own short risk/share), same exits. Edge = A minus control.
Pass bar (BAR90 Testing bar, rules 22 / RESEARCH_RULES): avg R after costs > 0; day-clustered t >= 1.35; >= 20 trigger
days; avg R w/o best day > 0 and best-day share < 50%; avg R > 0 in BOTH fit (2024-10, 2025-03..09) and check
(2025-10..) halves; A beats control. Up/down session split reported (SPY open->close +-0.3%).
Usage: python l19_lab.py WORK sig|walk|score.   Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "research/ultimate_1119/top10"))
sys.path.insert(0, str(HERE.parents[2]))
import bench10 as B  # noqa: E402

B.SETUPS = [("L3-gap-slope-fromopen-FD", "default.yaml", "primary"),
            ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml", "primary"),
            ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml", "primary"),
            ("L3-gap-slope-lowdist-FD", "account_testing.yaml", "testing"),
            ("L3-gap-slope-rsi5hi-FD", "account_testing.yaml", "testing"),
            ("RW1-gapdn-bounce-flowsell-short-FD", "account_testing.yaml", "testing"),
            ("RW7-gapdn-bounce-early-short-FD", "account_testingf.yaml", "testingf"),
            ("RW3S-gapdn-flowsell-short-FD", "account_graveyard.yaml", "graveyard")]
K, WIN, T0, T1 = 10, 10, 10 * 60 + 30, 14 * 60 + 30


def mm(hhmm):
    return (hhmm // 100) * 60 + hhmm % 100


def long_walk(b, day, m_entry, rps):
    """buy at the close of minute m_entry; stop entry - rps from the next minute; else 15:55 open."""
    x = b[b.index.date.astype(str) == day]
    if not len(x):
        return None
    hm = x.index.hour * 60 + x.index.minute
    i0 = np.flatnonzero(hm == m_entry)
    if not len(i0):
        return None
    e = float(x.close.iloc[i0[0]]); st = e - rps
    for k in range(i0[0] + 1, len(x)):
        if hm[k] >= 955:
            return e, float(x.open.iloc[k]), 0, int(hm[k])
        if x.low.iloc[k] <= st:
            return e, float(min(x.open.iloc[k], st)), 1, int(hm[k])
    return e, float(x.close.iloc[-1]), 0, int(hm[-1])


def lw_job(args):
    sym, rows = args
    b = B.hist_bars(sym)
    out = []
    for r in rows:
        w = long_walk(b, r["date"], r["m"], r["rps"])
        if w:
            out.append({**r, "symbol": sym, "entry": w[0], "px": w[1], "kind": w[2], "xm": w[3]})
    return out


def cost_r(t):
    tier = np.where((np.abs(t.gap) >= 20) | (t.entry < 5), 3.0, 1.0)
    tod = ((t.m // 60) * 100 + t.m % 60).to_numpy()
    ec = (0.01 + t.entry * 1e-4) * B.tod_cost_mult(tod)
    xc = 0.01 + t.px * 1e-4 + np.where(t.kind == 1, 0.02, 0.0)
    t["r"] = ((t.px - t.entry) - tier * (ec + xc)) / t.rps
    t["r_gross"] = (t.px - t.entry) / t.rps
    return t


def summ(t, spy, name):
    if not len(t):
        return {"arm": name, "n": 0}
    day = t.groupby("date").r.sum(); best = day.idxmax(); tot = day.sum()
    hf = B.half(t.date)
    d = {"arm": name, "n": len(t), "days": int(day.size), "avg_r": round(t.r.mean(), 4), "avg_r_gross": round(t.r_gross.mean(), 4),
         "win": round((t.r > 0).mean(), 3), "total_r": round(tot, 1), "t_day": round(B.clustered_t(t), 2),
         "avg_wo_best_day": round(t.loc[t.date != best, "r"].mean(), 4), "best_day": best,
         "best_share": round(day.max() / tot, 3) if tot > 0 else None, "stops": round((t.kind == 1).mean(), 3)}
    for h in ("fit", "check"):
        z = t[hf == h]; d[f"avg_{h}"] = round(z.r.mean(), 4) if len(z) else None; d[f"n_{h}"] = len(z)
    ty = t.date.map(spy)
    for k in ("up", "flat", "down"):
        z = t[ty == k]; d[f"avg_{k}"] = round(z.r.mean(), 4) if len(z) else None; d[f"n_{k}"] = len(z)
    return d


def score(W):
    t = B.add_r(pd.read_parquet(W / "trades_fam.parquet"))
    etb = pd.Series(1.0, index=t.symbol.unique())   # etb_rate.parquet not in the repo (as gapdef_1124): all shorts kept
    t = pd.concat([B.book(t[t.setup == s], B.BOOK.get(a, B.TESTING_RULES), etb) for s, _, a in B.SETUPS], ignore_index=True)
    t["rps"] = t.risk
    print(f"family booked lots {len(t)} on {t.date.nunique()} sessions; stops {(t.kind == 1).sum()}")
    st = t[t.kind == 1].groupby(["date", "symbol"]).agg(xm=("xm", "min"), rps=("rps", "first"), gap=("gap", "first")).reset_index()
    trig, C = {}, []
    for d, g in st.groupby("date"):
        for m in range(T0, T1 + 1):
            if g[(g.xm > m - WIN) & (g.xm <= m)].symbol.nunique() >= K:
                trig[d] = m; break
    print(f"trigger days {len(trig)} of {t.date.nunique()} family sessions")
    for d, m in trig.items():
        g = st[st.date == d]
        stopped = set(g[g.xm <= m].symbol)
        fam = t[t.date == d].groupby("symbol").agg(rps=("rps", "first"), gap=("gap", "first"))
        for s, r in fam.iterrows():
            if s not in stopped:
                C.append({"date": d, "m": int(m), "rps": float(r.rps), "gap": float(r.gap), "arm": "control", "sym": s})
    jobs = {}
    rowsA = []
    for d, m in trig.items():
        g = st[st.date == d]
        for r in g[(g.xm >= m) & (g.xm <= T1)].itertuples():
            rowsA.append((r.symbol, {"date": d, "m": int(r.xm), "rps": float(r.rps), "gap": float(r.gap), "arm": "A"}))
    rowsC = [(r.pop("sym"), r) for r in C]
    for s, r in rowsA + rowsC:
        jobs.setdefault(s, []).append(r)
    jobs = [(s, rr) for s, rr in jobs.items() if (B.CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(lw_job, jobs, chunksize=4) for x in r]
    L = cost_r(pd.DataFrame(out))
    L = L[L.rps > 0]
    B.no_locked(L.date.unique())
    spy = B.spy_t1()
    res = [summ(L[L.arm == "A"], spy, "A (stopped names, K10)"), summ(L[L.arm == "control"], spy, "control (not-stopped family names at T)")]
    R = pd.DataFrame(res)
    pd.set_option("display.width", 250)
    print(R.T.to_string())
    a = L[L.arm == "A"]
    print("trigger minute distribution:", pd.Series(list(trig.values())).describe().round(0).to_dict())
    print("A by year:", a.groupby(a.date.str[:4]).r.agg(["count", "mean"]).round(4).to_dict("index"))
    dm = a.groupby("date").r.mean(); cm = L[L.arm == "control"].groupby("date").r.mean()
    j = pd.concat([dm, cm], axis=1, keys=["A", "C"]).dropna()
    dif = j.A - j.C
    print(f"A - control per trigger day: mean {dif.mean():+.4f}R, days {len(dif)}, t {dif.mean() / (dif.std(ddof=1) / np.sqrt(len(dif))):+.2f}")
    L.to_parquet(W / "l19_trades.parquet")
    R.to_csv(HERE / "l19_lab_results.csv", index=False)
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True); stg = sys.argv[2]
    if stg == "sig":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(3) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif stg == "walk":
        sig = pd.concat([pd.read_parquet(p) for p in sorted(W.glob("sig1_*.parquet"))], ignore_index=True)
        B.no_locked(sig["date"].unique())
        jobs = [(s, g) for s, g in sig.groupby("symbol") if (B.CACHE / f"{s}.parquet").exists()]
        with Pool(3) as p:
            out = [x for r in p.imap_unordered(B.walk1_job, jobs, chunksize=4) for x in r]
        a = pd.DataFrame(out, columns=["i", "px", "kind", "xt"]).set_index("i")
        sig = sig.join(a)
        sig.to_parquet(W / "trades_fam.parquet")
        print(len(sig), "signals;", int((sig.kind.isna() | (sig.kind < 0)).sum()), "without path")
    elif stg == "score":
        score(W)
