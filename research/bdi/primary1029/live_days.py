"""Primary live paper record per session (run 1, after costs): all setups and the current 8 only. R = pnl_adj / $ risk.
Also: same-symbol same-side multi-setup clusters per day (k setups on one symbol within 120 min) and what they did.
Usage: python live_days.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3, json
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
CUR = json.loads(Path("/home/user/MCF/docs/live/assignments.json").read_text())["accounts"]["primary"]
c = sqlite3.connect(S / "p" / "journal.db")
t = pd.read_sql("select id,date,symbol,strategy,side,entry_time,exit_time,entry,stop,shares,pnl,pnl_adj,exit_reason from trades where run_id=1", c)
t["nt"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
t["risk"] = (t.entry - t.stop).abs() * t.shares; t = t[t.risk > 0]
t["R"] = t.pnl_adj / t.risk
t["cur"] = t.strategy.isin(CUR)
t = t.sort_values("nt")
d = t.groupby("date").agg(n=("id", "size"), R=("R", "sum"), usd=("pnl_adj", "sum"))
dc = t[t.cur].groupby("date").agg(n8=("id", "size"), R8=("R", "sum"), usd8=("pnl_adj", "sum"), avgR8=("R", "mean"))
x = d.join(dc)
pd.set_option("display.width", 200)
print(x.round(2).to_string())
y = x[x.index >= "2026-10-15"]
print("\nsince 10-15 current-8: days", len(y), "R", round(y.R8.sum(), 1), "usd", round(y.usd8.sum(), 0), "worst", round(y.R8.min(), 2), "red", int((y.R8 < 0).sum()))
# clusters: current 8, same date/symbol/side, multiple setups
cu = t[t.cur].copy()
cu["k"] = cu.groupby(["date", "symbol", "side"]).id.transform("size")
cu["nset"] = cu.groupby(["date", "symbol", "side"]).strategy.transform("nunique")
cl = cu[cu.k > 1].groupby(["date", "symbol", "side"]).agg(k=("id", "size"), R=("R", "sum"), usd=("pnl_adj", "sum"),
     wins=("R", lambda r: int((r > 0).sum())), first=("nt", lambda s: s.min().strftime("%H:%M")), last=("nt", lambda s: s.max().strftime("%H:%M")))
print("\nmulti-lot clusters (current 8):"); print(cl.round(2).to_string())
print("cluster R total", round(cl.R.sum(), 2), "n", int(cl.k.sum()), "single-lot R", round(cu[cu.k == 1].R.sum(), 2), "n", int((cu.k == 1).sum()))
t.to_csv(S / "live_all.csv", index=False)
