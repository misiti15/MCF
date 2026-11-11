"""ROT-A layout check: proposed homes after the migration (on top of the TEAM-6 switch), per-account counts, live
entries/session (cumulative playing time), long/short mix, low-rep counts. Writes layout.csv.
Educational only - not financial advice."""
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
I = pd.read_csv(HERE / "inventory.csv").set_index("setup")
MOVE = {"CWT13-vwapstretch-z075-long": "T1", "ST8-volspikedn-long-pm-t1s1-FD": "T1", "CWT12-flag-s1-long": "T1",
        "CWT05-flush-m075-v3-long": "T2", "MF5-flowsell-vwapup-rsi5hi": "T2", "exhaustion_short-FD": "T2"}
GYP = ["RW3S-gapdn-flowsell-short-FD", "CWT13-vwapstretch-z05-long", "NM-AR-AM-gapdown-capitulation-long",
       "NS3-failed-vwap-reclaim-short", "intraday_momentum"]
I["now"] = I.home
I["rot_a"] = [MOVE.get(s, h) for s, h in I.home.items()]
I["rot_a_gy"] = [("GY" if s in GYP else h) for s, h in I.rot_a.items()]
I[["name", "now", "rot_a", "rot_a_gy", "trades", "sessions", "side", "pt_entries_per_session"]].to_csv(HERE / "layout.csv")
for col in ("now", "rot_a", "rot_a_gy"):
    print(col)
    for h, x in I.groupby(col):
        print(f"  {h:6s} setups {len(x):2d}  entries/session {x.pt_entries_per_session.sum():6.1f}  "
              f"long/short/both {sum(x.side=='long')}/{sum(x.side=='short')}/{sum(x.side=='both')}  <20 trades {sum(x.trades<20)}  0 trades {sum(x.trades==0)}")
