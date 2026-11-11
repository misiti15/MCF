"""REPS1b - lever table in SETUP-DAYS (Lead lead-20261111-1300-2; Observer ICC ~0.19; Skeptic skeptic-20261111-1251-2).
Descriptive, 0 configs. Input: reps1_signals_sim.csv.gz (REPS1 output) + trades.csv.gz.
 - new setup-days: a skipped signal on a (setup, day) where that setup submitted NOTHING that day (any account) adds a new
   setup-day; otherwise it is an extra same-day entry (worth little: a session ~ 4.8 independent trades).
 - exit-model gap by entry hour (sim minus live gross on submitted trades) is subtracted per signal by its hour.
 - day-clustered t, n days, best-day share for each lever's adjusted what-if minus same-group submitted live gross.
    python -I reps1b.py <reps1_signals_sim.csv.gz> <trades.csv.gz>       Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
S = pd.read_csv(sys.argv[1]); T = pd.read_csv(sys.argv[2])
NS = S.day.nunique(); WK = NS / 5
S["hr"] = pd.to_datetime(S.ts, utc=True).dt.tz_convert("America/New_York").dt.hour.clip(9, 15)
T["k"] = T.acct + "|" + T.strategy + "|" + T.symbol + "|" + T.date
T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0]; T["gR"] = T.pnl / T.risk
S["k"] = S.acct + "|" + S.strategy + "|" + S.symbol + "|" + S.day
C = S[S.status == "submitted"].drop_duplicates("k").join(T.groupby("k").gR.mean(), on="k").dropna(subset=["sim", "gR"])
gap = (C.sim - C.gR).groupby(C.hr).agg(["mean", "size"])
print(f"{NS} sessions (10-20..11-10). Exit-model gap (sim - live gross) by entry hour, submitted trades:")
print("   " + "  ".join(f"{h}h {r['mean']:+.3f} (n {int(r['size'])})" for h, r in gap.iterrows()))
S["adj"] = S.sim - S.hr.map(gap["mean"])
sub_days = set(zip(S[S.status == "submitted"].strategy, S[S.status == "submitted"].day))
S["newday"] = [(s, d) not in sub_days for s, d in zip(S.strategy, S.day)]
live = C.groupby("grp").gR.mean() if "grp" in C else None
def rows(df, grp):
    base = C[C.grp == grp] if grp != "ALL" else C
    bd = base.groupby("day").gR.mean()
    out = []
    for lv, g in df[df.status != "submitted"].groupby("lever"):
        nd = g[g.newday].groupby(["strategy", "day"]).ngroups
        x = g.dropna(subset=["adj"]); dd = (x.groupby("day").adj.mean() - bd).dropna()
        t = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))) if len(dd) > 2 and dd.std() > 0 else np.nan
        tot = (x.groupby("day").adj.sum() - x.groupby("day").size() * bd.reindex(x.groupby("day").size().index)).dropna()
        share = tot.max() / tot.sum() if tot.sum() > 0 else np.nan
        out.append(dict(lever=lv, signals=len(g), new_setup_days_wk=nd / WK, setups=g.strategy.nunique(),
                        newday_share=g.newday.mean(), adj_vs_live=x.adj.mean() - base.gR.mean(), day_t=t, n_days=len(dd),
                        best_day_share=share, longs=(g.side > 0).mean()))
    return pd.DataFrame(out).sort_values("new_setup_days_wk", ascending=False)
pd.set_option("display.width", 230)
cur = {g: S[(S.grp == g) & (S.status == "submitted")].groupby(["strategy", "day"]).ngroups / WK for g in ("Gen", "low-rep", "other")}
print("current submitted setup-days per week: " + ", ".join(f"{g} {v:.1f}" for g, v in cur.items()))
for g in ("Gen", "low-rep", "other"):
    print(f"\n{g.upper()}: levers ranked by NEW setup-days per week (adj_vs_live = hour-adjusted what-if minus this group's "
          f"submitted live gross; day_t / best_day_share on per-day differences)")
    print(rows(S[S.grp == g], g).round(3).to_string(index=False))
# low-rep: is the limit blocks or signal frequency?
lr = S[S.grp == "low-rep"]
ss = lr.groupby("strategy").agg(sig_days=("day", "nunique"), sub_days=("day", lambda d: lr.loc[d.index][lr.loc[d.index].status == "submitted"].day.nunique()))
print(f"\nLOW-REP: {len(ss)} setups with any signal; median signal-days {ss.sig_days.median():.0f} of {NS}, median submitted-days "
      f"{ss.sub_days.median():.0f}; setup-days with a signal but no submission: {int((ss.sig_days - ss.sub_days).sum())}")
print("HTB / not-shortable skips stay labelled 'virtual' and out of any verdict (Skeptic): squeeze-prone names, no borrow fee.")
print("Educational only - not financial advice.")
