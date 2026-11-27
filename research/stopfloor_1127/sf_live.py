"""STOPFLOOR-1127 live leg: non-Graveyard live trades (primshorts_1126 cleaned set, 10-14..11-25) - realized R by stop-width
bins (bp, cents, spreads) and the 8 live skip configs vs 500 same-share random skips within setup (PREREG.md).
Usage (repo root): python research/stopfloor_1127/sf_live.py PS_LIVE_DIR. Educational only - not financial advice."""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE + "/../primshorts_1126")
sys.argv = [sys.argv[0], sys.argv[1]]
import calib_live as CL  # noqa: E402

t = CL.prep()
t = t[t.account != "graveyard"].copy()
cells = json.load(open(HERE + "/../primshorts_1126/cells_live.json"))
s = t.side
eng = np.where(s > 0, np.minimum(t.x_open, t.stop), np.maximum(t.x_open, t.stop))
eng = np.where(np.isnan(t.x_open), t.stop, eng)
xpx = np.where(t.kind == "target", t.target, np.where(t.kind == "stop", eng, t.x_open))
t["gross_R"] = s * (xpx - t.ref_price) / t.risk_ps
t["R"] = t.gross_R - t.real_R                                     # live realized (decision basis, realized costs)
t["liveL_R"] = t.gross_R - CL.predict_R(cells, t.ref_price, t.risk_ps, t.kind)
t["cents"] = t.risk_ps
t["nspr"] = t.w_bps / t.spread_bps
lo, hi = t.R.quantile([0.005, 0.995])
print("non-GY live trades", len(t), "days", t.date.nunique(), "setups", t.strategy.nunique(), "R clip (report both)", lo, hi)


def dstats(x, d):
    g = pd.Series(x).groupby(np.asarray(d)).sum()
    n = len(g); m = g.mean(); se = g.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    tot = g.sum(); best = g.max()
    return dict(days=n, tot=round(float(tot), 2), t=round(float(m / se), 2) if se else None,
                best_share=round(float(best / tot), 3) if tot > 0 else None, wo_best=round(float(tot - best), 2))


bins = {"bp": ("w_bps", [0, 25, 50, 75, 100, 150, 250, 1e9]), "cents": ("cents", [0, .10, .20, .35, .60, 1e9]),
        "spreads": ("nspr", [0, 6, 8, 12, 20, 1e9])}
out = {"n": len(t), "bins": {}}
for nm, (col, edges) in bins.items():
    b = pd.cut(t[col], edges, right=False)
    g = t.groupby(b, observed=True).agg(n=("R", "size"), R=("R", "mean"), R_clip=("R", lambda x: x.clip(lo, hi).mean()),
                                        liveL=("liveL_R", "mean"), lr8=("r", "mean"), gross=("gross_R", "mean"),
                                        cost=("real_R", "mean"))
    print("\n== by", nm); print(g.round(3).to_string())
    out["bins"][nm] = {str(k): v for k, v in g.round(4).to_dict("index").items()}
# by account x bp bin (CF accounts truncate tight stops after 10-30)
b = pd.cut(t.w_bps, [0, 50, 100, 1e9], right=False)
x = t.groupby(["account", b], observed=True).R.agg(["size", "mean"]).round(3)
print("\n== account x bp", x.to_string()); out["acct_bp"] = {f"{a}|{c}": v for (a, c), v in x.to_dict("index").items()}

CONF = {"L-bp50": t.w_bps < 50, "L-bp75": t.w_bps < 75, "L-bp100": t.w_bps < 100, "L-k6": t.nspr < 6, "L-k8": t.nspr < 8,
        "L-k12": t.nspr < 12, "L-c10": t.cents < 0.10, "L-c20": t.cents < 0.20}
