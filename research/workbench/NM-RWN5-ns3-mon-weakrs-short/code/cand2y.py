"""Mechanic NM-RWN5: 2-year candidate rows from the lab frames (research/history2y, lib.load_month(context=True) - the
same frame + context columns the module reads live), every weekday, inside the loose BOX (common.py). Adds prev_vwap
(previous 5-minute bar's vwapDistPct, same symbol-day, as the module's _prev), spy950 / fo950 (SPY's and the stock's %
move since the 09:50 bar close - owner rule: market state measured after 09:50) and dow. Open months only; the locked
block 2024-11..2025-02 is never read. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, LOCK, BOX, COLS
sys.path.insert(0, "/home/user/MCF/research/history2y")
from lib import months, load_month

def one(m):
    df = load_month(m, context=True)
    df["date"] = df["date"].astype(str)
    key = df.symbol + "|" + df.date
    df["prev_vwap"] = df.groupby(key, sort=False).vwapDistPct.shift(1)
    c950 = df[df.tod == 950].set_index(["symbol", "date"]).close
    df["fo950"] = (df.close / pd.MultiIndex.from_arrays([df.symbol, df.date]).map(c950).to_numpy() - 1) * 100
    s = df[df.symbol == "SPY"].set_index(["date", "tod"])
    spy950 = s.close / s.close.xs(950, level="tod").reindex(s.index.get_level_values(0)).to_numpy() - 1
    df["spy950"] = pd.MultiIndex.from_arrays([df.date, df.tod]).map(spy950 * 100).to_numpy()
    df["dow"] = pd.to_datetime(df.date).dt.dayofweek
    keep = (df.tod >= BOX["lo"]) & (df.tod <= BOX["hi"]) & (df.adv20 >= BOX["adv"]) & (df.vwapDistPct > 0) \
        & (df.prev_vwap <= 0) & (df.fromOpen < BOX["fo"])
    r = df.loc[keep, [c for c in COLS if c in df.columns]].copy()
    print(m, len(r), flush=True)
    return r

if __name__ == "__main__":
    ms = [m for m in months() if m not in ("2024-11", "2024-12", "2025-01", "2025-02")]
    with Pool(2) as p:
        parts = p.map(one, ms)
    s = pd.concat(parts, ignore_index=True)
    assert not s.date.between(*LOCK).any()
    s.to_parquet(OUT + "cand2y.parquet"); print(len(s), s.date.min(), s.date.max(), s.groupby(["symbol", "date"]).ngroups)
