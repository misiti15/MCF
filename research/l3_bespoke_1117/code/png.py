import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
a = pd.read_csv("A_engine.csv", dtype={"level": str}); l = pd.read_csv("A_live.csv", dtype={"level": str})
lv = ['-1.00','-1.25','-1.50','-1.75','-2.00','-2.25','-2.50','-2.75','-3.00','-3.25','-3.50','-3.75','-4.00','none']
x = np.arange(len(lv)); C = ["#2a78d6", "#eb6834", "#1baf7a"]
def d(df, col="total_wo_best"):
    s = df.set_index("level")[col].reindex(lv); return s - s["-2.00"]
rows = []
fig, ax = plt.subplots(2, 1, figsize=(11, 8), sharex=True, facecolor="#fcfcfb")
for i, seg in enumerate(["TRAIN", "VALID"]):
    s = d(a[(a.test == "2y") & (a.seg == seg)]); ax[0].plot(x, s, marker="o", ms=6, lw=2, color=C[i], label=f"2-year {seg}")
    rows.append(s.rename(f"2y_{seg}"))
for i, (lab, df) in enumerate([("Live Primary", l[l["sample"] == "Primary"]), ("Live Primary + On Deck", l[l["sample"] == "Primary+On Deck"]), ("Session replay 10-12..11-17", a[a.test == "replay"])]):
    s = d(df); ax[1].plot(x, s, marker="o", ms=6, lw=2, color=C[i], label=lab); rows.append(s.rename(lab))
bands = [(0, 0, "after 1st stop"), (1, 4, "after 2nd stop (−2 today)"), (5, 8, "after 3rd stop"), (9, 12, "after 4th stop"), (13, 13, "no latch")]
for a_ in ax:
    a_.set_facecolor("#fcfcfb"); a_.axhline(0, color="#52514e", lw=1)
    for k, (s0, s1, t) in enumerate(bands):
        if k % 2 == 0: a_.axvspan(s0 - .5, s1 + .5, color="#e9e8e4", zorder=0)
    a_.grid(axis="y", color="#e2e1dd", lw=.6); a_.spines[["top", "right"]].set_visible(False)
    a_.legend(frameon=False, loc="lower left", fontsize=9); a_.set_ylabel("R w/o best day, minus −2R latch")
for s0, s1, t in bands:
    ax[0].text((s0 + s1) / 2, ax[0].get_ylim()[1], t, ha="center", va="bottom", fontsize=8, color="#52514e")
ax[1].set_xticks(x, lv); ax[1].set_xlabel("per-setup daily latch level (R after costs)")
ax[0].set_title("L3-gap-slope-fromopen-FD: total R without the best day at each latch level, relative to −2R\n(above 0 = better than today's −2R; shaded bands = same number of full stops before the latch)", fontsize=11, loc="left", pad=22)
fig.text(0.01, 0.005, "Educational only — not financial advice. Costs in (LR8). Locked block 2024-11-01..2025-02-28 not read. research/l3_bespoke_1117", fontsize=8, color="#52514e")
plt.tight_layout(rect=(0, .02, 1, 1)); plt.savefig("latch_curve.png", dpi=130)
pd.concat(rows, axis=1).to_csv("A_plateau_vs_m2.csv", float_format="%.3f")
