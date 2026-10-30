"""pdl1030/tape-flip scoring of the 16 pre-declared configs (PLAN.md). TRAIN+VALID only. Educational only - not financial advice."""
import os, sys, math
os.environ["OMP_NUM_THREADS"] = "1"
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research/bdi/top5_1028"), str(ROOT / "research/bdi/top5_1019"), str(ROOT / "research/bdi/gates1021/scripts")]
from scan_1019 import lib  # noqa
from mcf.research import gates  # noqa
D = Path(__file__).resolve().parent
T = pd.concat([pd.read_parquet(p) for p in sorted((D / "cache").glob("t_*.parquet"))], ignore_index=True)
T = T[T["r"].notna() | (T["leg"] == "Sb")]
d = pd.to_datetime(T["date"])
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not (((d >= "2026-04-01") & (d <= "2026-06-30")) | (d > "2026-09-15")).any()
T["split"] = np.where(d <= "2025-12-31", "train", "valid")
T["month"] = T["date"].astype(str).str[:7]
reg = lib.regimes()["regime"]
T["regime"] = T["date"].astype(str).map(lambda s: reg.get(s, reg.get(pd.Timestamp(s).date(), None)) if True else None)
SESS = T.loc[(T.setup == "p05") & (T.leg == "L"), "date"].nunique()
N_PRIOR, N_MINE = 121459, 16
N = N_PRIOR + 3 * N_MINE
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
PAR = {"train": -0.0677, "valid": -0.0675}


def stats(x, name, rule):
    x = x[x["r"].notna()]
    s = gates.summary(x[["date", "r"]])
    g = x.groupby("date")["r"].sum(); tot = g.sum()
    mon = x.groupby("month")["r"].mean()
    tr, va = x[x.split == "train"]["r"], x[x.split == "valid"]["r"]
    o = dict(id=name, rule=rule, n=s["n"], per_session=round(len(x) / SESS, 1), train_avg_r=round(tr.mean(), 4),
             valid_avg_r=round(va.mean(), 4), tv_avg_r=s["exp_r"], t_day=s["t"], wf_pct=round(100 * (mon > 0).mean(), 1),
             up_day_r=round(x[x.regime == "up"]["r"].mean(), 4), down_day_r=round(x[x.regime == "down"]["r"].mean(), 4),
             avg_r_wo_best_day=s["ex_best_day"], best_share=round(g.max() / tot, 3) if tot > 0 else None)
    o["passes_bar"] = bool(o["t_day"] is not None and o["t_day"] >= BAR and o["wf_pct"] >= 54 and o["train_avg_r"] > 0 and
                           o["valid_avg_r"] > 0 and o["train_avg_r"] > PAR["train"] and o["valid_avg_r"] > PAR["valid"] and
                           (o["per_session"] >= 25))
    return o


L = T[(T.setup == "p05") & (T.leg == "L")]; Sx = T[(T.setup == "p05") & (T.leg == "Sx")]; Sb = T[(T.setup == "p05") & (T.leg == "Sb")]
out = [stats(L, "parent-p05", "p05 parent (parity)"), stats(T[(T.setup == "p10") & (T.leg == "L")], "parent-p10", "p10 parent (parity)")]
TAPES = {"TA": ("spy_fo", 0.0, "SPY fromOpen"), "TB": ("spy_vd", 0.0, "SPY vs VWAP"), "TC": ("breadth", 0.5, "breadth vs 0.5")}
res = []
for tn, (col, thr, lab) in TAPES.items():
    up = lambda z: z[col] > thr
    dn = lambda z: z[col] < thr
    cfg = {"G": (L[up(L)], f"long if {lab} up, skip if down"),
           "Sx": (Sx[dn(Sx)], f"short at signal close if {lab} down"),
           "Sb": (Sb[dn(Sb)], f"short at first close back below PDL if {lab} down"),
           "F": (pd.concat([L[up(L)], Sx[dn(Sx)]]), f"long if {lab} up, short at signal close if down"),
           "B": (pd.concat([L[up(L)], Sb[dn(Sb)]]), f"long if {lab} up, short on PDL re-break if down")}
    for k, (x, rule) in cfg.items():
        o = stats(x, f"{tn}-{k}", rule); o["_x"] = x; res.append(o)
flips = [o for o in res if o["id"].endswith(("-F", "-B"))]
best = max(flips, key=lambda o: o["train_avg_r"])
xk = best["_x"]; xk = xk[xk["cost_rt_R"] <= 0.10]
res.append(stats(xk, f"K({best['id']})", best["rule"] + " + skip if round-trip cost > 10% of R"))
for o in res:
    o.pop("_x", None)
R = pd.DataFrame(out + res)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 60)
print(f"sessions {SESS}  configs scored {N_MINE}  N {N}  bar {BAR:.3f}")
print(R.drop(columns=["rule"]).to_string(index=False))
R.to_csv(D / "results.csv", index=False)
# month curves for flips
for o in ["TB-F", "TA-F", "TC-F"]:
    pass
