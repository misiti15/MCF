"""Giveback map, live tables (a)(b)(c). Usage: python analyze_live.py SCRATCH OUT.md. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import CK, state, dstat, tod_bucket, hold_bucket, md
S, OUT = sys.argv[1], sys.argv[2]
P = pd.read_parquet(f"{S}/live_paths.parquet")
P["m_in"] = P.m_in.astype(int)
X = P.sort_values("account").drop_duplicates(["strategy", "symbol", "m_in", "date"])   # identical signals in 2 accounts once
X = X[X.mfe_b.notna()].copy()
X["give"] = X.mfe_b - X.R
X["stop"] = X.exit_reason.eq("stop")
X["tod"] = tod_bucket(X.m_in).astype(str); X["holdb"] = hold_bucket(X.hold_min).astype(str)
X["day"] = np.where(X.spy_oc > .25, "SPY up day", np.where(X.spy_oc < -.25, "SPY down day", "SPY flat day"))
X["mkt"] = np.where(X.spy_tr > .2, "SPY with trade", np.where(X.spy_tr < -.2, "SPY against trade", "SPY flat in trade"))
X["sidec"] = np.where(X.side > 0, "long", "short")
X["tgtb"] = pd.cut(X.tgtR.fillna(99), [0, .6, .9, 1.2, 50, 1e9], labels=["tgt<0.6R", "tgt 0.6-0.9R", "tgt 0.9-1.2R", "tgt>1.2R", "no target (hold)"]).astype(str)
L = []
def p(s=""): L.append(s)
def cut(col, minn=150):
    rows = []
    for k, g in X.groupby(col):
        if len(g) < minn: continue
        r = dict(cut=k, n=len(g), avgR=g.R.mean(), MFE=g.mfe_b.mean(), MAE=g.mae_b.mean(), med_tMFE=g.tmfe.median(), give=g.give.mean())
        for x in (.5, .8, 1.0):
            gg = g[g.mfe_b >= x]; r[f"reach{x}"] = len(gg) / len(g); r[f"stop|{x}"] = gg.stop.mean() if len(gg) else np.nan
        nt = g[g.tgtR.notna() & (g.mfe_b >= .8 * g.tgtR)]; r["stop|80%tgt"] = nt.stop.mean() if len(nt) else np.nan
        u = g[(g.mfe_b >= .8) & (g.R <= 0)]
        r["R_lost_after_+0.8"] = (u.mfe_b - u.R).sum()      # distance from peak to exit, summed, for trades that reached +0.8 and closed <= 0
        r["R_of_those"] = u.R.sum(); r["n_those"] = len(u)
        rows.append(r)
    return pd.DataFrame(rows)
p(f"Live trades with minute paths (de-duplicated across accounts): {len(X)} on {X.date.nunique()} sessions; avg R {X.R.mean():+.3f}.")
p(f"Journal mfe_r vs bar MFE: corr {X[['mfe_r','mfe_b']].corr().iloc[0,1]:.2f}.")
p()
for col, title in (("sidec", "side"), ("tgtb", "target distance from fill"), ("itype", "instrument type"), ("tod", "entry time"), ("holdb", "hold time"), ("day", "day type (SPY open->close)"), ("mkt", "SPY during the trade, signed by trade side"), ("account", "account")):
    p(f"### (a) by {title}"); p(md(cut(col, 100))); p()
fam = X.assign(fs=X.family + " " + X.sidec)
X = fam
F = cut("fs", 100).sort_values("R_lost_after_+0.8", ascending=False)
p("### (a) by family x side (n >= 100), sorted by R lost after reaching +0.8R"); p(md(F)); p()
F.to_csv(f"{S}/live_family.csv", index=False)
# pockets: family x side x (tod | mkt | itype), n >= 60
rows = []
for c2 in ("tod", "mkt", "day", "itype", "holdb"):
    for (fs, k), g in X.groupby(["fs", c2]):
        if len(g) < 60: continue
        u = g[(g.mfe_b >= .8) & (g.R <= 0)]
        rows.append(dict(pocket=f"{fs} | {k}", n=len(g), avgR=g.R.mean(), reach08=(g.mfe_b >= .8).mean(), stop_given08=(g[g.mfe_b >= .8].stop.mean() if (g.mfe_b >= .8).any() else np.nan),
                         n_up_then_red=len(u), R_lost=(u.mfe_b - u.R).sum(), lost_per_trade=(u.mfe_b - u.R).sum() / len(g)))
PK = pd.DataFrame(rows).sort_values("R_lost", ascending=False)
PK.to_csv(f"{S}/live_pockets.csv", index=False)
p("### (a) strongest live giveback pockets (family x side x cut, n >= 60), top 25 by R lost after +0.8R"); p(md(PK.head(25))); p()
# (b) account-days
A = pd.read_csv(f"{S}/account_days.csv")
A["give"] = A.peak - A.close
A["leg_open"] = A.openlots_R_close - A.openlots_mark_peak
A["mkt_signed"] = A.spy_peak_close * A.netdir
p("### (b) account-day peak vs close (marked to market, R)")
for thr in (3, 5, 8):
    g = A[A.peak >= thr]
    p(f"- peak >= +{thr}R: {len(g)} account-days; closed red {int((g.close < 0).sum())} ({(g.close < 0).mean():.0%}); closed below half the peak {int((g.close < g.peak / 2).sum())}; avg giveback {g.give.mean():.1f}R")
p(f"- all account-days: {len(A)}; avg peak {A.peak.mean():.1f}R, avg close {A.close.mean():.1f}R, total giveback peak->close {A.give.sum():.0f}R")
g = A[(A.peak >= 5) & (A.close < 0)].sort_values("give", ascending=False)
p(); p("Green peak >= +5R that closed red:")
p(md(g[["account", "date", "n", "peak", "peak_m", "close", "trough", "open_at_peak", "same_dir_share", "netdir", "mkt_signed", "leg_open", "late_n", "late_R", "spy_oc", "top_setup_at_peak"]].assign(peak_m=lambda x: (x.peak_m // 60).astype(str) + ":" + (x.peak_m % 60).astype(str).str.zfill(2)), "{:.2f}"))
G5 = A[(A.peak >= 5) & (A.give >= 5)]
p(); p(f"Drivers across all account-days with peak >= +5R and giveback >= 5R (n {len(G5)}): giveback {G5.give.sum():.0f}R = open-at-peak lots {G5.leg_open.sum():.0f}R lost + late entries {-G5.late_R.sum():.0f}R lost (sum check {(G5.leg_open.sum() + G5.late_R.sum()):.0f}R vs -{G5.give.sum():.0f}R; the rest is the mark-vs-cost gap).")
p(f"  - SPY moved against the book's net direction after the peak on {int((G5.mkt_signed < 0).sum())} of {len(G5)} (median signed SPY move {G5.mkt_signed.median():+.2f}%); same-direction share of open lots at the peak: median {G5.same_dir_share.median():.0%}, >= 80% on {int((G5.same_dir_share >= .8).sum())}.")
p(f"  - peak time: median {int(G5.peak_m.median())//60}:{int(G5.peak_m.median())%60:02d}; peaks before 12:00 {int((G5.peak_m < 720).sum())}.")
oth = A[(A.peak >= 5) & (A.give < 5)]
p(f"  - comparison, peak >= +5R with giveback < 5R (n {len(oth)}): signed SPY after peak median {oth.mkt_signed.median():+.2f}%, same-direction share median {oth.same_dir_share.median():.0%}, late entries {oth.late_R.sum():+.0f}R.")
A["late_per"] = A.late_R / A.late_n.clip(lower=1)
ac = A.groupby("account").agg(days=("date", "size"), peak_ge5=("peak", lambda v: int((v >= 5).sum())), red_after_ge5=("close", lambda v: 0),
                              sum_close=("close", "sum"), sum_give=("give", "sum"), open_at_peak_change=("leg_open", "sum"), late_R=("late_R", "sum"), late_n=("late_n", "sum")).reset_index()
ac["red_after_ge5"] = [int(((A.account == a) & (A.peak >= 5) & (A.close < 0)).sum()) for a in ac.account]
p(); p("Per account (all sessions): giveback peak->close split into lots open at the peak vs entries after the peak"); p(md(ac, "{:.1f}"))
q = A[A.peak >= 3]
p(f"Across account-days with peak >= +3R (n {len(q)}): corr(open-at-peak change per open lot, signed SPY move after peak) = {np.corrcoef(q.leg_open / q.open_at_peak.clip(lower=1), q.mkt_signed.fillna(0))[0,1]:.2f}; "
  f"late entries average {q.late_R.sum() / max(1, q.late_n.sum()):+.3f}R per trade vs {X.R.mean():+.3f}R for all live trades.")
A.to_csv(f"{S}/account_days2.csv", index=False)
# (c) stalled signature, live descriptive
rows = []
for t in CK:
    y = X[X[f"rem{t}"].notna()].copy(); y["st"] = state(y[f"mk{t}"], y[f"mf{t}"]); y["r"] = y[f"rem{t}"]
    for (fs, st), g in list(y.groupby(["sidec", "st"])) + list(y.groupby(["fs", "st"])):
        if len(g) < 60: continue
        s_ = dstat(g); rows.append(dict(t=t, group=fs, state=st, n=s_["n"], days=s_["days"], rem=s_["mean"], t_stat=s_["t"], wo_best=s_["wo_best"],
                                        final=g.R.mean(), p_stop=g.stop.mean()))
C = pd.DataFrame(rows); C.to_csv(f"{S}/live_stalled.csv", index=False)
p(); p("### (c) live stalled-trade cells (remaining value = final R - exit at minute-t close, LR8 + half-spread + $0.01 extra), by side")
p(md(C[C.group.isin(["long", "short"])].sort_values(["group", "state", "t"]), "{:.3f}"))
p(); p("Most negative live family cells (n >= 60), descriptive (10-06..11-19, <= 33 sessions):")
p(md(C[~C.group.isin(["long", "short"])].sort_values("t_stat").head(20)))
p(); p("Most positive live family cells (holding paid):"); p(md(C[~C.group.isin(["long", "short"])].sort_values("t_stat", ascending=False).head(10)))
open(OUT, "w").write("\n".join(L) + "\n"); print("\n".join(L[:12]))
