"""REGSTEER-1126 Step 2: REGSTEER-1 monthly expanding walk-forward on Primary's base book (rs_cand.py base.parquet), as
pre-registered in PREREG.md: 12 configs {S1, S2, S1+S2} x {pooled, hierarchical} x {OFF, OFF/HALF} (6 pooled only if Step 1
stops at side level), nulls (a) unsteered (b) constant mean weight (c) same-day permuted weights (500 draws) (d) pooled twin,
CSCV PBO (16 blocks, 12,870 splits), Hansen SPA + White RC (stationary bootstrap, mean block 5, 2,000 draws), deflated
Sharpe, goal metrics. Usage: python rs_step2.py SCR STATES STEP1.json OUT.json. Locked block never read (asserted).
Educational only - not financial advice."""
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

SCR, ST, S1J, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
LOCK = ("2024-11-01", "2025-02-28")
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "NM-ETF-late-dip-di-long"]
SHORT = {"L3-gap-slope-fromopen-FD": "L3", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
         "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5", "NM-ETF-late-dip-di-long": "NM-ETF"}
N_PRIOR, N_LINEAGE = 2271, 8891
MINCELL, SEED = 10, 1126


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def cl_var(r, day):
    """day-clustered variance of the mean of r."""
    n = len(r)
    if n < 2:
        return np.inf
    e = pd.Series(r - r.mean()).groupby(np.asarray(day)).sum().to_numpy()
    G = len(e)
    if G < 2:
        return np.inf
    return float((e ** 2).sum() / n ** 2 * G / (G - 1))


def keys(df, V):
    return list(zip(*[df[v] for v in V])) if len(V) > 1 else list(df[V[0]])


def fit(tr, V, hier, half):
    """weights per (setup, aligned cell) from training lots tr (columns setup, r, date, a1, a2)."""
    tr = tr.assign(k=keys(tr, V))
    mu, vmu = {}, {}
    for s, g in tr.groupby("setup"):
        mu[s], vmu[s] = g.r.mean(), cl_var(g.r.to_numpy(), g.date.to_numpy())
    D = []
    for (s, k), g in tr.groupby(["setup", "k"]):
        if len(g) >= MINCELL:
            D.append((s, k, g.r.mean() - mu[s], cl_var(g.r.to_numpy(), g.date.to_numpy())))
    D = pd.DataFrame(D, columns=["s", "k", "d", "v"])
    D = D[np.isfinite(D.v) & (D.v > 0)]
    gam, vg = {}, {}
    for k, g in D.groupby("k"):
        wt = 1 / g.v
        gam[k], vg[k] = float((g.d * wt).sum() / wt.sum()), float(1 / wt.sum())
    tau2 = 0.0
    if hier and len(D):
        b = D.d - D.k.map(gam); wt = 1 / D.v
        Q = float((b ** 2 * wt).sum()); df = len(D) - len(gam)
        den = sum(float(g.sum() - (g ** 2).sum() / g.sum()) for _, g in wt.groupby(D.k))
        tau2 = max(0.0, (Q - df) / den) if den > 0 else 0.0
    Dd = {(r.s, r.k): (r.d, r.v) for r in D.itertuples()}
    grid = list(itertools.product(*[(-1, 0, 1)] * len(V)))
    Wt = {}
    for s in SETUPS:
        if s not in mu:
            for k in grid:
                Wt[(s, k if len(V) > 1 else k[0])] = 1.0
            continue
        raw = {}
        for k in grid:
            kk = k if len(V) > 1 else k[0]
            g0, v0 = gam.get(kk, 0.0), vg.get(kk, 0.0)
            m, var = mu[s] + g0, vmu[s] + v0
            if hier and (s, kk) in Dd and tau2 > 0:
                d, v = Dd[(s, kk)]
                B = tau2 / (tau2 + v)
                m += B * (d - g0); var += B * v
            P = norm.cdf(-m / math.sqrt(var)) if var > 0 and np.isfinite(var) else 0.5
            w = 0.0 if (m < -0.02 and P >= 0.9) else (0.5 if (half and P >= 0.75) else 1.0)
            raw[k] = w
        for k in grid:   # monotone: never below a less-aligned cell
            Wt[(s, k if len(V) > 1 else k[0])] = max(raw[j] for j in grid if all(a <= b for a, b in zip(j, k)))
    return Wt


def walk(base, sess, V, hier, half, months):
    w = np.full(len(base), np.nan)
    gaps = sess.set_index("date").gap
    for M in months:
        tr_days = sess.date[sess.date < M + "-01"]
        cuts = gaps.reindex(tr_days).dropna().quantile([1 / 3, 2 / 3]).to_numpy()
        b = base.assign(s1=np.where(base.gap <= cuts[0], -1, np.where(base.gap > cuts[1], 1, 0)))
        b["a1"], b["a2"] = b.side * b.s1, b.side * b.w60
        tr = b[b.date < M + "-01"]
        te = b.mon == M
        Wt = fit(tr, V, hier, half)
        kk = keys(b[te], V)
        w[te.to_numpy()] = [Wt[(s, k)] for s, k in zip(b.setup[te], kk)]
    return w


