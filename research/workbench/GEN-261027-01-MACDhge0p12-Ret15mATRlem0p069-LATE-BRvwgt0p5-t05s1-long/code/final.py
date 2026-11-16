"""Mechanic GEN-261027-01: side-by-side final table (parent + WB1..WB5), splits, day types, robustness (no April 2025,
day cap 20, drop k best+worst days), removed-vs-kept, replay trade list. Educational only - not financial advice."""
import pandas as pd, numpy as np
from scipy import stats as st
from sim import *
import lib
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2.date)); DAYSR = sorted(set(RC.date))
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d"); REG = reg.set_index("date").regime
G = (("br_chg", "<=", 0.2),)
V = {"parent": {}, "WB1 window 14:00-14:30": {"hi": 1430}, "WB2 ADV >= $100M": {"adv": 100e6}, "WB3 breadth chg <= +0.20": {"extra": G},
     "WB4 = WB1+WB3": {"hi": 1430, "extra": G}, "WB5 = WB1+WB2+WB3": {"hi": 1430, "adv": 100e6, "extra": G}}
rows = []; T = {}
for name, v in V.items():
    for test, (C, P, days) in {"replay": (RC, RP, DAYSR), "2y": (C2, P2, DAYS2)}.items():
        t = trades(C, P, v); T[(name, test)] = t
        s = stats(t); p = paired(t, T[("parent", test)], days)
        rows.append(dict(copy=name, test=test, **s, pair_day=p[0], pair_t=p[1]))
R = pd.DataFrame(rows); pd.set_option("display.width", 250); print(R.to_string()); R.to_csv(OUT + "final.csv", index=False)
for name, v in V.items():
    t = T[(name, "2y")]; rg = t.date.map(REG)
    sp = t.groupby(np.where(t.date <= "2025-12-31", "train", "valid")).r.agg(["count", "mean"]).round(3)
    noapr = t[~t.date.str.startswith("2025-04")].r
    c20 = trades(C2, P2, {**v, "daycap": 20})
    dd = t.groupby("date").r.sum().sort_values(); x5 = t[~t.date.isin(set(dd.index[:5]) | set(dd.index[-5:]))].r
    print(f"\n## {name}: {sp.to_dict()} | up/flat/down", t.r.groupby(rg).agg(['count', 'mean']).round(3).to_dict(),
          f"| w/o Apr-2025 {noapr.mean():.3f} (n {len(noapr)}) | daycap20 {c20.r.mean():.3f} (n {len(c20)}, wob {stats(c20)['wobest']}) | drop 5+5 days {x5.mean():.3f}",
          "| exits", t.groupby('why').r.agg(['count', 'mean']).round(3).to_dict(), "| gross", round(t.gross.mean(), 3))
    tr = T[(name, "replay")]; print("   replay exits", tr.groupby('why').r.agg(['count', 'mean']).round(3).to_dict(), "sessions traded", tr.date.nunique())
key = lambda d: set(zip(d.symbol, d.date))
for nm in ("WB4 = WB1+WB3", "WB5 = WB1+WB2+WB3"):
    p = T[("parent", "2y")]; k = T[(nm, "2y")]
    rem = p[[x not in key(k) for x in zip(p.symbol, p.date)]]
    print(f"\n{nm} removed trades (2y):", len(rem), rem.r.mean().round(3), "kept", len(k), k.r.mean().round(3), "Welch t", st.ttest_ind(k.r, rem.r, equal_var=False).statistic.round(2))
    for sp_ in ("T", "V"):
        f = (lambda d: d.date <= "2025-12-31") if sp_ == "T" else (lambda d: d.date > "2025-12-31")
        print("  ", sp_, "removed", rem[f(rem)].r.agg(['count', 'mean']).round(3).to_dict(), "kept", k[f(k)].r.agg(['count', 'mean']).round(3).to_dict())
rp = T[("parent", "replay")]; w5 = key(T[("WB5 = WB1+WB2+WB3", "replay")]); w4 = key(T[("WB4 = WB1+WB3", "replay")])
rp["inWB4"] = [x in w4 for x in zip(rp.symbol, rp.date)]; rp["inWB5"] = [x in w5 for x in zip(rp.symbol, rp.date)]
print(rp.groupby("date").agg(n=("r", "size"), R=("r", "sum"), n4=("inWB4", "sum"), n5=("inWB5", "sum")).round(2))
pd.to_pickle(T, OUT + "final_trades.pkl")
