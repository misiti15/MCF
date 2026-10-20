"""Intraday peak vs close for 2026-10-20, giveback1019 method: the marked P/L curve per minute (realized journal pnl_adj
+ open lots at the previous 1-min SIP close less a market exit cost of 1 bps + $0.01/sh), peak / trough / close, and the
attribution of the peak->close change per trade: (b) entered after the peak, (a) open winner at the peak, (a2) open loser
at the peak; plus (c) against SPY's peak->close move and (d) late flatten exits (>= 15:50).
All four journals are complete on 2026-10-20 (no replayed trades).
Also prints the runner's own intraday snapshot peak/trough (intraday/2026-10-20.jsonl). Writes giveback_out.txt, daily_peak.csv.
Usage: python giveback.py <scratch>   Educational only - not financial advice."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-10-20"; TZ = "America/New_York"
T = pd.read_csv(OUT / "trades.csv")
for c in ("nt", "et"): T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert(TZ)
T["est"] = False
A = T[["acct", "symbol", "strategy", "side", "entry", "shares", "pnl_adj", "exit_reason", "est", "nt", "et"]].copy()
bars = {}
def bar(s):
    if s not in bars:
        b = pd.read_parquet(S / "bars" / f"{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ); bars[s] = b
    return bars[s]
g = pd.date_range(pd.Timestamp(f"{D} 09:31", tz=TZ), pd.Timestamp(f"{D} 16:00", tz=TZ), freq="1min")
spy = bar("SPY").close.reindex(g - pd.Timedelta(minutes=1)).ffill()
qqq = bar("QQQ").close.reindex(g - pd.Timedelta(minutes=1)).ffill()
out, days, att = [], [], []
P = lambda *x: out.append(" ".join(str(y) for y in x))
for a in ("p", "t1", "t2", "gen"):
    d = A[A.acct == a].reset_index(drop=True)
    M = np.zeros((len(d), len(g)))
    for i, r in enumerate(d.itertuples()):
        closed = g >= r.et; openm = (g > r.nt) & ~closed
        M[i, closed] = r.pnl_adj
        if openm.any():
            cl = pd.Series(bar(r.symbol).close.reindex(g - pd.Timedelta(minutes=1)).values).ffill().bfill().values
            M[i, openm] = r.side * (cl[openm] - r.entry) * r.shares - r.shares * (0.01 + cl[openm] * 1e-4)
    cur = M.sum(0); ip, it = int(cur.argmax()), int(cur.argmin()); tp = g[ip]
    close = float(d.pnl_adj.sum())
    openp = (d.nt < tp) & (d.et > tp); mk = M[:, ip]; c = M[:, -1] - mk
    spy_pc = (spy.values[-1] / spy.values[ip] - 1) * 100
    cat = np.where(d.nt >= tp, "b_after_peak", np.where(~openp, "closed_before_peak", np.where(mk > 0, "a_open_winner", "a2_open_loser")))
    dd = d.assign(mark_at_peak=mk, contrib=c, cat=cat, against=np.sign(d.side) == -np.sign(spy_pc),
                  late=(d.exit_reason == "flatten") & (d.et.dt.strftime("%H:%M") >= "15:50"))
    att.append(dd)
    rn = [json.loads(x) for x in open(S / a / "intraday" / f"{D}.jsonl")]
    rpk = max(rn, key=lambda x: x["total"]); rtr = min(rn, key=lambda x: x["total"])
    days.append(dict(acct=a, trades=len(d), est_trades=int(d.est.sum()), peak=round(cur[ip], 2), peak_t=tp.strftime("%H:%M"),
                     trough=round(cur[it], 2), trough_t=g[it].strftime("%H:%M"), close=round(close, 2), giveback=round(cur[ip] - close, 2),
                     after_peak=int((d.nt >= tp).sum()), open_at_peak=int(openp.sum()), spy_peak_to_close=round(spy_pc, 2),
                     qqq_peak_to_close=round((qqq.values[-1] / qqq.values[ip] - 1) * 100, 2),
                     runner_peak=f"{rpk['total']} ({rpk['t']})", runner_trough=f"{rtr['total']} ({rtr['t']})", runner_last=f"{rn[-1]['total']} ({rn[-1]['t']})"))
    x = dd[dd.cat != "closed_before_peak"]
    P(f"\n===== {a}: peak {cur[ip]:.2f} at {tp:%H:%M}, trough {cur[it]:.2f} at {g[it]:%H:%M}, close {close:.2f}, giveback {cur[ip]-close:.2f}; "
      f"SPY peak->close {spy_pc:+.2f}%")
    P("by category:", x.groupby("cat").agg(n=("symbol", "size"), contrib=("contrib", "sum")).round(1).to_dict("index"))
    P("open winners at peak, exit:", x[x.cat == "a_open_winner"].groupby("exit_reason").contrib.agg(["size", "sum"]).round(1).to_dict("index"))
    P("against SPY's peak->close move:", round(x[x.against].contrib.sum(), 1), "| with:", round(x[~x.against].contrib.sum(), 1))
    P("late flatten (>=15:50):", round(x[x.late].contrib.sum(), 1), "n", int(x.late.sum()))
    P("side:", x.groupby("side").contrib.sum().round(1).to_dict())
    P("by entry hour:", x.groupby(x.nt.dt.hour).contrib.sum().round(1).to_dict())
    P("worst setups:", x.groupby("strategy").contrib.sum().sort_values().head(6).round(1).to_dict())
    P("best setups:", x.groupby("strategy").contrib.sum().sort_values().tail(3).round(1).to_dict())
    # setup marks at the peak minute and at the trough minute
    P("setups at peak:", pd.Series(mk, index=d.strategy).groupby(level=0).sum().sort_values().round(1).pipe(lambda s: {**s.head(3).to_dict(), **s.tail(3).to_dict()}))
    P("setups at trough:", pd.Series(M[:, it], index=d.strategy).groupby(level=0).sum().sort_values().round(1).pipe(lambda s: {**s.head(4).to_dict(), **s.tail(2).to_dict()}))
    P("curve every 30 min:", {g[j].strftime("%H:%M"): round(cur[j]) for j in range(0, len(g), 30)})
Dd = pd.DataFrame(days); Dd.to_csv(OUT / "daily_peak.csv", index=False)
pd.concat(att).to_csv(OUT / "giveback_attr.csv", index=False)
pd.set_option("display.width", 260)
out.insert(0, Dd.to_string(index=False))
open(OUT / "giveback_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
