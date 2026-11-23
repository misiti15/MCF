"""hardstop_1123 step 4: score the 17 bench configurations against base (PLAN.md metrics) -> small CSVs.
Usage: python score.py WORKDIR.  Educational only - not financial advice."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(sys.argv[1])
sys.path.insert(0, str(W))
from sim import CFGS  # noqa: E402


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if d >= "2025-10-01":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"

LVL = {"A6": 6, "A8": 8, "A10": 10, "A12": 12, "N4": 4, "N6": 6, "N8": 8, "L2": 2, "L3": 3, "LF2": 2, "LF3": 3}
spy = pd.read_parquet(W / "spy.parquet", columns=["date"]).date.unique()
SESS = pd.Series(sorted(set(map(str, spy)) | set(pd.read_csv(W / "runs" / "base.csv.gz", usecols=["date"]).date.astype(str))))
SESS = SESS[SESS.map(period) != "none"]
NS = SESS.map(period).value_counts().to_dict()
NS["ALL"] = len(SESS)
R = {c: pd.read_csv(W / "runs" / f"{c}.csv.gz") for c in CFGS}
B = R["base"]


def daytab(x):
    d = x.groupby("date").agg(r=("r", "sum"), lots=("lots", "sum"), fire=("fire_m", "first"))
    return d.reindex(SESS.values).fillna({"r": 0.0, "lots": 0})


bd = daytab(B)
bd["per"] = bd.index.map(period)
rows, setup_rows, boot_rows = [], [], []
rng = np.random.default_rng(20261123)
bar = max(1.5, math.sqrt(2 * math.log(len(CFGS) - 1)))
for c in CFGS:
    if c == "base":
        continue
    cd = daytab(R[c])
    dr = cd.r - bd.r
    fired = cd.fire.notna() | (cd.lots != bd.lots) | (dr.abs() > 1e-9)
    for per in ("FIT", "T2", "CHECK", "ALL"):
        m = (bd.per == per) if per != "ALL" else np.ones(len(bd), bool)
        b, x, d, f = bd.r[m], cd.r[m], dr[m], fired[m]
        n = int(m.sum())
        lvl = LVL.get(c)
        bad = f & (b <= -lvl) if lvl else f & (b < 0)
        rec = f & ~bad
        t = d.mean() / (d.std(ddof=1) / math.sqrt(n)) if d.std() > 0 else float("nan")
        rows.append(dict(cfg=c, period=per, sessions=n, fire_days=int(f.sum()), fires_per_yr=round(f.sum() / n * 252, 1),
                         base_R=round(b.sum(), 2), cfg_R=round(x.sum(), 2), dR=round(d.sum(), 2),
                         dR_per_yr=round(d.sum() / n * 252, 2),
                         saved_on_bad_days=round(d[bad].sum(), 2), n_bad=int(bad.sum()),
                         lost_on_recovered_days=round(d[rec].sum(), 2), n_rec=int(rec.sum()),
                         worst_base=round(b.min(), 2), worst_cfg=round(x.min(), 2),
                         days_le_m6_base=int((b <= -6).sum()), sum_le_m6_base=round(b[b <= -6].sum(), 2),
                         days_le_m6_cfg=int((x <= -6).sum()), sum_le_m6_cfg=round(x[x <= -6].sum(), 2),
                         days_better=int((d > 1e-9).sum()), days_worse=int((d < -1e-9).sum()),
                         t_day=round(t, 2), lots_base=int(bd.lots[m].sum()), lots_cfg=int(cd.lots[m].sum()),
                         base_avgR_lot=round(b.sum() / max(bd.lots[m].sum(), 1), 3),
                         dR_per_lot_removed=round(d.sum() / max(bd.lots[m].sum() - cd.lots[m].sum(), 1), 3)))
    # per setup
    ps = R[c].merge(B, on=["date", "setup"], suffixes=("", "_b"))
    ps["d"] = ps.r - ps.r_b
    ps["per"] = ps.date.map(period)
    for (per, s), g in ps.groupby(["per", "setup"]):
        setup_rows.append(dict(cfg=c, period=per, setup=s, base_R=round(g.r_b.sum(), 2), cfg_R=round(g.r.sum(), 2),
                               dR=round(g.d.sum(), 2), days_better=int((g.d > 1e-9).sum()), days_worse=int((g.d < -1e-9).sum()),
                               better_sum=round(g.d[g.d > 0].sum(), 2), worse_sum=round(g.d[g.d < 0].sum(), 2)))
    # bootstrap by day, pooled sessions
    dv, bv = dr.values, bd.r.values
    tail = bv <= -6
    idx = rng.integers(0, len(dv), size=(10000, len(dv)))
    per_yr = dv[idx].mean(1) * 252
    tail_yr = (dv * tail)[idx].mean(1) * 252
    nontail_yr = (dv * ~tail)[idx].mean(1) * 252
    worst = np.minimum.reduce([(bv + dv)[idx].min(1)]) - bv[idx].min(1)
    boot_rows.append(dict(cfg=c, dR_yr_p05=round(np.percentile(per_yr, 5), 1), dR_yr_p50=round(np.percentile(per_yr, 50), 1),
                          dR_yr_p95=round(np.percentile(per_yr, 95), 1), P_dR_pos=round((per_yr > 0).mean(), 3),
                          tail_yr_p05=round(np.percentile(tail_yr, 5), 1), tail_yr_p50=round(np.percentile(tail_yr, 50), 1),
                          tail_yr_p95=round(np.percentile(tail_yr, 95), 1),
                          nontail_yr_p50=round(np.percentile(nontail_yr, 50), 1),
                          worstday_gain_p05=round(np.percentile(worst, 5), 2), worstday_gain_p50=round(np.percentile(worst, 50), 2)))
S = pd.DataFrame(rows)
# exposure control: a blocked lot of a book that loses base_avgR_lot per lot "saves" that much by itself; dR_neutral
# removes it (book at zero expectancy), dR_book_p10 prices it for a book earning +0.10R per lot (approximation: blocked
# lots only, flattened lots' remainders not adjusted)
S["lots_removed"] = S.lots_base - S.lots_cfg
S["dR_neutral"] = (S.dR + S.base_avgR_lot * S.lots_removed).round(1)
S["dR_book_p10"] = (S.dR + (S.base_avgR_lot - 0.10) * S.lots_removed).round(1)
S["ratio_saved_lost"] = (S.saved_on_bad_days / (-S.lost_on_recovered_days)).round(2)
S.to_csv(W / "bench_results.csv", index=False)
pd.DataFrame(setup_rows).to_csv(W / "bench_per_setup.csv", index=False)
BT = pd.DataFrame(boot_rows)
BT.to_csv(W / "bench_bootstrap.csv", index=False)
# verdict per PLAN
ver = []
for c in [k for k in CFGS if k != "base"]:
    s = S[S.cfg == c].set_index("period")
    wb = all(s.at[p, "worst_cfg"] > s.at[p, "worst_base"] for p in ("FIT", "T2", "CHECK"))
    pos = sum(s.at[p, "dR"] >= 0 for p in ("FIT", "T2", "CHECK"))
    t = s.at["ALL", "t_day"]
    cheap = all(s.at[p, "dR_per_yr"] >= -1 for p in ("FIT", "T2", "CHECK"))
    v = "Yes" if (wb and pos >= 2 and t >= bar) else ("Optional" if (wb and cheap) else "No")
    ver.append(dict(cfg=c, worst_better_all3=wb, periods_dR_pos=pos, t_all=t, bar=round(bar, 2), verdict=v))
V = pd.DataFrame(ver)
V.to_csv(W / "bench_verdicts.csv", index=False)
# base per-setup totals (reproduction check) and worst base days
B["per"] = B.date.map(period)
print(B.groupby(["per", "setup"]).agg(r=("r", "sum"), lots=("lots", "sum")).round(2).to_string())
print("sessions", NS)
pd.set_option("display.width", 250)
print(S[S.period == "ALL"].drop(columns="period").to_string(index=False))
for p in ("FIT", "T2", "CHECK"):
    print("==", p)
    print(S[S.period == p][["cfg", "fire_days", "fires_per_yr", "dR", "saved_on_bad_days", "lost_on_recovered_days",
                            "worst_base", "worst_cfg", "days_le_m6_cfg", "t_day"]].to_string(index=False))
print(BT.to_string(index=False))
print(V.to_string(index=False))
w = bd.sort_values("r").head(15).copy()
for c in ("A8", "A10", "N6", "LF2", "LF3", "S1_0"):
    w[c] = daytab(R[c]).r.reindex(w.index).round(2)
w.round(2).to_csv(W / "bench_worst_days.csv")
print(w.round(2).to_string())
