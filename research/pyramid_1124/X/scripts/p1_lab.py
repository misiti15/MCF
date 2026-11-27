"""2-year lab (bt_lab1104: 95 live lab setups, uncapped signal chains, 5-min walk, production costs, open months only)."""
import pandas as pd, numpy as np
from pathlib import Path
X = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/"
P = Path("/home/user/MCF/research/history2y/data/bt_lab1104")
L = pd.concat([pd.read_parquet(p) for p in sorted(P.glob("sig_*.parquet"))], ignore_index=True)
assert not L.date.between("2024-11-01", "2025-02-28").any()
mins = lambda x: (x // 100) * 60 + x % 100
L["hold"] = mins(L.xtod) - mins(L.tod)
L["side_s"] = np.where(L.side == 1, "long", "short")
L["half"] = np.where(L.date < "2025-10-01", "FIT 24-10+25-03..09", "CHECK 25-10..26-11")
L["kind_s"] = L.kind.map({0: "flat", 1: "stop", 2: "target"})
print(len(L), L.setup.nunique(), L.date.min(), L.date.max())
def card(g):
    return pd.Series({"n": len(g), "setups": g.setup.nunique(), "avgR": g.r.mean(), "win": (g.r > 0).mean(),
                      "pct_target": (g.kind == 2).mean(), "pct_stop": (g.kind == 1).mean(), "pct_flat": (g.kind == 0).mean(),
                      "hold_med": g.hold.median(), "min_to_target_med": g.loc[g.kind == 2, "hold"].median(),
                      "min_to_stop_med": g.loc[g.kind == 1, "hold"].median()})
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(L.groupby(["half", "side_s"]).apply(card).round(3))
for geom in ("t1s1", "t05s1", "t05s05"):
    print(geom); print(L[L.geom == geom].groupby(["half", "side_s"]).apply(card).round(3))
ps = L.groupby(["half", "side_s", "setup"]).r.agg(["size", "mean"]).reset_index()
ps = ps[ps["size"] >= 50]
print(ps.groupby(["half", "side_s"])["mean"].agg(setups="size", med="median", share_pos=lambda x: (x > 0).mean()).round(3))
# daily per-trade mean R by side (each setup equal weight within a day: mean of per-setup day means)
sd = L.groupby(["date", "side_s", "setup"]).r.mean().groupby(["date", "side_s"]).mean().unstack()
sd.to_csv(X + "lab_side_daily.csv")
for h, g in sd.groupby(np.where(sd.index < "2025-10-01", "FIT", "CHECK")):
    print(h, "days", len(g), "corr long/short daily (setup-eq-wt mean R)", round(g.corr().iloc[0, 1], 3))
