"""Per-account headline, per-setup winner/loser autopsy and descriptive splits for 2026-10-21 (trades.csv).
Costs in: P/L = journal pnl_adj, avg R = pnl_adj / $ risk (radj); journal r_multiple shown as avgR_j. Writes autopsy_out.txt.
Usage: python autopsy.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 60)
T = pd.read_csv(OUT / "trades.csv")
for c in ("nt", "et", "st"): T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert(TZ)
out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
def agg(d):
    w, l = d[d.pnl_adj > 0], d[d.pnl_adj <= 0]
    return pd.Series(dict(n=len(d), win=round(100 * (d.pnl_adj > 0).mean()), avgR=round(d.radj.mean(), 3), avgR_j=round(d.r_multiple.mean(), 3),
        pnl=round(d.pnl.sum(), 2), adj=round(d.pnl_adj.sum(), 2), stop=int((d.exit_reason == "stop").sum()), tgt=int((d.exit_reason == "target").sum()),
        flat=int((d.exit_reason == "flatten").sum()), mfe_w=round(w.mfe.median(), 2), mae_w=round(w.mae.median(), 2),
        mfe_l=round(l.mfe.median(), 2), mae_l=round(l.mae.median(), 2), never=int(d.never.sum()), never_adj=round(d[d.never].pnl_adj.sum(), 2),
        lost_half=int(d.lost_after_half.sum()), gb_w=round((w.mfe - w.radj).median(), 2), tmfe_w=round(w.t_mfe.median(), 1),
        tmfe_l=round(l.t_mfe.median(), 1), maxcl=int(d.cluster.max()), cl5=int((d.cluster >= 5).sum()), twin=int(d.twin.sum()),
        lat=round(d.lat.median(), 1), lat90=round(d.lat.quantile(.9), 1), slip=round(d.slip_bps.mean(), 1), gt11=int((d.radj < -1.1).sum())))
def grp(d, by):
    return pd.DataFrame({k: agg(g) for k, g in d.groupby(by)}).T
# market
P("== index path 2026-10-21 (SIP 1-min; % from the 09:30 open)")
for k in ("SPY", "QQQ", "IWM"):
    b = pd.read_parquet(S / "bars" / f"{k}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    b = b.between_time("09:30", "15:59"); o = b.open.iloc[0]
    pct = lambda x: round((x / o - 1) * 100, 2)
    marks = {t: pct(b.close.asof(pd.Timestamp(f"2026-10-21 {t}", tz=TZ))) for t in ("09:45", "10:00", "10:30", "11:00", "11:30", "12:00", "13:00", "14:00", "15:00", "15:55")}
    P(k, "open", round(o, 2), "close", pct(b.close.iloc[-1]), "| high", pct(b.high.max()), b.high.idxmax().strftime("%H:%M"),
      "| low", pct(b.low.min()), b.low.idxmin().strftime("%H:%M"), "|", marks)
for a in ("p", "t1", "t2", "gy", "gen"):
    d = T[T.acct == a]
    P(f"\n===== {a}"); P(agg(d).to_dict())
    g = grp(d, "strategy").sort_values("adj")
    P("-- by setup (all)"); P(g.to_string())
    for by, name in [("side", "side"), ("hour", "entry hour"), ("exit_reason", "exit"), ("poll", "signal poll"), ("lot_no", "lot no"),
                     ("twin", "twin (another setup took same symbol+side <=3 min earlier)"), ("refire", "refire")]:
        P(f"-- {name}"); P(grp(d, by)[["n", "win", "avgR", "adj", "never", "stop", "tgt"]].to_string())
    P("-- cluster size (same setup, same poll)"); P(grp(d, pd.cut(d.cluster, [0, 1, 4, 9, 100]))[["n", "win", "avgR", "adj", "never"]].to_string())
    P("-- latency (signal->fill s) terciles"); P(grp(d, pd.qcut(d.lat.rank(method="first"), 3, labels=["fast", "mid", "slow"]))[["n", "win", "avgR", "adj", "lat"]].to_string())
    l = d[d.pnl_adj <= 0]
    P("-- loser types: never (MFE<0.2R)", int(d.never.sum()), round(d[d.never].pnl_adj.sum(), 2), "| small MFE 0.2-0.5R",
      int(((l.mfe >= .2) & (l.mfe < .5)).sum()), round(l[(l.mfe >= .2) & (l.mfe < .5)].pnl_adj.sum(), 2),
      "| reached >=0.5R then lost", int(d.lost_after_half.sum()), round(d[d.lost_after_half].pnl_adj.sum(), 2))
    P("-- worst 8 trades"); P(d.nsmallest(8, "pnl_adj")[["symbol", "strategy", "side", "nt", "exit_reason", "radj", "pnl_adj", "mfe", "mae", "twin", "lot_no"]].to_string())
open(OUT / "autopsy_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
