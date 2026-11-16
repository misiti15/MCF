"""Figure for the drop-rebound study (run after study.py and stocks.py). Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

H = Path(__file__).resolve().parent
B, O, GR, INK, MUT = "#2a78d6", "#eb6834", "#b9b8b2", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GR, "axes.labelcolor": MUT, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.spines.top": False, "axes.spines.right": False})
S = pd.read_csv(H / "scan_days.csv"); S = S[S.defn == "from_runhigh"]
S["q"] = pd.PeriodIndex(pd.to_datetime(S.day), freq="Q").astype(str)
C = pd.read_csv(H / "fwd_cells.csv", dtype={"h": str}); G = pd.read_csv(H / "trade_grid.csv"); GS = pd.read_csv(H / "trade_grid_stocks.csv")
fig, ax = plt.subplots(2, 2, figsize=(12, 8.2), facecolor="#fcfcfb")
for a in ax.flat: a.set_facecolor("#fcfcfb")

a = ax[0, 0]
q = S.groupby("q").agg(drop=("drop", "sum"), trig=("trig", "sum"), n=("day", "size"))
x = np.arange(len(q))
a.bar(x - 0.2, q["drop"], 0.38, color=GR, label="SPY fell >= 0.65% in the first hour")
a.bar(x + 0.2, q["trig"], 0.38, color=B, label="... and rebounded >= 0.5% by 12:00 (signal)")
a.set_xticks(x, q.index, rotation=60, fontsize=7); a.set_ylabel("days per quarter")
a.set_title("How often: 81 drop days, 57 signals in 461 sessions (12%)\n(locked block Nov-24..Feb-25 excluded)", loc="left", color=INK)
a.legend(frameon=False, fontsize=8)

a = ax[0, 1]
T = S[S.trig]
tm = lambda s: pd.to_datetime(s, format="%H:%M")
bins = pd.date_range("1900-01-01 09:30", "1900-01-01 12:00", freq="10min")
a.hist(tm(T.low_time), bins=bins, color=GR, label="time of the low", rwidth=0.9)
a.hist(tm(T.trig_time), bins=bins, color=B, alpha=0.85, label="signal (+0.5% off the low)", rwidth=0.6)
a.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M")); a.set_ylabel("signal days")
a.set_title("When: low median 10:11, signal median 10:37\n(signal never before 09:50; 8 days fire at 09:50 itself)", loc="left", color=INK)
a.legend(frameon=False, fontsize=8)

a = ax[1, 0]
c = C[(C.defn == "from_runhigh") & (C.sym == "SPY") & (C.split != "ALL")]
hs = ["30", "60", "90", "1555"]
for k, (sp, col) in enumerate([("TRAIN", B), ("VALID", O)]):
    y = c[c.split == sp].set_index("h").loc[hs]
    se = y.excess_bps / y.t
    a.errorbar(np.arange(4) + (k - 0.5) * 0.18, y.excess_bps, yerr=1.96 * se, fmt="o", ms=7, color=col, capsize=3,
               label=f"{sp} (n {int(y.n.iloc[0])})")
a.axhline(0, color=GR, lw=1); a.set_xticks(range(4), ["+30 min", "+60 min", "+90 min", "to 15:55"])
a.set_ylabel("SPY return after the signal minus\nsame minute on all days (bps, 95% CI)")
a.set_title("After the signal SPY drifts up a little, but no horizon\nis distinguishable from an ordinary day (all |t| < 1.5)", loc="left", color=INK)
a.legend(frameon=False, fontsize=8)

a = ax[1, 1]
rows = [(r.config, r.avgR_TRAIN, r.avgR_VALID, r.random_avgR_ALL) for r in G.itertuples()]
rows += [(r.config.replace("|stop=own low", ""), r.avgR_TRAIN, r.avgR_VALID, r.random_avgR_ALL) for r in GS.itertuples()]
y = np.arange(len(rows))[::-1]
a.scatter([r[1] for r in rows], y, color=B, s=30, label="TRAIN avg R", zorder=3)
a.scatter([r[2] for r in rows], y, color=O, s=30, label="VALID avg R", zorder=3)
a.scatter([r[3] for r in rows], y, marker="|", color=INK, s=120, label="random entry, same days (ALL)", zorder=3)
a.axvline(0, color=GR, lw=1); a.set_yticks(y, [r[0] for r in rows], fontsize=7)
a.set_xlabel("avg R per trade after costs")
a.set_title("20 trade configs: none clears the bar (2.68); most sit\non top of random entries on the same days", loc="left", color=INK)
a.legend(frameon=False, fontsize=7, loc="lower right")
fig.suptitle("SPY first-hour drop >= 0.65% then +0.5% rebound (Sep-2024..Nov-2026)  -  Educational only, not financial advice",
             x=0.01, ha="left", fontsize=10, color=INK)
fig.tight_layout()
fig.savefig(H / "drop_rebound.png", dpi=130, facecolor=fig.get_facecolor())
