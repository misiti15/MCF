"""Mechanic NM-ETF: the new sensor's threshold curve (2-year, costs in), parent vs ret12 >= x. Educational only - not financial advice."""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, numpy as np
from sim import *
D = load(); C2, P2 = D["y2"]
xs = [None, -0.5, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5]; rows = []
for x in xs:
    t = trades(C2, P2, {} if x is None else {"extra": (("ret12", ">=", x),)})
    T = t[t.date <= "2025-12-31"].r; V = t[t.date > "2025-12-31"].r; s = stats(t)
    rows.append((x, s["avg"], s["wobest"], T.mean(), V.mean(), s["n"]))
lab = ["parent\n(no ret12)" if x is None else f">= {x:+.2f}%" for x in xs]
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=110); fig.patch.set_facecolor("#f7f7f5"); ax.set_facecolor("#ffffff")
X = np.arange(len(xs))
for i, (k, c) in enumerate([(1, "#1b1b1b"), (2, "#666666"), (3, "#2563eb"), (4, "#d97706")]):
    ax.plot(X, [r[k] for r in rows], "-o", color=c, label=["2-year avg R", "2-year avg R w/o best day", "train (..2025-12)", "valid (2026-01..10-16)"][i])
for xi, r in zip(X, rows): ax.annotate(f"n {r[5]}", (xi, r[1]), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=8)
ax.axhline(0, color="#e3e3e0"); ax.axvline(4, color="#15803d", ls="--", lw=1); ax.text(4.05, ax.get_ylim()[1] * 0.92, "WB1: ret12 >= +0.5%", color="#15803d", fontsize=9)
ax.set_xticks(X, lab, fontsize=8); ax.set_ylabel("avg R per trade after costs (LR8)")
ax.set_title("Late-Day ETF Dip Buy — new sensor P10b: 60-min return (incl. the dip) at the signal bar\n"
             "2-year backtest 2024-10..2026-10-16, locked block 2024-11..2025-02 never read", fontsize=10)
ax.legend(fontsize=8, loc="lower right"); fig.text(0.01, 0.01, "Educational only — not financial advice", fontsize=7, color="#666666")
fig.tight_layout(); fig.savefig(OUT + "NM-ETF-late-dip-di-long_wb1_ret12_curve.png")
print(rows)
