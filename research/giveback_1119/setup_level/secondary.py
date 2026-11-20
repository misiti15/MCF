"""Addendum A readouts. Educational only - not financial advice."""
import numpy as np, pandas as pd
from score import *
lab, live = features(load_lab()), features(load_live())
F = pd.read_csv(D / "fit_grid.csv"); cm = {f"{c[0]}{c[1] or ''}": c for c in CONFIGS}
el = F[(F.keep >= .7) & (F.top_keep >= .9) & (F.dropped > 0)]
fb = el.sort_values("excess", ascending=False).drop_duplicates("setup")
out = []
for a in fb.itertuples():
    for name, src in (("lab", lab), ("live", live)):
        x = src[(src.setup == a.setup) & (src.half == "check")].reset_index(drop=True)
        if len(x) < 5: continue
        m = drop_mask(x, cm[a.cfg]); rec = dict(setup=a.setup, family=fam(a.setup), src=name, cfg=a.cfg, fit_excess=a.excess, fit_t=a.t_ex, **score(x, m))
        rec["rand_pct"] = rand_pct(x, m, 2000) if m.any() else np.nan
        out.append(rec)
C = pd.DataFrame(out); C.to_csv(D / "fitbest_check.csv", index=False)
pd.set_option("display.width", 250)
print(C[["setup", "src", "cfg", "fit_excess", "fit_t", "n", "days", "dropped", "dR", "avg_before", "avg_after", "wo_before", "wo_after", "excess", "t_ex", "t_raw", "rand_pct", "best_day_share"]].round(3).to_string())
# live descriptive (all sessions)
P = pd.read_parquet(LIVE, columns=["strategy", "symbol", "date", "m_in", "account", "id", "mfe_b", "exit_reason"])
P = P.sort_values(["account", "id"]).drop_duplicates(["strategy", "symbol", "date", "m_in"])
L = live.merge(P.assign(tod=(P.m_in // 60) * 100 + P.m_in % 60, date=P.date.astype(str)).rename(columns={"strategy": "setup"})[["setup", "symbol", "date", "tod", "mfe_b", "exit_reason"]],
               on=["setup", "symbol", "date", "tod"], how="left")
rows = []
for s, g in L.groupby("setup"):
    def cell(m):
        return (m.mean(), g.r[m].mean() if m.any() else np.nan, g.r[m].sum())
    rec = dict(setup=s, n=len(g), sessions=g.date.nunique(), avg=g.r.mean(), totR=g.r.sum())
    for k, m in (("crowd3", g.crowd >= 3), ("late14", g.tod >= 1400), ("refire", g.nth >= 2), ("refire_after_loss", g.prior_loss)):
        sh, av, tot = cell(m.values); rec.update({f"{k}_share": sh, f"{k}_avg": av, f"{k}_R": tot})
    r8 = g.mfe_b >= 0.8; rec["reach08"] = r8.mean(); rec["stop_after08"] = (g.exit_reason[r8] == "stop").mean() if r8.any() else np.nan
    rows.append(rec)
T = pd.DataFrame(rows).set_index("setup").loc[[s for s in SETUPS if s in set(L.setup)]]
T.to_csv(D / "live_causes.csv"); print(T.round(3).T.to_string())
