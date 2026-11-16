"""Mechanic orb20_a: live-trade teardown charts (5 worst + 5 best). Bars from data/cache_hist, data/team or the read-only
SIP GET (mcf.report.engine.fetch_bars). Every price and time printed; lettered callouts name the part (P-numbers as
DIAGNOSIS.md). Educational only - not financial advice."""
import sys, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-orb20a")
from mcf.report import engine as E
from mcf import features as F
W = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-orb20/"
OUTD = sys.argv[1]
TZ = "America/New_York"


def bars(sym, day):
    p = f"/home/user/MCF/data/team/1Min/{day}.parquet"
    if os.path.exists(p):
        t = pd.read_parquet(p, filters=[("symbol", "==", sym)])
        if len(t):
            t = t.set_index(pd.DatetimeIndex(pd.to_datetime(t.ts, utc=True)).tz_convert(TZ))[["open", "high", "low", "close", "volume"]]
            return t.sort_index()
    p = f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet"
    if os.path.exists(p) and day <= "2026-11-04":
        t = pd.read_parquet(p)
        t = t[t.index.strftime("%Y-%m-%d") == day]
        if len(t):
            return t
    m = E.fetch_bars(sym, day, lookback_days=1)
    return m[m.index.strftime("%Y-%m-%d") == day]


