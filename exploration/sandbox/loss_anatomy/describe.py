"""Descriptive loss anatomy tables (Primary and non-Graveyard arena, run 1, 10-23..11-27, LR8 R after costs):
totals, side, exit reason, time of day, stop width, stop in spreads, day types (SPY SIP), setup / family / setup-day
concentration, eras, weeks, bursts / concurrency / restacks with within-day checks. Run after extract.py and features.py.
Usage: python describe.py <scratch>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import load, arena, summ, dayt, spy_days
S = sys.argv[1]
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 45)
t = load(S); spy = spy_days(S).astype(float); f = pd.read_parquet(f"{S}/feat.parquet")
C = ["tr", "R", "avgR", "gross", "cost", "day_t", "R_wo_best"]
for nm, x in [("primary", t[t.book == "primary"].copy()), ("arena (deduped)", arena(t))]:
    print("\n=====", nm); print(summ(x).round(3).to_string())
    print(x.groupby("sidel").apply(summ)[C].round(3)); print(x.groupby("exit_reason").apply(summ)[C].round(3))
    x["tod"] = pd.cut(x.emin, [0, 585, 600, 630, 690, 780, 870, 960], right=False,
                      labels=["9:30-45", "9:45-10", "10-10:30", "10:30-11:30", "11:30-13", "13-14:30", "14:30-16"])
    print(x.groupby(["sidel", "tod"], observed=True).apply(summ)[C].round(3))
    x["sw"] = pd.cut(x.stop_bp, [0, 30, 50, 75, 100, 150, 250, 1e5]); print(x.groupby("sw", observed=True).apply(summ)[C].round(3))
    x["ss"] = pd.cut(x.stop_spreads, [0, 4, 6, 8, 12, 20, 40, 1e5]); print(x.groupby("ss", observed=True).apply(summ)[C].round(3))
    d = x.groupby("date").agg(R=("r", "sum"), n=("r", "size"), gross=("gross_r", "sum"), cost=("cost_r", "sum"))
    d["Rl"] = x[x.sidel == "long"].groupby("date").r.sum(); d["Rs"] = x[x.sidel == "short"].groupby("date").r.sum(); d = d.fillna(0).join(spy)
    d["dtype"] = np.where(d.spy_oc > 0.4, "up", np.where(d.spy_oc < -0.4, "down", "quiet"))
    d["gtype"] = np.where(d.spy_gap > 0.3, "gapup", np.where(d.spy_gap < -0.3, "gapdn", "flat"))
    for c in ["dtype", "gtype"]:
        print(d.groupby(c).agg(days=("R", "size"), R=("R", "sum"), Rl=("Rl", "sum"), Rs=("Rs", "sum"), red=("R", lambda s: (s <= 0).sum())).round(1))
    neg = d.R[d.R < 0].sum(); w5 = d.R.nsmallest(5)
    print(f"losing-day R {neg:.1f}; worst-5 {w5.sum():.1f} = {100*w5.sum()/neg:.0f}%; worst-5 dates {list(w5.index)}")
    s = x.groupby("strategy").r.sum().sort_values(); ns = s[s < 0].sum()
    print("worst 1/3/5/10 setups share of negative-setup R:", [f"{100*s.head(k).sum()/ns:.0f}%" for k in (1, 3, 5, 10)])
    print(x.groupby("family").apply(summ)[C].sort_values("R").round(3).head(10))
w = None
for nm, x in [("primary", f[f.book == "primary"]), ("arena (per account)", f[f.book == "arena"])]:
    print("\n=====", nm, "book features (per account)")
    sd = x.groupby(["account", "date", "strategy"]).agg(R=("r", "sum"), n=("r", "size"), stops=("exit_reason", lambda s: (s == "stop").sum()))
    nsd = sd.R[sd.R < 0].sum()
    for thr in (-3, -5, -10):
        m = sd.R <= thr; print(f"setup-days <= {thr}R: {m.sum()}/{len(sd)} carry {100*sd.R[m].sum()/nsd:.0f}% of negative setup-day R")
    print(sd.sort_values("R").head(10).round(1))
    for col, bins in [("burst15", [0, 1, 2, 4, 8, 1000]), ("conc_side", [-1, 0, 2, 5, 10, 20, 1000]), ("side_lot", [0, 3, 6, 10, 20, 40, 1000])]:
        print(col); print(x.groupby(pd.cut(x[col], bins), observed=True).apply(summ)[C].round(3))
    for col in ["name_lot", "setup_name_lot"]:
        print(col); print(x.groupby(x[col].clip(upper=4)).apply(summ)[C].round(3))
    # within account-day checks
    for lab, a_, b_ in [("side_lot>10 vs <=10", lambda g: g.side_lot <= 10, lambda g: g.side_lot > 10),
                        ("repeat name vs first", lambda g: g.name_lot == 1, lambda g: g.name_lot >= 2),
                        ("burst15>4 vs <=4", lambda g: g.burst15 <= 4, lambda g: g.burst15 > 4)]:
        rows = []
        for k, g in x.groupby(["account", "date"]):
            e, l = g[a_(g)].r, g[b_(g)].r
            if len(e) >= 1 and len(l) >= 1: rows.append((k[1], l.mean() - e.mean()))
        dd = pd.DataFrame(rows, columns=["date", "diff"]).groupby("date")["diff"].mean()
        print(f"within-day {lab}: mean diff {dd.mean():+.3f} R/lot, day-clustered t {dayt(dd):.2f}, days worse {(dd<0).sum()}/{len(dd)}")
