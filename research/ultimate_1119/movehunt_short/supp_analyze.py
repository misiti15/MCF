"""Score supp_rows.parquet: every candidate set x geometry (D15/D30/D45/G5-G8), fit half only. Educational only - not financial advice."""
import os, numpy as np, pandas as pd

OUT = os.path.dirname(os.path.abspath(__file__)) + "/"
ROWS = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mhs_supp_rows.parquet"
S = pd.read_parquet(ROWS)
S["half"] = np.where(S.date < "2025-06-01", "A", "B")
spyday = S[S.tod == 1515].groupby("date").spyfo.first()
ndays = S.date.nunique()
TODB = [950, 1030, 1130, 1300, 1400, 1516]


def st(d, g):
    d = d[np.isfinite(d[g])]
    if len(d) == 0:
        return {}
    day = d.groupby("date")[g].agg(["sum", "count"])
    tot, best = day["sum"].sum(), day["sum"].max()
    bc = day.loc[day["sum"].idxmax(), "count"]
    se = day["sum"].std(ddof=1) * np.sqrt(len(day)) / len(d) if len(day) > 1 else np.nan
    up = d.date.map(spyday > 0).fillna(False).astype(bool)
    return dict(n=len(d), days=len(day), per_day=round(len(d) / 169, 2), avgR=round(d[g].mean(), 4), totR=round(tot, 1),
                t=round(d[g].mean() / se, 2) if se and se > 0 else np.nan,
                avgR_wo_best=round((tot - best) / (len(d) - bc), 4) if len(d) > bc else np.nan,
                best_share=round(best / tot, 2) if tot > 0 else np.nan,
                hit=round(d[g + "w"].mean(), 3) if g + "w" in d else np.nan,
                A=round(d[d.half == "A"][g].mean(), 4), B=round(d[d.half == "B"][g].mean(), 4),
                spy_up=round(d[up][g].mean(), 4), spy_dn=round(d[~up][g].mean(), 4), medR=round(d[g].median(), 4))


rows = []
ctrl = S[S["set"] == "CTRL random U1 bar"]
cb = {g: ctrl.groupby(pd.cut(ctrl.tod, TODB, right=False), observed=True)[g].mean() for g in ["D15", "D30", "D45", "G5", "G6", "G7", "G8"]}
for nm, d in S.groupby("set", sort=False):
    w = pd.cut(d.tod, TODB, right=False).value_counts(normalize=True)
    for g in ["D15", "D30", "D45", "G5", "G6", "G7", "G8"]:
        s = st(d, g)
        s.update(set=nm, geom=g, ctrl_tod_matched=round(float((w * cb[g].reindex(w.index)).sum()), 4))
        s["lift_vs_ctrl"] = round(s["avgR"] - s["ctrl_tod_matched"], 4)
        rows.append(s)
r = pd.DataFrame(rows)
cols = ["set", "geom", "n", "days", "per_day", "avgR", "ctrl_tod_matched", "lift_vs_ctrl", "medR", "hit", "totR", "t", "avgR_wo_best", "best_share", "A", "B", "spy_up", "spy_dn"]
r = r[cols]
r.to_csv(OUT + "supp_cells.csv", index=False)
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 30)
print(r.to_string(index=False))
print("configurations (set x geometry):", len(r))
# tod profile of the control drift (diagnostic)
print(ctrl.groupby(pd.cut(ctrl.tod, TODB, right=False), observed=True)[["D15", "D30", "D45", "G5", "a15_R0"]].mean().round(4))
