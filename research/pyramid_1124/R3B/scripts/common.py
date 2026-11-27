"""R3B shared helpers. Educational only - not financial advice."""
import sys, itertools, math
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX); sys.path.insert(0, INBOX + "/research/ultimate_1119/top10")
import bench10 as B
P = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/R3B/"
SHORTS = ["L3-fromopen", "L3-lowdist", "L3-rsi5hi", "RW3", "RW5", "CWT09", "RW6", "NM-RWN4", "GEN-261029-06", "GEN-261023-06"]
LONGS = ["NM-ETF", "CWT14", "B3", "GEN-261019-02", "GEN-261027-01"]
FAM = {"L3-fromopen": "GD", "L3-lowdist": "GD", "L3-rsi5hi": "GD", "RW3": "GD", "RW5": "GD", "CWT09": "GD",
       "RW6": "NS2", "NM-RWN4": "NS2", "GEN-261029-06": "GLATE", "GEN-261023-06": "GPOP", "NM-ETF": "ETF",
       "CWT14": "FB", "B3": "TREND", "GEN-261019-02": "PMDIP", "GEN-261027-01": "PMDIP"}
TOP10 = ["L3-fromopen", "RW3", "L3-lowdist", "RW5", "L3-rsi5hi", "RW6", "NM-RWN4", "CWT14", "NM-ETF", "CWT09"]
PRIM = ["L3-fromopen", "RW3", "RW5", "NM-ETF"]

def sessions():
    spy = B.spy_t1(); days = [d for d in spy.index if d <= "2026-11-04"]; h = B.half(pd.Series(days))
    spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet"); spy2.index = spy2.index.astype(str)
    t2 = [d for d in spy2.index if B.T2_LO <= d <= B.T2_HI]
    return {"fit": [d for d, x in zip(days, h) if x == "fit"], "check": [d for d, x in zip(days, h) if x == "check"], "T2": t2}

def daily(T, var, ses, col="r", w=1.0):
    x = T[T["var"] == var]
    return (x.groupby("date")[col].sum() * w).reindex(ses, fill_value=0.0)

def metrics(d):
    d = pd.Series(d, dtype=float); n = len(d); tot = d.sum()
    s = d.std(ddof=1)
    w5 = d.nsmallest(5).mean(); best = d.max()
    return {"avg_day": round(d.mean(), 4), "green_pct": round(100 * (d > 0).mean(), 1),
            "green_of_active": round(100 * (d[d != 0] > 0).mean(), 1) if (d != 0).any() else None,
            "worst_day": round(d.min(), 2), "avg_worst5": round(w5, 2), "total": round(tot, 2),
            "total_wo_best": round(tot - best, 2), "best_share": round(best / tot, 3) if tot > 0 else None,
            "day_t": round(d.mean() / s * math.sqrt(n), 2) if s > 0 else None, "sessions": n}

def paired(a, b):
    x = pd.Series(a) - pd.Series(b); s = x.std(ddof=1)
    return {"diff_avg_day": round(x.mean(), 4), "paired_t": round(x.mean() / s * math.sqrt(len(x)), 2) if s > 0 else None}

def feasible(longs_n=(2, 3), long_gates=("TT1", "SPYOPEN")):
    """yield books: tuple of variant names (longs carry a gate suffix)."""
    for nl in longs_n:
        for lb in itertools.combinations(LONGS, nl):
            if sum(FAM[x] == "PMDIP" for x in lb) > 2: continue
            for gs in itertools.product(long_gates, repeat=nl):
                lv = tuple(f"{b}+{g}" for b, g in zip(lb, gs))
                for sb in itertools.combinations(SHORTS, 5 - nl):
                    fams = [FAM[x] for x in sb] + [FAM[x] for x in lb]
                    if max(fams.count(f) for f in set(fams)) > 2: continue
                    yield lv + sb
