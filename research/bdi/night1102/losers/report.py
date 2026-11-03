"""Loser lists + pattern table. Usage: python report.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); D = Path(__file__).parent
t = pd.read_parquet(S / "feat3.parquet")
t["stop_bps"] = (t.entry - t.stop).abs() / t.entry * 1e4
t["side_s"] = np.where(t.side > 0, "long", "short")
cols = ["account", "date", "etod", "strategy", "symbol", "ty", "side_s", "R", "exit_reason", "mfe_r", "mins_to_exit", "pos5_side",
        "rng5_R", "vwap_dist_R", "stop_bps", "fill_vs_bar_R", "spy_fo", "spy_30", "spy_rest", "sym_day_pos", "clu_pos",
        "R_base", "R_wait1", "R_wait3", "R_wait5", "R_lim_vwap", "R_lim_pb25", "R_ts30", "R_ts60", "R_scr30", "R_be03",
        "R_part05", "R_wide15", "R_opposite"]
L = t[t.loser].copy()
L["acc_order"] = L.account.map({"primary": 0, "testing1": 1, "testing2": 2, "graveyard": 3, "gen": 4})
L = L.sort_values(["acc_order", "date", "etod"])
L[L.account == "primary"][cols].to_csv(D / "losers_primary.csv", index=False, float_format="%.3f")
L[cols].to_csv(D / "losers_all.csv.gz", index=False, float_format="%.3f")
P = {  # name: (flag, actionable at entry?, adjustment tested)
    "P1 inverse-ETF short (= long the underlying)": (L.ty.eq("inverse") & (L.side < 0), "yes", "B_no_inverse_short"),
    "P2 same symbol again (2nd+ lot that day, any setup)": (L.sym_day_pos > 1, "yes", "A_one_per_symbol_day"),
    "P3 stacked same-side lots (4th+ entry in a 10-min chain)": (L.clu_pos > 3, "yes", "E_stack_cap3_10min"),
    "P4 late (>=13:30) entry WITH an extended SPY move (|SPY from open| >= 0.75%)": (
        (L.etod >= "1330") & (np.sign(L.spy_fo) == L.side) & (L.spy_fo.abs() >= 0.75), "yes", "C_late_with_extended_spy_1330_075"),
    "P5 chased entry (top/bottom 10% of the prior 5 bars, trade direction)": (L.pos5_side > 0.9, "yes", "wait3 / lim_pb25"),
    "P6 tight stop (< 53 bps of price, bottom quintile)": (L.stop_bps < 53, "yes", "wide15"),
    "P7 never worked (MFE < 0.2R before the stop)": (L.mfe_r.fillna(L.sim_mfe) < 0.2, "no (hindsight)", "scr30 / scr60"),
    "P8 fast stop (stopped within 5 min)": ((L.exit_reason == "stop") & (L.mins_to_exit <= 5), "no (hindsight)", "wait1 / wide15"),
    "P9 market moved against after entry (SPY entry->15:55 against the side)": (np.sign(L.spy_rest) == -L.side, "no (hindsight)", "regime layer (other workstream)"),
}
rows = []
for name, (m, act, adj) in P.items():
    r = {"pattern": name, "actionable": act, "adjustment": adj}
    for a, x in [("primary", L.account == "primary"), ("all", L.account.notna())]:
        mm = m & x
        r[f"{a}_losers"] = int(mm.sum()); r[f"{a}_share"] = mm.sum() / x.sum(); r[f"{a}_lossR"] = L.R[mm].sum()
    rows.append(r)
T = pd.DataFrame(rows); T.to_csv(D / "pattern_table.csv", index=False, float_format="%.3f")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
print(T.round(3).to_string())
print("\nlosers by account:", L.account.value_counts().to_dict(), "loser R:", L.groupby("account").R.sum().round(1).to_dict())
print("\nloser medians (primary / all):")
for a, x in [("primary", L[L.account == "primary"]), ("all", L)]:
    print(a, x[["R", "mfe_r", "mins_to_exit", "pos5_side", "rng5_R", "stop_bps", "fill_vs_bar_R", "spy_fo"]].median().round(3).to_dict())
    print(a, "side", x.side_s.value_counts().to_dict(), "type", x.ty.value_counts().to_dict(), "exit", x.exit_reason.value_counts().to_dict())
    print(a, "opposite side would have won (R_opposite>0):", round((x.R_opposite > 0).mean(), 3), "mean", round(x.R_opposite.mean(), 3))
    print(a, "entry hour", x.etod.str[:2].value_counts().sort_index().to_dict())
print("\nPrimary losers by setup"); p = L[L.account == "primary"]
print(p.groupby("strategy").agg(n=("R", "size"), R=("R", "sum")).sort_values("R").round(2).to_string())
