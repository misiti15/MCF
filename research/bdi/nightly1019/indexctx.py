"""Index context at entry for 2026-10-19 trades (trades.csv + t1_missing.csv estimate): QQQ % from the open, % below its
session high so far, and the QQQ move over the previous 60 min, at the signal minute. Descriptive split only
(one session, in-sample; about 12 cells looked at). Writes indexctx_out.txt. Usage: python indexctx.py <scratch>
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-10-19"; TZ = "America/New_York"
q = pd.read_parquet(S / "bars" / "QQQ.parquet"); q.index = pd.to_datetime(q.index, utc=True).tz_convert(TZ); q = q.between_time("09:30", "15:59")
o = q.open.iloc[0]; hod = q.high.cummax(); lod = q.low.cummin()
T = pd.read_csv(OUT / "trades.csv"); T["st"] = pd.to_datetime(T.st, utc=True).dt.tz_convert(TZ); T["est"] = False
X = pd.read_csv(OUT / "t1_missing.csv"); X["st"] = pd.to_datetime(D + " " + X.signal).dt.tz_localize(TZ); X["acct"] = "t1"; X["est"] = True
A = pd.concat([T[["acct", "strategy", "side", "st", "pnl_adj", "radj", "est"]], X[["acct", "strategy", "side", "st", "pnl_adj", "radj", "est"]]], ignore_index=True)
m = A.st.dt.floor("1min") - pd.Timedelta(minutes=1)
A["q_open"] = ((q.close.reindex(m).values / o) - 1) * 100
A["q_off_hod"] = ((q.close.reindex(m).values / hod.reindex(m).values) - 1) * 100
A["q_off_lod"] = ((q.close.reindex(m).values / lod.reindex(m).values) - 1) * 100
A["q_60"] = ((q.close.reindex(m).values / q.close.reindex(m - pd.Timedelta(minutes=60)).values) - 1) * 100
# "with the last hour": trade side agrees with QQQ's 60-min move
A["chase"] = np.sign(A.side) == np.sign(A.q_60)
A["near_extreme"] = np.where(A.side == 1, A.q_off_hod > -0.15, A.q_off_lod < 0.15)   # long within 0.15% of QQQ HOD / short within 0.15% of LOD
out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
f = lambda d: pd.Series(dict(n=len(d), win=round((d.pnl_adj > 0).mean() * 100), avgR=round(d.radj.mean(), 3), adj=round(d.pnl_adj.sum(), 2), est=int(d.est.sum())))
for acc in (["p"], ["t1"], ["t2"], ["p", "t1", "t2"]):
    d = A[A.acct.isin(acc)]
    P(f"===== {'+'.join(acc)}")
    P("side x near QQQ extreme in the trade's direction (long within 0.15% of HOD / short within 0.15% of LOD):")
    P(d.groupby(["side", "near_extreme"]).apply(f, include_groups=False).to_string())
    P("side x with QQQ's last-60-min move (chase):")
    P(d.groupby(["side", "chase"]).apply(f, include_groups=False).to_string())
open(OUT / "indexctx_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
