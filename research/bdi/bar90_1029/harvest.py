"""Harvest stored results rows from every research results CSV whose day-clustered t >= 1.35 (the BAR90 floor).

Educational only - not financial advice. Read-only over research/; writes harvest_raw.csv here.
"""
import csv, glob, math, os, re, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SKIP = re.compile(r"(trades|per_trade|combined|autopsy|losers|live_|days\.csv|regime_days|ranking|week_features|"
                  r"regime_class|ic_summary|gross|lift_summary|tod_by|ingredients|coverage|skipped|bar90_1029)")
T_PREF = ["t_tv", "t_all", "t_day", "t", "tday", "t_trval"]
EXP_PREF = ["exp_tv", "exp_all", "avgR_tv", "exp_r", "exp", "avg_r", "avgR", "exp_2y", "mean_r", "avg_r_2y", "exp_r_all"]
ID_PREF = ["id", "setup", "config", "cfg", "variant", "name", "label", "key", "row", "rule", "candidate"]
out = []
for f in sorted(glob.glob(os.path.join(ROOT, "research", "**", "*.csv"), recursive=True)):
    rel = os.path.relpath(f, ROOT)
    if SKIP.search(rel):
        continue
    try:
        df = pd.read_csv(f, low_memory=False)
    except Exception:
        continue
    if len(df) == 0 or len(df) > 2_000_000:
        continue
    cols = {c.lower(): c for c in df.columns}
    tc = next((cols[c.lower()] for c in T_PREF if c.lower() in cols), None)
    if tc is None:
        continue
    ec = next((cols[c.lower()] for c in EXP_PREF if c.lower() in cols), None)
    t = pd.to_numeric(df[tc], errors="coerce")
    m = t >= 1.35
    if ec is not None:
        m &= pd.to_numeric(df[ec], errors="coerce") > 0
    sub = df[m]
    if not len(sub):
        continue
    idcols = [cols[c] for c in ID_PREF if c in cols][:3]
    for _, r in sub.iterrows():
        rec = {"file": rel, "t_col": tc, "t": r[tc], "exp_col": ec, "exp": r[ec] if ec else None,
               "id": " | ".join(str(r[c]) for c in idcols)}
        for k in ["n", "n_all", "n_tv", "trades", "per_day", "up_exp", "down_exp", "wf_share_pos", "wf_share",
                  "ex_best_day", "t_required", "t_req", "t_bar", "t_bar_lineage", "tries", "lineage_n", "verdict"]:
            if k in cols:
                rec[k] = r[cols[k]]
        out.append(rec)
pd.DataFrame(out).to_csv(os.path.join(os.path.dirname(__file__), "harvest_raw.csv"), index=False)
print(len(out))
print(pd.DataFrame(out).groupby("file").size().sort_values(ascending=False).to_string())
