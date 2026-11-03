"""Per-setup detail for 2026-11-02 suggestions, marks and watches (all accounts merged, real trades run 1, costs in:
R = pnl_adj / $ risk). avg R, w/o best session + its share, avg R on the 3 busiest sessions (by trade count), since-date.
Usage: python detail.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, symbol, entry, stop, shares, pnl, pnl_adj, exit_reason from trades where run_id=1 and exit is not null", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows); T["risk"] = (T.entry - T.stop).abs() * T.shares
T = T[T.risk > 0]; T["R"] = T.pnl_adj / T.risk
def card(name, since=None, acct=None):
    d = T[T.strategy == name]
    if acct: d = d[d.acct.isin(acct)]
    if since: d = d[d.date >= since]
    if d.empty: return f"{name}: no trades"
    by = d.groupby("date").R.agg(["sum", "size"])
    best = by["sum"].idxmax(); tot = d.R.sum()
    ex = d[d.date != best].R.mean() if len(by) > 1 else np.nan
    busy = by.sort_values("size", ascending=False).head(3).index
    b3 = d[d.date.isin(busy)].R.mean()
    return (f"{name}{' since ' + since if since else ''}{' ' + ','.join(acct) if acct else ''}: {len(d)} trades / {len(by)} sessions, "
            f"win {100 * (d.pnl_adj > 0).mean():.1f}%, avg R {d.R.mean():+.3f}, sum {tot:+.2f}R, ${d.pnl_adj.sum():+.2f}; "
            f"w/o best day ({best}) {ex:+.3f} (share {by['sum'].max() / tot * 100 if tot else np.nan:.0f}%); "
            f"3 busiest {','.join(busy)} avg {b3:+.3f}; accts {sorted(d.acct.unique())}")
out = []
for n in ["NS5-sma50-flush-oversold-long-FD", "ST4-emadn-long-am-t1s05-FD", "RW6G1-ns2-up3-vwap2sd-short-FD", "MF1-945-flowsell-vwapup",
          "ST7-rsi50dn-long-pm-t1s1-FD", "MF4-h40-open-flowsell-FD", "L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD",
          "MF2-open-rsimidhi-flowsell-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "NS4-pm-vwap-reclaim-oversold-short-FD", "RW7-gapdn-bounce-early-short-FD", "RW1-gapdn-bounce-flowsell-short-FD",
          "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short", "NM-HL-T75-pm-long",
          "CWT14-failbrk-pdl-p10-lowvol-long", "CWT14-failbrk-pdl-p10-long", "CWT13-vwapstretch-z05-long"]:
    out.append(card(n))
out.append("-- since marks / moves")
out.append(card("NS4-pm-vwap-reclaim-oversold-short-FD", "2026-10-27"))
out.append(card("GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short", "2026-10-27"))
out.append(card("CWT14-failbrk-pdl-p10-lowvol-long", "2026-10-28"))
out.append(card("CWT14-failbrk-pdl-p05-R2A-long")); out.append(card("CWT14-failbrk-pdl-p05-R2A-short"))
out.append(card("ST7-rsi50dn-long-pm-t1s1-FD", "2026-10-26", ["p"]))
out.append(card("L3-gap-slope-fromopen-FD", "2026-10-30", ["p"])); out.append(card("L3-gap-slope-rsi5hi-FD", "2026-10-30", ["p"]))
# Primary daily record since Day 1
P = T[T.acct == "p"].groupby("date").agg(n=("R", "size"), R=("R", "sum"), adj=("pnl_adj", "sum"), pnl=("pnl", "sum")).round(2)
out.append("-- Primary per session\n" + P.to_string())
s = P[P.index >= "2026-10-23"]
out.append(f"since Day 1 2026-10-23: {len(s)} sessions, {(s.adj > 0).sum()} positive, ${s.adj.sum():+.2f} after costs (${s.pnl.sum():+.2f} before)")
out.append(f"since start: {len(P)} sessions, {(P.adj > 0).sum()} positive, ${P.adj.sum():+.2f}; last 10 green {(P.adj.tail(10) > 0).sum()}")
# L3 on leveraged / inverse ETFs (live, all accounts)
lev = set("SOXS SOXL SQQQ TQQQ SPXU SPXL UVIX UVXY SVIX TZA TNA LABD LABU GDXD GDXU NVDL NVDS TSLL TSLQ TSLZ AMDL MSTU MSTZ CONL METU QLD QID SDS SSO SH PSQ UPRO SPXS FNGU FNGD YINN YANG BOIL KOLD NUGT DUST JDST JNUG ERX ERY FAS FAZ TMF TMV TBT UCO SCO DRIP GUSH WEBL WEBS".split())
for k in ("L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "L3-gap-slope-lowdist-FD"):
    d = T[T.strategy == k]; m = d.symbol.isin(lev)
    out.append(f"{k} live leveraged/inverse ETF list: {m.sum()} trades avg {d[m].R.mean():+.3f} sum {d[m].R.sum():+.2f}R | others {(~m).sum()} avg {d[~m].R.mean():+.3f}")
# same symbol re-entry after a stop, same setup, same day (all accounts)
T2 = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, symbol, side, entry, stop, shares, pnl_adj, entry_time, exit_time, exit_reason from trades where run_id=1 and exit is not null", c)
    t["acct"] = a; T2.append(t)
U = pd.concat(T2); U["risk"] = (U.entry - U.stop).abs() * U.shares; U = U[U.risk > 0]; U["R"] = U.pnl_adj / U.risk
U["nt"] = pd.to_datetime(U.entry_time, utc=True, format="mixed"); U["et"] = pd.to_datetime(U.exit_time, utc=True, format="mixed")
U = U.sort_values("nt"); flag = []
for r in U.itertuples():
    g = U[(U.acct == r.acct) & (U.date == r.date) & (U.symbol == r.symbol) & (U.side == r.side) & (U.et < r.nt) & (U.exit_reason == "stop")]
    flag.append(len(g) > 0)
U["after_stop"] = flag
out.append("-- entries on a symbol+side already stopped earlier that day in the same account (any setup), by account")
out.append(U.groupby(["acct", "after_stop"]).R.agg(["size", "mean", "sum"]).round(3).to_string())
out.append("by date (all accts, after_stop only):\n" + U[U.after_stop].groupby("date").R.agg(["size", "mean", "sum"]).round(2).to_string())
U.to_csv(S / "allrows.csv", index=False)
txt = "\n".join(out); open(OUT / "detail_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
