"""Decompose a broker-vs-journal gap step between two status snapshots (Testing 2, 2026-10-15): broker position changes vs
journal entries/exits booked in between, and per-symbol broker MTM vs journal MTM. Read-only. Educational only."""
import sys, json, pandas as pd
S, acct, t_a, t_b = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
st = pd.read_csv(f"{S}/{acct}/st.csv"); st = st[(st.session == "2026-10-15") & (st.phase == "trading")]
a = st[st.asof_et == f"2026-10-15 {t_a} ET"].iloc[-1]; b = st[st.asof_et == f"2026-10-15 {t_b} ET"].iloc[-1]
ta, tb = pd.Timestamp(a["asof"]), pd.Timestamp(b["asof"])
pa, pb = json.loads(a.positions), json.loads(b.positions)
T = pd.read_csv("trades.csv"); T = T[T.acct == acct].copy()
for c in ("nt", "et"): T[c] = pd.to_datetime(T[c], utc=True)
bars = {}
def px(s, t):
    if s not in bars:
        x = pd.read_parquet(f"{S}/bars/{s}.parquet"); x.index = pd.to_datetime(x.index, utc=True); bars[s] = x
    x = bars[s]; x = x[x.index < t.floor("1min")]; return x.close.iloc[-1]
rows = []
for s in sorted(set(pa) | set(pb) | set(T[((T.nt > ta) & (T.nt <= tb)) | ((T.et > ta) & (T.et <= tb))].symbol)):
    d = T[T.symbol == s]
    # journal P/L change of this symbol over the interval (realized + marked)
    def jv(t):
        x = d[d.nt <= t]
        return sum(r.pnl if r.et <= t else r.side * (px(s, t) - r.entry) * r.shares for r in x.itertuples())
    j = jv(tb) - jv(ta)
    qa, qb = pa.get(s, 0), pb.get(s, 0)
    mtm = qa * (px(s, tb) - px(s, ta)) if qa else 0.0
    rows.append(dict(symbol=s, qa=qa, qb=qb, jentries=int(((d.nt > ta) & (d.nt <= tb)).sum()), jexits=int(((d.et > ta) & (d.et <= tb)).sum()),
                     journal=round(j, 2), broker_held_mtm=round(mtm, 2), diff=round(mtm - j, 2)))
o = pd.DataFrame(rows).sort_values("diff")
print(f"equity change {b.equity - a.equity:.2f}; journal change {o.journal.sum():.2f}; held-mtm {o.broker_held_mtm.sum():.2f}")
print(o.head(12).to_string()); print(o.tail(5).to_string())
