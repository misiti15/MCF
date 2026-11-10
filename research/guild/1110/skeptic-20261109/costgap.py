"""Skeptic: live paper costs vs the lab cost model on the SAME live trades (journals, run_id 1, 2026-10-06..11-06).
entry slip = side x (fill - signal ref_price) / ref  (ref = price at the signal; includes ~1 min delay + spread)
exit slip (stops only) = side x (stop - exit fill) / stop; adj = (pnl - pnl_adj) per share (journal fill-realism haircut)
lab model (mcf.research.gates): entry (1c + 1bp) x tod mult + 4.4bp x tod mult; exit 1c + 1bp; stops +2c.
All in R = per-share cost / |entry - stop|. Paper fills are optimistic, so live paper cost is a LOWER bound on real cost.
usage: python costgap.py <journal_dir>      Educational only - not financial advice."""
import sys, glob, os, json, sqlite3, numpy as np, pandas as pd
TOD = ((935, 3.8), (950, 2.1), (1030, 1.4))
def mult(t):
    for e, m in TOD:
        if t < e: return m
    return 1.0
R = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.db"))):
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("journal", "primary"); c = sqlite3.connect(f)
    t = pd.read_sql("select t.date,t.symbol,t.strategy,t.side,t.entry,t.stop,t.exit,t.exit_reason,t.shares,t.pnl,t.pnl_adj,t.slip_bps,"
                    "s.ref_price,s.info from trades t join signals s on s.broker_order_id=t.broker_order_id "
                    "where t.run_id=1 and s.run_id=1 and t.date between '2026-10-06' and '2026-11-06' and t.exit is not null", c)
    t["acct"] = a; R.append(t)
T = pd.concat(R, ignore_index=True)
info = T["info"].map(lambda s: json.loads(s) if s else {})
T["spread_bps"] = info.map(lambda d: d.get("spread_bps")); T["bar_time"] = info.map(lambda d: int(d.get("bar_time") or 0))
T["risk"] = (T.entry - T.stop).abs(); T = T[(T.risk > 0) & T.ref_price.notna()].copy()
T["stop_x"] = T.exit_reason.fillna("").str.contains("stop")
T["e_slip"] = T.side * (T.entry - T.ref_price)                                   # $/share, + = cost
T["x_slip"] = np.where(T.stop_x, T.side * (T.stop - T.exit), 0.0)
T["adj"] = (T.pnl - T.pnl_adj) / T.shares
T["m"] = T.bar_time.map(mult)
T["lab"] = (0.01 + T.entry * 1e-4) * T.m + 4.4e-4 * T.entry * T.m + 0.01 + T.entry * 1e-4 + np.where(T.stop_x, 0.02, 0)
for k in ("e_slip", "x_slip", "adj", "lab"): T[k + "_R"] = T[k] / T.risk
T["live_R"] = T.e_slip_R + T.x_slip_R + T.adj_R
T["gap_R"] = T.live_R - T.lab_R
T["e_bps"] = T.e_slip / T.ref_price * 1e4
def s(g): return pd.Series(dict(n=len(g), entry_bps_med=g.e_bps.median(), entry_bps_mean=g.e_bps.mean(), spread_bps_med=g.spread_bps.median(),
                                entry_R=g.e_slip_R.mean(), stopx_R=g.x_slip_R.mean(), adj_R=g.adj_R.mean(), live_R=g.live_R.mean(),
                                lab_R=g.lab_R.mean(), gap_R=g.gap_R.mean(), gap_R_med=g.gap_R.median(), risk_bps_med=(g.risk / g.entry * 1e4).median()))
pd.set_option("display.width", 250)
print(f"trades {len(T)} (joined to their signal), {T.date.min()}..{T.date.max()}")
print("\nALL:\n", s(T).round(3).to_string())
print("\nby account:\n", T.groupby("acct").apply(s).round(3).to_string())
T["tod_b"] = pd.cut(T.bar_time, [0, 1000, 1030, 1200, 1400, 1600], labels=["<10:00", "10:00-10:30", "10:30-12", "12-14", "14-16"])
print("\nby signal time:\n", T.groupby("tod_b").apply(s).round(3).to_string())
T["risk_b"] = pd.qcut(T.risk / T.entry * 1e4, 4, labels=["risk Q1 (tight)", "Q2", "Q3", "Q4 (wide)"])
print("\nby stop width (risk bps quartile):\n", T.groupby("risk_b").apply(s).round(3).to_string())
print("\nby side:\n", T.groupby("side").apply(s).round(3).to_string())
d = T.groupby("date").gap_R.mean(); print(f"\ndays {len(d)}; days with gap_R > 0: {int((d > 0).sum())}; daily gap mean {d.mean():.3f}, sd {d.std():.3f}, t {d.mean() / (d.std() / np.sqrt(len(d))):.2f}")
print("Educational only - not financial advice.")
