"""Observer: faster sound verdicts (Lead lead-20261111-1100-4, owner live-reps priority item 3). Builds on fastdec (main session).
Compares verdict rules on live setup records with the common DAY x SIDE factor removed (Skeptic skeptic-20261111-1102-3):
  x = R - mean R of OTHER setups' trades on the same date and side (leave-one-setup-out), per trade.
Rules, each on excess x AND on raw R (for contrast); shared call floor: >= 4 traded sessions and >= 10 trades (as fastdec):
  (a) RAW  running session-clustered avg; demote if avg < -0.05 and t <= -1.28; promote if avg > 0 and t >= 1.28
  (b) EB   shrink toward the leave-one-out family x side mean (DerSimonian-Laird tau^2 on the checkpoint's setups, floor 0.02^2);
           demote if P(mu < -0.05) >= 0.90 and own avg < 0; promote if P(mu > 0) >= 0.90 and own avg > 0
  (c) EPROC XA-EPROC betting e-process on the setup's per-session mean (cap 1.0R, alpha 0.05 -> K >= 20): HARM alarm = demote, EDGE = promote
Walk-forward as fastdec: checkpoints after live sessions 6..21; first call per setup per direction; scored on the setup's NEXT 5 sessions
(>= 3 forward trades): demote correct if forward avg < 0, promote correct if > 0, on the SAME measure (excess or raw). Base rate = share
of eligible setups at that checkpoint with forward avg < 0 (demote) / > 0 (promote); lift = precision - matched base rate.
False-demote cost = forward avg of demoted setups (excess R per trade; > 0 = we cut something that was doing better than its day-side pool).
Split-half persistence: corr(odd-session avg, even-session avg) across setups with >= 8 sessions, raw vs excess.
Descriptive comparison, 6 rule x measure cells (counted as looks). usage: python verdicts.py <journal_dir> [max_date]. Educational only - not financial advice."""
import sys, glob, os, sqlite3, math, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "xaeproc"))
from eproc import eprocess
pd.set_option("display.width", 220); J = sys.argv[1]; MAXD = sys.argv[2] if len(sys.argv) > 2 else "2026-11-10"
Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
R = []
for f in sorted(glob.glob(os.path.join(J, "*.db"))):
    t = pd.read_sql("select date, strategy, side, entry, stop, shares, pnl_adj from trades where run_id=1 and exit is not null and date<=?",
                    sqlite3.connect(f), params=(MAXD,)); R.append(t)
T = pd.concat(R, ignore_index=True); T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares).replace(0, np.nan); T = T[T.R.notna()]
T["fam"] = T.strategy.str.extract(r"^(GEN|RW|L3|MF|NS|CWT|ST|NM|LD|LIQ)")[0].fillna("CLS")
g = T.groupby(["date", "side"]); s_all, n_all = g.R.transform("sum"), g.R.transform("count")
gs = T.groupby(["date", "side", "strategy"]); s_own, n_own = gs.R.transform("sum"), gs.R.transform("count")
T["x"] = np.where(n_all - n_own > 0, T.R - (s_all - s_own) / (n_all - n_own).replace(0, np.nan), np.nan)
T = T[T.x.notna()]
days = sorted(T.date.unique()); print(f"trades {len(T)}, setups {T.strategy.nunique()}, sessions {len(days)} ({days[0]}..{days[-1]})")
def stats(sub, col):
    d = sub.groupby("date")[col].agg(["sum", "count"]); k, n = len(d), d["count"].sum()
    avg = d["sum"].sum() / n
    if k < 2: return avg, np.nan, k, n, d
    resid = d["sum"] - avg * d["count"]; se = math.sqrt(k / (k - 1) * (resid ** 2).sum()) / n
    return avg, se, k, n, d
