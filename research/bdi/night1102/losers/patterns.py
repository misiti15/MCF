"""Loser profile vs all trades, and entry-time pattern flags. Usage: python patterns.py <scratch>"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); t = pd.read_parquet(S / "feat.parquet")
t = t.sort_values("entry_time").reset_index(drop=True)
t["etod"] = t.entry_time.dt.strftime("%H%M")
# stacked lots: same account + date + side, entries within 10 minutes of each other -> cluster; order inside cluster
t["clu"] = 0; t["clu_pos"] = 0; t["clu_n"] = 1
for _, g in t.groupby(["account", "date", "side"]):
    tm = g.entry_time.values; cid = np.cumsum(np.r_[1, np.diff(tm).astype("timedelta64[s]").astype(float) > 600])
    t.loc[g.index, "clu"] = cid
t["clu_pos"] = t.groupby(["account", "date", "side", "clu"]).cumcount() + 1
t["clu_n"] = t.groupby(["account", "date", "side", "clu"]).R.transform("size")
# same-setup lots on one day in the same direction (same theme)
t["setup_day_pos"] = t.groupby(["account", "date", "strategy"]).cumcount() + 1
t["mkt_against"] = np.sign(t.spy_fo) == -t.side  # SPY from open is against the trade at entry
t["mkt_against_hs"] = np.sign(t.spy_rest) == -t.side  # hindsight: SPY moved against the trade after entry
t["chased"] = t.pos5_side > 0.9
t["late"] = t.etod >= "1430"
t["open10"] = t.etod < "0940"
t["inv"] = t.ty == "inverse"; t["lev"] = t.ty == "lev"; t["etf"] = t.ty == "etf"
t["inv_short"] = t.inv & (t.side < 0); t["inv_long"] = t.inv & (t.side > 0)
t["stacked"] = t.clu_pos > 3
t["fast_stop"] = (t.exit_reason == "stop") & (t.mins_to_exit <= 5)
t["no_mfe"] = t.mfe_r.fillna(t.sim_mfe) < 0.2
t.to_parquet(S / "feat2.parquet", index=False)
FL = ["inv_short", "inv_long", "lev", "etf", "stacked", "late", "open10", "chased", "mkt_against", "mkt_against_hs", "fast_stop", "no_mfe"]
rows = []
for scope, x in [("primary", t[t.account == "primary"]), ("all", t)]:
    L = x[x.loser]
    for f in FL:
        rows.append(dict(scope=scope, flag=f, share_losers=L[f].mean(), share_all=x[f].mean(), lift=L[f].mean() / max(x[f].mean(), 1e-9),
                         n_flag=int(x[f].sum()), avgR_flag=x.loc[x[f], "R"].mean(), avgR_rest=x.loc[~x[f], "R"].mean(),
                         sumR_flag=x.loc[x[f], "R"].sum()))
P = pd.DataFrame(rows); P.to_csv(Path(__file__).parent / "flag_profile.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 220); print(P.round(3).to_string())
L = t[t.loser]
print("\nloser describe (all accounts)"); print(L[["R", "mfe_r", "sim_mfe", "mins_to_exit", "pos5_side", "rng5_R", "vwap_dist_R", "spy_fo", "fill_vs_bar_R"]].describe().round(3).to_string())
print(L.exit_reason.value_counts())
print("\nside x mkt_against_hs among losers", pd.crosstab(L.side, L.mkt_against_hs))
