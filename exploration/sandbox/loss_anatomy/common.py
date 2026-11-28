"""Shared loaders for loss anatomy. Educational only - not financial advice."""
import numpy as np, pandas as pd
ARENA = ["testing", "testing2", "gen", "livelab", "explore1", "testingd", "testinge", "testingf"]

def load(S):
    t = pd.read_parquet(f"{S}/trades.parquet")
    t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
    t["book"] = np.where(t.account == "primary", "primary", np.where(t.account == "graveyard", "graveyard", "arena"))
    return t

def arena(t):
    a = t[t.book == "arena"].drop_duplicates("k").copy()  # identical signals counted once
    return a

def dayt(d):
    d = pd.Series(d)
    if len(d) < 3 or d.std(ddof=1) == 0:
        return np.nan
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))

def summ(g, daycol="date"):
    d = g.groupby(daycol)["r"].sum()
    tot = g.r.sum()
    return pd.Series({"tr": len(g), "R": tot, "avgR": g.r.mean(), "gross": g.gross_r.mean(), "cost": g.cost_r.mean(),
                      "day_t": dayt(d), "R_wo_best": tot - (d.max() if len(d) else 0),
                      "best_share": (d.max() / tot) if tot > 0 else np.nan, "win%": (g.r > 0).mean() * 100})

def spy_days(S):
    b = pd.read_parquet(f"{S}/spy.parquet")
    b.index = pd.to_datetime(b.index)
    out = {}
    for d, g in b.groupby(b.index.date):
        o = g.open.iloc[0]; c = g.close.iloc[-1]
        g10 = g[g.index.time <= pd.Timestamp("10:00").time()]
        p10 = g10.close.iloc[-1] if len(g10) else o
        out[str(d)] = {"spy_oc": (c / o - 1) * 100, "spy_open30": (p10 / o - 1) * 100, "spy_10c": (c / p10 - 1) * 100,
                       "spy_rng": (g.high.max() / g.low.min() - 1) * 100, "spy_open": o, "spy_close": c}
    s = pd.DataFrame(out).T
    s["spy_gap"] = (s.spy_open / s.spy_close.shift(1) - 1) * 100
    return s
