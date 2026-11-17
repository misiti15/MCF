"""Mechanic NM-RWN5: side-by-side final table (parent + copies + counted experimental layers), plateau grid, splits, day
types, removed-vs-kept, live trades kept / skipped, volumeRatio curve PNG. Educational only - not financial advice."""
import sys, pandas as pd, numpy as np
from sim import *
from common import WT, SETUP
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib
from scipy import stats as st
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2[C2.dow == 0].date)); DAYSR = sorted(set(RC[RC.dow == 0].date)) or ["2026-10-19"]
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d")
VR = (("volumeRatio", ">=", 0.45),)
V = {"parent": {}, "WB1 volR>=0.45": {"extra": VR}, "WB2 start 10:05": {"lo": 1005},
     "WB3 = WB1+WB2": {"lo": 1005, "extra": VR},
     "exp WB3 + SPY>=09:50 close": {"lo": 1005, "extra": VR + (("spy950", ">=", 0.0),)},
     "exp WB3 + target 1.25R": {"lo": 1005, "extra": VR, "tk": 1.25}}
rows = []; T = {}
for name, v in V.items():
    for test, (C, P, days) in {"replay": (RC, RP, DAYSR), "2y": (C2, P2, DAYS2)}.items():
        t = trades(C, P, v); T[(name, test)] = t
        s = stats(t); p = paired(t, T[("parent", test)], days)
        hold = np.median([mdiff(a, b) for a, b in zip(t.xt, t.ent)]) if len(t) else np.nan
        x = dict(copy=name, test=test, **s, hold=hold, pair_day=p[0], pair_t=p[1])
        if test == "2y":
            x["T"] = round(t[t.date <= "2025-12-31"].r.mean(), 3); x["V"] = round(t[t.date > "2025-12-31"].r.mean(), 3)
            x["xApr25"] = round(t[~t.date.str.startswith("2025-04")].r.mean(), 3)
        rows.append(x)
R = pd.DataFrame(rows); pd.set_option("display.width", 250); print(R.to_string()); R.to_csv(OUT + "final.csv", index=False)
print("\n## plateau around WB3 (start x volR): 2y avg / wob | replay avg / wob")
for lo in (1000, 1005, 1010):
    for vr in (0.35, 0.45, 0.55):
        a = trades(C2, P2, {"lo": lo, "extra": (("volumeRatio", ">=", vr),)}); b = trades(RC, RP, {"lo": lo, "extra": (("volumeRatio", ">=", vr),)})
        print(lo, vr, stats(a)["avg"], stats(a)["wobest"], "|", stats(b)["avg"], stats(b)["wobest"], len(a), len(b))
for name in ("parent", "WB1 volR>=0.45", "WB2 start 10:05", "WB3 = WB1+WB2"):
    t = T[(name, "2y")].merge(reg[["date", "regime"]], on="date", how="left")
    t["tb"] = pd.cut(t.tod, [945, 1000, 1030, 1100, 1130]); t["px"] = pd.cut(t.close, [0, 50, 150, 300, 1e5])
    print(f"\n## {name} 2y by day type", t.groupby("regime").r.agg(["count", "mean"]).round(3).to_dict(),
          "\n by tod", t.groupby("tb", observed=True).r.agg(["count", "mean"]).round(3).to_dict(),
          "\n by price", t.groupby("px", observed=True).r.agg(["count", "mean"]).round(3).to_dict(),
          "\n exits", t.groupby("why").r.agg(["count", "mean"]).round(3).to_dict(),
          "\n w/o best month", round(t[t.date.str[:7] != t.groupby(t.date.str[:7]).r.sum().idxmax()].r.mean(), 3))
p = T[("parent", "2y")]; k = T[("WB3 = WB1+WB2", "2y")]
kk = set(zip(k.symbol, k.date)); rem = p[[x not in kk for x in zip(p.symbol, p.date)]]
pk = p[[x in kk for x in zip(p.symbol, p.date)]]
print("\nWB3 removed parent trades (2y):", len(rem), round(rem.r.mean(), 3), "parent trades kept", len(pk), round(pk.r.mean(), 3),
      "Welch t", round(st.ttest_ind(pk.r, rem.r, equal_var=False).statistic, 2), "| new later entries", len(k) - len(pk))
