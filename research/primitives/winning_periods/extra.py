"""Follow-ups from analyse.py: (a) per-setup concurrency caps (re-allocation, train -> valid, day-clustered);
(b) does a green morning predict the afternoon? (c) concentration of the winning days; (d) what the big days had.
Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd

OUT = "research/primitives/winning_periods/"
tr = pd.read_csv(OUT + "trades_with_features.csv")
mark = np.load(OUT + "minute_marks.npy").astype(float)
tr0 = pd.read_csv(OUT + "trades_enriched.csv")
assert len(tr0) == len(tr)
tr["date"] = pd.to_datetime(tr["date"]).dt.date
VALID0 = pd.Timestamp("2026-08-26").date()
res = {}


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 1 and x.std(ddof=1) > 0 else float("nan")


# (a) caps: re-run the allocation with a lower per-setup cap (entry order = engine order: entry_time, symbol)
def capped(df, N, only=None):
    keep = np.ones(len(df), bool)
    for d, g in df.groupby("date"):
        g = g.sort_values(["m0", "symbol"])
        open_ = []
        for i, r in g.iterrows():
            open_ = [(j, s, m1) for (j, s, m1) in open_ if m1 > r.m0]
            if (only is None or r.strategy in only) and sum(s == r.strategy for _, s, _ in open_) >= N:
                keep[df.index.get_loc(i)] = False
                continue
            open_.append((i, r.strategy, r.m1))
    return keep


rows = []
days = sorted(tr.date.unique())
base = tr.groupby("date").pnl.sum()
for only in (None, ("heat_fade_short",), ("heat_fade_long",), ("exhaustion_short",), ("orb20_a",)):
    for N in (3, 5, 8, 11, 15, 20, 30):
        k = capped(tr, N, only)
        new = tr[k].groupby("date").pnl.sum().reindex(days, fill_value=0)
        diff = (new - base.reindex(days)).to_numpy()
        isv = np.array([d >= VALID0 for d in days])
        rem = tr[~k]
        rows.append(dict(rule=f"cap-{N}-{'all' if only is None else only[0]}", removed_train=int((~k & (tr.split == 'train')).sum()),
                         removed_valid=int((~k & (tr.split == 'valid')).sum()),
                         removed_exp_r_train=round(rem[rem.split == "train"].r_multiple.mean(), 3) if len(rem) else None,
                         removed_exp_r_valid=round(rem[rem.split == "valid"].r_multiple.mean(), 3) if (rem.split == "valid").any() else None,
                         train_gain=round(diff[~isv].sum(), 1), train_t=round(tstat(diff[~isv]), 2),
                         valid_gain=round(diff[isv].sum(), 1), valid_t=round(tstat(diff[isv]), 2),
                         valid_ex_best=round(diff[isv].sum() - diff[isv].max(), 1)))
caps = pd.DataFrame(rows)
caps.to_csv(OUT + "caps_grid.csv", index=False)
res["caps_tried"] = len(rows)

# (b) morning vs afternoon: P/L at 11:05 (heat_fade_long switch-on) vs P/L from 11:05 to close
path = {d: np.nansum(mark[tr.index[tr.date == d]], axis=0) for d in days}
k1105 = 95
mo = np.array([path[d][k1105] for d in days])
af = np.array([path[d][-1] - path[d][k1105] for d in days])
res["morning_vs_afternoon"] = dict(
    spearman=round(float(pd.Series(mo).corr(pd.Series(af), method="spearman")), 3),
    afternoon_mean_when_morning_green=round(float(af[mo > 0].mean()), 1), n_green_mornings=int((mo > 0).sum()),
    afternoon_mean_when_morning_red=round(float(af[mo <= 0].mean()), 1), n_red_mornings=int((mo <= 0).sum()),
    afternoon_green_share_when_morning_green=round(float((af[mo > 0] > 0).mean()), 3),
    afternoon_green_share_when_morning_red=round(float((af[mo <= 0] > 0).mean()), 3))
# same split restricted to heat_fade_long P/L only (the 10-06 question)
hfl = tr[tr.strategy == "heat_fade_long"].groupby("date").pnl.sum().reindex(days, fill_value=0).to_numpy()
res["hfl_vs_morning"] = dict(hfl_mean_when_morning_green=round(float(hfl[mo > 0].mean()), 1),
                             hfl_mean_when_morning_red=round(float(hfl[mo <= 0].mean()), 1),
                             hfl_t_when_morning_green=round(tstat(hfl[mo > 0]), 2))
for sp, m in (("train", np.array([d < VALID0 for d in days])), ("valid", np.array([d >= VALID0 for d in days]))):
    res["hfl_vs_morning"][sp] = dict(green=round(float(hfl[m & (mo > 0)].mean()), 1), n_green=int((m & (mo > 0)).sum()),
                                     red=round(float(hfl[m & (mo <= 0)].mean()), 1), n_red=int((m & (mo <= 0)).sum()))

# (c) concentration
dsum = base.sort_values(ascending=False)
res["concentration"] = dict(total=round(float(dsum.sum()), 1), top3_days=[str(x) for x in dsum.index[:3]],
                            top3_sum=round(float(dsum.iloc[:3].sum()), 1),
                            total_ex_top3=round(float(dsum.iloc[3:].sum()), 1),
                            train_ex_top3=round(float(dsum[[d < VALID0 for d in dsum.index]].iloc[3:].sum()), 1))
# (d) daily P/L vs trades per day and market move
day = tr.groupby("date").agg(pnl=("pnl", "sum"), n=("pnl", "size"))
mk = tr.groupby("date").mkt_fromopen.median()
day["mkt_med_fromopen_at_entries"] = mk
day["abs_mkt"] = day.mkt_med_fromopen_at_entries.abs()
res["day_drivers"] = dict(spearman_pnl_vs_ntrades=round(float(day.pnl.corr(day.n, method="spearman")), 3),
                          spearman_pnl_vs_abs_mkt=round(float(day.pnl.corr(day.abs_mkt, method="spearman")), 3),
                          top_quartile_n_days_mean_pnl=round(float(day[day.n >= day.n.quantile(.75)].pnl.mean()), 1),
                          other_days_mean_pnl=round(float(day[day.n < day.n.quantile(.75)].pnl.mean()), 1))
by = tr[tr.date.astype(str).isin(res["concentration"]["top3_days"])].groupby("strategy").agg(n=("pnl", "size"), pnl=("pnl", "sum"),
                                                                                             exp_r=("r_multiple", "mean"))
res["top3_by_setup"] = by.round(3).reset_index().to_dict("records")
json.dump(res, open(OUT + "results_extra.json", "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
pd.set_option("display.width", 250)
print(caps.to_string())
