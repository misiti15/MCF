"""Reviewer re-check (live, k=0.25 profit lock): per-account red-day change and pooled dR without Testing F.
Usage: python review_live_recheck.py <scratch_dir>. Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import lock_mask
t = pd.read_parquet(f"{sys.argv[1]}/live_acct.parquet")
t["em"] = t.et.dt.hour * 60 + t.et.dt.minute + t.et.dt.second / 60
t["xm"] = t.xt.dt.hour * 60 + t.xt.dt.minute + t.xt.dt.second / 60
t = t.sort_values(["account", "date", "em"]).reset_index(drop=True)
day = t.groupby(["account", "date"]).r.sum()
sd = {}
for a, s in day.groupby(level=0):
    s = s.droplevel(0); e = s.expanding().std().shift(1); cnt = s.expanding().count().shift(1)
    for d in s.index: sd[(a, d)] = e[d] if cnt[d] >= 5 else np.nan
keep = np.ones(len(t), bool)
for (a, d), ix in t.groupby(["account", "date"]).indices.items():
    X = 0.25 * sd[(a, d)] if np.isfinite(sd[(a, d)]) else np.inf
    g = t.iloc[ix]; keep[ix] = lock_mask(g.em.to_numpy(), g.xm.to_numpy(), g.r.to_numpy(), X)
elig = pd.Series({k: np.isfinite(v) for k, v in sd.items()})
base = day[elig.reindex(day.index).values]
new = t[keep].groupby(["account", "date"]).r.sum().reindex(base.index, fill_value=0.0)
r = pd.DataFrame({"days": base.groupby(level=0).size(), "red_base": (base <= 0).groupby(level=0).sum(),
                  "red_lock": (new <= 0).groupby(level=0).sum(), "dR": (new - base).groupby(level=0).sum().round(1)})
print(r.to_string()); print("total", r.sum().to_dict())
x = r.drop(index="testingf"); print("without testingf: dR", round(x.dR.sum(), 1), "red", int(x.red_base.sum()), "->", int(x.red_lock.sum()))
d = (new - base); print("best account-day:", d.idxmax(), round(d.max(), 1), "share of pooled dR", round(d.max() / d.sum(), 3))
