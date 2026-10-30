"""pdl1030/entry-confirm: score the pre-declared configs on TRAIN and VALID (no HOLD rows exist in the inputs).
Educational only - not financial advice."""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(Path("/home/user/MCF/research/history2y")), "/home/user/MCF"]
import lib  # noqa
from mcf.research import gates  # noqa
N_PRIOR, K = 121459, int(sys.argv[1]) if len(sys.argv) > 1 else 18
N = N_PRIOR + 3 * K
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
SESS = 348
T = pd.concat([pd.read_parquet(p) for p in sorted(HERE.glob("tr*_*.parquet"))], ignore_index=True)
d = pd.to_datetime(T["date"])
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any()
assert not (((d >= "2026-04-01") & (d <= "2026-06-30")) | (d >= "2026-09-16")).any()
T["split"] = np.where(d <= "2025-12-31", "train", "valid")
reg = lib.regimes()["regime"]; reg.index = pd.to_datetime(reg.index).strftime("%Y-%m-%d")
T["regime"] = T["date"].astype(str).map(reg)
T["month"] = d.dt.strftime("%Y-%m")
print("sessions", T["date"].nunique())
rows = []
for v, V in T.groupby("var", observed=True):
    s, a, b = gates.summary(V[["date", "r"]]), gates.summary(V[V.split == "train"][["date", "r"]]), gates.summary(V[V.split == "valid"][["date", "r"]])
    g = V.groupby("date")["r"].sum()
    mon = V.groupby("month")["r"].sum()
    wf = gates.walk_forward(V[["date", "r"]])
    rows.append(dict(var=v, n=s["n"], per_sess=round(s["n"] / SESS, 1), exp_tv=s["exp_r"], t_tv=s["t"], exp_tr=a["exp_r"], t_tr=a["t"],
                     exp_va=b["exp_r"], t_va=b["t"], up=round(V[V.regime == "up"]["r"].mean(), 4),
                     down=round(V[V.regime == "down"]["r"].mean(), 4), ex_best=s["ex_best_day"],
                     best_share=round(g.max() / g.sum(), 3) if g.sum() > 0 else np.nan,
                     mon_pos=round(float((mon > 0).mean()), 3), wf_gates=wf["share_positive"],
                     win=s["win_rate"], lim_share=round(float(V["lim"].mean()), 3)))
R = pd.DataFrame(rows).set_index("var")
p = R.loc["P"]
R["pass"] = (R.t_tv >= BAR) & (R.mon_pos >= 0.54) & (R.exp_tr > 0) & (R.exp_va > 0) & (R.exp_tr > p.exp_tr) & (R.exp_va > p.exp_va) \
    & ((R.per_sess >= 76.6) | (R.per_sess >= 25))
R.loc["P", "pass"] = False
pd.set_option("display.width", 250)
print(f"Educational only - not financial advice.\nconfigs scored {K}; N = {N}; BAR90 t >= {BAR:.3f}")
print(R.to_string())
R.to_csv(HERE / "results.csv")
