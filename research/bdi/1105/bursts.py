"""BDI 2026-11-05 step 1 focus: bursts / stacking and give-back, all 7 accounts (journal run 1, R = pnl_adj / $ risk).
  setup burst  = >= 4 entries of the same setup and side within 10 minutes (chained: each entry within 10 min of the first)
  book burst   = >= 8 same-side entries (any setup) within 10 minutes
  stack        = same symbol, same side, >= 2 setups, entries within 30 min
Tags the patterns rows of the day (patterns_1105.csv notes += 'burst S<k>/B<k>/stack') and prints the summary.
Usage: python bursts.py    Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
T = pd.read_csv(HERE.parent / "nightly1105" / "trades.csv"); T = T[T.run_id == 1].copy()
T["nt"] = pd.to_datetime(T.nt, utc=True, format="mixed").dt.tz_convert(TZ)
NM = {"p": "primary", "t1": "testing", "t2": "testing2", "gy": "graveyard", "gen": "generator", "ex1": "explore1", "ll": "livelab"}
def chains(g, k):
    g = g.sort_values("nt"); out = pd.Series(-1, index=g.index); cid = 0; i = 0; idx = list(g.index); ts = g.nt.tolist()
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and ts[j + 1] - ts[i] <= pd.Timedelta("10min"): j += 1
        if j - i + 1 >= k: out.loc[idx[i:j + 1]] = cid; cid += 1; i = j + 1
        else: i += 1
    return out
T["sb"] = -1; T["bb"] = -1; T["stk"] = False
for (a, s, sd), g in T.groupby(["acct", "strategy", "side"]):
    c = chains(g, 4); T.loc[c.index, "sb"] = np.where(c >= 0, c, -1)
for (a, sd), g in T.groupby(["acct", "side"]):
    c = chains(g, 8); T.loc[c.index, "bb"] = c
for (a, sy, sd), g in T.groupby(["acct", "symbol", "side"]):
    if g.strategy.nunique() >= 2 and g.nt.max() - g.nt.min() <= pd.Timedelta("30min"): T.loc[g.index, "stk"] = True
P = []
def pr(*x): P.append(" ".join(str(y) for y in x)); print(P[-1])
pk = pd.read_csv(HERE.parent / "nightly1105" / "daily_peak.csv").set_index("acct")
pr("acct | trades | setup-burst entries (n, avg R, sum) | other entries avg R | book-burst entries (n, avg R) | stacks (lots, sum R) | give-back $ (peak t -> close)")
for a in NM:
    t = T[T.acct == a]; sb = t[t.sb >= 0]; ob = t[t.sb < 0]; bb = t[t.bb >= 0]; st = t[t["stk"]]
    pr(f"{a} | {len(t)} | {len(sb)} {sb.radj.mean():+.3f} {sb.radj.sum():+.1f} | {ob.radj.mean():+.3f} | {len(bb)} {bb.radj.mean():+.3f} | "
       f"{len(st)} {st.radj.sum():+.1f} | {pk.loc[a, 'giveback']:+.0f} ({pk.loc[a, 'peak_t']} {pk.loc[a, 'peak']:+.0f} -> {pk.loc[a, 'close']:+.0f})")
pr("\nlargest setup bursts (by |sum R|):")
G = T[T.sb >= 0].groupby(["acct", "strategy", "side", "sb"]).agg(n=("radj", "size"), t0=("nt", "min"), t1=("nt", "max"), R=("radj", "sum"),
                                                              stops=("exit_reason", lambda s: (s == "stop").sum())).reset_index()
G = G.reindex(G.R.abs().sort_values(ascending=False).index)
for _, r in G.head(12).iterrows():
    pr(f"  {r.acct} `{r.strategy}` {'S' if r.side == -1 else 'L'} {r.n} entries {r.t0:%H:%M}-{r.t1:%H:%M} {r.R:+.2f}R, stops {r.stops}")
pr(f"\nall setup bursts: {len(G)}, {G.n.sum()} entries, {G.R.sum():+.1f}R (avg {T[T.sb >= 0].radj.mean():+.3f}R vs non-burst {T[T.sb < 0].radj.mean():+.3f}R); "
   f"bursts with >= 75% stops: {(G.stops >= 0.75 * G.n).sum()} ({G[G.stops >= 0.75 * G.n].R.sum():+.1f}R)")
G.to_csv(HERE / "bursts_1105.csv", index=False)
# tag the patterns rows
Pt = pd.read_csv(HERE / "patterns_1105.csv")
T["account"] = T.acct.map(NM); T["et_s"] = T.nt.dt.strftime("%H:%M")
T["tag"] = np.where(T.sb >= 0, "burst S" + T.groupby(["acct", "strategy", "side", "sb"]).radj.transform("size").astype(str), "") + \
           np.where(T.bb >= 0, " bookburst", "") + np.where(T["stk"], " stack", "")
Pt["et_s"] = Pt.notes.str.extract(r"entry (\d\d:\d\d)")[0]
tg = T.groupby(["account", "symbol", "strategy", "et_s"]).tag.first().rename("tag").reset_index().rename(columns={"strategy": "setup"})
Pt = Pt.merge(tg, on=["account", "symbol", "setup", "et_s"], how="left")
Pt["notes"] = Pt.notes + np.where(Pt.tag.fillna("").str.strip() != "", "; " + Pt.tag.fillna("").str.strip(), "")
Pt.drop(columns=["et_s", "tag"]).to_csv(HERE / "patterns_1105.csv", index=False)
pr(f"\npatterns rows {len(Pt)}, tagged {(Pt.tag.fillna('').str.strip() != '').sum()}")
pr("\nEducational only - not financial advice."); (HERE / "bursts_out.txt").write_text("\n".join(P) + "\n")