def stationary_idx(n, B, mean_block, rng):
    p = 1.0 / mean_block
    idx = np.empty((B, n), int)
    idx[:, 0] = rng.integers(0, n, B)
    for t in range(1, n):
        new = rng.random(B) < p
        idx[:, t] = np.where(new, rng.integers(0, n, B), (idx[:, t - 1] + 1) % n)
    return idx


def spa(X, B=2000, rng=None):
    n, K = X.shape
    idx = stationary_idx(n, B, 5, rng)
    dbar = X.mean(0)
    bm = np.stack([X[i].mean(0) for i in idx])          # B x K
    om = np.sqrt(n * bm.var(0))
    t = math.sqrt(n) * dbar / om
    T = max(0.0, t.max())
    g = np.where(t >= -math.sqrt(2 * math.log(math.log(n))), dbar, 0.0)
    Ts = np.maximum(0, (math.sqrt(n) * (bm - g) / om).max(1))
    V = math.sqrt(n) * dbar.max()
    Vs = (math.sqrt(n) * (bm - dbar)).max(1)
    return float((Ts >= T).mean()), float((Vs >= V).mean())


def cscv(X, S=16):
    n, K = X.shape
    edges = np.linspace(0, n, S + 1).astype(int)
    bs = np.stack([X[a:b].sum(0) for a, b in zip(edges[:-1], edges[1:])]); bn = np.diff(edges)
    lg = []
    for c in itertools.combinations(range(S), S // 2):
        ins = np.zeros(S, bool); ins[list(c)] = True
        mi = bs[ins].sum(0) / bn[ins].sum(); mo = bs[~ins].sum(0) / bn[~ins].sum()
        k = int(np.argmax(mi))
        rank = (mo < mo[k]).sum() + 1 + 0.5 * ((mo == mo[k]).sum() - 1)
        om = rank / (K + 1)
        lg.append(math.log(om / (1 - om)))
    lg = np.array(lg)
    return float((lg <= 0).mean()), len(lg)


def dsr(x, sr_var, N):
    x = np.asarray(x, float); T = len(x)
    sr = x.mean() / x.std(ddof=1)
    sk = float(pd.Series(x).skew()); ku = float(pd.Series(x).kurt()) + 3
    e = 0.5772156649
    sr0 = math.sqrt(sr_var) * ((1 - e) * norm.ppf(1 - 1 / N) + e * norm.ppf(1 - 1 / (N * math.e)))
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(max(1e-12, 1 - sk * sr + (ku - 1) / 4 * sr ** 2))
    return float(norm.cdf(z)), float(sr), float(sr0)


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 1 and x.std() > 0 else 0.0


def goal(dayR):
    s = pd.Series(dayR)
    w5_60 = [np.sort(s.iloc[i:i + 60].to_numpy())[:5].sum() for i in range(0, len(s) - 59)]
    return dict(mean=round(float(s.mean()), 3), red_per_21=round(float((s < 0).mean() * 21), 2),
                worst5=round(float(np.sort(s.to_numpy())[:5].sum()), 1), worst_trailing60_worst5=round(float(min(w5_60)), 1),
                median_trailing60_worst5=round(float(np.median(w5_60)), 1),
                roll20_floor=round(float(s.rolling(20).sum().min()), 1),
                avg_wo_best=round(float((s.sum() - s.max()) / (len(s) - 1)), 3))


if __name__ == "__main__":
    base = pd.read_parquet(SCR / "base.parquet")
    no_locked(base.date.unique())
    base = base[base.gap.notna() & (base.w60 != -9)].reset_index(drop=True)
    base["mon"] = base.date.str[:7]
    sess = pd.read_parquet(ST / "gap.parquet")
    sess = sess[sess.date.map(period) != "none"].sort_values("date").reset_index(drop=True)
    no_locked(sess.date)
    months = sorted(m for m in sess.date.str[:7].unique() if m >= "2023-04")
    oos_days = sess.date[sess.date >= "2023-04-01"].tolist()
    s1 = json.load(open(S1J))
    side_only = s1["gate"].startswith("STOP")
    configs = [(V, h, half) for V in (("a1",), ("a2",), ("a1", "a2")) for h in (False, True) for half in (False, True)]
    if side_only:
        configs = [c for c in configs if not c[1]]
    name = lambda c: f"{'+'.join({'a1': 'S1', 'a2': 'S2'}[v] for v in c[0])}|{'hier' if c[1] else 'pooled'}|{'OFFHALF' if c[2] else 'OFF'}"
    oos = base[base.date >= "2023-04-01"].copy()
    base_day = oos.groupby("date").r.sum().reindex(oos_days, fill_value=0.0)
    rng = np.random.default_rng(SEED)
    res, X, Ex = {"configs_scored": len(configs), "side_only": side_only, "oos_months": len(months),
                  "oos_sessions": len(oos_days), "base_lots_oos": int(len(oos))}, {}, {}
    W = {}
    for c in configs:
        w = walk(base, sess, list(c[0]), c[1], c[2], months)
        W[name(c)] = w
    for nm, w in W.items():
        o = base.assign(w=w)
        o = o[o.date >= "2023-04-01"]
        steer = (o.w * o.r).groupby(o.date).sum().reindex(oos_days, fill_value=0.0)
        wbar = o.groupby("date").w.mean().reindex(oos_days).fillna(1.0)
        nullc = wbar * base_day
        cst = o.w.mean()
        exc = steer - nullc
        X[nm] = exc.to_numpy(); Ex[nm] = (steer, cst)
        # random-switch distribution of the total (same-day permutation)
        tots = np.zeros(500)
        for d, g in o.groupby("date"):
            ww = np.tile(g.w.to_numpy(), (500, 1)); rng.permuted(ww, axis=1, out=ww)
            tots += ww @ g.r.to_numpy()
        mon = exc.groupby(exc.index.str[:7]).sum()
        h1 = exc[exc.index < "2024-11-01"]; h2 = exc[exc.index >= "2025-03-01"]
        vs_b = steer - cst * base_day
        per = {}
        for s in SETUPS:
            q = o[o.setup == s]
            dl = (q.w * q.r - cst * q.r).sum() / len(months); du = ((q.w - 1) * q.r).sum() / len(months)
            per[SHORT[s]] = dict(vs_const_R_per_month=round(float(dl), 2), vs_unsteered_R_per_month=round(float(du), 2),
                                 mean_w=round(float(q.w.mean()), 3))
        bt = exc.sum()
        res[nm] = dict(mean_w=round(float(cst), 3), excess_mean=round(float(exc.mean()), 3), excess_t=round(tstat(exc), 2),
                       vs_const_mean=round(float(vs_b.mean()), 3), vs_const_t=round(tstat(vs_b), 2),
                       vs_unsteered_mean=round(float((steer - base_day).mean()), 3),
                       total_steer=round(float(steer.sum()), 1), random_p95_total=round(float(np.percentile(tots, 95)), 1),
                       random_mean_total=round(float(tots.mean()), 1), half1_mean=round(float(h1.mean()), 3),
                       half2_mean=round(float(h2.mean()), 3), months_pos=f"{int((mon > 0).sum())}/{len(mon)}",
                       best_day_share=round(float(exc.max() / bt), 3) if bt > 0 else None, per_setup=per,
                       goal=goal(steer.to_numpy()))
    Xm = np.column_stack([X[k] for k in X])
    res["PBO"], res["cscv_splits"] = cscv(Xm)
    res["SPA_p"], res["WhiteRC_p"] = spa(Xm, rng=np.random.default_rng(SEED))
    srs = np.array([x.mean() / x.std(ddof=1) for x in X.values()])
    best = max(X, key=lambda k: X[k].mean())
    res["best"] = best
    for N in (N_PRIOR, N_LINEAGE + len(configs)):
        res[f"DSR_N{N}"] = dsr(X[best], srs.var(ddof=1), N)
    res["goal_unsteered"] = goal(base_day.to_numpy())
    st, cst = Ex[best]
    res["goal_constant_best"] = goal((cst * base_day).to_numpy())
    b = res[best]; bar = max(3.46, math.sqrt(2 * math.log(N_LINEAGE + len(configs))))
    w5u = res["goal_unsteered"]["worst5"]; w5s = b["goal"]["worst5"]
    checks = {"rho>=0.3": bool(s1["build_bar_rho"]),
              "excess>=0.5R/day": b["excess_mean"] >= 0.5, f"t>={bar:.2f}": b["excess_t"] >= bar, "t>=3.46": b["excess_t"] >= 3.46,
              "beats_const(t>=2)": b["vs_const_mean"] > 0 and b["vs_const_t"] >= 2,
              "above_random_p95": b["total_steer"] > b["random_p95_total"],
              "PBO<=0.20": res["PBO"] <= 0.20, "SPA<=0.05": res["SPA_p"] <= 0.05,
              "both_halves": b["half1_mean"] > 0 and b["half2_mean"] > 0,
              "months>=60%": int(b["months_pos"].split("/")[0]) >= 0.6 * int(b["months_pos"].split("/")[1]),
              "best_day<10%": b["best_day_share"] is not None and b["best_day_share"] < 0.10,
              "worst5>=20%": w5s >= 0.8 * w5u,
              "no_setup<-2R/mo": all(v["vs_const_R_per_month"] >= -2 for v in b["per_setup"].values())}
    res["bar_t"] = bar; res["checks"] = checks; res["PASS"] = all(v for k, v in checks.items() if k != "t>=3.46")
    json.dump(res, open(OUT, "w"), indent=1, default=float)
    print(json.dumps({k: res[k] for k in res if k not in X}, indent=1, default=float))
