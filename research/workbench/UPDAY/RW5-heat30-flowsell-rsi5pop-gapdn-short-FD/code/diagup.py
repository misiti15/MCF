import sys, pandas as pd
pd.set_option("display.width",250)
T=pd.read_pickle(sys.argv[1])
for n in ("PARENT","WB3"):
  for k in ("replay","2y"):
    t=T[n][k].copy()
    t["b950"]=pd.cut(t.spy950,[-9,-0.25,0,0.15,0.3,0.5,9]); t["b30"]=pd.cut(t.spy30,[-9,-0.1,0,0.1,0.2,9]); t["btod"]=pd.cut(t.tod,[900,1030,1100,1200,1300,1600])
    print(f"#### {n} {k}  kinds:", t.groupby("dtype").kind.value_counts(normalize=True).round(2).to_dict())
    for b in ("b950","b30","btod"):
        x=t.pivot_table(index=b,columns="dtype",values="r",aggfunc=["mean","size"],observed=True); print(x.round(3).to_string())
