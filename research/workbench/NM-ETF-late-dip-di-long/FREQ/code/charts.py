"""FREQ charts: (1) cumulative R, parent vs WB4 (2-year + replay); (2) every config: trades/session vs avg R (2-year).
Educational only - not financial advice."""
import glob, pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
SC = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/etffreq/"
OUTD = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-etffreq/research/workbench/NM-ETF-late-dip-di-long/FREQ/"
B, O, INK, MUT = "#2a78d6", "#eb6834", "#222222", "#8a8a85"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUT,
                     "axes.labelcolor": INK, "xtick.color": MUT, "ytick.color": MUT, "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6})
T = pd.read_pickle(SC + "out/final_trades.pkl")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw=dict(width_ratios=[2.2, 1]))
for i, k in enumerate(("y2", "rep")):
    for n, c in (("parent", B), ("WB4", O)):
        t = T[(n, k)].sort_values(["date", "ent"]); d = t.groupby("date").r.sum().cumsum()
        x = pd.to_datetime(d.index)
        ax[i].plot(x, d.values, color=c, lw=2, label=f"{n}: {len(t)} trades, {t.r.sum():+.1f}R")
        ax[i].annotate(f"{d.values[-1]:+.1f}R", (x[-1], d.values[-1]), xytext=(4, 0), textcoords="offset points", color=INK, fontsize=9, va="center")
    ax[i].set_title(("2-year backtest 2024-10..2026-10-16 (locked block excluded)" if k == "y2" else "Replay of live sessions 10-19..11-16"), color=INK, fontsize=10, loc="left")
    ax[i].set_ylabel("cumulative R after costs (LR8)"); ax[i].legend(frameon=False, fontsize=9, loc="upper left")
    ax[i].tick_params(axis="x", rotation=30)
fig.suptitle("Late-Day ETF Dip Buy: parent vs WB4 (more dips) - Educational only, not financial advice", color=INK, fontsize=11, x=0.01, ha="left")
fig.tight_layout(); fig.savefig(OUTD + "NM-ETF-late-dip-di-long_freq_wb4_curve.png", dpi=130)
R = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(SC + "out/f*.csv"))])
R = R.drop_duplicates("cfg")
fig, ax = plt.subplots(figsize=(8.5, 5.2))
par = R[R.cfg == "parent"].iloc[0]
ax.axvline(par.y2_tps * 1.25, color=MUT, lw=1, ls="--"); ax.axhline(par.y2_avg - 0.03, color=MUT, lw=1, ls="--")
ok = R.freq_pass == True
ax.scatter(R[~ok].y2_tps, R[~ok].y2_avg, s=28, color="#c3c2b7", edgecolor="white", lw=1, label=f"fails the frequency rule ({(~ok).sum() - 1})", zorder=2)
ax.scatter(R[ok].y2_tps, R[ok].y2_avg, s=40, color=B, edgecolor="white", lw=1, label=f"passes on both tests ({ok.sum()})", zorder=3)
ax.scatter([par.y2_tps], [par.y2_avg], s=80, color=INK, marker="D", zorder=4, label="parent")
w = R[R.cfg.str.startswith("N1 ")].iloc[0]
ax.scatter([w.y2_tps], [w.y2_avg], s=110, color=O, edgecolor="white", lw=1.5, zorder=5, label="WB4 (recommended)")
ax.annotate("WB4", (w.y2_tps, w.y2_avg), xytext=(6, 4), textcoords="offset points", color=INK)
ax.annotate("parent", (par.y2_tps, par.y2_avg), xytext=(6, -12), textcoords="offset points", color=INK)
ax.text(par.y2_tps * 1.25 + 0.03, ax.get_ylim()[0] + 0.005, "+25% trades/session", color=MUT, fontsize=8)
ax.set_xlabel("trades per session (2-year)"); ax.set_ylabel("avg R per trade after costs (2-year)")
ax.set_title(f"All {len(R)} configurations (incl. parent): frequency vs quality - Educational only", color=INK, fontsize=10, loc="left")
ax.legend(frameon=False, fontsize=8, loc="upper right"); fig.tight_layout(); fig.savefig(OUTD + "NM-ETF-late-dip-di-long_freq_configs.png", dpi=130)
print(len(R), ok.sum())
