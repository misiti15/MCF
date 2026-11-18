"""U5 diagnostics (descriptive, no new configs): cost drag, Primary-day overlay, overlap with Primary trades.
Educational only - not financial advice."""
import json, glob, sys, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u5"; OUT = sys.argv[1]
pd.set_option("display.width", 220)
rows = []
for tag in ("fit", "check"):
    T = pd.read_csv(f"{S}/trades_{tag}.csv")
    for (s, v), g in T.groupby(["setup", "var"]):
        rows.append(dict(sample=tag, setup=s, version=v, trades=len(g), avg_gross=round(g.r_gross.mean(), 4), avg_net=round(g.r.mean(), 4),
                         cost_R=round((g.r_gross - g.r).mean(), 4), med_r_atr=round(g.r_atr.median(), 3),
                         avg_net_r_atr_ge_0p25=round(g.r[g.r_atr >= 0.25].mean(), 4), n_ge_0p25=int((g.r_atr >= 0.25).sum())))
C = pd.DataFrame(rows); C.to_csv(f"{OUT}/u5_cost_drag.csv", index=False); print(C.to_string(index=False))
# Primary overlay on check sessions
info = pd.DataFrame([json.load(open(f)) for f in sorted(glob.glob(f"{S}/out_chk/*.json"))]).set_index("date")
q40 = float(pd.DataFrame([json.load(open(f)) for f in glob.glob(f"{S}/out_fit/*.json")]).or30s.quantile(.4))
P = pd.read_csv(f"{S}/primary_daily.csv").set_index("date").R
T = pd.read_csv(f"{S}/trades_check.csv"); T = T[T["var"] == "cue"]
dd = T.pivot_table(index="date", columns="setup", values="r", aggfunc="sum").reindex(info.index).fillna(0)
o = pd.DataFrame(dict(spy_oc_pct=(info.spy_oc * 100).round(2), dtype=np.where(info.spy_oc > .0025, "up", np.where(info.spy_oc < -.0025, "down", "quiet")),
                      quiet_cue=(info.or30s <= q40), up_cue=info.up_any, primary_R=P.reindex(info.index).round(1)))
o = o.join(dd.round(1)); o.to_csv(f"{OUT}/u5_check_days.csv"); print(o.to_string())
print("\nPrimary R by realized day type:", o.groupby("dtype").primary_R.agg(["size", "sum", "mean"]).round(1).to_dict())
for s in dd.columns:
    act = o[o[s] != 0]
    red = act[act.primary_R < 0]
    print(s, "active days", len(act), "corr w Primary", round(act[s].corr(act.primary_R), 2) if len(act) > 2 else None,
          "| on Primary red days:", len(red), "green", int((red[s] > 0).sum()), "red", int((red[s] < 0).sum()), "sum R", round(red[s].sum(), 1),
          "Primary those days", round(red.primary_R.sum(), 1))
# overlap with Primary live trades (same symbol-day), incl. L3-gap-slope-fromopen-FD
pt = pd.read_csv(f"{S}/primary_trades.csv")
k = set(zip(pt.symbol, pt.date)); kl3 = set(zip(pt[pt.strategy == "L3-gap-slope-fromopen-FD"].symbol, pt[pt.strategy == "L3-gap-slope-fromopen-FD"].date))
for s, g in T.groupby("setup"):
    ks = list(zip(g.symbol, g.date))
    print(s, "symbol-day overlap with Primary", round(np.mean([x in k for x in ks]), 3), "with L3-fromopen", round(np.mean([x in kl3 for x in ks]), 3))
