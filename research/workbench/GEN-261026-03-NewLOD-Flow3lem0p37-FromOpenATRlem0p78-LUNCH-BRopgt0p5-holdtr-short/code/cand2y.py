"""Mechanic GEN-261026-03: 2-year candidate rows (bar close 10:30-15:00, adv20 >= $100M, new_lod == 1, flow3 <= -0.15,
fromOpen_atr <= -0.45 - a loose box around the parent) with the arena indicators (compute(context=False), as the module), the
lab context columns (breadth_open etc., lib.load_month(context=True)), SPY/QQQ % change since the 09:50 close, and the
generator's earnings-blackout flag. Open months only; the locked block 2024-11..2025-02 is never read.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, IND, LOCK, BOX, WT
sys.path.insert(0, "/home/user/MCF/research/history2y")
from lib import months, load_month
from mcf.research.arena.indicators import compute
from mcf.research.generator.data import _blackout

def one(m):
    df = load_month(m, context=True)
    df["date"] = df["date"].astype(str)
    big = df.groupby("symbol").adv20.max()
    keep_s = set(big[big >= BOX["adv"]].index) | {"SPY", "QQQ"}
    df = df[df.symbol.isin(keep_s)].reset_index(drop=True)
    x = compute(df, names=IND, context=False)
    base = ["symbol", "date", "tod", "open", "close", "high", "low", "atr_d", "adv20", "gap", "breadth_open", "breadth", "spy_fo", "qqq_fo"]
    df = pd.concat([df[[c for c in base if c in df.columns]], x], axis=1)
    ix = {}
    for e in ("SPY", "QQQ"):
        g = df[df.symbol == e][["date", "tod", "close"]]
        b = g[g.tod == 950].set_index("date").close
        ix[e] = g.assign(v=(g.close / g.date.map(b) - 1) * 100).set_index(["date", "tod"]).v
    keep = (df.tod >= BOX["lo"]) & (df.tod <= BOX["hi"]) & (df.adv20 >= BOX["adv"]) & (df.new_lod == 1) \
        & (df.flow3 <= BOX["flow3"]) & (df.fromOpen_atr <= BOX["fo"])
    r = df[keep].copy()
    k = pd.MultiIndex.from_arrays([r.date, r.tod])
    r["spy950"] = ix["SPY"].reindex(k).to_numpy(); r["qqq950"] = ix["QQQ"].reindex(k).to_numpy()
    r["blackout"] = _blackout(r.symbol.to_numpy(), r.date.to_numpy())
    r["month"] = m
    print(m, len(r), flush=True)
    return r

if __name__ == "__main__":
    ms = [m for m in months() if m not in ("2024-11", "2024-12", "2025-01", "2025-02")]
    with Pool(2) as p:
        parts = p.map(one, ms)
    s = pd.concat(parts, ignore_index=True)
    assert not s.date.between(*LOCK).any()
    s.to_parquet(OUT + "cand2y.parquet"); print(len(s), s.date.min(), s.date.max())
