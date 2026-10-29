"""Screen swarm1017 arena results (stored, train+valid) against BAR90. Educational only - not financial advice."""
import numpy as np, pandas as pd, sys
BARS = {"arena-am-long": 4.62, "arena-am-short": 4.62, "arena-mid-long": 4.73, "arena-mid-short": 4.85,
        "arena-pm-both": 4.93, "arena-index-etf": 5.00}
out = []
for a, bar in BARS.items():
    d = pd.read_csv(f"research/swarm1017/{a}/results.csv.gz", low_memory=False)
    if "all_t" in d:
        t = d.all_t; e = d.all_exp; n = d.all_n
        up = d.reg_up; dn = d.reg_down; nd = d.reg_n_down
    else:
        se_tr = (d.tr_exp / d.tr_t).abs(); se_va = (d.va_exp / d.va_t).abs()
        n = d.tr_n + d.va_n
        e = (d.tr_n * d.tr_exp + d.va_n * d.va_exp) / n
        se = np.sqrt((d.tr_n * se_tr) ** 2 + (d.va_n * se_va) ** 2) / n
        t = e / se
        up = (d.tr_n_up * d.tr_exp_up + d.va_n_up * d.va_exp_up) / (d.tr_n_up + d.va_n_up)
        dn = (d.tr_n_down * d.tr_exp_down + d.va_n_down * d.va_exp_down) / (d.tr_n_down + d.va_n_down)
        nd = d.tr_n_down + d.va_n_down
    m = (t >= 0.9 * bar) & (up > 0) & (dn > 0) & (nd >= 30) & (d.tr_exp > 0 if "tr_exp" in d else True) & (d.va_exp > 0)
    print(a, len(d), "max t (regime ok)", round(t[(up > 0) & (dn > 0) & (nd >= 30)].max(), 2), "bar90", round(0.9 * bar, 2), "pass", int(m.sum()))
    s = d[m].copy(); s["t_all_est"] = t[m]; s["arena"] = a; out.append(s)
o = pd.concat(out)
o.to_csv("research/bdi/bar90_1029/arena_bar90.csv", index=False)
print(o[["arena", "conds", "window", "geom", "t_all_est"] + [c for c in ["ex_best_day", "wf_share", "per_day", "near_miss"] if c in o]].sort_values("t_all_est", ascending=False).head(30).to_string())
