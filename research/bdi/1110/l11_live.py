"""swing1109-L11 (ECG1 early compass gate) forward day 1 on 2026-11-10: block new momentum shorts (^(NM-)?MF\\d | flowsell |
^L3-) entered at/after 10:00 while the live W60 compass at the latest 15-min mark reads UP-confirmed. 7 journals, run 1,
R = pnl_adj / $ risk. Usage: python l11_live.py <scratch with <acct>/journal.db>. Educational only - not financial advice."""
import io, sqlite3, subprocess, sys
from pathlib import Path
import pandas as pd
J = Path(sys.argv[1]); D = "2026-11-10"; FAM = r"^(?:NM-)?MF\d|flowsell|^L3-"
cp = pd.read_csv(io.StringIO(subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/mcf-data-compass:compass/{D}.csv"], capture_output=True, text=True).stdout))
cp["m"] = cp["T"].str[:2].astype(int) * 60 + cp["T"].str[3:].astype(int)
print("W60 by mark:", "; ".join(f"{r.T} {r.w60}" for r in cp.itertuples()))
L = []
for a in ("p", "t1", "t2", "gy", "gen", "ex1", "ll"):
    t = pd.read_sql("select symbol, strategy, side, entry_time, entry, stop, shares, pnl_adj from trades where date=? and run_id=1", sqlite3.connect(J / a / "journal.db"), params=(D,))
    t["acct"] = a; L.append(t)
L = pd.concat(L); L = L[(L.side == -1) & L.strategy.str.contains(FAM, regex=True)].copy()
L["R"] = L.pnl_adj / ((L.entry - L.stop).abs() * L.shares)
et = pd.to_datetime(L.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York"); L["m"] = et.dt.hour * 60 + et.dt.minute
def lg(m):
    x = cp[(cp.m <= m) & (cp.m >= 600)]
    return bool(len(x) and x.w60.iloc[-1] == "UP-confirmed")
L["blk"] = L.m.map(lg)
print(f"LIVE {D}: family shorts {len(L)}, shadow-blocked {int(L.blk.sum())} live {L[L.blk].R.sum():+.2f}R -> gate gain {-L[L.blk].R.sum():+.2f}R; kept {int((~L.blk).sum())} {L[~L.blk].R.sum():+.2f}R")
print("   by account: " + "; ".join(f"{a} {len(x)} {-x.R.sum():+.2f}R" for a, x in L[L.blk].groupby("acct")))
print("   by setup: " + "; ".join(f"{s} {len(x)} {-x.R.sum():+.2f}R" for s, x in L[L.blk].groupby("strategy")))
print("Educational only - not financial advice.")
