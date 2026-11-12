"""Nightly 2026-11-12 Primary (TEAM-6 day 1) autopsy: winners vs losers per setup (MFE/MAE from SIP 1-min, time to MFE,
give-back, entry hour, cluster, exit reason), intraday R path (realized + open marks every 15 min) vs SPY from its open.
Usage: python pautopsy.py <scratch>   Costs in (radj = pnl_adj / $ risk). Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
T = pd.read_csv(OUT / "trades.csv"); T["nt"] = pd.to_datetime(T.nt, utc=True).dt.tz_convert(TZ); T["et"] = pd.to_datetime(T.et, utc=True).dt.tz_convert(TZ)
P = T[T.acct == "p"].copy(); P["win"] = P.radj > 0; P["giveback"] = P.mfe - P.radj
out = []; W = out.append
W(f"Primary {len(P)} trades, {P.radj.sum():+.2f}R after costs (gross {P.r_multiple.sum():+.2f}), win {P.win.mean():.0%}, ${P.pnl_adj.sum():+.2f}")
W("-- per setup x win/lose: n, avg R, avg MFE, avg MAE, avg t_mfe (min), avg give-back, avg entry hour, avg cluster")
g = P.groupby(["strategy", "win"]).agg(n=("radj", "size"), R=("radj", "mean"), mfe=("mfe", "mean"), mae=("mae", "mean"), tmfe=("t_mfe", "mean"),
    gb=("giveback", "mean"), hour=("hour", "mean"), clus=("cluster", "mean"))
W(g.round(2).to_string())
W("-- exit reasons: " + str(P.groupby("exit_reason").radj.agg(["size", "sum"]).round(2).to_dict("index")))
W("-- entries by hour: " + str(P.groupby("hour").radj.agg(["size", "sum"]).round(2).to_dict("index")))
W(f"-- never positive (MFE < 0.1R): {(P.mfe < 0.1).sum()} trades, {P[P.mfe < 0.1].radj.sum():+.2f}R; reached +0.5R then lost: {((P.mfe >= 0.5) & ~P.win).sum()}")
bars = {}
def b(s):
    if s not in bars:
        x = pd.read_parquet(S / "bars" / f"{s}.parquet"); x.index = pd.to_datetime(x.index, utc=True).tz_convert(TZ); bars[s] = x.close
    return bars[s]
spy = b("SPY"); o = float(pd.read_parquet(S / "bars" / "SPY.parquet").open.iloc[0])
path = []
for t in pd.date_range("2026-11-12 09:45", "2026-11-12 15:55", freq="15min", tz=TZ):
    real = P[P.et <= t].radj.sum(); op = P[(P.nt <= t) & (P.et > t)]
    m = sum(r.side * (b(r.symbol)[:t].iloc[-1] - r.entry) / abs(r.entry - r.stop) for _, r in op.iterrows() if len(b(r.symbol)[:t]))
    path.append(dict(t=t.strftime("%H:%M"), realized=round(real, 2), open_marks=round(m, 2), total=round(real + m, 2), n_open=len(op),
                     shorts_open=int((op.side < 0).sum()), spy_pct=round(100 * (spy[:t].iloc[-1] / o - 1), 2)))
D = pd.DataFrame(path); W(D.to_string(index=False))
pk = D.loc[D.total.idxmax()]; W(f"peak {pk.total:+.2f}R at {pk.t} (SPY {pk.spy_pct:+.2f}%); close {P.radj.sum():+.2f}R -> gave back {pk.total - P.radj.sum():.2f}R")
txt = "\n".join(out); (OUT / "pautopsy_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
