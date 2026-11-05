"""Move Hunt 11-05, descriptive second cut (v1 catalogue unchanged in moves.csv): on a one-factor crash day the v1 top 50
are index ETPs at the 09:35 decision. This cut keeps (a) single names: |corr| of 5-min returns to SPY (09-22..11-04) < 0.85,
and (b) decision points >= 09:50 (the live no-entry-before rule), then rescores capture with the same v1 rules, 7 accounts.
Usage: python moves_alt.py <scratch>   Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); D = "2026-11-05"; TZ = "America/New_York"
R = pd.read_parquet(S / "mh" / D / "rows.parquet")
B5 = pd.read_parquet(S / "mh" / D / "bars5.parquet"); B5 = B5[B5.index < pd.Timestamp(D, tz=TZ)]
X = B5.pivot_table(index=B5.index, columns="symbol", values="close").pct_change(fill_method=None)
cor = X.corrwith(X["SPY"]).abs()
R = R[(R.symbol.map(cor) < 0.85) & (R.tod >= 950) & ~R.blackout]
T, G = [], []
for a in ("p", "t1", "t2", "gy", "gen", "ex1", "ll"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select symbol, strategy, side, entry_time, entry, stop, shares, pnl_adj from trades where date=? and run_id=1", c, params=(D,)); t["acct"] = a; T.append(t)
    g = pd.read_sql("select symbol, strategy, side, ts, status, reason from signals where day=? and run_id=1", c, params=(D,)); g["acct"] = a; G.append(g)
T = pd.concat(T); G = pd.concat(G)
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ); G["et"] = pd.to_datetime(G.ts, utc=True, format="mixed").dt.tz_convert(TZ)
mod = lambda x: x.dt.hour * 60 + x.dt.minute - 570 + x.dt.second / 60
T["m"] = mod(T.et); G["m"] = mod(G.et); T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares)
out = []
for side, col, mn, sgn in (("long", "up_atr", "up_min", 1), ("short", "dn_atr", "dn_min", -1)):
    best = R.loc[R.groupby("symbol")[col].idxmax()].sort_values(col, ascending=False).head(25)
    for rank, (_, r) in enumerate(best.iterrows(), 1):
        m0 = (r.tod // 100 - 9) * 60 + r.tod % 100 - 30; m1 = m0 + r[mn]; ts = T[T.symbol == r.symbol]; gs = G[G.symbol == r.symbol]
        w = lambda x: x[(x.m >= m0 - 30) & (x.m <= m1)]
        right, wrong, sk = w(ts[ts.side == sgn]), w(ts[ts.side == -sgn]), w(gs[(gs.side == sgn) & (gs.status != "submitted")])
        why = "caught" if len(right) else ("skipped: " + "; ".join(sorted(set(sk.reason.fillna("?").str[:30])))[:80] if len(sk) else
               "wrong side only" if len(wrong) else "traded outside the move" if len(ts) else "no setup signalled")
        out.append(dict(side=side, rank=rank, symbol=r.symbol, tod=int(r.tod), extreme_min=int(r[mn]), move_atr=round(r[col], 2),
                        gap=round(r.gap, 2), fromOpen=round(r.fromOpen, 2), rsi5=round(r.rsi5, 1), spy_fo=round(r.spy_fo, 2),
                        caught_by=";".join(sorted(set(right.acct + ":" + right.strategy))), r_captured=round(right.R.sum(), 2),
                        n_wrong=len(wrong), r_wrong=round(wrong.R.sum(), 2), why=why))
O = pd.DataFrame(out); O.to_csv(Path(__file__).resolve().parent / "moves_alt_1105.csv", index=False)
print(O.to_string(index=False))
c = O.r_captured.ne(0) | O.caught_by.ne("")
print(f"\nSINGLE-NAME >= 09:50 CAPTURE: {c.sum()}/{len(O)} = {c.mean():.0%} (long {c[O.side == 'long'].sum()}/25, short {c[O.side == 'short'].sum()}/25); "
      f"R captured {O.r_captured.sum():+.2f}; wrong-side {O.n_wrong.sum()} trades {O.r_wrong.sum():+.2f}R")
print(O.why.str.split(":").str[0].value_counts().to_string())
print("decision time histogram:", O.tod.value_counts().sort_index().to_dict())
print("\nEducational only - not financial advice.")
