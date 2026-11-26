"""COMPASSIDX-1126 CI-1 (PREREG.md): standalone SPY overlay at the first W60 confirmation 10:00..13:00, session-extreme stop
(cap 0.6%, floor 0.15%), exit 15:55 / stop / opposite confirmation, LIVE-L costs; placebos P1 random side (1,000 draws, seed
1126) and P2 prior-session close side; goal metrics. Usage: python ci1_score.py OUT.json [SPLITS...] (default FIT CHECK T2;
LIVE alone). Writes ci1_trades.csv. Locked block never read (ci_lib asserts). Educational only - not financial advice."""
import json
import sys

import numpy as np
import pandas as pd

import ci_lib as C

OUT = sys.argv[1]
SPLITS = sys.argv[2:] or ["FIT", "CHECK", "T2"]
C.LIVE_MODE = SPLITS == ["LIVE"]
assert C.LIVE_MODE or "LIVE" not in SPLITS, "score LIVE on its own"
if set(SPLITS) - {"FIT"}:
    C.prereg_gate()
G, M = C.spy_days(SPLITS), C.marks(SPLITS)
# prior session close side (P2), within the same source; 2025-03-03's prior session is in the locked block -> no P2
days = sorted(G)
cside = {d: int(np.sign(G[d].close.iloc[-1] - G[d].open.iloc[0])) for d in days}
rng = np.random.default_rng(1126)
ND = 1000
rows, P1 = [], []
for i, d in enumerate(days):
    if d not in M:
        continue
    g = G[d]; T, L = M[d]
    t0, side = C.first_conf(T, L, 600, 780)
    if t0 is None:
        continue
    tr = C.trade(g, T, L, t0, side)
    if tr is None:
        continue
    tx = tr["tx"]
    up = C.trade(g, T, L, t0, 1, exit_after=tx); dn = C.trade(g, T, L, t0, -1, exit_after=tx)
    prev = days[i - 1] if i > 0 else None
    ok_prev = prev is not None and C.period(prev) == C.period(d) and not (prev < "2025-03-01" <= d)
    ps = cside[prev] if ok_prev else 0
    p2 = (up if ps > 0 else dn)["r"] if ps != 0 else np.nan
    ret1 = tr["ret_bps"]
    r1bp = tr["r_gross"] - 1.0 / tr["dist_bps"]
    rows.append(dict(date=d, per=C.period(d), T=t0, **tr, r_1bp=r1bp, p_up=up["r"], p_dn=dn["r"], p2=p2))
x = pd.DataFrame(rows)
C.no_locked(x.date)
x.to_csv(C.H / ("ci1_trades_live.csv" if C.LIVE_MODE else "ci1_trades.csv"), index=False)


def goal(s):
    s = pd.Series(np.asarray(s, float))
    return dict(mean=round(float(s.mean()), 3), red_per_21=round(float((s < 0).mean() * 21), 2),
                worst5=round(float(s.nsmallest(5).sum()), 2), roll20_floor=round(float(s.rolling(20).sum().min()), 2),
                avg_wo_best=round(float((s.sum() - s.max()) / (len(s) - 1)), 3))


res = {"prereg_sha256": open(C.H / "PREREG.sha256").read().split()[0], "configs_counted": 2, "bar_strict": 4.26,
       "bar_C": 3.46}
for per in SPLITS:
    g = x[x.per == per]
    if not len(g):
        continue
    sess = [d for d in days if C.period(d) == per]
    r = g.r.to_numpy()
    mon = g.groupby(g.date.str[:7]).r.sum()
    tot = r.sum()
    # P1: random side per day
    draws = rng.integers(0, 2, size=(ND, len(g)))
    pr = np.where(draws == 1, g.p_up.to_numpy()[None, :], g.p_dn.to_numpy()[None, :]).mean(1)
    p2 = g.dropna(subset=["p2"])
    dd = p2.r - p2.p2
    daily = pd.Series(0.0, index=sess); daily.loc[g.date] = g.r.to_numpy()
    o = dict(sessions=len(sess), trades=int(len(g)), mean_R=round(float(r.mean()), 3), t=round(C.tstat(r), 2),
             median_R=round(float(np.median(r)), 3), hit=round(float((r > 0).mean()), 3), total_R=round(float(tot), 1),
             gross_mean_R=round(float(g.r_gross.mean()), 3), mean_R_1bp_cost=round(float(g.r_1bp.mean()), 3),
             t_1bp=round(C.tstat(g.r_1bp), 2), ret_bps_mean=round(float(g.ret_bps.mean()), 2),
             stop_share=round(float((g.kind == "stop").mean()), 3), flip_share=round(float(((g.kind == "market") & (g.tx < C.EXIT_M)).mean()), 3),
             dist_bps_median=round(float(g.dist_bps.median()), 1),
             months_pos=f"{int((mon > 0).sum())}/{len(mon)}", months_pos_share=round(float((mon > 0).mean()), 3),
             best_day_share=round(float(r.max() / tot), 3) if tot > 0 else None,
             p1_mean=round(float(pr.mean()), 3), p1_p95=round(float(np.quantile(pr, 0.95)), 3),
             beats_p1=bool(r.mean() > np.quantile(pr, 0.95)),
             p2_n=int(len(p2)), p2_mean=round(float(p2.p2.mean()), 3), p2_paired_t=round(C.tstat(dd), 2),
             goal_per_session=goal(daily.to_numpy()),
             by_month={k: round(float(v), 2) for k, v in mon.items()})
    if per in ("CHECK", "T2"):
        o["pass"] = dict(pos_t2=bool(r.mean() > 0 and o["t"] >= 2), months60=bool(o["months_pos_share"] >= 0.6),
                         bestday10=bool(o["best_day_share"] is not None and o["best_day_share"] < 0.10),
                         p1=o["beats_p1"], p2=bool(o["p2_paired_t"] >= 2))
    res[per] = o
if {"CHECK", "T2"} <= set(SPLITS):
    pc = x[x.per.isin(["CHECK", "T2"])].r
    res["pooled_CHECK_T2_t"] = round(C.tstat(pc), 2)
    res["CI1_PASS"] = bool(all(all(res[p]["pass"].values()) for p in ("CHECK", "T2")))
    res["CI1_PASS_strict"] = bool(res["CI1_PASS"] and res["pooled_CHECK_T2_t"] >= 4.26)
json.dump(res, open(OUT, "w"), indent=1)
for k, v in res.items():
    if isinstance(v, dict):
        print(k, {a: b for a, b in v.items() if a != "by_month"})
    else:
        print(k, v)
