import sys, glob, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/"
sys.path.insert(0, S + "cp1/research/forward/compass_gate"); sys.path.insert(0, S + "cp1")
import shadow as CG
bf = pd.concat([pd.read_parquet(p) for p in glob.glob(S + "crd/cmp_*.parquet")])
rec = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(S + "cmp/2026-*.csv"))])
rec = rec[~rec.date.isin(["2026-11-16", "2026-11-17"])]
rec = rec[rec.groupby("date").T.transform("size") >= 20]
c = pd.concat([bf[~bf.date.isin(rec.date)], rec])[["date", "T", "w60", "c30", "gate1_state", "checkpoint", "spy_fo"]]
c["m"] = c["T"].str[:2].astype(int) * 60 + c["T"].str[3:].astype(int)
c = c.sort_values(["date", "m"]); c.to_parquet(S + "crd/compass_marks.parquet")
print(c.date.nunique(), "sessions with marks;", c.groupby("date").size().min(), "min marks")
t = pd.read_parquet(S + "crd/live_feat.parquet")
t["beta"] = t.symbol.map(CG.beta_sign); t["expo"] = t.side * t.beta
CONF = {"UP-confirmed": 1, "DOWN-confirmed": -1}
cmp_state, after, g1 = [], [], []
by = {d: g for d, g in c.groupby("date")}
for d, em in zip(t.date, t.em):
    g = by.get(d)
    if g is None: cmp_state.append(np.nan); after.append(np.nan); g1.append(None); continue
    x = g[g.m + 2 <= em]
    if not len(x): cmp_state.append(0); after.append(0); g1.append(None); continue
    w = x.w60.map(CONF).fillna(0)
    cmp_state.append(int(w.iloc[-1])); after.append(int((w != 0).any())); g1.append(x.gate1_state.dropna().iloc[-1] if x.gate1_state.notna().any() else None)
t["cmp"] = cmp_state; t["cmp_after"] = after; t["gate1"] = g1
t.to_parquet(S + "crd/live_feat.parquet"); print(t.cmp.value_counts(dropna=False).to_dict(), (t.beta == 0).sum(), (t.beta == -1).sum())
