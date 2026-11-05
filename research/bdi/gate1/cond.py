"""GATE1: per-setup (and family x side) avg R by checkpoint state (entries >= 10:00, latest 30-min checkpoint, k=1),
TRAIN / VALID / LIVE; flags 'conditional performers' (PLAN.md). Usage: python cond.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
SN = {1: "UP", -1: "DOWN", 0: "MIXED"}
T = pd.read_parquet(Path(sys.argv[1]) / "trades.parquet")
T = T[T.w.isin(["TRAIN", "VALID", "LIVE"]) & (T.m >= 600) & T.cp.notna()]
acc = pd.read_csv("/home/user/MCF/research/history2y/data/bt_lab1104/setups.csv").drop_duplicates("setup").set_index("setup").account
out = {}
for key in ["setup", "fs"]:
    g = T.groupby([key, "w", "st"]).agg(n=("r", "size"), d=("date", "nunique"), a=("r", "mean")).reset_index()
    g["st"] = g.st.map(SN)
    p = g.pivot_table(index=[key], columns=["w", "st"], values=["a", "n"])
    p.columns = [f"{w}_{s}_{v}" for v, w, s in p.columns]
    out[key] = p
P = out["setup"].copy(); P["home"] = P.index.map(acc)
rows = []
for s, r in P.iterrows():
    for st in ["UP", "DOWN", "MIXED"]:
        oth = [x for x in ["UP", "DOWN", "MIXED"] if x != st]
        ta, tn, va = r.get(f"TRAIN_{st}_a"), r.get(f"TRAIN_{st}_n", 0), r.get(f"VALID_{st}_a")
        cond = (ta > 0.05) and (tn >= 60) and (va > 0) and all((r.get(f"TRAIN_{o}_a", np.nan) <= 0) for o in oth)
        rows.append(dict(setup=s, home=r.home, state=st, TRAIN_n=tn, TRAIN_a=ta, VALID_n=r.get(f"VALID_{st}_n", 0), VALID_a=va,
                         LIVE_n=r.get(f"LIVE_{st}_n", 0), LIVE_a=r.get(f"LIVE_{st}_a"),
                         TRAIN_other=np.nanmean([r.get(f"TRAIN_{o}_a", np.nan) for o in oth]),
                         VALID_other=np.nanmean([r.get(f"VALID_{o}_a", np.nan) for o in oth]), conditional=cond))
C = pd.DataFrame(rows).round(3); C.to_csv(HERE / "conditional_setups.csv", index=False)
out["fs"].round(3).to_csv(HERE / "family_side_by_state.csv")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print("conditional:"); print(C[C.conditional].sort_values("VALID_a", ascending=False).to_string())
# both-window positive in a state (n>=60 each)
B = C[(C.TRAIN_a > 0) & (C.VALID_a > 0) & (C.TRAIN_n >= 60) & (C.VALID_n >= 60)].copy()
B["minTV"] = B[["TRAIN_a", "VALID_a"]].min(axis=1)
print("positive TRAIN & VALID in a state:"); print(B.sort_values("minTV", ascending=False).head(25).to_string())
print(C[C.home == "graveyard"].sort_values("VALID_a", ascending=False).head(20).to_string())
print(out["fs"].round(3).to_string())
