"""Part D scoring (pre-registered metrics, D_PREREG.md) from D_lots.parquet. Educational only - not financial advice."""
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W, OUT = Path(sys.argv[1]), Path(__file__).parent
L = pd.read_parquet(W / "D_lots.parquet")
L["r"] = L.r.fillna(0.0)
NCFG = L.cfg.nunique() - 1
BAR_STUDY = max(1.5, math.sqrt(2 * math.log(NCFG)))
BAR_LINEAGE = max(1.5, math.sqrt(2 * math.log(21 + 2 + NCFG)))
day = L.groupby(["cfg", "per", "date"]).r.sum().unstack("cfg").fillna(0.0)
base_lots = L[(L.cfg == "base") & (L.i >= 0)]
burst_days = set(base_lots[base_lots.is_burst].date)
bR = base_lots[base_lots.inburst].groupby("date").r.sum()
april = {d for d in burst_days if "2025-04-03" <= d <= "2025-04-11"}
losing_burst = {d for d in burst_days if bR.get(d, 0) < 0}
win_burst_other = {d for d in burst_days if d not in april and bR.get(d, 0) >= 0}


def wobd(x):
    return x.drop(x.idxmax()).sum() if len(x) > 1 else 0.0


rows = []
for c in [k for k in day.columns if k != "base"]:
    for per in ("FIT", "T2", "CHECK", "ALL"):
        d = day if per == "ALL" else day.xs(per, level="per", drop_level=False)
        b, x = d["base"], d[c]
        dd = (x - b)
        dates = d.index.get_level_values("date")
        n = len(dd)
        t = dd.mean() / (dd.std(ddof=1) / math.sqrt(n)) if n > 2 and dd.std(ddof=1) > 0 else float("nan")
        lots = L[(L.cfg == c) & (L.i >= 0) & ((L.per == per) | (per == "ALL"))]
        row = dict(cfg=c, per=per, R_base=b.sum(), R=x.sum(), dR=dd.sum(), lots=len(lots),
                   worst_base=b.min(), worst=x.min(), worst_cut=x.min() - b.min(),
                   d_le4_base=int((b <= -4).sum()), d_le4=int((x <= -4).sum()),
                   sum_le4_base=b[b <= -4].sum(), sum_le4=x[x <= -4].sum(),
                   days_better=int((dd > 1e-9).sum()), days_worse=int((dd < -1e-9).sum()),
                   wobd_base=wobd(b), wobd=wobd(x), t_dR=t,
                   dR_april=dd[dates.isin(april)].sum(), dR_losing_bursts=dd[dates.isin(losing_burst)].sum(),
                   dR_other_win_bursts=dd[dates.isin(win_burst_other)].sum(),
                   dR_nonburst=dd[~dates.isin(burst_days)].sum())
        rows.append(row)
R = pd.DataFrame(rows)
# ranking: worst-day cut per R given up (ALL periods); tail cut = worst-day improvement (positive = better)
A = R[R.per == "ALL"].copy()
A["tail_cut"] = A.worst_cut
A["R_given_up"] = -A.dR
A["cut_per_R"] = np.where(A.R_given_up > 0, A.tail_cut / A.R_given_up, np.inf)
fin = []
for c in A.cfg:
    f = R[(R.cfg == c) & (R.per == "FIT")].iloc[0]
    t2 = R[(R.cfg == c) & (R.per == "T2")].iloc[0]
    fin.append(bool(f.worst_cut > 0 and t2.worst_cut > 0 and f.dR >= -5 and t2.dR >= -5))
A["finalist"] = fin
A = A.sort_values(["cut_per_R"], ascending=False)
R.round(3).to_csv(OUT / "D_results.csv", index=False)
A.round(3).to_csv(OUT / "D_ranking.csv", index=False)
pd.set_option("display.width", 260)
cols = ["cfg", "per", "R_base", "R", "dR", "lots", "worst_base", "worst", "d_le4_base", "d_le4", "sum_le4_base", "sum_le4",
        "days_better", "days_worse", "wobd", "t_dR", "dR_april", "dR_losing_bursts", "dR_other_win_bursts", "dR_nonburst"]
for per in ("FIT", "T2", "CHECK", "ALL"):
    print("=====", per)
    print(R[R.per == per][cols].round(2).to_string(index=False))
print("bars: study N=%d -> %.2f; lineage N=%d -> %.2f" % (NCFG, BAR_STUDY, 21 + 2 + NCFG, BAR_LINEAGE))
print("burst days:", len(burst_days), "april:", sorted(april), "losing:", len(losing_burst), sorted(losing_burst))
print(A[["cfg", "R", "dR", "worst_base", "worst", "tail_cut", "cut_per_R", "d_le4_base", "d_le4", "sum_le4_base", "sum_le4", "finalist"]]
      .round(2).to_string(index=False))
# worst 8 base days and each config on them
wd = day.sum(level="date") if hasattr(day, "sum") and False else day.droplevel("per")
worst = wd["base"].nsmallest(10).index
wd.loc[worst].round(2).T.to_csv(OUT / "D_worst_days.csv")
print(wd.loc[worst].round(1).T.to_string())
