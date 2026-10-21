"""Build trades.csv for 2026-10-21 (Primary p, Testing 1 t1, Testing 2 t2, Setup Generator gen; real trades, run 1).
Per trade: MFE/MAE on SIP 1-min bars (journal mfe_r/mae_r kept as a fallback), time to MFE, latency (signal -> fill),
same-setup cluster size per 5-min poll, lot number, twin entries (same symbol + side already entered by another setup
within 3 min), refire/retry flags, realized R after costs (pnl_adj / $ risk).
All four journals are complete on 2026-10-21 (submitted signals = trade rows).
Usage: python build.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-10-21"; TZ = "America/New_York"
bars = {}
def bar(s):
    if s not in bars:
        f = S / "bars" / f"{s}.parquet"
        b = pd.read_parquet(f) if f.exists() else None
        if b is not None:
            b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
        bars[s] = b
    return bars[s]
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select * from trades where date=? and run_id=1", c, params=(D,))
    sg = pd.read_sql("select broker_order_id, info from signals where day=? and run_id=1 and status='submitted'", c, params=(D,))
    t = t.merge(sg.drop_duplicates("broker_order_id"), on="broker_order_id", how="left")
    t["retry"] = t["info"].fillna("").str.contains('"retry_after_release": true')
    t["refire"] = t["info"].fillna("").str.contains('"refire": true')
    for x, y in [("nt", "entry_time"), ("et", "exit_time"), ("st", "signal_time")]:
        t[x] = pd.to_datetime(t[y], utc=True, format="mixed").dt.tz_convert(TZ)
    t = t.sort_values("nt").reset_index(drop=True)
    t["acct"] = a
    t["setup_seq"] = t.groupby(["symbol", "strategy"]).cumcount() + 1
    t["lot_no"] = [1 + int(((t.symbol == r.symbol) & (t.side == r.side) & (t.id != r.id) & (t.nt < r.nt) & (t.et > r.nt)).sum())
                   for r in t.itertuples()]
    # twin: another setup already entered the same symbol + side within the previous 3 minutes
    t["twin"] = [bool(((t.symbol == r.symbol) & (t.side == r.side) & (t.strategy != r.strategy) & (t.nt <= r.nt) & (t.id != r.id)
                       & (t.nt > r.nt - pd.Timedelta(minutes=3))).any()) for r in t.itertuples()]
    t["twin_group"] = t.groupby(["symbol", "side", t.nt.dt.floor("5min")]).strategy.transform("nunique")
    rows.append(t.drop(columns=["info"]))
T = pd.concat(rows, ignore_index=True)
T["R"] = (T.entry - T.stop).abs(); T["risk"] = T.R * T.shares
T["radj"] = np.where(T.risk > 0, T.pnl_adj / T.risk, np.nan)
T["lat"] = (T.nt - T.st).dt.total_seconds()
T["hold"] = (T.et - T.nt).dt.total_seconds() / 60
T["hour"] = T.nt.dt.hour
T["poll"] = T.st.dt.floor("5min").dt.strftime("%H:%M")
T["cluster"] = T.groupby(["acct", "strategy", "poll"]).id.transform("size")
mfe, mae, tm, src = [], [], [], []
for r in T.itertuples():
    b = bar(r.symbol)
    w = None if b is None else b[(b.index >= r.nt.floor("1min")) & (b.index <= r.et.floor("1min"))]
    if w is None or w.empty or r.R <= 0:
        mfe.append(r.mfe_r); mae.append(-abs(r.mae_r) if pd.notna(r.mae_r) else np.nan); tm.append(np.nan); src.append("journal"); continue
    hi, lo = w.high.max(), w.low.min()
    mfe.append((hi - r.entry) / r.R if r.side == 1 else (r.entry - lo) / r.R)
    mae.append((r.entry - lo) / r.R if r.side == 1 else (hi - r.entry) / r.R)
    i = w.high.idxmax() if r.side == 1 else w.low.idxmin()
    tm.append((i - r.nt.floor("1min")).total_seconds() / 60); src.append("sip")
T["mfe"], T["mae"], T["t_mfe"], T["mfe_src"] = mfe, mae, tm, src
T["never"] = (T.pnl_adj <= 0) & (T.mfe < 0.2)
T["lost_after_half"] = (T.pnl_adj <= 0) & (T.mfe >= 0.5)
T.to_csv(OUT / "trades.csv", index=False)
print(T.groupby("acct").agg(n=("id", "size"), pnl=("pnl", "sum"), adj=("pnl_adj", "sum"), sip=("mfe_src", lambda x: (x == "sip").sum()),
                            twin=("twin", "sum"), stacked=("lot_no", lambda x: (x > 1).sum()), refire=("refire", "sum")).round(2))
