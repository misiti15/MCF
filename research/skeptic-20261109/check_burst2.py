"""Skeptic spot-check of BURST2 decision.csv (branch origin/claude/preval-1107, research/bdi/burst2).
Usage (from the MCF repo):  git show origin/claude/preval-1107:research/bdi/burst2/decision.csv > dec.csv; python check_burst2.py dec.csv
Shows: raw VALID t vs excess t (volume cut vs real timing) and Primary concentration on the motivating days 11-05/11-06.
Educational only - not financial advice."""
import sys, pandas as pd
d = pd.read_csv(sys.argv[1])
d["P_1105_1106"] = d.d1105 + d.d1106
d["share_motivating_days"] = d.P_1105_1106 / d.P_d
d["best_day_share"] = d[["d1104", "d1105", "d1106"]].max(axis=1) / d.P_d
cols = ["config", "vs", "va_t", "va_xt", "live_d", "live_t", "P_d", "P_1105_1106", "share_motivating_days", "best_day_share"]
print(d[cols].round(2).to_string(index=False))
print("bar(N=29) =", round((2 * __import__("math").log(29)) ** .5, 2), "; configs with VALID excess t >= bar:", int((d.va_xt >= 2.60).sum()))
