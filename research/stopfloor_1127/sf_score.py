"""STOPFLOOR-1127 bench scoring (PREREG.md): width bins, 5 skip + 5 widen configs vs BASE, per-setup/family effects,
skip random controls (200 same-share skips within setup x split). Widen controls: sf_ctrl.py.
Usage (repo root): python research/stopfloor_1127/sf_score.py WALK_DIR. Educational only - not financial advice."""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sf_common import lot_R, dstats, no_locked, FAM, SHORT  # noqa: E402

W = sys.argv[1]
c = pd.read_parquet(W + "/walk.parquet")
no_locked(c.date.unique())
c["wbp"] = c.risk / c.entry * 1e4
for v in ("BASE", "W50", "W75", "W100", "Wc10", "Wc20"):
    g, ll, l8 = lot_R(c.entry.to_numpy(), c[f"px_{v}"].to_numpy(), c[f"rk_{v}"].to_numpy(), c[f"kind_{v}"].to_numpy(),
                      c.side.to_numpy(), c.tod.to_numpy(), c.gap.to_numpy())
    c[f"g_{v}"], c[f"ll_{v}"], c[f"l8_{v}"] = g, ll, l8
out = {"lots": int(len(c)), "parity_xm": round(float((c.xm_BASE == c.xm).mean()), 4),
       "parity_r_lr8_absdiff": round(float((c.l8_BASE - c.r).abs().mean()), 4),
       "parity_r_lr8_mean": [round(float(c.l8_BASE.mean()), 4), round(float(c.r.mean()), 4)]}
print(out)
DAYS = {p: sorted(g.date.unique()) for p, g in c.groupby("per")}
out["sessions"] = {p: len(d) for p, d in DAYS.items()}
# measurement
out["bins"] = {}
for nm, col, edges in (("bp", "wbp", [0, 25, 50, 75, 100, 150, 250, 1e9]), ("cents", "risk", [0, .10, .20, .35, .60, 1e9])):
    b = pd.cut(c[col], edges, right=False)
    t = c.groupby(["per", b], observed=True).agg(n=("ll_BASE", "size"), liveL=("ll_BASE", "mean"), lr8=("l8_BASE", "mean"),
                                                 gross=("g_BASE", "mean"))
    t["cost"] = t.gross - t.liveL
    print("\n== bins", nm); print(t.round(3).to_string())
    out["bins"][nm] = {f"{a}|{b_}": v for (a, b_), v in t.round(4).to_dict("index").items()}
    t2 = c.groupby(["setup", "per", b], observed=True).ll_BASE.agg(["size", "mean"]).round(3)
    out["bins"][nm + "_setup"] = {f"{SHORT[a]}|{p}|{b_}": v for (a, p, b_), v in t2.to_dict("index").items()}

SKIP = {"S50": c.wbp < 50, "S75": c.wbp < 75, "S100": c.wbp < 100, "Sc10": c.risk < 0.10, "Sc20": c.risk < 0.20}
WID = {"W50": "W50", "W75": "W75", "W100": "W100", "Wc10": "Wc10", "Wc20": "Wc20"}
rng = np.random.default_rng(20261127)
out["configs"] = {}
for name in list(SKIP) + list(WID):
    res = {}
    for per, g in c.groupby("per"):
        if name in SKIP:
            m = SKIP[name][g.index].to_numpy()
            dLL, dL8, dG = (-np.where(m, g[f"{k}_BASE"], 0.0) for k in ("ll", "l8", "g"))
            post_avg = float(g.ll_BASE[~m].mean())
        else:
            m = (g[f"rk_{name}"] > g.risk).to_numpy()
            dLL, dL8, dG = ((g[f"{k}_{name}"] - g[f"{k}_BASE"]).to_numpy() for k in ("ll", "l8", "g"))
            post_avg = float(g[f"ll_{name}"].mean())
        r = dict(share=round(float(m.mean()), 3), n_aff=int(m.sum()), dLL=dstats(g.date, dLL, DAYS[per]),
                 dL8=dstats(g.date, dL8, DAYS[per]), dGross_per_day=round(float(dG.sum() / len(DAYS[per])), 4),
                 base_avg=round(float(g.ll_BASE.mean()), 4), post_avg=round(post_avg, 4),
                 base_per_day=round(float(g.ll_BASE.sum() / len(DAYS[per])), 3),
                 post_per_day=round(float((g.ll_BASE.sum() + dLL.sum()) / len(DAYS[per])), 3),
                 aff_base_avg=round(float(g.ll_BASE[m].mean()), 4) if m.any() else None,
                 aff_base_gross=round(float(g.g_BASE[m].mean()), 4) if m.any() else None,
                 unaff_base_avg=round(float(g.ll_BASE[~m].mean()), 4))
        ps = {}
        for s, gs in g.groupby("setup"):
            ii = g.index.get_indexer(gs.index)
            ps[SHORT[s]] = dict(lots=len(gs), share=round(float(m[ii].mean()), 3), dLL_per_lot=round(float(dLL[ii].sum() / len(gs)), 4),
                                dL8_per_lot=round(float(dL8[ii].sum() / len(gs)), 4), dLL_tot=round(float(dLL[ii].sum()), 1),
                                fam=FAM[s])
        res_f = {}
        for f in set(FAM.values()):
            ii = np.flatnonzero(g.setup.map(FAM).to_numpy() == f)
            res_f[f] = dict(lots=len(ii), dLL_per_lot=round(float(dLL[ii].sum() / max(len(ii), 1)), 4), dLL_tot=round(float(dLL[ii].sum()), 1))
        r["per_setup"], r["per_family"] = ps, res_f
        if name in SKIP:
            setups = g.setup.to_numpy(); R = g.ll_BASE.to_numpy(); tots = []
            idx = {s: np.flatnonzero(setups == s) for s in np.unique(setups)}
            cnt = {s: int(m[ix].sum()) for s, ix in idx.items()}
            for _ in range(200):
                tots.append(-sum(R[rng.choice(ix, cnt[s], replace=False)].sum() for s, ix in idx.items() if cnt[s]))
            tots = np.array(tots)
            r["ctrl"] = dict(mean=round(float(tots.mean()), 1), p95=round(float(np.percentile(tots, 95)), 1),
                             pct=round(float((tots < r["dLL"]["tot"]).mean() * 100), 1))
        res[per] = r
    out["configs"][name] = res
    print("\n", name, {p: (v["share"], v["dLL"]["per_day"], v["dLL"]["t"], v["dLL"]["best_share"], v.get("ctrl"),
                        {k: x["dLL_per_lot"] for k, x in v["per_setup"].items()}) for p, v in res.items()})
json.dump(out, open(HERE + "/score.json", "w"), indent=1, default=str)
