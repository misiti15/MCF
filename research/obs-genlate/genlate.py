"""Observer: is late-buying a GEN generator trait? Journals only (all accounts, run_id 1, all dates), 0 configs, descriptive.
Lateness proxy without bars: never-worked share (mfe_r < 0.15) and avg R of LONG trades; GEN setup names parsed into
window token and 'chase' (an extension condition with ge: ORHdist/FromPC/Since950/Ret15m/Ret5m/RSIslope/DayRngVsPrev/NewHOD/UpWick/VWAPxUp)
vs 'dip' (PDLdist le / ORLdist le / RSI5 le / NewLOD / RSIslope le / LowWick). usage: python genlate.py <journal_dir>
Educational only - not financial advice."""
import sys, sqlite3, glob, os, re
import numpy as np, pandas as pd
J = sys.argv[1]
T = []
for f in sorted(glob.glob(os.path.join(J, "*.db"))):
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("journal", "primary")
    t = pd.read_sql("select date, symbol, strategy, side, entry, stop, shares, pnl_adj, mfe_r, mae_r from trades where run_id=1 and side=1 and date<='2026-11-06'",
                    sqlite3.connect(f)); t["acct"] = a; T.append(t)
T = pd.concat(T); T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares).replace(0, np.nan)
T = T[T.R.notna()]; T["nw"] = T.mfe_r < 0.15; T["gen"] = T.strategy.str.startswith("GEN-")
def agg(g): return pd.Series(dict(n=len(g), R=g.R.sum(), avg=g.R.mean(), nw=g.nw.mean(), mfe_med=g.mfe_r.median(), days=g.date.nunique()))
print(f"long trades {len(T)}, dates {T.date.min()}..{T.date.max()}")
print("\nGEN vs non-GEN longs:\n", T.groupby("gen").apply(agg).round(3).to_string())
print("\nby account:\n", T.groupby("acct").apply(agg).round(3).to_string())
G = T[T.gen].copy()
G["win"] = G.strategy.str.extract(r"-(OPEN|AM|MID|LAM|LUNCH|PM|LATE)-")[0]
CH = r"(ORHdistge|FromPCATRge|FromPCge|Since950ATRge|Ret15mge|Ret15mATRge|Ret5mge|RSIslopege|DayRngVsPrevge|NewHOD|UpWickge|VWAPxUp|EMAdChgge|MACDhge)"
DP = r"(PDLdistle|ORLdistle|RSI5le|NewLOD|RSIslopele|LowWickge|BBpctle|Ret15mle|Ret15mATRle)"
G["chase"] = G.strategy.str.contains(CH); G["dip"] = G.strategy.str.contains(DP)
G["kind"] = np.select([G.chase & ~G.dip, G.dip & ~G.chase, G.chase & G.dip], ["chase", "dip", "both"], "other")
print("\nGEN longs by window:\n", G.groupby("win").apply(agg).round(3).to_string())
print("\nGEN longs by kind (name-parsed):\n", G.groupby("kind").apply(agg).round(3).to_string())
print("\nGEN long setups (n>=10), worst first:\n", G.groupby(["strategy"]).apply(agg).query("n>=10").sort_values("R").round(2).to_string())
N = T[~T.gen].copy(); N["fam"] = N.strategy.str.extract(r"^([A-Za-z]+\d*[A-Za-z]?)")[0]
print("\nnon-GEN long families (n>=20):\n", N.groupby("fam").apply(agg).query("n>=20").sort_values("avg").round(3).to_string())
# giveback: trades that reached mfe >= 0.5R and closed <= 0
T["gb"] = (T.mfe_r >= 0.5) & (T.R <= 0)
gb = lambda g: pd.Series(dict(n=len(g), reached05=(g.mfe_r >= 0.5).mean(), gaveback_of_reached=g.gb.sum() / max((g.mfe_r >= 0.5).sum(), 1), gb_R=g[g.gb].R.sum()))
print("\ngiveback (mfe >= 0.5R then closed <= 0):\n", T.groupby("gen").apply(gb).round(3).to_string())
print("\nGEN giveback by exit tag:\n", G.assign(gb=T.loc[G.index, "gb"] if False else (G.mfe_r >= 0.5) & (G.R <= 0),
      ex=G.strategy.str.extract(r"-(hold|holdtr|t05s05|t05s1|t1s1|t1s05)-long")[0]).groupby("ex").apply(lambda g: pd.Series(dict(n=len(g), avg=g.R.mean(), mfe_med=g.mfe_r.median(), gb_share=g.gb.mean()))).round(3).to_string())
