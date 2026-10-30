"""Primary 2026-10-29 autopsy: per trade R after costs, latency, entry vs signal ref price, MFE/MAE on SIP 1-min bars,
time to MFE, what happened after the exit (did a stopped short later reach its target = 'stop was the problem'; did
a target winner keep going), the symbol's move from the open / from the day low at entry, and the 'cluster' each
trade belongs to (same symbol + side, any Primary setup, entries within 120 min).
Usage: python autopsy.py <scratch> [date]   Educational only - not financial advice."""
import sys, sqlite3, json
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); D = sys.argv[2] if len(sys.argv) > 2 else "2026-10-29"; TZ = "America/New_York"
OUT = Path(__file__).resolve().parent
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
c = sqlite3.connect(S / "p" / "journal.db")
t = pd.read_sql("select * from trades where date=? and run_id=1", c, params=(D,))
sg = pd.read_sql("select broker_order_id, ref_price, ts from signals where day=? and run_id=1 and status='submitted'", c, params=(D,))
t = t.merge(sg.drop_duplicates("broker_order_id"), on="broker_order_id", how="left")
for x, y in [("nt", "entry_time"), ("et", "exit_time"), ("st", "signal_time"), ("pt", "ts")]:
    t[x] = pd.to_datetime(t[y], utc=True, format="mixed").dt.tz_convert(TZ)
