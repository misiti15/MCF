"""Step 1-2: per account per session, the intraday marked P/L curve (realized pnl_adj + open lots marked at the 1-min
close less a market exit cost), peak / trough / close / giveback, and attribution of the peak->close giveback.
Writes daily_peaks.csv, giveback_attr.csv (per trade contributions), giveback_attr_out.txt. Educational only."""
import numpy as np
import pandas as pd

from common import ACCTS, NAMES, OUT, bars, load_trades, marked_matrix, TZ

T = load_trades()
days, contrib = [], []
for a in ACCTS:
    for day, d in T[T.acct == a].groupby("date"):
        d = d.reset_index(drop=True)
        g, M = marked_matrix(d, day)
        cur = M.sum(0)
        ip, it = int(cur.argmax()), int(cur.argmin())
        close = float(d.pnl_adj.sum())
        tp = g[ip]
        idx = {}
        for k in ("SPY", "QQQ"):
            b = bars(day, k)
            cl = b.close.reindex(g - pd.Timedelta(minutes=1)).ffill()
            idx[k] = (cl.values[-1] / cl.values[ip] - 1) * 100 if ip < len(g) else np.nan
            o = b.open.iloc[0]
            idx[k + "_day"] = (b.close.iloc[-1] / o - 1) * 100
        # trades open at the peak and the book's net direction there
        openp = (d.nt < tp) & (d.et > tp)
        mk = M[:, ip]
        px = np.array([bars(day, s).close.asof(tp - pd.Timedelta(minutes=1)) if bars(day, s) is not None else np.nan for s in d.symbol])
        net = float(np.nansum(np.where(openp, d.side * d.shares * px, 0)))
        gross = float(np.nansum(np.where(openp, d.shares * px, 0)))
        c = M[:, -1] - mk
        cat = np.where(d.nt >= tp, "b_entered_after_peak",
                       np.where(~openp, "closed_before_peak", np.where(mk > 0, "a_open_winner_at_peak", "a2_open_loser_at_peak")))
        dd = d[["uid", "acct", "date", "strategy", "side", "symbol", "hour", "poll", "exit_reason", "hold", "pnl_adj", "radj", "nt", "et"]].copy()
        dd["mark_at_peak"], dd["contrib"], dd["cat"] = mk, c, cat
        dd["late_flat"] = (d.exit_reason == "flatten") & (d.et.dt.strftime("%H:%M") >= "15:50")
        # (c) index: trade side opposite to SPY's move from the peak to the close
        dd["against_index"] = np.sign(d.side) == -np.sign(idx["SPY"])
        contrib.append(dd)
        days.append(dict(acct=a, date=day, trades=len(d), peak=round(cur[ip], 2), peak_t=tp.strftime("%H:%M"),
                         trough=round(cur[it], 2), trough_t=g[it].strftime("%H:%M"), close=round(close, 2),
                         giveback=round(cur[ip] - close, 2), gb_pct=round((cur[ip] - close) / cur[ip] * 100, 0) if cur[ip] > 0 else np.nan,
                         trades_after_peak=int((d.nt >= tp).sum()), open_at_peak=int(openp.sum()),
                         net_exposure_at_peak=round(net), gross_at_peak=round(gross),
                         spy_peak_to_close=round(idx["SPY"], 2), qqq_peak_to_close=round(idx["QQQ"], 2),
                         spy_day=round(idx["SPY_day"], 2)))
D = pd.DataFrame(days)
D.to_csv(OUT / "daily_peaks.csv", index=False)
C = pd.concat(contrib, ignore_index=True)
C.to_csv(OUT / "giveback_attr.csv", index=False)

out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
P(D.to_string(index=False))
P("\n== giveback counts (peak >= X and closed red / gave back > 50%)")
for a in ACCTS:
    x = D[D.acct == a]
    for X in (50, 100, 250):
        pk = x[x.peak >= X]
        P(f"{NAMES[a]:9s} X={X:>3}: days {len(x)}, peak>=X {len(pk)}, of those closed red {int((pk.close < 0).sum())}, gave back >50% {int((pk.gb_pct > 50).sum())}")
    P(f"{NAMES[a]:9s} sum peak {x.peak.sum():.0f}, sum close {x.close.sum():.0f}, sum giveback {x.giveback.sum():.0f}, median giveback {x.giveback.median():.0f}, "
      f"median peak time {sorted(x.peak_t)[len(x)//2]}, days peak before 11:00 {int((x.peak_t < '11:00').sum())}")

P("\n== attribution of the peak->close change (sum over days), by category")
C2 = C[C.cat != "closed_before_peak"]
for a in ACCTS:
    x = C2[C2.acct == a]
    gb = D[D.acct == a].giveback.sum()
    P(f"--- {NAMES[a]} (total giveback {gb:.0f}; trade contributions sum {x.contrib.sum():.0f})")
    P(x.groupby("cat").agg(n=("uid", "size"), contrib=("contrib", "sum")).round(1).to_string())
    P(" by exit reason:", x.groupby("exit_reason").contrib.sum().round(1).to_dict())
    P(" late-day flatten exits (>=15:50):", round(x[x.late_flat].contrib.sum(), 1), "n", int(x.late_flat.sum()))
    P(" open winners at peak, how they exited:", x[x.cat == "a_open_winner_at_peak"].groupby("exit_reason").contrib.agg(["size", "sum"]).round(1).to_dict("index"))
    P(" against SPY's peak->close move:", round(x[x.against_index].contrib.sum(), 1), "| with:", round(x[~x.against_index].contrib.sum(), 1))
    P(" side:", x.groupby("side").contrib.sum().round(1).to_dict())
    P(" by entry hour:", x.groupby("hour").contrib.sum().round(1).to_dict())
    P(" worst setups:", x.groupby("strategy").contrib.sum().sort_values().head(6).round(1).to_dict())
    P(" best setups:", x.groupby("strategy").contrib.sum().sort_values().tail(3).round(1).to_dict())
    hb = pd.cut(x.hold, [0, 15, 30, 60, 120, 400])
    P(" by hold (min):", x.groupby(hb, observed=True).contrib.sum().round(1).to_dict())
P("\n== per day: index move vs book direction at the peak")
P(D[["acct", "date", "peak", "peak_t", "close", "giveback", "net_exposure_at_peak", "gross_at_peak", "spy_peak_to_close", "qqq_peak_to_close"]].to_string(index=False))
# share of each day's giveback explained by trades against the index
g = C2.groupby(["acct", "date"]).apply(lambda x: pd.Series(dict(total=x.contrib.sum(), against=x[x.against_index].contrib.sum(),
     after=x[x.cat == "b_entered_after_peak"].contrib.sum(), openwin=x[x.cat == "a_open_winner_at_peak"].contrib.sum(),
     openlos=x[x.cat == "a2_open_loser_at_peak"].contrib.sum(), late=x[x.late_flat].contrib.sum())), include_groups=False).round(1)
P(g.to_string())
open(OUT / "giveback_attr_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
