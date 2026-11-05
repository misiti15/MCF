"""COMP15/HC1: SPY point-in-time state every 15 min (09:45..15:30) from the 1-min cache (locked block filtered out
before use) + lab breadth_open (GATE1 convention), and the same for the live day 2026-11-05 from an Alpaca
market-data GET (breadth = the 200 Hunch names). Usage: python state15.py <scratch>. Educational only."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

M = Path("/home/user/MCF")
S = Path(sys.argv[1])
CPS = list(range(585, 931, 15))
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())


def rth(b):
    b = b.copy(); b["date"] = b.index.date
    b = b[~((b.date >= LOCK[0]) & (b.date <= LOCK[1]))]
    b["m"] = b.index.hour * 60 + b.index.minute
    return b[(b.m >= 570) & (b.m < 960)]


def per_day(b, full):
    rows = []
    for d, g in b.groupby("date"):
        o = g.open.iloc[0]; c = g.close.values; m = g.m.values
        tp = (g.high + g.low + g.close).values / 3; v = g.volume.values
        cpv, cv = np.cumsum(tp * v), np.cumsum(v)
        close = c[-1] if m[-1] >= 955 else np.nan
        for T in CPS:
            i = np.searchsorted(m, T) - 1
            if i < 0:
                continue
            r = dict(date=str(d), T=T, fo=c[i] / o - 1)
            if full:
                j30 = np.searchsorted(m, T + 30) - 1; j60 = np.searchsorted(m, T + 60) - 1
                r.update(px=c[i], open=o, close=close, vw=c[i] / (cpv[i] / max(cv[i], 1)) - 1,
                         px30=c[j30] if T + 30 <= 960 and m[-1] >= T + 29 else np.nan,
                         px60=c[j60] if T + 60 <= 960 and m[-1] >= T + 59 else np.nan)
            rows.append(r)
    return pd.DataFrame(rows)


def build(load, breadth):
    spy = per_day(rth(load("SPY")), True)
    for s in ["QQQ", "IWM"]:
        q = per_day(rth(load(s)), False).rename(columns={"fo": s.lower() + "_fo"})
        spy = spy.merge(q, on=["date", "T"], how="left")
    spy = spy.merge(breadth, on=["date", "T"], how="left")
    spy.loc[spy["T"] == 585, "breadth_open"] = 0.5            # no breadth row at 09:45 (as GATE1)
    return spy


def hist():
    load = lambda s: pd.read_parquet(M / "data/cache_hist/1Min" / f"{s}.parquet")
    ctx = pd.concat(pd.read_parquet(p) for p in sorted((M / "research/history2y/data/context").glob("month=*.parquet")))
    ctx["date"] = pd.to_datetime(ctx.date).dt.strftime("%Y-%m-%d")
    ctx["T"] = (ctx.tod // 100) * 60 + ctx.tod % 100
    add = [ctx[ctx["T"] == 900].assign(T=t) for t in (915, 930)]  # context ends at 15:00
    ctx = pd.concat([ctx] + add)
    return build(load, ctx[["date", "T", "breadth_open"]])


def live(day="2026-11-05"):
    from mcf.data.alpaca_data import fetch_bars
    import os
    U = [ln.split()[0] for ln in (M / "research/hunch/universe200.txt").read_text().splitlines() if ln.strip() and ln[0] != "#"]
    start = pd.Timestamp(day + " 09:30", tz="America/New_York"); end = pd.Timestamp(day + " 16:00", tz="America/New_York")
    feed = os.environ.get("ALPACA_DATA_FEED", "sip")
    bars = {}
    syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + U))
    for i in range(0, len(syms), 100):
        bars.update(fetch_bars(syms[i:i + 100], start.to_pydatetime(), end.to_pydatetime(), feed=feed))
    for k, b in bars.items():
        b.index = pd.to_datetime(b.index).tz_convert("America/New_York")
    rows = []
    for T in CPS:
        up = []
        for s in U:
            b = bars.get(s)
            if b is None or not len(b):
                continue
            m = b.index.hour * 60 + b.index.minute
            x = b[(m >= 570) & (m < T)]
            if len(x):
                up.append(x.close.iloc[-1] > b.open.iloc[0])
        rows.append(dict(date=day, T=T, breadth_open=np.mean(up) if up else np.nan))
    pd.concat([b.assign(sym=k) for k, b in bars.items()]).to_parquet(S / "live_1105_bars.parquet")
    return build(lambda s: bars[s], pd.DataFrame(rows)), len(bars)


if __name__ == "__main__":
    sys.path.insert(0, str(M))
    h = hist(); h.to_parquet(S / "state15.parquet"); print(h.date.nunique(), "days", h.breadth_open.isna().mean())
    lv, n = live(); lv.to_parquet(S / "state15_live.parquet"); print("live symbols", n); print(lv.round(4).to_string())
