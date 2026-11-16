"""Mechanic NM-ETF: 2-year candidate rows (module ETF list, bar close 13:00-15:00, ret3 <= -0.40%, adv20 >= $95M) with the
arena indicators (compute(context=False), as the module) + SPY/QQQ change since the 09:50 close at the same bar.
Open months only; the locked block 2024-11..2025-02 is never read. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd, pyarrow.dataset as ds
from multiprocessing import Pool
from common import OUT, SYMS, IND, LOCK
sys.path.insert(0, "/home/user/MCF/research/history2y")
from lib import months, DATA
from mcf.research.arena.indicators import compute

def one(m):
    d = ds.dataset(str(DATA / "frames" / f"month={m}"), format="parquet")
    df = d.to_table(filter=ds.field("symbol").isin(SYMS)).to_pandas()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    x = compute(df, names=IND, context=False)
    df = pd.concat([df[["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "r_long_t05s1"]], x], axis=1)
    ix = {}
    for e in ("SPY", "QQQ"):
        g = df[df.symbol == e][["date", "tod", "close"]]
        b = g[g.tod == 950].set_index("date").close
        ix[e] = g.assign(v=(g.close / g.date.map(b) - 1) * 100).set_index(["date", "tod"]).v
    keep = (df.tod >= 1300) & (df.tod <= 1500) & (df.adv20 >= 95e6) & (df.ret3 <= -0.40)
    r = df[keep].copy()
    k = pd.MultiIndex.from_arrays([r.date, r.tod])
    r["spy950"] = ix["SPY"].reindex(k).to_numpy(); r["qqq950"] = ix["QQQ"].reindex(k).to_numpy()
    r["month"] = m
    return r

if __name__ == "__main__":
    ms = [m for m in months() if m not in ("2024-11", "2024-12", "2025-01", "2025-02")]
    with Pool(4) as p:
        parts = p.map(one, ms)
    s = pd.concat(parts, ignore_index=True)
    assert not s.date.between(*LOCK).any()
    s.to_parquet(OUT + "cand2y.parquet"); print(len(s), s.date.min(), s.date.max())
