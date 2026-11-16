"""Mechanic GEN-261027-01: candidate rows (bar close 13:30-15:00, adv20 >= $10M, macd_hist >= 0.04, ret3_atr <= -0.03 -
wider than the parent and every variant) with the arena indicators (compute(context=False), as the module), the lab
context (breadth etc., lib.load_month(context=True)) and SPY % since the 09:50 close / breadth at 09:50 (market state
measured after 09:50, owner rule). 2y: open months only, locked block 2024-11..2025-02 never read.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, IND, LOCK, PRE
from mcf.research.arena.indicators import compute

def cands(df, ctx):
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    x = compute(df, names=IND, context=False)
    base = df[["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20"] + [c for c in ("r_long_t05s1",) if c in df.columns]]
    df = pd.concat([base, x], axis=1)
    spy = df[df.symbol == "SPY"][["date", "tod", "close"]]
    b = spy[spy.tod == 950].set_index("date").close
    spy = spy.assign(spy950=(spy.close / spy.date.map(b) - 1) * 100)[["date", "tod", "spy950"]]
    c = ctx.copy()
    b0 = c[c.tod == 950].set_index("date").breadth
    c["br950"] = c.date.map(b0); c["br_chg"] = c.breadth - c.br950
    keep = (df.tod >= PRE["lo"]) & (df.tod <= PRE["hi"]) & (df.adv20 >= PRE["adv"]) & (df.macd_hist >= PRE["mh"]) & (df.ret3_atr <= PRE["r3"])
    r = df[keep].merge(spy, on=["date", "tod"], how="left").merge(c, on=["date", "tod"], how="left")
    return r

def one(m):
    import lib
    df = lib.load_month(m)
    ctx = lib.load_context(m)
    df["date"] = df.date.astype(str); ctx["date"] = ctx.date.astype(str)
    r = cands(df, ctx); r["month"] = m
    return r

if __name__ == "__main__":
    import lib
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    with Pool(3) as p:
        parts = p.map(one, ms)
    s = pd.concat(parts, ignore_index=True)
    assert not s.date.between(*LOCK).any()
    s.to_parquet(OUT + "cand_frames.parquet"); print(len(s), s.date.min(), s.date.max(), s.symbol.nunique())
