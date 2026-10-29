"""MH2 earnings-sympathy table for the 2-year test (Move Hunt 2026-10-29 precursor 2).
Event: a symbol on the earnings calendar (research/bdi/earnings/data/earnings_cal.parquet) whose reaction day D (the
calendar date or the next weekday, whichever has the larger |gap|; the calendar time field is mostly missing) gaps
>= 4% (open vs prior close; known at 09:30). Peers: the 5 symbols with the highest correlation of daily close-to-close
returns over the 60 sessions before D (data through D-1 only; corr >= 0.5). Direction = sign of the reporter's gap.
Peers pointed both ways on the same day are dropped. Reads history2y daily via lib.daily() (locked block excluded).
Usage: python sympathy.py [out.parquet]. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/user/MCF/research/bdi/1029/sympathy.parquet")
GAP, TOPK, CMIN, LOOK = 0.04, 5, 0.5, 60
d = lib.daily()
d["date"] = pd.to_datetime(d["date"])
C = d.pivot(index="date", columns="symbol", values="close").sort_index()
O = d.pivot(index="date", columns="symbol", values="open").reindex(C.index)
ret = C.pct_change(fill_method=None)
gap = O / C.shift(1) - 1
dates = C.index
e = pd.read_parquet("/home/user/MCF/research/bdi/earnings/data/earnings_cal.parquet")
e["date"] = pd.to_datetime(e["date"]); e = e[e.symbol.isin(C.columns) & (e.date >= dates[0]) & (e.date <= dates[-1])]
rows = []
for _, r in e.drop_duplicates(["symbol", "date"]).iterrows():
    i = dates.searchsorted(r.date)
    cand = [j for j in (i, i + 1) if j < len(dates) and (j != i or dates[i] == r.date)]
    if not cand:
        continue
    g = [(abs(gap.iat[j, gap.columns.get_loc(r.symbol)]) if np.isfinite(gap.iat[j, gap.columns.get_loc(r.symbol)]) else -1, j) for j in cand]
    ga, j = max(g)
    if ga < GAP or j < 30:
        continue
    win = ret.iloc[max(0, j - LOOK):j]
    x = win[r.symbol]
    if x.notna().sum() < 30:
        continue
    cor = win.corrwith(x, min_periods=30) if False else win.apply(lambda s: s.corr(x, min_periods=30))
    cor = cor.drop(r.symbol).dropna().sort_values(ascending=False).head(TOPK)
    cor = cor[cor >= CMIN]
    sg = int(np.sign(gap.iat[j, gap.columns.get_loc(r.symbol)]))
    for p, cv in cor.items():
        rows.append(dict(date=dates[j].date(), symbol=p, dir=sg, reporter=r.symbol, corr=round(cv, 3), rep_gap=round(ga * sg, 4)))
T = pd.DataFrame(rows)
k = T.groupby(["date", "symbol"]).dir.agg(lambda s: s.iloc[0] if s.nunique() == 1 else 0).rename("dir_final")
T = T.merge(k.reset_index(), on=["date", "symbol"]); T = T[T.dir_final != 0]
T = T.sort_values("corr", ascending=False).drop_duplicates(["date", "symbol"])
T.to_parquet(OUT, index=False)
print(len(T), "peer symbol-days;", T.date.nunique(), "days; long", (T.dir > 0).sum(), "short", (T.dir < 0).sum())
