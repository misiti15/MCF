"""pdl1030/time-bucket scoring of the 18 pre-declared configs (PLAN.md). TRAIN+VALID only.
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
T = T[T["date"].astype(str) <= "2026-09-15"].reset_index(drop=True)
d = T["date"].astype(str)
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
T["month"] = d.str[:7]
T["split"] = np.where(d <= "2025-12-31", "train", "valid")
T = T.sort_values(["setup", "symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
NSESS = T["date"].nunique()
COUNT = 18
N = 121566 + 3 * COUNT
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
PAR = dict(train=-0.0677, valid=-0.0675)

def pick(setup, win):
    """first flagged bar per symbol-day inside the window (list of (lo, hi) tod ranges)."""
    t = T[T.setup == setup]
    w = np.zeros(len(t), bool)
    for lo, hi in win:
        w |= (t.tod.to_numpy() >= lo) & (t.tod.to_numpy() <= hi)
    t = t[w]
    return t[~t.duplicated(["symbol", "date"])]

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
                and st["avg_train"] > PAR["train"] and st["avg_valid"] > PAR["valid"] and st["per_session"] >= 25)

LIVE = [(950, 1500)]
print(f"sessions {NSESS}  N {N}  BAR {BAR:.3f}")
# parity (not counted: already scored by swarm15 / symbol-quality)
for nm, s, rc, c in (("p05 P", "p05", "r_P", None), ("p10 P", "p10", "r_P", None), ("p05 S3+c5 (Q08)", "p05", "r_S3", 0.05)):
    t = pick(s, LIVE)
    if c:
        t = t[t.cost_rt_R <= c]
    st = stats(t, rc); print("PARITY", nm, st["avg_train"], st["avg_valid"], st["avg_tv"], st["n_tv"], st["per_session"])
W_ALL, W_OPEN, W_10 = [(935, 1500)], [(935, 945)], [(1000, 1500)]
CFG = [
    ("T01", "p05", "r_P", None, W_ALL, "p05 P 09:35-15:00"),
    ("T02", "p05", "r_P", None, W_OPEN, "p05 P 09:35-09:45"),
    ("T03", "p05", "r_P", None, W_10, "p05 P 10:00-15:00"),
    ("T04", "p05", "r_P", None, [(1130, 1500)], "p05 P 11:30-15:00"),
    ("T05", "p05", "r_P", None, [(1300, 1500)], "p05 P 13:00-15:00"),
    ("T06", "p05", "r_S3", None, W_ALL, "p05 S3 09:35-15:00"),
    ("T07", "p05", "r_S3", 0.05, W_ALL, "p05 S3+c5 09:35-15:00"),
    ("T08", "p05", "r_S3", 0.05, W_OPEN, "p05 S3+c5 09:35-09:45"),
    ("T09", "p05", "r_S3", 0.05, [(935, 1030)], "p05 S3+c5 09:35-10:30"),
    ("T10", "p05", "r_S3", 0.05, W_10, "p05 S3+c5 10:00-15:00"),
    ("T11", "p05", "r_S3", 0.05, [(1030, 1500)], "p05 S3+c5 10:30-15:00"),
    ("T12", "p05", "r_S3", 0.05, [(1130, 1330)], "p05 S3+c5 11:30-13:30"),
    ("T13", "p05", "r_S3", 0.05, [(1300, 1500)], "p05 S3+c5 13:00-15:00"),
    ("T14", "p05", "r_S3", 0.05, [(935, 945), (1000, 1500)], "p05 S3+c5 09:35-09:45+10:00-15:00"),
    ("T15", "p05", "r_S3", 0.08, W_ALL, "p05 S3+c8 09:35-15:00"),
    ("T16", "p05", "r_S3", 0.08, W_10, "p05 S3+c8 10:00-15:00"),
    ("T17", "p10", "r_S3", 0.05, W_ALL, "p10 S3+c5 09:35-15:00"),
    ("T18", "p10", "r_S3", 0.05, W_10, "p10 S3+c5 10:00-15:00"),
]
assert len(CFG) == COUNT
rows = []
for id_, s, rc, c, win, rule in CFG:
    t = pick(s, win)
    if c is not None:
        t = t[t.cost_rt_R <= c]   # cost floor applied after the first-in-window pick (the module skips the name for the day)
    st = stats(t, rc); st.update(id=id_, rule=rule, passes=passes(st)); rows.append(st)
R = pd.DataFrame(rows)[["id", "rule", "avg_train", "avg_valid", "avg_tv", "t_tv", "n_tv", "per_session", "wf_pct", "up_day_r",
                        "down_day_r", "ex_best", "best_share", "passes"]]
R["bar_t"], R["N"] = round(BAR, 3), N
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(R.to_string(index=False))
R.to_csv(D / "results.csv", index=False)
