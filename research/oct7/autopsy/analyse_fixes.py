"""Score the fix families from test_fixes.py (train/valid only). Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd

OUT = "research/oct7/autopsy/"
R = pd.read_parquet(OUT + "fix_trades.parquet")
B = R[R.variant == "base"].copy()
B["key"] = B.symbol + "|" + B.date + "|" + B.setup
B["r0"] = B.pnl / (B.shares * B.entry * B.risk_pct / 100)          # original R units, $-based
res = {}


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def paired(base, var, split, setup=None):
    """Daily-clustered paired $ difference variant - base (all days with base trades in the split)."""
    b = base[(base.split == split) & ((base.setup == setup) if setup else True)]
    v = var[(var.split == split) & ((var.setup == setup) if setup else True)]
    db = b.groupby("date").pnl.sum()
    dv = v.groupby("date").pnl.sum().reindex(db.index, fill_value=0.0)
    d = dv - db
    return dict(n_base=len(b), n_var=len(v), base_usd=round(db.sum(), 1), var_usd=round(dv.sum(), 1),
                base_per_trade=round(b.pnl.mean(), 2), var_per_trade=round(v.pnl.mean(), 2) if len(v) else None,
                d_usd=round(d.sum(), 1), d_t_day=round(tstat(d), 2), d_ex_best=round(d.sum() - d.max(), 1),
                days=len(d))


# ---- 1. Recovery: once a trade is down x% from the fill, how often does it still close green? ----------
rec = []
for setup in ["orb20_a", "heat_fade_short", "heat_fade_long", "exhaustion_short", "ALL"]:
    b = B if setup == "ALL" else B[B.setup == setup]
    for x in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0):
        s = b[b.mae_pct <= -x]
        ret = s.pnl / s.notional * 100
        rec.append(dict(setup=setup, down_at_least_pct=x, n=len(s), share_of_trades=round(len(s) / max(len(b), 1), 3),
                        closed_green=round(float((s.pnl > 0).mean()), 3) if len(s) else None,
                        avg_final_pct=round(float(ret.mean()), 3) if len(s) else None,
                        median_risk_pct=round(float(s.risk_pct.median()), 2) if len(s) else None,
                        days=s.date.nunique()))
rec = pd.DataFrame(rec)
rec.to_csv(OUT + "recovery_table.csv", index=False)
print(rec.to_string())
print("risk_pct (stop distance % of price) by setup:\n", B.groupby("setup").risk_pct.describe(percentiles=[.25, .5, .75, .9]).round(2))

# ---- 2. Max-loss cap and give-back exits: per setup and all-at-once ------------------------------------
rows = []
for var in sorted(R.variant.unique()):
    if var == "base":
        continue
    V = R[R.variant == var]
    for setup in ["orb20_a", "heat_fade_short", "heat_fade_long", "exhaustion_short", None]:
        for split in ("train", "valid"):
            rows.append(dict(variant=var, setup=setup or "ALL4", split=split, **paired(B, V, split, setup)))
X = pd.DataFrame(rows)
# a config "passes" (pre-registered, same as the nightly gate): d_usd > 0 on train AND valid, valid t_day >= 1.0
# (>= 1.5 for the exit_* family: a rework look 2 of the EXIT_STUDY lineage), ex-best-day > 0 on both
# max-loss caps and exits are scored per setup and ALL4 (configs counted separately)
piv = X.pivot_table(index=["variant", "setup"], columns="split", values=["d_usd", "d_t_day", "d_ex_best", "var_per_trade", "base_per_trade", "n_var"], aggfunc="first")
piv.columns = [f"{a}_{b}" for a, b in piv.columns]
piv = piv.reset_index()
need_t = np.where(piv.variant.str.startswith("exit_"), 1.5, 1.0)
piv["pass"] = (piv.d_usd_train > 0) & (piv.d_usd_valid > 0) & (piv.d_t_day_valid >= need_t) & (piv.d_ex_best_train > 0) & (piv.d_ex_best_valid > 0)
piv.to_csv(OUT + "fix_results.csv", index=False)
print(piv[["variant", "setup", "n_var_train", "base_per_trade_train", "var_per_trade_train", "d_usd_train", "d_t_day_train",
           "n_var_valid", "base_per_trade_valid", "var_per_trade_valid", "d_usd_valid", "d_t_day_valid", "d_ex_best_valid", "pass"]].to_string())

# ---- 3. orb20_a opening-range width filters (skip wide ORs) ---------------------------------------------
O = B[B.setup == "orb20_a"].copy()
O["w_pct"] = O.or_width / O.entry * 100
O["w_atr"] = O.or_width / O.atr
print("\norb20_a OR width % of price:", O.w_pct.describe(percentiles=[.25, .5, .75, .9]).round(2).to_dict())
print("orb20_a OR width / ATR:", O.w_atr.describe(percentiles=[.25, .5, .75, .9]).round(2).to_dict())
for col, edges in (("w_pct", [0, 2, 3, 4, 5, 6, 8, 100]), ("w_atr", [0, .3, .5, .75, 1, 1.5, 10])):
    g = O.groupby([pd.cut(O[col], edges), "split"], observed=True).agg(n=("pnl", "size"), usd=("pnl", "mean"), r0=("r0", "mean"),
                                                                       win=("pnl", lambda x: (x > 0).mean()), days=("date", "nunique"))
    print(g.round(3).to_string())
frows = []
rng = np.random.default_rng(7)
for col, xs in (("w_pct", [3, 4, 5, 6, 8]), ("w_atr", [0.5, 0.75, 1.0])):
    for x in xs:
        for split in ("train", "valid"):
            s = O[O.split == split]
            keep = s[s[col] <= x]
            db = s.groupby("date").pnl.sum()
            dk = keep.groupby("date").pnl.sum().reindex(db.index, fill_value=0.0)
            frac = len(keep) / len(s)
            # baseline (rule 6): random drop of the same share of trades -> expected daily total = frac * base
            d_rand = dk - frac * db
            # random-drop simulation for a p-value on the total
            sims = []
            for _ in range(2000):
                m = rng.random(len(s)) < frac
                sims.append(s.pnl.to_numpy()[m].sum())
            sims = np.array(sims)
            frows.append(dict(filter=f"orb_{col}<={x}", split=split, n_base=len(s), n_keep=len(keep),
                              base_usd=round(s.pnl.sum(), 1), keep_usd=round(keep.pnl.sum(), 1),
                              base_per_trade=round(s.pnl.mean(), 2), keep_per_trade=round(keep.pnl.mean(), 2),
                              dropped_per_trade=round(s[s[col] > x].pnl.mean(), 2) if len(keep) < len(s) else None,
                              d_vs_base_t_day=round(tstat(dk - db), 2), d_vs_random=round(d_rand.sum(), 1),
                              d_vs_random_t_day=round(tstat(d_rand), 2), p_random_better=round(float((sims >= keep.pnl.sum()).mean()), 3),
                              ex_best_d=round((dk - db).sum() - (dk - db).max(), 1)))
F = pd.DataFrame(frows)
F.to_csv(OUT + "orb_width_filters.csv", index=False)
print(F.to_string())