for nm, f in (("T", lambda d: d.date <= "2025-12-31"), ("V", lambda d: d.date > "2025-12-31")):
    print(nm, "removed", rem[f(rem)].r.agg(["count", "mean"]).round(3).to_dict(), "kept", pk[f(pk)].r.agg(["count", "mean"]).round(3).to_dict())
# other weekdays with the WB3 parts (is the Monday part still needed?)
for dw in range(1, 5):
    x = trades(C2, P2, {"lo": 1005, "extra": VR, "dows": (dw,)}); print("WB3 parts on dow", dw, stats(x)["n"], stats(x)["avg"])
# live trades: sensor values and which copies keep them
L = pd.read_pickle(OUT + "live.pkl")
rp = trades(RC, RP, {"cf": None})
m = L[["acct", "symbol", "date", "R", "exit_reason", "mfe_r", "entry"]].merge(
    rp[["symbol", "date", "tod", "r", "volumeRatio", "spy950", "fromOpen", "close", "upper_wick"]], on=["symbol", "date"], how="left")
m["WB1"] = m.volumeRatio >= 0.45; m["WB2"] = m.tod >= 1005; m["WB3"] = m.WB1 & m.WB2
print(m.sort_values("R").round(3).to_string())
for c in ("WB1", "WB2", "WB3"):
    print(c, "keeps", m[m[c]].R.agg(["count", "mean", "sum"]).round(3).to_dict(), "skips", m[~m[c]].R.agg(["count", "mean", "sum"]).round(3).to_dict())
# replay trades of WB3 vs parent
print(T[("WB3 = WB1+WB2", "replay")][["symbol", "date", "tod", "r", "why", "volumeRatio"]].round(3).to_string())
pd.to_pickle(T, OUT + "final_trades.pkl")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
xs = [None, 0.25, 0.35, 0.40, 0.45, 0.50, 0.55, 0.65, 0.75]; ys = {"2y all": [], "2y train": [], "2y valid": [], "replay": []}
for x in xs:
    v = {} if x is None else {"extra": (("volumeRatio", ">=", x),)}
    t = trades(C2, P2, v); r = trades(RC, RP, v)
    ys["2y all"].append(t.r.mean()); ys["2y train"].append(t[t.date <= "2025-12-31"].r.mean()); ys["2y valid"].append(t[t.date > "2025-12-31"].r.mean()); ys["replay"].append(r.r.mean())
fig, ax = plt.subplots(figsize=(8, 4.4), dpi=130)
lab = ["parent\n(none)"] + [f"{x}" for x in xs[1:]]
for (k_, y), c in zip(ys.items(), ["#1f2937", "#2563eb", "#d97706", "#059669"]):
    ax.plot(range(len(xs)), y, marker="o", label=k_, color=c, lw=2 if k_ == "2y all" else 1.2)
ax.axhline(0, color="#9ca3af", lw=0.8); ax.axvline(4, color="#dc2626", lw=0.8, ls="--"); ax.text(4.05, ax.get_ylim()[1] * 0.92, "WB1 0.45", color="#dc2626", size=8)
ax.set_xticks(range(len(xs)), lab, size=8); ax.set_xlabel("P9b: signal-bar volume / 20-bar average volume, at least"); ax.set_ylabel("avg R per trade after costs (LR8)")
ax.set_title("Monday Weak-RS NS3 Short - WB1 threshold curve (costs in; locked block never read)", size=10); ax.legend(fontsize=8)
fig.text(0.01, 0.01, "Educational only - not financial advice.", size=7, color="#6b7280"); fig.tight_layout()
fig.savefig(f"{WT}/research/workbench/{SETUP}/{SETUP}_wb1_volratio_curve.png"); print({k_: [round(v, 3) for v in y] for k_, y in ys.items()})
