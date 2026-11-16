"""Mechanic NM-ETF: side-by-side final table (parent + spawned copies), splits, day types, concentration, groups,
removed-vs-kept trades, replay trade list. Educational only - not financial advice."""
import sys, json, pandas as pd, numpy as np
from sim import *
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2.date)); DAYSR = sorted(set(RC.date))
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d")
print(reg.columns.tolist()[:10])
V = {"parent": {}, "WB1 ret12>=+0.5%": {"extra": (("ret12", ">=", 0.5),)}, "WB2 ret3<=-0.90%": {"ret3": -0.90},
     "WB3 = WB1+WB2": {"ret3": -0.90, "extra": (("ret12", ">=", 0.5),)}}
rows = []; T = {}
for name, v in V.items():
    for test, (C, P, days) in {"replay": (RC, RP, DAYSR), "2y": (C2, P2, DAYS2)}.items():
        t = trades(C, P, v); T[(name, test)] = t
        s = stats(t); p = paired(t, T[("parent", test)], days)
        hold = np.median([mdiff(a, b) for a, b in zip(t.xt, t.ent)]) if len(t) else np.nan
        rows.append(dict(copy=name, test=test, **s, hold=hold, pair_day=p[0], pair_t=p[1]))
R = pd.DataFrame(rows); print(R.to_string()); R.to_csv(OUT + "final.csv", index=False)
for name in V:
    t = T[(name, "2y")]
    sp = t.groupby(np.where(t.date <= "2025-12-31", "train", "valid")).r.agg(["count", "mean"]).round(3)
    noapr = t[~t.date.str.startswith("2025-04")].r
    t2 = t.merge(reg[["date", "regime"]], on="date", how="left")
    col = t2.columns[-1]
    print(f"\n## {name}: {sp.to_dict()} | w/o Apr-2025 {noapr.mean():.3f} (n {len(noapr)}) | by {col}:",
          t2.groupby(col).r.agg(['count', 'mean']).round(3).to_dict(), "| inverse", t[t.symbol.isin(INVERSE)].r.agg(['count', 'mean']).round(3).to_dict(),
          "| non-inverse", t[~t.symbol.isin(INVERSE)].r.agg(['count', 'mean']).round(3).to_dict(),
          "| 3x", t[t.symbol.isin(LEV3)].r.agg(['count', 'mean']).round(3).to_dict(), "| 1x", t[~t.symbol.isin(LEV3)].r.agg(['count', 'mean']).round(3).to_dict(),
          "| exits", t.groupby('why').r.agg(['count', 'mean']).round(3).to_dict())
p = T[("parent", "2y")]; k = T[("WB1 ret12>=+0.5%", "2y")]
key = lambda d: set(zip(d.symbol, d.date))
rem = p[[x not in key(k) for x in zip(p.symbol, p.date)]]
from scipy import stats as st
print("\nWB1 removed trades (2y):", len(rem), rem.r.mean().round(3), "kept", len(k), k.r.mean().round(3), "Welch t", st.ttest_ind(k.r, rem.r, equal_var=False).statistic.round(2))
for sp_ in ("T", "V"):
    f = (lambda d: d.date <= "2025-12-31") if sp_ == "T" else (lambda d: d.date > "2025-12-31")
    print(sp_, "removed", rem[f(rem)].r.agg(['count', 'mean']).round(3).to_dict(), "kept", k[f(k)].r.agg(['count', 'mean']).round(3).to_dict())
rp = T[("parent", "replay")].merge(RC[["symbol", "date", "tod", "ret12", "vwap_atr"]], on=["symbol", "date", "tod"], how="left", suffixes=("", "_c"))
print(rp[["symbol", "date", "tod", "r", "why", "mfe", "ret12_c"]].round(3).to_string())
pd.to_pickle(T, OUT + "final_trades.pkl")
