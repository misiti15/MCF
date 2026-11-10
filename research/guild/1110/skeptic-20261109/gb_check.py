"""Skeptic check of obs-genlate giveback: day concentration and family scope (journals 10-06..11-06, longs, run_id 1)."""
import sys, glob, os, sqlite3, numpy as np, pandas as pd
T=[]
for f in sorted(glob.glob(os.path.join(sys.argv[1],"*.db"))):
    a=os.path.basename(f).replace("mcf-data-","").replace(".db","").replace("journal","primary")
    t=pd.read_sql("select date,strategy,side,entry,stop,shares,pnl_adj,mfe_r from trades where run_id=1 and date<='2026-11-06'",sqlite3.connect(f)); t["acct"]=a; T.append(t)
T=pd.concat(T); T["R"]=T.pnl_adj/((T.entry-T.stop).abs()*T.shares).replace(0,np.nan); T=T[T.R.notna()]
T["gen"]=T.strategy.str.startswith("GEN-"); T["gb"]=(T.mfe_r>=.5)&(T.R<=0)
T["fam"]=np.where(T.gen,"GEN",T.strategy.str.extract(r"^([A-Za-z]+\d*)")[0])
for side,nm in ((1,"LONG"),(-1,"SHORT")):
    X=T[T.side==side]
    print(f"\n== {nm}: giveback R (mfe>=0.5R then closed<=0) by family, n>=50 ==")
    g=X.groupby("fam").apply(lambda g: pd.Series(dict(n=len(g),R=g.R.sum(),gbR=g[g.gb].R.sum(),gb_of_reached=g.gb.sum()/max((g.mfe_r>=.5).sum(),1)))).query("n>=50").sort_values("gbR")
    print(g.round(2).to_string()); print("total gbR", round(X[X.gb].R.sum(),1), "GEN share", round(X[X.gb&X.gen].R.sum()/X[X.gb].R.sum(),2))
G=T[T.gen&(T.side==1)]; d=G.groupby("date").R.sum().sort_values(); dg=G[G.gb].groupby("date").R.sum().sort_values()
print("\nGEN long R by day (worst 3):", d.head(3).round(1).to_dict(), "total", round(d.sum(),1), "worst-day share", round(d.iloc[0]/d.sum(),2))
print("GEN long giveback R by day (worst 3):", dg.head(3).round(1).to_dict(), "total", round(dg.sum(),1), "worst-day share", round(dg.iloc[0]/dg.sum(),2))
print("Educational only - not financial advice.")
