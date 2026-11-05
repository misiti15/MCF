"""GATE1 case study: every live session 10-06..11-04 - point-in-time state at the checkpoints, R by account x side,
and R of trades entered after 10:00 split by whether the checkpoint state agreed with the side. 11-04 setup detail.
Usage: python case.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
S = Path(sys.argv[1])
SN = {1: "UP", -1: "DN", 0: "mx"}
st = pd.read_parquet(S / "state.parquet"); st["date"] = st.date.astype(str)
st = st[st.date >= "2026-10-06"]
CP = [600, 630, 660, 690, 720, 750, 780, 840]
lab = lambda T: f"{T//60}:{T%60:02d}"
rows = []
for d, g in st.groupby("date"):
    g = g.set_index("T")
    r = dict(date=d, gap=round(100 * g.gap.iloc[0], 2), oc=round(100 * g.oc.iloc[0], 2), dtype=g.dtype.iloc[0])
    for T in CP:
        x = g.loc[T]
        r[lab(T)] = f'{SN[x.st]} {100*x.fo:+.2f}/{100*x.qqq_fo:+.2f}/{100*x.iwm_fo:+.2f} b{x.breadth_open:.2f}{" v+" if x.vw > 0 else " v-"}'
    rows.append(r)
D = pd.DataFrame(rows)
T = pd.read_parquet(S / "trades.parquet"); T = T[T.w == "LIVE"].copy()
T["sd"] = np.where(T.side > 0, "L", "S")
by = T.pivot_table(index="date", columns=["acct", "sd"], values="r", aggfunc="sum").round(1)
AB = {"primary": "P", "testing": "T1", "testing2": "T2", "graveyard": "GY", "gen": "GEN"}
by.columns = [f"{AB[a]}_{s}" for a, s in by.columns]
af = T[T.m >= 600].copy(); af["agree"] = np.sign(af.side) * af.st
ag = af.groupby(["date", "agree"]).r.agg(["size", "sum"]).unstack().round(1)
ag.columns = [f"{'with' if a == 1 else ('against' if a == -1 else 'mixed')}_{c}" for c, a in ag.columns]
out = D.merge(by, left_on="date", right_index=True, how="left").merge(ag, left_on="date", right_index=True, how="left")
out.to_csv(HERE / "live_sessions.csv", index=False)
pd.set_option("display.width", 400); pd.set_option("display.max_columns", 50)
print(D.to_string(index=False))
print(out[["date", "dtype"] + list(by.columns)].to_string(index=False))
print(out[["date", "dtype"] + list(ag.columns)].to_string(index=False))
tot = af.groupby("agree").r.agg(["size", "mean", "sum"]); print(tot)
# winning setup-days (>= +2R on the day): how much of their R came from entries whose checkpoint state agreed with the side
sdR = T.groupby(["date", "acct", "setup"]).r.sum().rename("dayR")
W = T.merge(sdR.reset_index(), on=["date", "acct", "setup"])
W["agree"] = np.where(W.m < 600, 9, np.sign(W.side) * W.st.fillna(0))
for lbl, msk in [("winning setup-days (>= +2R)", W.dayR >= 2), ("losing setup-days (<= -2R)", W.dayR <= -2)]:
    q = W[msk].groupby("agree").r.agg(["size", "sum"]).round(1); q.index = q.index.map({9: "before 10:00", 1: "state with side", 0: "MIXED", -1: "state against side"})
    print(lbl, msk.sum()); print(q); q.to_csv(HERE / f"live_{'win' if 'winning' in lbl else 'lose'}_setupdays_by_state.csv")
# 11-04 detail
x = T[T.date == "2026-11-04"]
s = x.groupby(["acct", "setup"]).agg(n=("r", "size"), R=("r", "sum"), side=("side", "first"), first=("m", "min"), last=("m", "max")).reset_index()
s["first"] = s["first"].map(lab); s["last"] = s["last"].map(lab)
s = s.sort_values("R", ascending=False); s.to_csv(HERE / "s1104_setups.csv", index=False)
print(s.head(20).to_string(index=False)); print(s.tail(10).to_string(index=False))
# 11-04 R by entry half-hour and side
x = x.assign(hh=(x.m // 30) * 30)
h = x.pivot_table(index="hh", columns="sd", values="r", aggfunc=["size", "sum"]).round(1); h.index = h.index.map(lab)
print(h.to_string()); h.to_csv(HERE / "s1104_by_halfhour.csv")
