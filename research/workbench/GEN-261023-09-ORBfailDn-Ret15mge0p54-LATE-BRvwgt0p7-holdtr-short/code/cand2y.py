"""Mechanic GEN-261023-09: 2-year candidate rows (bar close 13:30-15:00, adv20 >= $75M, orb_fail_dn == 1, ret3 >= 0.30% -
a loose box around the parent; breadth not filtered) with the arena indicators (compute(context=False), as the module),
the lab context (breadth = share above VWAP, breadth_open; lib.load_month(context=True)), breadth at 09:50 and its change
since, SPY % since the 09:50 close (market state measured after 09:50, owner rule). Open months only; the locked block
2024-11..2025-02 is never read. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, IND, LOCK, BOX, END2Y
from lib import months, load_month
from mcf.research.arena.indicators import compute

def cands(df):
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    x = compute(df, names=IND, context=False)
    base = ["symbol", "date", "tod", "open", "close", "high", "low", "atr_d", "adv20", "breadth_open", "breadth"]
    df = pd.concat([df[[c for c in base if c in df.columns]], x], axis=1)
    g = df[df.symbol == "SPY"][["date", "tod", "close"]]; b = g[g.tod == 950].set_index("date").close
    spy = g.assign(spy950=(g.close / g.date.map(b) - 1) * 100).set_index(["date", "tod"]).spy950
    br = df.drop_duplicates(["date", "tod"]).set_index(["date", "tod"])[["breadth", "breadth_open"]]
    b950 = br.xs(950, level="tod").breadth
    keep = (df.tod >= BOX["lo"]) & (df.tod <= BOX["hi"]) & (df.adv20 >= BOX["adv"]) & (df.orb_fail_dn == 1) & (df.ret3 >= BOX["r3"])
    r = df[keep].copy()
    k = pd.MultiIndex.from_arrays([r.date, r.tod])
    r["spy950"] = spy.reindex(k).to_numpy(); r["br950"] = r.date.map(b950).to_numpy(); r["br_chg"] = r.breadth - r.br950
    return r

def one(m):
    df = load_month(m, context=True)
    df["date"] = df["date"].astype(str)
    big = df.groupby("symbol").adv20.max()
    df = df[df.symbol.isin(set(big[big >= BOX["adv"]].index) | {"SPY"})].reset_index(drop=True)
    r = cands(df); r["month"] = m
    print(m, len(r), flush=True)
    return r

if __name__ == "__main__":
    ms = [m for m in months() if m not in ("2024-11", "2024-12", "2025-01", "2025-02") and m <= END2Y[:7]]
    with Pool(3) as p:
        parts = p.map(one, ms)
    s = pd.concat(parts, ignore_index=True)
    s = s[s.date <= END2Y]
    assert not s.date.between(*LOCK).any()
    s.to_parquet(OUT + "cand2y.parquet"); print(len(s), s.date.min(), s.date.max(), s.symbol.nunique())
