"""PNG for the morning-low study. Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
H = Path(__file__).resolve().parent
W = pd.read_csv(H / "q1_windows.csv"); C = pd.read_csv(H / "q2_cells.csv", dtype={"h": str}); C2 = pd.read_csv(H / "q2_setup_cells.csv", dtype={"h": str})
w = W[(W.group == "all") & (W.split == "ALL")]
lab = [f"{a}-{b}" for a, b in zip(w.win, C[(C.defn == "D1_reclaim_wstart") & (C.sym == "SPY") & (C.h == "60") & (C.split == "ALL")].win)]
x = np.arange(len(w))
fig, ax = plt.subplots(4, 1, figsize=(11, 14), sharex=True)
ax[0].bar(x, w.share * 100, color="#3b6ea5", label="actual share of days (SPY, 461 sessions)")
ax[0].plot(x, w.null_shuffle * 100, "o-", color="#d08c2e", label="null: shuffled 1-min bars per day")
ax[0].plot(x, w.null_arcsine * 100, "s--", color="#777777", label="null: random-walk argmin (arcsine)")
ax[0].set_ylabel("% of days")
ax[0].set_title("Where is the 09:50-11:30 SPY low? Share of days with the low inside each 25-min window")
ax[0].legend(fontsize=8, frameon=False)
cols = {"D1_reclaim_wstart": "#3b6ea5", "D2_up15bp_off_wlow": "#d08c2e", "D3_above_vwap950": "#5a9e6f"}
names = {"D1_reclaim_wstart": "D1 new low in W, back above W-start price", "D2_up15bp_off_wlow": "D2 new low in W, +0.15% off W low",
         "D3_above_vwap950": "D3 new low in W, above VWAP since 09:50"}
for k, h in enumerate(["60", "90"]):
    a = ax[k + 1]
    for j, (d, c) in enumerate(cols.items()):
        s = C[(C.defn == d) & (C.sym == "SPY") & (C.h == h) & (C.split == "ALL")]
        a.bar(x + (j - 1) * 0.27, s.excess_bps, 0.27, color=c, label=names[d] if k == 0 else None)
        for xi, (e, t) in enumerate(zip(s.excess_bps, s.t)):
            if abs(t) >= 2:
                a.text(xi + (j - 1) * 0.27, e + (1 if e > 0 else -3), f"t{t:.1f}", ha="center", fontsize=6)
    a.axhline(0, color="black", lw=0.6)
    a.set_ylabel(f"SPY +{h} min, excess bps\nvs same minute all days")
    a.set_title(f"After a turn at the end of W: SPY forward return +{h} min minus the all-days return from the same minute "
                f"(any new low; bar for N=1155 tries: t >= 3.76)", fontsize=9)
ax[1].legend(fontsize=8, frameon=False)
a = ax[3]
for j, (X, c) in enumerate([(10, "#b9c9dd"), (25, "#7f9cc0")]):
    s_ = C2[(C2.X_bps == X) & (C2.defn == "D1_reclaim_wstart") & (C2.sym == "SPY") & (C2.h == "60") & (C2.split == "ALL")]
    a.bar(x + (j - 0.5) * 0.4, s_.share_a_nosetup * 100, 0.4, color=c, label=f"(a) NO-SETUP share: no new 09:50+ low >= {X} bps under the 09:50 price in W")
s_ = C2[(C2.X_bps == 10) & (C2.defn == "D1_reclaim_wstart") & (C2.sym == "SPY") & (C2.h == "60") & (C2.split == "ALL")]
a.plot(x, s_.hit_b_over_bc * 100, "o-", color="#c0392b", label="turn worked b/(b+c), D1, X=10, SPY +60 (no lower low and up at exit)")
a.axhline(50, color="#c0392b", lw=0.5, ls=":")
a.set_ylabel("% of days / % of turns"); a.set_ylim(0, 100)
a.set_title("Owner 11-16: days with no qualifying dip are 'no setup', not failures - their share, and the hit rate over setup days only", fontsize=9)
a.legend(fontsize=7, frameon=False, loc="lower left")
ax[3].set_xticks(x); ax[3].set_xticklabels(lab, rotation=45, fontsize=8)
ax[3].set_xlabel("25-minute window W (start-end = decision time); locked block 2024-11..2025-02 excluded")
fig.text(0.01, 0.005, "Educational only - not financial advice. Costs not in these bars (index returns); see NOTES.md for the 3x trade with costs.", fontsize=7)
fig.tight_layout(rect=(0, 0.015, 1, 1))
fig.savefig(H / "morning_low.png", dpi=110)
