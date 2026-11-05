"""GATE1: point-in-time market state at each checkpoint (PLAN.md). Writes <scratch>/state.parquet.
Usage: python state.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd

M = Path("/home/user/MCF")
CPS = [585] + list(range(600, 931, 30))          # 09:45 (confirm only), 10:00..15:30, minutes since midnight
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())


def idx(sym):
    b = pd.read_parquet(M / "data/cache_hist/1Min" / f"{sym}.parquet")
    b["date"] = b.index.date
    b = b[~((b.date >= LOCK[0]) & (b.date <= LOCK[1]))].copy()
    b["m"] = b.index.hour * 60 + b.index.minute
    return b[(b.m >= 570) & (b.m < 960)]


def per_day(b, full):
    rows = []
    for d, g in b.groupby("date"):
        o = g.open.iloc[0]; c = g.close.values; m = g.m.values
        tp = (g.high + g.low + g.close).values / 3; v = g.volume.values
        cpv, cv = np.cumsum(tp * v), np.cumsum(v)
        hi, lo = np.maximum.accumulate(g.high.values), np.minimum.accumulate(g.low.values)
        close = c[-1] if m[-1] >= 955 else np.nan
        for T in CPS:
            i = np.searchsorted(m, T) - 1           # last bar with start < T (closed by T)
            if i < 0:
                continue
            j = np.searchsorted(m, T - 30) - 1
            r = dict(date=d, T=T, fo=c[i] / o - 1, px=c[i], close=close, oc=close / o - 1, open=o)
            if full:
                r.update(vw=c[i] / (cpv[i] / cv[i]) - 1, r30=c[i] / (c[j] if j >= 0 else o) - 1, rng=(hi[i] - lo[i]) / o)
            rows.append(r)
    return pd.DataFrame(rows)


def main(S):
    spy = per_day(idx("SPY"), True)
    for s in ["QQQ", "IWM"]:
        q = per_day(idx(s), False)[["date", "T", "fo"]].rename(columns={"fo": s.lower() + "_fo"})
        spy = spy.merge(q, on=["date", "T"], how="left")
    # gap
    dd = spy.groupby("date").agg(open=("open", "first"), close=("close", "first")).sort_index()
    dd["gap"] = dd.open / dd.close.shift(1) - 1
    spy = spy.merge(dd[["gap"]], left_on="date", right_index=True, how="left")
    # range vs prior-20-session median at same T
    spy = spy.sort_values(["T", "date"])
    spy["rng_med"] = spy.groupby("T").rng.transform(lambda x: x.shift(1).rolling(20, min_periods=10).median())
    spy["rngx"] = spy.rng / spy.rng_med
    # breadth (context tables, tod = bar end HHMM)
    ctx = pd.concat(pd.read_parquet(p) for p in sorted((M / "research/history2y/data/context").glob("month=*.parquet")))
    ctx["date"] = pd.to_datetime(ctx.date).dt.date
    ctx["T"] = (ctx.tod // 100) * 60 + ctx.tod % 100
    c2 = ctx[ctx["T"] == 900].copy(); c2["T"] = 930          # context ends at the 15:00 bar: 15:30 uses the 15:00 value
    ctx = pd.concat([ctx, c2])
    spy = spy.merge(ctx[["date", "T", "breadth", "breadth_open"]], on=["date", "T"], how="left")
    bo = spy.breadth_open.where(spy["T"] != 585, 0.5)   # 09:45: no 5-min breadth row in the context table (starts 09:50)
    up = (spy.fo >= 0.0015) & (spy.vw > 0) & (bo >= 0.5) & ((spy.qqq_fo > 0) | (spy.iwm_fo > 0))
    dn = (spy.fo <= -0.0015) & (spy.vw < 0) & (bo <= 0.5) & ((spy.qqq_fo < 0) | (spy.iwm_fo < 0))
    spy["st"] = np.where(up, 1, np.where(dn, -1, 0))
    spy = spy.sort_values(["date", "T"]).reset_index(drop=True)
    prev = spy.groupby("date").st.shift(1)
    spy["st2"] = np.where(spy.st == prev, spy.st, 0)
    spy["quiet"] = (spy.st == 0) & (spy.rngx < 0.75)
    spy["dtype"] = np.where(spy.oc >= 0.0025, "up", np.where(spy.oc <= -0.0025, "down", "quiet"))
    spy.to_parquet(Path(S) / "state.parquet")
    print(spy.date.nunique(), "days;", spy.breadth_open.isna().mean().round(3), "breadth missing")
    print(spy[spy["T"].isin([600, 660, 720])].groupby("T").st.value_counts().unstack())
    print(spy[spy.breadth_open.isna()].groupby("T").size())


if __name__ == "__main__":
    main(sys.argv[1])
