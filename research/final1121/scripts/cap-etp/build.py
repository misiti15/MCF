"""cap-etp: build 5-min ETP/index frames from the 1-minute caches (read in place, locked block filtered at read).
T1 = data/cache_hist/1Min (2024-10 + 2025-03.. ; the 2024-11-01..2025-02-28 block is filtered out by pyarrow and asserted),
T2 = data/cache_fresh/1Min (2023-01-03..2024-09-13). Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads

TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
W = Path(__file__).resolve().parent
INV = "SQQQ SPXU SPXS SDS PSQ QID SDOW SPDN RWM TZA SOXS LABD UVXY VXX".split()
BULL = "TQQQ SPXL UPRO QLD SSO UDOW TNA SOXL TECL".split()
IDX = ["SPY", "QQQ", "IWM"]
SRC = {"T1": Path("/home/user/MCF/data/cache_hist/1Min"), "T2": Path("/home/user/MCF/data/cache_fresh/1Min")}


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked row"


def bars1(sym, test):
    p = SRC[test] / f"{sym}.parquet"
    if not p.exists():
        return None
    d = pads.dataset(str(p), format="parquet")
    fld = pads.field("__index_level_0__")
    L0, L1 = pd.Timestamp(LOCK[0], tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    b = d.to_table(filter=(fld < L0) | (fld >= L1)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def frame(sym, test):
    b = bars1(sym, test)
    if b is None or not len(b):
        return None
    x = b.copy()
    x["date"] = x.index.date.astype(str)
    mn = x.index.hour * 60 + x.index.minute
    lab = ((mn - 570) // 5 + 1) * 5 + 570
    x["tod"] = (lab // 60) * 100 + lab % 60
    x["tp"] = (x.high + x.low + x.close) / 3
    x["pv"] = x.tp * x.volume
    g = x.groupby(["date", "tod"], sort=True).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                                  close=("close", "last"), v=("volume", "sum"), pv=("pv", "sum")).reset_index()
    g["dopen"] = g.groupby("date").open.transform("first")
    g["cpv"] = g.groupby("date").pv.cumsum()
    g["cv"] = g.groupby("date").v.cumsum()
    g["vwap"] = g.cpv / g.cv.replace(0, np.nan)
    g["hod_prev"] = g.groupby("date").high.transform(lambda s: s.cummax().shift(1))
    g["lod_prev"] = g.groupby("date").low.transform(lambda s: s.cummin().shift(1))
    g["fo"] = (g.close / g.dopen - 1) * 100
    g["vw"] = (g.close / g.vwap - 1) * 100
    # daily table: ATR14 (simple mean of prior 14 true ranges), prior close, adv20 (prior 20 sessions RTH $ volume)
    d = x.groupby("date").agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"),
                              dv=("pv", "sum")).reset_index()
    pc = d.c.shift(1)
    tr = np.maximum(d.h - d.l, np.maximum((d.h - pc).abs(), (d.l - pc).abs()))
    d["atr_d"] = tr.shift(1).rolling(14, min_periods=5).mean()
    d["pclose"] = pc
    d["adv20"] = d.dv.shift(1).rolling(20, min_periods=5).mean()
    d["gap"] = (d.o / pc - 1) * 100
    # split guard: drop 15 sessions after any |close-to-open| jump > 40% (unadjusted reverse split)
    big = np.flatnonzero(d.gap.abs().to_numpy() > 40)
    bad = set()
    for i in big:
        bad.update(d.date.iloc[i:i + 16].tolist())
    g = g.merge(d[["date", "atr_d", "adv20", "gap", "pclose"]], on="date", how="left")
    g = g[~g.date.isin(bad)]
    g["symbol"] = sym
    return g


if __name__ == "__main__":
    test = sys.argv[1]
    out = []
    for s in INV + BULL + IDX:
        f = frame(s, test)
        if f is None:
            print("missing", s, test)
            continue
        out.append(f)
        print(s, len(f), f.date.min(), f.date.max(), flush=True)
    F = pd.concat(out, ignore_index=True)
    no_locked(F.date.unique())
    F.to_parquet(W / f"frames_{test}.parquet")
