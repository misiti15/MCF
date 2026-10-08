"""AUDIT pass-2 scoring: gapdn plateau/baselines and hfl_pdl neighbours (production fills and costs).
Educational only - not financial advice."""
import json
import pickle
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "."); sys.path.insert(0, "research/oct7/audit")
from analyse import frame, stats, tday  # noqa: E402

C2 = frame(pickle.load(open("research/oct7/audit/data/cands2.pkl", "rb"))["cands"])
C = pickle.load(open("research/oct7/audit/data/C.pkl", "rb"))
res = {}
a = C[C.setup == "gapdn"].set_index(["symbol", "date"])
b = C2[C2.setup == "gd_g0.88_w1300-1430"].set_index(["symbol", "date"])
j = a.join(b, rsuffix="_2", how="outer")
res["reimpl_check"] = {"pass1_n": len(a), "reimpl_n": len(b), "both": int(j.pnl.notna().sum() - j.pnl_2.isna().sum()),
                       "max_abs_pnl_diff": float((j.pnl - j.pnl_2).abs().max())}
print(res["reimpl_check"])
for st in sorted(C2.setup.unique()):
    s = C2[C2.setup == st]
    r = {sp: stats(s[s.split == sp]) for sp in ("train", "valid")}
    for sp in ("train", "valid"):
        r[sp]["t_dailysumR"] = round(tday(s[s.split == sp].groupby("date").r.sum()), 2)
    res[st] = r
    print(f"{st:28s}", " | ".join(f"{sp}: n {r[sp]['n']} R {r[sp]['r_pt']:+.3f} $pt {r[sp]['usd_pt']:+.2f} $ {r[sp]['usd_total']:+.0f} "
                                     f"t$ {r[sp]['t_day_usd']:.2f} tmR {r[sp]['t_day_meanR']:.2f} exb {r[sp]['ex_best_usd']:+.0f} best {r[sp]['best_share']}"
                                     for sp in ("train", "valid")))
# same-time control: gapdn trade R minus the mean R of ALL names shorted at the same entry minute that day
ctrl = C2[C2.setup == "ctrl_all_first_bar"].groupby(["date", "entry_time"]).r.mean().rename("ctrl_r")
for nm, s in (("gapdn", C[C.setup == "gapdn"]), ("gapdn_rsi3", C[C.setup == "gapdn_rsi3"])):
    x = s.join(ctrl, on=["date", "entry_time"])
    out = {}
    for sp in ("train", "valid"):
        y = x[(x.split == sp) & x.ctrl_r.notna()]
        e = (y.r - y.ctrl_r)
        out[sp] = {"n_matched": len(y), "of": int((x.split == sp).sum()), "edge_vs_same_time_all_names_R": round(e.mean(), 4),
                   "t_day": round(tday(e.groupby(y.date).mean()), 2)}
    res[f"{nm}_same_time_edge"] = out
    print(nm, "same-time edge", out)
json.dump(res, open("research/oct7/audit/score2.json", "w"), indent=1, default=str)
# all-names (incl. symbol-days with missing 1-minute bars) version: same-time edge and increment over the
# plain gap-down 13:00 short (its failed P1-gap parent family)
G = C2[C2.setup == "gd_g0.88_w1300-1430"]
x = G.join(ctrl, on=["date", "entry_time"])
par = C2[C2.setup == "ctrl_gd_g0.88_first_bar"]
for sp in ("train", "valid"):
    y = x[(x.split == sp) & x.ctrl_r.notna()]
    e = y.r - y.ctrl_r
    g, p = G[G.split == sp], par[par.split == sp]
    inc = g.groupby("date").r.mean() - p.groupby("date").r.mean()
    res[f"gapdn_allnames_{sp}"] = {"same_time_edge_R": round(e.mean(), 4), "same_time_t_day": round(tday(e.groupby(y.date).mean()), 2),
                                   "increment_vs_gapdown_13h_R_daymean": round(inc.mean(), 4), "increment_t_day": round(tday(inc), 2)}
    print(sp, res[f"gapdn_allnames_{sp}"])
s = C[C.setup == "gapdn"]
for sp in ("train", "valid"):
    p = par[par.split == sp]; g = s[s.split == sp]
    inc = g.groupby("date").r.mean() - p.groupby("date").r.mean().reindex(g.date.unique())
    print("390-bar subset increment", sp, round(inc.mean(), 4), round(tday(inc.dropna()), 2))
json.dump(res, open("research/oct7/audit/score2.json", "w"), indent=1, default=str)
