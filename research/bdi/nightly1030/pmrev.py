"""Descriptive look (1 config) for backlog nightly-1030-afternoon-index-reversal-long: on sessions where SPY is <= -1.0%
from the open at 14:30 (history2y context, 2-year open history, locked block not in the file), SPY's move from the
14:30 bar to the close (daily close, 16:00) and from its 14:00-15:00 low to the close (in % of the open), vs all other sessions.
Usage: python pmrev.py   Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd
C = pd.read_parquet("/home/user/MCF/research/history2y/data/context"); C["date"] = C.date.astype(str)
assert not C.date.between("2024-11-01", "2025-02-28").any()
p = C.pivot_table(index="date", columns="tod", values="spy_fo")
D = pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet"); D = D[D.symbol == "SPY"].copy(); D["date"] = D.date.astype(str)
D = D[~D.date.between("2024-11-01", "2025-02-28")].set_index("date")
close_fo = (D.close / D.open - 1) * 100   # daily close (16:00) stands in for 15:55; context bars end at 15:00
d = pd.DataFrame({"fo1430": p[1430], "fo1555": close_fo, "low_pm": p.loc[:, 1400:1500].min(axis=1)}).dropna()
d["m1430_close"] = d.fo1555 - d.fo1430; d["m_low_close"] = d.fo1555 - d.low_pm
d["grp"] = np.where(d.fo1430 <= -1.0, "SPY<=-1% at 14:30", np.where(d.fo1430 >= 1.0, "SPY>=+1% at 14:30", "other"))
g = d.groupby("grp").agg(n=("fo1430", "size"), m1430_close=("m1430_close", "mean"), up_share=("m1430_close", lambda x: (x > 0).mean()),
                         low_to_close=("m_low_close", "mean"), med=("m1430_close", "median"))
txt = g.round(3).to_string() + "\n\n" + d[d.grp.str.startswith("SPY<=")].round(2).to_string() + "\n\nEducational only - not financial advice.\n"
open(Path(__file__).resolve().parent / "pmrev_out.txt", "w").write(txt); print(txt[:1800])
