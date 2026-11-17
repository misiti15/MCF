"""FREQ parity: the new pipeline vs the first pass (parent on the cached symbols; replay on 10-19..11-13). Educational only."""
from sim2 import *
D = load(); C, P, d2 = D["y2"]; RC, RP, dr = D["rep"]
cached = sorted(set(C[C.src == "cache"].symbol) & set(SETS["PAR"]))
t = trades(C, P, dict(univ=tuple(cached))); print("2y parent cached-only", stats(t, len(d2)))
t = trades(C, P, {}); print("2y parent complete", stats(t, len(d2)), "sessions", len(d2))
print(t.groupby(t.symbol.isin(cached)).r.agg(["count", "mean"]))
r = trades(RC, RP, {}); r13 = r[r.date <= "2026-11-13"]
print("replay complete", stats(r, len(dr)), "sessions", len(dr)); print("replay to 11-13", stats(r13, 20))
old = pd.read_pickle(SC.replace("etffreq/", "mech-nmetf/") + "final_trades.pkl")[("parent", "replay")]
a = set(zip(old.symbol, old.date)); b = set(zip(r13.symbol, r13.date)); print("old-only", a - b, "new-only", b - a)
print(r[["symbol", "date", "tod", "r", "why"]].to_string())
