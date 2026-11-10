"""STOPW size-cut control (Builder 2026-11-09 ~20:50 ET, added AFTER the plan's score - reported as a post-hoc control,
no new configs, N stays 77). At equal $ risk a wider stop D' = max(D, X bp) means fewer shares; on a losing book that
alone shrinks average losses in R. CTRL = BASE x D / D' (same trade, old stop, the smaller size; net of costs, which
scale the same way). Stop-width effect = variant - CTRL. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/history2y")
from mcf.research import gates as G
import lib
HERE = Path(__file__).resolve().parent; SPLIT = pd.Timestamp("2025-09-30").date(); T90 = round(max(1.35, .9 * G.t_required(77)), 2)
X = pd.read_parquet(HERE / "stopw_trades.parquet"); X["date"] = pd.to_datetime(X.date).dt.date
D = lib.daily(); S = D[D.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
rows = []
for v, bp in (("W60", 60), ("W80", 80), ("W100", 100), ("W80S", 80)):
    sc = X.stop_bp / np.maximum(X.stop_bp, bp)
    ctrl = X.BASE * sc
    x = X.assign(r=X[v] - ctrl, sizecut=ctrl - X.BASE)
    s_ = G.summary(x); tr, va = G.summary(x[x.date <= SPLIT]), G.summary(x[x.date > SPLIT])
    sz = G.summary(x.assign(r=x.sizecut))
    ty = x.groupby(x.date.map(dtype)).r.sum()
    fam = x.groupby(["family", "side"]).r.mean()
    rows.append(dict(config=v, raw_delta=round((X[v] - X.BASE).mean(), 4), sizecut_part=sz["exp_r"], sizecut_t=sz.get("t"),
                     stop_effect=s_["exp_r"], stop_t=s_.get("t"), wo_best=s_.get("ex_best_day"), train=tr.get("exp_r"), train_t=tr.get("t"),
                     valid=va.get("exp_r"), valid_t=va.get("t"), up=round(ty.get("up", 0), 1), down=round(ty.get("down", 0), 1),
                     quiet=round(ty.get("quiet", 0), 1), fam_better=int((fam > 0).sum()), fam_worse=int((fam < 0).sum()),
                     worst_fam=round(fam.min(), 4), passes=bool((s_.get("t") or 0) >= T90 and (tr.get("exp_r") or -1) > 0 and (va.get("exp_r") or -1) > 0
                                                               and ty.get("up", 0) > 0 and ty.get("down", 0) > 0 and (fam > 0).sum() > (fam < 0).sum() and fam.min() >= -0.03)))
    fam.round(4).rename("stop_effect").reset_index().to_csv(HERE / f"stopw_sizectl_family_{v}.csv", index=False)
R = pd.DataFrame(rows); pd.set_option("display.width", 300); pd.set_option("display.max_columns", 30)
print(R.to_string(index=False)); print(f"\nraw_delta = sizecut_part + stop_effect; bar (N 77) {T90} applied to stop_effect. Post-hoc control.")
R.to_csv(HERE / "stopw_sizectl_results.csv", index=False); print("Educational only - not financial advice.")
