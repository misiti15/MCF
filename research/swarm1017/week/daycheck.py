"""Stability checks for the two leading reworks. Educational only - not financial advice."""
from load import *
R = pd.read_csv(S / "rework.csv")
for v in ["sim_base", "no_target_hold", "trail1R", "stop0.5"]: R[v + "_c"] = R[v] - R.cost
R["against"] = ((R.side == 1) & (R.spy_at_entry < -0.15)) | ((R.side == -1) & (R.spy_at_entry > 0.15))
print("against-SPY(0.15) trades: avg R after cost by day (n) vs with/flat")
print(R.groupby(["date", "against"]).sim_base_c.agg(["mean", "size"]).round(3).unstack().to_string())
print("days where skipping 'against' helps:", int((R[R.against].groupby("date").sim_base_c.sum() < 0).sum()), "of", R[R.against].date.nunique())
c = R[R.strategy.str.startswith("CWT14") | R.strategy.str.startswith("CWT12")]
print("\nCWT12/14 by day: base vs hold vs trail (avg R after cost)")
print(c.groupby("date")[["sim_base_c", "no_target_hold_c", "trail1R_c"]].mean().round(3).join(c.groupby("date").size().rename("n")).to_string())
print("\nstop0.5 vs base by day, all:"); print(R.groupby("date")[["sim_base_c", "stop0.5_c"]].mean().round(3).T.to_string())