t = t.sort_values("nt").reset_index(drop=True)
t["Rps"] = (t.entry - t.stop).abs(); t["risk"] = t.Rps * t.shares
t["R"] = t.pnl_adj / t.risk
t["lat_s"] = (t.nt - t.pt).dt.total_seconds()
t["ref_slip_R"] = t.side * (t.ref_price - t.entry) / t.Rps        # >0 = filled better than the signal's reference
t["notional"] = t.entry * t.shares
t["spread_bps"] = t.meta.map(lambda m: json.JSONDecoder().raw_decode(m)[0].get("spread_bps") if isinstance(m, str) else np.nan)
t["spread_frac_stop"] = t.spread_bps / 1e4 * t.entry / t.Rps
t["stop_slip_R"] = np.where(t.exit_reason == "stop", t.side * (t.stop - t.exit) / t.Rps, np.nan)
t["cost_R"] = (t.pnl - t.pnl_adj) / t.risk
t["fam"] = np.where(t.strategy.str.match(r"^(RW3|RW5|MF4|MF2)"), "SHORTFAM", t.strategy.str.split("-").str[0])
bars = {}
def bar(s):
    if s not in bars:
        b = pd.read_parquet(S / "bars" / f"{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
        bars[s] = b.between_time("09:30", "15:59")
    return bars[s]
rows = []
for r in t.itertuples():
    b = bar(r.symbol); o = b.open.iloc[0]
    w = b[(b.index >= r.nt.floor("1min")) & (b.index <= (r.et.floor("1min") if pd.notna(r.et) else b.index[-1]))]
    s = r.side
    mfe = ((w.high.max() - r.entry) if s == 1 else (r.entry - w.low.min())) / r.Rps
    mae = ((r.entry - w.low.min()) if s == 1 else (w.high.max() - r.entry)) / r.Rps
    tmfe = ((w.high.idxmax() if s == 1 else w.low.idxmin()) - r.nt.floor("1min")).total_seconds() / 60
    pre = b[b.index < r.nt.floor("1min")]
    after = b[b.index > (r.et.floor("1min") if pd.notna(r.et) else b.index[-1])]
    after = after[after.index <= after.index[0].normalize() + pd.Timedelta(hours=15, minutes=55)] if len(after) else after
    tgt_after = bool(len(after) and ((after.low.min() <= r.target) if s == -1 else (after.high.max() >= r.target)))
    close_R = s * (b.close.iloc[-1] - r.entry) / r.Rps
    # p1_1029 backlog idea: stop x2.5 at the same $ risk (target price unchanged), 1-min walk from the entry minute to 15:55
    ww = b[(b.index >= r.nt.floor("1min")) & (b.index <= b.index[0].normalize() + pd.Timedelta(hours=15, minutes=55))]
    st2 = r.entry - s * 2.5 * r.Rps; px2 = ww.close.iloc[-1]
    for _, x in ww.iterrows():
        if (s == -1 and x.high >= st2) or (s == 1 and x.low <= st2):
            px2 = st2; break
        if (s == -1 and x.low <= r.target) or (s == 1 and x.high >= r.target):
            px2 = r.target; break
    wide_R = s * (px2 - r.entry) / (2.5 * r.Rps)
    rows.append(dict(id=r.id, mfe=round(mfe, 2), mae=round(mae, 2), t_mfe=tmfe,
                     from_open_pct=round((r.entry / o - 1) * 100, 2),
                     from_low_atr=round((r.entry - pre.low.min()) / (4 * r.Rps), 2) if len(pre) else np.nan,
                     from_high_atr=round((pre.high.max() - r.entry) / (4 * r.Rps), 2) if len(pre) else np.nan,
                     tgt_after_exit=tgt_after, wide25_R_gross=round(wide_R, 2), close_vs_entry_R=round(close_R, 2),
                     sym_close_from_open=round((b.close.iloc[-1] / o - 1) * 100, 2)))
t = t.merge(pd.DataFrame(rows), on="id")
# clusters: same symbol + side, chained entries
t["cluster"] = t.groupby(["symbol", "side"]).ngroup()
t["k_in_cluster"] = t.groupby("cluster").id.transform("size")
t["lot_seq"] = t.groupby("cluster").cumcount() + 1
cols = ["symbol", "strategy", "side", "nt", "et", "exit_reason", "R", "pnl_adj", "Rps", "shares", "notional", "lat_s", "ref_slip_R",
        "spread_bps", "spread_frac_stop", "stop_slip_R", "cost_R", "mfe", "mae", "t_mfe", "from_open_pct", "from_low_atr", "from_high_atr", "tgt_after_exit", "wide25_R_gross", "close_vs_entry_R",
        "sym_close_from_open", "k_in_cluster", "lot_seq"]
v = t[cols].copy(); v["nt"] = v.nt.dt.strftime("%H:%M"); v["et"] = v.et.dt.strftime("%H:%M"); v["strategy"] = v.strategy.str.slice(0, 14)
print(v.round(2).to_string())
t.drop(columns=["meta"], errors="ignore").to_csv(OUT / "trades_today.csv", index=False)
print("\nexecution: stop slippage beyond the stop", round(t.stop_slip_R.sum(), 2), "R; fill-realism cost", round(t.cost_R.sum(), 2),
      "R; entry vs signal ref", round(t.ref_slip_R.sum(), 2), "R (+ = better); median latency", t.lat_s.median(), "s; median spread", t.spread_bps.median(), "bps")
print("wide stop x2.5 (same $ risk), gross R sum", round(t.wide25_R_gross.sum(), 2), "vs actual gross R sum", round((t.R + t.cost_R).sum(), 2))
print("\nTOTAL n", len(t), "R", round(t.R.sum(), 2), "$adj", round(t.pnl_adj.sum(), 2), "$gross", round(t.pnl.sum(), 2),
      "avgR", round(t.R.mean(), 3), "risk$ mean", round(t.risk.mean(), 1))
g = t.groupby(["symbol", "side"]).agg(n=("id", "size"), R=("R", "sum"), usd=("pnl_adj", "sum"), setups=("strategy", lambda x: ",".join(s.split("-")[0] for s in x)))
print(g.sort_values("R").round(2).to_string())
print(t.groupby("strategy").agg(n=("id", "size"), R=("R", "sum"), usd=("pnl_adj", "sum")).round(2).to_string())
print(t.groupby("side").agg(n=("id", "size"), R=("R", "sum"), usd=("pnl_adj", "sum")).round(2).to_string())