calls = []
for ci in range(5, 21):                                   # checkpoint after session ci+1 (6..21)
    cut, fwd = days[ci], days[ci + 1:ci + 6]
    past, fut = T[T.date <= cut], T[T.date.isin(fwd)]
    for col in ("x", "R"):
        rec = {}
        for st, sub in past.groupby("strategy"):
            avg, se, k, n, _ = stats(sub, col)
            if k >= 4 and n >= 10 and np.isfinite(se) and se > 0: rec[st] = (avg, se, k, n, sub.fam.iloc[0], int(np.sign(sub.side.mean())))
        if not rec: continue
        Rdf = pd.DataFrame(rec, index=["avg", "se", "k", "n", "fam", "side"]).T
        for c in ("avg", "se", "k", "n"): Rdf[c] = Rdf[c].astype(float)
        # EB: DL tau^2 on all eligible setups' avgs (fixed-effects weights), prior = leave-one-out family x side mean
        w = 1 / Rdf.se ** 2; mu0 = (w * Rdf.avg).sum() / w.sum(); Q = (w * (Rdf.avg - mu0) ** 2).sum()
        tau2 = max(0.02 ** 2, (Q - (len(Rdf) - 1)) / (w.sum() - (w ** 2).sum() / w.sum())) if len(Rdf) > 2 else 0.02 ** 2
        fwd_avg = {st: (sub[col].sum() / len(sub)) for st, sub in fut.groupby("strategy") if len(sub) >= 3}
        for st, r in Rdf.iterrows():
            peers = Rdf[(Rdf.fam == r.fam) & (Rdf.side == r.side) & (Rdf.index != st)]
            pm = peers.avg.mean() if len(peers) else Rdf[Rdf.index != st].avg.mean()
            post_v = 1 / (1 / tau2 + 1 / r.se ** 2); post_m = post_v * (pm / tau2 + r.avg / r.se ** 2)
            ts = r.avg / r.se
            sess = past[past.strategy == st].groupby("date")[col].mean().to_numpy()
            ep = eprocess(sess, 1.0, 0.05)
            dec = {"RAW": ("demote" if (r.avg < -0.05 and ts <= -1.28) else "promote" if (r.avg > 0 and ts >= 1.28) else None),
                   "EB": ("demote" if (1 - Phi((-0.05 - post_m) / math.sqrt(post_v)) < 0.10 and r.avg < 0) else
                          "promote" if (Phi(post_m / math.sqrt(post_v)) >= 0.90 and r.avg > 0) else None),
                   "EPROC": ("demote" if ep["harm_alarm_day"] else "promote" if ep["edge_alarm_day"] else None)}
            for m, d in dec.items():
                calls.append(dict(ck=ci + 1, measure=col, method=m, setup=st, call=d, k=int(r.k), fwd=fwd_avg.get(st, np.nan)))
C = pd.DataFrame(calls)
out = []
for (meas, m), g in C.groupby(["measure", "method"]):
    for direction in ("demote", "promote"):
        firsts = g[g.call == direction].sort_values("ck").groupby("setup").head(1)
        sc = firsts[firsts.fwd.notna()]
        base = []
        for ck, f in sc.groupby("ck"):
            e = g[(g.ck == ck) & g.fwd.notna()].drop_duplicates("setup")
            base += [((e.fwd < 0) if direction == "demote" else (e.fwd > 0)).mean()] * len(f)
        if len(sc) == 0: out.append(dict(measure=meas, method=m, dir=direction, calls=0)); continue
        corr = (sc.fwd < 0) if direction == "demote" else (sc.fwd > 0)
        p = corr.mean(); n = len(sc); z = 1.96; lo = (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)
        out.append(dict(measure=meas, method=m, dir=direction, calls=n, precision=p, ci_lo=lo, base=np.mean(base), lift=p - np.mean(base),
                        fwd_avg_of_called=sc.fwd.mean(), wrong_calls=int((~corr).sum()), wrong_fwd_avg=sc[~corr].fwd.mean() if (~corr).any() else np.nan,
                        median_sessions_at_call=sc.k.median()))
O = pd.DataFrame(out); print("\nwalk-forward (16 checkpoints, first call per setup, next-5-session outcome on the SAME measure):")
print(O.round(3).to_string(index=False))
# split-half persistence
print("\nsplit-half persistence across setups with >= 8 sessions (corr of odd-session avg vs even-session avg):")
for col in ("R", "x"):
    a = []
    for st, sub in T.groupby("strategy"):
        d = sub.groupby("date")[col].agg(["sum", "count"])
        if len(d) < 8: continue
        od, ev = d.iloc[0::2], d.iloc[1::2]; a.append((od["sum"].sum() / od["count"].sum(), ev["sum"].sum() / ev["count"].sum()))
    a = np.array(a); r = np.corrcoef(a[:, 0], a[:, 1])[0, 1]; se = 1 / math.sqrt(len(a) - 3)
    print(f"   {col:2s}: setups {len(a)}, r {r:+.3f} (Fisher z {np.arctanh(r) / se:+.2f})")
print("\nx = R minus the leave-one-out mean of other setups' trades on the same date and side. Live paper R (after paper costs).")
print("Educational only - not financial advice.")