def chart(tr, tag, atr):
    day = tr["date"]; s = int(tr["side"])
    b = bars(tr["symbol"], day)
    b = b[(b.index.strftime("%H%M") >= "0930") & (b.index.strftime("%H%M") < "1600")]
    et = pd.Timestamp(tr["entry_time"]).tz_convert(TZ); xt = pd.Timestamp(tr["exit_time"]).tz_convert(TZ)
    rng = b[b.index.strftime("%H%M") <= "0949"]
    hi, lo, op, c49 = rng.high.max(), rng.low.min(), rng.open.iloc[0], rng.close.iloc[-1]
    vw = F.vwap(b)
    end = min(b.index[-1], max(xt + pd.Timedelta(minutes=40), pd.Timestamp(f"{day} 11:45", tz=TZ)))
    v = b[b.index <= end]
    x = np.arange(len(v)); ix = {ts: i for i, ts in enumerate(v.index)}
    fig, ax = plt.subplots(figsize=(13, 6.8), dpi=110)
    up = v.close >= v.open
    ax.vlines(x, v.low, v.high, color=np.where(up, "#16a34a", "#dc2626"), lw=0.8)
    ax.bar(x, (v.close - v.open).abs().clip(lower=1e-4), bottom=np.minimum(v.open, v.close), color=np.where(up, "#16a34a", "#dc2626"), width=0.7)
    ax.plot(x, vw.reindex(v.index).values, color="#7c3aed", lw=1.2, label="VWAP")
    n49 = len(rng)
    ax.axvspan(-0.5, n49 - 0.5, color="#0891b2", alpha=0.08)
    ax.hlines([hi, lo], -0.5, len(v), colors="#0891b2", linestyles=":", lw=1)
    ax.hlines(tr["stop"], 0, len(v), colors="#dc2626", linestyles="--", lw=1.2, label=f"stop {tr['stop']:.2f}")
    if tr["target"] == tr["target"] and tr["target"]:
        ax.hlines(tr["target"], 0, len(v), colors="#16a34a", linestyles="--", lw=1.2, label=f"target {tr['target']:.2f}")
    ei = ix.get(et.floor("min"), np.searchsorted(v.index, et.floor("min")))
    xi = ix.get(xt.floor("min"), min(len(v) - 1, np.searchsorted(v.index, xt.floor("min"))))
    ax.scatter([ei], [tr["entry"]], marker="^" if s == 1 else "v", s=140, color="#0d9488", zorder=5)
    ax.scatter([xi], [tr["exit"]], marker="X", s=140, color="black", zorder=5)
    width = hi - lo
    rpct = abs(tr["entry"] - tr["stop"]) / tr["entry"] * 100
    cost_r = (2 * (0.01 + tr["entry"] * 1e-4) + max(0.02, 4e-4 * tr["entry"])) / abs(tr["entry"] - tr["stop"])
    notes = [
        f"A  P6 opening range 09:30-09:49: high {hi:.2f} / low {lo:.2f} (width {width:.2f} = {width / atr:.2f} x ATR {atr:.2f}); open {op:.2f} -> 09:49 close {c49:.2f} = {'LONG' if s == 1 else 'SHORT'} side (P9; P10 VWAP agrees)",
        f"B  P15 entry: stop order at the {'high +1c' if s == 1 else 'low -1c'} {hi + 0.01 if s == 1 else lo - 0.01:.2f}; live fill {tr['entry']:.2f} at {et:%H:%M:%S} (slip {tr['slip_bps']:.0f} bps)",
        f"C  P17 stop = level -/+ 0.5 x range = {tr['stop']:.2f} (1R = {abs(tr['entry'] - tr['stop']):.3f} = {rpct:.2f}% of price; round-trip+stop cost ~ {cost_r:.2f}R) ; P18 target 0.75 x range = {tr['target']:.2f}",
        f"D  exit {tr['exit']:.2f} at {xt:%H:%M:%S} by {tr['exit_reason']} ({'P17 stop' if tr['exit_reason'] == 'stop' else 'P18 target' if tr['exit_reason'] == 'target' else 'P19 time exit'}) -> {tr['r']:+.2f}R ; MFE {tr['mfe_r'] if tr['mfe_r'] == tr['mfe_r'] else float('nan'):+.2f}R / MAE {tr['mae_r'] if tr['mae_r'] == tr['mae_r'] else float('nan'):+.2f}R",
    ]
    for k, (xx, yy, l) in enumerate([(n49 / 2, hi, "A"), (ei, tr["entry"], "B"), (ei + 3, tr["stop"], "C"), (xi, tr["exit"], "D")]):
        ax.annotate(l, (xx, yy), xytext=(8, 12 if k % 2 == 0 else -18), textcoords="offset points", fontsize=12, fontweight="bold",
                    color="#111", bbox=dict(boxstyle="circle,pad=0.2", fc="#fde68a", ec="#92400e"))
    step = max(1, len(v) // 14)
    ax.set_xticks(x[::step]); ax.set_xticklabels([ts.strftime("%H:%M") for ts in v.index[::step]], fontsize=8)
    ax.set_title(f"orb20_a {tag}: {tr['symbol']} {day} ({tr['acct']} #{tr['id']}) {'long' if s == 1 else 'short'} {tr['r']:+.2f}R", fontsize=12)
    ax.legend(loc="upper left", fontsize=8)
    fig.text(0.01, 0.01, "\n".join(notes) + "\nEducational only - not financial advice.", fontsize=8, family="monospace", va="bottom")
    fig.subplots_adjust(bottom=0.27, left=0.05, right=0.99, top=0.94)
    name = f"orb20_a_{tag}_{tr['symbol']}_{day}.png"
    fig.savefig(OUTD + "/" + name); plt.close(fig)
    return name, dict(hi=hi, lo=lo, width_atr=width / atr, risk_pct=rpct, cost_r=cost_r)


if __name__ == "__main__":
    L = pd.read_csv(W + "live.csv").sort_values("r")
    picks = [(f"worst{k + 1}", r) for k, (_, r) in enumerate(L.head(5).iterrows())] + \
            [(f"best{k + 1}", r) for k, (_, r) in enumerate(L.sort_values("r", ascending=False).head(5).iterrows())]
    for tag, r in picks:
        dl = E.fetch_daily(r.symbol, r.date)
        atr = float(F.atr(dl).iloc[-1])
        name, info = chart(r, tag, atr)
        print(tag, name, {k: round(v, 3) for k, v in info.items()})
