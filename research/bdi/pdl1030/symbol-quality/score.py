"""pdl1030/symbol-quality scoring of the 17 pre-declared configs (PLAN.md). TRAIN+VALID only.
Educational only - not financial advice."""
import os, sys, math
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates
D = Path(__file__).resolve().parent
T = pd.concat([pd.read_parquet(p) for p in sorted((D / "cache").glob("tr_*.parquet"))], ignore_index=True)
T = T[T["date"].astype(str) <= "2026-09-15"]
d = T["date"].astype(str)
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
T["month"] = d.str[:7]
T["split"] = np.where(d <= "2025-12-31", "train", "valid")
NSESS = T["date"].nunique()
COUNT = 17
N = 121512 + 3 * COUNT
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
PAR = dict(train=-0.0677, valid=-0.0675)

def stats(o, rcol):
    o = o[np.isfinite(o[rcol])].rename(columns={rcol: "r"})
    res = {}
    for sp in ("train", "valid"):
        s = gates.summary(o[o.split == sp][["date", "r"]])
        res[f"avg_{sp}"], res[f"n_{sp}"] = s["exp_r"], s["n"]
    s = gates.summary(o[["date", "r"]])
    g = o.groupby("date")["r"].sum()
    res.update(n_tv=s["n"], avg_tv=s["exp_r"], t_tv=s["t"], ex_best=s["ex_best_day"],
               best_share=round(float(g.max() / g.sum()), 3) if g.sum() > 0 else None,
               per_session=round(s["n"] / NSESS, 1))
    res["up_day_r"] = round(float(o[o.spy_day > 0].r.mean()), 4)
    res["down_day_r"] = round(float(o[o.spy_day < 0].r.mean()), 4)
    res["wf_pct"] = round(float((o.groupby("month")["r"].mean() > 0).mean() * 100), 1)
    return res

def passes(st):
    return bool(st["t_tv"] is not None and st["t_tv"] >= BAR and st["wf_pct"] >= 54 and st["avg_train"] > 0 and st["avg_valid"] > 0
                and st["avg_train"] > PAR["train"] and st["avg_valid"] > PAR["valid"] and (st["per_session"] >= 76.6 or st["per_session"] >= 25))

p05, p10 = T[T.setup == "p05"], T[T.setup == "p10"]
c5 = lambda t: t.cost_rt_R <= 0.05
print(f"sessions {NSESS}  N {N}  BAR {BAR:.3f}")
# parity (not counted: parents / swarm15 S3 rows already scored)
for nm, t, rc in (("p05 P", p05, "r_P"), ("p10 P", p10, "r_P"), ("p05 S3", p05, "r_S3")):
    st = stats(t, rc); print("PARITY", nm, st["avg_train"], st["avg_valid"], st["avg_tv"], st["n_tv"], st["per_session"])
CFG = [
    ("Q01", p05, "r_P", lambda t: t.vd >= 0.5, "p05 | vd>=+0.5%"),
    ("Q02", p05, "r_P", lambda t: t.rs >= 0.5, "p05 | rs vs SPY>=+0.5%"),
    ("Q03", p05, "r_P", lambda t: t.vr >= 1.5, "p05 | volumeRatio>=1.5"),
    ("Q04", p05, "r_P", lambda t: t.gap <= -1.5, "p05 | gap<=-1.5%"),
    ("Q05", p05, "r_S3", lambda t: t.vd >= 0.5, "p05 S3 | vd>=+0.5%"),
    ("Q06", p05, "r_S3", lambda t: t.rs >= 0.5, "p05 S3 | rs>=+0.5%"),
    ("Q07", p05, "r_S3", lambda t: t.vr >= 1.5, "p05 S3 | volumeRatio>=1.5"),
    ("Q08", p05, "r_S3", lambda t: c5(t), "p05 S3 + cost5"),
    ("Q09", p05, "r_S3", lambda t: c5(t) & (t.vd >= 0.5), "p05 S3 + cost5 | vd>=+0.5%"),
    ("Q10", p05, "r_S3", lambda t: c5(t) & (t.vd >= 0), "p05 S3 + cost5 | vd>=0"),
    ("Q11", p05, "r_S3", lambda t: c5(t) & (t.rs >= 0.5), "p05 S3 + cost5 | rs>=+0.5%"),
    ("Q12", p05, "r_S3", lambda t: c5(t) & (t.vr >= 1.5), "p05 S3 + cost5 | volumeRatio>=1.5"),
    ("Q13", p05, "r_S3", lambda t: c5(t) & (t.gap <= -1.5), "p05 S3 + cost5 | gap<=-1.5%"),
    ("Q14", p05, "r_S3", lambda t: c5(t) & ((t.vd >= 0.5) | (t.rs >= 0.5)), "p05 S3 + cost5 | vd>=0.5 or rs>=0.5"),
    ("Q15", p05, "r_S3", lambda t: c5(t) & (t.vd >= 0.5) & (t.vr >= 1.5), "p05 S3 + cost5 | vd>=0.5 and vr>=1.5"),
    ("Q16", p10, "r_S3", lambda t: c5(t) & (t.vd >= 0.5), "p10 S3 + cost5 | vd>=+0.5%"),
    ("Q17", p10, "r_S3", lambda t: c5(t) & (t.vr >= 1.5), "p10 S3 + cost5 | volumeRatio>=1.5"),
]
assert len(CFG) == COUNT
rows = []
for id_, t, rc, f, rule in CFG:
    st = stats(t[f(t).to_numpy()], rc); st.update(id=id_, rule=rule, passes=passes(st)); rows.append(st)
R = pd.DataFrame(rows)[["id", "rule", "avg_train", "avg_valid", "avg_tv", "t_tv", "n_tv", "per_session", "wf_pct", "up_day_r",
                        "down_day_r", "ex_best", "best_share", "passes"]]
R["bar_t"], R["N"] = round(BAR, 3), N
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(R.to_string(index=False))
R.to_csv(D / "results.csv", index=False)
