"""Mechanic GEN-261026-03: side-by-side final table (parent + spawned copies), splits, day types, families, removed-vs-kept,
live trades kept / skipped, curve PNG. Educational only - not financial advice."""
import sys, json, pandas as pd, numpy as np
from sim import *
from common import WT, SETUP
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib
from scipy import stats as st
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2.date)); DAYSR = sorted(set(RC.date))
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d")
FPC = [["from_pc_atr", "<=", -1.3]]
V = {"parent": {}, "WB1 from_pc<=-1.3": {"extra": tuple(map(tuple, FPC))}, "WB2 end 13:00": {"hi": 1300},
     "WB3 = WB1+WB2": {"hi": 1300, "extra": tuple(map(tuple, FPC))}}
rows = []; T = {}
for name, v in V.items():
    for test, (C, P, days) in {"replay": (RC, RP, DAYSR), "2y": (C2, P2, DAYS2)}.items():
        t = trades(C, P, v); T[(name, test)] = t
        s = stats(t); p = paired(t, T[("parent", test)], days)
        hold = np.median([mdiff(a, b) for a, b in zip(t.xt, t.ent)]) if len(t) else np.nan
        x = dict(copy=name, test=test, **s, hold=hold, pair_day=p[0], pair_t=p[1])
        if test == "2y":
            x["T"] = round(t[t.date <= "2025-12-31"].r.mean(), 3); x["V"] = round(t[t.date > "2025-12-31"].r.mean(), 3)
        rows.append(x)
R = pd.DataFrame(rows); print(R.to_string()); R.to_csv(OUT + "final.csv", index=False)
for name in V:
    t = T[(name, "2y")].merge(reg[["date", "regime"]], on="date", how="left")
    t["tb"] = pd.cut(t.tod, [1125, 1200, 1230, 1300, 1330, 1400]); t["px"] = pd.cut(t.close, [0, 50, 150, 400, 1e5])
    print(f"\n## {name} 2y by day type", t.groupby("regime").r.agg(["count", "mean"]).round(3).to_dict(),
          "\n by tod", t.groupby("tb", observed=True).r.agg(["count", "mean"]).round(3).to_dict(),
          "\n by price", t.groupby("px", observed=True).r.agg(["count", "mean"]).round(3).to_dict(),
          "\n exits", t.groupby("why").r.agg(["count", "mean"]).round(3).to_dict(),
          "\n w/o best month", round(t[t.date.str[:7] != t.groupby(t.date.str[:7]).r.sum().idxmax()].r.mean(), 3))
p = T[("parent", "2y")]; k = T[("WB1 from_pc<=-1.3", "2y")]
kk = set(zip(k.symbol, k.date)); rem = p[[x not in kk for x in zip(p.symbol, p.date)]]
print("\nWB1 removed (2y):", len(rem), round(rem.r.mean(), 3), "kept", len(k), round(k.r.mean(), 3), "Welch t", round(st.ttest_ind(k.r, rem.r, equal_var=False).statistic, 2))
for nm, f in (("T", lambda d: d.date <= "2025-12-31"), ("V", lambda d: d.date > "2025-12-31")):
    print(nm, "removed", rem[f(rem)].r.agg(["count", "mean"]).round(3).to_dict(), "kept", k[f(k)].r.agg(["count", "mean"]).round(3).to_dict())
# the live trades (Gen, no cost filter): sensor values and which copies keep them
L = pd.read_pickle(OUT + "live.pkl")
rp = trades(RC, RP, {"cf": None})
m = L.merge(rp[["symbol", "date", "tod", "from_pc_atr", "fromOpen_atr", "flow3", "breadth_open", "gap_atr", "costR" if "costR" in rp else "close", "atr_d"]],
            on=["symbol", "date"], how="left")
m["costR"] = (2 * (0.01 + m.close * 1e-4) + 0.02) / (0.25 * m.atr_d)
m["WB1"] = m.from_pc_atr <= -1.3; m["WB2"] = m.tod <= 1300; m["CF"] = m.costR <= 0.15
print(m[["symbol", "date", "tod", "r", "exit_reason", "mfe_r", "from_pc_atr", "fromOpen_atr", "flow3", "gap_atr", "costR", "CF", "WB1", "WB2"]].sort_values("r").round(2).to_string())
for c in ("CF", "WB1", "WB2"):
    print(c, "keeps", m[m[c]].r.agg(["count", "mean", "sum"]).round(3).to_dict(), "skips", m[~m[c]].r.agg(["count", "mean", "sum"]).round(3).to_dict())
m.to_parquet(OUT + "live_sensors.parquet")
pd.to_pickle(T, OUT + "final_trades.pkl")
# threshold curve PNG for WB1
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
xs = [None, -0.8, -1.0, -1.1, -1.2, -1.3, -1.4, -1.5, -1.75, -2.0]; ys = {"2y all": [], "2y train": [], "2y valid": [], "replay": []}
for x in xs:
    v = {} if x is None else {"extra": (("from_pc_atr", "<=", x),)}
    t = trades(C2, P2, v); r = trades(RC, RP, v)
    ys["2y all"].append(t.r.mean()); ys["2y train"].append(t[t.date <= "2025-12-31"].r.mean()); ys["2y valid"].append(t[t.date > "2025-12-31"].r.mean()); ys["replay"].append(r.r.mean())
fig, ax = plt.subplots(figsize=(8, 4.4), dpi=130)
lab = ["parent\n(none)"] + [f"{x}" for x in xs[1:]]
for (k_, y), c in zip(ys.items(), ["#1f2937", "#2563eb", "#d97706", "#059669"]):
    ax.plot(range(len(xs)), y, marker="o", label=k_, color=c, lw=2 if k_ == "2y all" else 1.2)
ax.axhline(0, color="#9ca3af", lw=0.8); ax.axvline(5, color="#dc2626", lw=0.8, ls="--"); ax.text(5.05, ax.get_ylim()[1] * 0.92, "WB1 -1.3", color="#dc2626", size=8)
ax.set_xticks(range(len(xs)), lab, size=8); ax.set_xlabel("P11b: close vs prior close, in daily ATRs, at most"); ax.set_ylabel("avg R per trade after costs (LR8)")
ax.set_title("Lunch New-Low Short - WB1 threshold curve (costs in; locked block never read)", size=10); ax.legend(fontsize=8)
fig.text(0.01, 0.01, "Educational only - not financial advice.", size=7, color="#6b7280"); fig.tight_layout()
fig.savefig(f"{WT}/research/workbench/{SETUP}/{SETUP}_wb1_frompc_curve.png"); print({k_: [round(v, 3) for v in y] for k_, y in ys.items()})