rng = np.random.default_rng(1127)
R = t.R.to_numpy(); D = t.date.to_numpy(); S = t.strategy.to_numpy()
idx_by_s = {k: np.flatnonzero(S == k) for k in np.unique(S)}
out["skip"] = {}
for nm, m in CONF.items():
    m = m.to_numpy()
    dR = -np.where(m, R, 0.0)
    st = dstats(dR, D)
    rnd = []
    cnt = {k: int(m[ix].sum()) for k, ix in idx_by_s.items()}
    for _ in range(500):
        tot = 0.0
        for k, ix in idx_by_s.items():
            if cnt[k]:
                tot -= R[rng.choice(ix, cnt[k], replace=False)].sum()
        rnd.append(tot)
    rnd = np.array(rnd)
    ps = []
    for k, ix in idx_by_s.items():
        if cnt[k] >= 5:
            ps.append((k, cnt[k], len(ix), float(-R[ix][m[ix]].sum()), float(R[ix][m[ix]].mean()), float(R[ix][~m[ix]].mean()) if (~m[ix]).any() else None))
    imp = [p for p in ps if p[3] > 0]; wor = [p for p in ps if p[3] < 0]
    res = dict(share=round(float(m.mean()), 3), n_skip=int(m.sum()), skipped_avgR=round(float(R[m].mean()), 4),
               kept_avgR=round(float(R[~m].mean()), 4), skipped_gross=round(float(t.gross_R[m].mean()), 4),
               kept_gross=round(float(t.gross_R[~m].mean()), 4), skipped_avgR_clip=round(float(np.clip(R[m], lo, hi).mean()), 4),
               dR=st, rnd_mean=round(float(rnd.mean()), 2), rnd_p95=round(float(np.percentile(rnd, 95)), 2),
               pct=round(float((rnd < st["tot"]).mean() * 100), 1),
               setups_affected=len(ps), improve=len(imp), worsen=len(wor),
               improve_R=round(sum(p[3] for p in imp), 1), worsen_R=round(sum(p[3] for p in wor), 1),
               worst_setups=sorted([(p[0][:40], p[1], round(p[3], 1)) for p in wor], key=lambda z: z[2])[:5],
               best_setups=sorted([(p[0][:40], p[1], round(p[3], 1)) for p in imp], key=lambda z: -z[2])[:5])
    # per-account dR
    res["by_account"] = {a: round(float(-R[(t.account == a).to_numpy() & m].sum()), 1) for a in sorted(t.account.unique())}
    out["skip"][nm] = res
    print("\n", nm, json.dumps({k: v for k, v in res.items() if k not in ("worst_setups", "best_setups")}))
# per-family effect (family = name prefix without digits; GEN = generator)
fam = t.strategy.str.split("-").str[0].str.replace(r"\d+", "", regex=True)
t["fam"] = fam
out["family"] = {}
for nm in ("L-bp50", "L-k6", "L-k8", "L-c20"):
    m = CONF[nm].to_numpy(); rows = {}
    for f, g in t.groupby("fam"):
        ii = t.index.get_indexer(g.index); mm = m[ii]
        if mm.sum() >= 5:
            rows[f] = dict(trades=len(g), skipped=int(mm.sum()), dR=round(float(-R[ii][mm].sum()), 1),
                           skipped_avg=round(float(R[ii][mm].mean()), 3), kept_avg=round(float(R[ii][~mm].mean()), 3) if (~mm).any() else None)
    out["family"][nm] = rows
    imp = sum(1 for v in rows.values() if v["dR"] > 0); wor = sum(1 for v in rows.values() if v["dR"] < 0)
    print("\nfamily", nm, "improve", imp, "worsen", wor, {k: (v["skipped"], v["dR"]) for k, v in sorted(rows.items(), key=lambda z: z[1]["dR"])})
# LIVE-L vs realized cost by spread multiple
b = pd.cut(t.nspr, [0, 6, 8, 12, 20, 1e9], right=False)
cc = t.groupby(b, observed=True).apply(lambda g: pd.Series(dict(n=len(g), realized_cost=g.real_R.mean(), liveL_cost=(g.gross_R - g.liveL_R).mean())))
cc["liveL_minus_real"] = cc.liveL_cost - cc.realized_cost
print("\n== cost by spreads", cc.round(3).to_string()); out["cost_by_spreads"] = {str(k): v for k, v in cc.round(4).to_dict("index").items()}
json.dump(out, open(HERE + "/live.json", "w"), indent=1, default=str)
